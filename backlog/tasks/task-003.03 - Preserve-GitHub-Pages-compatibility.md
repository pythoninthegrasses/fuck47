---
id: TASK-003.03
title: Preserve GitHub Pages compatibility
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 20:19'
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
- [x] #1 Deployed site continues to serve from app/ via the existing GitHub Pages workflow with no workflow changes required beyond what's necessary for the new build step
- [x] #2 Custom domain (CNAME) configuration remains intact after the build step runs
- [x] #3 A manual or CI dry-run of the workflow succeeds after the build step is added
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC #1 and #3 confirmed: both `.github/workflows/static.yml` and `.github/workflows/news-refresh.yml` are live on `main` (news-refresh shipped in d16f2ad). The deployed site continues to serve from `app/` via the unchanged `static.yml` workflow with no workflow changes required to `static.yml` itself — the new build step only writes `app/index.html` and `app/archive/`, both already under the published path. Per user direction, marking without an additional live curl since the deploy history on `main` demonstrates the workflow succeeds after the build step was added. DoD #4 (TDD) N/A: this task is a compatibility verification rather than a code feature; checked per user direction.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Pages compatibility preserved end-to-end. `static.yml` deploys `app/` unchanged; `news-refresh.yml` commits pipeline output back to `main` where `static.yml` picks it up. Custom domain lives in repo Pages settings, no CNAME file needed. Verified via successful deploy history on `main` following d16f2ad.
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
