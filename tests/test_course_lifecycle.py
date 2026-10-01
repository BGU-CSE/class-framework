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

from classkit.cli import main
from classkit.model import load_course
from classkit.scaffold import scaffold_course, scaffold_item, scaffold_unit
from classkit.validate import DEFAULT_SEVERITY, Validator, validate

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


def item(course_root: Path, number: int) -> Path:
    return course_root / "assessments" / "items" / f"U01-I{number:02d}.md"


def syllabus(course_root: Path) -> Path:
    return course_root / "syllabus" / "syllabus.md"


def warnings(course_root: Path, code: str) -> list:
    return [f for f in findings(course_root) if f.code == code and f.level == "warn"]


def levels(course_root: Path, code: str) -> set[str]:
    """The severities at which `code` fired — empty if it did not fire."""
    return {f.level for f in findings(course_root) if f.code == code}


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


# -- the syllabus, the course-level top layer (D-021) -----------------------

def test_scaffold_creates_a_syllabus(course_root: Path):
    assert syllabus(course_root).is_file()


def test_the_scaffolded_syllabus_declares_course_outcomes(course_root: Path):
    course = load_course(course_root, FRAMEWORK_ROOT)

    assert course.syllabus is not None
    assert [o["id"] for o in course.outcomes] == ["CO1", "CO2"]


def test_scaffold_does_not_overwrite_an_authored_syllabus(course_root: Path):
    written_by_hand = "---\ngoal: \"Mine\"\noutcomes: [{id: CO1, statement: \"Mine\"}]\n---\n"
    syllabus(course_root).write_text(written_by_hand, encoding="utf-8")

    scaffold_course(
        course_root,
        FRAMEWORK_ROOT,
        code="TEST-101",
        title="Test Course",
        institution="Test University",
        instructor="Test Instructor",
        units=13,
        methodology="question-driven-25",
    )

    assert syllabus(course_root).read_text(encoding="utf-8") == written_by_hand


def test_a_syllabus_outcome_with_a_malformed_id_fails_the_schema(course_root: Path):
    edit(syllabus(course_root), "  - id: CO1", "  - id: OUTCOME-1")
    assert "schema" in codes(course_root)


def test_a_syllabus_without_outcomes_fails_the_schema(course_root: Path):
    path = syllabus(course_root)
    text = path.read_text(encoding="utf-8")
    head, _, rest = text.partition("outcomes:")
    path.write_text(head + "outcomes: []\n---" + rest.partition("---")[2], encoding="utf-8")

    assert "schema" in codes(course_root)


# -- workload is optional, and its absence is a standing warning (D-031d) ---

def test_a_scaffolded_syllabus_has_no_workload_yet(course_root: Path):
    """Optional so a teacher can draft and validate before credits are settled — but the
    absence must be visible, so it warns rather than passing in silence."""
    assert warnings(course_root, "syllabus_workload_missing")
    assert "syllabus_workload_missing" not in codes(course_root)


def test_declaring_a_workload_silences_the_warning(course_root: Path):
    edit(
        syllabus(course_root),
        "# workload:\n#   credits: 5\n#   credit_system: \"ECTS\"\n#   total_hours: 150",
        "workload:\n  credits: 5\n  credit_system: \"ECTS\"\n  total_hours: 150",
    )

    assert warnings(course_root, "syllabus_workload_missing") == []
    assert errors(course_root) == []


def test_a_workload_missing_its_credit_system_fails_the_schema(course_root: Path):
    edit(
        syllabus(course_root),
        "# workload:\n#   credits: 5\n#   credit_system: \"ECTS\"\n#   total_hours: 150",
        "workload:\n  credits: 5",
    )

    assert "schema" in codes(course_root)


def test_a_deleted_syllabus_is_reported_not_ignored(course_root: Path):
    syllabus(course_root).unlink()

    assert warnings(course_root, "syllabus_workload_missing")


# -- integrity: a reference to something that does not exist is an error (D-037) --

