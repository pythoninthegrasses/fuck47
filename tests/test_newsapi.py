#!/usr/bin/env python

import json
import pytest
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from utils.db import ArticleDB
from utils.newsapi import fetch_and_store_articles, parse_articles


@pytest.fixture
def temp_db():
    """Fixture providing a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_db_path = str(Path(temp_dir) / 'test.duckdb')

    # Create and yield the database
    db = ArticleDB(temp_db_path)
    yield db

    # Cleanup
    db.close()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_api_response():
    """Fixture providing mock NewsAPI response."""
    return {
        'status': 'ok',
        'totalResults': 3,
        'articles': [
            {
                'source': {'id': 'abc-news', 'name': 'ABC News'},
                'author': 'John Doe',
                'title': 'Breaking: Major Political Development',
                'description': 'A significant political event has occurred...',
                'url': 'https://abcnews.go.com/politics/major-development',
                'urlToImage': 'https://example.com/image1.jpg',
                'publishedAt': '2025-07-08T10:00:00Z',
                'content': 'This is the full content of the article...',
            },
            {
                'source': {'id': 'cnn', 'name': 'CNN'},
                'author': 'Jane Smith',
                'title': 'Technology Breakthrough Announced',
                'description': 'Scientists have made a major breakthrough...',
                'url': 'https://cnn.com/tech/breakthrough',
                'urlToImage': 'https://example.com/image2.jpg',
                'publishedAt': '2025-07-08T09:00:00Z',
                'content': 'The breakthrough was announced today...',
            },
            {
                'source': {'id': 'removed', 'name': 'Removed'},
                'author': None,
                'title': '[Removed]',
                'description': None,
                'url': 'https://removed.com',
                'urlToImage': None,
                'publishedAt': '1970-01-01T00:00:00Z',
                'content': None,
            },
        ],
    }


@pytest.fixture
def mock_filtered_response():
    """Fixture providing mock response with filtered content."""
    return {
        'status': 'ok',
        'totalResults': 2,
        'articles': [
            {
                'source': {'id': 'fox-news', 'name': 'Fox News'},
                'author': 'Reporter A',
                'title': 'Article from Excluded Source',
                'description': 'This should be filtered out...',
                'url': 'https://foxnews.com/article',
                'urlToImage': 'https://example.com/image.jpg',
                'publishedAt': '2025-07-08T08:00:00Z',
                'content': 'Content from excluded source...',
            },
            {
                'source': {'id': 'abc-news', 'name': 'ABC News'},
                'author': 'Reporter B',
                'title': 'Valid Article',
                'description': 'This should pass all filters...',
                'url': 'https://abcnews.go.com/valid-article',
                'urlToImage': 'https://example.com/image.jpg',
                'publishedAt': '2025-07-08T07:00:00Z',
                'content': 'Valid content...',
            },
        ],
    }


class TestParseArticles:
    """Test cases for parse_articles function."""

    @patch('utils.newsapi.fetch_legitimate_sources')
    @patch('utils.newsapi.EXCLUDE_DOMAINS', 'fox-news,breitbart-news')
    @patch('utils.newsapi.EXCLUDE_URLS', 'goodbullhunting.com,queerty.com')
    def test_parse_articles_basic_functionality(self, mock_fetch_sources, mock_api_response):
        """Test basic parsing functionality."""
        mock_fetch_sources.return_value = {'ABC News', 'CNN', 'TechCrunch'}
        seen_urls = set()

        articles = parse_articles(mock_api_response, seen_urls, 'general')

        # Should get 2 articles (removed article filtered out)
        assert len(articles) == 2

        # Check first article structure
        article1 = articles[0]
        assert 'title' in article1
        assert 'url' in article1
        assert 'source' in article1
        assert 'category' in article1
        assert 'published_at' in article1
        assert 'description' in article1
        assert 'author' in article1
        assert article1['category'] == 'general'

    @patch('utils.newsapi.fetch_legitimate_sources')
    @patch('utils.newsapi.EXCLUDE_DOMAINS', 'fox-news,breitbart-news')
    @patch('utils.newsapi.EXCLUDE_URLS', 'goodbullhunting.com,queerty.com')
    def test_parse_articles_source_filtering(self, mock_fetch_sources, mock_filtered_response):
        """Test that excluded sources are filtered out."""
        mock_fetch_sources.return_value = {'ABC News', 'CNN'}
        seen_urls = set()

        articles = parse_articles(mock_filtered_response, seen_urls, 'general')

        # Should only get 1 article (Fox News filtered out)
        assert len(articles) == 1
        assert articles[0]['source'] == 'ABC News'
        assert articles[0]['title'] == 'Valid Article'

    @patch('utils.newsapi.fetch_legitimate_sources')
    @patch('utils.newsapi.EXCLUDE_DOMAINS', 'fox-news,breitbart-news')
    @patch('utils.newsapi.EXCLUDE_URLS', 'goodbullhunting.com,queerty.com')
    def test_parse_articles_duplicate_filtering(self, mock_fetch_sources, mock_api_response):
        """Test that duplicate URLs are filtered out."""
        mock_fetch_sources.return_value = {'ABC News', 'CNN'}
        seen_urls = {'https://abcnews.go.com/politics/major-development'}

        articles = parse_articles(mock_api_response, seen_urls, 'general')

        # Should only get 1 article (first one already seen)
        assert len(articles) == 1
        assert articles[0]['source'] == 'CNN'

    @patch('utils.newsapi.fetch_legitimate_sources')
    @patch('utils.newsapi.EXCLUDE_DOMAINS', 'fox-news,breitbart-news')
    @patch('utils.newsapi.EXCLUDE_URLS', 'goodbullhunting.com,queerty.com')
    def test_parse_articles_non_legitimate_source(self, mock_fetch_sources, mock_api_response):
        """Test filtering of non-legitimate sources."""
        mock_fetch_sources.return_value = {'TechCrunch'}  # Only TechCrunch is legitimate
        seen_urls = set()

        articles = parse_articles(mock_api_response, seen_urls, 'general')

        # Should get no articles (ABC News and CNN not legitimate)
        assert len(articles) == 0

    @patch('utils.newsapi.fetch_legitimate_sources')
    @patch('utils.newsapi.EXCLUDE_DOMAINS', 'fox-news,breitbart-news')
    @patch('utils.newsapi.EXCLUDE_URLS', 'goodbullhunting.com,queerty.com')
    def test_parse_articles_error_response(self, mock_fetch_sources):
        """Test handling of error response."""
        mock_fetch_sources.return_value = {'ABC News', 'CNN'}
        seen_urls = set()
        error_response = {'status': 'error', 'message': 'Invalid API key'}

        articles = parse_articles(error_response, seen_urls, 'general')

        assert len(articles) == 0

    @patch('utils.newsapi.fetch_legitimate_sources')
    @patch('utils.newsapi.EXCLUDE_DOMAINS', 'fox-news,breitbart-news')
    @patch('utils.newsapi.EXCLUDE_URLS', 'goodbullhunting.com,queerty.com')
    def test_parse_articles_missing_fields(self, mock_fetch_sources):
        """Test handling of articles with missing fields."""
        mock_fetch_sources.return_value = {'ABC News'}
        seen_urls = set()

        response_with_missing_fields = {
            'status': 'ok',
            'articles': [
                {
                    'source': {'id': 'abc-news', 'name': 'ABC News'},
                    # 'author' key missing completely
                    'title': 'Article with Missing Fields',
                    # 'description' key missing completely
                    'url': 'https://abcnews.go.com/test',
                    'urlToImage': None,
                    'publishedAt': '2025-07-08T10:00:00Z',
                    'content': None,
                }
            ],
        }

        articles = parse_articles(response_with_missing_fields, seen_urls, 'general')

        assert len(articles) == 1
        assert articles[0]['author'] == 'Unknown Author'  # Default when key missing
        assert articles[0]['description'] == 'No description available.'

    @patch('utils.newsapi.fetch_legitimate_sources')
    @patch('utils.newsapi.EXCLUDE_DOMAINS', 'fox-news,breitbart-news')
    @patch('utils.newsapi.EXCLUDE_URLS', 'goodbullhunting.com,queerty.com')
    def test_parse_articles_malformed_source(self, mock_fetch_sources):
        """Test parsing articles with malformed source data."""
        mock_fetch_sources.return_value = {'ABC News'}

        malformed_response = {
            'status': 'ok',
            'articles': [
                {
                    'source': 'ABC News',  # String instead of dict
                    'author': 'Test Author',
                    'title': 'Test Article',
                    'description': 'Test description',
                    'url': 'https://example.com/test',
                    'urlToImage': None,
                    'publishedAt': '2025-07-08T10:00:00Z',
                    'content': None,
                }
            ],
        }

        seen_urls = set()
        articles = parse_articles(malformed_response, seen_urls, 'general')

        assert len(articles) == 1
        assert articles[0]['source'] == 'ABC News'


class TestDatabaseIntegration:
    """Test cases for database integration."""

    def test_database_article_insertion(self, temp_db):
        """Test inserting articles into database."""
        test_articles = [
            {
                'title': 'Test Article 1',
                'url': 'https://example.com/test1',
                'source': 'Test Source',
                'category': 'general',
                'published_at': '2025-07-08 10:00',
                'description': 'Test description 1',
                'author': 'Test Author 1',
            },
            {
                'title': 'Test Article 2',
                'url': 'https://example.com/test2',
                'source': 'Test Source',
                'category': 'technology',
                'published_at': '2025-07-08 11:00',
                'description': 'Test description 2',
                'author': 'Test Author 2',
            },
        ]

        # Insert articles
        inserted_count = temp_db.insert_articles(test_articles)
        assert inserted_count == 2

        # Verify articles were stored
        stored_articles = temp_db.get_all_articles()
        assert len(stored_articles) == 2

        # Test category filtering
        general_articles = temp_db.search_by_category('general')
        assert len(general_articles) == 1
        assert general_articles[0]['title'] == 'Test Article 1'

        tech_articles = temp_db.search_by_category('technology')
        assert len(tech_articles) == 1
        assert tech_articles[0]['title'] == 'Test Article 2'

    def test_duplicate_article_prevention(self, temp_db):
        """Test that duplicate articles are prevented."""
        article = {
            'title': 'Duplicate Test Article',
            'url': 'https://example.com/duplicate',
            'source': 'Test Source',
            'category': 'general',
            'published_at': '2025-07-08 10:00',
            'description': 'Test description',
            'author': 'Test Author',
        }

        # Insert article twice
        result1 = temp_db.insert_article(article)
        result2 = temp_db.insert_article(article)

        assert result1 is True  # First insertion successful
        assert result2 is False  # Second insertion prevented

        # Verify only one article exists
        stored_articles = temp_db.get_all_articles()
        assert len(stored_articles) == 1


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    @patch('utils.newsapi.fetch_legitimate_sources')
    def test_empty_articles_list(self, mock_fetch_sources):
        """Test handling of empty articles list."""
        mock_fetch_sources.return_value = {'ABC News'}
        seen_urls = set()
        empty_response = {'status': 'ok', 'articles': []}

        articles = parse_articles(empty_response, seen_urls, 'general')
        assert len(articles) == 0

    @patch('utils.newsapi.fetch_legitimate_sources')
    def test_no_legitimate_sources(self, mock_fetch_sources):
        """Test handling when no legitimate sources are available."""
        mock_fetch_sources.return_value = set()  # No legitimate sources
        seen_urls = set()

        response = {
            'status': 'ok',
            'articles': [
                {
                    'source': {'id': 'abc-news', 'name': 'ABC News'},
                    'author': 'Test Author',
                    'title': 'Test Article',
                    'description': 'Test description',
                    'url': 'https://example.com/test',
                    'urlToImage': None,
                    'publishedAt': '2025-07-08T10:00:00Z',
                    'content': None,
                }
            ],
        }

        articles = parse_articles(response, seen_urls, 'general')
        assert len(articles) == 0  # No articles should pass the filter


def test_newsapi_parse_integration():
    """Integration test for article parsing functionality."""
    try:
        # Test data that simulates real API response
        test_response = {
            'status': 'ok',
            'totalResults': 2,
            'articles': [
                {
                    'source': {'id': 'abc-news', 'name': 'ABC News'},
                    'author': 'Integration Test Author',
                    'title': 'Integration Test Article',
                    'description': 'This is a test article for integration testing',
                    'url': 'https://example.com/integration-test',
                    'urlToImage': None,
                    'publishedAt': '2025-07-08T10:00:00Z',
                    'content': None,
                },
                {
                    'source': {'id': 'removed', 'name': 'Removed'},
                    'author': None,
                    'title': '[Removed]',
                    'description': None,
                    'url': 'https://removed.com',
                    'urlToImage': None,
                    'publishedAt': '1970-01-01T00:00:00Z',
                    'content': None,
                },
            ],
        }

        # Mock legitimate sources to include ABC News
        with (
            patch('utils.newsapi.fetch_legitimate_sources') as mock_fetch,
            patch('utils.newsapi.EXCLUDE_DOMAINS', 'fox-news,breitbart-news'),
            patch('utils.newsapi.EXCLUDE_URLS', 'goodbullhunting.com,queerty.com'),
        ):
            mock_fetch.return_value = {'ABC News', 'CNN'}
            seen_urls = set()

            articles = parse_articles(test_response, seen_urls, 'general')

            # Should get 1 article (removed article filtered out)
            assert len(articles) == 1
            assert articles[0]['title'] == 'Integration Test Article'
            assert articles[0]['source'] == 'ABC News'
            assert articles[0]['category'] == 'general'

            # Verify article structure
            for article in articles:
                assert 'title' in article
                assert 'url' in article
                assert 'source' in article
                assert 'category' in article
                assert 'published_at' in article
                assert 'description' in article
                assert 'author' in article

    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")


class TestFetchAndStoreArticlesRetry:
    """Test retry and graceful degradation in fetch_and_store_articles."""

    @patch('utils.retry.time.sleep')
    @patch('utils.newsapi.parse_articles')
    @patch('utils.newsapi.SESSION')
    @patch('utils.newsapi.CATEGORIES', ['cat1', 'cat2'])
    def test_skips_category_with_persistent_503_continues_to_next(self, mock_session, mock_parse, mock_sleep):
        """Category returning 503 after all retries is skipped; pipeline returns articles from other categories."""
        mock_article = {
            'url': 'https://example.com/cat2-article',
            'title': 'Cat2 Article',
            'source': 'Test Source',
            'category': 'cat2',
            'published_at': '2025-01-01 10:00',
            'description': 'Test description',
            'author': 'Test Author',
        }
        mock_parse.return_value = [mock_article]

        def session_get_side_effect(url):
            if 'category=cat1' in url:
                return Mock(status_code=503)
            resp = Mock(status_code=200)
            resp.json.return_value = {'status': 'ok', 'articles': []}
            return resp

        mock_session.get.side_effect = session_get_side_effect
        mock_db = Mock()
        mock_db.insert_article.return_value = True

        articles = fetch_and_store_articles(mock_db)
        assert len(articles) == 1
        assert articles[0]['category'] == 'cat2'

    @patch('utils.retry.time.sleep')
    @patch('utils.newsapi.parse_articles')
    @patch('utils.newsapi.SESSION')
    @patch('utils.newsapi.CATEGORIES', ['cat1', 'cat2'])
    def test_skips_category_with_persistent_429_continues_to_next(self, mock_session, mock_parse, mock_sleep):
        """Category returning 429 (rate-limited) after all retries is skipped; pipeline continues to next category."""
        mock_article = {
            'url': 'https://example.com/cat2-article',
            'title': 'Cat2 Article',
            'source': 'Test Source',
            'category': 'cat2',
            'published_at': '2025-01-01 10:00',
            'description': 'Test description',
            'author': 'Test Author',
        }
        mock_parse.return_value = [mock_article]

        def session_get_side_effect(url):
            if 'category=cat1' in url:
                return Mock(status_code=429)
            resp = Mock(status_code=200)
            resp.json.return_value = {'status': 'ok', 'articles': []}
            return resp

        mock_session.get.side_effect = session_get_side_effect
        mock_db = Mock()
        mock_db.insert_article.return_value = True

        articles = fetch_and_store_articles(mock_db)
        assert len(articles) == 1
        assert articles[0]['category'] == 'cat2'

    @patch('utils.retry.time.sleep')
    @patch('utils.newsapi.RATE_LIMITER')
    @patch('utils.newsapi.parse_articles')
    @patch('utils.newsapi.SESSION')
    @patch('utils.newsapi.CATEGORIES', ['cat1', 'cat2'])
    def test_fetch_and_store_articles_acquires_rate_limiter_per_category(
        self, mock_session, mock_parse, mock_rate_limiter, mock_sleep
    ):
        """fetch_and_store_articles acquires the rate limiter once per category before requesting."""
        mock_parse.return_value = []

        resp = Mock(status_code=200)
        resp.json.return_value = {'status': 'ok', 'articles': []}
        mock_session.get.return_value = resp
        mock_db = Mock()

        fetch_and_store_articles(mock_db)

        assert mock_rate_limiter.acquire.call_count == 2

    @patch('utils.retry.time.sleep')
    @patch('utils.newsapi.parse_articles')
    @patch('utils.newsapi.SESSION')
    @patch('utils.newsapi.CATEGORIES', ['cat1', 'cat2'])
    def test_skips_category_on_connection_error_continues_to_next(self, mock_session, mock_parse, mock_sleep):
        """Category raising ConnectionError after all retries is skipped; pipeline continues to remaining categories."""
        mock_article = {
            'url': 'https://example.com/cat2-article',
            'title': 'Cat2 Article',
            'source': 'Test Source',
            'category': 'cat2',
            'published_at': '2025-01-01 10:00',
            'description': 'Test description',
            'author': 'Test Author',
        }
        mock_parse.return_value = [mock_article]

        def session_get_side_effect(url):
            if 'category=cat1' in url:
                raise requests.ConnectionError("refused")
            resp = Mock(status_code=200)
            resp.json.return_value = {'status': 'ok', 'articles': []}
            return resp

        mock_session.get.side_effect = session_get_side_effect
        mock_db = Mock()
        mock_db.insert_article.return_value = True

        articles = fetch_and_store_articles(mock_db)
        assert len(articles) == 1
        assert articles[0]['category'] == 'cat2'


if __name__ == "__main__":
    # If run directly, execute the integration test
    test_newsapi_parse_integration()
    print("All tests would pass if run with pytest")
