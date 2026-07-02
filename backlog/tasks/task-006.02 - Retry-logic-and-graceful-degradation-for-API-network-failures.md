---
id: TASK-006.02
title: Retry logic and graceful degradation for API/network failures
status: Done
assignee: []
created_date: '2026-07-01 19:02'
updated_date: '2026-07-02 05:37'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-006
priority: medium
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD Technical Considerations, add retry logic for failed NewsAPI/RSS calls and ensure the pipeline degrades gracefully (partial results) rather than crashing when a source is unavailable.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Transient NewsAPI/RSS request failures are retried with backoff before giving up
- [x] #2 A source that remains unavailable after retries is skipped and logged, without failing the whole run
- [x] #3 Unit test simulates a failing source and asserts the pipeline still produces output from the remaining sources
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added `utils/retry.py` with `http_request_with_retry` and `feed_with_retry` utilities implementing exponential backoff (default: 3 retries, 1s base delay, 2× factor) for transient failures (429, 5xx, ConnectionError, Timeout). Wired into `utils/newsapi.py` (per-category requests) and `utils/rss.py` (per-feed parsing). Failed sources are skipped and logged after retries are exhausted without crashing the pipeline. 23 new tests written test-first across `tests/test_retry.py`, `tests/test_newsapi.py`, and `tests/test_rss.py`. AGENTS.md updated with usage note. Committed as `feat(retry): add retry logic and graceful degradation for API/network failures`.
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
