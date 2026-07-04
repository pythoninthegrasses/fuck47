#!/usr/bin/env python

"""Single-URL fetch + metadata extraction for manual article ingestion (see cli.py add-article)."""

import trafilatura
from curl_cffi import requests as creq


class ScrapeError(Exception):
    """Raised when a URL cannot be fetched."""


def fetch_html(url, proxy=None, timeout=20):
    """Fetch a URL with a Chrome TLS fingerprint, returning the response body as text."""
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    try:
        response = creq.get(url, impersonate='chrome', timeout=timeout, proxies=proxies)
        response.raise_for_status()
    except Exception as e:
        raise ScrapeError(f"Failed to fetch {url}: {e}") from e
    return response.text


def extract_metadata(html, url):
    """Extract title, description, and published_at (YYYY-MM-DD) from HTML via trafilatura."""
    meta = trafilatura.extract_metadata(html, default_url=url)
    if meta is None:
        return {'title': None, 'description': None, 'published_at': None}
    return {
        'title': meta.title,
        'description': meta.description,
        'published_at': meta.date,
    }
