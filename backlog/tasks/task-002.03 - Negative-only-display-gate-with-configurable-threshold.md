---
id: TASK-002.03
title: Negative-only display gate with configurable threshold
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-01 19:01'
labels: []
dependencies:
  - TASK-002.02
documentation:
  - doc-001
parent_task_id: TASK-002
priority: high
ordinal: 2300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR2, only articles with negative sentiment (below a configurable threshold) should be included in filtered_articles.json for display. Depends on sentiment scoring existing (see sibling subtask "Add sentiment analysis scoring").
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A new env-configurable threshold (e.g. SENTIMENT_MAX_SCORE) controls the negative-sentiment cutoff, following the pattern of DJT_FILTER_MIN_SCORE in config.py
- [ ] #2 Articles with sentiment score above the threshold are excluded from filtered_articles.json
- [ ] #3 Default threshold value is documented in config.py and README
- [ ] #4 Unit test covers articles on both sides of the threshold boundary
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
