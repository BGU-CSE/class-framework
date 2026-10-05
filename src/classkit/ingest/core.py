"""Scan, reconcile, convert — the deterministic half of `/ingest` (spec §8.7).

The one piece of logic everything shares is `reconcile()`: given the manifest and what is in
`materials/source/` now, what is new, changed, moved, duplicated or gone? The pre-flight
report, the run itself, and the validator's `materials_not_ingested` rule all call it, so the
three can never disagree about what "not yet ingested" means. It works on a copy; only `run()`
saves what it decided.

A run is incremental and resumable: only new or changed sources are converted, and the manifest
is saved after every material, so an interrupted run picks up where it stopped. If it stopped
between writing a material's `.md` and saving the manifest, the next run finds that orphan file
(same canonical path, same source hash) and adopts its id instead of minting a new one.

`materials/source/` is the teacher's. Nothing in this module writes, moves or deletes anything
under it; every write goes through `classkit.write`.

**Private material** (D-040) is anything under `source/private/`, which the course's `.gitignore`
keeps out of git. For it, the committed `ingested/` file is an *index* — every anchor, with its
one-line labels, no body text — and the full text goes to the gitignored `private-text/`, on this
machine only. A private source that is missing is "not on this machine", never "removed": a TA's
clone that never had the book and a teacher's machine that lost it look the same from inside a
checkout. Removing one is explicit (`remove`).

The full text **certifies itself** (D-041): its front matter carries `body_hash`, the hash of the
file as ingest wrote it (everything but that line). A file that still matches is ingest's own
output and may be replaced freely — even a stale one, made from another version of the source, or
by another library version; one that does not match is the teacher's edit, protected like any
hand edit. Nothing machine-specific reaches the committed manifest.
"""

from __future__ import annotations

import copy
import datetime
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..frontmatter import FrontMatterError, parse as parse_front_matter
from ..scaffold import slugify
from ..write import content_hash, remove as remove_file, write
from . import extract as ex
from . import links as linkfile
from .manifest import (
    AUDIENCES,
    INGESTED_DIR,
    KINDS,
    PRIVATE_TEXT_DIR,
    SOURCE_DIR,
    active,
    by_id,
    ingested_file,
    is_private,
    load,
    next_id,
    private_text_file,
    save,
    sha256_bytes,
    sha256_file,
)

#: Files in `source/` that are not course material. `README.md` and `links.md` at the top level
#: are the framework's (links.md is read separately); the rest is operating-system litter.
SKIP_TOP_LEVEL = {"readme.md", linkfile.LINKS_FILE}
SKIP_NAMES = {"thumbs.db", "desktop.ini"}

#: Which status values come with an ingested `.md` (and so with anchors).
HAS_FILE = (ex.INGESTED, ex.NO_TEXT)

#: `units: all` — a course-wide material (D-040).
ALL_UNITS = "all"


def units_of(record: dict, unit_ids: list[str]) -> list[str]:
    """The units a material supports, with `all` expanded to every unit in `unit_ids` — how a
    consumer reads the hint."""
    units = record.get("units") or []
    return list(unit_ids) if units == ALL_UNITS else [u for u in units if isinstance(u, str)]


def today() -> str:
    return datetime.date.today().isoformat()


# -- scanning --------------------------------------------------------------------

@dataclass
class SourceFile:
    rel: str  # POSIX path relative to materials/source/
    path: Path
    hash: str
    size: int

    @property
    def format(self) -> str:
        return ex.format_of(self.path)


def scan(course_root: Path) -> list[SourceFile]:
    """Every material file under `materials/source/`, sorted, hashed. Reads; never writes."""
    source = course_root / SOURCE_DIR
    if not source.is_dir():
        return []
    found = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source)
        if any(part.startswith(".") for part in rel.parts):
            continue  # .DS_Store, .gitkeep, editors' swap files
        name = rel.name.lower()
        if name in SKIP_NAMES or name.startswith("~$"):  # Office lock files
            continue
        if len(rel.parts) == 1 and name in SKIP_TOP_LEVEL:
            continue
        found.append(SourceFile(rel.as_posix(), path, sha256_file(path), path.stat().st_size))
    return found


def link_hash(url: str) -> str:
    return sha256_bytes(linkfile.normalize(url).encode("utf-8"))


# -- reconcile -------------------------------------------------------------------

@dataclass
class NewMaterial:
    """Sources not yet in the manifest. Exact copies of one another arrive as one."""

    paths: list[str]
    hash: str
    files: list[SourceFile] = field(default_factory=list)


