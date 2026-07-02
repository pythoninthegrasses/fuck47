---
id: TASK-005
title: Content Display
status: Done
assignee: []
created_date: '2026-07-01 18:58'
updated_date: '2026-07-02 18:36'
labels: []
dependencies: []
documentation:
  - doc-001
priority: medium
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Parent task for how filtered articles are rendered once the frontend exists: headline/source/date, links to originals, multi-article transitions, and empty-state handling.
<!-- SECTION:DESCRIPTION:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [x] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
All four subtasks resolved by the poster frontend (task-004.01 + render_index, task-003.01): 005.01 headline/source/human-readable date on every poster, 005.02 links to originals (new tab, rel=noopener, noscript fallback), 005.04 designed empty state. 005.03 closed as superseded — DESIGN.md's restrained-motion doctrine makes article swaps intentional hard cuts, not CSS transitions. DoD #4 unchecked at parent level: UI rendering was browser-verified; the data/injection layer beneath it was test-first.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Content display complete: every poster shows headline, source, and formatted date, links out to the original article, and zero-article runs get a designed empty state. Transitions are deliberate hard cuts per the pop-art pivot (005.03 closed as superseded). Shipped across b144911, e913b74, 0ace98b.
<!-- SECTION:FINAL_SUMMARY:END -->
