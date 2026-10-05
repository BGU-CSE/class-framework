"""`classkit approve syllabus` and `classkit status` (D-043, spec §8.9), and the syllabus fields
the increment added: `unit_map`, `reading`, `approved`, a drafted `assessment`.

A throwaway course in tmp_path, as everywhere (invariant 1)."""

from __future__ import annotations

import difflib
from pathlib import Path

import pytest

from classkit import log
from classkit.approve import ApproveError, approve_syllabus, approve_unit, content_hash, read
from classkit.cli import main
from classkit.model import load_course
from classkit.scaffold import scaffold_course, scaffold_item, scaffold_unit
from classkit.status import (APPROVED, DESIGNED, DRAFT, EDITED, NOT_STARTED, PLANNED, UNIT_DRAFTED,
                             UNTRACKED, report, status)
from classkit.validate import validate

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]

DRAFTED = '''---
# The teacher's own comment, which approving must not lose.
goal: "Students learn to design and analyse efficient algorithms."
outcomes:
  - id: CO1
    statement: "Analyse the running time of an algorithm"
    bloom: analyze
  - id: CO2
    statement: "Choose a data structure for a problem and justify it"
unit_map:
  - number: 1
    title: "First Unit"
    summary: "Growth of functions."
  - number: 2
    title: "Heaps"
    evidence: ["CLRS ch. 6"]
workload: {credits: 5, credit_system: "ECTS", total_hours: 150}
prerequisites: ["Data Structures"]
reading:
  required: ["CLRS"]
  recommended: ["Kleinberg & Tardos"]
assessment:
  - {type: exam, weight: 60}
  - {type: homework, weight: 40, description: "six problem sets"}
---

# Syllabus

## Course description

Algorithms, for second-year students.
'''


@pytest.fixture
def course_root(tmp_path: Path) -> Path:
    root = tmp_path / "course"
    scaffold_course(root, FRAMEWORK_ROOT, code="TEST-101", title="Test Course",
                    institution="Test University", instructor="Test Instructor", units=13,
                    methodology="question-driven-25")
    scaffold_unit(root, FRAMEWORK_ROOT, 1, "First Unit")
    return root


def syllabus(course_root: Path) -> Path:
    return course_root / "syllabus" / "syllabus.md"


def drafted(course_root: Path) -> Path:
    syllabus(course_root).write_text(DRAFTED, encoding="utf-8")
    return syllabus(course_root)


def findings(course_root: Path):
    return validate(load_course(course_root, FRAMEWORK_ROOT), FRAMEWORK_ROOT)


def errors(course_root: Path) -> list:
    return [f for f in findings(course_root) if f.level == "error"]


def state(course_root: Path) -> str:
    return status(course_root, FRAMEWORK_ROOT).syllabus.state


def log_entries(course_root: Path) -> list[log.Entry]:
    return log.parse((course_root / log.LOG_FILE).read_text(encoding="utf-8"))


# -- the schema accepts the new fields; a fresh scaffold still validates -----

def test_a_fresh_scaffold_still_validates_with_no_errors(course_root: Path):
    assert errors(course_root) == []


def test_the_schema_accepts_unit_map_reading_and_a_drafted_grading_scheme(course_root: Path):
    drafted(course_root)
    assert errors(course_root) == []


def test_an_approved_syllabus_validates(course_root: Path):
    drafted(course_root)
    approve_syllabus(course_root, on="2026-10-05")
    assert errors(course_root) == []


def test_a_hand_written_approval_validates(course_root: Path):
    # What §8.9 tells a teacher to write by hand: `approved: {date: 2026-10-05}`.
    path = drafted(course_root)
    path.write_text(DRAFTED.replace("---\n\n#", "approved: {date: 2026-10-05}\n---\n\n#"), encoding="utf-8")
    assert errors(course_root) == []
    assert load_course(course_root, FRAMEWORK_ROOT).syllabus.data["approved"] == {"date": "2026-10-05"}


def test_an_old_on_key_is_still_read_as_the_date(course_root: Path):
    # The key was `on` until D-044; YAML 1.1 reads a bare `on` as True. Still read, as `date`.
    path = drafted(course_root)
    path.write_text(DRAFTED.replace("---\n\n#", "approved: {on: 2026-10-05}\n---\n\n#"), encoding="utf-8")
    assert errors(course_root) == []
    assert load_course(course_root, FRAMEWORK_ROOT).syllabus.data["approved"] == {"date": "2026-10-05"}


