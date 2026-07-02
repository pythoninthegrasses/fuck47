#!/usr/bin/env python

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import ArticleDB
from utils.render import render_archive


def _article(url, title, published_at='2026-07-01 10:00', source='Example News'):
    return {
        'url': url,
        'published_at': published_at,
        'title': title,
        'description': f'Coverage: {title}',
        'source': source,
        'category': 'politics',
        'author': 'Reporter',
    }


def _seed_snapshot(db_path, articles, run_at, archive_dir):
    db = ArticleDB(str(db_path))
    try:
        db.insert_articles(articles)
        db.archive_snapshot(str(archive_dir), run_at)
    finally:
        db.close()


class TestRenderArchive:
    def test_creates_index_and_per_date_fragments(self, tmp_path):
        archive_dir = tmp_path / 'archive'
        output_dir = tmp_path / 'app_archive'

        _seed_snapshot(
            tmp_path / 'filtered_articles.duckdb',
            [_article('https://example.com/a', 'Trump Article A')],
            datetime(2026, 7, 1, 14, 0),
            archive_dir,
        )

        dates = render_archive(str(archive_dir), str(output_dir))

        assert dates == ['2026-07-01']
        assert (output_dir / 'index.html').exists()
        assert (output_dir / '2026-07-01.html').exists()

        index_html = (output_dir / 'index.html').read_text()
        assert 'hx-get="archive/2026-07-01.html"' in index_html

        fragment_html = (output_dir / '2026-07-01.html').read_text()
        assert 'Trump Article A' in fragment_html
        assert 'https://example.com/a' in fragment_html

    def test_lists_dates_most_recent_first(self, tmp_path):
        archive_dir = tmp_path / 'archive'

        _seed_snapshot(
            tmp_path / 'filtered_articles.duckdb',
            [_article('https://example.com/old', 'Old Article')],
            datetime(2026, 6, 30, 10, 0),
            archive_dir,
        )
        _seed_snapshot(
            tmp_path / 'filtered_articles.duckdb',
            [_article('https://example.com/new', 'New Article')],
            datetime(2026, 7, 1, 10, 0),
            archive_dir,
        )

        dates = render_archive(str(archive_dir), str(tmp_path / 'app_archive'))

        assert dates == ['2026-07-01', '2026-06-30']

    def test_dedupes_articles_across_same_day_runs(self, tmp_path):
        """Multiple cron runs on the same day shouldn't produce duplicate entries for the same article."""
        archive_dir = tmp_path / 'archive'
        db_path = tmp_path / 'filtered_articles.duckdb'

        _seed_snapshot(
            db_path,
            [_article('https://example.com/a', 'Trump Article A')],
            datetime(2026, 7, 1, 8, 0),
            archive_dir,
        )
        _seed_snapshot(
            db_path,
            [_article('https://example.com/a', 'Trump Article A')],
            datetime(2026, 7, 1, 16, 0),
            archive_dir,
        )

        render_archive(str(archive_dir), str(tmp_path / 'app_archive'))
        fragment_html = (tmp_path / 'app_archive' / '2026-07-01.html').read_text()

        assert fragment_html.count('Trump Article A') == 1

    def test_no_archive_dir_renders_empty_index_without_error(self, tmp_path):
        dates = render_archive(str(tmp_path / 'missing'), str(tmp_path / 'app_archive'))

        assert dates == []
        index_html = (tmp_path / 'app_archive' / 'index.html').read_text()
        assert 'No archived runs' in index_html

    def test_escapes_html_in_article_fields(self, tmp_path):
        """Article titles/descriptions come from untrusted feeds and must be HTML-escaped."""
        archive_dir = tmp_path / 'archive'

        _seed_snapshot(
            tmp_path / 'filtered_articles.duckdb',
            [_article('https://example.com/xss', '<script>alert(1)</script>')],
            datetime(2026, 7, 1, 14, 0),
            archive_dir,
        )

        render_archive(str(archive_dir), str(tmp_path / 'app_archive'))
        fragment_html = (tmp_path / 'app_archive' / '2026-07-01.html').read_text()

        assert '<script>alert(1)</script>' not in fragment_html
        assert '&lt;script&gt;' in fragment_html
