---
id: TASK-006.03
title: API rate-limit handling for NewsAPI/RSS
status: Done
assignee: []
created_date: '2026-07-01 19:02'
updated_date: '2026-07-02 15:41'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-006
priority: medium
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD Technical Considerations, implement rate limiting so the pipeline stays within NewsAPI/RSS quota, working alongside the existing requests_cache layer.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Requests to NewsAPI respect a configurable rate limit (requests per interval)
- [x] #2 A 429/rate-limit response is handled without crashing the pipeline (backoff or skip)
- [x] #3 Unit test simulates a rate-limit response and asserts graceful handling
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add `utils/ratelimit.py` with a `RateLimiter` class: sliding-window limiter over a `deque` of `time.monotonic()` timestamps; `acquire()` evicts expired timestamps then sleeps just long enough to stay under `max_requests` per `interval_sec` before recording a new timestamp. Write `tests/test_ratelimit.py` first (mocking `time.monotonic`/`time.sleep`), confirm it fails (module missing), then implement until green.
2. Add config vars in `config.py` following the `decouple.config()` pattern: `RATE_LIMIT_REQUESTS` (default 100), `RATE_LIMIT_INTERVAL_SEC` (default 3600).
3. Instantiate one module-level `RateLimiter` in `utils/newsapi.py` (call `.acquire()` before both `SESSION.get()` sites: sources endpoint and per-category top-headlines) and a separate instance in `utils/rss.py` (call `.acquire()` before each `feedparser.parse()` in `parse_feed`) — independent budgets since they're different services, both driven by the same two config knobs.
4. AC#2 (429 handled without crashing) is already satisfied by the existing `http_request_with_retry`/`feed_with_retry` from task-006.02 (429 is in `TRANSIENT_HTTP_CODES`, exhausted retries return the last bad response and the caller skips+logs). Add an explicit regression test mirroring the existing `test_skips_category_with_persistent_503_continues_to_next` pattern in `tests/test_newsapi.py`, but for persistent 429, to cover AC#3's "simulate a rate-limit response" requirement directly (this test is expected to pass immediately since the behavior pre-exists — it documents/locks in the guarantee rather than driving new implementation).
5. Update `AGENTS.md` with the two new env vars and a short note on the rate limiter.
6. Run `ruff format --check --diff .`, `ruff check`, `pytest`; check off ACs/DoD; commit as `feat(ratelimit): add configurable rate limiting for NewsAPI/RSS requests`.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added `utils/ratelimit.py` with a `RateLimiter` sliding-window class (deque of `time.monotonic()` timestamps; `acquire()` evicts expired entries and sleeps just enough to stay under `max_requests` per `interval_sec`). Added config knobs `RATE_LIMIT_REQUESTS` (default 100) and `RATE_LIMIT_INTERVAL_SEC` (default 3600) in `config.py`. Wired independent module-level `RateLimiter` instances into `utils/newsapi.py` (both the sources endpoint and per-category top-headlines calls) and `utils/rss.py` (per-feed `feedparser.parse` calls), each calling `.acquire()` before the outbound request. AC#2 (429 handled gracefully) was already satisfied by task-006.02's retry/backoff logic; added a regression test (`test_skips_category_with_persistent_429_continues_to_next`) to lock that in explicitly, plus new rate-limiter-specific tests: `tests/test_ratelimit.py` (4 unit tests, written test-first), `test_fetch_and_store_articles_acquires_rate_limiter_per_category` in `test_newsapi.py`, and `test_parse_feed_acquires_rate_limiter` in `test_rss.py`. Full suite (172 tests) passes; `ruff format --check` and `ruff check` clean. AGENTS.md updated with the new module and env vars. Committed as `feat(ratelimit): add configurable rate limiting for NewsAPI/RSS requests`.
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