def test_an_invented_locator_in_the_unit_maps_evidence_warns(course_root: Path):
    """D-044: nothing about the syllabus's content is an error (D-043), but an invented locator
    behind a unit's plan is caught — at the prose-locator rule's severity, warn."""
    path = drafted(course_root)
    path.write_text(DRAFTED.replace('evidence: ["CLRS ch. 6"]', 'evidence: ["M0042#page-3", "CLRS ch. 6"]'),
                    encoding="utf-8")
    found = [f for f in findings(course_root) if f.code == "material_locator_in_text"]
    assert [f.level for f in found] == ["warn"]
    assert "unit 2" in found[0].message and "M0042#page-3" in found[0].message
    assert errors(course_root) == []


def test_a_malformed_approval_hash_is_a_schema_error(course_root: Path):
    path = drafted(course_root)
    path.write_text(DRAFTED.replace("---\n\n#", 'approved: {date: 2026-10-05, hash: "abc"}\n---\n\n#'),
                    encoding="utf-8")
    assert any(f.code == "schema" and "hash" in f.message for f in errors(course_root))


def test_a_unit_map_entry_needs_a_number_and_a_title(course_root: Path):
    path = drafted(course_root)
    path.write_text(DRAFTED.replace('    title: "Heaps"\n', ""), encoding="utf-8")
    assert any(f.code == "schema" and "title" in f.message for f in errors(course_root))


# -- approve ----------------------------------------------------------------

def test_approve_writes_the_date_and_the_hash_and_logs_it(course_root: Path):
    path = drafted(course_root)
    approval = approve_syllabus(course_root, on="2026-10-05", why="step 4 of /plan-syllabus")

    data, body = read(path.read_text(encoding="utf-8"))
    assert data["approved"] == {"date": "2026-10-05", "hash": approval.hash}
    assert approval.hash == content_hash(data, body)
    last = log_entries(course_root)[-1]
    assert last.title == "classkit approve syllabus"
    assert last.date == "2026-10-05"
    assert last.why == "step 4 of /plan-syllabus"
    assert last.files == ["syllabus/syllabus.md"]


def test_approve_changes_nothing_but_the_record(course_root: Path):
    path = drafted(course_root)
    approve_syllabus(course_root, on="2026-10-05")
    text = path.read_text(encoding="utf-8")

    assert "# The teacher's own comment, which approving must not lose." in text
    changes = [line for line in difflib.ndiff(DRAFTED.splitlines(), text.splitlines())
               if line[:2] in ("- ", "+ ")]
    assert not [line for line in changes if line.startswith("- ")]
    assert all(line[2:].startswith(("approved:", "  date: 2026-10-05", '  hash: "sha256:', "# "))
               or not line[2:].strip() for line in changes)
    assert read(text)[1] == read(DRAFTED)[1]


def test_approve_diff_writes_and_logs_nothing(course_root: Path, capsys):
    path = drafted(course_root)
    entries = len(log_entries(course_root))

    assert main(["approve", "syllabus", "--diff", "--course", str(course_root)]) == 0

    assert path.read_text(encoding="utf-8") == DRAFTED
    assert len(log_entries(course_root)) == entries
    assert "+approved:" in capsys.readouterr().out


def test_approving_again_without_edits_records_nothing(course_root: Path):
    drafted(course_root)
    approve_syllabus(course_root, on="2026-10-05")
    text = syllabus(course_root).read_text(encoding="utf-8")
    entries = len(log_entries(course_root))

    again = approve_syllabus(course_root, on="2026-10-09")

    assert again.already and again.on == "2026-10-05"
    assert syllabus(course_root).read_text(encoding="utf-8") == text
    assert len(log_entries(course_root)) == entries


def test_approving_after_an_edit_replaces_the_record_in_place(course_root: Path):
    path = drafted(course_root)
    approve_syllabus(course_root, on="2026-10-05")
    path.write_text(path.read_text(encoding="utf-8").replace("for second-year", "for third-year"),
                    encoding="utf-8")

    second = approve_syllabus(course_root, on="2026-11-01")

    text = path.read_text(encoding="utf-8")
    assert text.count("approved:") == 1
    assert text.count("# The teacher's approval") == 1
    assert read(text)[0]["approved"] == {"date": "2026-11-01", "hash": second.hash}
    assert "re-approved" in log_entries(course_root)[-1].changed