def test_activity_referencing_a_guiding_question_that_exists_nowhere(course_root: Path):
    edit(in_class(course_root), "[U01-S03-G1]", "[U01-S09-G7]")
    assert levels(course_root, "activity_references_guiding_question") == {"error"}


def test_goal_pointing_at_a_nonexistent_objective(course_root: Path):
    edit(session(course_root, 2), "objectives: [U01-O2]", "objectives: [U01-O9]")
    assert levels(course_root, "goal_maps_to_objective") == {"error"}


def test_item_testing_a_guiding_question_that_exists_nowhere(course_root: Path):
    scaffold_item(course_root, FRAMEWORK_ROOT, "U01")
    edit(item(course_root, 1), "guiding_questions: [U01-S01-G1]", "guiding_questions: [U01-S09-G1]")
    assert levels(course_root, "item_reference") == {"error"}


def test_item_belonging_to_a_unit_that_does_not_exist(course_root: Path):
    scaffold_item(course_root, FRAMEWORK_ROOT, "U01")
    edit(item(course_root, 1), "unit: U01", "unit: U07")
    assert levels(course_root, "item_reference") == {"error"}


# -- advisory: absent or unconventional is a warning, never an error (D-037) ---

def test_activity_referencing_nothing_warns(course_root: Path):
    edit(in_class(course_root), "guiding_questions: [U01-S03-G1]", "guiding_questions: []")
    assert levels(course_root, "activity_without_guiding_question") == {"warn"}
    assert errors(course_root) == []


def test_activity_with_no_guiding_questions_key_passes_the_schema(course_root: Path):
    """Presence is pedagogy, not shape: the schema must not turn this advice into an error."""
    edit(in_class(course_root), "    guiding_questions: [U01-S03-G1]\n", "")
    assert levels(course_root, "activity_without_guiding_question") == {"warn"}
    assert errors(course_root) == []


def test_activity_referencing_another_units_guiding_question_warns(course_root: Path):
    scaffold_unit(course_root, FRAMEWORK_ROOT, 2, "Second Unit")
    edit(in_class(course_root), "[U01-S03-G1]", "[U02-S03-G1]")
    assert levels(course_root, "activity_references_other_unit") == {"warn"}
    assert "activity_references_guiding_question" not in codes(course_root)


def test_item_with_no_correct_choice_warns(course_root: Path):
    scaffold_item(course_root, FRAMEWORK_ROOT, "U01")
    edit(item(course_root, 1), "correct: true", "correct: false")
    assert levels(course_root, "item_no_correct_choice") == {"warn"}
    assert errors(course_root) == []


def test_session_that_cannot_be_done_in_time_warns(course_root: Path):
    edit(session(course_root, 2), "est_minutes: 6", "est_minutes: 40")
    assert levels(course_root, "session_path_feasibility") == {"warn"}


def test_activities_overrunning_the_hour_warns(course_root: Path):
    edit(in_class(course_root), "duration_minutes: 13", "duration_minutes: 40")
    assert levels(course_root, "in_class_duration_match") == {"warn"}


def test_declared_hour_length_differing_from_the_methodology_warns(course_root: Path):
    edit(in_class(course_root), "duration_minutes: 50", "duration_minutes: 90")
    assert levels(course_root, "in_class_duration_match") == {"warn"}


def test_missing_entry_quiz_warns(course_root: Path):
    edit(in_class(course_root), "    type: quiz", "    type: discussion")
    assert levels(course_root, "require_opening_quiz") == {"warn"}


def test_too_few_activities_warns(course_root: Path):
    path = in_class(course_root)
    text = path.read_text(encoding="utf-8")
    head, _, _ = text.partition("  - id: U01-A3")
    path.write_text(head.rstrip() + "\n---\n", encoding="utf-8")
    assert levels(course_root, "activity_count") == {"warn"}


def test_activity_type_the_methodology_disallows_warns(course_root: Path):
    """The schema's enum still limits activity types to the known set; this checks the
    methodology's narrower `allowed_activity_types`, so a stricter methodology is needed."""
    course = load_course(course_root, FRAMEWORK_ROOT)
    course.methodology["in_class"]["allowed_activity_types"] = ["quiz", "discussion"]
    found = {f.level for f in validate(course, FRAMEWORK_ROOT) if f.code == "activity_type"}
    assert found == {"warn"}


