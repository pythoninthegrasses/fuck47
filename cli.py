#!/usr/bin/env python

"""
CLI for the article store: CRUD, feed fetching, and LLM sentiment judging.

Examples:
    uv run ./cli.py --add https://www.axios.com/2023/03/27/labor-board-says-non-disparagement-clauses-are-unlawful
    uv run ./cli.py -a URL1 URL2 --file urls.csv
    uv run ./cli.py --remove "labor board non-disparagement"
    uv run ./cli.py -r https://fuckfortyseven.org/#labor-board-says-non-disparagement-clauses-are-unlawful
    uv run ./cli.py --articles --hours 8 --djt-only
    uv run ./cli.py --fetch --hours 8
    uv run ./cli.py --judge --target local --hours 8
    uv run ./cli.py --compare --hours 8
"""

import argparse
import csv
import requests
import sys
import time
from config import (
    ARCHIVE_DIR,
    CACHE_HOURS,
    DJT_FILTER_MIN_SCORE,
    EXCLUDE_URLS_CSV,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LOCAL_LLM_API_KEY,
    LOCAL_LLM_BASE_URL,
    LOCAL_LLM_MODEL,
    RATE_LIMIT_INTERVAL_SEC,
    RATE_LIMIT_REQUESTS,
    SENTIMENT_MAX_SCORE,
)
from datetime import datetime, timedelta
from eliot import log_message, start_action, to_file
from pathlib import Path
from urllib.parse import urlparse
from utils.db import create_article_db
from utils.filter import DJTNewsFilter
from utils.newsapi import fetch_and_store_articles
from utils.ratelimit import RateLimiter
from utils.render import _slugify, render_index
from utils.rss import fetch_rss_articles
from utils.scrape import ScrapeError, extract_metadata, fetch_html
from utils.sentiment import SentimentJudgeError, score_articles

# Hostname of the live site — used to tell site-anchor URLs apart from source URLs.
_SITE_HOST = 'fuckfortyseven.org'

# Named judge targets. 'local' points at an oMLX (or other local OpenAI-compatible) server;
# temperature=0 asks for deterministic scoring since local runs are meant to be reproducible.
# 'remote' reuses the configured production judge (Fireworks by default) unchanged.
TARGETS = {
    'local': {
        'base_url': LOCAL_LLM_BASE_URL,
        'model': LOCAL_LLM_MODEL,
        'api_key': LOCAL_LLM_API_KEY,
        'temperature': 0,
    },
    'remote': {
        'base_url': LLM_BASE_URL,
        'model': LLM_MODEL,
        'api_key': LLM_API_KEY,
    },
}

# Small canned batch for `health` - one clearly negative, one clearly favorable article,
# mirroring the sample used in tests/test_sentiment.py.
_SMOKE_ARTICLES = [
    {
        'title': 'Trump Pulled In About $1.4 Billion From Crypto Ventures',
        'description': 'Financial disclosure shows the president profiting heavily while in office.',
    },
    {
        'title': 'Trump Signs Bipartisan Bill to Widespread Praise',
        'description': 'Lawmakers from both parties celebrate a rare moment of unity.',
    },
]


def _target_config(name):
    """Resolve a target name to its score_articles() kwargs, or exit with a clear error."""
    try:
        return TARGETS[name]
    except KeyError:
        raise SystemExit(f"Unknown target {name!r}; choose from {sorted(TARGETS)}") from None


def _recent_articles(db, hours):
    """Return articles with published_at within the last `hours` (string-cutoff, matching ArticleDB.clear_old_articles)."""
    cutoff = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M')
    return [a for a in db.get_all_articles() if a.get('published_at') and a['published_at'] >= cutoff]


def _load_djt_articles(db_path, hours, limit=None):
    """Load DJT-related articles from the last `hours`, same filter main.py applies before judging."""
    with create_article_db(db_path) as db:
        articles = _recent_articles(db, hours)
    djt_articles = DJTNewsFilter(min_score=DJT_FILTER_MIN_SCORE).filter_articles(articles)
    return djt_articles[:limit] if limit else djt_articles


