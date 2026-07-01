---
id: TASK-009
title: 'Data Quality: Article Text Cleanup'
status: To Do
assignee: []
created_date: '2026-07-01 18:58'
updated_date: '2026-07-01 19:00'
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
- [ ] #1 Smart-quote unicode escapes (‘ ’ “ ”) are decoded to their literal characters in stored article text
- [ ] #2 Escaped double quotes (\") in article text render as plain double quotes, not literal backslash-quote sequences
- [ ] #3 A regression test in tests/ covers the cleanup against a fixture containing each problematic sequence
- [ ] #4 Existing tests/fixtures/articles.json and tests/test_db.py continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Likely fix point: utils/db.py where articles are stored/serialized, or wherever article text is read from NewsAPI/RSS responses before being written to TinyDB. Confirm exact location during grooming; add a targeted unit test first (TDD) using a string containing the escaped sequences from TODO.md.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
