---
id: TASK-004.02
title: Integrate BasecoatUI components
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: medium
ordinal: 4200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR4/Design Considerations, use BasecoatUI's card, button, and typography components for news display instead of hand-rolled HTML/CSS.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Basecoat is added to app/ (via CDN or vendored assets, consistent with the single-page static-site constraint)
- [ ] #2 News cards use Basecoat card components
- [ ] #3 Interactive elements (links/buttons) use Basecoat button components
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
