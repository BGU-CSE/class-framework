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
"""

from __future__ import annotations

import os
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


@dataclass
class WriteOutcome:
    """What `write()` did, or refused to do."""

    path: Path
    status: str  # created | replaced | unchanged | refused
    message: str = ""
    preview: str = ""

    @property
    def wrote(self) -> bool:
        """True when bytes were actually written."""
        return self.status in (CREATED, REPLACED)

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


def _atomic_write(path: Path, content: str) -> None:
    """Write via a temp file in the same directory, so an interrupted write cannot
    truncate the teacher's file to nothing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".classkit-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
