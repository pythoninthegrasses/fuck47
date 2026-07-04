#!/usr/bin/env python

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import cli
from utils.db import create_article_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / 'backfill.duckdb')


@pytest.fixture
def fake_upnote_db(tmp_path):
    """A stand-in path; copy_db_readonly and sqlite3.connect are mocked so no real sqlite3 file is needed."""
    return str(tmp_path / 'upnote.sqlite3')


def _args(db_path, upnote_db, **overrides):
    argv = ['import-upnote', '--db', db_path, '--upnote-db', upnote_db]
    for flag, value in overrides.items():
        flag_name = f'--{flag.replace("_", "-")}'
        if value is True:
            argv.append(flag_name)
        else:
            argv += [flag_name, str(value)]
    return cli.build_parser().parse_args(argv)


# extract_url only trusts a standalone-URL line near the top of `text` (see utils/upnote.py); html
# hrefs are never treated as authoritative, so fixture notes carry their URL in `text`.
_NOTES = [
    {'id': '1', 'title': 'Trump story one', 'text': 'Headline\nhttps://example.com/a\nBy Author', 'html': ''},
    {'id': '2', 'title': 'Trump story two', 'text': 'Headline\nhttps://example.com/b\nBy Author', 'html': ''},
    {'id': '3', 'title': 'Duplicate url note', 'text': 'Headline\nhttps://example.com/a\nBy Author', 'html': ''},
    {
        'id': '4',
        'title': 'Unresolved note',
        'text': 'Full clip with no dedicated url line, just body text.',
        'html': '<a href="https://example.com/some-hint">hint</a>',
    },
]


# Decorators apply bottom-up, so mock args are: mock_copy, mock_iter, mock_connect (class-level,
# closest to the function first), then any method-level @patch args come before those.
@patch('sqlite3.connect')
@patch('utils.upnote.iter_matching_notes', side_effect=lambda con: iter(_NOTES))
@patch('utils.upnote.copy_db_readonly')
class TestCmdImportUpnote:
    def test_dry_run_lists_candidates_without_inserting(
        self, mock_copy, mock_iter, mock_connect, db_path, fake_upnote_db, capsys
    ):
        rc = cli.cmd_import_upnote(_args(db_path, fake_upnote_db, dry_run=True))

        out = capsys.readouterr().out
        assert rc == 0
        assert 'https://example.com/a' in out
        assert 'https://example.com/b' in out
        # deduped: url from note 3 should not appear twice
        assert out.count('https://example.com/a') == 1
        assert '2 high-confidence candidate' in out
        assert '1 note(s) need manual review' in out

    def test_dry_run_never_touches_db(self, mock_copy, mock_iter, mock_connect, db_path, fake_upnote_db):
        cli.cmd_import_upnote(_args(db_path, fake_upnote_db, dry_run=True))

        assert not Path(db_path).exists()

    @patch('cli.ingest_url')
    def test_processes_deduped_urls_and_reports_summary(
        self, mock_ingest, mock_copy, mock_iter, mock_connect, db_path, fake_upnote_db, tmp_path, capsys
    ):
        mock_ingest.side_effect = [('inserted', 'Title A'), ('inserted', 'Title B')]

        rc = cli.cmd_import_upnote(_args(db_path, fake_upnote_db, review_report=str(tmp_path / 'unresolved.txt')))

        out = capsys.readouterr().out
        assert rc == 0
        assert mock_ingest.call_count == 2
        assert 'inserted=2' in out
        assert 'unresolved=1' in out

    @patch('cli.ingest_url')
    def test_continues_past_fetch_failure_and_writes_report(
        self, mock_ingest, mock_copy, mock_iter, mock_connect, db_path, fake_upnote_db, tmp_path, capsys
    ):
        mock_ingest.side_effect = [('fetch_failed', 'boom'), ('inserted', 'Title B')]
        report_path = str(tmp_path / 'failures.txt')

        rc = cli.cmd_import_upnote(
            _args(db_path, fake_upnote_db, report=report_path, review_report=str(tmp_path / 'unresolved.txt'))
        )

        out = capsys.readouterr().out
        assert rc == 0
        assert 'fetch_failed=1' in out
        assert Path(report_path).read_text().strip() == 'https://example.com/a'

    @patch('cli.ingest_url')
    def test_writes_unresolved_notes_with_hint_link(
        self, mock_ingest, mock_copy, mock_iter, mock_connect, db_path, fake_upnote_db, tmp_path
    ):
        mock_ingest.return_value = ('inserted', 'Title')
        review_path = str(tmp_path / 'unresolved.txt')

        cli.cmd_import_upnote(_args(db_path, fake_upnote_db, review_report=review_path))

        contents = Path(review_path).read_text()
        assert 'Unresolved note' in contents
        assert 'https://example.com/some-hint' in contents

    @patch('cli.ingest_url')
    def test_limit_caps_number_processed(
        self, mock_ingest, mock_copy, mock_iter, mock_connect, db_path, fake_upnote_db, tmp_path
    ):
        mock_ingest.return_value = ('inserted', 'Title')

        cli.cmd_import_upnote(_args(db_path, fake_upnote_db, limit=1, review_report=str(tmp_path / 'unresolved.txt')))

        assert mock_ingest.call_count == 1

    @patch('cli.ingest_url')
    def test_calls_ingest_url_non_interactively_with_proxy(
        self, mock_ingest, mock_copy, mock_iter, mock_connect, db_path, fake_upnote_db, tmp_path
    ):
        mock_ingest.return_value = ('inserted', 'Title')

        cli.cmd_import_upnote(
            _args(
                db_path,
                fake_upnote_db,
                proxy='http://localhost:8080',
                limit=1,
                review_report=str(tmp_path / 'unresolved.txt'),
            )
        )

        assert mock_ingest.call_args.kwargs.get('proxy') == 'http://localhost:8080'
        assert mock_ingest.call_args.kwargs.get('interactive') is False

    @patch('cli.ingest_url')
    def test_real_run_uses_staging_db_not_live_db(
        self, mock_ingest, mock_copy, mock_iter, mock_connect, db_path, fake_upnote_db, tmp_path
    ):
        mock_ingest.return_value = ('inserted', 'Title')

        cli.cmd_import_upnote(_args(db_path, fake_upnote_db, review_report=str(tmp_path / 'unresolved.txt')))

        # ingest_url is mocked so nothing is actually inserted through it; this just confirms
        # the staging db file at --db is the one opened/created, not the live articles.duckdb.
        db = create_article_db(db_path)
        try:
            count = len(db.get_all_articles())
        finally:
            db.close()
        assert count == 0
        assert Path(db_path).exists()
