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
)

OK = "ok"
ACTION = "action"
NOTE = "note"

#: The paths the scaffolded course/.gitignore must keep out of git, relative to the course.
IGNORED = ("materials/source/private/", "materials/private-text/")

#: A run of this many consecutive words, shared by a committed course file and a private full
#: text, counts as copied (D-042). Long enough that a definition's usual phrasing ("a binary tree
#: in which every node …") does not trigger it; short enough to catch a copied sentence.
QUOTE_WORDS = 12

#: Course files that are not checked for quotation: the teacher's sources, derived ingest output
#: (the index's labels come from the book by design), and the local full texts themselves.
NOT_SCANNED = ("materials/source", "materials/ingested", "materials/private-text")

#: Distribution name → the module it is imported as, where they differ.
MODULES = {"pyyaml": "yaml", "python-pptx": "pptx", "python-docx": "docx", "fonttools": "fontTools"}

#: Used only when classkit's own metadata cannot be read (run from a source tree, not installed).
FALLBACK_REQUIREMENTS = ("PyYAML", "jsonschema", "python-pptx", "python-docx", "pypdf", "fonttools")


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
        *check_quotation(course_root),
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


def _gitignore_travels(course_root: Path) -> list[Line]:
    """The rules protect every clone only if `course/.gitignore` is itself committed. A global
    excludes file that ignores `.gitignore` (it happens) keeps it on this machine alone: here
    everything looks fine, and the next clone has no protection at all."""
    rule = _git(course_root, "check-ignore", "-v", ".gitignore")
    if rule is not None and rule.returncode == 0:
        source = rule.stdout.decode("utf-8", "replace").split("\t")[0].strip()
        return [Line(ACTION, f"course/.gitignore is itself ignored by git ({source}), so it is never "
                             "committed: this machine is protected, but no clone of the course is",
                     "git add -f course/.gitignore, and commit it")]
    tracked = _git(course_root, "ls-files", "--error-unmatch", ".gitignore")
    if tracked is not None and tracked.returncode != 0:
        return [Line(NOTE, "course/.gitignore is not committed yet — commit it, so every clone of "
                           "the course keeps private material out of git too")]
    return []


