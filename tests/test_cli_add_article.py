#!/usr/bin/env python

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import cli
from utils.db import create_article_db
from utils.scrape import ScrapeError


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / 'articles.duckdb')


def _args(db_path, url, **overrides):
    argv = ['add-article', url, '--db', db_path]
    for flag, value in overrides.items():
        argv += [f'--{flag.replace("_", "-")}', value]
    return cli.build_parser().parse_args(argv)


class TestCmdAddArticle:
    @patch('cli.extract_metadata')
    @patch('cli.fetch_html')
    def test_successful_extraction_inserts_article(self, mock_fetch, mock_extract, db_path, capsys):
        mock_fetch.return_value = '<html>...</html>'
        mock_extract.return_value = {
            'title': 'Some Headline',
            'description': 'Some summary.',
            'published_at': '2026-07-01',
        }

        rc = cli.cmd_add_article(_args(db_path, 'https://example.com/story'))

        out = capsys.readouterr().out
        assert rc == 0
        assert 'Inserted: Some Headline (https://example.com/story)' in out

        db = create_article_db(db_path)
        try:
            rows = db.search_by_url('https://example.com/story')
        finally:
            db.close()
        assert rows[0]['title'] == 'Some Headline'
        assert rows[0]['source'] == 'example.com'

    @patch('cli.extract_metadata')
    @patch('cli.fetch_html')
    def test_partial_extraction_prompts_for_missing_fields(self, mock_fetch, mock_extract, db_path, capsys):
        mock_fetch.return_value = '<html>...</html>'
        mock_extract.return_value = {'title': None, 'description': 'Some summary.', 'published_at': '2026-07-01'}

        with patch('cli.sys.stdin.isatty', return_value=True), patch('builtins.input', return_value='Prompted Title'):
            rc = cli.cmd_add_article(_args(db_path, 'https://example.com/story'))

        assert rc == 0
        db = create_article_db(db_path)
        try:
            rows = db.search_by_url('https://example.com/story')
        finally:
            db.close()
        assert rows[0]['title'] == 'Prompted Title'

    @patch('cli.extract_metadata')
    @patch('cli.fetch_html')
    def test_cli_flags_bypass_prompts(self, mock_fetch, mock_extract, db_path):
        mock_fetch.return_value = '<html>...</html>'
        mock_extract.return_value = {'title': None, 'description': None, 'published_at': None}

        with patch('cli.sys.stdin.isatty', return_value=True), patch('builtins.input') as mock_input:
            rc = cli.cmd_add_article(
                _args(
                    db_path,
                    'https://example.com/story',
                    title='Flag Title',
                    description='Flag description.',
                    date='2026-07-02',
                )
            )

        assert rc == 0
        mock_input.assert_not_called()
        db = create_article_db(db_path)
        try:
            rows = db.search_by_url('https://example.com/story')
        finally:
            db.close()
        assert rows[0]['title'] == 'Flag Title'
        assert rows[0]['published_at'] == '2026-07-02'

    @patch('cli.extract_metadata')
    @patch('cli.fetch_html')
    def test_duplicate_url_reported_without_error(self, mock_fetch, mock_extract, db_path, capsys):
        mock_fetch.return_value = '<html>...</html>'
        mock_extract.return_value = {
            'title': 'Some Headline',
            'description': 'Some summary.',
            'published_at': '2026-07-01',
        }
        cli.cmd_add_article(_args(db_path, 'https://example.com/story'))
        capsys.readouterr()

        rc = cli.cmd_add_article(_args(db_path, 'https://example.com/story'))

        out = capsys.readouterr().out
        assert rc == 0
        assert 'Duplicate (already in store): https://example.com/story' in out

    @patch('cli.extract_metadata')
    @patch('cli.fetch_html')
    def test_non_tty_with_missing_fields_exits_nonzero(self, mock_fetch, mock_extract, db_path, capsys):
        mock_fetch.return_value = '<html>...</html>'
        mock_extract.return_value = {'title': None, 'description': None, 'published_at': '2026-07-01'}

        with patch('cli.sys.stdin.isatty', return_value=False):
            rc = cli.cmd_add_article(_args(db_path, 'https://example.com/story'))

        out = capsys.readouterr().out
        assert rc == 1
        assert 'title' in out
        assert 'description' in out

    @patch('cli.extract_metadata')
    @patch('cli.fetch_html')
    def test_proxy_flag_passed_to_fetch_html(self, mock_fetch, mock_extract, db_path):
        mock_fetch.return_value = '<html>...</html>'
        mock_extract.return_value = {
            'title': 'Some Headline',
            'description': 'Some summary.',
            'published_at': '2026-07-01',
        }

        cli.cmd_add_article(_args(db_path, 'https://example.com/story', proxy='http://localhost:8080'))

        assert mock_fetch.call_args.kwargs.get('proxy') == 'http://localhost:8080'

    @patch('cli.fetch_html')
    def test_fetch_failure_returns_nonzero(self, mock_fetch, db_path, capsys):
        mock_fetch.side_effect = ScrapeError("boom")

        rc = cli.cmd_add_article(_args(db_path, 'https://example.com/story'))

        assert rc == 1
        assert 'boom' in capsys.readouterr().out
