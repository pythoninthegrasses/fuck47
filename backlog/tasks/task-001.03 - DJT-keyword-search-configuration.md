---
id: TASK-001.03
title: DJT keyword search configuration
status: Done
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
parent_task_id: TASK-001
priority: medium
ordinal: 1300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Configure keyword/category search terms ("Donald Trump", "Trump", "45th President", "47th President") used to query NewsAPI/RSS. Implemented via config.py categories.
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
config.py category/keyword configuration consumed by main.py's fetch step.
<!-- SECTION:FINAL_SUMMARY:END -->
