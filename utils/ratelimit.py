#!/usr/bin/env python

import time
from collections import deque


class RateLimiter:
    """Sliding-window rate limiter: acquire() blocks until under max_requests per interval_sec."""

    def __init__(self, max_requests, interval_sec):
        self.max_requests = max_requests
        self.interval_sec = interval_sec
        self._timestamps = deque()

    def acquire(self):
        now = time.monotonic()
        self._evict(now)

        if len(self._timestamps) >= self.max_requests:
            sleep_time = self.interval_sec - (now - self._timestamps[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                now = time.monotonic()
                self._evict(now)

        self._timestamps.append(now)

    def _evict(self, now):
        while self._timestamps and now - self._timestamps[0] >= self.interval_sec:
            self._timestamps.popleft()
