---
id: TASK-002.02
title: Add sentiment analysis scoring
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-002
priority: high
ordinal: 2200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The PRD requires filtering articles by sentiment, not just DJT relevance. Currently utils/filter.py only computes a trump_relevance_score; there is no sentiment score. Add a lightweight sentiment analysis step (VADER or TextBlob per PRD Technical Considerations) that scores each article's sentiment and attaches the score alongside trump_relevance_score.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each stored article gains a sentiment score field computed from its title/description
- [ ] #2 Sentiment scoring uses a lightweight library (VADER or TextBlob) added as a project dependency via uv
- [ ] #3 A unit test asserts a known-negative sample scores negative and a known-positive sample scores positive
- [ ] #4 Sentiment scoring runs as part of the existing main.py pipeline after DJT relevance filtering
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
