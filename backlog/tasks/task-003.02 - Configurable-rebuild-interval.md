---
id: TASK-003.02
title: Configurable rebuild interval
status: Done
assignee: []
created_date: '2026-07-01 19:01'
updated_date: '2026-07-02 20:19'
labels: []
dependencies: []
documentation:
  - doc-001
parent_task_id: TASK-003
priority: medium
ordinal: 812.5
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per PRD FR3, the site rebuilds automatically on a configurable cadence. The original plan called for a `BUILD_INTERVAL_MINUTES` env var read through `config.py`, but that pattern does not fit the shipped architecture: the Python process only runs when GitHub Actions invokes it, so scheduling belongs in the workflow file rather than in the Python process. Rebuild cadence is controlled by the cron expression in `.github/workflows/news-refresh.yml`, with manual overrides via `workflow_dispatch`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Rebuild cadence is controlled by a cron schedule in .github/workflows/news-refresh.yml (currently `0 */8 * * *` — every 8 hours)
- [x] #2 Manual rebuild is supported via workflow_dispatch and push-to-main triggers
- [x] #3 Default cadence (8 hours) and workflow behavior are documented in docs/ci.md and linked from AGENTS.md
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Cadence shipped in `.github/workflows/news-refresh.yml` (d16f2ad): `schedule: cron: '0 */8 * * *'` plus `workflow_dispatch` and push-to-main triggers. Workflow runs `uv run main.py` (aggregation + render_index) then `uv run python -m utils.render` (archive), then commits any `archive/`, `app/archive/` diffs back to `main`. Failure path opens a labelled issue. No `config.py` entry added: a Python-side interval env var would be dead code because the process only runs when Actions invokes it. Documented in `docs/ci.md`, backlinked from AGENTS.md Deployment section (commit alongside this backlog update). DoD #4 (TDD) N/A: the deliverable is a YAML workflow file rather than testable Python code; correctness verified via successful CI runs on `main` — checked per user direction.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
8-hour cron rebuild shipped via `.github/workflows/news-refresh.yml` (d16f2ad), with `workflow_dispatch` and push-to-main for manual/on-demand runs. Cadence lives in the workflow rather than `config.py` because the Python process only runs when Actions invokes it — a runtime interval env var would be dead code. Documented in `docs/ci.md`; AGENTS.md Deployment section backlinks it. ACs rewritten to reflect the shipped architecture rather than the obsolete `BUILD_INTERVAL_MINUTES` plan.
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
