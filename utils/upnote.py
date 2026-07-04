#!/usr/bin/env python

"""Read-only extraction of Trump-related article URLs from a local UpNote SQLite store.

See backlog task-014. UpNote's x-callback-url endpoints are write/navigate-only (no data-return
callback), so the only way to programmatically read note content is UpNote's local SQLite DB.
This module never opens the live DB directly: callers must copy it (WAL included) first via
copy_db_readonly(), so a concurrently-running UpNote instance is never touched.
"""

import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_DB_PATH = Path(
    '~/Library/Containers/com.getupnote.desktop/Data/Library/Application Support/UpNote/upnote.sqlite3'
).expanduser()

# Matches the tag/keyword scope requested: notes tagged #fuck45, or mentioning "trump" anywhere
# in title/text. Deliberately excludes other Trump-adjacent tags (e.g. #NeverTrumpers,
# #WeLoveTrumpers) that don't carry "trump" in tagLinks/title/text under this filter.
MATCHING_NOTES_QUERY = """
    SELECT id, title, text, html, createdAt
    FROM notes
    WHERE trashed = 0 AND deleted = 0
      AND (tagLinks LIKE '%fuck45%' OR lower(title) LIKE '%trump%' OR lower(text) LIKE '%trump%')
"""

_URL_RE = re.compile(r'https?://\S+')
_HREF_RE = re.compile(r'href="(https?://[^"]+)"')
# Note attachments (images, PDFs) UpNote clips alongside the article are served from a local
# per-instance file server, not the article's own host - never treat these as the source URL.
_LOCAL_ATTACHMENT_HOST = 'localhost'
# UpNote's web clipper writes the source URL as its own line near the top of `text` (see the
# "<headline>\n#tag\n<url>\nBy <author>\n<body>" shape observed in real notes) - only lines that
# are *just* a URL count; in-body reference/footnote links and author-profile links do not.
_LINES_TO_SCAN = 6

# The backfill is meant to be news articles, not video/Q&A platforms clipped alongside them.
EXCLUDED_HOSTS = {'youtube.com', 'www.youtube.com', 'youtu.be', 'quora.com', 'www.quora.com'}


def is_excluded_source(url):
    """True if `url`'s host is a non-article platform (video, Q&A) excluded from the backfill."""
    return (urlparse(url).hostname or '').lower() in EXCLUDED_HOSTS


def copy_db_readonly(db_path, dest_dir):
    """Copy the sqlite3 file (plus -wal/-shm sidecars, if present) into dest_dir; return the copy's path."""
    db_path = Path(db_path)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / db_path.name
    shutil.copy2(db_path, dest_path)

    for suffix in ('-wal', '-shm'):
        sidecar = db_path.with_name(db_path.name + suffix)
        if sidecar.exists():
            shutil.copy2(sidecar, dest_dir / sidecar.name)

    return dest_path


def iter_matching_notes(con):
    """Yield dicts for notes tagged #fuck45 or mentioning 'trump', excluding trashed/deleted ones."""
    columns = ('id', 'title', 'text', 'html', 'created_at')
    for row in con.execute(MATCHING_NOTES_QUERY):
        yield dict(zip(columns, row, strict=False))


def extract_url(note):
    """Pull the source article URL from a note, high-precision only.

    Only trusts a standalone-URL line near the top of `text` (the web clipper's own
    source-link line, e.g. "<headline>\\n#tag\\n<url>\\nBy <author>\\n<body>"). Deliberately
    does NOT fall back to "any href in html": most matching notes are full article clips with
    many in-body reference/footnote/author-profile links, and grabbing the first non-attachment
    href produced wrong URLs (an author bio page, a Flickr photo, etc. instead of the article) -
    see backlog task-014 investigation notes. Notes without a standalone URL line return None
    and are logged for manual review rather than guessed at.
    """
    text = note.get('text') or ''
    for line in text.splitlines()[:_LINES_TO_SCAN]:
        stripped = line.strip().rstrip('.,)')
        if _URL_RE.fullmatch(stripped) and _LOCAL_ATTACHMENT_HOST not in stripped:
            return stripped

    return None


def hint_link(note):
    """Best-guess (non-authoritative) link for a note extract_url() couldn't resolve confidently.

    Returns the first non-attachment href in `html`, purely as a manual-review lead - it is
    frequently wrong (author bio pages, footnotes, etc; see extract_url()'s docstring), so
    callers must never insert it automatically.
    """
    for href in _HREF_RE.findall(note.get('html') or ''):
        if _LOCAL_ATTACHMENT_HOST not in href:
            return href
    return None
