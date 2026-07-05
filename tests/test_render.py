#!/usr/bin/env python

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import ArticleDB
from utils.render import _slugify, render_archive, render_index


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


TEMPLATE = (
    '<!DOCTYPE html>\n<html>\n<body>\n'
    '<!-- ARTICLES:BEGIN -->\n'
    '<script type="application/json" id="poster-articles">[]</script>\n'
    '<noscript><ul id="poster-fallback"></ul></noscript>\n'
    '<!-- ARTICLES:END -->\n'
    '</body>\n</html>\n'
)


def _seed_db(db_path, articles):
    db = ArticleDB(str(db_path))
    try:
        db.insert_articles(articles)
    finally:
        db.close()


class TestRenderIndex:
    def test_injects_articles_json_between_markers(self, tmp_path):
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)
        _seed_db(db_path, [_article('https://example.com/a', 'Trump Article A')])

        count = render_index(str(db_path), str(index_path))

        assert count == 1
        html = index_path.read_text()
        assert 'Trump Article A' in html
        assert 'https://example.com/a' in html
        assert '<!-- ARTICLES:BEGIN -->' in html
        assert '<!-- ARTICLES:END -->' in html

    def test_rerun_replaces_previous_injection(self, tmp_path):
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)
        _seed_db(db_path, [_article('https://example.com/a', 'Trump Article A')])

        render_index(str(db_path), str(index_path))
        render_index(str(db_path), str(index_path))

        html = index_path.read_text()
        assert html.count('https://example.com/a') == 2  # once in JSON, once in noscript
        assert html.count('poster-articles') == 1

    def test_smart_quotes_and_embedded_quotes_round_trip_cleanly(self, tmp_path):
        """Regression guard for task-009: titles/descriptions must inject as literal unicode,
        not mangled \\u201x escapes or literal backslash-quote sequences."""
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)
        title = 'Trump Says Musk Is ‘Off the Rails’ With "America Party" Effort'
        _seed_db(db_path, [_article('https://example.com/a', title)])

        render_index(str(db_path), str(index_path))

        html = index_path.read_text()
        assert '‘Off the Rails’' in html
        assert '\\u2018' not in html and '\\u2019' not in html
        assert '\\"America Party\\"' in html  # valid JSON escaping of the embedded "

        payload = html.split('id="poster-articles">', 1)[1].split('</script>', 1)[0]
        articles = json.loads(payload)
        assert articles[0]['title'] == title

    def test_missing_db_leaves_file_unchanged(self, tmp_path):
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)

        count = render_index(str(tmp_path / 'missing.duckdb'), str(index_path))

        assert count == 0
        assert index_path.read_text() == TEMPLATE

    def test_empty_db_leaves_file_unchanged(self, tmp_path):
        """An empty-but-present DB must not overwrite a populated index (mirrors missing-DB posture)."""
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        # Write index with a populated article block so we can detect an unwanted overwrite.
        populated = TEMPLATE.replace(
            '<script type="application/json" id="poster-articles">[]</script>',
            '<script type="application/json" id="poster-articles">'
            '[{"url":"https://example.com/a","title":"Existing Article","description":"Desc",'
            '"source":"News","published_at":"2026-07-01 10:00","slug":"existing-article"}]'
            '</script>',
        )
        index_path.write_text(populated)
        _seed_db(db_path, [])  # DB exists but contains no articles

        count = render_index(str(db_path), str(index_path))

        assert count == 0
        assert index_path.read_text() == populated

    def test_orders_most_recent_first_and_limits(self, tmp_path):
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)
        _seed_db(
            db_path,
            [
                _article('https://example.com/old', 'Old Article', published_at='2026-06-30 09:00'),
                _article('https://example.com/new', 'New Article', published_at='2026-07-01 09:00'),
            ],
        )

        render_index(str(db_path), str(index_path), limit=1)

        html = index_path.read_text()
        assert 'New Article' in html
        assert 'Old Article' not in html

    def test_escapes_script_breakout_and_html(self, tmp_path):
        """Titles come from untrusted feeds; must not break out of the JSON script tag or noscript list."""
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)
        _seed_db(db_path, [_article('https://example.com/xss', '</script><script>alert(1)</script>')])

        render_index(str(db_path), str(index_path))

        html = index_path.read_text()
        assert '</script><script>alert(1)' not in html
        assert '<\\/script>' in html
        assert '&lt;script&gt;' in html

    def test_writes_noscript_fallback_links(self, tmp_path):
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)
        _seed_db(db_path, [_article('https://example.com/a', 'Trump Article A')])

        render_index(str(db_path), str(index_path))

        html = index_path.read_text()
        assert '<noscript>' in html
        assert '<a href="https://example.com/a"' in html

    def test_injects_slug_per_article(self, tmp_path):
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)
        _seed_db(db_path, [_article('https://example.com/a', 'Trump Article A')])

        render_index(str(db_path), str(index_path))

        payload = _poster_payload(index_path)
        assert payload[0]['slug'] == 'trump-article-a'

    def test_dedupes_slugs_within_payload(self, tmp_path):
        db_path = tmp_path / 'filtered_articles.duckdb'
        index_path = tmp_path / 'index.html'
        index_path.write_text(TEMPLATE)
        _seed_db(
            db_path,
            [
                _article('https://example.com/a', 'Same Title', published_at='2026-07-01 09:00'),
                _article('https://example.com/b', 'Same Title', published_at='2026-07-01 10:00'),
            ],
        )

        render_index(str(db_path), str(index_path))

        payload = _poster_payload(index_path)
        slugs = sorted(a['slug'] for a in payload)
        assert slugs == ['same-title', 'same-title-2']


def _poster_payload(index_path):
    html = Path(index_path).read_text()
    marker = '<script type="application/json" id="poster-articles">'
    start = html.index(marker) + len(marker)
    end = html.index('</script>', start)
    return json.loads(html[start:end])


class TestSlugify:
    def test_basic_title(self):
        assert _slugify('Tucker Carlson Eyes Third Party') == 'tucker-carlson-eyes-third-party'

    def test_collapses_punctuation_and_whitespace(self):
        assert _slugify('Trump: "Big, Beautiful" Bill!!') == 'trump-big-beautiful-bill'

    def test_none_title_falls_back_to_url_hash(self):
        slug = _slugify(None, url='https://example.com/a')
        assert slug != ''
        assert slug == _slugify('', url='https://example.com/a')

    def test_empty_title_falls_back_to_url_hash(self):
        slug = _slugify('!!!', url='https://example.com/a')
        assert slug != ''

    def test_truncates_long_titles_at_word_boundary(self):
        title = 'word ' * 30
        slug = _slugify(title)
        assert len(slug) <= 60
        assert not slug.endswith('-')
