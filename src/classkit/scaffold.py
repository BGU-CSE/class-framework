"""Scaffolding — create content skeletons in a course repo from framework templates.

Two properties, both decided deliberately (Q-008):

* **Create-only.** Nothing is ever overwritten. Re-running `scaffold unit 5` after you
  have edited unit 5 is safe: you get whatever files are missing and keep everything you
  wrote. Skipped files are reported, never silently passed over.
* **Templates are copied, not shipped.** The framework never places files in the course
  tree itself (D-009), so the course tree exists only because scaffold built it (D-015).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import load_methodology, load_yaml
from .write import write

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


@dataclass
class Result:
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)

    def merge(self, other: Result) -> Result:
        self.created.extend(other.created)
        self.skipped.extend(other.skipped)
        return self


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def render(template: str, values: dict) -> str:
    return _PLACEHOLDER.sub(lambda m: str(values.get(m.group(1), m.group(0))), template)


def write_new(path: Path, content: str, result: Result) -> None:
    """Write `content` to `path` unless something is already there.

    The create-only special case of the overwrite-safe write path (`write.write`):
    scaffolding never passes `overwrite`, so it has no way to replace a teacher's file
    at all. A path that already holds content — or already holds exactly this content —
    is recorded as skipped and reported, never silently passed over.
    """
    outcome = write(path, content, overwrite=False)
    (result.created if outcome.wrote else result.skipped).append(path)


def _template(framework_root: Path, *parts: str) -> str:
    return (framework_root.joinpath("templates", *parts)).read_text(encoding="utf-8")


def _methodology_values(methodology: dict) -> dict:
    home = methodology.get("home_study", {})
    in_class = methodology.get("in_class", {})
    objectives = (methodology.get("unit") or {}).get("objectives", {})
    goals = home.get("goals_per_session", {})
    return {
        "sessions_per_unit": home.get("sessions_per_unit", 4),
        "session_minutes": home.get("session_minutes", 25),
        "home_minutes": home.get("total_minutes", 100),
        "in_class_minutes": in_class.get("minutes", 50),
        "objectives_min": objectives.get("min", 2),
        "objectives_max": objectives.get("max", 4),
        "goals_min": goals.get("min", 3),
        "goals_max": goals.get("max", 5),
    }


# -- course ----------------------------------------------------------------

COURSE_DIRECTORIES = [
    "syllabus",
    "units",
    "assessments/items",
    "assessments/quizzes",
    "assessments/homework",
    "assessments/exams",
    "materials",
    "policies",
]

# `materials/source/` is where the teacher drops their existing course materials. It is the
# primary input to /ingest and the curriculum-architect, so it ships with a README explaining
# what belongs there — an empty unexplained directory gets ignored.
SOURCE_README = "materials/source/README.md"


def scaffold_course(
    course_root: Path,
    framework_root: Path,
    *,
    code: str,
    title: str,
    institution: str,
    instructor: str,
    units: int,
    methodology: str,
) -> Result:
    result = Result()

    for directory in COURSE_DIRECTORIES:
        write_new(course_root / directory / ".gitkeep", "", result)

    write_new(
        course_root / SOURCE_README,
        _template(framework_root, "course", "materials-source-README.md"),
        result,
    )

    write_new(
        course_root / "course.yaml",
        render(
            _template(framework_root, "course", "course.yaml"),
            {
                "code": code,
                "title": title,
                "institution": institution,
                "instructor": instructor,
                "units": units,
                "methodology": methodology,
            },
        ),
        result,
    )
    return result


# -- unit ------------------------------------------------------------------

def find_unit_directory(course_root: Path, number: int) -> Path | None:
    units_dir = course_root / "units"
    if not units_dir.is_dir():
        return None
    for candidate in sorted(units_dir.iterdir()):
        if candidate.is_dir() and candidate.name.startswith(f"{number:02d}-"):
            return candidate
    return None


def scaffold_unit(
    course_root: Path,
    framework_root: Path,
    number: int,
    title: str | None = None,
) -> Result:
    methodology = _course_methodology(course_root, framework_root)
    values = _methodology_values(methodology)

    unit_id = f"U{number:02d}"
    unit_title = title or f"Unit {number}"

    directory = find_unit_directory(course_root, number)
    if directory is None:
        directory = course_root / "units" / f"{number:02d}-{slugify(unit_title)}"

    values |= {"unit_id": unit_id, "unit_number": number, "unit_title": unit_title}

    result = Result()
    write_new(
        directory / "unit.md",
        render(_template(framework_root, "unit", "unit.md"), values),
        result,
    )

    for index in range(1, int(values["sessions_per_unit"]) + 1):
        result.merge(
            scaffold_session(course_root, framework_root, unit_id, index, directory=directory)
        )

    write_new(
        directory / "in-class.md",
        render(_template(framework_root, "unit", "in-class.md"), values),
        result,
    )
    return result


# -- study session ---------------------------------------------------------

def scaffold_session(
    course_root: Path,
    framework_root: Path,
    unit_id: str,
    number: int,
    title: str | None = None,
    directory: Path | None = None,
) -> Result:
    methodology = _course_methodology(course_root, framework_root)
    values = _methodology_values(methodology)

    unit_number = int(unit_id[1:])
    if directory is None:
        directory = find_unit_directory(course_root, unit_number)
        if directory is None:
            raise FileNotFoundError(
                f"no directory for unit {unit_id}. Run `classkit scaffold unit {unit_number}` first."
            )

    values |= {
        "unit_id": unit_id,
        "session_id": f"{unit_id}-S{number:02d}",
        "session_number": number,
        "session_title": title or f"Study session {number}",
    }

    result = Result()
    write_new(
        directory / "sessions" / f"{number:02d}.md",
        render(_template(framework_root, "unit", "session.md"), values),
        result,
    )
    return result


# -- assessment item -------------------------------------------------------

def scaffold_item(
    course_root: Path,
    framework_root: Path,
    unit_id: str,
    item_format: str = "multiple-choice",
) -> Result:
    items_dir = course_root / "assessments" / "items"
    existing = {p.stem for p in items_dir.glob(f"{unit_id}-I*.md")} if items_dir.is_dir() else set()

    number = 1
    while f"{unit_id}-I{number:02d}" in existing:
        number += 1
    item_id = f"{unit_id}-I{number:02d}"

    template_name = "item-open.md" if item_format == "open" else "item-multiple-choice.md"

    result = Result()
    write_new(
        items_dir / f"{item_id}.md",
        render(
            _template(framework_root, "assessment", template_name),
            {"item_id": item_id, "unit_id": unit_id},
        ),
        result,
    )
    return result


# -- helpers ---------------------------------------------------------------

def _course_methodology(course_root: Path, framework_root: Path) -> dict:
    config_path = course_root / "course.yaml"
    name = "question-driven-25"
    if config_path.is_file():
        name = load_yaml(config_path).get("methodology", name)
    return load_methodology(framework_root, name)
