---
id: TASK-005.02
title: Link to original articles
status: To Do
assignee: []
created_date: '2026-07-01 19:02'
labels: []
dependencies:
  - TASK-003.01
documentation:
  - doc-001
parent_task_id: TASK-005
priority: medium
ordinal: 5200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR5, each displayed article must link out to its original source URL.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each article card links to its original article URL
- [ ] #2 Links open in a new tab (target="_blank" with rel="noopener")
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
