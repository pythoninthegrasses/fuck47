#!/usr/bin/env python

import requests_cache
import sys
from config import CACHE_HOURS, CACHE_SESSION, DJT_FILTER_ENABLED, DJT_FILTER_MIN_SCORE, TTL
from eliot import to_file
from utils.db import create_article_db
from utils.filter import DJTNewsFilter
from utils.newsapi import fetch_and_store_articles
from utils.rss import fetch_rss_articles

to_file(sys.stdout)

if CACHE_SESSION:
    requests_cache.install_cache(cache_name='newsapi_cache', backend='sqlite', expire_after=TTL, allowable_codes=(200,))

article_db = create_article_db('articles.json')


def main():
    """Fetch and store articles from NewsAPI and RSS feeds."""
    article_db.clear_old_articles(hours=CACHE_HOURS)

    # Fetch and store articles from NewsAPI
    articles = fetch_and_store_articles(article_db)
    print(f"Fetched and stored {len(articles)} articles from NewsAPI")

    # Fetch and store articles from RSS feeds
    rss_articles = fetch_rss_articles()
    stored_rss_count = article_db.insert_articles(rss_articles)
    print(f"Stored {stored_rss_count} new articles from RSS feeds")

    # Apply DJT filtering if enabled and create filtered_articles.json
    if DJT_FILTER_ENABLED:
        djt_filter = DJTNewsFilter(min_score=DJT_FILTER_MIN_SCORE)
        
        # Get all articles from database
        all_articles = article_db.get_all_articles()
        print(f"Total articles before filtering: {len(all_articles)}")
        
        # Filter for DJT-related articles
        djt_articles = djt_filter.filter_articles(all_articles)
        print(f"DJT-related articles: {len(djt_articles)}")
        
        # Create filtered articles database
        filtered_db = create_article_db('filtered_articles.json')
        filtered_db.clear_all_articles()
        filtered_db.insert_articles(djt_articles)
        filtered_db.sort_and_reindex_articles()
        print(f"Stored {len(djt_articles)} DJT-related articles in filtered_articles.json")

    # Sort and reindex articles by published_at (desc) then source (asc)
    article_db.sort_and_reindex_articles()


if __name__ == "__main__":
    main()
