#!/usr/bin/env python

import pytest
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.rss import RSSFeedParser, create_rss_parser, fetch_rss_articles


@pytest.fixture
def mock_feed_entry():
    """Fixture providing a mock RSS feed entry."""
    mock_entry = Mock()
    mock_entry.title = 'Test RSS Article Title'
    mock_entry.link = 'https://example.com/test-article'
    mock_entry.description = 'This is a test RSS article description'
    mock_entry.summary = 'This is a test RSS article summary'
    mock_entry.author = 'Test Author'

    # Mock published_parsed as a time struct
    test_time = time.struct_time((2025, 7, 8, 10, 30, 0, 0, 0, 0))
    mock_entry.published_parsed = test_time
    mock_entry.updated_parsed = test_time

    # Add get method to behave like a dict
    def get_method(key, default=None):
        return getattr(mock_entry, key, default)

    mock_entry.get = get_method
    return mock_entry


@pytest.fixture
def mock_feed_entry_minimal():
    """Fixture providing a minimal mock RSS feed entry."""
    mock_entry = Mock()
    mock_entry.title = 'Minimal RSS Article'
    mock_entry.link = 'https://example.com/minimal-article'
    mock_entry.published_parsed = None
    mock_entry.updated_parsed = None

    def get_method(key, default=None):
        if key == 'title':
            return mock_entry.title
        elif key == 'link':
            return mock_entry.link
        elif key in ['description', 'summary'] or key == 'author':
            return default
        return default

    mock_entry.get = get_method
    return mock_entry


@pytest.fixture
def mock_feed_entry_excluded():
    """Fixture providing a mock RSS feed entry with excluded URL."""
    mock_entry = Mock()
    mock_entry.title = 'Excluded Article'
    mock_entry.link = 'https://goodbullhunting.com/excluded-article'
    mock_entry.description = 'This article should be excluded'
    mock_entry.author = 'Excluded Author'

    test_time = time.struct_time((2025, 7, 8, 9, 0, 0, 0, 0, 0))
    mock_entry.published_parsed = test_time

    def get_method(key, default=None):
        return getattr(mock_entry, key, default)

    mock_entry.get = get_method
    return mock_entry


@pytest.fixture
def mock_feedparser_feed():
    """Fixture providing a mock feedparser feed object."""
    mock_feed = Mock()
    mock_feed.status = 200
    mock_feed.feed = Mock()
    mock_feed.feed.title = 'Test RSS Feed'
    mock_feed.feed.get = lambda key, default=None: getattr(mock_feed.feed, key, default)
    mock_feed.entries = []
    return mock_feed


@pytest.fixture
def sample_rss_feeds():
    """Fixture providing sample RSS feed URLs."""
    return ['https://example.com/feed1.xml', 'https://example.com/feed2.xml', 'https://test.com/rss.xml']