def cmd_health(args):
    """Smoke-test a judge target: confirm the server is reachable and the model returns parseable scores."""
    cfg = _target_config(args.target)
    if args.model:
        cfg = {**cfg, 'model': args.model}
    print(f"target={args.target} base_url={cfg['base_url']} model={cfg['model']}")

    if args.target == 'local':
        status_url = f"{cfg['base_url']}/models/status"
        try:
            resp = requests.get(status_url, headers={'Authorization': f"Bearer {cfg['api_key']}"}, timeout=10)
            resp.raise_for_status()
            loaded = [m['id'] for m in resp.json().get('models', []) if m.get('loaded')]
            print(f"loaded models: {loaded or '(none)'}")
            if cfg['model'] not in loaded:
                print(f"WARNING: {cfg['model']!r} is not in the loaded-models list")
        except requests.RequestException as e:
            print(f"WARNING: could not reach {status_url}: {e}")

    start = time.monotonic()
    try:
        scores = score_articles(_SMOKE_ARTICLES, **cfg)
    except SentimentJudgeError as e:
        print(f"FAILED after {time.monotonic() - start:.1f}s: {e}")
        return 1

    print(f"OK: parsed scores {scores} in {time.monotonic() - start:.1f}s")
    return 0


def cmd_fetch(args):
    """Populate the article store: prune stale rows, fetch NewsAPI + RSS (mirrors main.py, no sentiment gate)."""
    with create_article_db(args.db or 'articles.duckdb') as db:
        db.clear_old_articles(hours=args.hours)
        print(f"Fetched and stored {len(fetch_and_store_articles(db))} articles from NewsAPI")
        print(f"Stored {db.insert_articles(fetch_rss_articles())} new articles from RSS feeds")
        db.sort_and_reindex_articles()
    return 0


def cmd_articles(args):
    """List articles from the store, optionally restricted to DJT-related ones."""
    with create_article_db(args.db or 'articles.duckdb') as db:
        articles = _recent_articles(db, args.hours)
    if args.djt_only:
        articles = DJTNewsFilter(min_score=DJT_FILTER_MIN_SCORE).filter_articles(articles)
    if args.limit:
        articles = articles[: args.limit]
    suffix = " (DJT-only)" if args.djt_only else ""
    print(f"{len(articles)} article(s) in the last {args.hours}h{suffix}")
    for a in articles:
        score = a.get('djt_relevance_score')
        print(f"{a['published_at']}  {f'{score:.1f}' if score is not None else '-':>5}  {a['source']:<20}  {a['title']}")
    return 0


def cmd_judge(args):
    """Score current DJT-related articles against one target and show the keep/drop gate outcome."""
    if not args.target:
        raise SystemExit("--judge requires --target; choose from " + str(sorted(TARGETS)))
    articles = _load_djt_articles(args.db or 'articles.duckdb', args.hours, args.limit)
    if not articles:
        print("No DJT-related articles in range; nothing to judge")
        return 0

    cfg = _target_config(args.target)
    if args.model:
        cfg = {**cfg, 'model': args.model}
    try:
        scores = score_articles(articles, timeout=args.timeout, **cfg)
    except SentimentJudgeError as e:
        print(f"Judge call failed: {e}")
        return 1

    for i, a in enumerate(articles):
        score = scores[i]
        keep = "keep" if score <= SENTIMENT_MAX_SCORE else "drop"
        print(f"{i:>3}  {score:+.2f}  {keep:<4}  {a['title']}")
    return 0


def cmd_compare(args):
    """Score the same DJT-related articles against both targets and report deltas/agreement."""
    articles = _load_djt_articles(args.db or 'articles.duckdb', args.hours, args.limit)
    if not articles:
        print("No DJT-related articles in range; nothing to compare")
        return 0

    results = {}
    for name in ('local', 'remote'):
        cfg = _target_config(name)
        try:
            results[name] = score_articles(articles, timeout=args.timeout, **cfg)
        except SentimentJudgeError as e:
            print(f"{name} judge call failed: {e}")
            results[name] = None

    if results['local'] is None or results['remote'] is None:
        return 1

    deltas = []
    disagreements = 0
    print(f"{'#':>3}  {'local':>7}  {'remote':>7}  {'delta':>6}  {'agree':<5}  title")
    for i, a in enumerate(articles):
        local_score, remote_score = results['local'][i], results['remote'][i]
        delta = local_score - remote_score
        deltas.append(abs(delta))

        agree = (local_score <= SENTIMENT_MAX_SCORE) == (remote_score <= SENTIMENT_MAX_SCORE)
        if not agree:
            disagreements += 1

        print(f"{i:>3}  {local_score:+7.2f}  {remote_score:+7.2f}  {delta:+6.2f}  {'yes' if agree else 'NO':<5}  {a['title']}")

    mean_abs_delta = sum(deltas) / len(deltas)
    print(f"\n{len(articles)} article(s); mean |delta|={mean_abs_delta:.3f}; keep/drop disagreements={disagreements}")
    return 0


