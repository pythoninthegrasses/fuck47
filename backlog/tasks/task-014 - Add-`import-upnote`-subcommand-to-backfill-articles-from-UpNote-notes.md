---
id: TASK-014
title: Add `import-upnote` subcommand to backfill articles from UpNote notes
status: Done
assignee: []
created_date: '2026-07-04 02:01'
updated_date: '2026-07-04 02:14'
labels:
  - cli
  - scraping
  - ingestion
  - upnote
dependencies: []
references:
  - cli.py
  - utils/db.py
  - utils/scrape.py
  - utils/ratelimit.py
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Read UpNote's local SQLite DB (read-only, copied to a temp dir), find notes tagged `#fuck45` or containing "trump", extract the source URL from each, and run them through the existing add-article fetch+extract pipeline (utils/scrape.py) into a staging DuckDB. User reviews staged rows before merging into the live articles.duckdb.

Key findings from investigation:
- UpNote's x-callback-url endpoints (openNote, note/new, tag/view, view?action=search, etc.) are write/navigate-only — none return note content to the caller, so the local SQLite DB is the only read path.
- DB location: ~/Library/Containers/com.getupnote.desktop/Data/Library/Application Support/UpNote/upnote.sqlite3
- notes table: id, html, text, title, createdAt (epoch ms), tagLinks (JSON slug array), trashed, deleted
- Filter: trashed=0 AND deleted=0 AND (tagLinks LIKE '%fuck45%' OR lower(title) LIKE '%trump%' OR lower(text) LIKE '%trump%') → 294 notes, ~265 with an http link
- note.text format: "<headline>\n#fuck45\n<article URL>\nBy <author>\n<body>"
- note.createdAt is UNRELIABLE as publish date (275/294 notes stamped 2022 — bulk-import artifact). Must use trafilatura's extracted date, not the note's createdAt.
- Scope is #fuck45 OR trump keyword ONLY — explicitly exclude #NeverTrumpers / #WeLoveTrumpers tags (user-confirmed).
- Stage-then-merge: import into a separate staging DuckDB (e.g. backfill.duckdb) first for review, merge into articles.duckdb afterward via the existing dedup-by-url path (ArticleDB.insert_article ON CONFLICT DO NOTHING).

See full plan at /Users/lance/.claude/plans/cuddly-wiggling-waffle.md for the detailed design.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 utils/upnote.py provides a read-only extractor: copies the sqlite3+wal+shm to a temp dir, queries the confirmed filter, and extracts the source URL per note from a standalone URL line near the top of `text` only (high-precision; see implementation notes)
- [x] #2 cli.py:cmd_add_article's per-URL core is refactored into a reusable ingest_url() helper returning a result status (inserted/duplicate/fetch_failed/missing_fields)
- [x] #3 New `uv run ./cli.py import-upnote --db <staging.duckdb>` subcommand iterates matching notes, dedups URLs, and calls ingest_url() for each via the RateLimiter
- [x] #4 --dry-run lists candidate URLs/titles (and the manual-review count) without fetching or inserting anything
- [x] #5 --limit N caps how many URLs are processed
- [x] #6 Per-URL failures (dead links, fetch errors) are logged and skipped; the batch continues rather than aborting, and failed URLs are written to --report for retry
- [x] #7 A final summary of inserted/duplicate/fetch_failed/unresolved counts is printed
- [x] #8 Notes tagged #NeverTrumpers or #WeLoveTrumpers (without #fuck45 or 'trump' keyword) are excluded
- [x] #9 Tests use a fixture SQLite DB and mock the network layer (fetch_html/extract_metadata) — no real network calls, no touching the real UpNote DB
- [x] #10 AGENTS.md documents the new command, utils/upnote.py, and the high-precision-only extraction tradeoff
- [x] #11 Notes with no confidently-extractable URL (full-text clips with no dedicated source line) are written to --review-report with a non-authoritative hint_link lead, never auto-inserted with a guessed URL
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented as planned (utils/upnote.py + cli.py import-upnote, staging DB, RateLimiter, dry-run/limit/report), with one material change discovered mid-implementation and confirmed with the user before shipping:

Original assumption (from the single NYT test URL used to validate the approach) was that notes reliably carry their source URL. Real data disproved this: of 294 matching notes, only 25 have a standalone source-URL line near the top of `text` (the web clipper's own link line). The other 269 are full-text clips (pasted article body, inline images, many in-body author-bio/footnote/reference links) with no canonical URL preserved anywhere in the schema (checked notes and files tables). Falling back to "first non-attachment href in html" — the original design — produced silently wrong results in manual testing: a Quartz author-bio page, an NYT columnist bio page, and a Flickr photo link were each picked as "the article" instead of the real source.

Given the choice between (a) high-precision-only with a manual-review report, (b) best-effort with a confidence flag, or (c) treating the note body itself as the article, the user chose (a). extract_url() therefore only trusts a standalone URL line in the first 6 lines of `text` and returns None otherwise; it never falls back to html hrefs. Unresolved notes (269 of 294) are written to --review-report (default upnote_import_unresolved.txt) with a non-authoritative hint_link (first non-attachment html href) as a manual lead, for one-by-one handling via the existing add-article command — not auto-inserted.

Live dry-run against the real UpNote store confirms: 25 high-confidence candidates, all real article URLs (no author pages, no attachment links, no reference-link false positives), 269 flagged for manual review.

Read-only guarantee verified in practice: copy_db_readonly copies the live .sqlite3 + -wal/-shm sidecars to a scratch dir before any query; the live UpNote container was never opened directly (confirmed via `ps`/file listing before touching anything, and explicit user authorization was obtained before any DB access since the harness's auto-mode classifier initially blocked it as a personal-data-store read).
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 ruff format --check --diff . passes with no changes needed
- [x] #2 ruff check passes with no errors
- [x] #3 pytest passes (all tests green)
- [x] #4 New feature/bugfix developed test-first: failing test written before implementation
- [x] #5 Relevant docs updated (README.md / AGENTS.md)
- [x] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
