# CI

Two GitHub Actions workflows drive the site.

## `.github/workflows/news-refresh.yml`

Runs the aggregation pipeline and rebuilds the rendered output, then commits
any new archive content back to `main`.

### Triggers

- `schedule: cron: '0 */8 * * *'` — every 8 hours (default rebuild cadence).
- `push` to `main` — rebuild on any pushed change.
- `workflow_dispatch` — manual runs from the Actions tab.

### Steps

1. `uv run main.py` — fetch, filter, sentiment-score, and write
   `filtered_articles.duckdb`; inject articles into `app/index.html` via
   `render_index`.
2. `uv run python -m utils.render` — rebuild the htmx-driven archive at
   `app/archive/` from the Parquet snapshot history.
3. Commit any changes under `archive/` and `app/archive/` back to `main`
   (skipped if nothing changed).

### Failure handling

On workflow failure, a `bug`/`automated`-labelled issue is opened with a
link to the failed run. Because the pipeline only writes `app/index.html`
on success, a failed run cannot deploy a broken page — Pages continues
serving the last-known-good file.

### Rebuild cadence

The cron expression in this workflow file is the single source of truth for
rebuild frequency. There is no runtime env var (`BUILD_INTERVAL_MINUTES` or
equivalent) — a Python-side interval knob would be dead code because the
Python process only runs when Actions invokes it.

## `.github/workflows/static.yml`

Publishes `app/` to GitHub Pages on push to `main` and via
`workflow_dispatch`.

Concurrency is pinned to the `pages` group so in-flight production deploys
are never cancelled. The custom domain (`fuckfortyseven.org`) is configured
in the repository Pages settings — no `CNAME` file exists in `app/`.

### Workflow coupling

The two workflows are intentionally decoupled. `news-refresh` commits
refreshed content to `main`; that push then triggers `static.yml` to deploy
it. A failed `news-refresh` run never pushes anything, so Pages always serves
the last committed `app/index.html`.
