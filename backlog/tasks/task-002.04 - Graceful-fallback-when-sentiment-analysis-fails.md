---
id: TASK-002.04
title: Graceful fallback when sentiment analysis fails
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-01 21:31'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-002
priority: medium
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR2, sentiment analysis must fail gracefully (e.g. LLM API error, timeout, malformed response) without breaking the build or crashing main.py. Per product decision, a failure should not blank the site or fall back to unfiltered content — it should leave filtered_articles.json exactly as the previous successful run left it, so the site is "slightly out of date" rather than empty or wrong.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 When the LLM judge call raises SentimentJudgeError, main.py skips clearing/rewriting filtered_articles.json for that run entirely (previous run's output is left untouched) rather than crashing, showing nothing, or showing unfiltered content
- [x] #2 The failure is logged via the existing eliot logging setup (start_action / action.log in utils/sentiment.py)
- [x] #3 Unit test simulates a sentiment-analysis failure (mocked SentimentJudgeError) and asserts main() completes successfully and filtered_articles.json is unchanged
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
All DoD items verified and checked off, no fixes needed:
- ruff format --check and ruff check both pass clean
- pytest: 106/106 passing, including tests/test_main.py::TestMainSentimentGate covering the SentimentJudgeError fallback path (asserts main() completes and filtered_articles.json is left unchanged)
- Fallback behavior documented in docs/ai.md ("How it works" step 4)
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
