---
id: TASK-004.02
title: Integrate BasecoatUI components
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:33'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: medium
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR4/Design Considerations, use BasecoatUI's card, button, and typography components for news display instead of hand-rolled HTML/CSS.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Basecoat is added to app/ (via CDN or vendored assets, consistent with the single-page static-site constraint)
- [ ] #2 News cards use Basecoat card components
- [ ] #3 Interactive elements (links/buttons) use Basecoat button components
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Superseded by the pop-art poster pivot (task-004.01, 2026-07-02): DESIGN.md commits to a hand-rolled print system (silkscreen/halftone plates, Anton/Special Elite paste-up type) with no component library. BasecoatUI no longer fits the design direction. Closed without implementation.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Closed as superseded, not implemented. The pop-art poster pivot (task-004.01) committed DESIGN.md to a hand-rolled print system with no component library, so BasecoatUI integration no longer applies. ACs/DoD intentionally left unchecked.
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
