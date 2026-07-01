---
id: TASK-007.02
title: Set up CI pipeline
status: To Do
assignee: []
created_date: '2026-07-01 19:02'
labels: []
dependencies: []
references:
  - TODO.md
parent_task_id: TASK-007
priority: high
ordinal: 7200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Carried over from TODO.md. Add a GitHub Actions workflow that installs dependencies via uv and runs ruff and pytest on every push/PR.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A CI workflow (e.g. .github/workflows/ci.yml) installs dependencies via uv
- [ ] #2 CI runs ruff format --check, ruff check, and pytest on push and pull_request
- [ ] #3 CI passes on the current main branch
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
