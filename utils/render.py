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


_ARCHIVE_FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
    "%3Crect width='16' height='16' fill='%23221f1a'/%3E"
    "%3Ctext x='8' y='12.5' text-anchor='middle' font-family='Arial Narrow, sans-serif' "
    "font-weight='bold' font-size='11' fill='%23f4efe3'%3E47%3C/text%3E%3C/svg%3E"
)

_ARCHIVE_STYLE = """\
  <style>
  @font-face {
    font-family: 'Anton';
    src: url('../fonts/anton.woff2') format('woff2');
    font-weight: 400;
    font-display: swap;
  }
  @font-face {
    font-family: 'Special Elite';
    src: url('../fonts/special-elite.woff2') format('woff2');
    font-weight: 400;
    font-display: swap;
  }

  :root {
    --ink: #221f1a;
    --ground: #dfe2dd;
    --stock: #f1e6c9;
    --tan: #e8b98a;
    --olive: #48566d;
    --masthead: 'Anton', 'Arial Narrow', Impact, sans-serif;
    --typewriter: 'Special Elite', 'Courier New', monospace;

    /* Width cascade: date text → date separators (+5%) → both rules (+10%) */
    --date-text-w: 11.2ch;
    --sep-w: calc(var(--date-text-w) * 1.05);
    --rule-w: calc(var(--sep-w) * 1.10);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--ground);
    color: var(--ink);
    font-family: var(--typewriter);
    font-size: 1rem;
    line-height: 1.6;
    padding: clamp(1.5rem, 4vw, 3rem);
  }

  .masthead {
    font-family: var(--masthead);
    font-size: clamp(2rem, 6vw, 3.5rem);
    letter-spacing: -0.02em;
    line-height: 1;
    text-transform: uppercase;
    margin-bottom: 0.25em;
  }

  .masthead a { color: var(--ink); text-decoration: none; }
  .masthead a:hover { color: var(--olive); }

  .subtitle {
    font-family: var(--typewriter);
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--olive);
    margin-bottom: 2rem;
  }

  /* Rule 1: narrow line under subtitle, same width as Rule 2.
     font-size: 1rem ensures ch resolves at body scale, not subtitle's 0.8rem. */
  .subtitle::after {
    content: '';
    display: block;
    font-size: 1rem;
    width: var(--rule-w);
    height: 2px;
    background: var(--ink);
    margin-top: 0.75rem;
  }

  .layout { display: block; }

  .date-list {
    list-style: none;
    width: var(--sep-w);
  }

  .date-list li { border-bottom: 1px solid var(--tan); }

  .date-list a {
    display: block;
    padding: 0.4em 0;
    color: var(--ink);
    text-decoration: none;
    white-space: nowrap;
  }

  .date-list a::before { content: '› '; color: var(--olive); }
  .date-list a:hover { color: var(--olive); }

  /* Rule 2: narrow line below date nav, same width as Rule 1 */
  .date-nav::after {
    content: '';
    display: block;
    width: var(--rule-w);
    height: 2px;
    background: var(--ink);
    margin-top: 1rem;
  }

  #archive-content { margin-top: 2rem; }

  #archive-content h2 {
    font-family: var(--masthead);
    font-size: 1.4rem;
    margin-bottom: 0.75rem;
  }

  #archive-content ul { list-style: none; }

  #archive-content li {
    padding: 0.35em 0;
    border-bottom: 1px solid var(--tan);
    break-inside: avoid;
  }

  #archive-content a { color: var(--olive); }
  #archive-content a:hover { color: var(--ink); }

  /* Desktop: sidebar + content columns */
  @media (min-width: 768px) {
    .layout {
      display: grid;
      grid-template-columns: auto 1fr;
      column-gap: 3rem;
      align-items: start;
    }

    #archive-content {
      margin-top: 0;
      padding-left: 2rem;
      border-left: 2px solid var(--ink);
    }
  }

  /* 2 article columns at half QHD width */
  @media (min-width: 1280px) {
    #archive-content ul {
      column-count: 2;
      column-gap: 2rem;
      column-rule: 1px solid var(--tan);
    }
  }

  /* 3 article columns at QHD */
  @media (min-width: 2560px) {
    #archive-content ul {
      column-count: 3;
    }
  }
  </style>"""


def _render_index(dates):
    if not dates:
        nav_content = '      <p>No archived runs yet.</p>'
    else:
        items = '\n'.join(
            f'      <li><a href="{escape(d)}.html" hx-get="{escape(d)}.html" '
            f'hx-target="#archive-content" hx-swap="innerHTML">{escape(d)}</a></li>'
            for d in dates
        )
        nav_content = f'      <ul class="date-list">\n{items}\n      </ul>'
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '  <title>Fuck Forty Seven \u2014 Archive</title>\n'
        f'  <link rel="icon" href="{_ARCHIVE_FAVICON}">\n'
        '  <link rel="preload" href="../fonts/anton.woff2" as="font" type="font/woff2" crossorigin>\n'
        '  <link rel="preload" href="../fonts/special-elite.woff2" as="font" type="font/woff2" crossorigin>\n'
        f'{_ARCHIVE_STYLE}\n'
        '  <script src="https://unpkg.com/htmx.org@2"></script>\n'
        '</head>\n'
        '<body>\n'
        '  <h1 class="masthead"><a href="../index.html">Fuck 47</a></h1>\n'
        '  <p class="subtitle">Archive</p>\n'
        '  <div class="layout">\n'
        '    <nav class="date-nav">\n'
        f'{nav_content}\n'
        '    </nav>\n'
        '    <main id="archive-content"></main>\n'
        '  </div>\n'
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
    If the filtered store is missing or empty, the page is left untouched so the
    site keeps serving the previous run's output (same failure posture as main.py's
    sentiment fallback). Returns the number of articles injected.
    """
    index_file = Path(index_path)
    if not Path(db_path).exists():
        return 0

    articles = _filtered_articles(db_path, limit)
    if not articles:
        return 0
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
