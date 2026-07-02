#!/usr/bin/env python

import pytest
import requests
import sys
from pathlib import Path
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.retry import TRANSIENT_HTTP_CODES, feed_with_retry, http_request_with_retry


def _make_response(status_code):
    r = Mock()
    r.status_code = status_code
    return r


def _make_feed(status=200):
    f = Mock()
    f.status = status
    f.feed = Mock()
    f.feed.get = Mock(return_value='Test Feed')
    f.entries = []
    return f


class TestHttpRequestWithRetry:
    @patch('utils.retry.time.sleep')
    def test_returns_immediately_on_200(self, mock_sleep):
        fn = Mock(return_value=_make_response(200))
        result = http_request_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status_code == 200
        fn.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_no_retry_on_404(self, mock_sleep):
        fn = Mock(return_value=_make_response(404))
        result = http_request_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status_code == 404
        fn.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_no_retry_on_400(self, mock_sleep):
        fn = Mock(return_value=_make_response(400))
        result = http_request_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status_code == 400
        fn.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_retries_on_503_then_succeeds(self, mock_sleep):
        fn = Mock(side_effect=[_make_response(503), _make_response(503), _make_response(200)])
        result = http_request_with_retry(fn, max_retries=3, base_delay=1.0, backoff_factor=2.0)
        assert result.status_code == 200
        assert fn.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('utils.retry.time.sleep')
    def test_retries_on_429_then_succeeds(self, mock_sleep):
        fn = Mock(side_effect=[_make_response(429), _make_response(200)])
        result = http_request_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status_code == 200
        assert fn.call_count == 2

    @patch('utils.retry.time.sleep')
    def test_retries_on_connection_error_then_succeeds(self, mock_sleep):
        fn = Mock(side_effect=[requests.ConnectionError("refused"), _make_response(200)])
        result = http_request_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status_code == 200
        assert fn.call_count == 2

    @patch('utils.retry.time.sleep')
    def test_retries_on_timeout_then_succeeds(self, mock_sleep):
        fn = Mock(side_effect=[requests.Timeout("timed out"), _make_response(200)])
        result = http_request_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status_code == 200
        assert fn.call_count == 2

    @patch('utils.retry.time.sleep')
    def test_returns_last_bad_response_after_max_retries(self, mock_sleep):
        fn = Mock(return_value=_make_response(503))
        result = http_request_with_retry(fn, max_retries=2, base_delay=1.0)
        assert result.status_code == 503
        assert fn.call_count == 3  # initial + 2 retries

    @patch('utils.retry.time.sleep')
    def test_raises_connection_error_after_max_retries(self, mock_sleep):
        fn = Mock(side_effect=requests.ConnectionError("refused"))
        with pytest.raises(requests.ConnectionError):
            http_request_with_retry(fn, max_retries=2, base_delay=1.0)
        assert fn.call_count == 3

    @patch('utils.retry.time.sleep')
    def test_backoff_delay_doubles(self, mock_sleep):
        fn = Mock(side_effect=[requests.ConnectionError(), requests.ConnectionError(), _make_response(200)])
        http_request_with_retry(fn, max_retries=3, base_delay=1.0, backoff_factor=2.0)
        assert mock_sleep.call_args_list == [call(1.0), call(2.0)]

    def test_transient_http_codes_contains_expected_codes(self):
        assert 429 in TRANSIENT_HTTP_CODES
        assert 500 in TRANSIENT_HTTP_CODES
        assert 502 in TRANSIENT_HTTP_CODES
        assert 503 in TRANSIENT_HTTP_CODES
        assert 504 in TRANSIENT_HTTP_CODES
        assert 200 not in TRANSIENT_HTTP_CODES
        assert 404 not in TRANSIENT_HTTP_CODES


class TestFeedWithRetry:
    @patch('utils.retry.time.sleep')
    def test_returns_immediately_on_200(self, mock_sleep):
        fn = Mock(return_value=_make_feed(200))
        result = feed_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status == 200
        fn.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_no_retry_on_404(self, mock_sleep):
        fn = Mock(return_value=_make_feed(404))
        result = feed_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status == 404
        fn.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_no_retry_on_feed_without_status_attribute(self, mock_sleep):
        feed = Mock(spec=[])  # no attributes
        fn = Mock(return_value=feed)
        result = feed_with_retry(fn, max_retries=3, base_delay=1.0)
        fn.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_retries_on_503_then_succeeds(self, mock_sleep):
        fn = Mock(side_effect=[_make_feed(503), _make_feed(503), _make_feed(200)])
        result = feed_with_retry(fn, max_retries=3, base_delay=1.0, backoff_factor=2.0)
        assert result.status == 200
        assert fn.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('utils.retry.time.sleep')
    def test_retries_on_exception_then_succeeds(self, mock_sleep):
        fn = Mock(side_effect=[Exception("connection error"), _make_feed(200)])
        result = feed_with_retry(fn, max_retries=3, base_delay=1.0)
        assert result.status == 200
        assert fn.call_count == 2

    @patch('utils.retry.time.sleep')
    def test_returns_last_bad_feed_after_max_retries(self, mock_sleep):
        fn = Mock(return_value=_make_feed(503))
        result = feed_with_retry(fn, max_retries=2, base_delay=1.0)
        assert result.status == 503
        assert fn.call_count == 3

    @patch('utils.retry.time.sleep')
    def test_raises_after_max_retries_on_exception(self, mock_sleep):
        fn = Mock(side_effect=Exception("network error"))
        with pytest.raises(Exception, match="network error"):
            feed_with_retry(fn, max_retries=2, base_delay=1.0)
        assert fn.call_count == 3

    @patch('utils.retry.time.sleep')
    def test_backoff_delay_doubles(self, mock_sleep):
        fn = Mock(side_effect=[Exception("err"), Exception("err"), _make_feed(200)])
        feed_with_retry(fn, max_retries=3, base_delay=1.0, backoff_factor=2.0)
        assert mock_sleep.call_args_list == [call(1.0), call(2.0)]
