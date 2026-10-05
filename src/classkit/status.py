"""`classkit status` — where the course stands (D-043, spec §8.9). Read-only.

Assembled from the records the course already holds, never from a progress file of its own: the
syllabus's `approved` block and hash, its unit map, the units on disk, the materials manifest and
the course log. Every command shows it first (§5.2), so the teacher and the agent start from the
same picture.

It reads committed files only — private sources are not looked at — so it gives the same answer
on every clone, like `validate` (§2.2). It judges nothing: `validate` reports inconsistencies,
`doctor` this machine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import log
from .approve import SYLLABUS, ApproveError, content_hash, read, unit_hash
from .frontmatter import FrontMatterError, load_yaml

_UNIT_DIR = re.compile(r"^(\d{2})-")

NOT_STARTED = "not started"
DRAFT = "draft"
APPROVED = "approved"
EDITED = "approved, edited since"
UNTRACKED = "approved, edits untracked"
MISSING = "missing"
UNREADABLE = "unreadable"

# A unit's states (D-046, spec §8.9). *Not started* — on the map, no directory yet; *drafted* — a
# directory, not yet approved; then the approved stages, each possibly edited since.
UNIT_DRAFTED = "drafted, not approved"
PLANNED = "planned"
DESIGNED = "designed"


@dataclass
class SyllabusState:
    state: str
    detail: str = ""
    outcomes: int = 0
    unit_map: list[dict] = field(default_factory=list)


@dataclass
class UnitLine:
    number: int
    title: str
    #: NOT_STARTED, UNIT_DRAFTED, PLANNED or DESIGNED — or UNREADABLE
    state: str
    #: what the overview prints: "planned 2026-10-05 — edited since", "not in the unit map", …
    detail: str = ""
    #: True when the approved stage's hash no longer matches
    edited: bool = False


@dataclass
class Status:
    course: str
    units_declared: int | None
    syllabus: SyllabusState
    units: list[UnitLine]
    materials: list[str]
    last_log: str = ""


def syllabus_state(course_root: Path, framework_root: Path | None) -> SyllabusState:
    path = course_root / SYLLABUS
    if not path.is_file():
        return SyllabusState(MISSING, f"there is no {SYLLABUS.as_posix()}")
    try:
        text = path.read_text(encoding="utf-8")
        data, body = read(text)
    except (OSError, UnicodeDecodeError, ApproveError) as exc:
        return SyllabusState(UNREADABLE, str(exc))

    outcomes = len([o for o in data.get("outcomes") or [] if isinstance(o, dict)])
    unit_map = [u for u in data.get("unit_map") or [] if isinstance(u, dict)]
    found = SyllabusState(DRAFT, "not approved", outcomes, unit_map)

    record = data.get("approved")
    if record is not None:
        if not isinstance(record, dict) or not record.get("date"):
            found.detail = "its `approved` record is malformed — `classkit validate` says how"
            return found
        on = record["date"]
        if not record.get("hash"):
            found.state, found.detail = UNTRACKED, f"approved {on} (by hand: edits since cannot be tracked)"
        elif record["hash"] == content_hash(data, body):
            found.state, found.detail = APPROVED, f"approved {on}"
        else:
            found.state, found.detail = EDITED, f"approved {on} — edited since"
        return found

    template = framework_root / "templates" / "course" / "syllabus.md" if framework_root else None
    if (template is not None and template.is_file() and template.read_text(encoding="utf-8") == text) \
            or str(data.get("goal", "")).strip() in ("", "TODO"):
        found.state, found.detail = NOT_STARTED, "the scaffolded placeholders — run /plan-syllabus"
    return found


def unit_state(course_root: Path, directory: Path, number: int) -> tuple[str, str, bool]:
    """(state, detail, edited since) of a unit on disk, from its `approved` record (§8.9)."""
    try:
        data, _body = read((directory / "unit.md").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ApproveError) as exc:
        return UNREADABLE, f"unit.md cannot be read: {exc}", False
    record = data.get("approved")
    if record is None:
        return UNIT_DRAFTED, UNIT_DRAFTED, False
    stage = record.get("stage") if isinstance(record, dict) else None
    if not isinstance(record, dict) or stage not in (PLANNED, DESIGNED) or not record.get("date"):
        return UNIT_DRAFTED, "its `approved` record is malformed — `classkit validate` says how", False
    on = record["date"]
    if not record.get("hash"):
        return stage, f"{stage} {on} (by hand: edits since cannot be tracked)", False
    if record["hash"] == unit_hash(course_root, directory, number, stage):
        return stage, f"{stage} {on}", False
    return stage, f"{stage} {on} — edited since", True


def unit_lines(course_root: Path, unit_map: list[dict], declared: int | None) -> list[UnitLine]:
    """The unit map with each unit's state (D-046): not started / drafted / planned / designed,
    each approved stage "edited since" when its hash no longer matches."""
    on_disk: dict[int, Path] = {}
    units = course_root / "units"
    if units.is_dir():
        for directory in sorted(units.iterdir()):
            found = _UNIT_DIR.match(directory.name)
            if directory.is_dir() and found and (directory / "unit.md").is_file():
                on_disk.setdefault(int(found.group(1)), directory)

    lines: list[UnitLine] = []
    mapped: set[int] = set()
    for entry in sorted(unit_map, key=lambda u: u.get("number") if isinstance(u.get("number"), int) else 99):
        number = entry.get("number")
        if not isinstance(number, int) or number in mapped:
            continue
        mapped.add(number)
        title = str(entry.get("title") or "—")
        if number in on_disk:
            state, detail, edited = unit_state(course_root, on_disk[number], number)
            lines.append(UnitLine(number, title, state, detail, edited))
        else:
            lines.append(UnitLine(number, title, NOT_STARTED, NOT_STARTED))
    for number, directory in sorted(on_disk.items()):
        if number not in mapped:
            state, detail, edited = unit_state(course_root, directory, number)
            if unit_map:
                detail += " — not in the unit map"
            lines.append(UnitLine(number, directory.name[3:], state, detail, edited))
    lines.sort(key=lambda line: line.number)
    return lines


def materials_lines(course_root: Path) -> list[str]:
    from .ingest import core, links  # noqa: PLC0415
    from .ingest.manifest import ManifestError, active, load  # noqa: PLC0415

    try:
        records = [r for r in load(course_root) if isinstance(r, dict)]
    except ManifestError as exc:
        return [f"the manifest cannot be read: {exc}"]
    live = active(records)
    files = core.scan(course_root)
    listed = links.read(course_root / "materials" / "source")
    _state, plan = core.reconcile(course_root, records, files, listed, local=False)
    outstanding = plan.outstanding()

    # The count leaves private files out, by design (§2.2: the same answer on every clone) — so
    # it says so, rather than disagree silently with the pre-flight's count (teacher test).
    not_private = " (private files are not counted here: `classkit doctor` reports them)"
    lines = []
    if not records:
        lines.append("none ingested yet" + ("" if outstanding else not_private))
    else:
        private = sum(1 for r in live if r.get("private"))
        instructor = sum(1 for r in live if r.get("audience") == "instructor")
        unclassified = sum(1 for r in live if not r.get("kind"))
        parts = [f"{len(live)} ingested"]
        if private:
            parts.append(f"{private} private")
        if instructor:
            parts.append(f"{instructor} instructor-only")
        if unclassified:
            parts.append(f"{unclassified} not yet classified")
        lines.append(", ".join(parts))
    if outstanding:
        shown = "; ".join(outstanding[:3]) + (f"; and {len(outstanding) - 3} more" if len(outstanding) > 3 else "")
        lines.append(f"{len(outstanding)} outstanding since the last ingest — {shown}. Run /ingest."
                     + not_private)
    elif records:
        lines.append("nothing outstanding" + not_private)
    coverage = course_root / "materials" / "coverage.md"
    if not coverage.is_file():
        lines.append("no coverage report saved yet (/ingest writes materials/coverage.md)")
        return lines
    lines.append("coverage report: materials/coverage.md")
    missing = coverage_predates(coverage, [str(r.get("id")) for r in live])
    if missing:
        newest = sorted(missing, reverse=True)
        shown = ", ".join(newest[:3]) + (f" and {len(newest) - 3} more" if len(newest) > 3 else "")
        lines.append(f"coverage report predates {shown} — re-run /ingest step 4 to refresh it")
    return lines


_COVERED = re.compile(r"Materials covered:(.*)", re.IGNORECASE)
_ID_RANGE = re.compile(r"M(\d{4})(?:\s*[–—-]\s*M?(\d{4}))?")


def covered_ids(text: str) -> set[str] | None:
    """The material ids a saved coverage report names on its "Materials covered:" line (and the
    lines continuing it, up to a blank line): `M0001–M0016, M0017`. None when there is no such line
    — then nothing can be said about what it predates."""
    lines = text.splitlines()
    for number, line in enumerate(lines):
        found = _COVERED.search(line)
        if not found:
            continue
        span = [found.group(1)]
        for following in lines[number + 1:]:
            if not following.strip() or following.lstrip().startswith("#"):
                break
            span.append(following)
        ids: set[str] = set()
        for match in _ID_RANGE.finditer(" ".join(span)):
            first = int(match.group(1))
            last = int(match.group(2)) if match.group(2) else first
            ids.update(f"M{n:04d}" for n in range(first, max(first, last) + 1))
        return ids
    return None


def coverage_predates(coverage: Path, active_ids: list[str]) -> list[str]:
    """The active materials a saved coverage report does not cover (teacher test: M0017, the
    teacher's own syllabus, arrived after the report and nothing said so)."""
    try:
        covered = covered_ids(coverage.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return []
    if covered is None:
        return []
    return [mid for mid in active_ids if mid not in covered]


def status(course_root: Path, framework_root: Path | None) -> Status:
    try:
        config = load_yaml(course_root / "course.yaml")
    except (OSError, ValueError, FrontMatterError):
        config = {}
    declared = config.get("units") if isinstance(config.get("units"), int) else None
    syllabus = syllabus_state(course_root, framework_root)

    last = ""
    log_file = course_root / log.LOG_FILE
    if log_file.is_file():
        entries = log.parse(log_file.read_text(encoding="utf-8"))
        if entries:
            last = " — ".join(part for part in (entries[-1].date, entries[-1].title) if part)

    return Status(
        course=" ".join(str(config.get(k)) for k in ("code", "title") if config.get(k)) or course_root.name,
        units_declared=declared,
        syllabus=syllabus,
        units=unit_lines(course_root, syllabus.unit_map, declared),
        materials=materials_lines(course_root),
        last_log=last,
    )


def report(found: Status) -> str:
    s = found.syllabus
    out = [f"Course status — {found.course}", ""]
    out.append(f"Syllabus      {s.state.upper()}: {s.detail}")
    if s.state not in (MISSING, UNREADABLE):
        out.append(f"              {s.outcomes} course outcome(s); unit map: "
                   + (f"{len(s.unit_map)} unit(s)" if s.unit_map else "none yet"))

    declared = f"{found.units_declared} in course.yaml" if found.units_declared else "course.yaml declares none"
    out += ["", f"Units         {declared}" + (f", {len(s.unit_map)} in the unit map" if s.unit_map else "")]
    if found.units:
        counts = [(n, label) for label in (DESIGNED, PLANNED, UNIT_DRAFTED, NOT_STARTED)
                  if (n := sum(1 for line in found.units if line.state == label))]
        edited = sum(1 for line in found.units if line.edited)
        out.append("              " + ", ".join(f"{n} {'drafted' if label == UNIT_DRAFTED else label}"
                                                for n, label in counts)
                   + (f"; {edited} edited since approval" if edited else ""))
    if found.units:
        width = max(len(line.title) for line in found.units)
        for line in found.units:
            out.append(f"  U{line.number:02d}  {line.title:<{width}}  {line.detail}")
    else:
        out.append("  no unit map yet, and no unit on disk")
    if s.unit_map and found.units_declared and len(s.unit_map) != found.units_declared:
        out.append(f"  (the unit map has {len(s.unit_map)} units; course.yaml says {found.units_declared})")

    out += ["", "Materials     " + found.materials[0]]
    out += [f"              {line}" for line in found.materials[1:]]
    if found.last_log:
        out += ["", f"Last log      {found.last_log}"]
    return "\n".join(out)
