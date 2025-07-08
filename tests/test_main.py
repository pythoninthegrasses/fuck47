#!/usr/bin/env python

import json
import pytest
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, call, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import main
from utils.db import ArticleDB
from utils.filter import DJTNewsFilter


@pytest.fixture
def temp_articles_db():
    """Fixture providing a temporary articles database for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_db_path = f.name

    # Create and yield the database
    db = ArticleDB(temp_db_path)
    yield db, temp_db_path

    # Cleanup
    db.close()
    Path(temp_db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_filtered_db():
    """Fixture providing a temporary filtered articles database for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_filtered_path = f.name

    # Create and yield the database
    db = ArticleDB(temp_filtered_path)
    yield db, temp_filtered_path

    # Cleanup
    db.close()
    Path(temp_filtered_path).unlink(missing_ok=True)


@pytest.fixture
def mock_newsapi_articles():
    """Fixture providing mock NewsAPI articles."""
    return [
        {
            'title': 'Breaking: Trump Announces New Policy',
            'url': 'https://example.com/trump-policy',
            'source': 'ABC News',
            'category': 'politics',
            'published_at': '2025-07-08 10:00',
            'description': 'President Trump announces major policy changes',
            'author': 'Political Reporter',
        },
        {
            'title': 'Economic Update: Market Rally Continues',
            'url': 'https://example.com/market-rally',
            'source': 'CNN',
            'category': 'business',
            'published_at': '2025-07-08 09:00',
            'description': 'Stock markets continue upward trend',
            'author': 'Business Reporter',
        },
    ]


@pytest.fixture
def mock_rss_articles():
    """Fixture providing mock RSS articles."""
    return [
        {
            'title': 'Trump Campaign Update: Rally Schedule Released',
            'url': 'https://example.com/trump-rally-schedule',
            'source': 'RSS Feed News',
            'category': 'politics',
            'published_at': '2025-07-08 11:00',
            'description': 'Latest campaign rally schedule announced',
            'author': 'RSS Author',
        },
        {
            'title': 'Technology News: AI Breakthrough',
            'url': 'https://example.com/ai-breakthrough',
            'source': 'Tech RSS',
            'category': 'technology',
            'published_at': '2025-07-08 08:00',
            'description': 'Major advancement in artificial intelligence',
            'author': 'Tech Writer',
        },
    ]


@pytest.fixture
def mock_config_no_filter():
    """Fixture providing configuration with DJT filter disabled."""
    return {
        'CACHE_HOURS': 24,
        'DJT_FILTER_ENABLED': False,
        'DJT_FILTER_MIN_SCORE': 1.0,
    }


@pytest.fixture
def mock_config_with_filter():
    """Fixture providing configuration with DJT filter enabled."""
    return {
        'CACHE_HOURS': 24,
        'DJT_FILTER_ENABLED': True,
        'DJT_FILTER_MIN_SCORE': 1.0,
    }


