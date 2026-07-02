---
id: TASK-004.04
title: Text truncation with ellipsis
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:33'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-004
priority: low
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR4, long article text in the speech bubble must be truncated with an ellipsis rather than overflowing or wrapping awkwardly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Article text exceeding the speech bubble's display length is truncated with an ellipsis
- [ ] #2 Truncation behavior verified with a long-title fixture article
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Superseded by the pop-art poster pivot: the speech bubble no longer exists. Long-title overflow is handled by length-tiered headline sizing (data-len long/xlong clamps in app/index.html) rather than ellipsis truncation — headlines are the poster's show and are never cut. Full descriptions are displayed on the story plate. Closed without implementation.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Closed as superseded, not implemented. The speech bubble no longer exists; long-title overflow is handled by length-tiered headline sizing (data-len clamps) and headlines are never cut — they're the poster's punchline. ACs/DoD intentionally left unchecked.
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