class TestRSSFeedParser:
    """Test cases for RSSFeedParser class."""

    def test_parser_initialization_default(self):
        """Test parser initialization with default exclude URLs."""
        parser = RSSFeedParser()
        assert parser.exclude_urls is not None
        assert isinstance(parser.exclude_urls, str)

    def test_parser_initialization_custom_exclude_urls(self):
        """Test parser initialization with custom exclude URLs."""
        custom_exclude = "test.com,example.org"
        parser = RSSFeedParser(exclude_urls=custom_exclude)
        assert parser.exclude_urls == custom_exclude

    def test_parse_feed_entry_success(self, mock_feed_entry):
        """Test successful parsing of RSS feed entry."""
        parser = RSSFeedParser(exclude_urls="")
        source = "Test Feed"

        article = parser.parse_feed_entry(mock_feed_entry, source)

        assert article is not None
        assert article['title'] == 'Test RSS Article Title'
        assert article['url'] == 'https://example.com/test-article'
        assert article['source'] == source
        assert article['category'] == 'politics'
        assert article['author'] == 'Test Author'
        assert article['description'] == 'This is a test RSS article description'
        assert 'published_at' in article
        assert article['published_at'] == '2025-07-08 10:30'

    def test_parse_feed_entry_minimal_data(self, mock_feed_entry_minimal):
        """Test parsing of RSS feed entry with minimal data."""
        parser = RSSFeedParser(exclude_urls="")
        source = "Minimal Feed"

        article = parser.parse_feed_entry(mock_feed_entry_minimal, source)

        assert article is not None
        assert article['title'] == 'Minimal RSS Article'
        assert article['url'] == 'https://example.com/minimal-article'
        assert article['source'] == source
        assert article['author'] == 'RSS Feed'  # Default author
        assert article['description'] == 'No description available.'  # Default description

    def test_parse_feed_entry_excluded_url(self, mock_feed_entry_excluded):
        """Test that excluded URLs are filtered out."""
        parser = RSSFeedParser(exclude_urls="goodbullhunting.com,queerty.com")
        source = "Test Feed"

        article = parser.parse_feed_entry(mock_feed_entry_excluded, source)

        assert article is None  # Should be excluded

    def test_parse_feed_entry_no_url(self):
        """Test handling of entry with no URL."""
        mock_entry = Mock()
        mock_entry.get = lambda key, default=None: None if key == 'link' else 'Test'

        parser = RSSFeedParser(exclude_urls="")
        article = parser.parse_feed_entry(mock_entry, "Test Feed")

        assert article is None

    def test_parse_feed_entry_exception_handling(self):
        """Test exception handling in parse_feed_entry."""
        mock_entry = Mock()
        mock_entry.get.side_effect = Exception("Test error")

        parser = RSSFeedParser(exclude_urls="")
        article = parser.parse_feed_entry(mock_entry, "Test Feed")

        assert article is None

    def test_extract_publication_date_published_parsed(self):
        """Test date extraction from published_parsed."""
        parser = RSSFeedParser()
        mock_entry = Mock()
        test_time = time.struct_time((2025, 7, 8, 14, 45, 30, 0, 0, 0))
        mock_entry.published_parsed = test_time
        mock_entry.updated_parsed = None

        result = parser._extract_publication_date(mock_entry)
        assert result == '2025-07-08 14:45'

    def test_extract_publication_date_updated_parsed(self):
        """Test date extraction from updated_parsed fallback."""
        parser = RSSFeedParser()
        mock_entry = Mock()
        mock_entry.published_parsed = None
        test_time = time.struct_time((2025, 7, 8, 16, 20, 15, 0, 0, 0))
        mock_entry.updated_parsed = test_time

        result = parser._extract_publication_date(mock_entry)
        assert result == '2025-07-08 16:20'

    def test_extract_publication_date_no_date_info(self):
        """Test date extraction when no date info is available."""
        parser = RSSFeedParser()
        mock_entry = Mock()
        mock_entry.published_parsed = None
        mock_entry.updated_parsed = None

        result = parser._extract_publication_date(mock_entry)

        # Should return current datetime in correct format
        assert isinstance(result, str)
        assert len(result) == 16  # 'YYYY-MM-DD HH:MM' format
        assert result[4] == '-' and result[7] == '-' and result[13] == ':'

    def test_extract_publication_date_exception_handling(self):
        """Test date extraction with malformed date data."""
        parser = RSSFeedParser()
        mock_entry = Mock()
        # Malformed time struct (not enough elements)
        mock_entry.published_parsed = (2025, 7)  # Invalid time struct
        mock_entry.updated_parsed = None

        result = parser._extract_publication_date(mock_entry)

        # Should fallback to current time
        assert isinstance(result, str)
        assert len(result) == 16

    @patch('utils.rss.feedparser.parse')
    def test_parse_feed_success(self, mock_feedparser, mock_feedparser_feed, mock_feed_entry):
        """Test successful parsing of RSS feed."""
        mock_feedparser_feed.entries = [mock_feed_entry]
        mock_feedparser.return_value = mock_feedparser_feed

        parser = RSSFeedParser(exclude_urls="")
        articles = parser.parse_feed('https://example.com/feed.xml')

        assert len(articles) == 1
        assert articles[0]['title'] == 'Test RSS Article Title'
        assert articles[0]['source'] == 'Test RSS Feed'

    @patch('utils.rss.feedparser.parse')
    def test_parse_feed_http_error(self, mock_feedparser, mock_feedparser_feed):
        """Test handling of HTTP errors when parsing feed."""
        mock_feedparser_feed.status = 404
        mock_feedparser.return_value = mock_feedparser_feed

        parser = RSSFeedParser()
        articles = parser.parse_feed('https://example.com/notfound.xml')

        assert len(articles) == 0

    @patch('utils.rss.feedparser.parse')
    def test_parse_feed_exception(self, mock_feedparser):
        """Test exception handling in parse_feed."""
        mock_feedparser.side_effect = Exception("Network error")

        parser = RSSFeedParser()
        articles = parser.parse_feed('https://example.com/error.xml')

        assert len(articles) == 0

    @patch('utils.rss.feedparser.parse')
    def test_parse_feed_no_status_attribute(self, mock_feedparser):
        """Test parsing feed without status attribute."""
        mock_feed = Mock()
        # No status attribute
        delattr(mock_feed, 'status') if hasattr(mock_feed, 'status') else None
        mock_feed.feed = Mock()
        mock_feed.feed.title = 'Test Feed'
        mock_feed.feed.get = lambda key, default=None: getattr(mock_feed.feed, key, default)
        mock_feed.entries = []
        mock_feedparser.return_value = mock_feed

        parser = RSSFeedParser()
        articles = parser.parse_feed('https://example.com/feed.xml')

        assert len(articles) == 0  # No entries, but should not error

    @patch('utils.rss.feedparser.parse')
    def test_parse_multiple_feeds_success(self, mock_feedparser):
        """Test parsing multiple RSS feeds."""

        # Create different mock entries for each feed to avoid duplicates
        def mock_parse_side_effect(url):
            mock_feed = Mock()
            mock_feed.status = 200
            mock_feed.feed = Mock()
            mock_feed.feed.title = f'Feed for {url}'
            mock_feed.feed.get = lambda key, default=None: getattr(mock_feed.feed, key, default)

            # Create unique entry for each feed
            mock_entry = Mock()
            if 'feed1' in url:
                mock_entry.title = 'Article from Feed 1'
                mock_entry.link = 'https://example.com/article-1'
            else:
                mock_entry.title = 'Article from Feed 2'
                mock_entry.link = 'https://example.com/article-2'

            mock_entry.description = f'Description for {url}'
            mock_entry.author = 'Test Author'
            mock_entry.published_parsed = time.struct_time((2025, 7, 8, 10, 30, 0, 0, 0, 0))
            mock_entry.get = lambda key, default=None: getattr(mock_entry, key, default)

            mock_feed.entries = [mock_entry]
            return mock_feed

        mock_feedparser.side_effect = mock_parse_side_effect

        parser = RSSFeedParser(exclude_urls="")
        feed_urls = ['https://example.com/feed1.xml', 'https://example.com/feed2.xml']
        articles = parser.parse_multiple_feeds(feed_urls)

        assert len(articles) == 2  # One article from each feed
        assert any('Feed 1' in article['title'] for article in articles)
        assert any('Feed 2' in article['title'] for article in articles)

    @patch('utils.rss.feedparser.parse')
    def test_parse_multiple_feeds_duplicate_removal(self, mock_feedparser, mock_feedparser_feed):
        """Test duplicate article removal in multiple feeds."""
        # Create two entries with same URL
        mock_entry1 = Mock()
        mock_entry1.title = 'Article 1'
        mock_entry1.link = 'https://example.com/same-article'
        mock_entry1.get = lambda key, default=None: getattr(mock_entry1, key, default)
        mock_entry1.published_parsed = None
        mock_entry1.updated_parsed = None

        mock_entry2 = Mock()
        mock_entry2.title = 'Article 2'
        mock_entry2.link = 'https://example.com/same-article'  # Same URL
        mock_entry2.get = lambda key, default=None: getattr(mock_entry2, key, default)
        mock_entry2.published_parsed = None
        mock_entry2.updated_parsed = None

        # Mock different feeds returning the same article
        def mock_parse_side_effect(url):
            mock_feed = Mock()
            mock_feed.status = 200
            mock_feed.feed = Mock()
            mock_feed.feed.title = f'Feed for {url}'
            mock_feed.feed.get = lambda key, default=None: getattr(mock_feed.feed, key, default)
            if 'feed1' in url:
                mock_feed.entries = [mock_entry1]
            else:
                mock_feed.entries = [mock_entry2]
            return mock_feed

        mock_feedparser.side_effect = mock_parse_side_effect

        parser = RSSFeedParser(exclude_urls="")
        feed_urls = ['https://example.com/feed1.xml', 'https://example.com/feed2.xml']
        articles = parser.parse_multiple_feeds(feed_urls)

        assert len(articles) == 1  # Duplicate should be removed

    def test_parse_multiple_feeds_empty_list(self):
        """Test parsing with empty feed list."""
        parser = RSSFeedParser()
        articles = parser.parse_multiple_feeds([])
        assert len(articles) == 0


