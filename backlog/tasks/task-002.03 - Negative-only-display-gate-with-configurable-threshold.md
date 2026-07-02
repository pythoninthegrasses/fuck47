---
id: TASK-002.03
title: Negative-only display gate with configurable threshold
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-01 21:30'
labels: []
dependencies:
  - TASK-002.02
documentation:
  - doc-001
parent_task_id: TASK-002
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR2, only articles with negative sentiment (below a configurable threshold) should be included in filtered_articles.json for display. Depends on the LLM sentiment judge existing (see sibling subtask "Add LLM-based sentiment judge scoring").
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A new env-configurable threshold (SENTIMENT_MAX_SCORE) controls the negative-sentiment cutoff, following the pattern of DJT_FILTER_MIN_SCORE in config.py
- [x] #2 Articles with sentiment_score above the threshold are excluded from filtered_articles.json (inclusive: score <= threshold is kept)
- [x] #3 Default threshold value (0.0) is documented in config.py, .env.example, and docs/ai.md
- [x] #4 Unit test covers articles on both sides of the threshold boundary, including the boundary value itself
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
All DoD items verified and checked off, no fixes needed:
- ruff format --check and ruff check both pass clean
- pytest: 106/106 passing, including a dedicated boundary test (tests/test_main.py::test_negative_and_positive_articles_split_at_threshold) covering scores below, at, and above SENTIMENT_MAX_SCORE
- SENTIMENT_MAX_SCORE documented in config.py, .env.example, and docs/ai.md
- Landed as part of commit 75dbed6 "feat: replace VADER/TextBlob with an LLM sentiment judge" (atomic conventional commit)
- Test-first (DoD #4) unverifiable from git history since this landed in the same squashed commit as the sentiment judge itself; noted but not blocking
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [x] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [x] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
