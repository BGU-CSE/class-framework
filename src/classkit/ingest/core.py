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
from ..write import write
from . import extract as ex
from . import links as linkfile
from .manifest import (
    INGESTED_DIR,
    KINDS,
    SOURCE_DIR,
    active,
    by_id,
    ingested_file,
    load,
    next_id,
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
    #: (id, why) — materials whose conversion is due: changed, file missing, refused last time,
    #: or a converter that is now available
    pending: list[tuple[str, str]] = field(default_factory=list)
    rejected_link_lines: list[tuple[int, str]] = field(default_factory=list)

    def outstanding(self) -> list[str]:
        """One line per thing the manifest does not yet reflect — the substance of
        `materials_not_ingested`."""
        lines = []
        for item in self.new:
            lines.append(f"new: {item.paths[0]}" + (f" (+{len(item.paths) - 1} identical)" if len(item.paths) > 1 else ""))
        lines += [f"new link: {link.url}" for link in self.new_links]
        lines += [f"changed: {path} ({mid})" for mid, path in self.changed]
        lines += [f"moved: {old} → {new} ({mid})" for mid, old, new in self.moved]
        lines += [f"duplicate of {mid}: {path}" for mid, path in self.duplicates]
        lines += [f"copy no longer identical: {path} (was part of {mid})" for mid, path in self.detached]
        lines += [f"copy removed: {path} ({mid})" for mid, path in self.gone]
        lines += [f"back again: {path} ({mid})" for mid, path in self.restored]
        lines += [f"source removed: {mid}" for mid in self.removed]
        changed_ids = {mid for mid, _ in self.changed}
        lines += [f"not converted: {mid} — {why}" for mid, why in self.pending if mid not in changed_ids]
        return lines


def reconcile(course_root: Path, records: list[dict], files: list[SourceFile],
              links: linkfile.LinksFile, *, date: str | None = None) -> tuple[list[dict], Plan]:
    """Match what is on disk against the manifest. Pure: returns updated *copies* of the
    records and a Plan, and touches no file."""
    date = date or today()
    records = copy.deepcopy(records)
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
    for record in list(live):
        sources = record.get("sources") or []
        canonical = record.get("canonical")
        for path in [p for p in sources if p not in present and p != canonical]:
            sources.remove(path)
            record["source_hashes"].pop(path, None)
            plan.gone.append((record["id"], path))
        if canonical in present or canonical not in sources:
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

    # 4. Links: matched by normalized URL. A link found inside a document stays while its
    #    `found_in` material does; one listed only in links.md goes when its line does.
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
            plan.restored.append((record["id"], link.url))
    for key, record in link_records.items():
        if key in listed or record.get("removed_at") or record.get("found_in"):
            continue
        record["removed_at"] = date
        plan.removed.append(record["id"])

    # 5. What is due for conversion.
    for record in live:
        canonical = record.get("canonical")
        current = record["source_hashes"].get(canonical)
        status = record.get("status")
        if current and current != record.get("source_hash"):
            plan.pending.append((record["id"], "source changed since it was last converted"))
        elif status in HAS_FILE and ingested_file(course_root, record["id"]) is None:
            plan.pending.append((record["id"], "its ingested file is missing"))
        elif status == ex.UNSUPPORTED and canonical in present and _converter_now_available(canonical):
            plan.pending.append((record["id"], "a converter for it is now available"))

    return records, plan


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
    embedded_links: int
    unsupported: list[tuple[str, str]]  # (path, reason)
    media: list[str]
    exact_duplicates: list[list[str]]
    suspected_duplicates: list[list[str]]
    seconds: float
    to_convert: int


def preflight(course_root: Path, *, fetch: bool = True) -> Preflight:
    """Count and inspect — no conversion, no writes. What `/ingest` shows before asking."""
    records = load(course_root)
    files = scan(course_root)
    links = linkfile.read(course_root / SOURCE_DIR)
    _state, plan = reconcile(course_root, records, files, links)

    by_format: dict[str, int] = defaultdict(int)
    slides = pages = embedded = 0
    unsupported: list[tuple[str, str]] = []
    media: list[str] = []
    for f in files:
        by_format[f.format] += 1
        probe = ex.probe(f.path)
        slides += probe.slides
        pages += probe.pages
        embedded += probe.links
        if probe.status == ex.UNSUPPORTED:
            unsupported.append((f.rel, probe.reason))
        elif probe.status == ex.MEDIA:
            media.append(f.rel)

    # Duplicates are worth showing only where this run has something to decide: a group the
    # manifest already holds as one material was settled by an earlier run.
    owner = {path: r["id"] for r in active(_state) for path in r.get("sources") or []}
    unsettled = {p for item in plan.new for p in item.paths} | {p for _m, p in plan.changed} \
        | {new for _m, _old, new in plan.moved}

    by_hash: dict[str, list[str]] = defaultdict(list)
    for f in files:
        by_hash[f.hash].append(f.rel)
    exact = [paths for paths in by_hash.values()
             if len(paths) > 1 and len({owner.get(p, p) for p in paths}) > 1]
    suspected = [group for group in suspected_by_name(files) if unsettled & set(group)]

    # What will actually be converted this run, and roughly how long it takes.
    due = {p for item in plan.new for p in item.paths[:1]}
    pending_ids = {mid for mid, _ in plan.pending}
    for record in by_id(_state).values():
        if record.get("id") in pending_ids and record.get("canonical"):
            due.add(record["canonical"])
    seconds = 0.0
    for f in files:
        if f.rel in due:
            probe = ex.probe(f.path)
            seconds += ex.seconds_for(f.path) + 0.04 * probe.pages + 0.02 * probe.slides
    seconds += (1.5 if fetch else 0.0) * len(plan.new_links)

    return Preflight(
        files=files, plan=plan, links_listed=len(links.links), by_format=dict(sorted(by_format.items())),
        size=sum(f.size for f in files), slides=slides, pages=pages, embedded_links=embedded,
        unsupported=unsupported, media=media, exact_duplicates=exact,
        suspected_duplicates=suspected, seconds=seconds,
        to_convert=len(due) + len(plan.new_links),
    )


_COPY_MARKERS = re.compile(r"(copy|final|export(ed)?|print|handout|v\d+|\(\d+\)|\d{1,2}$)", re.I)


def _stem_key(path: str) -> str:
    stem = Path(path).stem.lower()
    stem = re.sub(r"[\s_\-.]+", " ", stem)
    stem = " ".join(w for w in stem.split() if not _COPY_MARKERS.fullmatch(w))
    return re.sub(r"[^\w]", "", stem)


def suspected_by_name(files: list[SourceFile]) -> list[list[str]]:
    """Files whose names say they are the same material in different formats — a deck and its
    PDF export. A suspicion for the teacher to confirm, never merged automatically."""
    groups: dict[str, list[SourceFile]] = defaultdict(list)
    for f in files:
        key = _stem_key(f.rel)
        if key:
            groups[key].append(f)
    suspects = []
    for members in groups.values():
        hashes = {f.hash for f in members}
        formats = {f.format for f in members}
        if len(members) > 1 and len(hashes) > 1 and len(formats) > 1:
            suspects.append(sorted(f.rel for f in members))
    return suspects


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


@dataclass
class Refusal:
    id: str
    ingested: Path
    preview: str


@dataclass
class RunReport:
    plan: Plan
    converted: list[Converted] = field(default_factory=list)
    refused: list[Refusal] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)
    found_links: list[Converted] = field(default_factory=list)
    suspected_duplicates: list[tuple[str, str, str]] = field(default_factory=list)  # (a, b, why)
    #: URLs each conversion found inside its material, recorded as link materials at the end
    embedded: list[tuple[str, list[tuple[str, str]]]] = field(default_factory=list, repr=False)


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
    converted_ids: list[str] = []

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
            converted_ids.append(material_id)

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
            converted_ids.append(record["id"])

    for link in plan.new_links:
        say(f"recording link  {link.url}")
        report.converted.append(_add_link(course_root, records, link.url, note=link.note,
                                          fetch=fetch, date=date))
        save(course_root, records)

    # Links found inside the documents converted this run.
    known = {linkfile.normalize(r.get("canonical", "")) for r in records if r.get("format") == "url"}
    for material_id, found in report.embedded:
        for url, anchor in found:
            try:
                url = linkfile.check_url(url)
            except linkfile.BadURL:
                continue
            if linkfile.normalize(url) in known:
                continue
            known.add(linkfile.normalize(url))
            where = f"{material_id}#{anchor}" if anchor else material_id
            report.found_links.append(_add_link(course_root, records, url, found_in=where,
                                                fetch=fetch, date=date))
        save(course_root, records)

    report.suspected_duplicates = suspected_duplicates(course_root, records, among=set(converted_ids))
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
            return {
                "id": match.group(1), "title": str(data.get("title") or ""), "kind": "",
                "format": ex.format_of(Path(data["canonical"])), "status": "", "sources": [],
                "canonical": data["canonical"],
                "source_hash": "", "source_hashes": {},
                "ingested_hash": sha256_bytes(path.read_bytes()),
            }
    return None


