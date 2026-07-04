---
id: TASK-007.02
title: Set up CI pipeline
status: Done
assignee: []
created_date: '2026-07-01 19:02'
updated_date: '2026-07-04 04:35'
labels: []
dependencies: []
references:
  - TODO.md
parent_task_id: TASK-007
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Carried over from TODO.md. Add a GitHub Actions workflow that installs dependencies via uv and runs ruff and pytest on every push/PR.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A CI workflow (e.g. .github/workflows/ci.yml) installs dependencies via uv
- [x] #2 CI runs ruff format --check, ruff check, and pytest on push and pull_request
- [x] #3 CI passes on the current main branch
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
CI run 28695047743 passed on main (formatting, lint, pytest all green) after fixing `uv sync` to include the dev extra (ruff/pytest live in `[project.optional-dependencies].dev`, not the base deps).
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [x] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
