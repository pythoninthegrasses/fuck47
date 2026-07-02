#!/usr/bin/env python

import requests
import time

TRANSIENT_HTTP_CODES = frozenset({429, 500, 502, 503, 504})


def http_request_with_retry(fn, *, max_retries=3, base_delay=1.0, backoff_factor=2.0):
    """Call fn() retrying on transient HTTP errors and network exceptions.

    Returns the response on success or after exhausting retries on bad status.
    Raises the last exception after exhausting retries on connection/timeout errors.
    """
    delay = base_delay
    last_response = None

    for attempt in range(max_retries + 1):
        try:
            response = fn()
            last_response = response
            if response.status_code not in TRANSIENT_HTTP_CODES:
                return response
            if attempt < max_retries:
                print(f"Transient HTTP {response.status_code}, retrying (attempt {attempt + 1}/{max_retries}) after {delay}s")
                time.sleep(delay)
                delay *= backoff_factor
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt < max_retries:
                print(f"Network error, retrying (attempt {attempt + 1}/{max_retries}) after {delay}s: {exc}")
                time.sleep(delay)
                delay *= backoff_factor
            else:
                raise

    return last_response


def feed_with_retry(fn, *, max_retries=3, base_delay=1.0, backoff_factor=2.0):
    """Call fn() (returning a feedparser result) retrying on transient failures.

    Returns the feed on success or after exhausting retries on bad status.
    Raises the last exception after exhausting retries on errors.
    """
    delay = base_delay
    last_feed = None

    for attempt in range(max_retries + 1):
        try:
            feed = fn()
            last_feed = feed
            status = getattr(feed, "status", None)
            if status is None or status not in TRANSIENT_HTTP_CODES:
                return feed
            if attempt < max_retries:
                print(f"Transient HTTP {status} for feed, retrying (attempt {attempt + 1}/{max_retries}) after {delay}s")
                time.sleep(delay)
                delay *= backoff_factor
        except Exception as exc:
            if attempt < max_retries:
                print(f"Feed error, retrying (attempt {attempt + 1}/{max_retries}) after {delay}s: {exc}")
                time.sleep(delay)
                delay *= backoff_factor
            else:
                raise

    return last_feed
