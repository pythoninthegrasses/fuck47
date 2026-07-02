---
id: TASK-003.03
title: Preserve GitHub Pages compatibility
status: In Progress
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 18:31'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-003
priority: high
ordinal: 843.75
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ensure the generated app/index.html and any new build artifacts remain compatible with the existing GitHub Pages deployment workflow (.github/workflows/static.yml) and custom domain (fuckfortyseven.org).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Deployed site continues to serve from app/ via the existing GitHub Pages workflow with no workflow changes required beyond what's necessary for the new build step
- [x] #2 Custom domain (CNAME) configuration remains intact after the build step runs
- [ ] #3 A manual or CI dry-run of the workflow succeeds after the build step is added
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Partially verified this session: the build step only writes app/index.html (in-place marker swap) and app/archive/ — nothing touches CNAME or Pages settings (AC #2 checked; the custom domain is configured in repository settings, no CNAME file exists in app/). AC #1 and #3 need an actual push/CI run of .github/workflows/static.yml to verify the deployed site, so they stay open. No workflow changes were required: the new assets (fonts, img/djt, archive stub) all live under app/ which the workflow already publishes wholesale.
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
