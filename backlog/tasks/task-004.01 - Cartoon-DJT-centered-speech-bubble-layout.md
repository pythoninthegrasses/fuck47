---
id: TASK-004.01
title: Cartoon DJT + centered speech bubble layout
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: high
ordinal: 4100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR4, position the cartoon DJT image (app/img/trump.png) in the bottom-left corner and render news content in a speech bubble centered on the page, replacing the current static SVG placeholder layout.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 DJT cartoon image is anchored to the bottom-left of the viewport on desktop
- [ ] #2 Speech bubble is horizontally and vertically centered and visually prominent
- [ ] #3 Layout holds at common desktop breakpoints (manual check in browser)
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
