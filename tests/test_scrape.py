#!/usr/bin/env python

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.scrape import ScrapeError, extract_metadata, fetch_html


class TestFetchHtml:
    @patch('utils.scrape.creq.get')
    def test_returns_response_text(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text='<html>ok</html>')

        html = fetch_html('https://example.com/a')

        assert html == '<html>ok</html>'
        mock_get.assert_called_once()
        assert mock_get.call_args.kwargs.get('impersonate') == 'chrome'

    @patch('utils.scrape.creq.get')
    def test_threads_proxy_through(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text='<html>ok</html>')

        fetch_html('https://example.com/a', proxy='http://localhost:8080')

        assert mock_get.call_args.kwargs.get('proxies') == {
            'http': 'http://localhost:8080',
            'https': 'http://localhost:8080',
        }

    @patch('utils.scrape.creq.get')
    def test_request_exception_raises_scrape_error(self, mock_get):
        mock_get.side_effect = RuntimeError("boom")

        with pytest.raises(ScrapeError):
            fetch_html('https://example.com/a')


class TestExtractMetadata:
    def test_extracts_title_description_and_date(self):
        html = """
        <html><head>
        <meta property="og:title" content="Some Headline">
        <meta property="og:description" content="Some summary text.">
        <meta property="article:published_time" content="2026-07-01T12:00:00Z">
        </head><body><p>Body text goes here and is long enough to be extracted properly by trafilatura for sure.</p></body></html>
        """

        meta = extract_metadata(html, url='https://example.com/a')

        assert meta['title'] == 'Some Headline'
        assert meta['description'] == 'Some summary text.'
        assert meta['published_at'] == '2026-07-01'

    def test_missing_fields_are_none(self):
        html = "<html><head></head><body><p>no metadata here</p></body></html>"

        meta = extract_metadata(html, url='https://example.com/a')

        assert meta['title'] is None
        assert meta['description'] is None
        assert meta['published_at'] is None