def _resolve_field(field, cli_value, extracted_value, interactive=True):
    """Return the CLI flag value if given, else the extracted value, else prompt (or None if not interactive)."""
    if cli_value is not None:
        return cli_value
    if extracted_value is not None:
        return extracted_value
    if not interactive or not sys.stdin.isatty():
        return None
    return input(f"{field} not found; enter it now: ").strip() or None


def ingest_url(db, url, *, proxy=None, title=None, description=None, date=None, source=None, interactive=True):
    """Fetch a URL, extract metadata, and insert it into `db`.

    Returns (status, detail) where status is one of 'inserted', 'duplicate', 'fetch_failed',
    or 'missing_fields'. `interactive` controls whether gaps in extraction are prompted for
    (single add-article) or silently left missing (batch import, e.g. import-upnote).
    """
    try:
        html = fetch_html(url, proxy=proxy)
    except ScrapeError as e:
        return 'fetch_failed', str(e)

    extracted = extract_metadata(html, url=url)

    fields = {
        'title': _resolve_field('title', title, extracted['title'], interactive=interactive),
        'description': _resolve_field('description', description, extracted['description'], interactive=interactive),
        'published_at': _resolve_field('published_at', date, extracted['published_at'], interactive=interactive),
    }

    missing = [name for name, value in fields.items() if value is None]
    if missing:
        return 'missing_fields', ', '.join(missing)

    inserted = db.insert_article({'url': url, 'source': source or urlparse(url).hostname, **fields})

    if inserted:
        return 'inserted', fields['title']
    return 'duplicate', None


_eliot_log_configured = False


def _configure_eliot_logging(log_path):
    """Route eliot's structured logs to `log_path` (once per process, so repeated calls -
    e.g. across tests in the same process - don't stack up duplicate destinations)."""
    global _eliot_log_configured
    if not _eliot_log_configured:
        to_file(open(log_path, 'a'))
        _eliot_log_configured = True


def cmd_import_upnote(args):
    """Backfill news articles from local UpNote notes tagged #fuck45 or mentioning 'trump' into a staging DB."""
    import sqlite3
    import tempfile
    from utils.upnote import DEFAULT_DB_PATH, copy_db_readonly, extract_url, hint_link, is_excluded_source, iter_matching_notes

    _configure_eliot_logging(args.log or 'import_upnote.log')

    db_path = args.db or 'backfill.duckdb'
    with start_action(action_type="import_upnote", db=db_path, dry_run=args.dry_run) as action:
        src_db = args.upnote_db or DEFAULT_DB_PATH
        with tempfile.TemporaryDirectory() as tmp:
            copied = copy_db_readonly(src_db, tmp)
            con = sqlite3.connect(copied)
            try:
                notes = list(iter_matching_notes(con))
            finally:
                con.close()

        candidates = []
        seen_urls = set()
        unresolved_count = 0  # no confidently-extracted URL; needs manual add-article
        excluded_count = 0  # resolved URL, but from a non-article platform (video, Q&A)
        for note in notes:
            url = extract_url(note)
            if not url:
                unresolved_count += 1
                log_message(message_type="import_upnote_unresolved", note_title=note.get('title'), hint_link=hint_link(note))
                continue
            if is_excluded_source(url):
                excluded_count += 1
                log_message(message_type="import_upnote_excluded", url=url, note_title=note.get('title'))
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            candidates.append((url, note.get('title')))

        if args.limit:
            candidates = candidates[: args.limit]

        if args.dry_run:
            for url, title in candidates:
                print(f"{url}  ({title})")
            print(
                f"{len(candidates)} high-confidence candidate URL(s), "
                f"{unresolved_count} note(s) need manual review, {excluded_count} excluded (video/Q&A)"
            )
            return 0

        limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_INTERVAL_SEC)
        counts = {
            'inserted': 0,
            'duplicate': 0,
            'fetch_failed': 0,
            'missing_fields': 0,
            'unresolved': unresolved_count,
            'excluded': excluded_count,
        }

        with create_article_db(db_path) as db:
            for url, _title in candidates:
                limiter.acquire()
                status, detail = ingest_url(db, url, proxy=args.proxy, interactive=False)
                counts[status] += 1
                log_message(message_type="import_upnote_result", status=status, url=url, detail=detail)
                print(f"{status:<14} {url}")

        print(
            f"\n{len(candidates)} URL(s) processed: "
            f"inserted={counts['inserted']} duplicate={counts['duplicate']} "
            f"fetch_failed={counts['fetch_failed']} missing_fields={counts['missing_fields']} "
            f"unresolved={counts['unresolved']} excluded={counts['excluded']}"
        )
        action.add_success_fields(counts=counts)

    return 0