def _default_kind(fmt: str, status: str) -> str:
    """A first guess from the format alone; the classifying agent corrects it."""
    if fmt in ("pptx", "ppt", "odp", "key"):
        return "slides"
    if status == ex.MEDIA:
        return "video"
    return "other"


def render_ingested(record: dict, body: str) -> str:
    front = {
        "id": record["id"],
        "title": record.get("title") or record["id"],
        "format": record.get("format"),
        "canonical": record.get("canonical"),
        "source_hash": record.get("source_hashes", {}).get(record.get("canonical")) or record.get("source_hash"),
    }
    note = (
        f"<!-- Extracted by `classkit ingest` from materials/source/{record.get('canonical')}. "
        "You may correct a bad extraction by hand: a later ingest notices the edit and asks "
        f"before replacing it. Cite a place in this file as {record['id']}#<anchor>, where the "
        "anchor is a heading below, e.g. slide-3, page-12. -->"
    )
    return "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=100) + "---\n\n" + note + "\n\n" + body


def _convert(course_root: Path, record: dict, source: SourceFile, date: str, report: RunReport,
             *, overwrite: bool, keep: bool, new: bool = False) -> Converted | None:
    result = ex.extract(source.path)
    current_hash = record["source_hashes"].get(record["canonical"], source.hash)

    if not record.get("title"):
        record["title"] = result.title or Path(source.rel).stem
    if not record.get("kind"):
        record["kind"] = _default_kind(record.get("format", ""), result.status)
    record["format"] = source.format
    record["status"] = result.status
    if result.reason:
        record["status_reason"] = result.reason
    else:
        record.pop("status_reason", None)

    ingested_rel = ""
    if result.status in HAS_FILE:
        target = ingested_file(course_root, record["id"]) or (
            course_root / INGESTED_DIR / f"{record['id']}-{slugify(record['title'])[:60].strip('-') or 'material'}.md"
        )
        content = render_ingested(record, result.body)
        on_disk = sha256_bytes(target.read_bytes()) if target.is_file() else None
        hand_edited = on_disk is not None and on_disk != record.get("ingested_hash")

        if hand_edited and keep:
            # The teacher keeps their edit; the changed source counts as seen.
            record["source_hash"] = current_hash
            report.kept.append(record["id"])
            return None
        # Our own unmodified output may be replaced (that is what re-ingesting means); a hand
        # edit may be replaced only on the teacher's say-so. Without it, write() refuses.
        outcome = write(target, content, overwrite=overwrite or not hand_edited)
        if outcome.refused:
            report.refused.append(Refusal(record["id"], target, outcome.preview))
            return None
        record["ingested_hash"] = sha256_bytes(target.read_bytes())
        ingested_rel = target.relative_to(course_root).as_posix()

    record["source_hash"] = current_hash
    record["ingested_at"] = date
    report.embedded.append((record["id"], result.links))
    return Converted(record["id"], record["title"], result.status, source.rel, ingested_rel,
                     result.reason, new)