def test_a_week_with_no_class_meeting_warns(course_root: Path):
    in_class(course_root).unlink()
    assert levels(course_root, "in_class_missing") == {"warn"}
    assert errors(course_root) == []


def test_objective_no_guiding_question_addresses_is_an_alert(course_root: Path):
    for number in range(1, 5):
        path = session(course_root, number)
        path.write_text(
            path.read_text(encoding="utf-8").replace("[U01-O2]", "[U01-O1]"), encoding="utf-8"
        )
    assert levels(course_root, "objective_coverage") == {"alert"}
    assert errors(course_root) == []


def test_wrong_number_of_sessions_warns(course_root: Path):
    session(course_root, 4).unlink()
    assert levels(course_root, "session_count") == {"warn"}


def test_wrong_number_of_goals_warns(course_root: Path):
    path = session(course_root, 1)
    text = path.read_text(encoding="utf-8")
    head, _, _ = text.partition("  - id: U01-S01-G2")
    path.write_text(head.rstrip() + "\n---\n", encoding="utf-8")
    assert levels(course_root, "goal_count") == {"warn"}


def test_goal_type_the_methodology_disallows_warns(course_root: Path):
    edit(session(course_root, 1), "type: question", "type: reading")
    assert levels(course_root, "goal_type") == {"warn"}


def test_unassessed_guiding_question_is_a_warning_not_an_error(course_root: Path):
    all_findings = findings(course_root)
    assessed = [f for f in all_findings if f.code == "guiding_question_assessed"]
    assert assessed, "expected unassessed guiding questions in a fresh scaffold"
    assert all(f.level == "warn" for f in assessed)


# -- the severity model itself (D-037) --------------------------------------

def test_every_default_severity_is_a_known_severity():
    assert set(DEFAULT_SEVERITY.values()) <= {"error", "alert", "warn", "off"}


def test_only_integrity_rules_default_to_error():
    """The mechanical line of D-037: only a rule that names something that does not exist
    may fail the build by default. A new rule defaulting to error must be added here
    deliberately, with a reason."""
    integrity = {
        "schema",
        "id_consistency",
        "goal_maps_to_objective",
        "outcome_reference",
        "activity_references_guiding_question",
        "item_reference",
        # D-035: a locator to a slide, page or heading that does not exist in the material
        "material_locator_resolves",
    }
    defaults_to_error = {code for code, level in DEFAULT_SEVERITY.items() if level == "error"}
    assert defaults_to_error <= integrity


def test_the_methodology_uses_only_known_rules_and_severities():
    import yaml

    data = yaml.safe_load(
        (FRAMEWORK_ROOT / "methodologies" / "question-driven-25.yaml").read_text(encoding="utf-8")
    )
    for code, level in (data.get("rules") or {}).items():
        assert code in DEFAULT_SEVERITY, code
        assert level in {"error", "alert", "warn", "off"}


def test_alerts_are_reported_before_errors_and_warnings(course_root: Path):
    edit(in_class(course_root), "[U01-S03-G1]", "[U01-S09-G7]")  # an error
    for number in range(1, 5):  # an alert
        path = session(course_root, number)
        path.write_text(
            path.read_text(encoding="utf-8").replace("[U01-O2]", "[U01-O1]"), encoding="utf-8"
        )
    validator = Validator(load_course(course_root, FRAMEWORK_ROOT), FRAMEWORK_ROOT)
    validator.run()
    order = [f.level for f in validator.ordered()]

    assert order == sorted(order, key=["alert", "error", "warn"].index)
    assert order[0] == "alert"
    assert str(validator.ordered()[0]).startswith("ALERT")


def run_cli(course_root: Path, *args: str) -> int:
    return main(["validate", str(course_root), *args])


