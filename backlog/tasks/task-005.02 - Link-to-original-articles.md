---
id: TASK-005.02
title: Link to original articles
status: Done
assignee: []
created_date: '2026-07-01 19:02'
updated_date: '2026-07-02 18:35'
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
- [x] #1 Each article card links to its original article URL
- [x] #2 Links open in a new tab (target="_blank" with rel="noopener")
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Each poster's byline has a "Read the story" link bound to the article URL with target="_blank" rel="noopener". The noscript fallback list also links every article directly (covered by tests/test_render.py::test_writes_noscript_fallback_links, and URL escaping by the XSS test). DoD #4 unchecked for the visible UI link (browser-verified); the noscript link path was test-first.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Every poster links to its original article ("Read the story", new tab with rel=noopener); noscript users get a plain link list. Shipped in b144911 + e913b74.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [x] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
