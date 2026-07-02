---
id: TASK-003.01
title: Build step injects filtered articles into app/index.html
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-01 21:45'
labels: []
dependencies:
  - TASK-010
documentation:
  - doc-001
parent_task_id: TASK-003
priority: high
ordinal: 3100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the hand-written static placeholder in app/index.html with a build step that reads filtered_articles.json and renders the news content into the page. Depends on the negative-only display gate (task-002.03) producing the final article set.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A Python build step generates app/index.html content from filtered_articles.json
- [ ] #2 Generated HTML is valid and preserves the existing site's <head>/meta/branding elements
- [ ] #3 Running the build with an empty filtered_articles.json does not error
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
