"""`classkit approve syllabus` and `classkit status` (D-043, spec §8.9), and the syllabus fields
the increment added: `unit_map`, `reading`, `approved`, a drafted `assessment`.

A throwaway course in tmp_path, as everywhere (invariant 1)."""

from __future__ import annotations

import difflib
from pathlib import Path

import pytest

from classkit import log
from classkit.approve import ApproveError, approve_syllabus, content_hash, read
from classkit.cli import main
from classkit.model import load_course
from classkit.scaffold import scaffold_course, scaffold_unit
from classkit.status import APPROVED, DRAFT, EDITED, NOT_STARTED, UNTRACKED, report, status
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


def test_a_hand_written_approval_validates_although_yaml_reads_on_as_true(course_root: Path):
    # YAML 1.1 parses the bare key `on` as the boolean True — and the spec tells a teacher to
    # write exactly `approved: {on: 2026-10-05}`.
    path = drafted(course_root)
    path.write_text(DRAFTED.replace("---\n\n#", "approved: {on: 2026-10-05}\n---\n\n#"), encoding="utf-8")
    assert errors(course_root) == []
    assert load_course(course_root, FRAMEWORK_ROOT).syllabus.data["approved"] == {"on": "2026-10-05"}


def test_a_malformed_approval_hash_is_a_schema_error(course_root: Path):
    path = drafted(course_root)
    path.write_text(DRAFTED.replace("---\n\n#", 'approved: {on: 2026-10-05, hash: "abc"}\n---\n\n#'),
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
    assert data["approved"] == {"on": "2026-10-05", "hash": approval.hash}
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
    assert all(line[2:].startswith(("approved:", "  on: 2026-10-05", '  hash: "sha256:', "# "))
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
    assert read(text)[0]["approved"] == {"on": "2026-11-01", "hash": second.hash}
    assert "re-approved" in log_entries(course_root)[-1].changed


def test_approving_over_a_hand_written_record_adds_the_hash(course_root: Path):
    path = drafted(course_root)
    path.write_text(DRAFTED.replace("---\n\n#", "approved: {on: 2026-10-01}\n---\n\n#"), encoding="utf-8")

    approval = approve_syllabus(course_root, on="2026-10-05")

    assert read(path.read_text(encoding="utf-8"))[0]["approved"] == {"on": "2026-10-05", "hash": approval.hash}
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
    path.write_text(DRAFTED.replace("---\n\n#", "approved: {on: 2026-10-05}\n---\n\n#"), encoding="utf-8")
    found = status(course_root, FRAMEWORK_ROOT).syllabus
    assert found.state == UNTRACKED
    assert "edits since cannot be tracked" in found.detail


def test_status_lists_the_unit_map_with_each_units_state(course_root: Path):
    drafted(course_root)
    scaffold_unit(course_root, FRAMEWORK_ROOT, 5, "Extra")

    lines = {line.number: line for line in status(course_root, FRAMEWORK_ROOT).units}

    assert lines[1].state == "unit.md present"
    assert lines[2].title == "Heaps" and lines[2].state == "not planned yet"
    assert lines[5].state == "unit.md present — not in the unit map"


def test_status_reports_materials_and_the_last_log_entry(course_root: Path, capsys):
    assert main(["status", "--course", str(course_root)]) == 0
    out = capsys.readouterr().out

    assert "NOT STARTED" in out
    assert "none ingested yet" in out
    assert "no coverage report saved yet" in out
    assert "classkit scaffold course" in out
    assert "13 in course.yaml" in out


def test_status_counts_a_source_file_not_yet_ingested(course_root: Path):
    (course_root / "materials" / "source" / "notes.md").write_text("# Notes\n", encoding="utf-8")
    text = report(status(course_root, FRAMEWORK_ROOT))
    assert "1 outstanding since the last ingest" in text


def test_status_writes_nothing(course_root: Path):
    drafted(course_root)
    before = {p: p.read_bytes() for p in course_root.rglob("*") if p.is_file()}
    main(["status", "--course", str(course_root)])
    assert {p: p.read_bytes() for p in course_root.rglob("*") if p.is_file()} == before
