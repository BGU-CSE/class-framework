"""Which hat a Claude Code session in this repo wears: teacher, or framework developer.

A course repo is a *clone* of the framework (D-009), so anything the framework ships
also lands in every teacher's repo — a committed marker file could not tell the two
apart. The discriminator has to be something that never clones, which is why the marker
is **gitignored**: `dev/.developer` exists only where a developer put it.

That makes the ignore rule load-bearing rather than cosmetic. If the marker were ever
committed, every teacher's clone would start in framework-developer mode. So switching
modes goes through here, where the rule is verified before the file is created, instead
of through a remembered `touch`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

MARKER = Path("dev/.developer")

TEACHER = "teacher"
DEVELOPER = "framework-developer"


@dataclass
class ModeChange:
    mode: str
    changed: bool
    message: str


def marker_path(framework_root: Path) -> Path:
    return framework_root / MARKER


def current_mode(framework_root: Path) -> str:
    return DEVELOPER if marker_path(framework_root).exists() else TEACHER


def is_ignored(framework_root: Path, path: Path) -> bool | None:
    """Is `path` covered by a gitignore rule?

    Returns None when the question does not apply — git missing, or not a repository —
    in which case there is no commit to protect against either.
    """
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=framework_root,
            capture_output=True,
            check=False,
        )
    except (OSError, FileNotFoundError):
        return None

    # 0 = ignored, 1 = not ignored, 128 = not a git repository.
    if result.returncode == 128:
        return None
    return result.returncode == 0


class UnsafeMarker(RuntimeError):
    """The marker would not be ignored, so creating it risks committing it."""


def set_mode(framework_root: Path, mode: str) -> ModeChange:
    marker = marker_path(framework_root)
    before = current_mode(framework_root)

    if mode == TEACHER:
        if marker.exists():
            marker.unlink()
            return ModeChange(TEACHER, True, "removed dev/.developer")
        return ModeChange(TEACHER, False, "already in teacher mode")

    if before == DEVELOPER:
        return ModeChange(DEVELOPER, False, "already in framework-developer mode")

    # Check the ignore rule BEFORE creating the file, so an unsafe repo never has the
    # marker in it even briefly.
    ignored = is_ignored(framework_root, MARKER)
    if ignored is False:
        raise UnsafeMarker(
            f"{MARKER} is not covered by a gitignore rule, so it could be committed — "
            "and a committed marker would put every teacher's clone into "
            "framework-developer mode. Add `dev/.developer` to .gitignore (and make sure "
            ".gitignore itself is tracked) before switching."
        )

    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        "# This file is the framework-developer marker. It is gitignored on purpose:\n"
        "# it must never reach a teacher's clone. Remove it with `classkit mode teacher`.\n",
        encoding="utf-8",
    )
    note = "" if ignored else "  (could not verify the gitignore rule — no git repository here)"
    return ModeChange(DEVELOPER, True, f"created dev/.developer{note}")