@dataclass
class Plan:
    """What reconcile found. Paths are relative to `materials/source/`."""

    unchanged: list[str] = field(default_factory=list)
    new: list[NewMaterial] = field(default_factory=list)
    new_links: list[linkfile.Link] = field(default_factory=list)
    changed: list[tuple[str, str]] = field(default_factory=list)  # (id, path)
    moved: list[tuple[str, str, str]] = field(default_factory=list)  # (id, old, new)
    duplicates: list[tuple[str, str]] = field(default_factory=list)  # (id, path) — merged, same hash
    detached: list[tuple[str, str]] = field(default_factory=list)  # (id, path) — copy diverged
    gone: list[tuple[str, str]] = field(default_factory=list)  # (id, path) — a copy vanished
    restored: list[tuple[str, str]] = field(default_factory=list)  # (id, path)
    removed: list[str] = field(default_factory=list)  # ids
    #: links an earlier version harvested from inside a material (`found_in`) and that links.md
    #: does not list — retired, since links come only from links.md now (D-040)
    unharvested: list[str] = field(default_factory=list)  # ids
    #: (id, why) — materials whose conversion is due: changed, file missing, refused last time,
    #: or a converter that is now available
    pending: list[tuple[str, str]] = field(default_factory=list)
    #: ids whose source changed while their ingested file holds a hand edit: the next run will
    #: refuse until the teacher answers `--keep ID` or `--overwrite ID` (F-25)
    awaiting: list[str] = field(default_factory=list)
    rejected_link_lines: list[tuple[int, str]] = field(default_factory=list)

    def outstanding(self) -> list[str]:
        """One line per thing the manifest does not yet reflect — the substance of
        `materials_not_ingested`."""
        lines = []
        for item in self.new:
            lines.append(f"new: {item.paths[0]}" + (f" (+{len(item.paths) - 1} identical)" if len(item.paths) > 1 else ""))
        lines += [f"new link: {link.url}" for link in self.new_links]
        lines += [f"changed: {path} ({mid})" for mid, path in self.changed if mid not in self.awaiting]
        lines += [f"awaiting your decision on {mid}: its ingested file was edited by hand and its "
                  f"source has changed — `classkit ingest --keep {mid}` keeps your edit, "
                  f"`--overwrite {mid}` replaces it" for mid in self.awaiting]
        lines += [f"moved: {old} → {new} ({mid})" for mid, old, new in self.moved]
        lines += [f"duplicate of {mid}: {path}" for mid, path in self.duplicates]
        lines += [f"copy no longer identical: {path} (was part of {mid})" for mid, path in self.detached]
        lines += [f"copy removed: {path} ({mid})" for mid, path in self.gone]
        lines += [f"back again: {path} ({mid})" for mid, path in self.restored]
        lines += [f"source removed: {mid}" for mid in self.removed if mid not in self.unharvested]
        lines += [f"link found inside a material, not in links.md — no longer recorded: {mid}"
                  for mid in self.unharvested]
        changed_ids = {mid for mid, _ in self.changed}
        lines += [f"not converted: {mid} — {why}" for mid, why in self.pending
                  if mid not in changed_ids and mid not in self.awaiting]
        return lines

    def needs_ingest(self) -> bool:
        """Is there anything a plain `classkit ingest` would settle? Not true of a refusal awaiting
        the teacher's answer, which the same run would only refuse again."""
        return any(not line.startswith("awaiting your decision") for line in self.outstanding())


