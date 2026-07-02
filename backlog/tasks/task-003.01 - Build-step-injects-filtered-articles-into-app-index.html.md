---
id: TASK-003.01
title: Build step injects filtered articles into app/index.html
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:30'
labels: []
dependencies:
  - TASK-010
documentation:
  - doc-001
parent_task_id: TASK-003
priority: high
ordinal: 750
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the hand-written static placeholder in app/index.html with a build step that reads filtered_articles.json and renders the news content into the page. Depends on the negative-only display gate (task-002.03) producing the final article set.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A Python build step generates app/index.html content from filtered_articles.json
- [x] #2 Generated HTML is valid and preserves the existing site's <head>/meta/branding elements
- [x] #3 Running the build with an empty filtered_articles.json does not error
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
render_index() in utils/render.py replaces the block between <!-- ARTICLES:BEGIN/END --> markers in app/index.html in place: a JSON payload consumed by Alpine plus a noscript link list. Reads filtered_articles.duckdb (the interchange store from task-010 superseded the filtered_articles.json named in the ACs). Head/meta preserved by marker-scoped replacement; untrusted feed fields escaped both in JSON (</ -> <\/) and noscript HTML. Missing/empty store: missing db is a no-op returning 0 (page untouched); empty store injects [] and the page renders its designed empty state. Wired into main() at end of run (feat(main) commit) and runnable standalone via `uv run python -m utils.render`. TDD: tests/test_render.py::TestRenderIndex (6 tests) written failing-first; tests/test_main.py::TestMainRendersIndex covers the pipeline wiring with an autouse stub so tests never rewrite the real page.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Build-step injection shipped: render_index() rewrites app/index.html in place from filtered_articles.duckdb (JSON for Alpine + noscript links, markers preserve head/branding), wired into main() and python -m utils.render. Escaping hardened against script-breakout from untrusted feeds; missing store leaves the page untouched. Commits: e913b74 feat(render), dc7ffde feat(main), 93281eb docs(agents). Note: reads the DuckDB store rather than the filtered_articles.json named at creation time — the interchange format changed under task-010.
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
