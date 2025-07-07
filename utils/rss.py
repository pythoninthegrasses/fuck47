#!/usr/bin/env python

import feedparser
from config import EXCLUDE_URLS, RSS_FEEDS
from datetime import datetime


class RSSFeedParser:
    """RSS feed parser for extracting articles from RSS feeds"""

    def __init__(self, exclude_urls=None):
        self.exclude_urls = exclude_urls or EXCLUDE_URLS

    def parse_feed_entry(self, entry, source):
        """Parse a single RSS feed entry into an article dictionary"""
        try:
            # Extract article data using feedparser's normalized fields
            title = entry.get('title', 'No title')
            url = entry.get('link', '')

            if not url:
                return None

            # Check exclusions
            exclude_urls_lower = [u.lower() for u in self.exclude_urls.split(',')]
            url_lower = url.lower()
            if any(excluded_url in url_lower for excluded_url in exclude_urls_lower):
                return None

            # Extract description (feedparser handles multiple formats)
            description = entry.get('description', entry.get('summary', 'No description available.'))

            # Extract publication date (feedparser handles date parsing)
            published_at = self._extract_publication_date(entry)

            # Extract author (feedparser handles multiple formats)
            author = entry.get('author', 'RSS Feed')

            article = {
                'published_at': published_at,
                'title': title,
                'description': description,
                'url': url,
                'source': source,
                'category': 'politics',
                'author': author,
            }

            return article

        except Exception as e:
            print(f"Error parsing RSS item: {e}")
            return None

    def _extract_publication_date(self, entry):
        """Extract and format publication date from RSS entry"""
        # Extract publication date (feedparser handles date parsing)
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                # Convert time struct to datetime
                pub_datetime = datetime(*entry.published_parsed[:6])
                return pub_datetime.strftime('%Y-%m-%d %H:%M')
            except:
                return datetime.now().strftime('%Y-%m-%d %H:%M')
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                # Fallback to updated time
                pub_datetime = datetime(*entry.updated_parsed[:6])
                return pub_datetime.strftime('%Y-%m-%d %H:%M')
            except:
                return datetime.now().strftime('%Y-%m-%d %H:%M')
        else:
            return datetime.now().strftime('%Y-%m-%d %H:%M')

    def parse_feed(self, rss_url):
        """Parse a single RSS feed and return list of articles"""
        articles = []

        try:
            print(f"Fetching RSS feed: {rss_url}")

            # Use feedparser to parse the RSS feed
            feed = feedparser.parse(rss_url)

            # Check if feed was successfully parsed
            if hasattr(feed, 'status') and feed.status != 200:
                print(f"Error fetching RSS feed {rss_url}: HTTP {feed.status}")
                return articles

            # Get feed title for source
            source = feed.feed.get('title', 'RSS Feed')

            for entry in feed.entries:
                article = self.parse_feed_entry(entry, source)
                if article:
                    articles.append(article)

        except Exception as e:
            print(f"Error processing RSS feed {rss_url}: {e}")

        return articles

    def parse_multiple_feeds(self, feed_urls):
        """Parse multiple RSS feeds and return combined list of articles"""
        all_articles = []
        seen_urls = set()

        for rss_url in feed_urls:
            feed_articles = self.parse_feed(rss_url)

            # Deduplicate articles by URL
            for article in feed_articles:
                url_lower = article['url'].lower()
                if url_lower not in seen_urls:
                    seen_urls.add(url_lower)
                    all_articles.append(article)

        return all_articles


def fetch_rss_articles(rss_feeds=None, exclude_urls=None):
    """Fetch articles from RSS feeds with caching"""
    feeds = rss_feeds or RSS_FEEDS

    if not feeds:
        print("No RSS feeds configured")
        return []

    rss_urls = [url.strip() for url in feeds.split(',') if url.strip()]

    if not rss_urls:
        print("No valid RSS feed URLs found")
        return []

    parser = RSSFeedParser(exclude_urls=exclude_urls)
    articles = parser.parse_multiple_feeds(rss_urls)

    print(f"Fetched {len(articles)} articles from RSS feeds")
    return articles


def create_rss_parser(exclude_urls=None):
    """Create and return an RSSFeedParser instance"""
    return RSSFeedParser(exclude_urls=exclude_urls)
