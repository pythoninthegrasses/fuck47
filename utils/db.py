#!/usr/bin/env python

import duckdb
from datetime import datetime, timedelta
from pathlib import Path

ARTICLE_COLUMNS = [
    'url',
    'published_at',
    'title',
    'description',
    'source',
    'category',
    'author',
    'djt_relevance_score',
    'sentiment_score',
]


class ArticleDB:
    """Database manager for article storage and operations, backed by DuckDB with a Parquet export."""

    def __init__(self, db_path='articles.duckdb'):
        self.db_path = db_path
        self.parquet_path = str(Path(db_path).with_suffix('.parquet'))
        self.con = duckdb.connect(db_path)
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                url VARCHAR PRIMARY KEY,
                published_at VARCHAR,
                title VARCHAR,
                description VARCHAR,
                source VARCHAR,
                category VARCHAR,
                author VARCHAR,
                djt_relevance_score DOUBLE,
                sentiment_score DOUBLE
            )
        """)
        self._export_parquet()

    def _export_parquet(self):
        """Write the current table contents to the Parquet interchange file."""
        self.con.execute(f"COPY articles TO '{self.parquet_path}' (FORMAT parquet)")

    def _row_values(self, article):
        url = article.get('url')
        return [url.lower() if url else url] + [article.get(col) for col in ARTICLE_COLUMNS[1:]]

    def insert_article(self, article):
        """Insert a single article if it doesn't already exist"""
        result = self.con.execute(
            "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (url) DO NOTHING RETURNING url",
            self._row_values(article),
        ).fetchall()
        self._export_parquet()
        return len(result) > 0

    def insert_articles(self, articles):
        """Insert multiple articles, skipping duplicates"""
        inserted_count = 0
        for article in articles:
            if self.insert_article(article):
                inserted_count += 1
        return inserted_count

    def search_by_url(self, url):
        """Search for articles by URL"""
        rows = self.con.execute("SELECT * FROM articles WHERE url = ?", [url.lower() if url else url]).fetchall()
        return self._rows_to_dicts(rows)

    def search_by_category(self, category):
        """Search for articles by category"""
        rows = self.con.execute("SELECT * FROM articles WHERE category = ?", [category]).fetchall()
        return self._rows_to_dicts(rows)

    def get_all_articles(self):
        """Get all articles from the database, ordered by published_at (desc) then source (asc)"""
        rows = self.con.execute("SELECT * FROM articles ORDER BY published_at DESC, source ASC").fetchall()
        return self._rows_to_dicts(rows)

    def _rows_to_dicts(self, rows):
        columns = [col[0] for col in self.con.description]
        return [dict(zip(columns, row, strict=False)) for row in rows]

    def remove_by_url(self, url):
        """Remove articles by URL"""
        result = self.con.execute("DELETE FROM articles WHERE url = ? RETURNING *", [url.lower() if url else url]).fetchall()
        self._export_parquet()
        return self._rows_to_dicts(result)

    def clear_all_articles(self):
        """Clear all articles from the database"""
        removed_count = self.con.execute("SELECT count(*) FROM articles").fetchone()[0]
        self.con.execute("DELETE FROM articles")
        self._export_parquet()
        print(f"Cleared {removed_count} articles from database")
        return removed_count

    def clear_old_articles(self, hours):
        """Clear articles older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M')

        removed = self.con.execute("DELETE FROM articles WHERE published_at < ? RETURNING url", [cutoff_str]).fetchall()
        self._export_parquet()

        print(f"Removed {len(removed)} old articles")
        return len(removed)

    def sort_and_reindex_articles(self):
        """Persist the current articles ordered by published_at (desc) then source (asc)"""
        count = self.con.execute("SELECT count(*) FROM articles").fetchone()[0]

        if not count:
            print("No articles to sort")
            return None

        self._export_parquet()
        print(f"Sorted and reindexed {count} articles by published_at (desc) then source (asc)")
        return self

    def close(self):
        """Close the database connection"""
        self.con.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def create_article_db(db_path='articles.duckdb'):
    """Create and return an ArticleDB instance"""
    return ArticleDB(db_path)