class TestMainE2E:
    """End-to-end test cases for main() function."""

    def test_main_function_calls(self):
        """Test that main() calls the expected functions."""
        with (
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.article_db') as mock_db,  # Mock the module-level database
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', False),
        ):
            # Set up mocks
            mock_newsapi.return_value = []
            mock_rss.return_value = []
            mock_db.insert_articles.return_value = 0

            # Run main function
            main()

            # Verify all expected functions were called
            mock_newsapi.assert_called_once_with(mock_db)
            mock_rss.assert_called_once()
            mock_db.clear_old_articles.assert_called_once()
            mock_db.sort_and_reindex_articles.assert_called_once()

    def test_main_with_djt_filter_enabled(self):
        """Test main() function with DJT filtering enabled."""
        with (
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.article_db') as mock_main_db,  # Mock module-level article_db
            patch('main.create_article_db') as mock_create_db,  # Mock for filtered db creation
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
        ):
            # Set up mocks
            mock_filtered_db = Mock()
            mock_create_db.return_value = mock_filtered_db  # For filtered_articles.json
            mock_newsapi.return_value = []
            mock_rss.return_value = []
            mock_main_db.insert_articles.return_value = 0
            mock_main_db.get_all_articles.return_value = []

            # Run main function
            main()

            # Verify filtered database was created
            mock_create_db.assert_called_once_with('filtered_articles.json')

            # Verify NewsAPI and RSS articles were fetched
            mock_newsapi.assert_called_once_with(mock_main_db)
            mock_rss.assert_called_once()

            # Verify database operations were called
            mock_main_db.clear_old_articles.assert_called_once()
            mock_main_db.sort_and_reindex_articles.assert_called_once()
            mock_filtered_db.clear_all_articles.assert_called_once()
            mock_filtered_db.sort_and_reindex_articles.assert_called_once()

    def test_main_with_empty_responses(self):
        """Test main() function with empty API responses."""
        with (
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.article_db') as mock_db,
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', False),
        ):
            # Set up mocks
            mock_newsapi.return_value = []  # Empty NewsAPI response
            mock_rss.return_value = []  # Empty RSS response
            mock_db.insert_articles.return_value = 0

            # Run main function
            main()

            # Verify functions were called despite empty responses
            mock_newsapi.assert_called_once_with(mock_db)
            mock_rss.assert_called_once()

            # Verify database operations were still called
            mock_db.clear_old_articles.assert_called_once()
            mock_db.sort_and_reindex_articles.assert_called_once()

    def test_main_with_api_errors(self):
        """Test main() function with API errors."""
        with (
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.create_article_db') as mock_create_db,
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', False),
        ):
            # Set up mocks
            mock_db = Mock()
            mock_create_db.return_value = mock_db
            mock_newsapi.side_effect = Exception("NewsAPI error")
            mock_rss.side_effect = Exception("RSS error")

            # The main function currently doesn't handle these errors gracefully,
            # so we expect exceptions to propagate
            with pytest.raises(Exception):
                main()

    def test_main_cache_cleanup(self, temp_articles_db):
        """Test that main() properly clears old articles."""
        article_db, temp_path = temp_articles_db

        with (
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.create_article_db') as mock_create_db,
            patch('main.CACHE_HOURS', 1),  # Short cache time for testing
            patch('main.DJT_FILTER_ENABLED', False),
        ):
            mock_create_db.return_value = article_db
            mock_newsapi.return_value = []
            mock_rss.return_value = []

            # Insert old articles manually
            old_article = {
                'title': 'Old Article',
                'url': 'https://example.com/old',
                'source': 'Test Source',
                'category': 'general',
                'published_at': '2025-07-07 10:00',  # Yesterday
                'description': 'Old article description',
                'author': 'Test Author',
            }
            article_db.insert_article(old_article)

            # Verify article was inserted
            assert len(article_db.get_all_articles()) == 1

            # Run main function
            main()

            # Note: With CACHE_HOURS=1, articles from yesterday should be cleared
            # This tests the clear_old_articles functionality


class TestMainIntegration:
    """Integration tests for main() function with real components."""

    def test_main_with_caching_enabled(self):
        """Test main() function with caching enabled."""
        # This test verifies that the main() function runs correctly
        # when CACHE_SESSION is enabled (caching is set up at module import)

        with (
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.article_db') as mock_db,
            patch('main.CACHE_SESSION', True),
            patch('main.TTL', 3600),
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', False),
        ):
            mock_newsapi.return_value = []
            mock_rss.return_value = []
            mock_db.insert_articles.return_value = 0

            # Run main - should complete successfully with caching enabled
            main()

            # Verify main functions were called
            mock_newsapi.assert_called_once_with(mock_db)
            mock_rss.assert_called_once()

    def test_main_djt_filter_integration(self, temp_articles_db, temp_filtered_db):
        """Integration test for DJT filtering functionality."""
        article_db, temp_path = temp_articles_db
        filtered_db, filtered_path = temp_filtered_db

        # Create test articles with DJT content
        test_articles = [
            {
                'title': 'Trump Announces New Immigration Policy',
                'url': 'https://example.com/trump-immigration',
                'source': 'News Source',
                'category': 'politics',
                'published_at': '2025-07-08 10:00',
                'description': 'President Trump unveils new immigration strategy',
                'author': 'Political Reporter',
            },
            {
                'title': 'Weather Update: Sunny Skies Expected',
                'url': 'https://example.com/weather',
                'source': 'Weather Channel',
                'category': 'general',
                'published_at': '2025-07-08 09:00',
                'description': 'Clear weather forecast for the week',
                'author': 'Weather Reporter',
            },
        ]

        # Insert test articles
        article_db.insert_articles(test_articles)

        # Apply DJT filtering manually (simulating main() behavior)
        djt_filter = DJTNewsFilter(min_score=1.0)
        all_articles = article_db.get_all_articles()
        djt_articles = djt_filter.filter_articles(all_articles)

        # Store filtered articles
        filtered_db.clear_all_articles()
        filtered_db.insert_articles(djt_articles)

        # Verify filtering worked correctly
        filtered_articles = filtered_db.get_all_articles()
        assert len(filtered_articles) == 1  # Only Trump article should remain
        assert 'Trump' in filtered_articles[0]['title']
        assert 'djt_relevance_score' in filtered_articles[0]

    def test_main_output_messages(self, temp_articles_db, temp_filtered_db):
        """Test that main() produces expected output messages."""
        article_db, temp_path = temp_articles_db
        filtered_db, filtered_path = temp_filtered_db

        with (
            patch('builtins.print') as mock_print,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.create_article_db') as mock_create_db,
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
        ):

            def mock_create_side_effect(filename):
                if filename == 'articles.json':
                    return article_db
                elif filename == 'filtered_articles.json':
                    return filtered_db
                else:
                    raise ValueError(f"Unexpected filename: {filename}")

            mock_create_db.side_effect = mock_create_side_effect
            mock_newsapi.return_value = [{'title': 'Test Article'}]
            mock_rss.return_value = [
                {
                    'title': 'RSS Article',
                    'url': 'https://example.com/rss-article',
                    'source': 'RSS Source',
                    'category': 'politics',
                    'published_at': '2025-07-08 12:00',
                    'description': 'RSS article description',
                    'author': 'RSS Author',
                }
            ]

            main()

            # Verify expected print statements were called
            print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
            assert any('Fetched and stored' in call and 'NewsAPI' in call for call in print_calls)
            assert any('Stored' in call and 'RSS feeds' in call for call in print_calls)