def reconcile(course_root: Path, records: list[dict], files: list[SourceFile],
              links: linkfile.LinksFile, *, date: str | None = None,
              local: bool = True) -> tuple[list[dict], Plan]:
    """Match what is on disk against the manifest. Pure: returns updated *copies* of the
    records and a Plan, and touches no file.

    `local=False` is the validator's view (spec §2.2: `validate` gives the same answer on every
    clone): what is under `source/private/` differs per machine, so private files are not looked
    at and private materials are not judged — `classkit doctor` reports them instead.
    """
    date = date or today()
    records = copy.deepcopy(records)
    if not local:
        files = [f for f in files if not is_private(f.rel)]
    plan = Plan(rejected_link_lines=list(links.rejected))
    live = [r for r in active(records) if r.get("format") != "url"]
    present = {f.rel: f for f in files}

    for record in live:
        hashes = record.setdefault("source_hashes", {})
        for path in record.get("sources") or []:
            if path not in hashes:
                hashes[path] = record.get("source_hash") if path == record.get("canonical") else None

    by_path = {path: record for record in live for path in record.get("sources") or []}

    # 1. Paths the manifest already knows.
    unmatched: list[SourceFile] = []
    for f in files:
        record = by_path.get(f.rel)
        if record is None:
            unmatched.append(f)
            continue
        hashes = record["source_hashes"]
        if hashes.get(f.rel) in (None, f.hash):
            hashes[f.rel] = f.hash
            plan.unchanged.append(f.rel)
        elif f.rel == record.get("canonical"):
            hashes[f.rel] = f.hash
            plan.changed.append((record["id"], f.rel))
        else:
            # A merged copy that is no longer identical (or a confirmed export that was
            # re-exported) — it may no longer be the same material, so it stands alone again
            # and the classifier asks about it afresh.
            record["sources"].remove(f.rel)
            del hashes[f.rel]
            plan.detached.append((record["id"], f.rel))
            unmatched.append(f)

    # 2. Paths it does not: moved, an exact duplicate, a removed file come back, or new.
    def index() -> dict[str, list[tuple[dict, str]]]:
        found: dict[str, list[tuple[dict, str]]] = defaultdict(list)
        for record in live:
            for path, value in record["source_hashes"].items():
                found[value].append((record, path))
        return found

    removed_records = [r for r in records if r.get("removed_at") and not r.get("merged_into")
                       and r.get("format") != "url"]
    new_by_hash: dict[str, NewMaterial] = {}

    for f in unmatched:
        matches = index().get(f.hash, [])
        missing = [(record, path) for record, path in matches if path not in present]
        if missing:
            record, old = missing[0]
            position = record["sources"].index(old)
            record["sources"][position] = f.rel
            record["source_hashes"][f.rel] = record["source_hashes"].pop(old)
            if record.get("canonical") == old:
                record["canonical"] = f.rel
            plan.moved.append((record["id"], old, f.rel))
        elif matches:
            record = matches[0][0]
            record["sources"].append(f.rel)
            record["source_hashes"][f.rel] = f.hash
            plan.duplicates.append((record["id"], f.rel))
        else:
            back = next((r for r in removed_records if r.get("source_hash") == f.hash), None)
            if back is not None:
                back.pop("removed_at", None)
                back["sources"], back["canonical"] = [f.rel], f.rel
                back["source_hashes"] = {f.rel: f.hash}
                removed_records.remove(back)
                live.append(back)
                plan.restored.append((back["id"], f.rel))
            else:
                group = new_by_hash.setdefault(f.hash, NewMaterial([], f.hash))
                group.paths.append(f.rel)
                group.files.append(f)

    # 3. Sources that vanished.
    #    A private path that is missing is "not on this machine", never gone (D-040).
    for record in list(live):
        sources = record.get("sources") or []
        canonical = record.get("canonical")
        for path in [p for p in sources if p not in present and p != canonical and not is_private(p)]:
            sources.remove(path)
            record["source_hashes"].pop(path, None)
            plan.gone.append((record["id"], path))
        if canonical in present or canonical not in sources or is_private(canonical):
            continue
        # The canonical source is gone. An identical copy can take its place without changing
        # a single anchor; anything else would change them, so the material is marked removed
        # and the surviving copies stand alone again.
        canonical_hash = record["source_hashes"].get(canonical)
        twin = next((p for p in sources if p != canonical and record["source_hashes"].get(p) == canonical_hash), None)
        if twin is not None:
            sources.remove(canonical)
            record["source_hashes"].pop(canonical, None)
            record["canonical"] = twin
            plan.moved.append((record["id"], canonical, twin))
            continue
        for path in [p for p in sources if p != canonical]:
            sources.remove(path)
            record["source_hashes"].pop(path, None)
            plan.detached.append((record["id"], path))
            f = present[path]
            group = new_by_hash.setdefault(f.hash, NewMaterial([], f.hash))
            group.paths.append(path)
            group.files.append(f)
        record["removed_at"] = date
        live.remove(record)
        plan.removed.append(record["id"])

    plan.new = list(new_by_hash.values())

    # 4. Links: matched by normalized URL. A link is a material only while links.md lists it
    #    (D-040). One an earlier version harvested from inside a material (`found_in`) is marked
    #    removed like any other unlisted link — and `add-url` brings it back under its old id.
    listed = {linkfile.normalize(link.url): link for link in links.links}
    link_records = {linkfile.normalize(r.get("canonical", "")): r for r in records
                    if r.get("format") == "url" and not r.get("merged_into")}
    for key, link in listed.items():
        record = link_records.get(key)
        if record is None:
            plan.new_links.append(link)
            continue
        if link.note and record.get("note") != link.note:
            record["note"] = link.note
        if record.get("removed_at"):
            record.pop("removed_at")
            record.pop("found_in", None)  # listed now: it is the teacher's link, not a harvested one
            plan.restored.append((record["id"], link.url))
    for key, record in link_records.items():
        if key in listed or record.get("removed_at"):
            continue
        record["removed_at"] = date
        plan.removed.append(record["id"])
        if record.get("found_in"):
            plan.unharvested.append(record["id"])

    # 5. What is due for conversion.
    for record in live:
        canonical = record.get("canonical")
        private = is_private(canonical or "")
        if private and not local:
            continue
        current = record["source_hashes"].get(canonical)
        status = record.get("status")
        if current and current != record.get("source_hash"):
            plan.pending.append((record["id"], "source changed since it was last converted"))
            if not private and _hand_edited(course_root, record):
                plan.awaiting.append(record["id"])
        elif status in HAS_FILE and ingested_file(course_root, record["id"]) is None:
            plan.pending.append((record["id"], "its ingested file is missing"))
        elif private != bool(record.get("private")):
            plan.pending.append((record["id"], "moved into private/: its committed copy becomes an index"
                                 if private else "moved out of private/: its committed copy becomes the full text"))
        elif private and status in HAS_FILE and canonical in present and _full_text_due(course_root, record):
            plan.pending.append((record["id"], "its full text is missing or stale on this machine"))
        elif status == ex.UNSUPPORTED and canonical in present and _converter_now_available(canonical):
            plan.pending.append((record["id"], "a converter for it is now available"))

    return records, plan


def front_matter_of(path: Path) -> dict:
    """The front matter of an ingested or full-text file, read without loading a book-sized
    body — only up to the closing `---`. Empty if there is none or it cannot be read."""
    try:
        with path.open(encoding="utf-8") as stream:
            if stream.readline().strip() != "---":
                return {}
            lines = []
            for line in stream:
                if line.strip() == "---":
                    data = yaml.safe_load("".join(lines))
                    return data if isinstance(data, dict) else {}
                lines.append(line)
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        pass
    return {}


def _hand_edited(course_root: Path, record: dict) -> bool:
    """Its ingested file differs from what ingest last wrote — the teacher's edit."""
    path = ingested_file(course_root, record["id"])
    return (path is not None and bool(record.get("ingested_hash"))
            and sha256_bytes(path.read_bytes()) != record["ingested_hash"])


def _full_text_due(course_root: Path, record: dict) -> bool:
    """A private material's full text is due when it is not on this machine, or was made from
    another version of the source than the one last converted (stale)."""
    path = private_text_file(course_root, record["id"])
    return path is None or front_matter_of(path).get("source_hash") != record.get("source_hash")


def _converter_now_available(path: str) -> bool:
    """An `unsupported` file is retried only when an optional converter for its format has been
    installed since — not merely because a corrupt file happens to probe cleanly, which would
    retry it (and warn about it) on every run."""
    extension = Path(path).suffix.lower()
    if extension in ex.PANDOC_EXTENSIONS:
        return ex.pandoc() is not None
    if extension in ex.LIBREOFFICE_EXTENSIONS:
        return ex.libreoffice() is not None
    return False


# -- pre-flight --------------------------------------------------------------------

@dataclass
class Preflight:
    files: list[SourceFile]
    plan: Plan
    links_listed: int
    by_format: dict[str, int]
    size: int
    slides: int
    pages: int
    unsupported: list[tuple[str, str]]  # (path, reason)
    media: list[str]
    exact_duplicates: list[list[str]]
    seconds: float
    to_convert: int
    private: int = 0  # files under source/private/
    #: (path, what the reader logged) — files a third-party reader complained about, once each
    complaints: list[tuple[str, list[str]]] = field(default_factory=list)