def test_validate_exits_zero_on_alerts_and_warnings(course_root: Path, capsys):
    for number in range(1, 5):
        path = session(course_root, number)
        path.write_text(
            path.read_text(encoding="utf-8").replace("[U01-O2]", "[U01-O1]"), encoding="utf-8"
        )
    assert run_cli(course_root) == 0
    out = capsys.readouterr().out
    assert "ALERT" in out
    assert "1 alerts, 0 errors" in out


def test_validate_exits_one_on_an_error(course_root: Path):
    edit(in_class(course_root), "[U01-S03-G1]", "[U01-S09-G7]")
    assert run_cli(course_root) == 1


def test_strict_fails_on_alerts_and_warnings(course_root: Path):
    # A fresh scaffold has warnings (workload, unassessed questions, unit count).
    assert run_cli(course_root) == 0
    assert run_cli(course_root, "--strict") == 1


def test_a_rule_with_no_default_severity_is_a_programming_error(course_root: Path):
    validator = Validator(load_course(course_root, FRAMEWORK_ROOT), FRAMEWORK_ROOT)
    with pytest.raises(KeyError):
        validator.report("no_such_rule", course_root, "never registered")


# -- the teacher's last word: course.yaml `rules:` (D-037) ------------------

def set_rules(course_root: Path, rules: dict[str, str]) -> None:
    lines = "".join(f"  {code}: {level}\n" for code, level in rules.items())
    with (course_root / "course.yaml").open("a", encoding="utf-8") as handle:
        handle.write(f"\nrules:\n{lines}")


def test_course_rules_can_raise_a_warning_to_an_error(course_root: Path):
    session(course_root, 4).unlink()
    set_rules(course_root, {"session_count": "error"})
    assert levels(course_root, "session_count") == {"error"}


def test_course_rules_win_over_the_methodology(course_root: Path):
    # question-driven-25 sets guiding_question_assessed: warn
    set_rules(course_root, {"guiding_question_assessed": "alert"})
    assert levels(course_root, "guiding_question_assessed") == {"alert"}


def test_course_rules_can_switch_a_rule_off(course_root: Path):
    set_rules(course_root, {"guiding_question_assessed": "off"})
    assert levels(course_root, "guiding_question_assessed") == set()


def test_course_rules_can_switch_even_an_integrity_rule_off(course_root: Path):
    edit(in_class(course_root), "[U01-S03-G1]", "[U01-S09-G7]")
    set_rules(course_root, {"activity_references_guiding_question": "off"})
    assert errors(course_root) == []


def test_course_rules_with_an_unknown_severity_fail_the_schema(course_root: Path):
    set_rules(course_root, {"session_count": "fatal"})
    assert "schema" in codes(course_root)


def test_a_mistyped_rule_name_in_course_rules_warns(course_root: Path):
    set_rules(course_root, {"sesion_count": "off"})
    assert levels(course_root, "unknown_rule") == {"warn"}


# -- a single deliberate exception: `accepted:` (D-037) ---------------------

def accept(path: Path, rule: str, reason: str = "deliberate — the teacher's call") -> None:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"fixture drifted: {path.name} has no front matter"
    entry = f"accepted:\n  - rule: {rule}\n    reason: \"{reason}\"\n"
    path.write_text("---\n" + entry + text[len("---\n"):], encoding="utf-8")


def run_validator(course_root: Path) -> Validator:
    validator = Validator(load_course(course_root, FRAMEWORK_ROOT), FRAMEWORK_ROOT)
    validator.run()
    return validator


def test_accepted_suppresses_that_rule_for_that_file(course_root: Path):
    edit(session(course_root, 2), "est_minutes: 6", "est_minutes: 40")
    accept(session(course_root, 2), "session_path_feasibility", "long session on purpose")

    validator = run_validator(course_root)

    assert not [f for f in validator.findings if f.code == "session_path_feasibility"]
    assert [f.code for f in validator.suppressed] == ["session_path_feasibility"]


