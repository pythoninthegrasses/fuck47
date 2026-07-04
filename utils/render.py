#!/usr/bin/env python

import duckdb
import hashlib
import json
import re
from html import escape
from pathlib import Path

ARCHIVE_STORE = 'filtered_articles'
INDEX_MARKER_BEGIN = '<!-- ARTICLES:BEGIN -->'
INDEX_MARKER_END = '<!-- ARTICLES:END -->'

SLUG_MAX_LEN = 60


def _slugify(title, url=None):
    """Human-readable, URL-hash-safe slug for an article.

    Lowercases the title, collapses runs of non-alphanumeric characters into a
    single hyphen, and truncates to SLUG_MAX_LEN at a word boundary. Falls back
    to a short hash of `url` when the title yields no usable characters (missing,
    empty, or all punctuation) so every article still gets a stable, non-empty id.
    """
    slug = re.sub(r'[^a-z0-9]+', '-', (title or '').lower()).strip('-')
    if not slug:
        return hashlib.sha1((url or '').encode()).hexdigest()[:8]
    if len(slug) > SLUG_MAX_LEN:
        slug = slug[:SLUG_MAX_LEN].rsplit('-', 1)[0]
    return slug


def _assign_unique_slugs(articles):
    """Set a `slug` key on each article dict, deduped within this list via -2, -3, ... suffixes."""
    seen = {}
    for article in articles:
        base = _slugify(article.get('title'), url=article.get('url'))
        count = seen.get(base, 0) + 1
        seen[base] = count
        article['slug'] = base if count == 1 else f'{base}-{count}'


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


def _filtered_articles(db_path, limit):
    """Newest filtered articles from the pipeline's DuckDB store."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        rows = con.execute(
            """
            SELECT url, title, description, source, published_at
            FROM articles
            ORDER BY published_at DESC, source ASC
            LIMIT ?
            """,
            [limit],
        ).fetchall()
        columns = [col[0] for col in con.description]
    finally:
        con.close()
    return [dict(zip(columns, row, strict=False)) for row in rows]


def render_index(db_path='filtered_articles.duckdb', index_path='app/index.html', limit=30):
    """Inject the filtered articles into the static index page, in place.

    Replaces the block between the ARTICLES:BEGIN/END markers in index_path with a
    JSON payload (consumed by Alpine to rotate posters) and a noscript link list.
    If the filtered store is missing, the page is left untouched so the site keeps
    serving the previous run's output (same failure posture as main.py's sentiment
    fallback). Returns the number of articles injected.
    """
    index_file = Path(index_path)
    if not Path(db_path).exists():
        return 0

    articles = _filtered_articles(db_path, limit)
    _assign_unique_slugs(articles)

    # `</` escaped so untrusted titles cannot close the script tag from inside the JSON.
    payload = json.dumps(articles, ensure_ascii=False).replace('</', '<\\/')
    links = '\n'.join(
        f'      <li><a href="{escape(a["url"])}">{escape(a["title"] or a["url"])}</a> &mdash; {escape(a["source"] or "")}</li>'
        for a in articles
    )
    block = (
        f'{INDEX_MARKER_BEGIN}\n'
        f'    <script type="application/json" id="poster-articles">{payload}</script>\n'
        f'    <noscript><ul id="poster-fallback">\n{links}\n    </ul></noscript>\n'
        f'    {INDEX_MARKER_END}'
    )
    html = index_file.read_text()
    html = re.sub(
        re.escape(INDEX_MARKER_BEGIN) + r'.*?' + re.escape(INDEX_MARKER_END),
        lambda _: block,
        html,
        count=1,
        flags=re.DOTALL,
    )
    index_file.write_text(html)
    return len(articles)


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

    count = render_index()
    print(f'Injected {count} articles into app/index.html')
    render_archive(ARCHIVE_DIR)