#: Rough conversion cost for the pre-flight estimate. Recalibrated on the teacher test: 2,204 PDF
#: pages (with fontTools) took ~30 s on a recent Mac, ~0.014 s a page; the estimate had said about
#: 3 minutes. (The earlier hand test, F-14, measured ~0.06 s a page on another machine — an older
#: one errs this many times slower; the estimate stays labelled "rough".) Slides scaled likewise.
SECONDS_PER_PAGE = 0.015
SECONDS_PER_SLIDE = 0.005


def preflight(course_root: Path, *, fetch: bool = True) -> Preflight:
    """Count and inspect — no conversion, no writes. What `/ingest` shows before asking."""
    records = load(course_root)
    files = scan(course_root)
    links = linkfile.read(course_root / SOURCE_DIR)
    _state, plan = reconcile(course_root, records, files, links)

    by_format: dict[str, int] = defaultdict(int)
    slides = pages = 0
    unsupported: list[tuple[str, str]] = []
    media: list[str] = []
    complaints: list[tuple[str, list[str]]] = []
    probes: dict[str, ex.Probe] = {}
    for f in files:
        by_format[f.format] += 1
        probe = probes[f.rel] = ex.probe(f.path)
        slides += probe.slides
        pages += probe.pages
        if probe.warnings:
            complaints.append((f.rel, probe.warnings))
        if probe.status == ex.UNSUPPORTED:
            unsupported.append((f.rel, probe.reason))
        elif probe.status == ex.MEDIA:
            media.append(f.rel)

    # Exact copies are worth showing only where this run has something new: a group the manifest
    # already holds as one material was settled by an earlier run. Copies that are *not* identical
    # (a deck and its PDF export) are not looked for at all (D-040).
    owner = {path: r["id"] for r in active(_state) for path in r.get("sources") or []}
    by_hash: dict[str, list[str]] = defaultdict(list)
    for f in files:
        by_hash[f.hash].append(f.rel)
    exact = [paths for paths in by_hash.values()
             if len(paths) > 1 and len({owner.get(p, p) for p in paths}) > 1]

    # What will actually be converted this run, and roughly how long it takes.
    due = {p for item in plan.new for p in item.paths[:1]}
    pending_ids = {mid for mid, _ in plan.pending}
    for record in by_id(_state).values():
        if record.get("id") in pending_ids and record.get("canonical"):
            due.add(record["canonical"])
    seconds = 0.0
    for f in files:
        if f.rel in due:
            probe = probes[f.rel]
            seconds += ex.seconds_for(f.path) + SECONDS_PER_PAGE * probe.pages + SECONDS_PER_SLIDE * probe.slides
    seconds += (1.5 if fetch else 0.0) * len(plan.new_links)

    return Preflight(
        files=files, plan=plan, links_listed=len(links.links), by_format=dict(sorted(by_format.items())),
        size=sum(f.size for f in files), slides=slides, pages=pages,
        unsupported=unsupported, media=media, exact_duplicates=exact, seconds=seconds,
        # Only for files this run converts: an unchanged file's complaints were reported when it
        # was converted, and repeating them every run is noise (teacher test).
        complaints=[(path, found) for path, found in complaints if path in due],
        to_convert=len(due) + len(plan.new_links),
        private=sum(1 for f in files if is_private(f.rel)),
    )


# -- the run -----------------------------------------------------------------------

@dataclass
class Converted:
    id: str
    title: str
    status: str
    path: str  # canonical source, relative to source/ (or the URL)
    ingested: str = ""  # the .md, relative to the course root
    reason: str = ""
    new: bool = False
    #: a private material's full text, relative to the course root — this machine only
    full_text: str = ""
    #: True when only this machine's full text was written: nothing committed changed, so the
    #: run is not a change to the course (not logged, not "updated")
    local: bool = False
    #: what the teacher should know about the extraction — low yield, empty slides or pages, a
    #: reader that complained (F-06, F-08, F-03/F-10); reported once, by id, in the summary
    quality: list[str] = field(default_factory=list)


@dataclass
class Refusal:
    id: str
    ingested: Path
    preview: str
    #: why the file may hold the teacher's work — shown with the refusal
    reason: str = "edited by hand, and its source has changed"
    #: what `--overwrite` would change: the current file against a fresh extraction, by anchor
    diff: str = ""


#: How much of a refusal's diff is shown: anchors, and lines per anchor.
DIFF_ANCHORS = 10
DIFF_LINES = 14


def _sections(text: str) -> tuple[list[str], dict[str, tuple[str, list[str]]]]:
    """A rendered ingested file's body split at its anchor headings: (anchors in order,
    anchor → (heading text, the lines under it)). The front matter and the opening note are left
    out — they say where the text came from, not what it says."""
    try:
        _front, body = parse_front_matter(text)
    except FrontMatterError:
        body = text
    order: list[str] = []
    found: dict[str, tuple[str, list[str]]] = {}
    seen: dict[str, int] = {}
    current = None
    fenced = False
    for line in body.splitlines():
        if ex._FENCE.match(line):
            fenced = not fenced
        heading = None if fenced else ex._HEADING.match(line)
        base = ex.slug(heading.group(2)) if heading else ""
        if base:
            seen[base] = seen.get(base, -1) + 1
            current = base if seen[base] == 0 else f"{base}-{seen[base]}"
            order.append(current)
            found[current] = (heading.group(2), [])
        elif current is not None:
            found[current][1].append(line)
    return order, found