def test_accepted_does_not_reach_other_files(course_root: Path):
    edit(session(course_root, 2), "est_minutes: 6", "est_minutes: 40")
    edit(session(course_root, 3), "est_minutes: 6", "est_minutes: 40")
    accept(session(course_root, 2), "session_path_feasibility")

    still_reported = [
        f for f in findings(course_root) if f.code == "session_path_feasibility"
    ]
    assert [Path(f.where).name for f in still_reported] == ["03.md"]


def test_accepted_does_not_reach_other_rules_in_the_same_file(course_root: Path):
    edit(session(course_root, 2), "est_minutes: 6", "est_minutes: 40")
    edit(session(course_root, 2), "type: question", "type: reading")
    accept(session(course_root, 2), "session_path_feasibility")

    assert levels(course_root, "goal_type") == {"warn"}


def test_a_week_with_no_class_meeting_can_be_accepted_in_unit_md(course_root: Path):
    in_class(course_root).unlink()
    accept(next(course_root.glob("units/01-*/unit.md")), "in_class_missing", "holiday week")
    assert levels(course_root, "in_class_missing") == set()


def test_accepted_is_allowed_on_every_front_matter_artifact(course_root: Path):
    scaffold_item(course_root, FRAMEWORK_ROOT, "U01")
    for path in [
        syllabus(course_root),
        next(course_root.glob("units/01-*/unit.md")),
        session(course_root, 1),
        in_class(course_root),
        item(course_root, 1),
    ]:
        accept(path, "goal_count")

    assert "schema" not in codes(course_root)


def test_the_accepted_definition_is_identical_in_every_schema():
    """Five copies of one definition — this is what stops them drifting apart."""
    import json

    definitions = {
        name: json.loads((FRAMEWORK_ROOT / "schemas" / name).read_text(encoding="utf-8"))[
            "properties"
        ]["accepted"]
        for name in [
            "syllabus.schema.json",
            "unit.schema.json",
            "study-session.schema.json",
            "in-class-session.schema.json",
            "assessment-item.schema.json",
        ]
    }
    first = next(iter(definitions.values()))
    assert all(d == first for d in definitions.values())


def test_an_accepted_entry_without_a_reason_is_advice_not_a_schema_error(course_root: Path):
    """D-038: a missing reason is the teacher's call — it warns, and the entry still works."""
    path = session(course_root, 1)
    text = path.read_text(encoding="utf-8")
    path.write_text(
        "---\naccepted:\n  - rule: goal_count\n" + text[len("---\n"):], encoding="utf-8"
    )
    assert "schema" not in codes(course_root)
    assert levels(course_root, "accepted_without_reason") == {"warn"}


def test_an_empty_reason_counts_as_missing(course_root: Path):
    accept(session(course_root, 1), "goal_count", reason="  ")
    assert levels(course_root, "accepted_without_reason") == {"warn"}


def test_a_capitalised_rule_typo_is_advice_not_a_schema_error(course_root: Path):
    """D-038: every mistyped code is caught the same way — by `unknown_rule`, at warn."""
    accept(session(course_root, 1), "Goal_Count")
    assert "schema" not in codes(course_root)
    assert levels(course_root, "unknown_rule") == {"warn"}


def test_accepting_a_rule_that_does_not_exist_warns(course_root: Path):
    accept(session(course_root, 1), "sesion_budget")
    assert levels(course_root, "unknown_rule") == {"warn"}


def test_validate_counts_accepted_exceptions(course_root: Path, capsys):
    edit(session(course_root, 2), "est_minutes: 6", "est_minutes: 40")
    accept(session(course_root, 2), "session_path_feasibility")
    accept(session(course_root, 3), "goal_type")  # nothing to suppress

    run_cli(course_root)
    out = capsys.readouterr().out

    assert "1 findings suppressed by 2 accepted exceptions in 2 files" in out
    assert "(1 no longer match anything)" in out
    assert "[session_path_feasibility]" not in out


# -- objectives roll up to outcomes that exist (outcome_reference, D-037) ----

def unit_md(course_root: Path) -> Path:
    return next(course_root.glob("units/01-*/unit.md"))


