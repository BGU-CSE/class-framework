"""`materials/manifest.yaml` — every material the course has ingested (spec §8.7).

A YAML list, one record per material. `classkit ingest` owns the bookkeeping fields; `kind`,
`units` and `title` are proposed by the classifying agent and recorded by `/ingest` through
`classkit material apply` (D-039), and the teacher may correct any of them by hand. Every save re-reads nothing and rewrites the whole
list, so a value the teacher changed survives (it was loaded with everything else) — but a
YAML *comment* the teacher added does not. That is the cost of a tool-owned file.

Records are never deleted. A removed source is marked `removed_at`; a confirmed duplicate is
marked `merged_into`. That is what keeps ids from ever being reused, and what makes a locator
pointing at either fail visibly rather than silently resolve to something else.
"""

from __future__ import annotations

import datetime
import hashlib
import re
from pathlib import Path

import yaml

from ..write import WriteOutcome, write

SOURCE_DIR = Path("materials") / "source"
INGESTED_DIR = Path("materials") / "ingested"
MANIFEST = Path("materials") / "manifest.yaml"

ID = re.compile(r"^M(\d{4})$")
KINDS = ("slides", "textbook", "notes", "exam", "exercise", "syllabus", "reading", "link",
         "video", "other")

#: Field order in the written file — identity first, bookkeeping last.
FIELDS = (
    "id", "title", "kind", "format", "status", "status_reason", "units", "sources", "canonical",
    "source_hash", "source_hashes", "ingested_hash", "found_in", "note", "duration",
    "ingested_at", "removed_at", "merged_into",
)

HEADER = """\
# Materials manifest — written by `classkit ingest` (spec §8.7). One record per material.
#
# You may correct `title`, `kind` and `units` here (or with `classkit material set`); a later
# ingest keeps your values. Leave the ids, paths and hashes to the tool. Records are never
# deleted: a removed source is marked `removed_at`, a merged duplicate `merged_into`.
# Comments you add to this file are not preserved.
"""


class ManifestError(ValueError):
    """The manifest exists but cannot be read as a list of records."""


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def load(course_root: Path) -> list[dict]:
    path = course_root / MANIFEST
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError(f"{path}: not valid YAML: {exc}") from exc
    if data is None:
        return []
    if not isinstance(data, list):
        raise ManifestError(f"{path}: expected a list of materials at the top level")
    records = []
    for record in data:
        if isinstance(record, dict):
            # YAML reads an unquoted 2026-10-01 as a date; the schema (and we) want a string.
            for key in ("ingested_at", "removed_at"):
                if isinstance(record.get(key), datetime.date):
                    record[key] = record[key].isoformat()
        records.append(record)
    return records


def dump(records: list[dict]) -> str:
    ordered = []
    for record in records:
        known = {key: record[key] for key in FIELDS if key in record and record[key] not in (None, "", [], {})}
        extra = {key: value for key, value in record.items() if key not in FIELDS}
        ordered.append({**known, **extra})
    body = yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True, width=100) if ordered else "[]\n"
    return HEADER + "\n" + body


def save(course_root: Path, records: list[dict]) -> WriteOutcome:
    """Write the manifest through the write path.

    `overwrite=True` is deliberate and safe here: the manifest is the tool's own record, the
    records being written were loaded from it (so the teacher's values are carried over), and
    the alternative — refusing — would make every second ingest fail.
    """
    return write(course_root / MANIFEST, dump(records), overwrite=True)


def active(records: list[dict]) -> list[dict]:
    """Materials that are neither removed nor merged into another."""
    return [r for r in records if not r.get("removed_at") and not r.get("merged_into")]


def by_id(records: list[dict]) -> dict[str, dict]:
    return {str(r.get("id")): r for r in records if isinstance(r, dict)}


def ingested_file(course_root: Path, material_id: str) -> Path | None:
    """The material's `.md` in `ingested/`, located by its id prefix — so the slug after the
    id may change, or be renamed by hand, without losing the file."""
    directory = course_root / INGESTED_DIR
    if not directory.is_dir():
        return None
    for candidate in sorted(directory.glob(f"{material_id}*.md")):
        if candidate.name == f"{material_id}.md" or candidate.name.startswith(f"{material_id}-"):
            return candidate
    return None


def next_id(course_root: Path, records: list[dict]) -> str:
    """One past the highest id ever used — in the manifest *or* in `ingested/` — so an id is
    never reused, even if a record was deleted from the manifest by hand."""
    highest = 0
    for record in records:
        match = ID.match(str(record.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    directory = course_root / INGESTED_DIR
    if directory.is_dir():
        for path in directory.glob("M*.md"):
            match = re.match(r"^M(\d{4})", path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return f"M{highest + 1:04d}"
