---
id: TASK-003.04
title: Graceful handling of build failures
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:30'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-003
priority: medium
ordinal: 859.375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR3, a failed build (e.g. API outage, sentiment analysis error) must not break the live site. Ensure the workflow retains the last-known-good app/index.html rather than deploying a broken page.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 If the pipeline (fetch/filter/sentiment) fails, the build step does not overwrite the previously deployed app/index.html
- [x] #2 A simulated pipeline failure in tests confirms the deploy step is skipped or the prior content is retained
- [x] #3 Failures are logged clearly enough to debug from CI logs
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Last-known-good posture holds at every failure point: (1) fetch/filter exceptions abort main() before render_index runs, so the committed app/index.html is never touched; (2) sentiment-judge failure keeps the previous filtered store (pre-existing main.py fallback) and the subsequent render_index re-injects that prior content idempotently; (3) missing filtered store makes render_index a no-op returning 0 (tests/test_render.py::test_missing_db_leaves_file_unchanged, written failing-first). Failures are printed (sentiment fallback message, injected-count line) alongside eliot stdout logging, so CI logs show exactly which stage degraded. Deploy is decoupled: GitHub Pages publishes whatever app/index.html is committed, so a failed pipeline run simply never produces a broken page to deploy.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Graceful failure handling verified: pipeline failures cannot break the live page. Aborts leave app/index.html unwritten, sentiment failures re-serve the previous filtered store, and a missing store is a tested no-op in render_index. Covered by test_render.py (missing-db) and test_main.py sentiment-failure tests; failures logged to stdout for CI. Shipped within commits e913b74/dc7ffde.
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
