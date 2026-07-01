---
id: TASK-007.01
title: Set up pre-commit hooks
status: To Do
assignee: []
created_date: '2026-07-01 19:02'
labels: []
dependencies: []
references:
  - TODO.md
parent_task_id: TASK-007
priority: high
ordinal: 7100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Carried over from TODO.md. Add a pre-commit configuration that runs ruff format --check and ruff check on Python files before each commit.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A .pre-commit-config.yaml is added running ruff format --check and ruff check
- [ ] #2 pre-commit run --all-files passes on the current codebase
- [ ] #3 Setup instructions for pre-commit are documented in README.md
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
