---
id: TASK-003.02
title: Configurable rebuild interval
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-003
priority: medium
ordinal: 3200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR3, the site must rebuild automatically based on a configurable time interval, set via environment variable following the config.py pattern used elsewhere.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A new env var (e.g. BUILD_INTERVAL_MINUTES) controls rebuild cadence, read via config.py
- [ ] #2 Rebuild scheduling mechanism (e.g. GitHub Actions cron) is documented
- [ ] #3 Default interval value is documented
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
