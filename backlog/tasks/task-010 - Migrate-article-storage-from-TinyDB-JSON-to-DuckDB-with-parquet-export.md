---
id: TASK-010
title: Migrate article storage from TinyDB/JSON to DuckDB with parquet export
status: Done
assignee: []
created_date: '2026-07-01 21:44'
updated_date: '2026-07-01 22:03'
labels: []
dependencies: []
priority: medium
ordinal: 4500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the TinyDB JSON backend behind `ArticleDB` (utils/db.py) with a persistent DuckDB database as the primary, growing store, keyed by a `url` PRIMARY KEY with ON CONFLICT upsert semantics. Export both the `articles` and `filtered_articles` tables to Parquet via `COPY ... (FORMAT parquet)` as the interchange format the static-site build step (task-003.01) consumes. Fully remove TinyDB; add only `duckdb` (no pandas/pyarrow). Preserve the `ArticleDB` public API (insert_article, insert_articles, search_by_url, search_by_category, get_all_articles, remove_by_url, clear_all_articles, clear_old_articles, sort_and_reindex_articles, create_article_db factory) so main.py and the producers (utils/newsapi.py, utils/rss.py, utils/sentiment.py, utils/filter.py) are unaffected.

Reference idioms (DuckDB Python):
- Persistent connection: `con = duckdb.connect("articles.duckdb")`
- Schema: `CREATE TABLE IF NOT EXISTS articles (url VARCHAR PRIMARY KEY, ...)`
- Upsert: `INSERT INTO articles VALUES (...) ON CONFLICT (url) DO UPDATE SET ...` (or DO NOTHING — decide to match current TinyDB skip-duplicates behavior)
- Purge: `DELETE FROM articles WHERE published_at < ?`
- Parquet export: `COPY articles TO 'articles.parquet' (FORMAT parquet)` and same for filtered_articles

Article schema fields: published_at (str '%Y-%m-%d %H:%M'), title, description, url (lowercased, PK), source, category, author, plus nullable djt_relevance_score (DOUBLE) and sentiment_score (DOUBLE) — not every record has these, they must round-trip as NULL without error.

main.py currently opens the master DB, writes filtered_articles.json via a second create_article_db call, then reindexes both. On sentiment-judge failure, filtered_articles is left untouched — preserve this behavior with the new store too.

Open implementation choice for the implementer (not pre-decided): whether the two datasets are two tables in one .duckdb file or two separate database files — either is acceptable as long as both parquet exports are produced and the API is preserved.

Also add the .duckdb database file and generated .parquet exports to .gitignore as build artifacts.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 duckdb added to pyproject.toml; tinydb removed; no pandas/pyarrow added
- [x] #2 ArticleDB is backed by a persistent DuckDB database file and preserves every existing public method's behavior
- [x] #3 Table schema declares url as PRIMARY KEY; insert_article/insert_articles dedupe via INSERT ... ON CONFLICT (url), matching current TinyDB skip-duplicates behavior
- [x] #4 djt_relevance_score and sentiment_score are nullable DOUBLE columns; records lacking them insert as NULL without error
- [x] #5 clear_old_articles drops rows older than the cutoff via DELETE ... WHERE published_at < ?; search_by_url, search_by_category, get_all_articles, remove_by_url, clear_all_articles reproduce prior behavior
- [x] #6 sort_and_reindex_articles returns/persists rows ordered by published_at desc then source asc (integer-string _default reindex removed)
- [x] #7 Both articles.parquet and filtered_articles.parquet are produced via COPY ... (FORMAT parquet) and reflect current table contents
- [x] #8 main.py still writes the master store and the filtered store; sentiment-judge failure leaves the filtered parquet/table untouched
- [x] #9 tests/test_db.py and tests/test_filter.py updated to exercise the DuckDB store and parquet export; fixtures converted to .parquet or generated in-test; empty-DB cases still covered
- [x] #10 pytest passes; ruff format --check --diff and ruff check are clean
- [x] #11 README.md / AGENTS.md updated to describe the DuckDB store + parquet export, dropping JSON/TinyDB references; stale filtered_articles.json references removed
- [x] #12 .duckdb database file and generated .parquet exports added to .gitignore
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Replaced the TinyDB/JSON-backed `ArticleDB` (utils/db.py) with a persistent DuckDB store per file (`articles.duckdb`, `filtered_articles.duckdb`), each holding a single `articles` table keyed by `url` (lowercased) with `INSERT ... ON CONFLICT (url) DO NOTHING` upsert semantics matching the prior skip-duplicates behavior. `djt_relevance_score`/`sentiment_score` are nullable DOUBLE columns. Every mutating operation re-exports the table to a Parquet file (`<name>.parquet`) via `COPY ... (FORMAT parquet)`, so the interchange file always reflects current contents. `get_all_articles` orders by `published_at DESC, source ASC` directly in SQL (published_at's `%Y-%m-%d %H:%M` format sorts correctly as a string), removing the old TinyDB integer-string `_default` reindexing; `sort_and_reindex_articles` now just reports/persists via export and returns `None` on an empty table. All other public methods (insert_article/insert_articles/search_by_url/search_by_category/remove_by_url/clear_all_articles/clear_old_articles) and the `create_article_db` factory preserve their prior signatures and behavior, so main.py and the producers (utils/newsapi.py, utils/rss.py, utils/sentiment.py, utils/filter.py) needed no logic changes beyond main.py's two store filenames switching to `articles.duckdb`/`filtered_articles.duckdb`.

Removed `get_article_query`/`Query` (TinyDB-specific, not part of the API list) and the `tinydb` dependency; added `duckdb`. Converted tests/fixtures/articles.json to tests/fixtures/articles.parquet and updated test_db.py, test_filter.py, test_main.py, and test_newsapi.py fixtures to use temp DuckDB files (via mkdtemp, since duckdb.connect rejects pre-created empty files) instead of NamedTemporaryFile JSON stubs. Updated docs/ai.md and AGENTS.md to describe the DuckDB/Parquet store instead of TinyDB/JSON, and added `*.duckdb`/`*.parquet` to .gitignore (fixtures remain tracked via the existing `!tests/fixtures/*` negation).

`ruff format --check`, `ruff check`, and `pytest` (106 tests) all pass.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [x] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [x] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
