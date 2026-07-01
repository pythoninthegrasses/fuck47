---
id: TASK-004.06
title: Loading indicators for content fetch
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies:
  - TASK-004.03
documentation:
  - doc-001
parent_task_id: TASK-004
priority: low
ordinal: 4600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD Design Considerations, show a subtle loading indicator while HTMX content is being fetched.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An HTMX hx-indicator is shown during content swap requests
- [ ] #2 Indicator is unobtrusive and matches the site's visual style
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
