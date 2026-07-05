#!/usr/bin/env python

import csv
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
    'manual_review',
]


class ArticleDB:
    """Database manager for article storage and operations, backed by DuckDB with a Parquet export."""

    def __init__(self, db_path='articles.duckdb', exclude_csv=None):
        from config import EXCLUDE_URLS_CSV

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
                sentiment_score DOUBLE,
                manual_review BOOLEAN DEFAULT FALSE
            )
        """)
        # Migrates pre-existing stores (created before manual_review existed) in place.
        self.con.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS manual_review BOOLEAN DEFAULT FALSE")
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS excluded_urls (
                url VARCHAR PRIMARY KEY,
                reason VARCHAR,
                excluded_at VARCHAR
            )
        """)
        # Load exclusions from the CSV so they survive ephemeral DB rebuilds.
        csv_path = exclude_csv if exclude_csv is not None else EXCLUDE_URLS_CSV
        if csv_path and Path(csv_path).exists():
            self.sync_exclusions_from_csv(csv_path)
        self._export_parquet()

    def _export_parquet(self):
        """Write the current table contents to the Parquet interchange file."""
        self.con.execute(f"COPY articles TO '{self.parquet_path}' (FORMAT parquet)")

    def _row_values(self, article):
        url = article.get('url')
        values = [article.get(col) for col in ARTICLE_COLUMNS[1:-1]] + [bool(article.get('manual_review', False))]
        return [url.lower() if url else url] + values

    def sync_exclusions_from_csv(self, path):
        """Read the exclusion CSV and upsert all rows into the excluded_urls table."""
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                url = (row.get('url') or '').lower()
                if url:
                    self.con.execute(
                        "INSERT INTO excluded_urls VALUES (?, ?, ?) ON CONFLICT (url) DO UPDATE SET reason=excluded.reason, excluded_at=excluded.excluded_at",
                        [url, row.get('reason', ''), row.get('excluded_at', '')],
                    )
                    count += 1
        return count

    def add_exclusion(self, url, reason='', excluded_at=None):
        """Insert or replace a single exclusion."""
        url_lower = url.lower() if url else url
        ts = excluded_at or datetime.now().strftime('%Y-%m-%dT%H:%M')
        self.con.execute(
            "INSERT INTO excluded_urls VALUES (?, ?, ?) ON CONFLICT (url) DO UPDATE SET reason=excluded.reason, excluded_at=excluded.excluded_at",
            [url_lower, reason, ts],
        )

    def remove_exclusion(self, url):
        """Remove a URL from the exclusion table."""
        self.con.execute("DELETE FROM excluded_urls WHERE url = ?", [(url.lower() if url else url)])

    def is_excluded(self, url):
        """Return True if the URL is in the exclusion table."""
        url_lower = url.lower() if url else url
        row = self.con.execute("SELECT 1 FROM excluded_urls WHERE url = ?", [url_lower]).fetchone()
        return row is not None

    def get_exclusions(self):
        """Return all exclusion rows as a list of dicts."""
        rows = self.con.execute("SELECT url, reason, excluded_at FROM excluded_urls").fetchall()
        return [{'url': r[0], 'reason': r[1], 'excluded_at': r[2]} for r in rows]

    def insert_article(self, article):
        """Insert a single article if it doesn't already exist and is not excluded."""
        url = (article.get('url') or '').lower()
        if url and self.is_excluded(url):
            return False
        result = self.con.execute(
            "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (url) DO NOTHING RETURNING url",
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

    def mark_manual_review(self, url):
        """Flag an existing article as manually reviewed.

        Separate from insert_article because ON CONFLICT DO NOTHING means an insert alone can't
        retroactively pin a row that already existed (e.g. a manually-curated URL the automated
        pipeline had already fetched) - see cli.py's merge-reviewed command.
        """
        self.con.execute("UPDATE articles SET manual_review = TRUE WHERE url = ?", [url.lower() if url else url])
        self._export_parquet()

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

    def archive_snapshot(self, archive_dir, run_at):
        """Write the current table contents as a dated snapshot under archive_dir.

        Never truncates or overwrites prior snapshots: each run writes to
        archive_dir/<store>/<date>/<timestamp>.parquet, where <store> is derived
        from db_path so distinct stores (e.g. articles vs filtered_articles) land
        in separate subtrees of the same archive.
        """
        store_name = Path(self.db_path).stem
        date_dir = Path(archive_dir) / store_name / run_at.strftime('%Y-%m-%d')
        date_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = date_dir / f"{run_at.strftime('%Y-%m-%dT%H%M')}.parquet"

        self.con.execute(
            "COPY (SELECT *, ? AS run_at FROM articles) TO ? (FORMAT parquet)",
            [run_at, str(snapshot_path)],
        )
        return str(snapshot_path)

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


def create_article_db(db_path='articles.duckdb', exclude_csv=None):
    """Create and return an ArticleDB instance"""
    return ArticleDB(db_path, exclude_csv=exclude_csv)
