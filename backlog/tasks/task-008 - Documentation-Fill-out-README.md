---
id: TASK-008
title: 'Documentation: Fill out README'
status: To Do
assignee: []
created_date: '2026-07-01 18:58'
labels: []
dependencies: []
references:
  - TODO.md
priority: low
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
README.md currently contains only a project title. Carried over from TODO.md: populate it with a real project overview and setup/usage instructions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 README.md describes what the project does and links to the live site (fuckfortyseven.org)
- [ ] #2 README.md documents setup via uv (uv sync / uv run)
- [ ] #3 README.md documents how to run the pipeline (main.py) and the test suite (pytest)
- [ ] #4 README.md documents required environment variables (API keys, config) without exposing secret values
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
