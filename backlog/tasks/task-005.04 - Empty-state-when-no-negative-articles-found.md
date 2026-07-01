---
id: TASK-005.04
title: Empty state when no negative articles found
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
ordinal: 5400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR5, handle the case where the pipeline produces zero negative-sentiment articles by showing a sensible empty state instead of a blank or broken speech bubble.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Building app/index.html with an empty filtered_articles.json renders a defined empty-state message in the speech bubble
- [ ] #2 Empty state is visually consistent with the rest of the design (Basecoat typography)
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
