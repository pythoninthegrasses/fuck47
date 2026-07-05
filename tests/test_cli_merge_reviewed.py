#!/usr/bin/env python

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import cli
from utils.db import create_article_db


def _article(url, published_at='2020-01-01', title='A reviewed article', description='desc', source='example.com'):
    return {
        'url': url,
        'published_at': published_at,
        'title': title,
        'description': description,
        'source': source,
    }


@pytest.fixture
def staging_db_path(tmp_path):
    return str(tmp_path / 'backfill.duckdb')


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


@pytest.fixture(autouse=True)
def log_path(tmp_path):
    return str(tmp_path / 'merge_reviewed.log')


def _seed_staging(path, urls):
    db = create_article_db(path)
    try:
        db.insert_articles([_article(u) for u in urls])
    finally:
        db.close()


def _args(staging_db_path, articles_db_path, filtered_db_path, index_path, log_path, **overrides):
    argv = [
        '--merge-reviewed',
        '--staging-db',
        staging_db_path,
        '--articles-db',
        articles_db_path,
        '--filtered-db',
        filtered_db_path,
        '--index-path',
        index_path,
        '--log',
        log_path,
    ]
    for flag, value in overrides.items():
        if value is True:
            argv.append(f'--{flag.replace("_", "-")}')
        elif value is False:
            argv.append(f'--no-{flag.replace("_", "-")}')
        else:
            argv += [f'--{flag.replace("_", "-")}', str(value)]
    return cli.build_parser().parse_args(argv)


@patch('cli._git_commit_and_push')
class TestCmdMergeReviewed:
    def test_merges_into_both_live_stores(
        self, mock_push, staging_db_path, articles_db_path, filtered_db_path, index_path, log_path
    ):
        _seed_staging(staging_db_path, ['https://example.com/a', 'https://example.com/b'])

        rc = cli.cmd_merge_reviewed(_args(staging_db_path, articles_db_path, filtered_db_path, index_path, log_path))

        assert rc == 0
        for db_path in (articles_db_path, filtered_db_path):
            db = create_article_db(db_path)
            try:
                urls = {a['url'] for a in db.get_all_articles()}
            finally:
                db.close()
            assert urls == {'https://example.com/a', 'https://example.com/b'}

    def test_renders_index_from_filtered_store(
        self, mock_push, staging_db_path, articles_db_path, filtered_db_path, index_path, log_path
    ):
        _seed_staging(staging_db_path, ['https://example.com/a'])

        cli.cmd_merge_reviewed(_args(staging_db_path, articles_db_path, filtered_db_path, index_path, log_path))

        html = Path(index_path).read_text()
        assert 'https://example.com/a' in html

    def test_pushes_by_default(self, mock_push, staging_db_path, articles_db_path, filtered_db_path, index_path, log_path):
        _seed_staging(staging_db_path, ['https://example.com/a'])

        cli.cmd_merge_reviewed(_args(staging_db_path, articles_db_path, filtered_db_path, index_path, log_path))

        mock_push.assert_called_once_with([index_path], 'chore(content): merge manually-reviewed backfill articles')

    def test_no_push_flag_skips_git(self, mock_push, staging_db_path, articles_db_path, filtered_db_path, index_path, log_path):
        _seed_staging(staging_db_path, ['https://example.com/a'])

        cli.cmd_merge_reviewed(_args(staging_db_path, articles_db_path, filtered_db_path, index_path, log_path, push=False))

        mock_push.assert_not_called()

    def test_empty_staging_db_is_a_noop(
        self, mock_push, staging_db_path, articles_db_path, filtered_db_path, index_path, log_path, capsys
    ):
        rc = cli.cmd_merge_reviewed(_args(staging_db_path, articles_db_path, filtered_db_path, index_path, log_path))

        out = capsys.readouterr().out
        assert rc == 0
        assert 'nothing to merge' in out
        assert not Path(articles_db_path).exists()
        mock_push.assert_not_called()

    def test_idempotent_on_rerun(self, mock_push, staging_db_path, articles_db_path, filtered_db_path, index_path, log_path):
        _seed_staging(staging_db_path, ['https://example.com/a', 'https://example.com/b'])
        args = _args(staging_db_path, articles_db_path, filtered_db_path, index_path, log_path)

        cli.cmd_merge_reviewed(args)
        cli.cmd_merge_reviewed(args)

        db = create_article_db(filtered_db_path)
        try:
            urls = [a['url'] for a in db.get_all_articles()]
        finally:
            db.close()
        assert sorted(urls) == ['https://example.com/a', 'https://example.com/b']