class TestFetchRSSArticles:
    """Test cases for fetch_rss_articles function."""

    @patch('utils.rss.RSS_FEEDS', 'https://example.com/feed1.xml,https://example.com/feed2.xml')
    @patch('utils.rss.RSSFeedParser')
    def test_fetch_rss_articles_default_feeds(self, mock_parser_class):
        """Test fetching articles with default RSS feeds."""
        mock_parser = Mock()
        mock_parser.parse_multiple_feeds.return_value = [
            {'title': 'Article 1', 'url': 'https://example.com/1'},
            {'title': 'Article 2', 'url': 'https://example.com/2'},
        ]
        mock_parser_class.return_value = mock_parser

        articles = fetch_rss_articles()

        assert len(articles) == 2
        mock_parser_class.assert_called_once_with(exclude_urls=None)
        mock_parser.parse_multiple_feeds.assert_called_once()

    @patch('utils.rss.RSSFeedParser')
    def test_fetch_rss_articles_custom_feeds(self, mock_parser_class):
        """Test fetching articles with custom RSS feeds."""
        mock_parser = Mock()
        mock_parser.parse_multiple_feeds.return_value = [{'title': 'Custom Article', 'url': 'https://custom.com/1'}]
        mock_parser_class.return_value = mock_parser

        custom_feeds = 'https://custom.com/feed.xml'
        articles = fetch_rss_articles(rss_feeds=custom_feeds)

        assert len(articles) == 1
        mock_parser.parse_multiple_feeds.assert_called_once_with(['https://custom.com/feed.xml'])

    @patch('utils.rss.RSSFeedParser')
    def test_fetch_rss_articles_custom_exclude_urls(self, mock_parser_class):
        """Test fetching articles with custom exclude URLs."""
        mock_parser = Mock()
        mock_parser.parse_multiple_feeds.return_value = []
        mock_parser_class.return_value = mock_parser

        custom_exclude = 'spam.com,bad.org'
        custom_feeds = 'https://example.com/feed.xml'
        articles = fetch_rss_articles(rss_feeds=custom_feeds, exclude_urls=custom_exclude)

        mock_parser_class.assert_called_once_with(exclude_urls=custom_exclude)

    @patch('utils.rss.RSS_FEEDS', '')
    def test_fetch_rss_articles_no_feeds_configured(self):
        """Test behavior when no RSS feeds are configured."""
        articles = fetch_rss_articles(rss_feeds=None)  # Use None to trigger default RSS_FEEDS
        assert len(articles) == 0

    def test_fetch_rss_articles_no_valid_urls(self):
        """Test behavior when no valid URLs are provided."""
        articles = fetch_rss_articles(rss_feeds="  ,  ,  ")  # Only whitespace and commas
        assert len(articles) == 0

    @patch('utils.rss.RSS_FEEDS', '')
    def test_fetch_rss_articles_empty_default_feeds(self):
        """Test behavior when default RSS_FEEDS is empty."""
        articles = fetch_rss_articles()
        assert len(articles) == 0