def anchor_diff(current: str, fresh: str) -> str:
    """What replacing `current` with `fresh` would change, grouped by anchor ("Slide 9: …").

    It cannot say which differences are the teacher's edit and which the source's change — only a
    hash of the old extraction is kept — but it shows exactly what `--overwrite` would lose and
    gain, which is the decision being asked (D-040, F-24)."""
    import difflib  # noqa: PLC0415

    old_order, old = _sections(current)
    new_order, new = _sections(fresh)
    order = old_order + [a for a in new_order if a not in old]
    out: list[str] = []
    changed = 0
    for anchor in order:
        before, after = old.get(anchor), new.get(anchor)
        if before is not None and after is not None and before[1] == after[1]:
            continue
        changed += 1
        if changed > DIFF_ANCHORS:
            continue
        name = (before or after)[0]
        if after is None:
            out.append(f"{name}: only in the current file — replacing removes it")
            body = [f"- {line}" for line in before[1] if line.strip()]
        elif before is None:
            out.append(f"{name}: new in the fresh extraction")
            body = [f"+ {line}" for line in after[1] if line.strip()]
        else:
            out.append(f"{name}:")
            body = [line[0] + " " + line[1:] for line in difflib.unified_diff(
                before[1], after[1], lineterm="", n=0) if line[:1] in "+-" and line[:3] not in ("+++", "---")]
        out += [f"    {line}" for line in body[:DIFF_LINES]]
        if len(body) > DIFF_LINES:
            out.append(f"    … {len(body) - DIFF_LINES} more line(s)")
    if changed > DIFF_ANCHORS:
        out.append(f"… and {changed - DIFF_ANCHORS} more anchor(s) differ")
    return "\n".join(out) if out else "(the text under every anchor is the same; only the front matter differs)"


@dataclass
class RunReport:
    plan: Plan
    converted: list[Converted] = field(default_factory=list)
    refused: list[Refusal] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)


def run(
    course_root: Path,
    *,
    overwrite: tuple[str, ...] | list[str] = (),
    keep: tuple[str, ...] | list[str] = (),
    fetch: bool = True,
    date: str | None = None,
    progress=None,
) -> RunReport:
    """Convert every new or changed source; record everything in the manifest.

    `overwrite` and `keep` are the teacher's answers about hand-edited ingested files the
    previous run refused to replace: replace the edit with a fresh extraction, or keep the edit
    and accept the changed source as converted.
    """
    date = date or today()
    say = progress or (lambda _message: None)
    records = load(course_root)
    files = scan(course_root)
    present = {f.rel: f for f in files}
    links = linkfile.read(course_root / SOURCE_DIR)
    records, plan = reconcile(course_root, records, files, links, date=date)
    save(course_root, records)  # bookkeeping first: moves, duplicates, removals

    report = RunReport(plan=plan)
    overwrite_ids, keep_ids = set(overwrite), set(keep)
    index = by_id(records)
    due = [mid for mid, _ in plan.pending]
    due += [mid for mid in sorted(overwrite_ids) if mid in index and mid not in due and index[mid].get("canonical") in present]

    for material_id in due:
        record = index[material_id]
        source = present.get(record.get("canonical"))
        if source is None:
            continue
        say(f"converting {material_id}  {source.rel}")
        result = _convert(course_root, record, source, date, report,
                          overwrite=material_id in overwrite_ids, keep=material_id in keep_ids)
        save(course_root, records)
        if result is not None:
            report.converted.append(result)

    for group in plan.new:
        first = group.files[0]
        say(f"converting new  {first.rel}")
        record = _adopt_orphan(course_root, records, group) or {
            "id": next_id(course_root, records),
            "title": "",
            "kind": "",
            "format": first.format,
            "status": "",
            "sources": [],
            "canonical": first.rel,
            "source_hash": "",
            "source_hashes": {},
        }
        record["sources"] = list(group.paths)
        record["source_hashes"] = {path: group.hash for path in group.paths}
        if record["canonical"] not in group.paths or not record.get("ingested_hash"):
            record["canonical"] = _preferred(group.paths)
        source = present[record["canonical"]]
        if record not in records:
            records.append(record)
        result = _convert(course_root, record, source, date, report, overwrite=False, keep=False, new=True)
        save(course_root, records)
        if result is not None:
            report.converted.append(result)

    for link in plan.new_links:
        say(f"recording link  {link.url}")
        report.converted.append(_add_link(course_root, records, link.url, note=link.note,
                                          fetch=fetch, date=date))
        save(course_root, records)

    return report


def _preferred(paths: list[str]) -> str:
    """Which of several identical copies is canonical: the shortest path, then alphabetical —
    deterministic, so a re-run never flips it."""
    return sorted(paths, key=lambda p: (p.count("/"), len(p), p))[0]


def _adopt_orphan(course_root: Path, records: list[dict], group: NewMaterial) -> dict | None:
    """An `ingested/` file whose id the manifest does not know, written for exactly this source
    — what an interrupted run leaves behind. Reusing its id keeps the run resumable."""
    known = {str(r.get("id")) for r in records}
    directory = course_root / INGESTED_DIR
    if not directory.is_dir():
        return None
    for path in sorted(directory.glob("M*.md")):
        match = re.match(r"^(M\d{4})(-|\.md$)", path.name)
        if not match or match.group(1) in known:
            continue
        try:
            data, _body = parse_front_matter(path.read_text(encoding="utf-8"))
        except (FrontMatterError, OSError, UnicodeDecodeError):
            continue
        if data.get("canonical") in group.paths and data.get("source_hash") == group.hash:
            record = {
                "id": match.group(1), "title": str(data.get("title") or ""), "kind": "",
                "format": ex.format_of(Path(data["canonical"])), "status": "", "sources": [],
                "canonical": data["canonical"],
                "source_hash": "", "source_hashes": {},
                "ingested_hash": sha256_bytes(path.read_bytes()),
            }
            return record
    return None