def _git_commit_and_push(paths, message):
    """Commit and push `paths` if any have changes; no-op if the working tree is already clean.

    `paths` is a list of file paths to stage and commit together.
    """
    import subprocess

    paths = [paths] if isinstance(paths, str) else list(paths)
    status = subprocess.run(['git', 'status', '--porcelain', '--'] + paths, capture_output=True, text=True, check=True)
    if not status.stdout.strip():
        print("No changes to commit; skipping commit/push")
        return

    for p in paths:
        subprocess.run(['git', 'add', p], check=True)
    subprocess.run(['git', 'commit', '-m', message], check=True)
    subprocess.run(['git', 'push'], check=True)
    print(f"Committed and pushed {', '.join(paths)}")


def cmd_merge_reviewed(args):
    """Merge manually-reviewed staged articles directly into the live stores.

    Bypasses the automated DJT filter and sentiment gate (main.py's pipeline) since these
    articles have already been reviewed by a human - see backlog task-014's UpNote backfill.
    Writes into both articles.duckdb (the permanent raw record) and filtered_articles.duckdb
    (the store render_index() actually reads), then re-renders app/index.html and - unless
    --no-push is given - commits and pushes it, triggering the GitHub Pages deploy.
    """
    _configure_eliot_logging(args.log or 'merge_reviewed.log')

    with start_action(action_type="merge_reviewed", staging_db=args.staging_db) as action:
        with create_article_db(args.staging_db) as staging_db:
            reviewed = staging_db.get_all_articles()

        if not reviewed:
            print("No articles in staging DB; nothing to merge")
            return 0

        run_at = datetime.now()
        urls = [a['url'] for a in reviewed]
        inserted = []
        for db_path in (args.articles_db, args.filtered_db):
            with create_article_db(db_path) as db:
                inserted.append(db.insert_articles(reviewed))
                for url in urls:
                    db.mark_manual_review(url)
                db.sort_and_reindex_articles()
                db.archive_snapshot(ARCHIVE_DIR, run_at)
        articles_inserted, filtered_inserted = inserted

        injected = render_index(db_path=args.filtered_db, index_path=args.index_path)
        print(
            f"Merged {len(reviewed)} reviewed article(s): "
            f"{articles_inserted} new in {args.articles_db}, {filtered_inserted} new in {args.filtered_db}"
        )
        print(f"Injected {injected} articles into {args.index_path}")
        action.add_success_fields(articles_inserted=articles_inserted, filtered_inserted=filtered_inserted, injected=injected)

        if args.push:
            _git_commit_and_push([args.index_path], 'chore(content): merge manually-reviewed backfill articles')

    return 0


