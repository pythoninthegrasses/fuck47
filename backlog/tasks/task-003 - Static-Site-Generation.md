---
id: TASK-003
title: Static Site Generation
status: In Progress
assignee: []
created_date: '2026-07-01 18:58'
updated_date: '2026-07-02 16:14'
labels: []
dependencies: []
documentation:
  - doc-001
priority: high
ordinal: 500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Parent task for generating app/index.html from filtered_articles.json on a configurable interval, replacing the current hand-written placeholder while preserving GitHub Pages compatibility.
<!-- SECTION:DESCRIPTION:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
