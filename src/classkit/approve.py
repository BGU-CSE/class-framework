"""`classkit approve syllabus` and `classkit approve unit N` — record the teacher's approval in the
file itself (D-043, D-046, §8.9).

A milestone is a teacher's act, so it is recorded, not derived — and recorded in the approved
file, never in a separate progress file that would drift from it:

    approved:
      date: 2026-10-05
      hash: "sha256:…"

A unit's record also carries its `stage` (D-046): `planned` — the objectives were approved, the
hash is over `unit.md`; `designed` — the whole unit was approved, the hash is over `unit.md`, its
sessions, its `in-class.md` and its entry-quiz items, each hashed as below and combined in a fixed
order, so editing any part of the unit shows "designed — edited since".

The hash is of the syllabus *without* its own `approved` block, so approving does not change what
it certifies, and `classkit status` can later say "approved 2026-10-05 — edited since" instead of
un-approving behind the teacher's back. It is taken over the **parsed** front matter (canonical
JSON, keys sorted) plus the body: a YAML comment, a key's order or a quoting style is not an edit
anyone reads, and the record can sit anywhere in the front matter, in any style, written by hand.

The record is written by a *textual* edit of the front matter — only the `approved` block's lines
change, so the teacher's comments survive — and then checked by re-parsing: if anything other than
the record would come out different, nothing is written. The write goes through the write path
(§8.6) with `overwrite=True`: the teacher's "approve" is the explicit confirmation, and `--diff`
shows the change first without writing.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import log
from .frontmatter import FrontMatterError, parse
from .model import normalize_approved
from .write import WriteOutcome, diff, write

SYLLABUS = Path("syllabus") / "syllabus.md"

_FENCE = re.compile(r"\A(?P<open>---[ \t]*\r?\n)(?P<fm>.*?\r?\n)?(?P<close>---[ \t]*(?:\r?\n|\Z))", re.S)
_KEY = re.compile(r"^approved\s*:")
_COMMENT = "# The teacher's approval — written by `classkit approve {what}` (spec §8.9). Edits after it\n" \
           "# are normal: `classkit status` then says \"edited since\". Approve again to record them.\n"

#: A unit's milestones, in order (D-046, spec §8.9).
STAGES = ("planned", "designed")


class ApproveError(ValueError):
    """The file cannot be approved: it is missing, its front matter does not parse, or the record
    could not be placed without changing anything else."""


def content_hash(data: dict, body: str) -> str:
    """`sha256:<hex>` of a document without its `approved` block: the front matter's values in
    canonical form, then the body. Comments and key order are not part of it."""
    values = {k: v for k, v in data.items() if k != "approved"}
    canonical = json.dumps(values, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(f"{canonical}\n---\n{body}".encode("utf-8")).hexdigest()


def read(text: str) -> tuple[dict, str]:
    """Front matter (with `approved` normalised) and body, or ApproveError."""
    try:
        data, body = parse(text)
    except FrontMatterError as exc:
        raise ApproveError(str(exc)) from exc
    normalize_approved(data)
    return data, body


def with_record(text: str, on: str, digest: str, *, stage: str | None = None,
                what: str = "syllabus") -> str:
    """`text` with its `approved` block set to `{date, stage?, hash}`: an existing top-level block
    is replaced where it stands; otherwise the record is added at the end of the front matter, with
    a comment saying what it is. Nothing else in the file changes — re-parsed to make sure."""
    match = _FENCE.match(text)
    if not match:
        raise ApproveError("no YAML front matter (the file must start with a '---' line)")
    newline = "\r\n" if match.group("open").endswith("\r\n") else "\n"
    expected = {"date": on, **({"stage": stage} if stage else {}), "hash": digest}
    record = ["approved:", f"  date: {on}", *([f"  stage: {stage}"] if stage else []), f'  hash: "{digest}"']
    lines = (match.group("fm") or "").splitlines()

    start = next((i for i, line in enumerate(lines) if _KEY.match(line)), None)
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        # The scaffolded templates already explain the record in an `# APPROVAL` comment.
        explained = any(line.startswith("# APPROVAL") for line in lines)
        lines += ([] if explained else _COMMENT.format(what=what).rstrip("\n").split("\n")) + record
    else:
        end = start + 1
        while end < len(lines):
            line = lines[end]
            if line[:1] in (" ", "\t"):
                end += 1
            elif not line.strip() and any(rest[:1] in (" ", "\t") for rest in lines[end + 1:end + 2]):
                end += 1  # a blank line inside the block
            else:
                break
        lines[start:end] = record

    front = newline.join(lines) + newline
    result = match.group("open") + front + match.group("close") + text[match.end():]

    before, body = read(text)
    after, new_body = read(result)
    if new_body != body or {k: v for k, v in after.items() if k != "approved"} != \
            {k: v for k, v in before.items() if k != "approved"} or \
            after.get("approved") != expected:
        by_hand = f"{{date: {on}" + (f", stage: {stage}" if stage else "") + "}"
        raise ApproveError(
            "could not place the `approved` record without changing anything else in the front "
            f"matter (an unusual layout?). Add it by hand: `approved: {by_hand}`."
        )
    return result


@dataclass
class Approval:
    path: Path
    on: str
    hash: str
    #: the record that was there before — None if the syllabus had never been approved
    previous: dict | None
    #: the file's new text; equal to the old when there was nothing to record
    text: str
    changes: str
    outcome: WriteOutcome | None = None
    #: a unit's stage (D-046); None for the syllabus
    stage: str | None = None

    @property
    def already(self) -> bool:
        """Already approved with exactly this content — nothing to record."""
        return self.changes == ""


def approve_syllabus(course_root: Path, *, on: str | None = None, dry_run: bool = False,
                     why: str = "") -> Approval:
    """Record the teacher's approval of `syllabus/syllabus.md` and log it.

    Approving content that is already approved with the same hash records nothing (and logs
    nothing); approving after edits, or over a hand-written record without a hash, records today's
    date and the new hash. `dry_run` only computes the change (`--diff`)."""
    path = course_root / SYLLABUS
    if not path.is_file():
        raise ApproveError(f"{SYLLABUS} does not exist — there is nothing to approve. Run /plan-syllabus.")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ApproveError(f"{path}: cannot be read: {exc}") from exc
    data, body = read(text)
    digest = content_hash(data, body)
    previous = data.get("approved") if isinstance(data.get("approved"), dict) else None
    on = on or datetime.date.today().isoformat()

    if previous and previous.get("hash") == digest:
        return Approval(path, str(previous.get("date")), digest, previous, text, "")

    new_text = with_record(text, on, digest)
    approval = Approval(path, on, digest, previous, new_text, diff(path, new_text))
    if dry_run:
        return approval

    approval.outcome = write(path, new_text, overwrite=True)
    if previous:
        before = f"approved {previous.get('date')}" + ("" if previous.get("hash") else " by hand, without a hash")
        changed = f"syllabus re-approved ({digest[:15]}…); was {before}"
    else:
        changed = f"syllabus approved ({digest[:15]}…)"
    log.append(course_root, log.Entry(
        title="classkit approve syllabus",
        changed=changed,
        why=why or "the teacher approved it",
        files=[SYLLABUS.as_posix()],
        date=on,
    ))
    return approval


# -- units (D-046) ----------------------------------------------------------------

def _file_digest(path: Path) -> str:
    """One file's part of a unit's hash: its parsed front matter (without `approved`) and body, as
    for the syllabus — or, if its front matter does not parse, its raw text, so a broken file still
    counts as a change rather than stopping the overview (`classkit validate` reports it)."""
    text = path.read_text(encoding="utf-8")
    try:
        data, body = read(text)
    except ApproveError:
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    return content_hash(data, body)


def _is_entry_quiz_item(path: Path) -> bool:
    try:
        data, _body = read(path.read_text(encoding="utf-8"))
    except (ApproveError, OSError, UnicodeDecodeError):
        return True  # cannot tell — counted, so an edit to it is not silently missed
    usage = data.get("usage")
    return "in-class-quiz" in usage if isinstance(usage, list) else usage == "in-class-quiz"


def unit_files(course_root: Path, directory: Path, number: int) -> list[tuple[str, Path]]:
    """The files a *designed* unit's hash covers, in their fixed order, each with the stable name
    it is hashed under: `unit.md`, `sessions/NN.md` in order, `in-class.md`, then the unit's
    entry-quiz items (`usage: in-class-quiz`) by id. Names are relative to the unit — not its
    directory's slug, which may be renamed by hand without being an edit (D-031f)."""
    files = [("unit.md", directory / "unit.md")]
    sessions = directory / "sessions"
    if sessions.is_dir():
        files += [(f"sessions/{p.name}", p) for p in sorted(sessions.glob("*.md"))]
    if (directory / "in-class.md").is_file():
        files.append(("in-class.md", directory / "in-class.md"))
    items = course_root / "assessments" / "items"
    if items.is_dir():
        files += [(f"items/{p.name}", p) for p in sorted(items.glob(f"U{number:02d}-I*.md"))
                  if _is_entry_quiz_item(p)]
    return files


