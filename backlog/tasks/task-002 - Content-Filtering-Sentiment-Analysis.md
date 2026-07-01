---
id: TASK-002
title: Content Filtering & Sentiment Analysis
status: In Progress
assignee: []
created_date: '2026-07-01 18:58'
labels: []
dependencies: []
documentation:
  - doc-001
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Parent task for filtering aggregated articles down to genuinely negative DJT coverage. DJT relevance filtering is already built (utils/filter.py); sentiment analysis and the negative-only display gate described in the PRD are not yet implemented.
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
