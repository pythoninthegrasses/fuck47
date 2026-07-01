---
id: TASK-006.03
title: API rate-limit handling for NewsAPI/RSS
status: To Do
assignee: []
created_date: '2026-07-01 19:02'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-006
priority: medium
ordinal: 6300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD Technical Considerations, implement rate limiting so the pipeline stays within NewsAPI/RSS quota, working alongside the existing requests_cache layer.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Requests to NewsAPI respect a configurable rate limit (requests per interval)
- [ ] #2 A 429/rate-limit response is handled without crashing the pipeline (backoff or skip)
- [ ] #3 Unit test simulates a rate-limit response and asserts graceful handling
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