def unit_hash(course_root: Path, directory: Path, number: int, stage: str) -> str:
    """`planned`: the hash of `unit.md` without its record. `designed`: the hash of the whole unit
    — every file's own hash, named and combined in the fixed order of `unit_files`."""
    if stage == "planned":
        return _file_digest(directory / "unit.md")
    combined = "".join(f"{name} {_file_digest(path)}\n"
                       for name, path in unit_files(course_root, directory, number))
    return "sha256:" + hashlib.sha256(combined.encode("utf-8")).hexdigest()


def find_unit(course_root: Path, number: int) -> Path:
    """The unit's directory, found by its `NN-` prefix (D-031f), or ApproveError."""
    units = course_root / "units"
    if units.is_dir():
        for directory in sorted(units.iterdir()):
            if directory.is_dir() and directory.name.startswith(f"{number:02d}-") \
                    and (directory / "unit.md").is_file():
                return directory
    raise ApproveError(f"unit {number} has no units/{number:02d}-…/unit.md — there is nothing to "
                       f"approve. Run /plan-units {number}.")


def next_stage(record: dict | None, planned_hash: str) -> str:
    """The stage `approve unit N` records when none is given — the next one (§8.9): `planned` for a
    unit never approved; `designed` once its plan is approved and unchanged, or if it was designed
    already. A plan edited since its approval is re-approved as `planned`: the edit is to the plan."""
    if not isinstance(record, dict):
        return "planned"
    if record.get("stage") == "designed":
        return "designed"
    if record.get("stage") == "planned" and record.get("hash") == planned_hash:
        return "designed"
    return "planned"


