---
id: TASK-005.01
title: 'Render headline, source, and publication date'
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:35'
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
- [x] #1 Each article card shows headline, source, and publication date
- [x] #2 Publication date is formatted human-readably (not raw ISO timestamp)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Delivered by the poster layout (task-004.01): each poster shows the headline as Anton paste-up strips, and the byline row on the story plate shows source (cleaned of feed suffixes like "NYT > U.S. > Politics" -> "NYT") and the publication date formatted via toLocaleDateString as e.g. "Jul 2, 2026" (falls back to the raw string if unparseable). "Card" in the AC reads as "poster" post-pivot. DoD #4 unchecked: markup/UI work, browser-verified rather than test-first (the injected data path itself is TDD-covered under task-003.01).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Headline, source, and human-readable publication date render on every poster (headline strips + byline row). Shipped in b144911 within the poster page; data supplied by render_index (task-003.01).
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
