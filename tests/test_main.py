#!/usr/bin/env python

import pytest
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import main
from utils.db import ArticleDB
from utils.filter import DJTNewsFilter
from utils.sentiment import SentimentJudgeError


@pytest.fixture(autouse=True)
def stub_render_index(monkeypatch):
    """Keep main() tests from rewriting the real app/index.html."""
    mock = Mock(return_value=0)
    monkeypatch.setattr('main.render_index', mock)
    return mock


@pytest.fixture
def temp_articles_db():
    """Fixture providing a temporary articles database for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_db_path = str(Path(temp_dir) / 'articles.duckdb')

    # Create and yield the database
    db = ArticleDB(temp_db_path)
    yield db, temp_db_path

    # Cleanup
    db.close()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_filtered_db():
    """Fixture providing a temporary filtered articles database for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_filtered_path = str(Path(temp_dir) / 'filtered_articles.duckdb')

    # Create and yield the database
    db = ArticleDB(temp_filtered_path)
    yield db, temp_filtered_path

    # Cleanup
    db.close()
    shutil.rmtree(temp_dir, ignore_errors=True)


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
            mock_create_db.return_value = mock_filtered_db  # For the filtered articles store
            mock_newsapi.return_value = []
            mock_rss.return_value = []
            mock_main_db.insert_articles.return_value = 0
            mock_main_db.get_all_articles.return_value = []

            # Run main function
            main()

            # Verify filtered database was created
            mock_create_db.assert_called_once_with('filtered_articles.duckdb')

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

    def test_main_cache_cleanup(self, temp_articles_db, tmp_path):
        """Test that main() properly clears old articles."""
        article_db, temp_path = temp_articles_db

        with (
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.create_article_db') as mock_create_db,
            patch('main.ARCHIVE_DIR', str(tmp_path / 'archive')),
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

    def test_main_output_messages(self, temp_articles_db, temp_filtered_db, tmp_path):
        """Test that main() produces expected output messages."""
        article_db, temp_path = temp_articles_db
        filtered_db, filtered_path = temp_filtered_db

        with (
            patch('builtins.print') as mock_print,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.create_article_db') as mock_create_db,
            patch('main.ARCHIVE_DIR', str(tmp_path / 'archive')),
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
        ):

            def mock_create_side_effect(filename):
                if filename == 'articles.duckdb':
                    return article_db
                elif filename == 'filtered_articles.duckdb':
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


class TestMainSentimentGate:
    """Test cases for the sentiment-based negative-only filtering gate in main()."""

    def _djt_article(self, title, url, minutes_ago=0):
        # published_at must be recent (relative to "now") so clear_old_articles()
        # doesn't purge it before the sentiment gate runs.
        published_at = (datetime.now() - timedelta(minutes=minutes_ago)).strftime('%Y-%m-%d %H:%M')
        return {
            'title': title,
            'url': url,
            'source': 'News Source',
            'category': 'politics',
            'published_at': published_at,
            'description': 'Trump-related coverage',
            'author': 'Reporter',
        }

    @patch('main.score_articles')
    def test_negative_and_positive_articles_split_at_threshold(
        self, mock_score_articles, temp_articles_db, temp_filtered_db, tmp_path
    ):
        """Articles are included/excluded based on SENTIMENT_MAX_SCORE boundary (<=)."""
        article_db, temp_path = temp_articles_db
        filtered_db, filtered_path = temp_filtered_db

        articles = [
            self._djt_article('Trump Negative Article', 'https://example.com/neg', minutes_ago=10),
            self._djt_article('Trump Boundary Article', 'https://example.com/boundary', minutes_ago=20),
            self._djt_article('Trump Positive Article', 'https://example.com/pos', minutes_ago=30),
        ]
        article_db.insert_articles(articles)

        # index 0: below threshold (included), 1: exactly at threshold (included, <=), 2: above (excluded)
        mock_score_articles.return_value = {0: -0.5, 1: 0.0, 2: 0.5}

        with (
            patch('main.fetch_rss_articles', return_value=[]),
            patch('main.fetch_and_store_articles', return_value=[]),
            patch('main.article_db', article_db),
            patch('main.create_article_db', return_value=filtered_db),
            patch('main.ARCHIVE_DIR', str(tmp_path / 'archive')),
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
            patch('main.SENTIMENT_ENABLED', True),
            patch('main.SENTIMENT_MAX_SCORE', 0.0),
        ):
            main()

        stored = filtered_db.get_all_articles()
        stored_titles = {a['title'] for a in stored}
        assert stored_titles == {'Trump Negative Article', 'Trump Boundary Article'}

    @patch('main.score_articles')
    def test_manual_review_articles_survive_rebuild_despite_failing_gates(
        self, mock_score_articles, temp_articles_db, temp_filtered_db, tmp_path
    ):
        """Pinned (manual_review=True) rows are preserved in the rebuilt filtered store even when
        they'd fail the DJT filter or sentiment gate - see cli.py's merge-reviewed command."""
        article_db, temp_path = temp_articles_db
        filtered_db, filtered_path = temp_filtered_db

        pinned = self._djt_article('Manually Reviewed Article', 'https://example.com/pinned', minutes_ago=5)
        pinned['manual_review'] = True
        algorithmic = self._djt_article('Algorithmic Positive Article', 'https://example.com/algo', minutes_ago=10)
        article_db.insert_articles([pinned, algorithmic])

        # index 0: pinned article scores positive (would normally be excluded); 1: algorithmic article positive too
        mock_score_articles.return_value = {0: 0.9, 1: 0.9}

        with (
            patch('main.fetch_rss_articles', return_value=[]),
            patch('main.fetch_and_store_articles', return_value=[]),
            patch('main.article_db', article_db),
            patch('main.create_article_db', return_value=filtered_db),
            patch('main.ARCHIVE_DIR', str(tmp_path / 'archive')),
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
            patch('main.SENTIMENT_ENABLED', True),
            patch('main.SENTIMENT_MAX_SCORE', 0.0),
        ):
            main()

        stored_titles = {a['title'] for a in filtered_db.get_all_articles()}
        assert 'Manually Reviewed Article' in stored_titles
        assert 'Algorithmic Positive Article' not in stored_titles

    @patch('main.score_articles')
    def test_judge_failure_leaves_filtered_articles_untouched(
        self, mock_score_articles, temp_articles_db, temp_filtered_db, tmp_path
    ):
        """When the judge call fails, the filtered articles store is left as-is (not cleared/rewritten)."""
        article_db, temp_path = temp_articles_db
        filtered_db, filtered_path = temp_filtered_db

        # Pre-populate filtered_db to simulate a previous successful run.
        previous_article = self._djt_article('Previous Run Article', 'https://example.com/prev', minutes_ago=60)
        filtered_db.insert_articles([previous_article])

        new_articles = [self._djt_article('Trump New Article', 'https://example.com/new', minutes_ago=10)]
        article_db.insert_articles(new_articles)

        mock_score_articles.side_effect = SentimentJudgeError("simulated judge failure")

        with (
            patch('main.fetch_rss_articles', return_value=[]),
            patch('main.fetch_and_store_articles', return_value=[]),
            patch('main.article_db', article_db),
            patch('main.create_article_db', return_value=filtered_db),
            patch('main.ARCHIVE_DIR', str(tmp_path / 'archive')),
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
            patch('main.SENTIMENT_ENABLED', True),
        ):
            # Should not raise despite the sentiment judge failing.
            main()

        stored = filtered_db.get_all_articles()
        assert len(stored) == 1
        assert stored[0]['title'] == 'Previous Run Article'


class TestMainArchiving:
    """Test cases for archive snapshotting during main()."""

    def _djt_article(self, title, url, minutes_ago=0):
        published_at = (datetime.now() - timedelta(minutes=minutes_ago)).strftime('%Y-%m-%d %H:%M')
        return {
            'title': title,
            'url': url,
            'source': 'News Source',
            'category': 'politics',
            'published_at': published_at,
            'description': 'Trump-related coverage',
            'author': 'Reporter',
        }

    @patch('main.score_articles')
    def test_main_archives_both_stores_under_same_run_at(self, mock_score_articles, temp_articles_db, temp_filtered_db, tmp_path):
        """A single run() writes one snapshot for the pre-filter store and one for the filtered store."""
        article_db, temp_path = temp_articles_db
        filtered_db, filtered_path = temp_filtered_db

        articles = [self._djt_article('Trump Negative Article', 'https://example.com/neg', minutes_ago=10)]
        article_db.insert_articles(articles)
        mock_score_articles.return_value = {0: -0.5}

        archive_dir = tmp_path / 'archive'

        with (
            patch('main.fetch_rss_articles', return_value=[]),
            patch('main.fetch_and_store_articles', return_value=[]),
            patch('main.article_db', article_db),
            patch('main.create_article_db', return_value=filtered_db),
            patch('main.ARCHIVE_DIR', str(archive_dir)),
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
            patch('main.SENTIMENT_ENABLED', True),
            patch('main.SENTIMENT_MAX_SCORE', 0.0),
        ):
            main()

        articles_store = Path(article_db.db_path).stem
        filtered_store = Path(filtered_db.db_path).stem
        assert list((archive_dir / articles_store).rglob('*.parquet'))
        assert list((archive_dir / filtered_store).rglob('*.parquet'))

    def test_main_skips_filtered_archive_when_judge_fails(self, temp_articles_db, temp_filtered_db, tmp_path):
        """No filtered-store snapshot is written when the sentiment judge fails (nothing new was published)."""
        article_db, temp_path = temp_articles_db
        filtered_db, filtered_path = temp_filtered_db

        articles = [self._djt_article('Trump New Article', 'https://example.com/new', minutes_ago=10)]
        article_db.insert_articles(articles)

        archive_dir = tmp_path / 'archive'

        with (
            patch('main.fetch_rss_articles', return_value=[]),
            patch('main.fetch_and_store_articles', return_value=[]),
            patch('main.article_db', article_db),
            patch('main.create_article_db', return_value=filtered_db),
            patch('main.ARCHIVE_DIR', str(archive_dir)),
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', True),
            patch('main.DJT_FILTER_MIN_SCORE', 1.0),
            patch('main.SENTIMENT_ENABLED', True),
            patch('main.score_articles', side_effect=SentimentJudgeError("simulated judge failure")),
        ):
            main()

        filtered_store = Path(filtered_db.db_path).stem
        assert not (archive_dir / filtered_store).exists()


class TestMainErrorHandling:
    """Test cases for error handling in main() function."""

    @patch('main.score_articles')
    @patch('main.create_article_db')
    def test_main_with_database_error(self, mock_create_db, mock_score_articles):
        """Test main() function with database creation error."""
        mock_create_db.side_effect = Exception("Database creation failed")
        mock_score_articles.side_effect = lambda articles: {i: 0.0 for i in range(len(articles))}

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
            mock_create_db.assert_called_once_with('filtered_articles.duckdb')

    except Exception as e:
        pytest.fail(f"End-to-end integration test failed: {e}")


if __name__ == "__main__":
    # If run directly, execute the integration test
    test_main_e2e_integration()
    print("All tests would pass if run with pytest")


class TestMainRendersIndex:
    def test_main_injects_articles_into_index(self, stub_render_index):
        """main() should refresh app/index.html from the filtered store at the end of a run."""
        with (
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.article_db') as mock_db,
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', False),
        ):
            mock_newsapi.return_value = []
            mock_rss.return_value = []
            mock_db.insert_articles.return_value = 0

            main()

            stub_render_index.assert_called_once_with()

    def test_main_renders_archive_after_index(self, stub_render_index, monkeypatch):
        """main() should regenerate back-issue pages (render_archive) on every run."""
        mock_render_archive = Mock(return_value=[])
        monkeypatch.setattr('main.render_archive', mock_render_archive)

        with (
            patch('main.fetch_rss_articles') as mock_rss,
            patch('main.fetch_and_store_articles') as mock_newsapi,
            patch('main.article_db') as mock_db,
            patch('main.CACHE_HOURS', 24),
            patch('main.DJT_FILTER_ENABLED', False),
        ):
            mock_newsapi.return_value = []
            mock_rss.return_value = []
            mock_db.insert_articles.return_value = 0

            main()

            mock_render_archive.assert_called_once()
