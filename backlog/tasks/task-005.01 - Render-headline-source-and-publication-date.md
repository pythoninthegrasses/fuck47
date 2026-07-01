---
id: TASK-005.01
title: 'Render headline, source, and publication date'
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies:
  - TASK-003.01
documentation:
  - doc-001
parent_task_id: TASK-005
priority: medium
ordinal: 5100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR5, each displayed article must show its headline, source, and publication date.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each article card shows headline, source, and publication date
- [ ] #2 Publication date is formatted human-readably (not raw ISO timestamp)
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
