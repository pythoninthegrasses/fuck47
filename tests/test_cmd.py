#!/usr/bin/env python

import csv
import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import cli as cmd_module
from utils.db import ArticleDB, create_article_db


LABOR_BOARD_URL = 'https://www.axios.com/2023/03/27/labor-board-says-non-disparagement-clauses-are-unlawful'
LABOR_BOARD_TITLE = 'Labor board says non-disparagement clauses are unlawful'
LABOR_BOARD_SLUG = 'labor-board-says-non-disparagement-clauses-are-unlawful'
SITE_URL_WITH_SLUG = f'https://fuckfortyseven.org/#{LABOR_BOARD_SLUG}'


@pytest.fixture
def csv_path(tmp_path):
    """A fresh exclude_urls.csv with just the header."""
    path = tmp_path / 'exclude_urls.csv'
    with path.open('w', newline='') as f:
        csv.DictWriter(f, fieldnames=['url', 'reason', 'excluded_at']).writeheader()
    return str(path)


@pytest.fixture
def articles_db_path(tmp_path):
    return str(tmp_path / 'articles.duckdb')


@pytest.fixture
def filtered_db_path(tmp_path):
    return str(tmp_path / 'filtered_articles.duckdb')


@pytest.fixture
def index_path(tmp_path):
    path = tmp_path / 'index.html'
    path.write_text('<html><!-- ARTICLES:BEGIN --><!-- ARTICLES:END --></html>')
    return str(path)