class TestCreateRSSParser:
    """Test cases for create_rss_parser function."""

    def test_create_rss_parser_default(self):
        """Test creating RSS parser with default settings."""
        parser = create_rss_parser()
        assert isinstance(parser, RSSFeedParser)

    def test_create_rss_parser_custom_exclude_urls(self):
        """Test creating RSS parser with custom exclude URLs."""
        custom_exclude = "test.com,example.org"
        parser = create_rss_parser(exclude_urls=custom_exclude)
        assert isinstance(parser, RSSFeedParser)
        assert parser.exclude_urls == custom_exclude


class TestRSSIntegration:
    """Integration tests for RSS functionality."""

    @patch('utils.rss.feedparser.parse')
    def test_end_to_end_rss_processing(self, mock_feedparser):
        """Test complete end-to-end RSS processing."""
        # Mock feed with multiple entries
        mock_feed = Mock()
        mock_feed.status = 200
        mock_feed.feed = Mock()
        mock_feed.feed.title = 'Integration Test Feed'
        mock_feed.feed.get = lambda key, default=None: getattr(mock_feed.feed, key, default)

        # Create mock entries
        mock_entry1 = Mock()
        mock_entry1.title = 'Integration Article 1'
        mock_entry1.link = 'https://example.com/article1'
        mock_entry1.description = 'Test description 1'
        mock_entry1.author = 'Author 1'
        mock_entry1.published_parsed = time.struct_time((2025, 7, 8, 10, 0, 0, 0, 0, 0))
        mock_entry1.get = lambda key, default=None: getattr(mock_entry1, key, default)

        mock_entry2 = Mock()
        mock_entry2.title = 'Integration Article 2'
        mock_entry2.link = 'https://example.com/article2'
        mock_entry2.description = 'Test description 2'
        mock_entry2.author = 'Author 2'
        mock_entry2.published_parsed = time.struct_time((2025, 7, 8, 11, 0, 0, 0, 0, 0))
        mock_entry2.get = lambda key, default=None: getattr(mock_entry2, key, default)

        mock_feed.entries = [mock_entry1, mock_entry2]
        mock_feedparser.return_value = mock_feed

        # Test the integration
        parser = RSSFeedParser(exclude_urls="spam.com")
        articles = parser.parse_multiple_feeds(['https://example.com/feed.xml'])

        assert len(articles) == 2

        # Verify article structure
        for i, article in enumerate(articles, 1):
            assert 'title' in article
            assert 'url' in article
            assert 'source' in article
            assert 'category' in article
            assert 'published_at' in article
            assert 'description' in article
            assert 'author' in article
            assert article['category'] == 'politics'
            assert article['source'] == 'Integration Test Feed'
            assert f'Integration Article {i}' in article['title']

    @patch('utils.rss.feedparser.parse')
    def test_rss_feed_with_errors_and_valid_entries(self, mock_feedparser):
        """Test RSS feed processing with mixed valid and invalid entries."""
        mock_feed = Mock()
        mock_feed.status = 200
        mock_feed.feed = Mock()
        mock_feed.feed.title = 'Mixed Feed'
        mock_feed.feed.get = lambda key, default=None: getattr(mock_feed.feed, key, default)

        # Valid entry
        valid_entry = Mock()
        valid_entry.title = 'Valid Article'
        valid_entry.link = 'https://example.com/valid'
        valid_entry.description = 'Valid description'
        valid_entry.author = 'Valid Author'
        valid_entry.published_parsed = time.struct_time((2025, 7, 8, 12, 0, 0, 0, 0, 0))
        valid_entry.get = lambda key, default=None: getattr(valid_entry, key, default)

        # Invalid entry (no URL)
        invalid_entry = Mock()
        invalid_entry.title = 'Invalid Article'
        invalid_entry.link = ''  # No URL
        invalid_entry.get = lambda key, default=None: getattr(invalid_entry, key, default) if key != 'link' else ''

        # Excluded entry
        excluded_entry = Mock()
        excluded_entry.title = 'Excluded Article'
        excluded_entry.link = 'https://goodbullhunting.com/excluded'
        excluded_entry.get = lambda key, default=None: getattr(excluded_entry, key, default)

        mock_feed.entries = [valid_entry, invalid_entry, excluded_entry]
        mock_feedparser.return_value = mock_feed

        parser = RSSFeedParser(exclude_urls="goodbullhunting.com")
        articles = parser.parse_feed('https://example.com/mixed-feed.xml')

        assert len(articles) == 1  # Only valid entry should remain
        assert articles[0]['title'] == 'Valid Article'


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    def test_parse_feed_entry_with_none_entry(self):
        """Test handling of None entry."""
        parser = RSSFeedParser()
        article = parser.parse_feed_entry(None, "Test Feed")
        assert article is None

    @patch('utils.rss.feedparser.parse')
    def test_parse_feed_with_malformed_feed(self, mock_feedparser):
        """Test handling of malformed feed data."""
        # Mock feed without required attributes
        mock_feed = Mock()
        mock_feed.feed = None  # Missing feed data
        mock_feedparser.return_value = mock_feed

        parser = RSSFeedParser()
        articles = parser.parse_feed('https://example.com/malformed.xml')

        assert len(articles) == 0

    def test_extract_publication_date_with_invalid_time_struct(self):
        """Test date extraction with various invalid time structures."""
        parser = RSSFeedParser()
        mock_entry = Mock()

        # Test with None values
        mock_entry.published_parsed = None
        mock_entry.updated_parsed = None
        result = parser._extract_publication_date(mock_entry)
        assert isinstance(result, str)

        # Test with invalid time struct
        mock_entry.published_parsed = "not a time struct"
        result = parser._extract_publication_date(mock_entry)
        assert isinstance(result, str)

    def test_feed_url_filtering_edge_cases(self):
        """Test URL filtering with various edge cases."""
        parser = RSSFeedParser(exclude_urls="EXAMPLE.COM,test.org")  # Test case sensitivity

        mock_entry = Mock()
        mock_entry.title = 'Test Article'
        mock_entry.link = 'https://Example.Com/article'  # Mixed case
        mock_entry.get = lambda key, default=None: getattr(mock_entry, key, default)

        article = parser.parse_feed_entry(mock_entry, "Test Feed")
        assert article is None  # Should be excluded due to case-insensitive matching


