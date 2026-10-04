"""`materials/source/links.md` — the course's links (spec §8.7).

One link per line, optionally followed by ` — ` and a note:

    https://www.youtube.com/watch?v=… — heaps explained, 12 min, good for U06
    https://en.wikipedia.org/wiki/Binary_heap

Headings, HTML comments and blank lines are skipped; a leading list bullet (`- `, `* `) is
allowed. Any other line is not a link and is reported, never guessed at.

`classkit add-url` appends a line through the write path's append mode, rejecting a malformed
URL or one already listed. In Core a link is recorded with whatever metadata can be fetched
safely (title, duration) — never its content — and a fetch that fails is not an error: the
link is recorded all the same.
"""

from __future__ import annotations

import html
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from ..write import append

LINKS_FILE = "links.md"

#: Separators accepted between a URL and its note. The spec writes an em dash; a teacher typing
#: by hand often writes " - " or " -- ".
_NOTE = re.compile(r"^\s*(?:—|–|--|-)\s*")
_BULLET = re.compile(r"^\s*[-*+]\s+")

VIDEO_HOSTS = ("youtube.com", "youtu.be", "vimeo.com", "panopto", "kaltura", "loom.com")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".m4v", ".mkv")


@dataclass
class Link:
    url: str
    note: str = ""
    line: int = 0


@dataclass
class LinksFile:
    links: list[Link]
    #: (line number, text) of lines that are not a link, a heading, a comment, or blank
    rejected: list[tuple[int, str]]


class BadURL(ValueError):
    pass


def check_url(url: str) -> str:
    """Return the URL stripped of surrounding space, or raise BadURL saying why."""
    url = url.strip()
    if not url or any(c.isspace() for c in url):
        raise BadURL(f"{url!r} is not a single URL (it is empty or contains spaces)")
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https"):
        raise BadURL(f"{url!r} must start with http:// or https://")
    host = parts.hostname or ""
    if not host or ("." not in host and host != "localhost"):
        raise BadURL(f"{url!r} has no valid host")
    return url


def normalize(url: str) -> str:
    """The form two URLs are compared in: scheme and host lowercased, fragment and a trailing
    slash dropped. The query is kept — `watch?v=…` is the whole identity of a video."""
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def kind_of(url: str) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if any(h in host for h in VIDEO_HOSTS) or parts.path.lower().endswith(VIDEO_EXTENSIONS):
        return "video"
    return "link"


def parse(text: str) -> LinksFile:
    links: list[Link] = []
    rejected: list[tuple[int, str]] = []
    seen: set[str] = set()
    in_comment = False

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if line.startswith("<!--"):
            in_comment = "-->" not in line
            continue
        if not line or line.startswith("#"):
            continue
        line = _BULLET.sub("", line)
        # Markdown link syntax, `[text](url)`, is common enough to accept.
        markdown_link = re.match(r"^\[([^\]]*)\]\((\S+?)\)\s*(.*)$", line)
        if markdown_link:
            url, rest = markdown_link.group(2), markdown_link.group(3)
            note_default = markdown_link.group(1)
        else:
            url, _, rest = line.partition(" ")
            note_default = ""
        try:
            url = check_url(url.strip("<>"))
        except BadURL:
            rejected.append((number, raw.strip()))
            continue
        note = _NOTE.sub("", rest.strip()).strip() or note_default
        key = normalize(url)
        if key in seen:
            continue
        seen.add(key)
        links.append(Link(url=url, note=note, line=number))

    return LinksFile(links, rejected)


def read(source_dir: Path) -> LinksFile:
    path = source_dir / LINKS_FILE
    if not path.is_file():
        return LinksFile([], [])
    return parse(path.read_text(encoding="utf-8", errors="replace"))


def add_url(source_dir: Path, url: str, note: str = "") -> Path:
    """Append one link to `links.md`. Raises BadURL for a malformed URL or a duplicate."""
    url = check_url(url)
    current = read(source_dir)
    if any(normalize(link.url) == normalize(url) for link in current.links):
        raise BadURL(f"{url} is already listed in {LINKS_FILE}")

    path = source_dir / LINKS_FILE
    note = " ".join(note.split())
    line = f"{url} — {note}\n" if note else f"{url}\n"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    separator = "" if not existing or existing.endswith("\n") else "\n"
    outcome = append(path, separator + line)
    if outcome.refused:
        raise BadURL(f"could not append to {path}: {outcome.message}")
    return path


# -- metadata: optional, best effort ---------------------------------------------

@dataclass
class Metadata:
    title: str = ""
    duration: str = ""


_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_OG_TITLE = re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', re.I)
_DURATION = re.compile(r'itemprop=["\']duration["\'][^>]+content=["\']PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', re.I)


def fetch_metadata(url: str, timeout: float = 5.0) -> Metadata:
    """Fetch a page's title (and, where a page declares it, a video's duration).

    Reads at most 512 KB and never follows anything but the page itself. Raises on any
    failure; the caller records the link regardless.
    """
    request = urllib.request.Request(url, headers={"User-Agent": "classkit-ingest/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (http/https checked)
        if "html" not in (response.headers.get("Content-Type") or ""):
            return Metadata()
        page = response.read(512 * 1024).decode("utf-8", "replace")
    found = _OG_TITLE.search(page) or _TITLE.search(page)
    title = " ".join(html.unescape(found.group(1)).split()) if found else ""
    duration = ""
    match = _DURATION.search(page)
    if match and any(match.groups()):
        hours, minutes, seconds = (int(g or 0) for g in match.groups())
        duration = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
    return Metadata(title=title[:200], duration=duration)