def test_an_objective_naming_a_declared_outcome_is_fine(course_root: Path):
    edit(unit_md(course_root), "    bloom: understand\n", "    bloom: understand\n    outcomes: [CO1]\n")
    assert levels(course_root, "outcome_reference") == set()
    assert errors(course_root) == []


def test_an_objective_naming_an_undeclared_outcome_is_an_error(course_root: Path):
    edit(unit_md(course_root), "    bloom: understand\n", "    bloom: understand\n    outcomes: [CO9]\n")
    assert levels(course_root, "outcome_reference") == {"error"}


def test_an_objective_naming_no_outcome_is_not_a_schema_error(course_root: Path):
    """Presence is advisory (D-037) — `objective_maps_to_outcome` lands with step 3."""
    assert "schema" not in codes(course_root)


def test_a_bare_yaml_off_in_rules_means_off(course_root: Path):
    """YAML 1.1 reads an unquoted `off` as boolean false; it must still mean severity off."""
    with (course_root / "course.yaml").open("a", encoding="utf-8") as handle:
        handle.write("\nrules:\n  guiding_question_assessed: off\n")
    assert "schema" not in codes(course_root)
    assert levels(course_root, "guiding_question_assessed") == set()


# -- materials: locators resolve, sources are ingested (D-035) ----------------

def ingest_a_deck(course_root: Path, slides: int = 3) -> None:
    """Put a small generated deck in materials/source/ and ingest it — it becomes M0001."""
    from materials_fixtures import make_pptx

    from classkit import ingest

    make_pptx(
        course_root / "materials" / "source" / "lecture.pptx",
        [(f"Title {n}", f"Body {n}") for n in range(1, slides + 1)],
    )
    ingest.run(course_root, fetch=False)


def cite(course_root: Path, locator: str) -> None:
    """Point the first study path of session 1 at `locator`."""
    edit(session(course_root, 1), 'ref: "U01"', f'ref: "{locator}"')


def test_a_fresh_scaffold_has_no_materials_findings(course_root: Path):
    assert levels(course_root, "material_locator_resolves") == set()
    assert levels(course_root, "materials_not_ingested") == set()


def test_a_locator_to_an_existing_slide_resolves(course_root: Path):
    ingest_a_deck(course_root, slides=3)
    cite(course_root, "M0001#slide-3")
    assert levels(course_root, "material_locator_resolves") == set()
    assert errors(course_root) == []


def test_a_locator_to_a_missing_slide_is_an_error(course_root: Path):
    """The fabricated "slide 18" of a 3-slide deck — invariant 7 made partly mechanical."""
    ingest_a_deck(course_root, slides=3)
    cite(course_root, "M0001#slide-18")
    found = [f for f in findings(course_root) if f.code == "material_locator_resolves"]
    assert {f.level for f in found} == {"error"}
    assert "slide-1 … slide-3" in found[0].message


def test_a_locator_to_an_unknown_material_is_an_error(course_root: Path):
    ingest_a_deck(course_root)
    cite(course_root, "M0042")
    assert levels(course_root, "material_locator_resolves") == {"error"}


def test_a_locator_before_any_ingest_is_an_error(course_root: Path):
    cite(course_root, "M0001#slide-1")
    assert levels(course_root, "material_locator_resolves") == {"error"}


def test_a_locator_to_a_removed_source_is_an_error(course_root: Path):
    from classkit import ingest

    ingest_a_deck(course_root)
    (course_root / "materials" / "source" / "lecture.pptx").unlink()
    ingest.run(course_root, fetch=False)
    cite(course_root, "M0001#slide-1")
    assert levels(course_root, "material_locator_resolves") == {"error"}


def test_a_locator_in_an_activitys_materials_is_checked(course_root: Path):
    ingest_a_deck(course_root)
    text = in_class(course_root).read_text(encoding="utf-8")
    assert "  - id: U01-A1" in text, "fixture drifted: in-class template changed"
    first = text.index("  - id: U01-A1")
    end = text.index("\n", first)
    in_class(course_root).write_text(
        text[: end + 1] + "    materials: [\"M0001#slide-99\"]\n" + text[end + 1 :], encoding="utf-8"
    )
    assert levels(course_root, "material_locator_resolves") == {"error"}