def test_approving_over_a_hand_written_record_adds_the_hash(course_root: Path):
    path = drafted(course_root)
    path.write_text(DRAFTED.replace("---\n\n#", "approved: {on: 2026-10-01}\n---\n\n#"), encoding="utf-8")

    approval = approve_syllabus(course_root, on="2026-10-05")

    assert read(path.read_text(encoding="utf-8"))[0]["approved"] == {"date": "2026-10-05", "hash": approval.hash}
    assert "by hand, without a hash" in log_entries(course_root)[-1].changed


def test_a_record_that_cannot_be_placed_cleanly_is_refused_not_written(course_root: Path):
    # A flow mapping continued at column 0 is valid YAML, but replacing the `approved:` line alone
    # would orphan its second line. The re-parse check refuses, and the file is untouched.
    odd = DRAFTED.replace("---\n\n#", "approved: {on: 2026-01-01,\nhash: x}\n---\n\n#")
    syllabus(course_root).write_text(odd, encoding="utf-8")
    with pytest.raises(ApproveError, match="could not place"):
        approve_syllabus(course_root, on="2026-10-05")
    assert syllabus(course_root).read_text(encoding="utf-8") == odd


def test_approve_without_a_syllabus_fails_cleanly(course_root: Path, capsys):
    syllabus(course_root).unlink()
    assert main(["approve", "syllabus", "--course", str(course_root)]) == 2
    assert "nothing to approve" in capsys.readouterr().err


def test_approve_refuses_a_file_whose_front_matter_does_not_parse(course_root: Path):
    syllabus(course_root).write_text("---\ngoal: [unclosed\n---\n", encoding="utf-8")
    with pytest.raises(ApproveError):
        approve_syllabus(course_root)


# -- status: approved / edited since / no hash / draft / not started ----------

def test_status_of_a_fresh_scaffold_says_not_started(course_root: Path):
    assert state(course_root) == NOT_STARTED


def test_status_of_an_unapproved_drafted_syllabus_says_draft(course_root: Path):
    drafted(course_root)
    assert state(course_root) == DRAFT


def test_status_says_approved_then_edited_since(course_root: Path):
    path = drafted(course_root)
    approve_syllabus(course_root, on="2026-10-05")
    assert state(course_root) == APPROVED

    path.write_text(path.read_text(encoding="utf-8").replace("Analyse the running", "Analyze the running"),
                    encoding="utf-8")
    found = status(course_root, FRAMEWORK_ROOT).syllabus
    assert found.state == EDITED
    assert "approved 2026-10-05 — edited since" in found.detail


def test_a_comment_or_key_order_change_is_not_an_edit(course_root: Path):
    path = drafted(course_root)
    approve_syllabus(course_root, on="2026-10-05")
    text = path.read_text(encoding="utf-8").replace(
        "# The teacher's own comment, which approving must not lose.", "# Reworded comment.")
    text = text.replace('prerequisites: ["Data Structures"]\n', "").replace(
        "workload:", 'prerequisites: ["Data Structures"]\nworkload:')
    path.write_text(text, encoding="utf-8")
    assert state(course_root) == APPROVED


def test_status_of_a_hand_approval_without_a_hash_says_edits_are_untracked(course_root: Path):
    path = drafted(course_root)
    path.write_text(DRAFTED.replace("---\n\n#", "approved: {date: 2026-10-05}\n---\n\n#"), encoding="utf-8")
    found = status(course_root, FRAMEWORK_ROOT).syllabus
    assert found.state == UNTRACKED
    assert "edits since cannot be tracked" in found.detail


def test_status_lists_the_unit_map_with_each_units_state(course_root: Path):
    drafted(course_root)
    scaffold_unit(course_root, FRAMEWORK_ROOT, 5, "Extra")

    lines = {line.number: line for line in status(course_root, FRAMEWORK_ROOT).units}

    assert lines[1].state == UNIT_DRAFTED
    assert lines[2].title == "Heaps" and lines[2].state == NOT_STARTED
    assert lines[5].state == UNIT_DRAFTED and lines[5].detail.endswith("not in the unit map")


def test_status_reports_materials_and_the_last_log_entry(course_root: Path, capsys):
    assert main(["status", "--course", str(course_root)]) == 0
    out = capsys.readouterr().out

    assert "NOT STARTED" in out
    assert "none ingested yet" in out
    assert "no coverage report saved yet" in out
    assert "classkit scaffold unit 1" in out  # the fixture scaffolds a unit last, and that is logged
    assert "13 in course.yaml" in out


