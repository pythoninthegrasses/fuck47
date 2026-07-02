#!/usr/bin/env python

import requests_cache
import sys
from config import (
    ARCHIVE_DIR,
    CACHE_HOURS,
    CACHE_SESSION,
    DJT_FILTER_ENABLED,
    DJT_FILTER_MIN_SCORE,
    SENTIMENT_ENABLED,
    SENTIMENT_MAX_SCORE,
    TTL,
)
from datetime import datetime
from eliot import to_file
from utils.db import create_article_db
from utils.filter import DJTNewsFilter
from utils.newsapi import fetch_and_store_articles
from utils.rss import fetch_rss_articles
from utils.sentiment import SentimentJudgeError, score_articles

to_file(sys.stdout)

if CACHE_SESSION:
    requests_cache.install_cache(cache_name='newsapi_cache', backend='sqlite', expire_after=TTL, allowable_codes=(200,))

article_db = create_article_db('articles.duckdb')


def main():
    """Fetch and store articles from NewsAPI and RSS feeds."""
    run_at = datetime.now()
    article_db.clear_old_articles(hours=CACHE_HOURS)

    # Fetch and store articles from NewsAPI
    articles = fetch_and_store_articles(article_db)
    print(f"Fetched and stored {len(articles)} articles from NewsAPI")

    # Fetch and store articles from RSS feeds
    rss_articles = fetch_rss_articles()
    stored_rss_count = article_db.insert_articles(rss_articles)
    print(f"Stored {stored_rss_count} new articles from RSS feeds")

    # Apply DJT filtering if enabled and create the filtered articles store
    if DJT_FILTER_ENABLED:
        djt_filter = DJTNewsFilter(min_score=DJT_FILTER_MIN_SCORE)

        # Get all articles from database
        all_articles = article_db.get_all_articles()
        print(f"Total articles before filtering: {len(all_articles)}")

        # Filter for DJT-related articles
        djt_articles = djt_filter.filter_articles(all_articles)
        print(f"DJT-related articles: {len(djt_articles)}")

        # Judge sentiment toward DJT and keep only negative-sentiment articles.
        # If the judge call fails, skip rewriting the filtered articles store so the
        # site keeps serving the previous run's output instead of going blank.
        negative_articles = djt_articles
        if djt_articles and SENTIMENT_ENABLED:
            try:
                scores = score_articles(djt_articles)
                for i, article in enumerate(djt_articles):
                    article['sentiment_score'] = scores[i]
                negative_articles = [a for a in djt_articles if a['sentiment_score'] <= SENTIMENT_MAX_SCORE]
                print(f"Negative-sentiment articles: {len(negative_articles)}")
            except SentimentJudgeError as e:
                print(f"Sentiment analysis failed ({e}); keeping existing filtered articles store unchanged")
                negative_articles = None

        if negative_articles is not None:
            # Create filtered articles database
            filtered_db = create_article_db('filtered_articles.duckdb')
            filtered_db.clear_all_articles()
            filtered_db.insert_articles(negative_articles)
            filtered_db.sort_and_reindex_articles()
            filtered_db.archive_snapshot(ARCHIVE_DIR, run_at)
            print(f"Stored {len(negative_articles)} articles in filtered articles store")

    # Sort and reindex articles by published_at (desc) then source (asc)
    article_db.sort_and_reindex_articles()
    article_db.archive_snapshot(ARCHIVE_DIR, run_at)


if __name__ == "__main__":
    main()
