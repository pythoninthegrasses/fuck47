---
id: TASK-004.03
title: HTMX-driven dynamic content loading
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: medium
ordinal: 4300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR6, use HTMX so news content updates without full page reloads, consistent with the project's htmx + alpine.js-only frontend constraint.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 HTMX is added to app/index.html
- [ ] #2 News content region is swapped via an HTMX request rather than a full page reload
- [ ] #3 Behavior verified manually in a browser
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
