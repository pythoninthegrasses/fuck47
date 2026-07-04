#!/usr/bin/env python

import json
import pytest
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.upnote import copy_db_readonly, extract_url, hint_link, is_excluded_source, iter_matching_notes

SCHEMA = """
CREATE TABLE "notes" (
  "id" TEXT PRIMARY KEY,
  "html" TEXT,
  "text" TEXT,
  "title" TEXT,
  "createdAt" DOUBLE,
  "tagLinks" TEXT,
  "trashed" INTEGER,
  "deleted" INTEGER
)
"""


def _note(con, id, title, text, html='', tag_links=None, trashed=0, deleted=0, created_at=0):
    con.execute(
        "INSERT INTO notes (id, html, text, title, createdAt, tagLinks, trashed, deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (id, html, text, title, created_at, json.dumps(tag_links or []), trashed, deleted),
    )


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / 'upnote.sqlite3'
    con = sqlite3.connect(path)
    con.execute(SCHEMA)

    _note(con, '1', 'Tagged fuck45', 'some body text', tag_links=['fuck45'])
    _note(con, '2', 'Mentions Trump', 'Trump did a thing today.')
    _note(con, '3', 'Unrelated note', 'A bakery won a pie contest.')
    _note(con, '4', 'Trashed trump note', 'Trump again.', trashed=1)
    _note(con, '5', 'Deleted trump note', 'Trump again.', deleted=1)
    _note(con, '6', 'Wrong tag', 'Nothing relevant here.', tag_links=['NeverTrumpers'])

    con.commit()
    con.close()
    return path


class TestCopyDbReadonly:
    def test_copies_db_to_new_location(self, db_path, tmp_path):
        dest_dir = tmp_path / 'copy'
        copied_path = copy_db_readonly(db_path, dest_dir)

        assert Path(copied_path).exists()
        assert Path(copied_path) != db_path

    def test_copy_is_independently_queryable(self, db_path, tmp_path):
        copied_path = copy_db_readonly(db_path, tmp_path / 'copy')

        con = sqlite3.connect(copied_path)
        count = con.execute("SELECT count(*) FROM notes").fetchone()[0]
        con.close()

        assert count == 6


class TestIterMatchingNotes:
    def test_selects_tagged_and_keyword_notes_only(self, db_path):
        con = sqlite3.connect(db_path)
        try:
            notes = list(iter_matching_notes(con))
        finally:
            con.close()

        ids = {n['id'] for n in notes}
        assert ids == {'1', '2'}

    def test_excludes_trashed_and_deleted(self, db_path):
        con = sqlite3.connect(db_path)
        try:
            notes = list(iter_matching_notes(con))
        finally:
            con.close()

        ids = {n['id'] for n in notes}
        assert '4' not in ids
        assert '5' not in ids

    def test_excludes_unrelated_tags(self, db_path):
        con = sqlite3.connect(db_path)
        try:
            notes = list(iter_matching_notes(con))
        finally:
            con.close()

        ids = {n['id'] for n in notes}
        assert '6' not in ids


class TestExtractUrl:
    """extract_url is high-precision only: it never falls back to an arbitrary html href, since
    most matching notes are full article clips with many unrelated in-body/author-bio/footnote
    links (see backlog task-014 investigation notes and utils/upnote.py's docstring)."""

    def test_finds_standalone_url_line_in_text(self):
        note = {
            'html': '<p><a href="https://example.com/from-html">link</a></p>',
            'text': 'Trump story\nhttps://example.com/from-text\nBy Author',
        }
        assert extract_url(note) == 'https://example.com/from-text'

    def test_does_not_fall_back_to_html_href_when_no_standalone_text_url(self):
        note = {
            'html': '<p><a href="https://example.com/from-html">link</a></p>',
            'text': 'see https://example.com/from-text mid-sentence, not its own line',
        }
        assert extract_url(note) is None

    def test_returns_none_when_no_url(self):
        note = {'html': '<p>nothing</p>', 'text': 'no links at all'}
        assert extract_url(note) is None

    def test_ignores_localhost_attachment_link_in_text(self):
        note = {
            'html': '<a href="https://example.com/real-article">real</a>',
            'text': 'Trump story\nhttp://localhost:9425/files/abc.jpeg\nBy Author',
        }
        assert extract_url(note) is None

    def test_only_scans_first_few_lines_of_text(self):
        padding = '\n'.join(['irrelevant body line'] * 10)
        note = {'html': '', 'text': f'{padding}\nhttps://example.com/too-late'}
        assert extract_url(note) is None


class TestHintLink:
    """hint_link is a non-authoritative lead for manual review only - see extract_url()."""

    def test_returns_first_non_attachment_href(self):
        note = {'html': '<a href="http://localhost:9425/files/abc.jpeg">img</a><a href="https://example.com/real">real</a>'}
        assert hint_link(note) == 'https://example.com/real'

    def test_returns_none_when_no_href(self):
        assert hint_link({'html': '<p>nothing</p>'}) is None


class TestIsExcludedSource:
    @pytest.mark.parametrize(
        'url',
        [
            'https://www.youtube.com/watch?v=abc123',
            'https://youtube.com/watch?v=abc123',
            'https://youtu.be/abc123',
            'https://www.quora.com/some-question',
            'https://quora.com/some-question',
        ],
    )
    def test_excludes_video_and_qa_platforms(self, url):
        assert is_excluded_source(url) is True

    def test_does_not_exclude_news_domains(self):
        assert is_excluded_source('https://www.nytimes.com/2024/01/01/us/politics/story.html') is False
