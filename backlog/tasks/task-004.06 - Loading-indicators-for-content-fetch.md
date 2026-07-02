---
id: TASK-004.06
title: Loading indicators for content fetch
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:33'
labels: []
dependencies:
  - TASK-004.03
documentation:
  - doc-001
parent_task_id: TASK-004
priority: low
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD Design Considerations, show a subtle loading indicator while HTMX content is being fetched.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An HTMX hx-indicator is shown during content swap requests
- [ ] #2 Indicator is unobtrusive and matches the site's visual style
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Superseded by the pop-art poster pivot: the index page performs no content fetches (build-time injection + instant Alpine swaps between already-loaded data), so there is nothing to indicate. Depended on task-004.03, closed for the same reason. Closed without implementation.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Closed as superseded, not implemented. The index page performs no content fetches (build-time injection, instant Alpine swaps), so there is no loading state to indicate. Followed its dependency task-004.03 into closure. ACs/DoD intentionally left unchecked.
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
