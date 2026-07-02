---
id: TASK-004.05
title: Responsive mobile/desktop layout
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:30'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: medium
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR4/Design Considerations (updated for the pop-art poster pivot), ensure the poster layout — portrait, headline strips, description plate, controls — scales correctly on mobile and desktop.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Layout is checked at a mobile viewport width and a desktop viewport width
- [x] #2 Portrait, headline, and description remain legible and non-overlapping at both sizes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified via Playwright at 1440x900 (side-by-side: 55vw portrait right, type column left), 768x1024 and 390x844 (stacked: pinned masthead, 58dvh portrait, headline strips pulled up over the image, description below, prev/next fixed in the thumb zone). Key responsive mechanics: type column flows top-to-bottom so variable-length titles can never collide with the description; headline sizing is length-tiered (data-len long/xlong) with separate clamp() ramps per breakpoint; mobile re-anchors children above the portrait (static type-col loses its z-index) and resets the control row's desktop left anchor. Defects found and fixed during inspection: masthead buried under portrait, headline painting beneath the image on stacked layouts, LoC portrait's transparent pillarboxes shrinking the print, below-the-fold next button. DoD #4 (test-first) unchecked: this is CSS/layout work verified by browser inspection; no failing test preceded it.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Responsive poster layout verified at 1440/768/390 with all breakpoint defects found during browser inspection fixed (masthead pinning, stacked z-order, control-row anchoring, portrait pillarbox trim). Shipped in b144911 and 0ace98b. AC wording updated from speech-bubble to poster terms per the task-004.01 pivot.
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