def _read_exclude_csv(path):
    """Return all rows from the exclusion CSV as a list of dicts; empty list if absent."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def _write_exclude_csv(path, rows):
    path = Path(path)
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'reason', 'excluded_at'])
        writer.writeheader()
        writer.writerows(rows)


def _add_to_exclude_csv(path, urls, reason=None):
    """Append URLs not already in the CSV; returns count added."""
    rows = _read_exclude_csv(path)
    existing = {r['url'] for r in rows}
    now = datetime.now().strftime('%Y-%m-%dT%H:%M')
    added = 0
    for url in urls:
        url_lower = url.lower()
        if url_lower not in existing:
            rows.append({'url': url_lower, 'reason': reason or '', 'excluded_at': now})
            existing.add(url_lower)
            added += 1
    _write_exclude_csv(path, rows)
    return added


def _remove_from_exclude_csv(path, urls):
    """Remove URLs from the CSV; returns count removed."""
    rows = _read_exclude_csv(path)
    urls_lower = {u.lower() for u in urls}
    before = len(rows)
    rows = [r for r in rows if r['url'] not in urls_lower]
    _write_exclude_csv(path, rows)
    return before - len(rows)


def _read_url_file(path):
    """Read URLs from a CSV file or stdin ('-'); expects a 'url' column."""
    import io

    content = sys.stdin.read() if path == '-' else Path(path).read_text()
    return [row['url'] for row in csv.DictReader(io.StringIO(content)) if row.get('url', '').strip()]


def _resolve_to_source_urls(values, articles):
    """Resolve VALUES to matching article dicts and pre-emptive source URLs.

    Each VALUE can be:
    - An external source URL  → exact match; pre-emptive block if not in the DB.
    - A site anchor URL       → fragment matched against each article's slugified title.
    - A bare substring        → case-insensitive search over url/title/source.

    Returns:
        matched    - dict mapping source URL → article dict
        preemptive - set of external URLs to block not currently in the DB
    """
    matched = {}
    preemptive = set()

    for value in values:
        parsed = urlparse(value)
        is_url = parsed.scheme in ('http', 'https')

        if is_url and parsed.hostname != _SITE_HOST:
            url_lower = value.lower().split('#')[0].rstrip('/')
            found = [a for a in articles if a['url'] == url_lower]
            if found:
                for a in found:
                    matched[a['url']] = a
            else:
                preemptive.add(url_lower)

        elif is_url and parsed.hostname == _SITE_HOST:
            fragment = parsed.fragment
            if not fragment:
                print(f"WARNING: site URL has no anchor, skipping: {value}")
                continue
            for a in articles:
                base_slug = _slugify(a.get('title', ''), url=a.get('url'))
                if fragment == base_slug or fragment.startswith(base_slug + '-'):
                    matched[a['url']] = a

        else:
            val_lower = value.lower()
            found_any = False
            for a in articles:
                if (
                    val_lower in (a.get('url') or '').lower()
                    or val_lower in (a.get('title') or '').lower()
                    or val_lower in (a.get('source') or '').lower()
                ):
                    matched[a['url']] = a
                    found_any = True
            if not found_any:
                print(f"WARNING: no articles matched: {value!r}")

    return matched, preemptive


def cmd_add(args):
    """Batch-insert articles by URL; un-excludes any URL that was previously blocked."""
    urls = list(args.add or [])
    if args.file:
        urls += _read_url_file(args.file)
    if not urls:
        print("No URLs provided")
        return 1

    limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_INTERVAL_SEC) if len(urls) > 1 else None
    counts = {'inserted': 0, 'duplicate': 0, 'fetch_failed': 0, 'missing_fields': 0}
    inserted_articles = []

    with create_article_db(args.articles_db, exclude_csv=args.exclude_csv) as db:
        for url in urls:
            if limiter:
                limiter.acquire()
            _remove_from_exclude_csv(args.exclude_csv, [url])
            db.remove_exclusion(url)
            status, detail = ingest_url(db, url, proxy=args.proxy, interactive=False)
            counts[status] = counts.get(status, 0) + 1
            suffix = f"  ({detail})" if status in {'fetch_failed', 'missing_fields'} else ""
            print(f"{status:<14} {url}{suffix}")
            if status in ('inserted', 'duplicate'):
                results = db.search_by_url(url)
                if results:
                    inserted_articles.append(results[0])

    if len(urls) > 1:
        print(
            f"\n{len(urls)} URL(s) processed: inserted={counts['inserted']} "
            f"duplicate={counts['duplicate']} fetch_failed={counts['fetch_failed']} "
            f"missing_fields={counts['missing_fields']}"
        )

    if not inserted_articles:
        return 0

    with create_article_db(args.filtered_db, exclude_csv=args.exclude_csv) as db:
        db.insert_articles(inserted_articles)
        for article in inserted_articles:
            db.mark_manual_review(article['url'])

    injected = render_index(db_path=args.filtered_db, index_path=args.index_path)
    print(f"Injected {injected} articles into {args.index_path}")

    if args.push:
        _git_commit_and_push([args.index_path], f"chore(content): manually add {len(inserted_articles)} article(s)")

    return 0


def cmd_remove(args):
    """Remove articles from both stores, block them in the exclusion CSV, and re-render."""
    values = list(args.remove or [])
    if args.file:
        values += _read_url_file(args.file)
    if not values:
        print("No values provided")
        return 1

    with create_article_db(args.articles_db, exclude_csv=args.exclude_csv) as db:
        articles = db.get_all_articles()

    matched, preemptive = _resolve_to_source_urls(values, articles)

    if not matched and not preemptive:
        print("Nothing to remove")
        return 0

    preview_items = list(matched.values()) + [
        {'url': u, 'title': '(pre-emptive block — not currently in DB)', 'source': ''} for u in preemptive
    ]
    print(f"{'#':>3}  {'title':<52}  url")
    for i, item in enumerate(preview_items):
        print(f"{i:>3}  {(item.get('title') or '')[:52]:<52}  {item['url']}")
    print(f"\n{len(preview_items)} article(s) will be excluded and removed.")

    if not args.force:
        if not sys.stdin.isatty():
            print("stdin is not interactive; use --force to skip confirmation")
            return 1
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer != 'y':
            print("Aborted")
            return 0

    all_urls = set(matched.keys()) | preemptive
    added_to_csv = _add_to_exclude_csv(args.exclude_csv, all_urls, reason=args.reason)

    run_at = datetime.now()
    for db_path in (args.articles_db, args.filtered_db):
        with create_article_db(db_path, exclude_csv=args.exclude_csv) as db:
            for url in all_urls:
                db.remove_by_url(url)
            db.archive_snapshot(ARCHIVE_DIR, run_at)

    injected = render_index(db_path=args.filtered_db, index_path=args.index_path)
    print(
        f"Removed {len(all_urls)} article(s); "
        f"added {added_to_csv} URL(s) to {args.exclude_csv}; "
        f"injected {injected} into {args.index_path}"
    )

    if args.push:
        n = len(all_urls)
        _git_commit_and_push(
            [args.exclude_csv, args.index_path],
            f"chore(content): exclude {n} article(s)",
        )

    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog='cli.py', description=__doc__.strip().splitlines()[0])

    cmd = parser.add_mutually_exclusive_group(required=True)
    cmd.add_argument('--health', action='store_true', help="smoke-test a judge target")
    cmd.add_argument('-f', '--fetch', action='store_true', help="fetch NewsAPI + RSS articles into the store")
    cmd.add_argument('-A', '--articles', action='store_true', help="list articles currently in the store")
    cmd.add_argument('-j', '--judge', action='store_true', help="score current DJT articles against one target")
    cmd.add_argument('-c', '--compare', action='store_true', help="score current DJT articles against both targets side by side")
    cmd.add_argument(
        '-a', '--add', nargs='*', metavar='URL', help="batch-add articles by URL; un-excludes previously blocked URLs"
    )
    cmd.add_argument(
        '-r',
        '--remove',
        nargs='*',
        metavar='VALUE',
        help="remove articles by URL, site anchor, or substring; adds to exclude_urls.csv",
    )
    cmd.add_argument(
        '-i',
        '--import-upnote',
        action='store_true',
        dest='import_upnote',
        help="backfill news articles from UpNote notes tagged #fuck45 or mentioning 'trump'",
    )
    cmd.add_argument(
        '-m',
        '--merge-reviewed',
        action='store_true',
        dest='merge_reviewed',
        help="merge manually-reviewed staged articles into the live stores, bypassing the DJT filter and sentiment gate",
    )

    parser.add_argument('--hours', type=int, default=CACHE_HOURS)
    parser.add_argument('--target', choices=sorted(TARGETS))
    parser.add_argument('--model', help="override the resolved target's model")
    parser.add_argument('--limit', type=int)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--djt-only', action='store_true')
    parser.add_argument('--db', default=None)
    parser.add_argument('--articles-db', default='articles.duckdb')
    parser.add_argument('--filtered-db', default='filtered_articles.duckdb')
    parser.add_argument('--staging-db', default='backfill.duckdb')
    parser.add_argument('--index-path', default='app/index.html')
    parser.add_argument('--upnote-db', help="path to UpNote's sqlite3 file (default: the standard macOS container path)")
    parser.add_argument('--proxy')
    parser.add_argument('--file', metavar='PATH', help="read URLs/values from a CSV file (- for stdin)")
    parser.add_argument('--exclude-csv', default=EXCLUDE_URLS_CSV)
    parser.add_argument('--reason', help="reason string recorded in exclude_urls.csv")
    parser.add_argument('--force', action='store_true', help="skip removal confirmation prompt")
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--log', default=None)
    parser.add_argument('--no-push', dest='push', action='store_false', help="skip git commit/push")
    parser.set_defaults(push=True)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    fn = next(
        fn
        for active, fn in [
            (args.health, cmd_health),
            (args.fetch, cmd_fetch),
            (args.articles, cmd_articles),
            (args.judge, cmd_judge),
            (args.compare, cmd_compare),
            (args.add is not None, cmd_add),
            (args.remove is not None, cmd_remove),
            (args.import_upnote, cmd_import_upnote),
            (args.merge_reviewed, cmd_merge_reviewed),
        ]
        if active
    )
    return fn(args) or 0


if __name__ == '__main__':
    raise SystemExit(main())
