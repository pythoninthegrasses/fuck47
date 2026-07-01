---
id: TASK-006.02
title: Retry logic and graceful degradation for API/network failures
status: To Do
assignee: []
created_date: '2026-07-01 19:02'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-006
priority: medium
ordinal: 6200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD Technical Considerations, add retry logic for failed NewsAPI/RSS calls and ensure the pipeline degrades gracefully (partial results) rather than crashing when a source is unavailable.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Transient NewsAPI/RSS request failures are retried with backoff before giving up
- [ ] #2 A source that remains unavailable after retries is skipped and logged, without failing the whole run
- [ ] #3 Unit test simulates a failing source and asserts the pipeline still produces output from the remaining sources
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
