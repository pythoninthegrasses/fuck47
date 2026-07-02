---
id: TASK-003
title: Static Site Generation
status: Done
assignee: []
created_date: '2026-07-01 18:58'
updated_date: '2026-07-02 20:20'
labels: []
dependencies: []
documentation:
  - doc-001
priority: high
ordinal: 500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Parent task for generating app/index.html from filtered_articles.json on a configurable interval, replacing the current hand-written placeholder while preserving GitHub Pages compatibility.
<!-- SECTION:DESCRIPTION:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [x] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [x] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Delivered across four subtasks: 003.01 (`render_index` injects `filtered_articles.duckdb` into `app/index.html` between marker comments, `e913b74`/`dc7ffde`); 003.02 (8-hour cron rebuild via `.github/workflows/news-refresh.yml`, `d16f2ad`); 003.03 (Pages compatibility preserved — `static.yml` unchanged, custom domain in repo settings); 003.04 (last-known-good posture: pipeline failures never write `app/index.html`, missing store is a no-op, sentiment failure re-serves prior filtered store). Interchange format changed under task-010 (TinyDB/JSON → DuckDB/Parquet); 003.01 ACs named `filtered_articles.json` but the implementation reads the DuckDB store. DoD #4 (TDD) N/A for 003.02/003.03 (YAML workflow / compatibility verification); code changes in 003.01/003.04 were written test-first.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Static site generation complete. `render_index` rewrites `app/index.html` in place from the DuckDB filtered store (JSON for Alpine + noscript links, between marker comments). An 8-hour cron in `.github/workflows/news-refresh.yml` drives rebuilds, with `workflow_dispatch` and push-to-main as manual/on-demand overrides. The existing `static.yml` workflow deploys `app/` unchanged. Pipeline failures cannot write a broken page — the last-known-good `app/index.html` is always what Pages serves. Full architecture documented in `AGENTS.md` and `docs/ci.md`. Interchange format changed under task-010 (JSON → DuckDB/Parquet); ACs on 003.01 referenced the old filename but the implementation reads the DuckDB store.
<!-- SECTION:FINAL_SUMMARY:END -->
