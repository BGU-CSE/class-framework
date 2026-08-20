"""Scaffold → validate round-trip.

The framework ships no example course (D-015), so these tests build a throwaway one
with the scaffold itself and assert against it. That keeps a CI signal without putting
course content in the framework tree, and has the side benefit of testing the templates:
if a template drifts out of line with a schema or a methodology, a fresh scaffold stops
validating clean and these tests fail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from classkit.model import load_course
from classkit.scaffold import scaffold_course, scaffold_unit
from classkit.validate import validate

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def course_root(tmp_path: Path) -> Path:
    root = tmp_path / "course"
    scaffold_course(
        root,
        FRAMEWORK_ROOT,
        code="TEST-101",
        title="Test Course",
        institution="Test University",
        instructor="Test Instructor",
        units=13,
        methodology="question-driven-25",
    )
    scaffold_unit(root, FRAMEWORK_ROOT, 1, "First Unit")
    return root


def findings(course_root: Path):
    return validate(load_course(course_root, FRAMEWORK_ROOT), FRAMEWORK_ROOT)


def errors(course_root: Path) -> list:
    return [f for f in findings(course_root) if f.level == "error"]


def codes(course_root: Path) -> set[str]:
    return {f.code for f in errors(course_root)}


def in_class(course_root: Path) -> Path:
    return next(course_root.glob("units/01-*/in-class.md"))


def session(course_root: Path, number: int) -> Path:
    return next(course_root.glob(f"units/01-*/sessions/{number:02d}.md"))


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"fixture drifted: {old!r} not found in {path.name}"
    path.write_text(text.replace(old, new), encoding="utf-8")


# -- the scaffold produces something valid ---------------------------------

def test_fresh_scaffold_has_no_errors(course_root: Path):
    assert errors(course_root) == []


def test_scaffold_creates_the_expected_shape(course_root: Path):
    unit_dir = next(course_root.glob("units/01-*"))
    assert (unit_dir / "unit.md").is_file()
    assert (unit_dir / "in-class.md").is_file()
    assert len(list((unit_dir / "sessions").glob("*.md"))) == 4  # sessions_per_unit


def test_scaffold_never_overwrites(course_root: Path):
    target = in_class(course_root)
    target.write_text("EDITED BY THE TEACHER", encoding="utf-8")

    result = scaffold_unit(course_root, FRAMEWORK_ROOT, 1, "First Unit")

    assert target.read_text(encoding="utf-8") == "EDITED BY THE TEACHER"
    assert result.created == []
    assert target in result.skipped


def test_scaffold_fills_in_only_what_is_missing(course_root: Path):
    session(course_root, 3).unlink()

    result = scaffold_unit(course_root, FRAMEWORK_ROOT, 1, "First Unit")

    assert [p.name for p in result.created] == ["03.md"]
    assert len(result.skipped) == 5


# -- the validator catches what it exists to catch -------------------------

def test_activity_referencing_unknown_guiding_question(course_root: Path):
    edit(in_class(course_root), "[U01-S03-G1]", "[U01-S09-G7]")
    assert "activity_references_guiding_question" in codes(course_root)


def test_activity_referencing_nothing(course_root: Path):
    edit(in_class(course_root), "guiding_questions: [U01-S03-G1]", "guiding_questions: []")
    assert "activity_references_guiding_question" in codes(course_root)


def test_session_that_cannot_be_done_in_time(course_root: Path):
    edit(session(course_root, 2), "est_minutes: 6", "est_minutes: 40")
    assert "session_path_feasibility" in codes(course_root)


def test_activities_overrunning_the_hour(course_root: Path):
    edit(in_class(course_root), "duration_minutes: 13", "duration_minutes: 40")
    assert "in_class_duration_match" in codes(course_root)


def test_missing_entry_quiz(course_root: Path):
    edit(in_class(course_root), "    type: quiz", "    type: discussion")
    assert "require_opening_quiz" in codes(course_root)


def test_goal_pointing_at_a_nonexistent_objective(course_root: Path):
    edit(session(course_root, 2), "objectives: [U01-O2]", "objectives: [U01-O9]")
    assert "goal_maps_to_objective" in codes(course_root)


def test_objective_no_guiding_question_addresses(course_root: Path):
    for number in range(1, 5):
        path = session(course_root, number)
        path.write_text(
            path.read_text(encoding="utf-8").replace("[U01-O2]", "[U01-O1]"), encoding="utf-8"
        )
    assert "objective_coverage" in codes(course_root)


def test_wrong_number_of_sessions(course_root: Path):
    session(course_root, 4).unlink()
    assert "session_count" in codes(course_root)


def test_goal_type_the_methodology_disallows(course_root: Path):
    edit(session(course_root, 1), "type: question", "type: reading")
    assert "goal_type" in codes(course_root)


def test_unassessed_guiding_question_is_a_warning_not_an_error(course_root: Path):
    all_findings = findings(course_root)
    assessed = [f for f in all_findings if f.code == "guiding_question_assessed"]
    assert assessed, "expected unassessed guiding questions in a fresh scaffold"
    assert all(f.level == "warn" for f in assessed)
