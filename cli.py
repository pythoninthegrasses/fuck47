#!/usr/bin/env python

"""
CLI for exploring the article store and running the LLM sentiment judge against
local (oMLX) and remote (Fireworks) targets. See docs/ai.md.

Examples:
    uv run ./cli.py health --target local
    uv run ./cli.py fetch --hours 8
    uv run ./cli.py articles --hours 8 --djt-only
    uv run ./cli.py judge --target local --hours 8
    uv run ./cli.py compare --hours 8
"""

import argparse
import requests
import sys
import time
from config import (
    CACHE_HOURS,
    DJT_FILTER_MIN_SCORE,
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
from urllib.parse import urlparse
from utils.db import create_article_db
from utils.filter import DJTNewsFilter
from utils.newsapi import fetch_and_store_articles
from utils.ratelimit import RateLimiter
from utils.rss import fetch_rss_articles
from utils.scrape import ScrapeError, extract_metadata, fetch_html
from utils.sentiment import SentimentJudgeError, score_articles

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
    db = create_article_db(db_path)
    try:
        articles = _recent_articles(db, hours)
    finally:
        db.close()

    djt_articles = DJTNewsFilter(min_score=DJT_FILTER_MIN_SCORE).filter_articles(articles)
    if limit:
        djt_articles = djt_articles[:limit]
    return djt_articles


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
    db = create_article_db(args.db)
    try:
        db.clear_old_articles(hours=args.hours)

        articles = fetch_and_store_articles(db)
        print(f"Fetched and stored {len(articles)} articles from NewsAPI")

        rss_articles = fetch_rss_articles()
        stored = db.insert_articles(rss_articles)
        print(f"Stored {stored} new articles from RSS feeds")

        db.sort_and_reindex_articles()
    finally:
        db.close()
    return 0


def cmd_articles(args):
    """List articles from the store, optionally restricted to DJT-related ones."""
    db = create_article_db(args.db)
    try:
        articles = _recent_articles(db, args.hours)
    finally:
        db.close()

    if args.djt_only:
        articles = DJTNewsFilter(min_score=DJT_FILTER_MIN_SCORE).filter_articles(articles)
    if args.limit:
        articles = articles[: args.limit]

    suffix = " (DJT-only)" if args.djt_only else ""
    print(f"{len(articles)} article(s) in the last {args.hours}h{suffix}")
    for a in articles:
        score = a.get('djt_relevance_score')
        score_str = f"{score:.1f}" if score is not None else "-"
        print(f"{a['published_at']}  {score_str:>5}  {a['source']:<20}  {a['title']}")
    return 0


def cmd_judge(args):
    """Score current DJT-related articles against one target and show the keep/drop gate outcome."""
    articles = _load_djt_articles(args.db, args.hours, args.limit)
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
    articles = _load_djt_articles(args.db, args.hours, args.limit)
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

    resolved_source = source or urlparse(url).hostname
    inserted = db.insert_article(
        {
            'url': url,
            'title': fields['title'],
            'description': fields['description'],
            'published_at': fields['published_at'],
            'source': resolved_source,
        }
    )

    if inserted:
        return 'inserted', fields['title']
    return 'duplicate', None


def cmd_add_article(args):
    """Manually ingest a single article by URL: fetch, extract metadata, prompt for gaps, insert."""
    db = create_article_db(args.db)
    try:
        status, detail = ingest_url(
            db, args.url, proxy=args.proxy, title=args.title, description=args.description, date=args.date, source=args.source
        )
    finally:
        db.close()

    if status == 'fetch_failed':
        print(f"Fetch failed: {detail}")
        return 1
    if status == 'missing_fields':
        print(f"Missing required field(s), stdin is not interactive: {detail}")
        return 1
    if status == 'inserted':
        print(f"Inserted: {detail} ({args.url})")
        return 0
    print(f"Duplicate (already in store): {args.url}")
    return 0


def cmd_import_upnote(args):
    """Backfill articles from local UpNote notes tagged #fuck45 or mentioning 'trump' into a staging DB."""
    import sqlite3
    import tempfile
    from utils.upnote import DEFAULT_DB_PATH, copy_db_readonly, extract_url, hint_link, iter_matching_notes

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
    unresolved = []  # (title, hint_link_or_None) - no confidently-extracted URL; needs manual add-article
    for note in notes:
        url = extract_url(note)
        if not url:
            unresolved.append((note.get('title'), hint_link(note)))
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
        print(f"{len(candidates)} high-confidence candidate URL(s), {len(unresolved)} note(s) need manual review")
        return 0

    limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_INTERVAL_SEC)
    counts = {'inserted': 0, 'duplicate': 0, 'fetch_failed': 0, 'missing_fields': 0, 'unresolved': len(unresolved)}
    failed_urls = []

    db = create_article_db(args.db)
    try:
        for url, _title in candidates:
            limiter.acquire()
            status, detail = ingest_url(db, url, proxy=args.proxy, interactive=False)
            counts[status] += 1
            if status == 'fetch_failed':
                failed_urls.append(url)
            print(f"{status:<14} {url}")
    finally:
        db.close()

    print(
        f"\n{len(candidates)} URL(s) processed: "
        f"inserted={counts['inserted']} duplicate={counts['duplicate']} "
        f"fetch_failed={counts['fetch_failed']} missing_fields={counts['missing_fields']} "
        f"unresolved={counts['unresolved']}"
    )

    if failed_urls:
        report_path = args.report or 'upnote_import_failures.txt'
        with open(report_path, 'w') as f:
            f.write('\n'.join(failed_urls) + '\n')
        print(f"Wrote {len(failed_urls)} failed URL(s) to {report_path}")

    if unresolved:
        review_path = args.review_report or 'upnote_import_unresolved.txt'
        with open(review_path, 'w') as f:
            for title, hint in unresolved:
                f.write(f"{title}\t{hint or '(no link found)'}\n")
        print(f"Wrote {len(unresolved)} unresolved note(s) (no confident URL) to {review_path} for manual add-article")

    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog='cli.py', description=__doc__.strip().splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('health', help="smoke-test a judge target")
    p.add_argument('--target', choices=sorted(TARGETS), default='local')
    p.add_argument('--model', help="override the resolved target's model")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser('fetch', help="fetch NewsAPI + RSS articles into the store")
    p.add_argument('--hours', type=int, default=CACHE_HOURS)
    p.add_argument('--db', default='articles.duckdb')
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser('articles', help="list articles currently in the store")
    p.add_argument('--hours', type=int, default=CACHE_HOURS)
    p.add_argument('--djt-only', action='store_true')
    p.add_argument('--limit', type=int)
    p.add_argument('--db', default='articles.duckdb')
    p.set_defaults(func=cmd_articles)

    p = sub.add_parser('judge', help="score current DJT articles against one target")
    p.add_argument('--target', choices=sorted(TARGETS), required=True)
    p.add_argument('--model', help="override the resolved target's model")
    p.add_argument('--hours', type=int, default=CACHE_HOURS)
    p.add_argument('--limit', type=int)
    p.add_argument('--timeout', type=float, default=120)
    p.add_argument('--db', default='articles.duckdb')
    p.set_defaults(func=cmd_judge)

    p = sub.add_parser('compare', help="score current DJT articles against both targets side by side")
    p.add_argument('--hours', type=int, default=CACHE_HOURS)
    p.add_argument('--limit', type=int)
    p.add_argument('--timeout', type=float, default=120)
    p.add_argument('--db', default='articles.duckdb')
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser('add-article', help="manually ingest an article by URL")
    p.add_argument('url')
    p.add_argument('--proxy')
    p.add_argument('--db', default='articles.duckdb')
    p.add_argument('--title')
    p.add_argument('--description')
    p.add_argument('--date', dest='date')
    p.add_argument('--source')
    p.set_defaults(func=cmd_add_article)

    p = sub.add_parser('import-upnote', help="backfill articles from UpNote notes tagged #fuck45 or mentioning 'trump'")
    p.add_argument('--db', default='backfill.duckdb', help="staging DB to insert backfilled articles into")
    p.add_argument('--upnote-db', help="path to UpNote's sqlite3 file (default: the standard macOS container path)")
    p.add_argument('--proxy')
    p.add_argument('--limit', type=int)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--report', help="path to write failed URLs to (default: upnote_import_failures.txt)")
    p.add_argument(
        '--review-report', help="path to write unresolved notes (no confident URL) to (default: upnote_import_unresolved.txt)"
    )
    p.set_defaults(func=cmd_import_upnote)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args) or 0


if __name__ == '__main__':
    raise SystemExit(main())