@pytest.fixture
def labor_board_article():
    now = datetime.now()
    return {
        'url': LABOR_BOARD_URL,
        'title': LABOR_BOARD_TITLE,
        'description': 'The ruling could affect millions of workers.',
        'source': 'Axios',
        'published_at': (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'),
    }


@pytest.fixture
def db_with_labor_board(articles_db_path, labor_board_article, csv_path):
    db = create_article_db(articles_db_path, exclude_csv=csv_path)
    db.insert_article(labor_board_article)
    db.close()
    return articles_db_path


def _parse(argv):
    """Parse cli.py argv, appending --no-push for remove invocations."""
    if '--remove' in argv or '-r' in argv:
        argv = argv + ['--no-push']
    return cmd_module.build_parser().parse_args(argv)


class TestCsvHelpers:
    def test_read_empty_csv(self, csv_path):
        rows = cmd_module._read_exclude_csv(csv_path)
        assert rows == []

    def test_read_nonexistent_csv(self, tmp_path):
        rows = cmd_module._read_exclude_csv(str(tmp_path / 'missing.csv'))
        assert rows == []

    def test_add_to_csv_deduplicates(self, csv_path):
        cmd_module._add_to_exclude_csv(csv_path, ['https://example.com/a'], reason='test')
        cmd_module._add_to_exclude_csv(csv_path, ['https://example.com/a'], reason='again')
        rows = cmd_module._read_exclude_csv(csv_path)
        assert len(rows) == 1

    def test_add_to_csv_lowercases_url(self, csv_path):
        cmd_module._add_to_exclude_csv(csv_path, ['https://EXAMPLE.COM/Path'])
        rows = cmd_module._read_exclude_csv(csv_path)
        assert rows[0]['url'] == 'https://example.com/path'

    def test_remove_from_csv(self, csv_path):
        cmd_module._add_to_exclude_csv(csv_path, ['https://example.com/a', 'https://example.com/b'])
        removed = cmd_module._remove_from_exclude_csv(csv_path, ['https://example.com/a'])
        assert removed == 1
        rows = cmd_module._read_exclude_csv(csv_path)
        assert len(rows) == 1
        assert rows[0]['url'] == 'https://example.com/b'


class TestResolveToSourceUrls:
    """Unit tests for URL/slug/substring resolution."""

    def test_exact_source_url_matches_article(self, labor_board_article):
        matched, preemptive = cmd_module._resolve_to_source_urls([LABOR_BOARD_URL], [labor_board_article])
        assert LABOR_BOARD_URL in matched
        assert not preemptive

    def test_site_anchor_matches_article_by_slug(self, labor_board_article):
        """The fragment from a fuckfortyseven.org/#slug URL resolves to the source article."""
        matched, preemptive = cmd_module._resolve_to_source_urls([SITE_URL_WITH_SLUG], [labor_board_article])
        assert LABOR_BOARD_URL in matched
        assert not preemptive

    def test_title_substring_matches(self, labor_board_article):
        matched, _ = cmd_module._resolve_to_source_urls(['labor board'], [labor_board_article])
        assert LABOR_BOARD_URL in matched

    def test_source_substring_matches(self, labor_board_article):
        matched, _ = cmd_module._resolve_to_source_urls(['Axios'], [labor_board_article])
        assert LABOR_BOARD_URL in matched

    def test_url_substring_matches(self, labor_board_article):
        matched, _ = cmd_module._resolve_to_source_urls(['non-disparagement'], [labor_board_article])
        assert LABOR_BOARD_URL in matched

    def test_external_url_not_in_db_becomes_preemptive_block(self):
        matched, preemptive = cmd_module._resolve_to_source_urls(['https://unknown.com/not-in-db'], [])
        assert not matched
        assert 'https://unknown.com/not-in-db' in preemptive

    def test_no_match_warns_and_returns_empty(self, capsys):
        matched, preemptive = cmd_module._resolve_to_source_urls(['totally-unknown-substring'], [])
        assert not matched
        assert not preemptive
        assert 'WARNING' in capsys.readouterr().out


class TestCmdAdd:
    @patch('cli.ingest_url')
    def test_single_url_inserted(self, mock_ingest, articles_db_path, csv_path, capsys):
        mock_ingest.return_value = ('inserted', 'Some Title')
        args = _parse(
            [
                '--add',
                'https://example.com/story',
                '--articles-db',
                articles_db_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        rc = cmd_module.cmd_add(args)

        assert rc == 0
        assert 'inserted' in capsys.readouterr().out
        mock_ingest.assert_called_once()

    @patch('cli.ingest_url')
    def test_multiple_urls_batch(self, mock_ingest, articles_db_path, csv_path):
        mock_ingest.return_value = ('inserted', 'Title')
        args = _parse(
            [
                '--add',
                'https://a.com/',
                'https://b.com/',
                '--articles-db',
                articles_db_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        rc = cmd_module.cmd_add(args)

        assert rc == 0
        assert mock_ingest.call_count == 2

    @patch('cli.ingest_url')
    def test_add_from_file(self, mock_ingest, articles_db_path, csv_path, tmp_path):
        mock_ingest.return_value = ('inserted', 'Title')
        urls_file = tmp_path / 'urls.csv'
        urls_file.write_text('url\nhttps://a.com/\nhttps://b.com/\n')
        args = _parse(
            [
                '--add',
                '--file',
                str(urls_file),
                '--articles-db',
                articles_db_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        cmd_module.cmd_add(args)

        assert mock_ingest.call_count == 2

    @patch('cli.ingest_url')
    def test_readd_removes_url_from_exclude_csv(self, mock_ingest, articles_db_path, csv_path):
        """Re-adding a previously excluded URL removes it from exclude_urls.csv."""
        now = datetime.now().strftime('%Y-%m-%dT%H:%M')
        with open(csv_path, 'a', newline='') as f:
            csv.DictWriter(f, fieldnames=['url', 'reason', 'excluded_at']).writerow(
                {'url': LABOR_BOARD_URL, 'reason': 'old block', 'excluded_at': now}
            )

        mock_ingest.return_value = ('inserted', 'Some Title')
        args = _parse(
            [
                '--add',
                LABOR_BOARD_URL,
                '--articles-db',
                articles_db_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        cmd_module.cmd_add(args)

        rows = cmd_module._read_exclude_csv(csv_path)
        assert not any(r['url'] == LABOR_BOARD_URL for r in rows)

    def test_no_urls_returns_error(self, articles_db_path, csv_path, capsys):
        args = _parse(
            [
                '--add',
                '--articles-db',
                articles_db_path,
                '--exclude-csv',
                csv_path,
            ]
        )
        args.add = []
        args.file = None

        rc = cmd_module.cmd_add(args)

        assert rc == 1


class TestCmdRemove:
    @patch('utils.db.ArticleDB.archive_snapshot', return_value='/tmp/test.parquet')
    def test_remove_by_exact_url(self, mock_snap, db_with_labor_board, filtered_db_path, index_path, csv_path):
        args = _parse(
            [
                '--remove',
                LABOR_BOARD_URL,
                '--force',
                '--articles-db',
                db_with_labor_board,
                '--filtered-db',
                filtered_db_path,
                '--index-path',
                index_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        rc = cmd_module.cmd_remove(args)

        assert rc == 0
        db = create_article_db(db_with_labor_board, exclude_csv=csv_path)
        try:
            assert db.search_by_url(LABOR_BOARD_URL) == []
        finally:
            db.close()
        rows = cmd_module._read_exclude_csv(csv_path)
        assert any(r['url'] == LABOR_BOARD_URL for r in rows)

    @patch('utils.db.ArticleDB.archive_snapshot', return_value='/tmp/test.parquet')
    def test_remove_by_site_anchor_resolves_to_source_url(
        self, mock_snap, db_with_labor_board, filtered_db_path, index_path, csv_path
    ):
        """Pasting the live-site anchor URL correctly removes the underlying source article."""
        args = _parse(
            [
                '--remove',
                SITE_URL_WITH_SLUG,
                '--force',
                '--articles-db',
                db_with_labor_board,
                '--filtered-db',
                filtered_db_path,
                '--index-path',
                index_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        rc = cmd_module.cmd_remove(args)

        assert rc == 0
        db = create_article_db(db_with_labor_board, exclude_csv=csv_path)
        try:
            assert db.search_by_url(LABOR_BOARD_URL) == []
        finally:
            db.close()

    @patch('utils.db.ArticleDB.archive_snapshot', return_value='/tmp/test.parquet')
    def test_remove_by_substring(self, mock_snap, db_with_labor_board, filtered_db_path, index_path, csv_path):
        args = _parse(
            [
                '--remove',
                'labor board',
                '--force',
                '--articles-db',
                db_with_labor_board,
                '--filtered-db',
                filtered_db_path,
                '--index-path',
                index_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        rc = cmd_module.cmd_remove(args)

        assert rc == 0
        db = create_article_db(db_with_labor_board, exclude_csv=csv_path)
        try:
            assert db.search_by_url(LABOR_BOARD_URL) == []
        finally:
            db.close()

    @patch('utils.db.ArticleDB.archive_snapshot', return_value='/tmp/test.parquet')
    def test_force_skips_confirmation_prompt(self, mock_snap, db_with_labor_board, filtered_db_path, index_path, csv_path):
        args = _parse(
            [
                '--remove',
                LABOR_BOARD_URL,
                '--force',
                '--articles-db',
                db_with_labor_board,
                '--filtered-db',
                filtered_db_path,
                '--index-path',
                index_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        with patch('cli.sys.stdin.isatty', return_value=True), patch('builtins.input') as mock_input:
            rc = cmd_module.cmd_remove(args)

        mock_input.assert_not_called()
        assert rc == 0

    def test_non_tty_without_force_aborts(self, db_with_labor_board, filtered_db_path, index_path, csv_path, capsys):
        args = _parse(
            [
                '--remove',
                LABOR_BOARD_URL,
                '--articles-db',
                db_with_labor_board,
                '--filtered-db',
                filtered_db_path,
                '--index-path',
                index_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        with patch('cli.sys.stdin.isatty', return_value=False):
            rc = cmd_module.cmd_remove(args)

        assert rc == 1
        db = create_article_db(db_with_labor_board, exclude_csv=csv_path)
        try:
            assert db.search_by_url(LABOR_BOARD_URL) != []
        finally:
            db.close()

    @patch('utils.db.ArticleDB.archive_snapshot', return_value='/tmp/test.parquet')
    @patch('cli._git_commit_and_push')
    def test_push_by_default(self, mock_push, mock_snap, db_with_labor_board, filtered_db_path, index_path, csv_path):
        argv = [
            '--remove',
            LABOR_BOARD_URL,
            '--force',
            '--articles-db',
            db_with_labor_board,
            '--filtered-db',
            filtered_db_path,
            '--index-path',
            index_path,
            '--exclude-csv',
            csv_path,
        ]
        args = cmd_module.build_parser().parse_args(argv)

        cmd_module.cmd_remove(args)

        mock_push.assert_called_once()

    @patch('utils.db.ArticleDB.archive_snapshot', return_value='/tmp/test.parquet')
    @patch('cli._git_commit_and_push')
    def test_no_push_skips_git(self, mock_push, mock_snap, db_with_labor_board, filtered_db_path, index_path, csv_path):
        args = _parse(
            [
                '--remove',
                LABOR_BOARD_URL,
                '--force',
                '--articles-db',
                db_with_labor_board,
                '--filtered-db',
                filtered_db_path,
                '--index-path',
                index_path,
                '--exclude-csv',
                csv_path,
            ]
        )

        cmd_module.cmd_remove(args)

        mock_push.assert_not_called()
