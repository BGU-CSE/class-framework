"""`classkit approve syllabus` — record the teacher's approval in the file itself (D-043, §8.9).

A milestone is a teacher's act, so it is recorded, not derived — and recorded in the approved
file, never in a separate progress file that would drift from it:

    approved:
      on: 2026-10-05
      hash: "sha256:…"

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
_COMMENT = "# The teacher's approval — written by `classkit approve syllabus` (spec §8.9). Edits after it\n" \
           "# are normal: `classkit status` then says \"edited since\". Approve again to record them.\n"


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


def with_record(text: str, on: str, digest: str) -> str:
    """`text` with its `approved` block set to `{on, hash}`: an existing top-level block is
    replaced where it stands; otherwise the record is added at the end of the front matter, with a
    comment saying what it is. Nothing else in the file changes — re-parsed to make sure."""
    match = _FENCE.match(text)
    if not match:
        raise ApproveError("no YAML front matter (the file must start with a '---' line)")
    newline = "\r\n" if match.group("open").endswith("\r\n") else "\n"
    record = [f"approved:", f"  on: {on}", f'  hash: "{digest}"']
    lines = (match.group("fm") or "").splitlines()

    start = next((i for i, line in enumerate(lines) if _KEY.match(line)), None)
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines += _COMMENT.rstrip("\n").split("\n") + record
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
            after.get("approved") != {"on": on, "hash": digest}:
        raise ApproveError(
            "could not place the `approved` record without changing anything else in the front "
            "matter (an unusual layout?). Add it by hand: `approved: {on: " + on + "}`."
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
        return Approval(path, str(previous.get("on")), digest, previous, text, "")

    new_text = with_record(text, on, digest)
    approval = Approval(path, on, digest, previous, new_text, diff(path, new_text))
    if dry_run:
        return approval

    approval.outcome = write(path, new_text, overwrite=True)
    if previous:
        before = f"approved {previous.get('on')}" + ("" if previous.get("hash") else " by hand, without a hash")
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
