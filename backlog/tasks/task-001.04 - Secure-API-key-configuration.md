---
id: TASK-001.04
title: Secure API key configuration
status: Done
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
parent_task_id: TASK-001
priority: medium
ordinal: 1400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Store and load NewsAPI/other API keys from environment variables, never committed to the repository. Implemented in config.py.
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
config.py reads API keys from environment variables; no secrets committed.
<!-- SECTION:FINAL_SUMMARY:END -->
