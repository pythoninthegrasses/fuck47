---
id: TASK-011
title: Archive historical article/filtered-article listings over time
status: Done
assignee: []
created_date: '2026-07-01 22:40'
updated_date: '2026-07-02 03:23'
labels: []
dependencies: []
references:
  - docs/ai.md
  - utils/db.py
  - main.py
priority: high
ordinal: 4500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Today `articles.duckdb` and `filtered_articles.duckdb` are treated as an ephemeral "current window" store, not an archive — this has been true since before the DuckDB migration (confirmed against the pre-migration TinyDB implementation, which had identical `clear_old_articles(hours)` age-based deletion and full-truncate-then-rewrite behavior). Every pipeline run:

- Prunes `articles.duckdb` rows older than `CACHE_HOURS` (main.py:31)
- Fully wipes and rewrites `filtered_articles.duckdb` from scratch (main.py:71-74)

So there has never been a historical record of what was shown on the landing page on any given past run.

The user wants a persistent archive of article listings over time, similar to the pattern used in `~/git/oth`: `data/bars/{symbol}.parquet` is an incremental, accumulating store (new rows appended, never wiped) plus timestamped daily CSV snapshots from a scheduler.

This task is for a future grooming session to pick a direction — do NOT implement yet. Two candidate approaches were presented and neither has been decided on:

1. **Append-only history table in the existing DuckDB file** — every write to the filtered-articles store also appends the same rows (plus a `run_at` timestamp) to a `history` table that is never truncated. Keeps everything in one DuckDB file; queryable via SQL for trend analysis.
2. **Timestamped Parquet snapshots** — alongside the live `filtered_articles.parquet` export, write a dated snapshot file per run, e.g. `archive/filtered_articles/2026-07-01T1400.parquet`. Filesystem-based, mirrors the oth pattern more directly, easy to prune/retain by age or count.

Open questions for the grooming session:

- Which of the two approaches (or a hybrid) fits this project's scale and how it's deployed (GitHub Actions cron + GitHub Pages)?
- Retention policy: keep archive forever, or prune after N days/runs?
- Does the archive need to be queryable from the site itself, or is it just for offline analysis?
- Does `articles.duckdb` (pre-filter) need archiving too, or only the filtered/published set?
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A grooming session has picked one of the two candidate approaches (or an explicitly justified alternative) and recorded the decision on this task
- [x] #2 The chosen approach's retention policy (forever vs. time/count-bounded pruning) is documented on this task before implementation begins
- [x] #3 Whether pre-filter `articles.duckdb` needs archiving (vs. only the filtered/published set) is decided and documented
- [x] #4 This task is split into an implementation task (with its own tests per repo TDD convention) once the design is settled
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Grooming decision (2026-07-01):

**Chosen approach:** Timestamped Parquet snapshots (candidate #2), not an append-only DuckDB history table. DuckDB stays the ephemeral query engine / current-window store (rebuildable, not committed); Parquet snapshot files are the durable, git-committed archive. One immutable file per run means git stores each new file once and never rewrites history — a growing committed .duckdb binary would be rewritten in full every run instead.

Layout: `archive/<store>/YYYY-MM-DD/YYYY-MM-DDTHHMM.parquet` for both `articles` and `filtered_articles` stores, each row carrying a `run_at` timestamp column. Query the whole archive with `read_parquet('archive/**/*.parquet')`, no partition-key prefix needed (parent dir already names the store).

**Retention:** keep forever. Snapshots are ~10KB; a few MB/year at 3 runs/day is negligible.

**Site access:** build-time pre-rendered static HTML fragments (`app/archive/index.html` + per-run fragments) loaded via htmx `hx-get`. No client-side query engine (DuckDB-WASM) for v1 — static hosting on GitHub Pages has no backend, and this is the simplest fit. Revisit DuckDB-WASM only if interactive trend queries are later requested.

**Scope:** archive both the pre-filter `articles` store and the filtered/published `filtered_articles` store, not just the published set — preserves raw signal for future re-analysis with different thresholds/models.

**Persistence constraint surfaced during grooming:** GitHub Actions runners are ephemeral; the only cross-run persistence is committing data back to the repo. `*.duckdb`/`*.parquet` are currently gitignored, so nothing persists between cron runs today. The archive/ directory must be un-gitignored and committed by CI; the live `*.duckdb`/`*.parquet` working files stay ignored.

Full design written up in implementation subtask.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Grooming complete. Chosen approach: timestamped Parquet snapshots (candidate #2) — DuckDB stays the ephemeral query engine, snapshots under `archive/<store>/YYYY-MM-DD/YYYY-MM-DDTHHMM.parquet` are the durable git-committed archive. Retention: forever. Scope: both `articles` and `filtered_articles` stores. Full decision rationale recorded in Implementation Notes above. Split into TASK-011.01 for implementation with TDD.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
