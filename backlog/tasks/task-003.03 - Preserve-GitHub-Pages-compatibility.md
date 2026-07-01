---
id: TASK-003.03
title: Preserve GitHub Pages compatibility
status: To Do
assignee: []
created_date: '2026-07-01 19:01'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-003
priority: high
ordinal: 3300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ensure the generated app/index.html and any new build artifacts remain compatible with the existing GitHub Pages deployment workflow (.github/workflows/static.yml) and custom domain (fuckfortyseven.org).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Deployed site continues to serve from app/ via the existing GitHub Pages workflow with no workflow changes required beyond what's necessary for the new build step
- [ ] #2 Custom domain (CNAME) configuration remains intact after the build step runs
- [ ] #3 A manual or CI dry-run of the workflow succeeds after the build step is added
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