def _add_link(course_root: Path, records: list[dict], url: str, *, note: str = "",
              found_in: str = "", fetch: bool, date: str) -> Converted:
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
        "found_in": found_in,
        "note": note,
        "duration": duration,
        "ingested_at": date,
    }
    records.append(record)
    return Converted(record["id"], record["title"], ex.LINK, url, new=True)


# -- suspected duplicates by content -------------------------------------------------

_WORD = re.compile(r"[^\W\d_]{3,}")
_ANCHOR_LINE = re.compile(r"^(## (Slide|Page) \d+|\*\((printed page|hidden slide).*)$", re.M)


def _words(text: str) -> set[str]:
    try:
        _front, text = parse_front_matter(text)
    except FrontMatterError:
        pass
    text = _ANCHOR_LINE.sub("", re.sub(r"<!--.*?-->", "", text, flags=re.S))
    return {w.lower() for w in _WORD.findall(text)}


def suspected_duplicates(course_root: Path, records: list[dict], *, among: set[str] | None = None,
                         threshold: float = 0.8, min_words: int = 20) -> list[tuple[str, str, str]]:
    """Pairs of materials that look like the same material — most of the smaller one's
    vocabulary appears in the larger, or their file names match across formats. For the teacher
    to confirm; nothing is merged here. With `among`, only pairs involving those ids."""
    texts: dict[str, set[str]] = {}
    names: dict[str, str] = {}
    for record in active(records):
        if record.get("status") not in HAS_FILE:
            continue
        path = ingested_file(course_root, record["id"])
        if path is None:
            continue
        texts[record["id"]] = _words(path.read_text(encoding="utf-8", errors="replace"))
        names[record["id"]] = _stem_key(record.get("canonical", ""))

    pairs = []
    ids = sorted(texts)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if among is not None and a not in among and b not in among:
                continue
            fa, fb = by_id(records)[a].get("format"), by_id(records)[b].get("format")
            small, large = sorted((texts[a], texts[b]), key=len)
            overlap = len(small & large) / len(small) if small else 0.0
            if len(small) >= min_words and overlap >= threshold:
                pairs.append((a, b, f"{overlap:.0%} of the shorter one's words appear in the other"))
            elif names[a] and names[a] == names[b] and fa != fb:
                pairs.append((a, b, "same file name, different format"))
    return pairs


# -- teacher/agent edits to the manifest ----------------------------------------------

class MaterialError(ValueError):
    pass


def set_fields(course_root: Path, material_id: str, *, kind: str | None = None,
               units: list[str] | None = None, title: str | None = None) -> dict:
    """Set a material's `kind`, `units` or `title` — how the classifying agent records what it
    decided without ever editing a file itself."""
    records = load(course_root)
    record = by_id(records).get(material_id)
    if record is None:
        raise MaterialError(f"no material {material_id} in the manifest")
    if kind is not None:
        if kind not in KINDS:
            raise MaterialError(f"kind must be one of {', '.join(KINDS)}, not {kind!r}")
        record["kind"] = kind
    if units is not None:
        bad = [u for u in units if not re.fullmatch(r"U\d{2}", u)]
        if bad:
            raise MaterialError(f"unit ids look like U03, not {', '.join(bad)}")
        record["units"] = sorted(set(units))
    if title is not None:
        if not title.strip():
            raise MaterialError("a title cannot be empty")
        record["title"] = " ".join(title.split())
    save(course_root, records)
    return record


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
    target["units"] = sorted(set(target.get("units") or []) | set(source.get("units") or [])) or target.get("units")
    source["merged_into"] = into
    save(course_root, records)
    return target
