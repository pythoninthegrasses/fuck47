---
id: TASK-011.01
title: Implement Parquet snapshot archive and htmx-rendered history view
status: Done
assignee: []
created_date: '2026-07-02 03:23'
updated_date: '2026-07-02 03:40'
labels: []
dependencies: []
references:
  - utils/db.py
  - main.py
  - .gitignore
  - .github/workflows/news-refresh.yml
  - app/index.html
parent_task_id: TASK-011
priority: medium
ordinal: 4500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implements the design decided in task-011's grooming session (see its Implementation Notes): timestamped Parquet snapshots as a persistent, git-committed archive, plus a build-time static HTML/htmx view of that archive. DuckDB remains the ephemeral query engine / current-window store; it is not the archive itself.

## Layout

```
archive/
  articles/YYYY-MM-DD/YYYY-MM-DDTHHMM.parquet          # pre-filter snapshot
  filtered_articles/YYYY-MM-DD/YYYY-MM-DDTHHMM.parquet # published snapshot
```

Each row carries a `run_at` timestamp column in addition to the existing `ARTICLE_COLUMNS` (utils/db.py:7-17). No `run_date=` Hive prefix — the parent directory already names the store; query the whole archive with `read_parquet('archive/**/*.parquet')` and group by `run_at` for the time dimension.

## Changes

1. **utils/db.py**: add `archive_snapshot(archive_dir, run_at)` to `ArticleDB` — writes the current table to `archive/<store>/<date>/<ts>.parquet` via DuckDB `COPY`, reusing the existing `self.con` / `_export_parquet` pattern. Never truncates the archive directory.
2. **main.py**: call `archive_snapshot` for `article_db` (pre-filter, after fetch/sort) and for `filtered_db` (after it's populated, main.py:74). Stamp a single `run_at` once per run and pass it to both calls.
3. **Static render step**: new `utils/render.py` (or extend the build step from task-003.01 if that's landed first — coordinate, don't duplicate) to emit `app/archive/index.html` (list of past run dates, each an `hx-get` link) and per-run fragments (`app/archive/YYYY-MM-DD.html`) from the archive contents.
4. **.gitignore**: negate `archive/` and its `*.parquet` files so CI can commit snapshots (currently `*.parquet` is globally ignored).
5. **.github/workflows/news-refresh.yml**: this workflow is stale — it references `news_aggregator.py` and `data/`, a pre-DuckDB-migration layout. Update it to run `main.py` and `git add archive/ app/archive/` in its commit step (or fold into whatever the task-006/007 CI work produces, whichever lands first).

## Coordination note

task-003.01 ("Build step injects filtered articles into app/index.html") is in flight and overlaps the render step in this task — reuse that build step for archive rendering rather than duplicating templating logic.

No new dependencies: DuckDB already reads/writes Parquet natively.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Snapshot files are written to the partitioned path (archive/<store>/<date>/<ts>.parquet) with a run_at column and the existing ARTICLE_COLUMNS
- [x] #2 Running main.py twice in the same day produces two distinct snapshot files without overwriting either
- [x] #3 read_parquet('archive/**/*.parquet') returns the union of all snapshots across both stores
- [x] #4 app/archive/index.html lists past run dates and htmx hx-get loads each date's fragment showing that run's articles
- [x] #5 archive/ is committed by CI (news-refresh.yml updated); live *.duckdb/*.parquet working files remain gitignored
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented per task-011's grooming decision, test-first throughout.

**utils/db.py**: `ArticleDB.archive_snapshot(archive_dir, run_at)` writes the current table to `archive/<store>/YYYY-MM-DD/YYYY-MM-DDTHHMM.parquet` via a parameterized `COPY (SELECT *, ? AS run_at FROM articles) TO ? (FORMAT parquet)`. Store name is derived from `db_path` stem. Never truncates prior snapshots.

**main.py / config.py**: added `ARCHIVE_DIR` config (default `archive`). `main()` stamps one `run_at` per run and calls `archive_snapshot` for the pre-filter `article_db` (unconditionally, end of run) and for `filtered_db` (only when `negative_articles is not None`, i.e. the judge didn't fail).

**utils/render.py**: new module reading the `filtered_articles` archive via `read_parquet` glob, deduping same-day multi-run articles by url/title/description/source/published_at, and writing `app/archive/index.html` (htmx `hx-get` links per date) + per-date fragments. All article-derived text is `html.escape`d (feed content is untrusted). Runnable standalone via `uv run python -m utils.render`.

**.gitignore**: added `!archive/**/*.parquet` negation so CI can commit the archive while the live `.duckdb`/`.parquet` working files stay ignored. Verified with `git check-ignore`/`git status`.

**.github/workflows/news-refresh.yml**: replaced the stale pre-DuckDB-migration script/pip references with `uv sync` / `uv run main.py` / `uv run python -m utils.render`, and the commit step now stages `archive/` + `app/archive/`.

**Testing note**: several pre-existing test_main.py tests called the real `main()` without patching `main.article_db` or `main.ARCHIVE_DIR`, relying on main.py's real module-level `article_db` global. Adding an unconditional `archive_snapshot` call at the end of `main()` would have made those tests write real snapshot files into the repo's working tree. Fixed by patching `main.ARCHIVE_DIR` to a pytest `tmp_path` in the 4 affected tests (test_main_cache_cleanup, test_main_output_messages, test_negative_and_positive_articles_split_at_threshold, test_judge_failure_leaves_filtered_articles_untouched) — confirmed via git status that no test run leaves stray files in the repo.

Docs: AGENTS.md/CLAUDE.md updated with the archive/render explanation.

Verification: 142/142 pytest passing, ruff format/check clean, manual end-to-end run (two same-day snapshots -> glob query groups by run_at -> render dedupes and HTML-escapes) confirmed working outside the repo tree.

Not done (explicitly out of scope per the parent task's coordination note): wiring `utils/render.py`'s output into `app/index.html` itself is task-003.01's job once that build step lands.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [x] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
- [x] #7 Failing tests written first for archive_snapshot() and the render step, per repo TDD convention, before implementation
<!-- DOD:END -->
