---
id: TASK-003.04
title: Graceful handling of build failures
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-003
priority: medium
ordinal: 3400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR3, a failed build (e.g. API outage, sentiment analysis error) must not break the live site. Ensure the workflow retains the last-known-good app/index.html rather than deploying a broken page.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 If the pipeline (fetch/filter/sentiment) fails, the build step does not overwrite the previously deployed app/index.html
- [ ] #2 A simulated pipeline failure in tests confirms the deploy step is skipped or the prior content is retained
- [ ] #3 Failures are logged clearly enough to debug from CI logs
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
