---
id: TASK-004.01
title: 'Pop-art poster layout: rotating DJT images with punk-flyer typography'
status: In Progress
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:10'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Pivot from the original cartoon-DJT-with-speech-bubble concept (PRD FR4). Instead, render each article as a full-viewport pop-art poster: a rotating DJT image, treated with muted pop-art print filters (Warhol/Lichtenstein — halftone, posterization, misregistered muted color plates), occupies the majority of the viewport. The article headline is set large in Raymond Pettibon / Black Flag punk-flyer lettering (dense condensed heavy caps, xerox-black energy) with the smaller description beneath in cramped typewriter-style text. See PRODUCT.md (Brand Personality, Design Principles) for the full aesthetic direction; reference artifacts in ~/Desktop/fuck47/ (black_flag_raymond_pettibon/, pop_art/).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Rotating DJT image occupies the majority of the viewport with a muted pop-art print treatment (halftone/posterize/misregistered muted color plates)
- [x] #2 Article headline is the dominant typographic element, in Pettibon-style condensed heavy caps; description is smaller, subordinate text
- [x] #3 Image rotation between articles has a prefers-reduced-motion alternative
- [x] #4 Headlines and descriptions remain legible over poster imagery at common desktop and mobile breakpoints (manual check in browser)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented in app/index.html (poster page) + utils/render.py render_index (build-step injection, TDD in tests/test_render.py::TestRenderIndex). Duotone via SVG #silkscreen filter (saturate 0 -> contrast -> posterize 5 -> duotone map to Xerox Black/Silkscreen Ground) with CSS radial-gradient halftone overlay; misregistered tan/olive plates; Anton headline paste-up strips (length-tiered sizing via data-len); Special Elite body on Flyer Stock plate. Rotation: hard cuts, auto-advance 12s (disabled under prefers-reduced-motion, paused when tab hidden), Next button + arrow keys. Verified in browser at 1440/768/390 incl. empty state and keyboard advance; ruff + pytest green. Commits pending.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