def approve_unit(course_root: Path, number: int, *, stage: str | None = None, on: str | None = None,
                 dry_run: bool = False, why: str = "") -> Approval:
    """Record the teacher's approval of unit `number` at `stage` in its `unit.md`, and log it.

    As for the syllabus: approving what is already approved at the same stage with the same hash
    records nothing; `dry_run` only computes the change (`--diff`). Nothing is blocked by state —
    a unit may be approved as designed without having been planned, or re-planned after it was
    designed (§8.9)."""
    if stage is not None and stage not in STAGES:
        raise ApproveError(f"the stage is one of {', '.join(STAGES)}, not {stage!r}")
    directory = find_unit(course_root, number)
    path = directory / "unit.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ApproveError(f"{path}: cannot be read: {exc}") from exc
    data, _body = read(text)
    previous = data.get("approved") if isinstance(data.get("approved"), dict) else None
    stage = stage or next_stage(previous, unit_hash(course_root, directory, number, "planned"))
    digest = unit_hash(course_root, directory, number, stage)
    on = on or datetime.date.today().isoformat()

    if previous and previous.get("stage") == stage and previous.get("hash") == digest:
        return Approval(path, str(previous.get("date")), digest, previous, text, "", stage=stage)

    new_text = with_record(text, on, digest, stage=stage, what=f"unit {number}")
    approval = Approval(path, on, digest, previous, new_text, diff(path, new_text), stage=stage)
    if dry_run:
        return approval

    approval.outcome = write(path, new_text, overwrite=True)
    unit_id = f"U{number:02d}"
    changed = f"{unit_id} approved as {stage} ({digest[:15]}…)"
    if previous:
        was = f"{previous.get('stage') or 'approved'} {previous.get('date')}"
        changed += f"; was {was}" + ("" if previous.get("hash") else " by hand, without a hash")
    relative = path.relative_to(course_root).as_posix()
    log.append(course_root, log.Entry(
        title=f"classkit approve unit {number}",
        changed=changed,
        why=why or "the teacher approved it",
        files=[relative] if stage == "planned" else [directory.relative_to(course_root).as_posix() + "/",
                                                     *(f"assessments/{name}" for name, _p in
                                                       unit_files(course_root, directory, number)
                                                       if name.startswith("items/"))],
        date=on,
    ))
    return approval