def _default_kind(fmt: str, status: str) -> str:
    """A first guess from the format alone; the classifying agent corrects it."""
    if fmt in ("pptx", "ppt", "odp", "key"):
        return "slides"
    if status == ex.MEDIA:
        return "video"
    return "other"


def render_ingested(record: dict, body: str, *, form: str = "text") -> str:
    """An ingested file: front matter, a note on what it is, then the body.

    `form` is "text" (the ordinary ingested copy), "index" (a private material's committed
    index, D-040: `text: index` in the front matter) or "full" (a private material's full text,
    written to `private-text/` on this machine only).
    """
    front = {
        "id": record["id"],
        "title": record.get("title") or record["id"],
        "format": record.get("format"),
        "canonical": record.get("canonical"),
        "source_hash": record.get("source_hashes", {}).get(record.get("canonical")) or record.get("source_hash"),
    }
    source = f"materials/source/{record.get('canonical')}"
    cite = (f"Cite a place in this file as {record['id']}#<anchor>, where the anchor is a heading "
            "below, e.g. slide-3, page-12.")
    if form == "index":
        front["text"] = "index"
        note = (
            f"<!-- The INDEX of a private material. Its source, {source}, is gitignored, so its "
            "text is never committed: this file has every anchor of the full text, each with its "
            "one-line labels (printed page, sections, slide titles) and no body text. On a machine "
            "that has the source, `classkit ingest` writes the full text to materials/private-text/ "
            "under the same file name; `classkit doctor` says whether it is here. Where it is not, "
            f"the material is index-only: do not present recall as a reading of it. {cite} -->"
        )
    elif form == "full":
        note = (
            f"<!-- The FULL TEXT of a private material, extracted by `classkit ingest` from {source}. "
            "This machine only: materials/private-text/ is gitignored — never commit it. The "
            "committed copy, in materials/ingested/ under the same file name, is an index with the "
            "same anchors. You may correct a bad extraction by hand: a later ingest notices the edit "
            f"and asks before replacing it. {cite} -->"
        )
    else:
        note = (
            f"<!-- Extracted by `classkit ingest` from {source}. "
            "You may correct a bad extraction by hand: a later ingest notices the edit and asks "
            f"before replacing it. {cite} -->"
        )
    return "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=100) + "---\n\n" + note + "\n\n" + body


BODY_HASH = "body_hash"
_CLOSE = "\n---\n"


def certify(content: str) -> str:
    """Add `body_hash` to a rendered file's front matter: the hash of the file as it is without
    that line. The file then certifies itself — any later edit, to the body or the front matter,
    breaks the match (D-041)."""
    head, sep, rest = content.partition(_CLOSE)
    return f"{head}\n{BODY_HASH}: {content_hash(content.encode('utf-8'))}{sep}{rest}"


def self_certified(path: Path) -> bool:
    """True when `path` still holds exactly what ingest wrote: its `body_hash` matches the hash of
    the file without that line. False for an edited file, one without a `body_hash`, or one that
    cannot be read — refusing is the safe direction."""
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    if not text.startswith("---\n"):
        return False
    end = text.find(_CLOSE)
    if end < 0:
        return False
    match = re.search(rf"\n{BODY_HASH}: (\S+)(?=\n)", text[: end + 1])
    if match is None:
        return False
    original = text[: match.start()] + text[match.end():]
    return content_hash(original.encode("utf-8")) == match.group(1)


def full_text_unedited(path: Path, record: dict) -> bool:
    """Is this machine's full text ingest's own, unedited output? It certifies itself; a full
    text written before D-041 has no `body_hash`, and is unedited if it matches the retired
    `private_text_hash` the manifest may still carry."""
    if self_certified(path):
        return True
    legacy = record.get("private_text_hash")
    return bool(legacy) and legacy == sha256_bytes(path.read_bytes())