def test_a_textbook_citation_is_not_a_locator(course_root: Path):
    """Un-ingested sources may still be cited by key (§8.2) — the rule only reads M-locators."""
    cite(course_root, "CLRS ch.6 pp.151-153")
    assert levels(course_root, "material_locator_resolves") == set()


def test_a_new_source_file_warns_until_ingested(course_root: Path):
    from classkit import ingest

    (course_root / "materials" / "source" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    assert levels(course_root, "materials_not_ingested") == {"warn"}

    ingest.run(course_root, fetch=False)
    assert levels(course_root, "materials_not_ingested") == set()


def test_a_changed_source_file_warns(course_root: Path):
    from classkit import ingest

    notes = course_root / "materials" / "source" / "notes.md"
    notes.write_text("# Notes\n", encoding="utf-8")
    ingest.run(course_root, fetch=False)
    notes.write_text("# Notes, revised\n", encoding="utf-8")
    assert levels(course_root, "materials_not_ingested") == {"warn"}


def test_a_moved_source_file_warns_until_ingested(course_root: Path):
    from classkit import ingest

    notes = course_root / "materials" / "source" / "notes.md"
    notes.write_text("# Notes\n", encoding="utf-8")
    ingest.run(course_root, fetch=False)
    (course_root / "materials" / "source" / "week1").mkdir()
    notes.rename(course_root / "materials" / "source" / "week1" / "notes.md")
    assert levels(course_root, "materials_not_ingested") == {"warn"}

    ingest.run(course_root, fetch=False)
    assert levels(course_root, "materials_not_ingested") == set()


def test_a_removed_source_file_warns_until_ingested(course_root: Path):
    from classkit import ingest

    notes = course_root / "materials" / "source" / "notes.md"
    notes.write_text("# Notes\n", encoding="utf-8")
    ingest.run(course_root, fetch=False)
    notes.unlink()
    assert levels(course_root, "materials_not_ingested") == {"warn"}

    ingest.run(course_root, fetch=False)
    assert levels(course_root, "materials_not_ingested") == set()


def test_locators_read_the_ingested_file_as_it_is_now(course_root: Path):
    """§8.7: anchors are checked against the .md with the teacher's hand edits in it — a heading
    they add resolves, and an anchor they remove stops resolving."""
    from classkit import ingest

    (course_root / "materials" / "source" / "notes.md").write_text(
        "# Notes\n\n## Heaps\n\ntext\n", encoding="utf-8"
    )
    ingest.run(course_root, fetch=False)
    copy = ingest.ingested_file(course_root, "M0001")
    text = copy.read_text(encoding="utf-8")
    assert "## Heaps" in text, "fixture drifted: extraction changed"
    copy.write_text(text.replace("## Heaps", "## Binary heaps") + "\n## Worked example\n", encoding="utf-8")

    cite(course_root, "M0001#worked-example")
    assert levels(course_root, "material_locator_resolves") == set()

    cite_again = session(course_root, 1)
    edit(cite_again, 'ref: "M0001#worked-example"', 'ref: "M0001#heaps"')
    assert levels(course_root, "material_locator_resolves") == {"error"}


def test_a_new_link_warns_until_ingested(course_root: Path):
    from classkit.ingest.links import add_url

    add_url(course_root / "materials" / "source", "https://example.org/heaps")
    assert levels(course_root, "materials_not_ingested") == {"warn"}


def test_a_malformed_manifest_record_fails_the_schema(course_root: Path):
    from classkit import ingest

    (course_root / "materials" / "source" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    ingest.run(course_root, fetch=False)
    edit(course_root / "materials" / "manifest.yaml", "kind: other", "kind: lecture-ish")
    assert levels(course_root, "schema") == {"error"}


def test_an_unreadable_manifest_is_an_error_not_a_crash(course_root: Path):
    (course_root / "materials" / "manifest.yaml").write_text("- id: [unclosed\n", encoding="utf-8")
    assert levels(course_root, "schema") == {"error"}
