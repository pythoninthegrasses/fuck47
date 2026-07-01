---
id: TASK-002.04
title: Graceful fallback when sentiment analysis fails
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-002
priority: medium
ordinal: 2400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR2, sentiment analysis must fail gracefully (e.g. malformed article text, library exception) without breaking the build or crashing main.py.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An article whose sentiment analysis raises an exception is excluded (or safely defaulted) rather than crashing the pipeline
- [ ] #2 The failure is logged via the existing eliot logging setup
- [ ] #3 Unit test simulates a sentiment-analysis failure and asserts the pipeline completes successfully
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
