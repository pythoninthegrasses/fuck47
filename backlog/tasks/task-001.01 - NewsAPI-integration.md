---
id: TASK-001.01
title: NewsAPI integration
status: Done
assignee: []
created_date: '2026-07-01 19:00'
labels: []
dependencies: []
parent_task_id: TASK-001
priority: medium
ordinal: 1100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fetch DJT-related articles from NewsAPI. Implemented in utils/newsapi.py.
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
utils/newsapi.py; tests in tests/test_newsapi.py.
<!-- SECTION:FINAL_SUMMARY:END -->
