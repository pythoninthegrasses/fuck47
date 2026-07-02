---
id: TASK-005.04
title: Empty state when no negative articles found
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
ordinal: 5400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR5, handle the case where the pipeline produces zero negative-sentiment articles by showing a sensible empty state instead of a blank or broken speech bubble.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Building app/index.html with an empty filtered articles store renders a defined empty-state message
- [x] #2 Empty state is visually consistent with the rest of the design
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The poster page ships a designed empty state: when the injected articles array is empty, Alpine renders "NO BAD NEWS YET." as the headline strips with "The presses are warming up. Try the back issues below, or come back after the next print run." on the story plate — same typography, plates, and layout as a real poster (AC #2 originally said "Basecoat typography"; reworded post-pivot, consistency is with the print design system). Prev/next controls hide when there is nothing to rotate. Build side: a missing store leaves the page untouched (test-first: tests/test_render.py::test_missing_db_leaves_file_unchanged); an empty store injects [] without error. Empty state verified in-browser by forcing articles=[] at 390px.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Zero-article runs render a designed on-brand empty state ("NO BAD NEWS YET.") instead of a blank page; controls hide, back-issues link remains. Missing-store no-op is TDD-covered; empty state browser-verified. Shipped in b144911 + e913b74. AC wording updated from speech-bubble/Basecoat to poster terms per the task-004.01 pivot.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [x] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [x] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
