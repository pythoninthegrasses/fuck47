---
id: TASK-004.04
title: Text truncation with ellipsis
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: low
ordinal: 4400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR4, long article text in the speech bubble must be truncated with an ellipsis rather than overflowing or wrapping awkwardly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Article text exceeding the speech bubble's display length is truncated with an ellipsis
- [ ] #2 Truncation behavior verified with a long-title fixture article
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
