---
id: TASK-002.01
title: DJT relevance filtering
status: Done
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
parent_task_id: TASK-002
priority: high
ordinal: 2100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Score and filter articles by DJT relevance before display. Implemented in utils/filter.py (DJTNewsFilter, trump_relevance_score, DJT_FILTER_MIN_SCORE).
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

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
utils/filter.py DJTNewsFilter with configurable DJT_FILTER_MIN_SCORE; tests in tests/test_filter.py.
<!-- SECTION:FINAL_SUMMARY:END -->