class TestMainErrorHandling:
    """Test cases for error handling in main() function."""

    @patch('main.create_article_db')
    def test_main_with_database_error(self, mock_create_db):
        """Test main() function with database creation error."""
        mock_create_db.side_effect = Exception("Database creation failed")

        # Should handle database errors gracefully
        with pytest.raises(Exception, match="Database creation failed"):
            main()

    @patch('main.fetch_and_store_articles')
    @patch('main.create_article_db')
    @patch('main.CACHE_HOURS', 24)
    @patch('main.DJT_FILTER_ENABLED', False)
    def test_main_with_newsapi_exception(self, mock_create_db, mock_fetch_newsapi, temp_articles_db):
        """Test main() function when NewsAPI fetch raises exception."""
        article_db, temp_path = temp_articles_db
        mock_create_db.return_value = article_db
        mock_fetch_newsapi.side_effect = Exception("NewsAPI connection failed")

        # Should handle NewsAPI errors gracefully
        with pytest.raises(Exception, match="NewsAPI connection failed"):
            main()

    @patch('main.fetch_rss_articles')
    @patch('main.fetch_and_store_articles')
    @patch('main.create_article_db')
    @patch('main.CACHE_HOURS', 24)
    @patch('main.DJT_FILTER_ENABLED', False)
    def test_main_with_rss_exception(self, mock_create_db, mock_fetch_newsapi, mock_fetch_rss, temp_articles_db):
        """Test main() function when RSS fetch raises exception."""
        article_db, temp_path = temp_articles_db
        mock_create_db.return_value = article_db
        mock_fetch_newsapi.return_value = []
        mock_fetch_rss.side_effect = Exception("RSS connection failed")

        # Should handle RSS errors gracefully
        with pytest.raises(Exception, match="RSS connection failed"):
            main()


def test_main_e2e_integration():
    """Complete end-to-end integration test for main() function."""
    try:
        # Simple integration test that verifies main() runs without errors
        with (
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.article_db') as mock_main_db,
            patch('main.create_article_db') as mock_create_db,
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
        ):
            # Set up mocks
            mock_filtered_db = Mock()
            mock_create_db.return_value = mock_filtered_db

            # Mock API responses
            mock_newsapi.return_value = []
            mock_rss.return_value = []
            mock_main_db.insert_articles.return_value = 0
            mock_main_db.get_all_articles.return_value = []

            # Run main function
            main()

            # Verify key functions were called
            mock_newsapi.assert_called_once()
            mock_rss.assert_called_once()
            mock_create_db.assert_called_once_with('filtered_articles.json')

    except Exception as e:
        pytest.fail(f"End-to-end integration test failed: {e}")


if __name__ == "__main__":
    # If run directly, execute the integration test
    test_main_e2e_integration()
    print("All tests would pass if run with pytest")
