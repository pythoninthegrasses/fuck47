#!/usr/bin/env python

import functools
import requests
import requests_cache
from config import (
    CACHE_HOURS,
    CACHE_SESSION,
    CATEGORIES,
    EVERYTHING,
    EXCLUDE_DOMAINS,
    EXCLUDE_URLS,
    NEWS_API_KEY as API_KEY,
    PAGE_SIZE,
    RATE_LIMIT_INTERVAL_SEC,
    RATE_LIMIT_REQUESTS,
    TOP_HEADLINES,
    TTL,
)
from datetime import datetime, timedelta
from dateutil import parser
from eliot import log_message
from urllib.parse import urlencode
from utils.ratelimit import RateLimiter
from utils.retry import http_request_with_retry

# Initialize session
SESSION = requests.Session()
SESSION.headers.update({'Authorization': API_KEY})

RATE_LIMITER = RateLimiter(max_requests=RATE_LIMIT_REQUESTS, interval_sec=RATE_LIMIT_INTERVAL_SEC)


# Cache for legitimate news sources
legitimate_sources = set()


def fetch_legitimate_sources():
    """Fetch legitimate news sources from NewsAPI sources endpoint"""
    global legitimate_sources

    if legitimate_sources:  # Return cached sources if already fetched
        return legitimate_sources

    sources_url = "https://newsapi.org/v2/sources"
    query_params = {'apiKey': API_KEY, 'language': 'en', 'country': 'us'}

    try:
        RATE_LIMITER.acquire()
        response = SESSION.get(sources_url, params=query_params)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                # Extract source names from the response
                sources = data.get('sources', [])
                legitimate_sources = {source['name'] for source in sources}
                print(f"Fetched {len(legitimate_sources)} legitimate news sources")
                return legitimate_sources
        else:
            print(f"Error fetching sources: {response.status_code}")
    except Exception as e:
        print(f"Error fetching legitimate sources: {e}")

    # Return empty set if fetch fails
    return set()


def fetch_and_store_articles(article_db, page=1):
    """Fetch articles from API and store in database"""
    all_articles = []
    seen_urls = set()

    for category in CATEGORIES:
        query_params = {
            'apiKey': API_KEY,
            'excludeDomains': EXCLUDE_DOMAINS,
            'category': category,
            'country': 'us',
            'pageSize': str(PAGE_SIZE),
            'page': str(page),
        }
        url = TOP_HEADLINES + '?' + urlencode(query_params)

        try:
            RATE_LIMITER.acquire()
            response = http_request_with_retry(lambda: SESSION.get(url))
            print(f"API Response for {category}: {response.status_code}")

            if response.status_code != 200:
                log_message(message_type="api_error", category=category, status_code=response.status_code)
                continue

            data = response.json()
            parsed_articles = parse_articles(data, seen_urls, category)
            print(f"Parsed {len(parsed_articles)} articles for {category}")

            stored_count = 0
            for article in parsed_articles:
                # Check if article already exists by URL
                if article_db.insert_article(article):
                    stored_count += 1
                    all_articles.append(article)

            print(f"Stored {stored_count} articles for {category}")

            if not parsed_articles:
                log_message(message_type="no_articles", category=category)

        except Exception as e:
            print(f"Error fetching {category}: {str(e)}")
            log_message(message_type="api_error", category=category, error=str(e))
            continue

    print(f"Total articles fetched and stored: {len(all_articles)}")
    return all_articles


@functools.lru_cache(maxsize=1)
def get_cached_articles(article_db, category: str = None):
    """Get articles from database cache, fetching from API if needed"""
    if category:
        cached_articles = article_db.search_by_category(category)
    else:
        cached_articles = article_db.get_all_articles()

    if not cached_articles:
        print("Cache miss - fetching from API")
        articles = fetch_and_store_articles(article_db)
        if articles:
            if category:
                cached_articles = article_db.search_by_category(category)
            else:
                cached_articles = article_db.get_all_articles()
        else:
            print("No articles fetched from API")
            return []

    print(f"Returning {len(cached_articles)} articles")

    return cached_articles


def parse_articles(response: dict, seen_urls: set, category: str) -> list:
    """
    Parses the response from the API and returns a list
    of dictionaries with the article information, filtered by legitimate sources and excluded domains
    """
    parsed_articles = []
    exclude_urls_lower = [url.lower() for url in EXCLUDE_URLS.split(',')]
    exclude_domains_lower = [domain.lower() for domain in EXCLUDE_DOMAINS.split(',')]
    legit_sources = fetch_legitimate_sources()

    if response.get('status') == 'ok':
        for article in response.get('articles', []):
            url = article['url'].lower()
            if url not in seen_urls and url not in exclude_urls_lower:
                seen_urls.add(url)
                source = article['source']['name'] if isinstance(article['source'], dict) else article['source']

                # Check if source is in excluded domains FIRST (case-insensitive)
                source_lower = source.lower()
                # Map common source names to their domain equivalents
                source_domain_map = {
                    'abc news': 'abc-news',
                    'cbs news': 'cbs-news',
                    'cnn': 'cnn',
                    'fox news': 'fox-news',
                    'msnbc': 'msnbc',
                    'nbc news': 'nbc-news',
                    'newsweek': 'newsweek',
                    'breitbart news': 'breitbart-news',
                    'espn': 'espn',
                    'mtv news': 'mtv-news',
                    'the huffington post': 'the-huffington-post',
                    'new york post': 'new-york-post',
                    'the washington times': 'the-washington-times',
                    'the american conservative': 'the-american-conservative',
                    'national review': 'national-review',
                    'google news': 'google-news',
                }

                # Check if source maps to an excluded domain
                mapped_domain = source_domain_map.get(source_lower)
                if mapped_domain and mapped_domain in exclude_domains_lower:
                    continue

                # Also check direct string matching
                if any(excluded_domain in source_lower for excluded_domain in exclude_domains_lower):
                    continue

                # Filter by legitimate sources (only after exclusion check)
                if source not in legit_sources:
                    continue

                # Check if URL contains excluded domains
                if any(excluded_domain in url for excluded_domain in exclude_domains_lower):
                    continue

                if (
                    article['title'] != '[Removed]'
                    and source.lower() != 'removed'
                    and url != 'https://removed.com'
                    and article['publishedAt'] != '1970-01-01T00:00:00Z'
                ):
                    parsed_articles.append(
                        {
                            'published_at': parser.isoparse(article['publishedAt']).strftime('%Y-%m-%d %H:%M'),
                            'title': article['title'],
                            'description': article.get('description') or "No description available.",
                            'url': url,
                            'source': source,
                            'category': category,
                            'author': article.get('author', 'Unknown Author'),
                        }
                    )

    return parsed_articles
