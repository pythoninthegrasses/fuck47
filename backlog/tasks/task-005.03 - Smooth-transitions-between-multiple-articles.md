---
id: TASK-005.03
title: Smooth transitions between multiple articles
status: Done
assignee: []
created_date: '2026-07-01 19:02'
updated_date: '2026-07-02 18:35'
labels: []
dependencies:
  - TASK-005.01
documentation:
  - doc-001
parent_task_id: TASK-005
priority: low
ordinal: 5300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR5, when multiple negative articles are available, display them with smooth transitions rather than an abrupt swap.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Switching between articles in the speech bubble uses a CSS transition/animation rather than an instant swap
- [ ] #2 Transition verified manually in a browser
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Superseded by the pop-art poster pivot: DESIGN.md commits to restrained motion — poster rotation is a deliberate hard cut ("flipping through a stack of flyers"), so a CSS transition between articles would contradict the shipped design. Auto-advance (12s), prev/next buttons, and arrow keys handle multi-article display; prefers-reduced-motion disables auto-advance. Closed without implementing the transition described in the ACs.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Closed as superseded, not implemented as specified. Multi-article display shipped (rotation + controls), but transitions are intentionally instant hard cuts per DESIGN.md's restrained-motion doctrine — the AC's "CSS transition rather than an instant swap" is the opposite of the chosen design. ACs/DoD intentionally left unchecked.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
