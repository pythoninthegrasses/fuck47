#!/usr/bin/env python

import duckdb
from html import escape
from pathlib import Path

ARCHIVE_STORE = 'filtered_articles'


def _dates_with_snapshots(archive_dir, store=ARCHIVE_STORE):
    """Dates (dir names) that have at least one snapshot, most recent first."""
    store_dir = Path(archive_dir) / store
    if not store_dir.exists():
        return []
    return sorted((d.name for d in store_dir.iterdir() if d.is_dir()), reverse=True)


def _articles_for_date(archive_dir, date, store=ARCHIVE_STORE):
    """Articles published on a date, deduped by url across same-day snapshot runs."""
    glob = str(Path(archive_dir) / store / date / '*.parquet')
    con = duckdb.connect()
    try:
        rows = con.execute(
            """
            SELECT url, title, description, source, published_at
            FROM read_parquet(?)
            GROUP BY url, title, description, source, published_at
            ORDER BY published_at DESC
            """,
            [glob],
        ).fetchall()
        columns = [col[0] for col in con.description]
    finally:
        con.close()
    return [dict(zip(columns, row, strict=False)) for row in rows]


def _render_fragment(date, articles):
    if not articles:
        body = '<p>No archived articles for this date.</p>'
    else:
        items = '\n'.join(
            f'  <li><a href="{escape(a["url"])}" target="_blank">{escape(a["title"] or a["url"])}</a>'
            f' &mdash; {escape(a["source"] or "")}</li>'
            for a in articles
        )
        body = f'<ul>\n{items}\n</ul>'
    return f'<h2>{escape(date)}</h2>\n{body}\n'


def _render_index(dates):
    if not dates:
        body = '<p>No archived runs yet.</p>'
    else:
        items = '\n'.join(
            f'  <li><a href="archive/{escape(d)}.html" hx-get="archive/{escape(d)}.html" '
            f'hx-target="#archive-content" hx-swap="innerHTML">{escape(d)}</a></li>'
            for d in dates
        )
        body = f'<ul>\n{items}\n</ul>'
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="utf-8">\n'
        '  <title>Article Archive</title>\n'
        '  <script src="https://unpkg.com/htmx.org@2"></script>\n'
        '</head>\n'
        '<body>\n'
        '  <h1>Article Archive</h1>\n'
        f'  {body}\n'
        '  <div id="archive-content"></div>\n'
        '</body>\n'
        '</html>\n'
    )


def render_archive(archive_dir='archive', output_dir='app/archive'):
    """Render a static htmx-driven archive index and per-date fragments.

    Reads the committed filtered_articles Parquet snapshots (see ArticleDB.archive_snapshot)
    and writes app/archive/index.html plus one app/archive/<date>.html fragment per date. Static
    output only, no server: fits GitHub Pages.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    dates = _dates_with_snapshots(archive_dir)
    for date in dates:
        articles = _articles_for_date(archive_dir, date)
        (output_path / f'{date}.html').write_text(_render_fragment(date, articles))

    (output_path / 'index.html').write_text(_render_index(dates))
    return dates


if __name__ == '__main__':
    from config import ARCHIVE_DIR

    render_archive(ARCHIVE_DIR)
