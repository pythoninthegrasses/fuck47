---
id: TASK-001.05
title: Article storage and stale-data cleanup
status: Done
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
parent_task_id: TASK-001
priority: medium
ordinal: 1500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Store fetched articles in TinyDB and clear out old/stale articles on each run. Implemented in utils/db.py.
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
utils/db.py TinyDB storage with old-article clearing; tests in tests/test_db.py.
<!-- SECTION:FINAL_SUMMARY:END -->
