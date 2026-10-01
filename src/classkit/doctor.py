"""`classkit doctor` — this machine's copy of the course (D-040, spec §2.2, §8.7).

**`validate` judges the course; `doctor` judges this machine.** What is committed is the same on
every clone, so `validate` reads only that, and gives the teacher and a TA the same answer. What
legitimately differs per machine is reported here: whether the private sources and their full
texts are on this disk (and current), whether `course/.gitignore` is in effect, leftover full
texts, whether the framework's dependencies import, which optional converters are installed, and
the working mode.

Read-only, like `validate`: it writes nothing, and each line that needs action names the command
that fixes it. Exit 0 when nothing needs action, 1 when something does — so a script can gate on
it. A `note` is information (a TA's clone without the textbook is normal) and does not fail.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .ingest import core, extract, links
from .ingest.manifest import (
    PRIVATE,
    PRIVATE_TEXT_DIR,
    SOURCE_DIR,
    ManifestError,
    active,
    ingested_file,
    is_private,
    load,
    private_text_file,
    sha256_bytes,
)

OK = "ok"
ACTION = "action"
NOTE = "note"

#: The paths the scaffolded course/.gitignore must keep out of git, relative to the course.
IGNORED = ("materials/source/private/", "materials/private-text/")

#: Distribution name → the module it is imported as, where they differ.
MODULES = {"pyyaml": "yaml", "python-pptx": "pptx", "python-docx": "docx", "fonttools": "fontTools"}

#: Used only when classkit's own metadata cannot be read (run from a source tree, not installed).
FALLBACK_REQUIREMENTS = ("PyYAML", "jsonschema", "python-pptx", "python-docx", "pypdf")


@dataclass
class Line:
    status: str  # ok | action | note
    what: str
    fix: str = ""

    def __str__(self) -> str:
        mark = {OK: "ok    ", ACTION: "ACTION", NOTE: "note  "}[self.status]
        text = f"{mark}  {self.what}"
        return text + (f"\n        fix: {self.fix}" if self.fix else "")


def diagnose(course_root: Path, framework_root: Path | None = None) -> list[Line]:
    """Everything doctor checks, in the order it is printed. Reads; never writes."""
    return [
        *check_gitignore(course_root),
        *check_private_material(course_root),
        *check_dependencies(),
        *check_converters(course_root),
        *check_mode(framework_root),
    ]


# -- git and the .gitignore ----------------------------------------------------------

def _git(course_root: Path, *args: str) -> subprocess.CompletedProcess | None:
    """Run git in the course, or None when git is not installed."""
    try:
        return subprocess.run(["git", *args], cwd=course_root, capture_output=True, check=False)
    except OSError:
        return None


def _gitignore_lines(course_root: Path) -> set[str]:
    path = course_root / ".gitignore"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()
    return {line.strip().lstrip("/") for line in text.splitlines()}


def check_gitignore(course_root: Path) -> list[Line]:
    lines: list[Line] = []
    rescaffold = ("add the line to course/.gitignore — or, if the file is missing, re-run "
                  "`classkit scaffold course --code CODE --title TITLE`, which only creates "
                  "what is missing")
    inside = _git(course_root, "rev-parse", "--is-inside-work-tree")
    in_repo = inside is not None and inside.returncode == 0

    if not (course_root / ".gitignore").is_file():
        lines.append(Line(ACTION, "course/.gitignore is missing, so nothing keeps private "
                          "material out of git", rescaffold))
    else:
        missing = []
        for pattern in IGNORED:
            if in_repo:
                probe = _git(course_root, "check-ignore", "-q", pattern + "probe")
                ignored = probe is not None and probe.returncode == 0
            else:
                listed = _gitignore_lines(course_root)
                ignored = pattern in listed or pattern.rstrip("/") in listed
            if not ignored:
                missing.append(pattern)
        if missing:
            lines += [Line(ACTION, f"{pattern} is not gitignored: a file there would be committed",
                           rescaffold.replace("the line", f"`{pattern}`")) for pattern in missing]
        else:
            lines.append(Line(OK, "course/.gitignore keeps materials/source/private/ and "
                                  "materials/private-text/ out of git"))

    if inside is None:
        lines.append(Line(NOTE, "git is not installed, so `validate` cannot check whether private "
                                "files are committed (private_material_committed is skipped)"))
    elif not in_repo:
        lines.append(Line(NOTE, "the course is not in a git repository, so `validate` cannot check "
                                "whether private files are committed (private_material_committed "
                                "is skipped)"))

    source = course_root / SOURCE_DIR
    if source.is_dir():
        for entry in sorted(source.iterdir()):
            if entry.is_dir() and entry.name.lower() == PRIVATE and entry.name != PRIVATE:
                lines.append(Line(
                    ACTION,
                    f"materials/source/{entry.name}/ is treated as private, but the ignore rule "
                    "names `private/`: where git is case-sensitive, its files would be committed",
                    f"rename it to materials/source/{PRIVATE}/",
                ))
    return lines


# -- private material on this machine ---------------------------------------------------

def check_private_material(course_root: Path) -> list[Line]:
    try:
        records = [r for r in load(course_root) if isinstance(r, dict)]
    except ManifestError as exc:
        return [Line(ACTION, f"materials/manifest.yaml cannot be read: {exc}",
                     "fix the YAML by hand, or restore it from git")]
    files = core.scan(course_root)
    state, plan = core.reconcile(course_root, records, files, links.read(course_root / SOURCE_DIR))
    present = {f.rel for f in files}
    pending = {mid: why for mid, why in plan.pending}
    lines: list[Line] = []

    for group in plan.new:
        private_paths = [p for p in group.paths if is_private(p)]
        if private_paths:
            lines.append(Line(ACTION, f"materials/source/{private_paths[0]} is new and not ingested",
                              "classkit ingest"))
    for mid, old, new in plan.moved:
        if is_private(old) or is_private(new):
            lines.append(Line(ACTION, f"{mid} moved: {old} → {new}, not yet recorded", "classkit ingest"))

    private_ids: set[str] = set()
    for record in active(state):
        canonical = str(record.get("canonical") or "")
        if record.get("format") == "url" or not (record.get("private") or is_private(canonical)):
            continue
        mid = str(record.get("id"))
        private_ids.add(mid)
        name = f"{mid} ({record.get('title') or canonical})"

        if canonical not in present:
            lines.append(Line(
                NOTE,
                f"{name}: its source is not on this machine — index only here: it can be cited "
                "and validated, not read",
                f"copy it to materials/source/{canonical} and run `classkit ingest`; if it is gone "
                f"for good, `classkit material remove {mid}`",
            ))
            continue
        if mid in pending:
            lines.append(Line(ACTION, f"{name}: {pending[mid]}", "classkit ingest"))
            continue
        if record.get("status") not in core.HAS_FILE:
            lines.append(Line(OK, f"{name}: source here ({record.get('status')}: no text to keep)"))
            continue

        index = ingested_file(course_root, mid)
        if index is not None and core.front_matter_of(index).get("text") != "index":
            lines.append(Line(
                ACTION,
                f"{name}: its committed copy {index.relative_to(course_root).as_posix()} is not an "
                "index — it may hold the full text, which would be committed",
                f"classkit ingest --overwrite {mid}",
            ))
            continue
        full = private_text_file(course_root, mid)
        if full is not None and sha256_bytes(full.read_bytes()) != record.get("private_text_hash"):
            lines.append(Line(NOTE, f"{name}: source and full text here; the full text was edited "
                                    "by hand — ingest keeps the edit and asks before replacing it"))
        else:
            lines.append(Line(OK, f"{name}: source and current full text here"))

    # Full texts left behind: a material removed, merged, moved out of private/, or unknown.
    directory = course_root / PRIVATE_TEXT_DIR
    if directory.is_dir():
        known = {str(r.get("id")): r for r in records}
        for path in sorted(directory.glob("*.md")):
            match = re.match(r"^(M\d{4})(-|\.md$)", path.name)
            mid = match.group(1) if match else ""
            if mid in private_ids:
                continue
            record = known.get(mid)
            if record is None:
                why = "no material has this id"
            elif record.get("removed_at"):
                why = f"{mid} was removed"
            elif record.get("merged_into"):
                why = f"{mid} was merged into {record['merged_into']}"
            else:
                why = f"{mid} is no longer private (its full text is now the committed file)"
            lines.append(Line(ACTION, f"leftover full text materials/private-text/{path.name}: {why}",
                              f"delete it if you no longer need it: rm materials/private-text/{path.name}"))

    if not lines:
        lines.append(Line(OK, "no private material (nothing under materials/source/private/)"))
    return lines


# -- the machine ----------------------------------------------------------------------

def _requirements() -> list[str]:
    try:
        requirements = importlib.metadata.requires("classkit") or []
    except importlib.metadata.PackageNotFoundError:
        return list(FALLBACK_REQUIREMENTS)
    return [re.split(r"[\s;<>=!~\[(]", r, maxsplit=1)[0] for r in requirements if "extra ==" not in r]


def check_dependencies() -> list[Line]:
    """Each of the framework's dependencies is installed and imports — a missing optional
    piece of a dependency (F-09's fontTools) shows up here rather than as garbled text."""
    broken = []
    names = _requirements()
    for name in names:
        module = MODULES.get(name.lower(), name.lower().replace("-", "_"))
        try:
            importlib.import_module(module)
        except Exception as exc:  # ImportError, or a broken install raising anything else
            broken.append(Line(ACTION, f"{name} does not import ({type(exc).__name__}: {exc})",
                               'pip install -e ".[dev]" in the framework repo'))
    return broken or [Line(OK, f"dependencies import: {', '.join(names)}")]


def check_converters(course_root: Path) -> list[Line]:
    try:
        records = [r for r in load(course_root) if isinstance(r, dict)]
    except ManifestError:
        records = []

    def waiting(extensions) -> int:
        return sum(1 for r in active(records) if r.get("status") == extract.UNSUPPORTED
                   and Path(str(r.get("canonical") or "")).suffix.lower() in extensions)

    lines = []
    for label, found, extensions, how in (
        ("pandoc", extract.pandoc(), extract.PANDOC_EXTENSIONS, "https://pandoc.org"),
        ("LibreOffice", extract.libreoffice(), extract.LIBREOFFICE_EXTENSIONS, "https://www.libreoffice.org"),
    ):
        formats = ", ".join(sorted(extensions))
        if found:
            lines.append(Line(OK, f"{label} is installed ({formats} can be read)"))
            continue
        count = waiting(extensions)
        lines.append(Line(
            NOTE,
            f"{label} is not installed: {formats} files are recorded unsupported"
            + (f" — {count} material(s) here are waiting for it" if count else ""),
            f"optional: install it ({how}); the next `classkit ingest` retries those files",
        ))
    return lines


def check_mode(framework_root: Path | None) -> list[Line]:
    if framework_root is None:
        return [Line(NOTE, "the framework repository was not found, so the working mode is unknown")]
    from .mode import current_mode  # noqa: PLC0415

    return [Line(OK, f"working mode: {current_mode(framework_root)} (`classkit mode` to switch)")]


def report(lines: list[Line]) -> str:
    actions = sum(1 for line in lines if line.status == ACTION)
    notes = sum(1 for line in lines if line.status == NOTE)
    body = "\n".join(str(line) for line in lines)
    summary = (f"{actions} to fix, {notes} note(s)." if actions
               else f"Nothing to fix on this machine; {notes} note(s).")
    return ("classkit doctor — this machine's copy of the course (read-only; `classkit validate` "
            "checks the course itself)\n\n" + body + "\n\n" + summary)