def test_rss_integration():
    """Integration test that validates the complete RSS workflow."""
    try:
        # Create a parser with test settings
        parser = RSSFeedParser(exclude_urls="spam.com,bad.org")

        # Test with mock data to avoid hitting real RSS feeds
        with patch('utils.rss.feedparser.parse') as mock_feedparser:
            # Mock a successful RSS feed
            mock_feed = Mock()
            mock_feed.status = 200
            mock_feed.feed = Mock()
            mock_feed.feed.title = 'Integration Test RSS Feed'
            mock_feed.feed.get = lambda key, default=None: getattr(mock_feed.feed, key, default)

            # Create a mock article entry
            mock_entry = Mock()
            mock_entry.title = 'Integration Test RSS Article'
            mock_entry.link = 'https://example.com/integration-test-rss'
            mock_entry.description = 'This is a test RSS article for integration testing'
            mock_entry.author = 'RSS Integration Test Author'
            mock_entry.published_parsed = time.struct_time((2025, 7, 8, 13, 45, 0, 0, 0, 0))
            mock_entry.get = lambda key, default=None: getattr(mock_entry, key, default)

            mock_feed.entries = [mock_entry]
            mock_feedparser.return_value = mock_feed

            # Test parsing a single feed
            articles = parser.parse_feed('https://example.com/test-feed.xml')

            assert len(articles) == 1
            assert articles[0]['title'] == 'Integration Test RSS Article'
            assert articles[0]['source'] == 'Integration Test RSS Feed'
            assert articles[0]['category'] == 'politics'
            assert articles[0]['published_at'] == '2025-07-08 13:45'

            # Test parsing multiple feeds with different mock data
            def mock_parse_side_effect_integration(url):
                mock_feed_int = Mock()
                mock_feed_int.status = 200
                mock_feed_int.feed = Mock()
                mock_feed_int.feed.title = f'Integration Feed for {url}'
                mock_feed_int.feed.get = lambda key, default=None: getattr(mock_feed_int.feed, key, default)

                mock_entry_int = Mock()
                if 'feed1' in url:
                    mock_entry_int.title = 'Integration Article 1'
                    mock_entry_int.link = 'https://example.com/int-article-1'
                else:
                    mock_entry_int.title = 'Integration Article 2'
                    mock_entry_int.link = 'https://example.com/int-article-2'

                mock_entry_int.description = f'Integration description for {url}'
                mock_entry_int.author = 'Integration Author'
                mock_entry_int.published_parsed = time.struct_time((2025, 7, 8, 14, 0, 0, 0, 0, 0))
                mock_entry_int.get = lambda key, default=None: getattr(mock_entry_int, key, default)

                mock_feed_int.entries = [mock_entry_int]
                return mock_feed_int

            mock_feedparser.side_effect = mock_parse_side_effect_integration
            feed_urls = ['https://example.com/feed1.xml', 'https://example.com/feed2.xml']
            multiple_articles = parser.parse_multiple_feeds(feed_urls)

            assert len(multiple_articles) == 2  # One from each feed

            # Test the convenience function with its own mock
            def mock_parse_convenience(url):
                mock_conv_feed = Mock()
                mock_conv_feed.status = 200
                mock_conv_feed.feed = Mock()
                mock_conv_feed.feed.title = 'Convenience Test Feed'
                mock_conv_feed.feed.get = lambda key, default=None: getattr(mock_conv_feed.feed, key, default)

                mock_conv_entry = Mock()
                mock_conv_entry.title = 'Convenience Test Article'
                mock_conv_entry.link = 'https://example.com/convenience-test'
                mock_conv_entry.description = 'Convenience test description'
                mock_conv_entry.author = 'Convenience Author'
                mock_conv_entry.published_parsed = time.struct_time((2025, 7, 8, 15, 0, 0, 0, 0, 0))
                mock_conv_entry.get = lambda key, default=None: getattr(mock_conv_entry, key, default)

                mock_conv_feed.entries = [mock_conv_entry]
                return mock_conv_feed

            with (
                patch('utils.rss.RSS_FEEDS', 'https://example.com/test.xml'),
                patch('utils.rss.feedparser.parse', mock_parse_convenience),
            ):
                convenience_articles = fetch_rss_articles()
                assert len(convenience_articles) == 1
                assert convenience_articles[0]['title'] == 'Convenience Test Article'

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


