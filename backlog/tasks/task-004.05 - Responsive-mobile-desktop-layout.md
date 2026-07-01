---
id: TASK-004.05
title: Responsive mobile/desktop layout
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: medium
ordinal: 4500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR4/Design Considerations, ensure the cartoon + speech bubble layout scales correctly on mobile and desktop.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Layout is checked at a mobile viewport width and a desktop viewport width
- [ ] #2 Speech bubble and DJT cartoon remain legible and non-overlapping at both sizes
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
