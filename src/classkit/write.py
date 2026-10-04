"""The overwrite-safe write path (D-031b; invariant 5).

Every agent and every command writes course content through this module — directly
from Python, or from a shell via `classkit write`. It exists for one reason: the
framework must never silently destroy a teacher's authored work, and that failure is
unrecoverable, so it is the one guarantee the framework does not entrust to a prompt
(FRAMEWORK-SPEC.md §5.2 rule 2).

The guarantee is structural, not advisory: `write()` with the default arguments
*cannot* replace a file that already has content. It returns a `refused` outcome and
touches nothing. Replacing content requires the caller to pass `overwrite=True`
(`--overwrite` on the command line), which is the explicit confirmation the rule asks
for — a separate, deliberate act, not something an agent does by forgetting a check.

Two cases are deliberately *not* refusals, because nothing can be lost in either:

* the target does not exist, or exists but holds only whitespace;
* the target already holds exactly the content being written (`unchanged`), so writing
  is a no-op and re-running a command stays safe.

`scaffold.write_new()` is this module's create-only special case — scaffolding has no
confirmed-overwrite mode at all.

`remove()` is the one deletion (D-041): it deletes a file only if its content still hashes to
what the caller says it wrote — the same argument that lets ingest replace its own unedited
output. Nothing a teacher runs deletes files, so it has no command-line verb.

Replacing a file keeps its permission bits; a new file gets the usual default (0666 less the
umask), not the temporary file's private 0600 (D-041).
"""

from __future__ import annotations

import difflib
import hashlib
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

#: How much of an existing file a refusal quotes back, so the caller can show the
#: teacher what it was about to replace.
PREVIEW_LINES = 8
PREVIEW_CHARS = 600

CREATED = "created"
REPLACED = "replaced"
UNCHANGED = "unchanged"
REFUSED = "refused"
APPENDED = "appended"
REMOVED = "removed"


@dataclass
class WriteOutcome:
    """What `write()` did, or refused to do."""

    path: Path
    status: str  # created | replaced | unchanged | refused | appended | removed
    message: str = ""
    preview: str = ""

    @property
    def wrote(self) -> bool:
        """True when bytes were actually written (or, for `remove()`, the file deleted)."""
        return self.status in (CREATED, REPLACED, APPENDED, REMOVED)

    @property
    def refused(self) -> bool:
        return self.status == REFUSED

    def __str__(self) -> str:
        return f"{self.status:<9} {self.path}\n           {self.message}"


def has_content(path: Path) -> bool:
    """True if `path` holds something a teacher could lose.

    A missing file, or one holding only whitespace, holds nothing. Anything that cannot
    be read as text is assumed to hold content — refusing is the safe direction.
    """
    path = Path(path)
    if path.is_dir():
        return True
    if not path.exists():
        return False
    try:
        return path.read_text(encoding="utf-8").strip() != ""
    except (OSError, UnicodeDecodeError):
        return True