def test_status_counts_a_source_file_not_yet_ingested(course_root: Path):
    (course_root / "materials" / "source" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    text = report(status(course_root, FRAMEWORK_ROOT))
    assert "1 outstanding since the last ingest" in text


def test_status_says_private_files_are_not_counted(course_root: Path):
    """Teacher test: status and the pre-flight gave two numbers; status leaves private files out by
    design (§2.2), and now says so."""
    private = course_root / "materials" / "source" / "private"
    private.mkdir(parents=True, exist_ok=True)
    (private / "book.md").write_text("# Book\n", encoding="utf-8")
    (course_root / "materials" / "source" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    text = report(status(course_root, FRAMEWORK_ROOT))
    assert "1 outstanding since the last ingest" in text
    assert "private files are not counted here: `classkit doctor` reports them" in text


def ingest_notes(course_root: Path, names: list[str]) -> None:
    from classkit import ingest

    for name in names:
        (course_root / "materials" / "source" / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    ingest.run(course_root, fetch=False)


def test_status_says_when_the_coverage_report_predates_a_material(course_root: Path):
    ingest_notes(course_root, ["a", "b", "c"])
    coverage = course_root / "materials" / "coverage.md"
    coverage.write_text("# Coverage report\n\nA snapshot. Materials covered: M0001–M0002.\n",
                        encoding="utf-8")
    text = report(status(course_root, FRAMEWORK_ROOT))
    assert "coverage report predates M0003 — re-run /ingest step 4 to refresh it" in text

    coverage.write_text("# Coverage report\n\nMaterials covered: M0001-M0002,\nM0003.\n", encoding="utf-8")
    assert "predates" not in report(status(course_root, FRAMEWORK_ROOT))


def test_status_names_the_newest_few_materials_a_coverage_report_predates(course_root: Path):
    ingest_notes(course_root, ["a", "b", "c", "d", "e", "f"])
    (course_root / "materials" / "coverage.md").write_text("Materials covered: M0001.\n", encoding="utf-8")
    assert "predates M0006, M0005, M0004 and 2 more" in report(status(course_root, FRAMEWORK_ROOT))


def test_a_coverage_report_without_the_line_is_not_judged(course_root: Path):
    ingest_notes(course_root, ["a"])
    (course_root / "materials" / "coverage.md").write_text("# Coverage\n\nnotes\n", encoding="utf-8")
    assert "predates" not in report(status(course_root, FRAMEWORK_ROOT))


def test_status_writes_nothing(course_root: Path):
    drafted(course_root)
    before = {p: p.read_bytes() for p in course_root.rglob("*") if p.is_file()}
    main(["status", "--course", str(course_root)])
    assert {p: p.read_bytes() for p in course_root.rglob("*") if p.is_file()} == before


# -- approve unit N: planned, designed, edited since (D-046, spec §8.9) ----------

def unit_dir(course_root: Path, number: int = 1) -> Path:
    return next(course_root.glob(f"units/{number:02d}-*"))


def unit_md(course_root: Path, number: int = 1) -> Path:
    return unit_dir(course_root, number) / "unit.md"


def unit_line(course_root: Path, number: int = 1):
    return next(line for line in status(course_root, FRAMEWORK_ROOT).units if line.number == number)


def touch(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"fixture drifted: {old!r} not in {path.name}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_the_schema_accepts_difficulties_and_a_unit_approval(course_root: Path):
    touch(unit_md(course_root), "objectives:\n",
          "difficulties:\n  - text: \"Reads O(n) as exact\"\n    origin: teacher\n"
          "  - text: \"Confuses best and worst case\"\n    origin: proposed\n"
          "approved: {date: 2026-10-05, stage: planned}\nobjectives:\n")
    assert errors(course_root) == []
    assert load_course(course_root, FRAMEWORK_ROOT).units[0].doc.data["approved"] == \
        {"date": "2026-10-05", "stage": "planned"}


@pytest.mark.parametrize("bad", [
    "difficulties:\n  - text: \"x\"\n    origin: guessed\n",   # origin not in the enum
    "difficulties:\n  - text: \"x\"\n",                         # origin missing
    "approved: {date: 2026-10-05}\n",                            # a unit's record needs a stage
    "approved: {date: 2026-10-05, stage: reviewed}\n",           # review is not a state
])
def test_the_schema_rejects_malformed_difficulties_and_records(course_root: Path, bad: str):
    touch(unit_md(course_root), "objectives:\n", bad + "objectives:\n")
    assert any(f.code == "schema" for f in errors(course_root))


def test_approve_unit_records_planned_with_the_hash_of_unit_md_and_logs_it(course_root: Path):
    approval = approve_unit(course_root, 1, stage="planned", on="2026-10-05", why="step 4 of /plan-units")

    data, body = read(unit_md(course_root).read_text(encoding="utf-8"))
    assert data["approved"] == {"date": "2026-10-05", "stage": "planned", "hash": approval.hash}
    assert approval.hash == content_hash(data, body)
    last = log_entries(course_root)[-1]
    assert last.title == "classkit approve unit 1"
    assert "U01 approved as planned" in last.changed
    assert last.why == "step 4 of /plan-units"
    assert last.files == [unit_md(course_root).relative_to(course_root).as_posix()]
    assert errors(course_root) == []
    assert unit_line(course_root).state == PLANNED and unit_line(course_root).detail == "planned 2026-10-05"


def test_approve_unit_changes_nothing_but_the_record(course_root: Path):
    before = unit_md(course_root).read_text(encoding="utf-8")
    approve_unit(course_root, 1, stage="planned", on="2026-10-05")
    after = unit_md(course_root).read_text(encoding="utf-8")

    removed = [line for line in difflib.ndiff(before.splitlines(), after.splitlines()) if line.startswith("- ")]
    assert removed == []
    assert read(after)[1] == read(before)[1]


def test_a_planned_unit_edited_since_says_so(course_root: Path):
    approve_unit(course_root, 1, stage="planned", on="2026-10-05")
    touch(unit_md(course_root), 'statement: "TODO"', 'statement: "Analyse a loop"')
    line = unit_line(course_root)
    assert line.state == PLANNED and line.edited
    assert line.detail == "planned 2026-10-05 — edited since"


def test_editing_a_session_does_not_touch_a_planned_units_hash(course_root: Path):
    approve_unit(course_root, 1, stage="planned", on="2026-10-05")
    touch(unit_dir(course_root) / "sessions" / "01.md", "TODO", "What is a loop invariant?")
    assert not unit_line(course_root).edited


def test_a_unit_approval_needs_its_stage(course_root: Path, capsys):
    """D-047: no default stage — a default "next one" turned a second "approve unit 1" into
    *designed* while the sessions were still placeholders."""
    with pytest.raises(ApproveError, match="which stage"):
        approve_unit(course_root, 1, on="2026-10-05")
    assert main(["approve", "unit", "1", "--course", str(course_root)]) == 2
    assert "--stage planned" in capsys.readouterr().err


def test_re_approving_an_edited_plan_records_it_again(course_root: Path):
    approve_unit(course_root, 1, stage="planned", on="2026-10-05")
    touch(unit_md(course_root), 'statement: "TODO"', 'statement: "Analyse a loop"')
    approval = approve_unit(course_root, 1, stage="planned", on="2026-10-06")
    assert approval.stage == "planned"
    assert "was planned 2026-10-05" in log_entries(course_root)[-1].changed


def test_designed_hashes_the_whole_unit(course_root: Path):
    scaffold_item(course_root, FRAMEWORK_ROOT, "U01")
    approve_unit(course_root, 1, stage="designed", on="2026-10-20")
    assert unit_line(course_root).detail == "designed 2026-10-20"
    last = log_entries(course_root)[-1]
    assert "assessments/items/U01-I01.md" in last.files

    for path, old, new in [
        (unit_md(course_root), 'statement: "TODO"', 'statement: "Analyse a loop"'),
        (unit_dir(course_root) / "sessions" / "03.md", "TODO", "Why?"),
        (course_root / "assessments" / "items" / "U01-I01.md", 'stem: "TODO"', 'stem: "Which?"'),
    ]:  # in-class.md: the next test
        original = path.read_text(encoding="utf-8")
        touch(path, old, new)
        line = unit_line(course_root)
        assert line.edited and line.detail == "designed 2026-10-20 — edited since", path.name
        path.write_text(original, encoding="utf-8")
        assert not unit_line(course_root).edited, path.name


def test_an_edit_to_the_in_class_hour_shows_on_a_designed_unit(course_root: Path):
    approve_unit(course_root, 1, stage="designed", on="2026-10-20")
    path = unit_dir(course_root) / "in-class.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nA note the teacher added.\n", encoding="utf-8")
    assert unit_line(course_root).edited


def test_a_new_session_or_entry_quiz_item_shows_on_a_designed_unit(course_root: Path):
    approve_unit(course_root, 1, stage="designed", on="2026-10-20")
    scaffold_item(course_root, FRAMEWORK_ROOT, "U01")
    assert unit_line(course_root).edited


def test_a_homework_item_or_another_units_item_is_not_part_of_the_unit_hash(course_root: Path):
    scaffold_item(course_root, FRAMEWORK_ROOT, "U01")
    homework = course_root / "assessments" / "items" / "U01-I01.md"
    touch(homework, "usage: [in-class-quiz]", "usage: [homework]")
    approve_unit(course_root, 1, stage="designed", on="2026-10-20")
    touch(homework, 'stem: "TODO"', 'stem: "Which?"')
    scaffold_unit(course_root, FRAMEWORK_ROOT, 2, "Second")
    scaffold_item(course_root, FRAMEWORK_ROOT, "U02")
    assert not unit_line(course_root).edited


def test_renaming_the_units_directory_is_not_an_edit(course_root: Path):
    approve_unit(course_root, 1, stage="designed", on="2026-10-20")
    unit_dir(course_root).rename(course_root / "units" / "01-renamed-by-hand")
    assert not unit_line(course_root).edited


def test_approving_a_unit_again_without_edits_records_nothing(course_root: Path):
    approve_unit(course_root, 1, stage="planned", on="2026-10-05")
    text = unit_md(course_root).read_text(encoding="utf-8")
    entries = len(log_entries(course_root))

    again = approve_unit(course_root, 1, stage="planned", on="2026-10-09")

    assert again.already and again.on == "2026-10-05"
    assert unit_md(course_root).read_text(encoding="utf-8") == text
    assert len(log_entries(course_root)) == entries


def test_re_approving_replaces_the_record_in_place(course_root: Path):
    approve_unit(course_root, 1, stage="planned", on="2026-10-05")
    approve_unit(course_root, 1, stage="designed", on="2026-10-20")
    text = unit_md(course_root).read_text(encoding="utf-8")
    assert text.count("\napproved:") == 1
    assert read(text)[0]["approved"]["stage"] == "designed"


def test_a_hand_written_unit_approval_is_untracked_and_approving_adds_the_hash(course_root: Path):
    touch(unit_md(course_root), "objectives:\n", "approved: {date: 2026-10-01, stage: planned}\nobjectives:\n")
    assert "edits since cannot be tracked" in unit_line(course_root).detail

    approval = approve_unit(course_root, 1, stage="planned", on="2026-10-05")
    assert read(unit_md(course_root).read_text(encoding="utf-8"))[0]["approved"]["hash"] == approval.hash
    assert "by hand, without a hash" in log_entries(course_root)[-1].changed


def test_approve_unit_cli_diff_writes_nothing_and_the_real_run_logs(course_root: Path, capsys):
    before = unit_md(course_root).read_text(encoding="utf-8")
    assert main(["approve", "unit", "1", "--stage", "planned", "--diff", "--course", str(course_root)]) == 0
    assert unit_md(course_root).read_text(encoding="utf-8") == before
    assert "+  stage: planned" in capsys.readouterr().out

    assert main(["approve", "unit", "1", "--stage", "planned", "--course", str(course_root)]) == 0
    out = capsys.readouterr().out
    assert "as planned" in out and "logged" in out


def test_approve_unit_cli_needs_a_number_and_the_syllabus_takes_none(course_root: Path, capsys):
    assert main(["approve", "unit", "--course", str(course_root)]) == 2
    assert "which unit" in capsys.readouterr().err
    assert main(["approve", "syllabus", "--stage", "planned", "--course", str(course_root)]) == 2


def test_approving_a_unit_with_no_directory_fails_cleanly(course_root: Path, capsys):
    assert main(["approve", "unit", "7", "--stage", "planned", "--course", str(course_root)]) == 2
    assert "Run /plan-units 7" in capsys.readouterr().err


def test_status_report_shows_each_units_state_and_the_counts(course_root: Path):
    drafted(course_root)  # a map of two units: 1 "First Unit", 2 "Heaps"
    approve_unit(course_root, 1, stage="planned", on="2026-10-05")
    text = report(status(course_root, FRAMEWORK_ROOT))
    assert "U01  First Unit  planned 2026-10-05" in text
    assert "U02  Heaps       not started" in text
    assert "1 planned, 1 not started" in text