def check_gitignore(course_root: Path) -> list[Line]:
    lines: list[Line] = []
    inside = _git(course_root, "rev-parse", "--is-inside-work-tree")
    in_repo = inside is not None and inside.returncode == 0

    if not (course_root / ".gitignore").is_file():
        lines.append(Line(ACTION, "course/.gitignore is missing, so nothing keeps private "
                          "material out of git",
                          "re-run `classkit scaffold course --code CODE --title TITLE` — it only "
                          "creates what is missing"))
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
                           f"add the line `{pattern}` to course/.gitignore") for pattern in missing]
        else:
            lines.append(Line(OK, "course/.gitignore keeps materials/source/private/ and "
                                  "materials/private-text/ out of git"))
        if in_repo:
            lines += _gitignore_travels(course_root)

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

    new_private = [next(p for p in group.paths if is_private(p))
                   for group in plan.new if any(is_private(p) for p in group.paths)]
    if len(new_private) == 1:
        lines.append(Line(ACTION, f"materials/source/{new_private[0]} is new and not ingested",
                          "classkit ingest"))
    elif new_private:
        # One line, not one per file: on a first run they would bury the ACTION that matters
        # (teacher test: seven of them above a `.gitignore` problem), and one command fixes all.
        lines.append(Line(ACTION, f"{len(new_private)} private files not ingested yet "
                                  f"(e.g. materials/source/{new_private[0]})", "classkit ingest"))
    for mid, old, new in plan.moved:
        if is_private(old) or is_private(new):
            lines.append(Line(ACTION, f"{mid} moved: {old} → {new}, not yet recorded", "classkit ingest"))

    private_ids: set[str] = set()
    for record in active(state):
        canonical = str(record.get("canonical") or "")
        copies = [p for p in record.get("sources") or [] if is_private(p) and p != canonical]
        if copies and not is_private(canonical):
            lines.append(Line(
                ACTION,
                f"{record.get('id')} ({record.get('title') or canonical}): materials/source/{copies[0]} is "
                f"an identical copy of materials/source/{canonical}, which is not private — so the "
                "material is not private, and the copy outside private/ is committed",
                f"if it must not be committed, delete materials/source/{canonical} (keep the copy "
                "in private/) and run `classkit ingest`",
            ))
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
        here_hash = (record.get("source_hashes") or {}).get(canonical)
        if here_hash and record.get("source_hash") and here_hash != record["source_hash"]:
            # Two machines, two copies (D-041): from inside a checkout "I updated the book" and
            # "my copy is older" look the same, so this is information, not an instruction.
            lines.append(Line(
                NOTE,
                f"{name}: this machine's copy of the source differs from the one the committed "
                "index was built from (another printing or version?). Ingesting here rebuilds the "
                "committed index from this copy — the last machine to ingest wins",
                "if this copy is the current one, `classkit ingest`; if not, replace it with the "
                "current one first",
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
        if full is not None and not core.full_text_unedited(full, record):
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
    if not (course_root / SOURCE_DIR / PRIVATE).is_dir():
        # git does not carry an ignored, empty folder, so a clone (a TA's) starts without it.
        lines.append(Line(NOTE, "materials/source/private/ does not exist on this machine — create it "
                                "for private material (a published book, a solutions manual)",
                          "mkdir course/materials/source/private"))
    return lines


# -- the machine ----------------------------------------------------------------------

# -- quotation of private material -----------------------------------------------------

_WORD = re.compile(r"\w+", re.UNICODE)
_ANCHOR = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def _words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def _shingles(course_root: Path, records: list[dict]) -> dict[int, tuple[str, str]]:
    """Every QUOTE_WORDS-word run of every private full text on this machine → (id, anchor)."""
    index: dict[int, tuple[str, str]] = {}
    for record in records:
        path = private_text_file(course_root, str(record.get("id")))
        if path is None:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # Section by section, so a match can name its anchor (`page-63`).
        bounds = [(m.start(), m.group(1)) for m in _ANCHOR.finditer(text)]
        sections = [(0, "")] + bounds
        for i, (start, heading) in enumerate(sections):
            end = sections[i + 1][0] if i + 1 < len(sections) else len(text)
            anchor = extract.slug(heading) if heading else ""
            words = _words(text[start:end])
            for k in range(len(words) - QUOTE_WORDS + 1):
                index.setdefault(hash(tuple(words[k:k + QUOTE_WORDS])), (record["id"], anchor))
    return index


def _scanned_files(course_root: Path) -> list[Path]:
    files = []
    for path in sorted(course_root.rglob("*.md")):
        rel = path.relative_to(course_root).as_posix()
        if any(rel == p or rel.startswith(p + "/") for p in NOT_SCANNED):
            continue
        if any(part.startswith(".") for part in path.relative_to(course_root).parts):
            continue
        files.append(path)
    return files


def check_quotation(course_root: Path) -> list[Line]:
    """D-042: no committed course file may copy text from a private material. Only a machine
    that has the full texts can check it — which is why it is here and not in `validate`."""
    try:
        records = [r for r in load(course_root) if isinstance(r, dict)]
    except ManifestError:
        return []  # check_private_material already reports an unreadable manifest
    private_records = [r for r in active(records) if r.get(PRIVATE)]
    if not private_records:
        return []
    index = _shingles(course_root, private_records)
    if not index:
        return [Line(OK, "quotation check skipped: no private full text on this machine to "
                         "compare against")]

    lines: list[Line] = []
    for path in _scanned_files(course_root):
        words = _words(path.read_text(encoding="utf-8", errors="replace"))
        # Longest run per material: consecutive matching windows extend one run.
        runs: dict[str, tuple[int, str]] = {}
        run_len, run_source = 0, None
        for k in range(len(words) - QUOTE_WORDS + 1):
            hit = index.get(hash(tuple(words[k:k + QUOTE_WORDS])))
            if hit is not None and run_source is not None and hit[0] == run_source[0]:
                run_len += 1
            elif hit is not None:
                run_len, run_source = 1, hit
            else:
                run_len, run_source = 0, None
            if run_source is not None:
                length = run_len + QUOTE_WORDS - 1
                if length > runs.get(run_source[0], (0, ""))[0]:
                    runs[run_source[0]] = (length, run_source[1])
        rel = path.relative_to(course_root.parent).as_posix()
        for mid, (length, anchor) in sorted(runs.items()):
            where = f"{mid}#{anchor}" if anchor else mid
            lines.append(Line(
                ACTION,
                f"{rel} copies {length} consecutive words of private material {where} — "
                "committed, it puts the book's text in git",
                f"rewrite it in your own words and cite the place: `{where}`",
            ))
    # Say what was checked: the ingested copies (NOT_SCANNED) are not (teacher test — a deck
    # adapted from the publisher's notes shares their text, and "no course file" overstated it).
    return lines or [Line(OK, "no committed course file copies text from a private material "
                              "(the ingested copies in materials/ingested/ are not checked)")]


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
