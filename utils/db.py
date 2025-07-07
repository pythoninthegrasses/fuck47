#!/usr/bin/env python

import json
from datetime import datetime, timedelta
from tinydb import Query, TinyDB


class ArticleDB:
    """Database manager for article storage and operations"""

    def __init__(self, db_path='articles.json'):
        self.db_path = db_path
        self.db = TinyDB(db_path)
        self.Article = Query()

    def insert_article(self, article):
        """Insert a single article if it doesn't already exist"""
        if not self.db.search(self.Article.url == article['url']):
            self.db.insert(article)
            return True
        return False

    def insert_articles(self, articles):
        """Insert multiple articles, skipping duplicates"""
        inserted_count = 0
        for article in articles:
            if self.insert_article(article):
                inserted_count += 1
        return inserted_count

    def search_by_url(self, url):
        """Search for articles by URL"""
        return self.db.search(self.Article.url == url)

    def search_by_category(self, category):
        """Search for articles by category"""
        return self.db.search(self.Article.category == category)

    def get_all_articles(self):
        """Get all articles from the database"""
        return self.db.all()

    def remove_by_url(self, url):
        """Remove articles by URL"""
        return self.db.remove(self.Article.url == url)
    
    def clear_all_articles(self):
        """Clear all articles from the database"""
        removed_count = len(self.db.all())
        self.db.truncate()
        print(f"Cleared {removed_count} articles from database")
        return removed_count

    def clear_old_articles(self, hours):
        """Clear articles older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M')

        # Remove articles older than cutoff
        old_articles = self.db.search(self.Article.published_at < cutoff_str)
        for article in old_articles:
            self.db.remove(self.Article.url == article['url'])

        print(f"Removed {len(old_articles)} old articles")
        return len(old_articles)

    def sort_and_reindex_articles(self):
        """Sort articles by published_at (desc) then source (asc) and rewrite TinyDB IDs"""
        # Get all articles
        all_articles = self.db.all()

        if not all_articles:
            print("No articles to sort")
            return

        # Sort articles by published_at (desc) then source (asc)
        def sort_key(article):
            # Parse published_at to datetime for proper sorting
            try:
                pub_date = datetime.strptime(article['published_at'], '%Y-%m-%d %H:%M')
            except ValueError:
                # Fallback if format is different
                pub_date = datetime.min

            # Return tuple: (-timestamp for desc, source for asc)
            return (-pub_date.timestamp(), article['source'])

        sorted_articles = sorted(all_articles, key=sort_key)

        # Manually create new TinyDB structure with sequential IDs
        new_data = {"_default": {}}
        for i, article in enumerate(sorted_articles, 1):
            new_data["_default"][str(i)] = article

        # Write the new structure directly to the JSON file
        self.db.close()
        with open(self.db_path, 'w') as f:
            json.dump(new_data, f, indent=2)

        # Reload the database to reflect changes
        self.db = TinyDB(self.db_path)

        print(f"Sorted and reindexed {len(sorted_articles)} articles by published_at (desc) then source (asc)")
        return self.db

    def close(self):
        """Close the database connection"""
        self.db.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience functions for backward compatibility
def create_article_db(db_path='articles.json'):
    """Create and return an ArticleDB instance"""
    return ArticleDB(db_path)


def get_article_query():
    """Get a Query instance for article operations"""
    return Query()