def preview_of(path: Path, *, lines: int = PREVIEW_LINES, chars: int = PREVIEW_CHARS) -> str:
    """The opening of an existing file, for a refusal message."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "(not readable as text)"
    head = "\n".join(text.splitlines()[:lines])[:chars]
    return head + ("\n…" if head != text.rstrip("\n") else "")


def write(
    path: Path | str,
    content: str,
    *,
    overwrite: bool = False,
    dry_run: bool = False,
) -> WriteOutcome:
    """Write `content` to `path`, refusing to destroy existing content.

    Never raises on a refusal: it returns an outcome whose status is ``refused`` and
    leaves the file untouched. A caller that ignores the return value therefore still
    cannot lose a teacher's work.
    """
    path = Path(path)

    if path.is_dir():
        return WriteOutcome(
            path,
            REFUSED,
            "a directory is already at this path.",
        )

    existed = path.exists()

    if existed:
        try:
            current = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            current = None
        if current == content:
            return WriteOutcome(path, UNCHANGED, "already holds exactly this content.")
        if has_content(path) and not overwrite:
            return WriteOutcome(
                path,
                REFUSED,
                "already has content. Show the teacher what is there, ask, and only "
                "then write again with overwrite=True (`--overwrite`).",
                preview=preview_of(path),
            )

    status = REPLACED if existed else CREATED
    if dry_run:
        return WriteOutcome(path, status, "would be written (dry run).")

    _atomic_write(path, content)
    return WriteOutcome(
        path,
        status,
        "written." if status == CREATED else "existing content replaced on request.",
    )


def append(path: Path | str, content: str, *, dry_run: bool = False) -> WriteOutcome:
    """Add `content` to the end of `path`. Existing bytes are never rewritten.

    Appending cannot lose anything, so it needs no confirmation — but it goes through this
    module like every other write, so "every write goes through one path" stays literally
    true (D-038; the course log is the first user). A missing or whitespace-only file is
    created through `write()`.
    """
    path = Path(path)
    if path.is_dir():
        return WriteOutcome(path, REFUSED, "a directory is already at this path.")
    if not has_content(path):
        return write(path, content, dry_run=dry_run)
    if dry_run:
        return WriteOutcome(path, APPENDED, "would be appended (dry run).")
    with path.open("a", encoding="utf-8", newline="") as stream:
        stream.write(content)
    return WriteOutcome(path, APPENDED, "appended; existing content untouched.")


def diff(path: Path | str, content: str) -> str:
    """A unified diff of exactly what `write(path, content, overwrite=True)` would change — ""
    when nothing would. Writes nothing. How a command shows the teacher a partial change (one key
    in `course.yaml`) before it writes with `--overwrite` (spec §8.6, D-040)."""
    path = Path(path)
    try:
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
    except (OSError, UnicodeDecodeError):
        current = None
    if current is None:
        return f"{path} is not readable as text; it would be replaced whole.\n"
    if current == content:
        return ""
    name = path.as_posix()
    return "".join(difflib.unified_diff(
        current.splitlines(keepends=True), content.splitlines(keepends=True),
        fromfile=f"{name} (now)" if path.exists() else "/dev/null",
        tofile=f"{name} (after --overwrite)" if path.exists() else name,
    ))


def content_hash(data: bytes) -> str:
    """`sha256:<hex>` — the form every hash in the manifest takes."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def remove(path: Path | str, expected_hash: str, *, dry_run: bool = False) -> WriteOutcome:
    """Delete `path` only if its content still hashes to `expected_hash` — proof that it is
    exactly what the caller wrote, so no teacher's edit is lost. Refuses otherwise, and touches
    nothing. A missing file is `unchanged`: there is nothing to remove (D-041)."""
    path = Path(path)
    if path.is_dir():
        return WriteOutcome(path, REFUSED, "a directory is at this path; remove() deletes files only.")
    if not path.exists():
        return WriteOutcome(path, UNCHANGED, "not there; nothing to remove.")
    try:
        actual = content_hash(path.read_bytes())
    except OSError as exc:
        return WriteOutcome(path, REFUSED, f"could not be read ({exc}); left in place.")
    if actual != expected_hash:
        return WriteOutcome(
            path, REFUSED,
            "its content is not what the caller wrote — it may hold edits — so it is left in place.",
            preview=preview_of(path),
        )
    if dry_run:
        return WriteOutcome(path, REMOVED, "would be removed (dry run).")
    path.unlink()
    return WriteOutcome(path, REMOVED, "removed: its content was exactly what was written.")


def _default_mode() -> int:
    """The permission bits a newly created file gets: 0666 less the process's umask."""
    mask = os.umask(0)
    os.umask(mask)
    return 0o666 & ~mask


def _atomic_write(path: Path, content: str) -> None:
    """Write via a temp file in the same directory, so an interrupted write cannot
    truncate the teacher's file to nothing.

    `mkstemp` creates the temporary file as 0600; it is given the replaced file's permission
    bits, or a new file's default, before it takes the target's place (D-041)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError:
        mode = _default_mode()
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".classkit-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
