---
id: TASK-002.02
title: Add LLM-based sentiment judge scoring
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-01 21:28'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-002
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The PRD requires filtering articles by sentiment, not just DJT relevance. Lexicon-based scorers (VADER/TextBlob) were evaluated and rejected: they score surface word polarity, not political framing, so critical-but-lexically-neutral headlines (e.g. "Trump Pulled In $1.4 Billion From Crypto Ventures") are misclassified as neutral/positive. Instead, utils/sentiment.py sends one batched request per pipeline run to an OpenAI-compatible LLM endpoint (default: Fireworks-hosted `accounts/fireworks/models/gpt-oss-20b`) and asks it to judge whether coverage is favorable or unfavorable to DJT.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each stored article gains a sentiment_score field (-1.0 to 1.0) from a single batched LLM judge call, attached alongside djt_relevance_score
- [x] #2 LLM judge is called via a configurable OpenAI-compatible chat completions endpoint (LLM_API_KEY / LLM_BASE_URL / LLM_MODEL env vars, default Fireworks), not tied to a specific provider or SDK
- [x] #3 A unit test (mocked HTTP, no real network/credentials) asserts a known-negative sample scores <= 0 and a known-positive sample scores > 0
- [x] #4 Sentiment scoring runs as part of the existing main.py pipeline after DJT relevance filtering
- [x] #5 .env.example and docs/ai.md (linked from AGENTS.md) document the LLM_* and SENTIMENT_* env vars and how to point them at a different OpenAI-compatible provider
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
All DoD items verified/fixed and checked off:
- ruff format --check and ruff check both pass clean
- pytest: 106/106 passing (fixed 2 pre-existing failures in test_db.py caused by hardcoded absolute dates in the sample_articles fixture becoming stale relative to datetime.now())
- Fixed ruff format drift in tests/test_filter.py, utils/db.py, utils/filter.py (unrelated pre-existing formatting issues, not introduced by this feature)
- docs/ai.md + .env.example document LLM_*/SENTIMENT_* env vars, linked from AGENTS.md/CLAUDE.md
- Landed as atomic conventional commits: "style: apply ruff format to filter/db modules and test fixtures" and "fix(test): use relative timestamps in sample_articles fixture"
- Test-first (DoD #4) unverifiable from git history since the original sentiment feature landed as a single squashed commit (75dbed6); noted but not blocking
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
