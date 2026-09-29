"""The course log — `LOG.md` at the course root (D-036, spec §8.8).

Git records which bytes changed; the log records **what a change meant and why**, which is
what an agent revising the course next year needs. It covers the course only — never
framework development.

One entry per non-trivial change, in one fixed shape so it stays parseable:

    ## 2026-10-02 — /design-unit 3, step 1 approved
    - **Changed:** U03-S01..S04 created (14 guiding questions)
    - **Why:** first design of unit 3; teacher asked for fewer proof-heavy questions
    - **Files:** units/03-heaps/sessions/01.md, units/03-heaps/sessions/04.md

The log is **append-only**: `append()` opens the file for appending and never rewrites
what is there, so — like the write path (§8.6) — it cannot destroy a teacher's text,
including entries the teacher wrote by hand.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path

from .write import write

LOG_FILE = "LOG.md"

HEADER = """# Course log

What changed in this course, and **why** — the meaning that git's history of bytes does not
carry. Agents read the recent entries before they start work, so they know what was done last
time and for what reason.

Append-only, newest at the bottom. Commands add an entry at every approved step through
`classkit log`; you may add your own by hand ("taught U03 — students found S02 too long").
Keep the shape below so the log stays readable by tools.
"""

_HEADING = re.compile(r"^## (?:(?P<date>\d{4}-\d{2}-\d{2}) — )?(?P<title>.*?)\s*$")
_FIELD = re.compile(r"^- \*\*(?P<name>Changed|Why|Files):\*\* ?(?P<value>.*?)\s*$")


@dataclass
class Entry:
    title: str
    changed: str = ""
    why: str = ""
    files: list[str] = field(default_factory=list)
    date: str = ""
    #: any other lines under the heading — hand-written entries need not follow the shape
    notes: list[str] = field(default_factory=list)


def _one_line(text: str) -> str:
    """Collapse runs of whitespace, newlines included: one field is one line."""
    return " ".join(str(text).split())


def format_entry(entry: Entry) -> str:
    title = _one_line(entry.title)
    if not title:
        raise ValueError("a log entry needs a title — which command or who, and what happened")
    date = entry.date or datetime.date.today().isoformat()

    lines = [f"## {date} — {title}"]
    if entry.changed:
        lines.append(f"- **Changed:** {_one_line(entry.changed)}")
    if entry.why:
        lines.append(f"- **Why:** {_one_line(entry.why)}")
    files = [_one_line(f) for f in entry.files if _one_line(f)]
    if files:
        lines.append(f"- **Files:** {', '.join(files)}")
    return "\n".join(lines) + "\n"


def parse(text: str) -> list[Entry]:
    """Read every entry in a log. Tolerant of hand-written entries: a heading with no date
    keeps its whole text as the title, and lines that are not a known field become notes."""
    entries: list[Entry] = []
    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading and not line.startswith("###"):
            entries.append(Entry(title=heading["title"], date=heading["date"] or ""))
            continue
        if not entries or not line.strip():
            continue  # the header above the first entry, or blank lines
        current = entries[-1]
        found = _FIELD.match(line)
        if found is None:
            current.notes.append(line)
        elif found["name"] == "Changed":
            current.changed = found["value"]
        elif found["name"] == "Why":
            current.why = found["value"]
        else:
            current.files = [f.strip() for f in found["value"].split(",") if f.strip()]
    return entries


def new_log(first: Entry) -> str:
    """The content of a fresh `LOG.md`: the header, then its first entry."""
    return f"{HEADER}\n{format_entry(first)}"


def append(course_root: Path, entry: Entry) -> Path:
    """Append one entry to the course's `LOG.md`, creating the log if it does not exist.

    Existing content is never rewritten: the file is opened for appending, and only a
    separating newline is added if the last entry does not end in one.
    """
    path = course_root / LOG_FILE
    text = format_entry(entry)

    if not path.exists():
        # Create through the write path, which refuses rather than replace anything that
        # appeared in between.
        outcome = write(path, f"{HEADER}\n{text}")
        if not outcome.refused:
            return path

    existing = path.read_text(encoding="utf-8")
    separator = "" if not existing else ("\n" if existing.endswith("\n") else "\n\n")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(separator + text)
    return path
