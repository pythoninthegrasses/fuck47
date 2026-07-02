---
id: TASK-007
title: Testing & CI
status: In Progress
assignee: []
created_date: '2026-07-01 18:58'
updated_date: '2026-07-02 20:20'
labels: []
dependencies: []
references:
  - TODO.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Parent task for project-wide testing/CI infrastructure carried over from TODO.md: pre-commit hooks and a CI pipeline are not yet set up despite an existing pytest suite.
<!-- SECTION:DESCRIPTION:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
