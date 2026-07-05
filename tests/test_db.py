#!/usr/bin/env python

import pytest
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
from utils.db import ArticleDB, create_article_db


@pytest.fixture
def sample_articles():
    """Fixture providing sample articles for testing.

    published_at values are relative to now so the fixture stays valid
    regardless of when the test suite runs (see clear_old_articles tests).
    """
    now = datetime.now()
    return [
        {
            'title': 'Trump Says Musk Is Off the Rails With America Party Effort',
            'description': 'The tech billionaire effort to create a new political party, called the America Party, comes amid a ramped-up feud with the president over his new domestic policy law.',
            'url': 'https://www.nytimes.com/2025/07/06/us/politics/trump-musk-america-party.html',
            'source': 'NYT > U.S. > Politics',
            'category': 'rss',
            'author': 'Tyler Pager',
            'published_at': (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
        },
        {
            'title': 'How to Make the Biggest Splash, According to Science',
            'description': 'Cannonball, belly-flop or manu jumping? Physicists study the splashiest way to hit the water.',
            'url': 'https://www.example.com/science/physics/big-splash-water-jump',
            'source': 'Science Daily',
            'category': 'science',
            'author': 'John Smith',
            'published_at': (now - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M'),
        },
        {
            'title': 'Can Democrats Find Their Way on Immigration?',
            'description': 'The party leftward shift in the Biden administration arguably laid the groundwork for President Trump aggressive approach.',
            'url': 'https://www.nytimes.com/2025/07/06/us/politics/democrats-immigration-trump.html',
            'source': 'NYT > U.S. > Politics',
            'category': 'rss',
            'author': 'Lisa Lerer',
            'published_at': (now - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M'),
        },
        {
            'title': 'Old Article from Yesterday',
            'description': 'This is an old article that should be removed.',
            'url': 'https://www.example.com/old-article',
            'source': 'Old News',
            'category': 'general',
            'author': 'Old Reporter',
            'published_at': (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M'),
        },
    ]


@pytest.fixture
def temp_db():
    """Fixture providing a temporary DuckDB-backed database for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_db_path = str(Path(temp_dir) / 'test.duckdb')

    db = ArticleDB(temp_db_path)
    yield db

    db.close()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def populated_db(temp_db, sample_articles):
    """Fixture providing a database populated with sample articles."""
    temp_db.insert_articles(sample_articles)
    return temp_db


@pytest.fixture
def articles_parquet_data():
    """Fixture providing all articles from the tests/fixtures/articles.parquet file."""
    articles_file = Path('tests/fixtures/articles.parquet')
    if not articles_file.exists():
        pytest.skip("articles.parquet fixture not found")

    con = duckdb.connect()
    try:
        rows = con.execute(f"SELECT * FROM read_parquet('{articles_file}')").fetchall()
        columns = [col[0] for col in con.description]
        return [dict(zip(columns, row, strict=False)) for row in rows]
    finally:
        con.close()


class TestArticleDB:
    """Test cases for ArticleDB class."""

    def test_db_initialization(self, temp_db):
        """Test that database initializes correctly."""
        assert isinstance(temp_db, ArticleDB)
        assert temp_db.db_path.endswith('.duckdb')
        assert temp_db.con is not None

    def test_db_initialization_with_custom_path(self):
        """Test database initialization with custom path."""
        temp_dir = tempfile.mkdtemp()
        custom_path = str(Path(temp_dir) / 'custom.duckdb')

        try:
            db = ArticleDB(custom_path)
            assert db.db_path == custom_path
            db.close()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_insert_single_article(self, temp_db, sample_articles):
        """Test inserting a single article."""
        article = sample_articles[0]
        result = temp_db.insert_article(article)

        assert result is True, "Should return True when inserting new article"

        # Verify article was inserted
        all_articles = temp_db.get_all_articles()
        assert len(all_articles) == 1
        assert all_articles[0]['url'] == article['url']

    def test_insert_duplicate_article(self, temp_db, sample_articles):
        """Test inserting duplicate article."""
        article = sample_articles[0]

        # Insert first time
        result1 = temp_db.insert_article(article)
        assert result1 is True

        # Insert same article again
        result2 = temp_db.insert_article(article)
        assert result2 is False, "Should return False when inserting duplicate"

        # Verify only one article exists
        all_articles = temp_db.get_all_articles()
        assert len(all_articles) == 1

    def test_insert_multiple_articles(self, temp_db, sample_articles):
        """Test inserting multiple articles."""
        inserted_count = temp_db.insert_articles(sample_articles)

        assert inserted_count == len(sample_articles)

        # Verify all articles were inserted
        all_articles = temp_db.get_all_articles()
        assert len(all_articles) == len(sample_articles)

    def test_insert_multiple_articles_with_duplicates(self, temp_db, sample_articles):
        """Test inserting multiple articles with some duplicates."""
        # Insert first batch
        inserted_count1 = temp_db.insert_articles(sample_articles[:2])
        assert inserted_count1 == 2

        # Insert second batch with one duplicate
        inserted_count2 = temp_db.insert_articles(sample_articles[1:3])
        assert inserted_count2 == 1, "Should insert only new articles"

        # Verify total count
        all_articles = temp_db.get_all_articles()
        assert len(all_articles) == 3

    def test_insert_article_missing_optional_fields(self, temp_db):
        """Test inserting an article with only a subset of fields round-trips nullable columns."""
        result = temp_db.insert_article({'url': 'https://example.com/minimal', 'title': 'Minimal Article'})
        assert result is True

        stored = temp_db.search_by_url('https://example.com/minimal')
        assert len(stored) == 1
        assert stored[0]['djt_relevance_score'] is None
        assert stored[0]['sentiment_score'] is None

    def test_insert_article_defaults_manual_review_to_false(self, temp_db):
        """manual_review defaults to False so ordinary pipeline-fetched articles aren't pinned."""
        temp_db.insert_article({'url': 'https://example.com/regular', 'title': 'Regular Article'})

        stored = temp_db.search_by_url('https://example.com/regular')
        assert stored[0]['manual_review'] is False

    def test_insert_article_respects_manual_review_true(self, temp_db):
        """manual_review=True round-trips, e.g. for cli.py merge-reviewed's pinned rows."""
        temp_db.insert_article({'url': 'https://example.com/pinned', 'title': 'Pinned Article', 'manual_review': True})

        stored = temp_db.search_by_url('https://example.com/pinned')
        assert stored[0]['manual_review'] is True

    def test_mark_manual_review_pins_an_existing_row(self, temp_db):
        """mark_manual_review flags a row after insertion, independent of the original insert call -
        used by cli.py merge-reviewed to pin rows that may have already existed (ON CONFLICT DO NOTHING
        means insert_article alone can't retroactively flag a pre-existing row)."""
        temp_db.insert_article({'url': 'https://example.com/existing', 'title': 'Existing Article'})
        assert temp_db.search_by_url('https://example.com/existing')[0]['manual_review'] is False

        temp_db.mark_manual_review('https://example.com/existing')

        assert temp_db.search_by_url('https://example.com/existing')[0]['manual_review'] is True

    def test_existing_db_without_manual_review_column_is_migrated(self, tmp_path):
        """Opening a pre-existing articles.duckdb (created before manual_review existed) adds the column."""
        db_path = str(tmp_path / 'legacy.duckdb')
        con = duckdb.connect(db_path)
        con.execute("""
            CREATE TABLE articles (
                url VARCHAR PRIMARY KEY,
                published_at VARCHAR,
                title VARCHAR,
                description VARCHAR,
                source VARCHAR,
                category VARCHAR,
                author VARCHAR,
                djt_relevance_score DOUBLE,
                sentiment_score DOUBLE
            )
        """)
        con.execute("INSERT INTO articles (url, title) VALUES ('https://example.com/legacy', 'Legacy Article')")
        con.close()

        db = ArticleDB(db_path)
        try:
            stored = db.search_by_url('https://example.com/legacy')
            assert stored[0]['manual_review'] is False
        finally:
            db.close()

    def test_search_by_url(self, populated_db, sample_articles):
        """Test searching articles by URL."""
        target_url = sample_articles[0]['url']
        results = populated_db.search_by_url(target_url)

        assert len(results) == 1
        assert results[0]['url'] == target_url

    def test_search_by_url_not_found(self, populated_db):
        """Test searching for non-existent URL."""
        results = populated_db.search_by_url('https://nonexistent.com')
        assert len(results) == 0

    def test_search_by_category(self, populated_db, sample_articles):
        """Test searching articles by category."""
        results = populated_db.search_by_category('rss')

        assert len(results) == 2  # Two RSS articles in sample data
        for result in results:
            assert result['category'] == 'rss'

    def test_search_by_category_not_found(self, populated_db):
        """Test searching for non-existent category."""
        results = populated_db.search_by_category('nonexistent')
        assert len(results) == 0

    def test_get_all_articles(self, populated_db, sample_articles):
        """Test getting all articles."""
        all_articles = populated_db.get_all_articles()
        assert len(all_articles) == len(sample_articles)

    def test_get_all_articles_empty_db(self, temp_db):
        """Test getting all articles from empty database."""
        all_articles = temp_db.get_all_articles()
        assert len(all_articles) == 0

    def test_remove_by_url(self, populated_db, sample_articles):
        """Test removing articles by URL."""
        target_url = sample_articles[0]['url']

        # Verify article exists
        assert len(populated_db.search_by_url(target_url)) == 1

        # Remove article
        removed_count = populated_db.remove_by_url(target_url)
        assert len(removed_count) == 1

        # Verify article is gone
        assert len(populated_db.search_by_url(target_url)) == 0

    def test_remove_by_url_not_found(self, populated_db):
        """Test removing non-existent article."""
        removed_count = populated_db.remove_by_url('https://nonexistent.com')
        assert len(removed_count) == 0

    def test_clear_all_articles(self, populated_db, sample_articles):
        """Test clearing all articles."""
        # Verify articles exist
        assert len(populated_db.get_all_articles()) == len(sample_articles)

        # Clear all articles
        removed_count = populated_db.clear_all_articles()
        assert removed_count == len(sample_articles)

        # Verify database is empty
        assert len(populated_db.get_all_articles()) == 0

    def test_clear_all_articles_empty_db(self, temp_db):
        """Test clearing articles from empty database."""
        removed_count = temp_db.clear_all_articles()
        assert removed_count == 0

    def test_clear_old_articles(self, populated_db):
        """Test clearing old articles based on time threshold."""
        # Clear articles older than 12 hours
        removed_count = populated_db.clear_old_articles(12)

        # Should remove the old article (24 hours old)
        assert removed_count == 1

        # Verify correct articles remain
        remaining_articles = populated_db.get_all_articles()
        assert len(remaining_articles) == 3

        # Verify the old article is gone
        old_article_results = populated_db.search_by_url('https://www.example.com/old-article')
        assert len(old_article_results) == 0

    def test_clear_old_articles_none_old(self, populated_db):
        """Test clearing old articles when none are old enough."""
        # Clear articles older than 48 hours (none should be removed)
        removed_count = populated_db.clear_old_articles(48)

        assert removed_count == 0

        # Verify all articles remain
        remaining_articles = populated_db.get_all_articles()
        assert len(remaining_articles) == 4

    def test_sort_and_reindex_articles(self, populated_db, sample_articles):
        """Test sorting and reindexing articles."""
        # Sort and reindex
        result_db = populated_db.sort_and_reindex_articles()

        # Verify the method returns the database
        assert result_db is not None

        # Get sorted articles
        sorted_articles = populated_db.get_all_articles()
        assert len(sorted_articles) == len(sample_articles)

        # Verify sorting (by published_at desc, then source asc)
        assert sorted_articles[0]['title'] == 'Trump Says Musk Is Off the Rails With America Party Effort'
        assert sorted_articles[1]['title'] == 'How to Make the Biggest Splash, According to Science'
        assert sorted_articles[2]['title'] == 'Can Democrats Find Their Way on Immigration?'
        assert sorted_articles[3]['title'] == 'Old Article from Yesterday'

    def test_sort_and_reindex_empty_db(self, temp_db):
        """Test sorting and reindexing empty database."""
        result_db = temp_db.sort_and_reindex_articles()
        assert result_db is None  # Returns None when no articles to sort
        assert len(temp_db.get_all_articles()) == 0

    def test_context_manager_usage(self, sample_articles):
        """Test using ArticleDB as context manager."""
        temp_dir = tempfile.mkdtemp()
        temp_db_path = str(Path(temp_dir) / 'test.duckdb')

        try:
            # Use as context manager
            with ArticleDB(temp_db_path) as db:
                db.insert_articles(sample_articles)
                assert len(db.get_all_articles()) == len(sample_articles)

            # Verify database is closed properly (can still access data)
            with ArticleDB(temp_db_path) as db:
                assert len(db.get_all_articles()) == len(sample_articles)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_close_method(self, temp_db):
        """Test explicit close method."""
        # Add some data
        temp_db.insert_article({'url': 'test', 'title': 'Test'})
        temp_db_path = temp_db.db_path

        # Close the database
        temp_db.close()

        # Verify we can still create a new instance with same path
        new_db = ArticleDB(temp_db_path)
        assert len(new_db.get_all_articles()) == 1
        new_db.close()

    def test_export_parquet_reflects_table_contents(self, temp_db, sample_articles):
        """Test that the Parquet export always reflects the current table contents."""
        temp_db.insert_articles(sample_articles)

        con = duckdb.connect()
        try:
            count = con.execute(f"SELECT count(*) FROM read_parquet('{temp_db.parquet_path}')").fetchone()[0]
        finally:
            con.close()

        assert count == len(sample_articles)


class TestArchiveSnapshot:
    """Test cases for ArticleDB.archive_snapshot."""

    def test_writes_snapshot_to_partitioned_path(self, temp_db, sample_articles, tmp_path):
        """Snapshot lands at archive/<store>/<date>/<timestamp>.parquet."""
        temp_db.insert_articles(sample_articles)
        run_at = datetime(2026, 7, 1, 14, 0)
        archive_dir = tmp_path / 'archive'

        snapshot_path = temp_db.archive_snapshot(str(archive_dir), run_at)

        store_name = Path(temp_db.db_path).stem
        expected_path = archive_dir / store_name / '2026-07-01' / '2026-07-01T1400.parquet'
        assert snapshot_path == str(expected_path)
        assert expected_path.exists()

    def test_snapshot_contains_run_at_and_article_columns(self, temp_db, sample_articles, tmp_path):
        """Snapshot rows carry the existing article columns plus a run_at column."""
        temp_db.insert_articles(sample_articles)
        run_at = datetime(2026, 7, 1, 14, 0)

        snapshot_path = temp_db.archive_snapshot(str(tmp_path / 'archive'), run_at)

        con = duckdb.connect()
        try:
            rows = con.execute(f"SELECT * FROM read_parquet('{snapshot_path}')").fetchall()
            columns = [col[0] for col in con.description]
        finally:
            con.close()

        assert len(rows) == len(sample_articles)
        assert 'run_at' in columns
        for row in rows:
            assert dict(zip(columns, row, strict=False))['run_at'] == run_at

    def test_repeated_snapshots_same_day_do_not_overwrite(self, temp_db, sample_articles, tmp_path):
        """Two runs on the same day produce two distinct files, neither overwritten."""
        temp_db.insert_articles(sample_articles)
        archive_dir = tmp_path / 'archive'

        first_path = temp_db.archive_snapshot(str(archive_dir), datetime(2026, 7, 1, 14, 0))
        second_path = temp_db.archive_snapshot(str(archive_dir), datetime(2026, 7, 1, 20, 0))

        assert first_path != second_path
        assert Path(first_path).exists()
        assert Path(second_path).exists()

    def test_archive_never_truncated(self, temp_db, sample_articles, tmp_path):
        """Writing a new snapshot does not remove or modify prior snapshot files."""
        temp_db.insert_articles(sample_articles)
        archive_dir = tmp_path / 'archive'

        first_path = temp_db.archive_snapshot(str(archive_dir), datetime(2026, 7, 1, 14, 0))
        first_mtime = Path(first_path).stat().st_mtime
        temp_db.archive_snapshot(str(archive_dir), datetime(2026, 7, 2, 14, 0))

        assert Path(first_path).exists()
        assert Path(first_path).stat().st_mtime == first_mtime

    def test_read_parquet_glob_returns_union_across_stores(self, temp_db, sample_articles, tmp_path):
        """read_parquet over the archive glob returns snapshots from every store."""
        temp_dir2 = tempfile.mkdtemp()
        try:
            other_db = ArticleDB(str(Path(temp_dir2) / 'filtered_articles.duckdb'))
            other_db.insert_articles(sample_articles[:2])

            archive_dir = tmp_path / 'archive'
            temp_db.insert_articles(sample_articles)
            temp_db.archive_snapshot(str(archive_dir), datetime(2026, 7, 1, 14, 0))
            other_db.archive_snapshot(str(archive_dir), datetime(2026, 7, 1, 14, 0))
            other_db.close()

            con = duckdb.connect()
            try:
                count = con.execute(f"SELECT count(*) FROM read_parquet('{archive_dir}/**/*.parquet')").fetchone()[0]
            finally:
                con.close()

            assert count == len(sample_articles) + 2
        finally:
            shutil.rmtree(temp_dir2, ignore_errors=True)


class TestExclusions:
    """Test cases for the excluded_urls table and related ArticleDB methods."""

    @pytest.fixture
    def csv_path(self, tmp_path):
        """A fresh exclude_urls.csv with just the header."""
        import csv as _csv

        path = tmp_path / 'exclude_urls.csv'
        with path.open('w', newline='') as f:
            _csv.DictWriter(f, fieldnames=['url', 'reason', 'excluded_at']).writeheader()
        return str(path)

    @pytest.fixture
    def db_with_csv(self, tmp_path, csv_path):
        """An ArticleDB that syncs from a fresh temp CSV."""
        db = ArticleDB(str(tmp_path / 'test.duckdb'), exclude_csv=csv_path)
        yield db
        db.close()

    def test_add_exclusion_and_is_excluded(self, db_with_csv):
        db_with_csv.add_exclusion('https://example.com/blocked')
        assert db_with_csv.is_excluded('https://example.com/blocked') is True
        assert db_with_csv.is_excluded('https://example.com/allowed') is False

    def test_is_excluded_is_case_insensitive(self, db_with_csv):
        db_with_csv.add_exclusion('https://example.com/blocked')
        assert db_with_csv.is_excluded('https://EXAMPLE.COM/Blocked') is True

    def test_remove_exclusion_clears_the_block(self, db_with_csv):
        db_with_csv.add_exclusion('https://example.com/blocked')
        db_with_csv.remove_exclusion('https://example.com/blocked')
        assert db_with_csv.is_excluded('https://example.com/blocked') is False

    def test_get_exclusions_returns_all_rows(self, db_with_csv):
        db_with_csv.add_exclusion('https://example.com/a', reason='spam')
        db_with_csv.add_exclusion('https://example.com/b')
        rows = db_with_csv.get_exclusions()
        assert len(rows) == 2
        urls = {r['url'] for r in rows}
        assert urls == {'https://example.com/a', 'https://example.com/b'}

    def test_sync_exclusions_from_csv_loads_on_open(self, tmp_path):
        """A URL written to the CSV before opening the DB is excluded on open."""
        import csv as _csv

        csv_path = tmp_path / 'exclude.csv'
        with csv_path.open('w', newline='') as f:
            w = _csv.DictWriter(f, fieldnames=['url', 'reason', 'excluded_at'])
            w.writeheader()
            w.writerow({'url': 'https://example.com/pre-blocked', 'reason': 'test', 'excluded_at': '2026-01-01 00:00'})

        db = ArticleDB(str(tmp_path / 'test.duckdb'), exclude_csv=str(csv_path))
        try:
            assert db.is_excluded('https://example.com/pre-blocked') is True
        finally:
            db.close()

    def test_insert_article_skips_excluded_url(self, db_with_csv):
        db_with_csv.add_exclusion('https://example.com/blocked')
        result = db_with_csv.insert_article({'url': 'https://example.com/blocked', 'title': 'Blocked'})
        assert result is False
        assert db_with_csv.get_all_articles() == []

    def test_insert_article_allows_non_excluded_url(self, db_with_csv):
        db_with_csv.add_exclusion('https://example.com/blocked')
        result = db_with_csv.insert_article({'url': 'https://example.com/allowed', 'title': 'Allowed'})
        assert result is True
        assert len(db_with_csv.get_all_articles()) == 1

    def test_exclusion_survives_ephemeral_db_reopen(self, tmp_path):
        """A URL in the CSV blocks insertion in any new DB opened against that CSV."""
        import csv as _csv

        csv_path = tmp_path / 'exclude.csv'
        with csv_path.open('w', newline='') as f:
            w = _csv.DictWriter(f, fieldnames=['url', 'reason', 'excluded_at'])
            w.writeheader()
            w.writerow({'url': 'https://example.com/blocked', 'reason': 'test', 'excluded_at': '2026-01-01 00:00'})

        # Simulate a fresh ephemeral DB (e.g., after main.py clears articles.duckdb)
        db = ArticleDB(str(tmp_path / 'fresh.duckdb'), exclude_csv=str(csv_path))
        try:
            assert db.is_excluded('https://example.com/blocked') is True
            result = db.insert_article({'url': 'https://example.com/blocked', 'title': 'Re-inserted'})
            assert result is False
        finally:
            db.close()

    def test_existing_db_without_excluded_urls_table_is_migrated(self, tmp_path):
        """Opening a pre-existing DB (created before excluded_urls existed) adds the table."""
        import csv as _csv

        db_path = str(tmp_path / 'legacy.duckdb')
        con = duckdb.connect(db_path)
        con.execute("""
            CREATE TABLE articles (
                url VARCHAR PRIMARY KEY,
                published_at VARCHAR,
                title VARCHAR,
                description VARCHAR,
                source VARCHAR,
                category VARCHAR,
                author VARCHAR,
                djt_relevance_score DOUBLE,
                sentiment_score DOUBLE,
                manual_review BOOLEAN DEFAULT FALSE
            )
        """)
        con.execute("INSERT INTO articles (url, title) VALUES ('https://example.com/legacy', 'Legacy')")
        con.close()

        csv_path = tmp_path / 'empty.csv'
        with csv_path.open('w', newline='') as f:
            _csv.DictWriter(f, fieldnames=['url', 'reason', 'excluded_at']).writeheader()

        db = ArticleDB(db_path, exclude_csv=str(csv_path))
        try:
            assert db.is_excluded('https://example.com/legacy') is False
            assert len(db.get_all_articles()) == 1
        finally:
            db.close()


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_create_article_db(self):
        """Test create_article_db convenience function."""
        temp_dir = tempfile.mkdtemp()
        temp_db_path = str(Path(temp_dir) / 'test.duckdb')

        try:
            db = create_article_db(temp_db_path)
            assert isinstance(db, ArticleDB)
            assert db.db_path == temp_db_path
            db.close()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestDBWithRealData:
    """Test cases using the articles.parquet fixture."""

    def test_real_articles_parquet_data(self, articles_parquet_data):
        """Test that the real articles.parquet fixture loads correctly."""
        if len(articles_parquet_data) == 0:
            pytest.skip("No articles available in test data")

        assert len(articles_parquet_data) > 0

        # Verify article structure
        for article in articles_parquet_data[:5]:  # Check first 5 articles
            assert 'url' in article
            assert 'title' in article
            assert 'source' in article

    def test_db_operations_with_real_data(self, articles_parquet_data):
        """Test database operations with real data."""
        if len(articles_parquet_data) == 0:
            pytest.skip("No articles available in test data")

        temp_dir = tempfile.mkdtemp()
        temp_db_path = str(Path(temp_dir) / 'test.duckdb')

        try:
            db = ArticleDB(temp_db_path)

            # Insert real articles
            inserted_count = db.insert_articles(articles_parquet_data)
            assert inserted_count == len(articles_parquet_data)

            # Test various operations
            all_articles = db.get_all_articles()
            assert len(all_articles) == len(articles_parquet_data)

            # Test search by category if categories exist
            first_article = articles_parquet_data[0]
            if 'category' in first_article and first_article['category']:
                category_results = db.search_by_category(first_article['category'])
                assert len(category_results) > 0

            # Test sort and reindex
            db.sort_and_reindex_articles()
            sorted_articles = db.get_all_articles()
            assert len(sorted_articles) == len(articles_parquet_data)

            db.close()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
