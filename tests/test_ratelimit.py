#!/usr/bin/env python

import sys
from pathlib import Path
from unittest.mock import call, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.ratelimit import RateLimiter


class TestRateLimiter:
    @patch('utils.ratelimit.time.sleep')
    @patch('utils.ratelimit.time.monotonic')
    def test_allows_requests_under_limit_without_sleeping(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0, 1, 2]
        limiter = RateLimiter(max_requests=3, interval_sec=10)
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        mock_sleep.assert_not_called()

    @patch('utils.ratelimit.time.sleep')
    @patch('utils.ratelimit.time.monotonic')
    def test_sleeps_when_limit_exceeded_within_interval(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0, 1, 2, 10]
        limiter = RateLimiter(max_requests=2, interval_sec=10)
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        mock_sleep.assert_called_once_with(8)

    @patch('utils.ratelimit.time.sleep')
    @patch('utils.ratelimit.time.monotonic')
    def test_no_sleep_when_prior_requests_outside_interval(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0, 10]
        limiter = RateLimiter(max_requests=1, interval_sec=5)
        limiter.acquire()
        limiter.acquire()
        mock_sleep.assert_not_called()

    @patch('utils.ratelimit.time.sleep')
    @patch('utils.ratelimit.time.monotonic')
    def test_evicts_expired_timestamps_after_sleep(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0, 1, 2, 10, 11]
        limiter = RateLimiter(max_requests=2, interval_sec=10)
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        assert mock_sleep.call_args_list == [call(8)]
        assert len(limiter._timestamps) == 2
