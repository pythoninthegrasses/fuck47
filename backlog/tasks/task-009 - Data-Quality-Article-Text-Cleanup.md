---
id: TASK-009
title: 'Data Quality: Article Text Cleanup'
status: Done
assignee: []
created_date: '2026-07-01 18:58'
updated_date: '2026-07-04 04:49'
labels: []
dependencies: []
references:
  - TODO.md
priority: medium
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix mangled characters in generated articles.json: unicode smart-quote escapes (‘, ’, “, ”) and escaped double quotes (\") render incorrectly in article titles/descriptions. Carried over from TODO.md.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Smart-quote unicode escapes (‘ ’ “ ”) are decoded to their literal characters in stored article text
- [x] #2 Escaped double quotes (\") in article text render as plain double quotes, not literal backslash-quote sequences
- [x] #3 A regression test in tests/ covers the cleanup against a fixture containing each problematic sequence
- [x] #4 Existing tests/fixtures/articles.json and tests/test_db.py continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Likely fix point: utils/db.py where articles are stored/serialized, or wherever article text is read from NewsAPI/RSS responses before being written to TinyDB. Confirm exact location during grooming; add a targeted unit test first (TDD) using a string containing the escaped sequences from TODO.md.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Investigated after the TinyDB→DuckDB/Parquet migration: the described bug no longer exists. `render.py` injects article text via `json.dumps(articles, ensure_ascii=False)`, so smart quotes (‘ ’ “ ”) are emitted as literal unicode glyphs, not `\u201x` escapes, and embedded double quotes become valid JSON `\"` (correctly restored by `JSON.parse`), not mangled backslash-quote text. Verified against `tests/fixtures/articles.parquet` (44 rows, smart quotes literal, zero mangled sequences) and the live `app/index.html` ARTICLES block. The task's references to `articles.json`/TinyDB are stale post-migration.

Added a regression test, `test_smart_quotes_and_embedded_quotes_round_trip_cleanly` in `tests/test_render.py`, asserting a title with both a smart quote and an embedded double quote injects and round-trips through `json.loads` unchanged.

No production code changes were needed in `utils/db.py` or `utils/render.py` — the pipeline was already correct.

Also fixed an unrelated Python 3 SyntaxError spotted while reading `utils/sentiment.py:53` (`except json.JSONDecodeError, TypeError:` → `except (json.JSONDecodeError, TypeError):`), which would have broken the module's import.
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
