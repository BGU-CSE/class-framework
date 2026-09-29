"""Locating and loading a course tree.

Layout, as created by `classkit scaffold course`:

    course/
      course.yaml
      LOG.md                the course log (D-036) — not loaded here; see log.py
      syllabus/syllabus.md
      units/
        01-slug/
          unit.md
          sessions/01.md 02.md ...
          in-class.md
      assessments/
        items/ quizzes/ homework/ exams/
      materials/
      policies/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .frontmatter import load, load_yaml


@dataclass
class Doc:
    """One parsed Markdown document: its front matter plus its prose body."""

    path: Path
    data: dict
    body: str = ""

    @property
    def id(self) -> str:
        return str(self.data.get("id", f"<no id: {self.path.name}>"))

    @property
    def accepted(self) -> list[dict]:
        """The teacher's accepted exceptions for this file (D-037): ``[{rule, reason}]``.

        Malformed entries are dropped here and reported by the schema layer instead.
        """
        entries = self.data.get("accepted") or []
        if not isinstance(entries, list):
            return []
        return [e for e in entries if isinstance(e, dict) and isinstance(e.get("rule"), str)]


@dataclass
class Unit:
    doc: Doc
    directory: Path
    sessions: list[Doc] = field(default_factory=list)
    in_class: Doc | None = None

    @property
    def id(self) -> str:
        return self.doc.id

    @property
    def objectives(self) -> list[dict]:
        return self.doc.data.get("objectives") or []

    def goals(self) -> list[dict]:
        """Every goal from every study session in this unit, in order."""
        return [g for s in self.sessions for g in (s.data.get("goals") or [])]


@dataclass
class Course:
    root: Path
    config: dict
    methodology: dict
    time_constants: dict
    #: `syllabus/syllabus.md` — the course-level top layer (D-021). `None` when the file
    #: does not exist: the syllabus is scaffolded, but a course tree can be edited by hand
    #: and the loader reports what is there rather than assuming.
    syllabus: Doc | None = None
    units: list[Unit] = field(default_factory=list)
    items: list[Doc] = field(default_factory=list)

    def documents(self) -> list[Doc]:
        """Every front-matter document in the course — the files that may carry `accepted:`."""
        docs: list[Doc] = [self.syllabus] if self.syllabus is not None else []
        for unit in self.units:
            docs.append(unit.doc)
            docs.extend(unit.sessions)
            if unit.in_class is not None:
                docs.append(unit.in_class)
        docs.extend(self.items)
        return docs

    @property
    def outcomes(self) -> list[dict]:
        """The Course Outcomes declared in the syllabus, in order."""
        if self.syllabus is None:
            return []
        return [o for o in (self.syllabus.data.get("outcomes") or []) if isinstance(o, dict)]


class LayoutError(Exception):
    """The framework or course tree is not where it was expected to be."""


def find_framework_root(start: Path | None = None) -> Path:
    """Walk upward looking for the framework repo (it holds schemas/ and methodologies/)."""
    candidates = []
    if start is not None:
        candidates.append(Path(start).resolve())
    candidates.append(Path.cwd().resolve())
    candidates.append(Path(__file__).resolve().parents[2])

    for candidate in candidates:
        for directory in [candidate, *candidate.parents]:
            if (directory / "schemas").is_dir() and (directory / "methodologies").is_dir():
                return directory
    raise LayoutError(
        "cannot find the framework root (a directory containing schemas/ and methodologies/)"
    )


def find_course_root(start: Path | None = None) -> Path:
    """Walk upward looking for the course tree (the directory holding course.yaml)."""
    base = Path(start).resolve() if start else Path.cwd().resolve()

    if (base / "course.yaml").is_file():
        return base
    for directory in [base, *base.parents]:
        if (directory / "course" / "course.yaml").is_file():
            return directory / "course"
    raise LayoutError(
        "cannot find a course (no course/course.yaml found here or above). "
        "Run `classkit scaffold course` first, or pass an explicit path."
    )


def load_methodology(framework_root: Path, name: str) -> dict:
    path = framework_root / "methodologies" / f"{name}.yaml"
    if not path.is_file():
        available = sorted(p.stem for p in (framework_root / "methodologies").glob("*.yaml"))
        raise LayoutError(
            f"unknown methodology {name!r}. Available: {', '.join(available) or '(none)'}"
        )
    return load_yaml(path)


def load_time_constants(framework_root: Path, overrides: dict | None) -> dict:
    constants = load_yaml(framework_root / "defaults" / "time-constants.yaml")
    constants.update(overrides or {})
    return constants


def normalize_rules(block: dict) -> None:
    """Read a bare ``off`` in a ``rules:`` block as the severity it was meant to be.

    YAML 1.1 — which PyYAML implements — parses an unquoted ``off`` (and ``no``) as the
    boolean ``False``. ``rules: {session_count: off}`` is exactly what the spec tells a
    teacher to write, so it must mean ``"off"``, not fail the schema.
    """
    rules = block.get("rules")
    if isinstance(rules, dict):
        block["rules"] = {code: ("off" if level is False else level) for code, level in rules.items()}


def load_course(course_root: Path, framework_root: Path) -> Course:
    config = load_yaml(course_root / "course.yaml")
    methodology = load_methodology(framework_root, config.get("methodology", "question-driven-25"))
    normalize_rules(config)
    normalize_rules(methodology)
    constants = load_time_constants(framework_root, config.get("time_constants"))

    course = Course(
        root=course_root,
        config=config,
        methodology=methodology,
        time_constants=constants,
    )

    syllabus_file = course_root / "syllabus" / "syllabus.md"
    if syllabus_file.is_file():
        s_data, s_body = load(syllabus_file)
        course.syllabus = Doc(syllabus_file, s_data, s_body)

    units_dir = course_root / "units"
    if units_dir.is_dir():
        for unit_dir in sorted(p for p in units_dir.iterdir() if p.is_dir()):
            unit_file = unit_dir / "unit.md"
            if not unit_file.is_file():
                continue
            data, body = load(unit_file)
            unit = Unit(doc=Doc(unit_file, data, body), directory=unit_dir)

            sessions_dir = unit_dir / "sessions"
            if sessions_dir.is_dir():
                for session_file in sorted(sessions_dir.glob("*.md")):
                    s_data, s_body = load(session_file)
                    unit.sessions.append(Doc(session_file, s_data, s_body))

            in_class_file = unit_dir / "in-class.md"
            if in_class_file.is_file():
                ic_data, ic_body = load(in_class_file)
                unit.in_class = Doc(in_class_file, ic_data, ic_body)

            course.units.append(unit)

    items_dir = course_root / "assessments" / "items"
    if items_dir.is_dir():
        for item_file in sorted(items_dir.glob("*.md")):
            i_data, i_body = load(item_file)
            course.items.append(Doc(item_file, i_data, i_body))

    return course