def _convert(course_root: Path, record: dict, source: SourceFile, date: str, report: RunReport,
             *, overwrite: bool, keep: bool, new: bool = False) -> Converted | None:
    result = ex.extract(source.path)
    current_hash = record["source_hashes"].get(record["canonical"], source.hash)

    private = is_private(source.rel)
    if not record.get("title"):
        # A private material's title is committed (manifest, index), so it is never a line of
        # its body text: a heading, slide title or metadata title, else the file name.
        from_body = private and result.title_from_body
        record["title"] = (not from_body and result.title) or ex.title_from_name(source.rel)
    if not record.get("kind"):
        record["kind"] = _default_kind(record.get("format", ""), result.status)
    record["format"] = source.format
    record["status"] = result.status
    if result.reason:
        record["status_reason"] = result.reason
    else:
        record.pop("status_reason", None)

    committed = new or record.get("source_hash") != current_hash or bool(record.get("private")) != private
    ingested_rel = full_text_rel = ""
    if result.status in HAS_FILE:
        target = ingested_file(course_root, record["id"]) or (
            course_root / INGESTED_DIR / f"{record['id']}-{slugify(record['title'])[:60].strip('-') or 'material'}.md"
        )
        # (file, content, the manifest field holding the hash of what ingest last wrote there —
        # None for the full text, which certifies itself instead: D-041)
        if private:
            full = private_text_file(course_root, record["id"]) or course_root / PRIVATE_TEXT_DIR / target.name
            writes = [
                (target, render_ingested(record, ex.index_body(result.body, result.labels), form="index"),
                 "ingested_hash"),
                (full, certify(render_ingested(record, result.body, form="full")), None),
            ]
        else:
            writes = [(target, render_ingested(record, result.body), "ingested_hash")]

        edited = []
        for path, _content, field_name in writes:
            if not path.is_file():
                edited.append(False)
            elif field_name is None:
                edited.append(not full_text_unedited(path, record))
            else:
                edited.append(sha256_bytes(path.read_bytes()) != record.get(field_name))

        if any(edited) and keep:
            # The teacher keeps their edit; the changed source counts as seen.
            record["source_hash"] = current_hash
            report.kept.append(record["id"])
            return None
        # Our own unmodified output may be replaced (that is what re-ingesting means); a hand
        # edit may be replaced only on the teacher's say-so. Without it, write() refuses. Both
        # files of a private material are asked first, so neither is written if one is refused —
        # an index and a full text from different versions would disagree about their anchors.
        refusals = [
            Refusal(record["id"], path, outcome.preview, _refusal_reason(record, path, field_name),
                    diff=anchor_diff(path.read_text(encoding="utf-8", errors="replace"), content))
            for (path, content, field_name), was_edited in zip(writes, edited)
            if (outcome := write(path, content, overwrite=overwrite or not was_edited, dry_run=True)).refused
        ]
        if refusals:
            report.refused += refusals
            return None
        for (path, content, field_name), was_edited in zip(writes, edited):
            outcome = write(path, content, overwrite=overwrite or not was_edited)
            if field_name == "ingested_hash":
                record[field_name] = sha256_bytes(path.read_bytes())
                committed = committed or outcome.wrote
                ingested_rel = path.relative_to(course_root).as_posix()
            else:
                full_text_rel = path.relative_to(course_root).as_posix()

    if private:
        record["private"] = True
    else:
        record.pop("private", None)
        _drop_full_text(course_root, record)
    # Retired by D-041 (the full text certifies itself): dropped whenever a material is converted,
    # so an older manifest sheds it as its materials are re-ingested.
    record.pop("private_text_hash", None)

    record["source_hash"] = current_hash
    if committed:
        record["ingested_at"] = date
    return Converted(record["id"], record["title"], result.status, source.rel, ingested_rel,
                     result.reason, new, full_text=full_text_rel, local=not committed,
                     quality=result.quality())


def _refusal_reason(record: dict, path: Path, field_name: str | None) -> str:
    if field_name is None:
        # The full text certifies itself, so this one really was edited (D-041). An unedited
        # stale one — another version of the source, another library — is simply refreshed.
        if front_matter_of(path).get("source_hash") != record.get("source_hash"):
            return ("this machine's full text was edited by hand, and was made from another "
                    "version of the source")
        return "this machine's full text was edited by hand, and its source has changed"
    return "edited by hand, and its source has changed"


def _drop_full_text(course_root: Path, record: dict) -> None:
    """A material moved out of `private/` no longer needs this machine's full text: its full
    text is now the committed file. The local copy is deleted only if it is exactly what ingest
    wrote — it certifies itself, so no teacher's edit is lost — and through the write path's
    guarded `remove()` (D-041). A hand-edited one is left in place, and `classkit doctor` lists
    it."""
    path = private_text_file(course_root, record["id"])
    if path is not None and full_text_unedited(path, record):
        remove_file(path, content_hash(path.read_bytes()))


def _add_link(course_root: Path, records: list[dict], url: str, *, note: str = "",
              fetch: bool, date: str) -> Converted:
    title, duration = "", ""
    if fetch:
        try:
            metadata = linkfile.fetch_metadata(url)
            title, duration = metadata.title, metadata.duration
        except Exception:  # offline, 404, a slow server: the link is recorded all the same
            pass
    record = {
        "id": next_id(course_root, records),
        "title": title or note or url,
        "kind": linkfile.kind_of(url),
        "format": "url",
        "status": ex.LINK,
        "sources": [url],
        "canonical": url,
        "source_hash": link_hash(url),
        "note": note,
        "duration": duration,
        "ingested_at": date,
    }
    records.append(record)
    return Converted(record["id"], record["title"], ex.LINK, url, new=True)


# -- teacher/agent edits to the manifest ----------------------------------------------

class MaterialError(ValueError):
    pass


def set_fields(course_root: Path, material_id: str, *, kind: str | None = None,
               units: list[str] | None = None, title: str | None = None,
               audience: str | None = None) -> dict:
    """Set a material's `kind`, `units`, `title` or `audience` — how the classifying agent's
    decisions, and the teacher's corrections, are recorded without editing a file by hand."""
    records = load(course_root)
    record = by_id(records).get(material_id)
    if record is None:
        raise MaterialError(f"no material {material_id} in the manifest")
    _set(record, _checked(material_id, kind, units, title, audience))
    save(course_root, records)
    return record


def _checked(material_id: str, kind, units, title, audience=None) -> dict:
    """The fields to set, validated; raises MaterialError naming the material."""
    fields: dict = {}
    if audience is not None:
        if audience not in AUDIENCES:
            raise MaterialError(f"{material_id}: audience must be one of {', '.join(AUDIENCES)}, "
                                f"not {audience!r}")
        fields["audience"] = audience
    if kind is not None:
        if kind not in KINDS:
            raise MaterialError(f"{material_id}: kind must be one of {', '.join(KINDS)}, not {kind!r}")
        fields["kind"] = kind
    if units is not None:
        # `all` = course-wide (D-040): the textbook, a course Gem. Accepted as the value itself or
        # as the only entry of a list (`--unit all` on the command line).
        if isinstance(units, str) and units.strip().lower() == ALL_UNITS:
            units = [ALL_UNITS]
        if not isinstance(units, list):
            raise MaterialError(f"{material_id}: units must be a list, e.g. [U03, U04], or `all`")
        units = [str(u).upper() if str(u).lower() != ALL_UNITS else ALL_UNITS for u in units]
        if ALL_UNITS in units:
            if len(units) > 1:
                raise MaterialError(f"{material_id}: `all` means every unit — use it alone, not "
                                    "alongside unit ids")
            fields["units"] = ALL_UNITS
        else:
            bad = [u for u in units if not re.fullmatch(r"U\d{2}", u)]
            if bad:
                raise MaterialError(f"{material_id}: unit ids look like U03, not {', '.join(bad)}")
            fields["units"] = sorted(set(units))
    if title is not None:
        if not str(title).strip():
            raise MaterialError(f"{material_id}: a title cannot be empty")
        fields["title"] = " ".join(str(title).split())
    return fields