class TestParseFeedRetry:
    """Test retry and graceful degradation in RSS feed parsing."""

    @patch('utils.retry.time.sleep')
    @patch('utils.rss.feedparser.parse')
    def test_parse_multiple_feeds_skips_failing_feed_continues_to_next(self, mock_feedparser, mock_sleep):
        """Feed raising exception after all retries is skipped; pipeline returns articles from remaining feeds."""
        good_feed = Mock()
        good_feed.status = 200
        good_feed.feed = Mock()
        good_feed.feed.title = 'Good Feed'
        good_feed.feed.get = lambda key, default=None: getattr(good_feed.feed, key, default)

        entry = Mock()
        entry.title = 'Good Article'
        entry.link = 'https://example.com/good-article'
        entry.description = 'Good description'
        entry.author = 'Test Author'
        entry.published_parsed = time.struct_time((2025, 7, 8, 10, 30, 0, 0, 0, 0))
        entry.get = lambda key, default=None: getattr(entry, key, default)
        good_feed.entries = [entry]

        def parse_side_effect(url):
            if 'failing' in url:
                raise Exception("connection refused")
            return good_feed

        mock_feedparser.side_effect = parse_side_effect

        parser = RSSFeedParser(exclude_urls="")
        articles = parser.parse_multiple_feeds(['https://failing.com/feed', 'https://good.com/feed'])

        assert len(articles) == 1
        assert articles[0]['title'] == 'Good Article'

    @patch('utils.retry.time.sleep')
    @patch('utils.rss.feedparser.parse')
    def test_parse_feed_retries_on_503_then_returns_empty_on_exhaustion(self, mock_feedparser, mock_sleep):
        """Feed returning 503 after all retries is treated as unavailable; parse_feed returns empty list."""
        bad_feed = Mock()
        bad_feed.status = 503
        bad_feed.feed = Mock()
        bad_feed.feed.get = lambda key, default=None: default
        bad_feed.entries = []
        mock_feedparser.return_value = bad_feed

        parser = RSSFeedParser(exclude_urls="")
        articles = parser.parse_feed('https://example.com/unavailable.xml')

        assert articles == []
        assert mock_feedparser.call_count == 4  # initial + 3 retries


if __name__ == "__main__":
    # If run directly, execute the integration test
    test_rss_integration()
    print("All tests would pass if run with pytest")
