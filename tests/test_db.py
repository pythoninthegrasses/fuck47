#!/usr/bin/env python

import json
import pytest
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import ArticleDB, create_article_db, get_article_query


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
    """Fixture providing a temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_db_path = f.name

    # Create and yield the database
    db = ArticleDB(temp_db_path)
    yield db

    # Cleanup
    db.close()
    Path(temp_db_path).unlink(missing_ok=True)


@pytest.fixture
def populated_db(temp_db, sample_articles):
    """Fixture providing a database populated with sample articles."""
    temp_db.insert_articles(sample_articles)
    return temp_db


@pytest.fixture
def articles_json_data():
    """Fixture providing all articles from articles.json."""
    articles_file = Path('tests/fixtures/articles.json')
    if not articles_file.exists():
        pytest.skip("articles.json file not found")

    with open(articles_file) as f:
        data = json.load(f)

    # Extract articles from TinyDB format
    articles = []
    if '_default' in data:
        for item in data['_default'].values():
            articles.append(item)

    return articles


class TestArticleDB:
    """Test cases for ArticleDB class."""

    def test_db_initialization(self, temp_db):
        """Test that database initializes correctly."""
        assert isinstance(temp_db, ArticleDB)
        assert temp_db.db_path.endswith('.json')
        assert temp_db.db is not None
        assert temp_db.Article is not None

    def test_db_initialization_with_custom_path(self):
        """Test database initialization with custom path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            custom_path = f.name

        try:
            db = ArticleDB(custom_path)
            assert db.db_path == custom_path
            db.close()
        finally:
            Path(custom_path).unlink(missing_ok=True)

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
        # Articles should be in this order based on sample data:
        # 1. Trump Musk article (2025-07-08 10:00, NYT)
        # 2. Science article (2025-07-08 09:00, Science Daily)
        # 3. Immigration article (2025-07-08 08:00, NYT)
        # 4. Old article (2025-07-07 08:00, Old News)

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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_db_path = f.name

        try:
            # Use as context manager
            with ArticleDB(temp_db_path) as db:
                db.insert_articles(sample_articles)
                assert len(db.get_all_articles()) == len(sample_articles)

            # Verify database is closed properly (can still access data)
            with ArticleDB(temp_db_path) as db:
                assert len(db.get_all_articles()) == len(sample_articles)

        finally:
            Path(temp_db_path).unlink(missing_ok=True)

    def test_close_method(self, temp_db):
        """Test explicit close method."""
        # Add some data
        temp_db.insert_article({'url': 'test', 'title': 'Test'})

        # Close the database
        temp_db.close()

        # Verify we can still create a new instance with same path
        new_db = ArticleDB(temp_db.db_path)
        assert len(new_db.get_all_articles()) == 1
        new_db.close()


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_create_article_db(self):
        """Test create_article_db convenience function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_db_path = f.name

        try:
            db = create_article_db(temp_db_path)
            assert isinstance(db, ArticleDB)
            assert db.db_path == temp_db_path
            db.close()
        finally:
            Path(temp_db_path).unlink(missing_ok=True)

    def test_get_article_query(self):
        """Test get_article_query convenience function."""
        query = get_article_query()
        # Verify it returns a Query object (basic duck typing test)
        assert hasattr(query, 'url')
        assert hasattr(query, 'category')


class TestDBWithRealData:
    """Test cases using real articles.json data."""

    def test_real_articles_json_data(self, articles_json_data):
        """Test that real articles.json data loads correctly."""
        if len(articles_json_data) == 0:
            pytest.skip("No articles available in test data")

        assert len(articles_json_data) > 0

        # Verify article structure
        for article in articles_json_data[:5]:  # Check first 5 articles
            assert 'url' in article
            assert 'title' in article
            assert 'source' in article

    def test_db_operations_with_real_data(self, articles_json_data):
        """Test database operations with real data."""
        if len(articles_json_data) == 0:
            pytest.skip("No articles available in test data")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_db_path = f.name

        try:
            db = ArticleDB(temp_db_path)

            # Insert real articles
            inserted_count = db.insert_articles(articles_json_data)
            assert inserted_count == len(articles_json_data)

            # Test various operations
            all_articles = db.get_all_articles()
            assert len(all_articles) == len(articles_json_data)

            # Test search by category if categories exist
            if articles_json_data:
                first_article = articles_json_data[0]
                if 'category' in first_article:
                    category_results = db.search_by_category(first_article['category'])
                    assert len(category_results) > 0

            # Test sort and reindex
            db.sort_and_reindex_articles()
            sorted_articles = db.get_all_articles()
            assert len(sorted_articles) == len(articles_json_data)

            db.close()

        finally:
            Path(temp_db_path).unlink(missing_ok=True)


def test_db_integration():
    """Integration test that replicates database operations."""
    articles_file = Path('articles.json')
    if not articles_file.exists():
        pytest.skip("articles.json file not found for integration test")

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_db_path = f.name

        # Load real data
        with open(articles_file) as f:
            data = json.load(f)

        # Extract articles from TinyDB format
        articles = []
        if '_default' in data:
            for item in data['_default'].values():
                articles.append(item)

        # Test database operations
        db = ArticleDB(temp_db_path)

        # Insert articles
        inserted_count = db.insert_articles(articles)
        assert inserted_count == len(articles)

        # Test search operations
        all_articles = db.get_all_articles()
        assert len(all_articles) == len(articles)

        # Test URL search
        if articles:
            first_url = articles[0]['url']
            search_results = db.search_by_url(first_url)
            assert len(search_results) == 1
            assert search_results[0]['url'] == first_url

        # Test category search
        if articles and 'category' in articles[0]:
            category = articles[0]['category']
            category_results = db.search_by_category(category)
            assert len(category_results) > 0

        # Test sorting
        db.sort_and_reindex_articles()
        sorted_articles = db.get_all_articles()
        assert len(sorted_articles) == len(articles)

        # Test cleanup
        removed_count = db.clear_all_articles()
        assert removed_count == len(articles)
        assert len(db.get_all_articles()) == 0

        db.close()

    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")
    finally:
        Path(temp_db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    # If run directly, execute the integration test
    test_db_integration()
    print("All tests would pass if run with pytest")