def _set(record: dict, fields: dict) -> None:
    record.update(fields)


APPLY_KEYS = {"id", "kind", "units", "title", "audience"}


def apply(course_root: Path, entries) -> list[tuple[str, dict]]:
    """`apply_all`, returning only (id, fields that changed) for the materials that changed."""
    return [(mid, {k: fields[k] for k in changed}) for mid, fields, changed in apply_all(course_root, entries)
            if changed]


def apply_all(course_root: Path, entries) -> list[tuple[str, dict, set[str]]]:
    """Record a batch of classifications — the classifying agent's returned block, applied by
    `/ingest` (D-039). All or nothing: every entry is checked before any is recorded, so a typo
    in entry 40 does not leave 39 recorded and the rest not.

    Each entry is `{id, kind?, units?, title?, audience?}`. Returns, for every entry, (id, every
    field it set, the names of those that changed) — so the teacher sees what was confirmed as
    well as what changed.
    """
    if not isinstance(entries, list):
        raise MaterialError("expected a list of entries, each with an `id`")
    records = load(course_root)
    index = by_id(records)
    planned: list[tuple[dict, dict]] = []
    seen: set[str] = set()
    for position, entry in enumerate(entries, 1):
        if not isinstance(entry, dict) or not entry.get("id"):
            raise MaterialError(f"entry {position}: each entry needs an `id`, e.g. id: M0007")
        material_id = str(entry["id"]).upper()
        unknown = set(entry) - APPLY_KEYS
        if unknown:
            raise MaterialError(f"{material_id}: unknown keys {', '.join(sorted(unknown))} "
                                f"(allowed: {', '.join(sorted(APPLY_KEYS))})")
        if material_id in seen:
            raise MaterialError(f"{material_id} appears twice")
        seen.add(material_id)
        record = index.get(material_id)
        if record is None:
            raise MaterialError(f"no material {material_id} in the manifest")
        if record.get("merged_into") or record.get("removed_at"):
            raise MaterialError(f"{material_id} is merged or removed; classify the material it became")
        fields = _checked(material_id, entry.get("kind"), entry.get("units"), entry.get("title"),
                          entry.get("audience"))
        planned.append((record, fields))

    results = []
    for record, fields in planned:
        changed = {k for k, v in fields.items() if record.get(k) != v}
        _set(record, fields)
        results.append((record["id"], fields, changed))
    if any(changed for _id, _fields, changed in results):
        save(course_root, records)
    return results


def merge(course_root: Path, material_id: str, into: str) -> dict:
    """Merge a confirmed same-material duplicate (a PDF export) into another (its deck).

    Only on the teacher's confirmation. The target keeps its canonical source — and so its
    anchors; the merged material's sources join it, and its id is retired (`merged_into`),
    never reused. Its ingested file is left where it is.
    """
    records = load(course_root)
    index = by_id(records)
    if material_id == into:
        raise MaterialError("a material cannot be merged into itself")
    for mid in (material_id, into):
        record = index.get(mid)
        if record is None:
            raise MaterialError(f"no material {mid} in the manifest")
        if record.get("merged_into") or record.get("removed_at"):
            raise MaterialError(f"{mid} is already merged or removed")
    source, target = index[material_id], index[into]
    if (source.get("format") == "url") != (target.get("format") == "url"):
        raise MaterialError("a link and a file cannot be merged")
    target.setdefault("source_hashes", {})
    for path in source.get("sources") or []:
        if path not in target["sources"]:
            target["sources"].append(path)
            target["source_hashes"][path] = (source.get("source_hashes") or {}).get(path) or source.get("source_hash")
    if ALL_UNITS in (target.get("units"), source.get("units")):
        target["units"] = ALL_UNITS
    else:
        target["units"] = sorted(set(target.get("units") or []) | set(source.get("units") or [])) or target.get("units")
    source["merged_into"] = into
    save(course_root, records)
    return target


def remove(course_root: Path, material_id: str, *, date: str | None = None) -> dict:
    """Mark a private material removed — the explicit act D-040 asks for, because ingest never
    infers it: a private source that is missing may simply not be on this machine.

    Only for a private material (any other is removed by deleting its source: ingest notices),
    and only once its source is gone from this machine — otherwise the next ingest would find it
    and restore it. Like every removal, the record and its index are kept, so a locator to it
    fails visibly.
    """
    records = load(course_root)
    record = by_id(records).get(material_id)
    if record is None:
        raise MaterialError(f"no material {material_id} in the manifest")
    if record.get("merged_into") or record.get("removed_at"):
        raise MaterialError(f"{material_id} is already merged or removed")
    if not (record.get("private") or is_private(record.get("canonical") or "")):
        raise MaterialError(
            f"{material_id} is not private material. To remove it, delete its source from "
            "materials/source/ and run `classkit ingest`, which marks it removed."
        )
    here = [p for p in record.get("sources") or [] if (course_root / SOURCE_DIR / p).is_file()]
    if here:
        raise MaterialError(
            f"the source of {material_id} is still on this machine (materials/source/{here[0]}). "
            "Delete or move it first — otherwise the next ingest finds it and restores the material."
        )
    record["removed_at"] = date or today()
    save(course_root, records)
    return record
