"""The course log — `LOG.md` and `classkit log` (D-036, spec §8.8).

What must hold: the log is append-only (nothing already in it — including entries the
teacher wrote by hand — is ever rewritten), its format is parseable, and a scaffolded
course starts with one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from classkit import log
from classkit.cli import main
from classkit.scaffold import scaffold_course

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]


def scaffold(root: Path):
    return scaffold_course(
        root,
        FRAMEWORK_ROOT,
        code="TEST-101",
        title="Test Course",
        institution="Test University",
        instructor="Test Instructor",
        units=13,
        methodology="question-driven-25",
    )


@pytest.fixture
def course_root(tmp_path: Path) -> Path:
    root = tmp_path / "course"
    scaffold(root)
    return root


def log_text(course_root: Path) -> str:
    return (course_root / "LOG.md").read_text(encoding="utf-8")


# -- scaffold starts the log -----------------------------------------------

def test_scaffold_creates_the_log_with_one_entry(course_root: Path):
    entries = log.parse(log_text(course_root))

    assert len(entries) == 1
    first = entries[0]
    assert first.title == "classkit scaffold course"
    assert first.date
    assert "course.yaml" in first.changed
    assert "syllabus/syllabus.md" in first.files
    assert "LOG.md" in first.files


def test_rescaffolding_leaves_the_log_alone(course_root: Path):
    log.append(course_root, log.Entry("taught U01", why="students liked it"))
    before = log_text(course_root)

    scaffold(course_root)

    assert log_text(course_root) == before


def test_scaffolding_a_course_that_predates_the_log_says_only_what_it_created(tmp_path: Path):
    root = tmp_path / "course"
    scaffold(root)
    (root / "LOG.md").unlink()

    scaffold(root)

    (entry,) = log.parse(log_text(root))
    assert "every other file already existed" in entry.changed
    assert entry.files == ["LOG.md"]


def test_scaffolding_a_unit_is_logged_naming_the_unit_and_its_files(course_root: Path):
    """Teacher test: `scaffold course` wrote an entry, `scaffold unit 1` (6 files) none."""
    from classkit.scaffold import scaffold_unit

    scaffold_unit(course_root, FRAMEWORK_ROOT, 3, "Heaps")
    entry = log.parse(log_text(course_root))[-1]
    assert entry.title == "classkit scaffold unit 3"
    assert 'U03 "Heaps"' in entry.changed
    assert "units/03-heaps/unit.md" in entry.files and "units/03-heaps/in-class.md" in entry.files
    assert len(entry.files) == 6


def test_rescaffolding_a_unit_that_creates_nothing_is_not_logged(course_root: Path):
    from classkit.scaffold import scaffold_unit

    scaffold_unit(course_root, FRAMEWORK_ROOT, 3, "Heaps")
    before = log_text(course_root)
    scaffold_unit(course_root, FRAMEWORK_ROOT, 3, "Heaps")
    assert log_text(course_root) == before


# -- append-only -----------------------------------------------------------

def test_append_adds_an_entry_at_the_end_and_keeps_everything_before_it(course_root: Path):
    before = log_text(course_root)

    log.append(
        course_root,
        log.Entry(
            "/design-unit 3, step 1 approved",
            changed="U03-S01..S04 created (14 guiding questions)",
            why="first design of unit 3",
            files=["units/03-heaps/sessions/01.md", "units/03-heaps/sessions/04.md"],
            date="2026-10-02",
        ),
    )

    after = log_text(course_root)
    assert after.startswith(before)
    assert after.endswith(
        "## 2026-10-02 — /design-unit 3, step 1 approved\n"
        "- **Changed:** U03-S01..S04 created (14 guiding questions)\n"
        "- **Why:** first design of unit 3\n"
        "- **Files:** units/03-heaps/sessions/01.md, units/03-heaps/sessions/04.md\n"
    )


def test_a_hand_edited_log_is_preserved_byte_for_byte(course_root: Path):
    path = course_root / "LOG.md"
    hand_written = log_text(course_root) + "\n## taught U01 — the entry quiz ran long\nno trailing newline"
    path.write_text(hand_written, encoding="utf-8")

    log.append(course_root, log.Entry("next change", changed="x", why="y"))

    text = log_text(course_root)
    assert text.startswith(hand_written)
    assert log.parse(text)[-1].title == "next change"


def test_append_creates_the_log_when_it_is_missing(course_root: Path):
    (course_root / "LOG.md").unlink()

    log.append(course_root, log.Entry("first", changed="x", why="y"))

    text = log_text(course_root)
    assert text.startswith("# Course log")
    assert [e.title for e in log.parse(text)] == ["first"]


# -- the format is parseable ------------------------------------------------

def test_format_and_parse_round_trip():
    entry = log.Entry(
        "/plan-units, step 2 approved",
        changed="U01..U13 created",
        why="the semester plan",
        files=["units/01-intro/unit.md", "units/02-lists/unit.md"],
        date="2026-10-01",
    )

    (parsed,) = log.parse(log.HEADER + "\n" + log.format_entry(entry))

    assert parsed == entry


def test_a_field_is_always_one_line():
    text = log.format_entry(log.Entry("t", why="first line\nsecond   line", date="2026-10-01"))
    assert "- **Why:** first line second line\n" in text


def test_an_entry_needs_a_title():
    with pytest.raises(ValueError):
        log.format_entry(log.Entry("   "))


def test_hand_written_entries_parse_even_off_the_shape():
    text = (
        "# Course log\n\nintro\n\n"
        "## 2026-11-03 — taught U03\n"
        "students found S02 too long\n"
        "- **Why:** noted for next year\n\n"
        "## a heading with no date\n"
    )

    first, second = log.parse(text)

    assert (first.date, first.title, first.why) == ("2026-11-03", "taught U03", "noted for next year")
    assert first.notes == ["students found S02 too long"]
    assert (second.date, second.title) == ("", "a heading with no date")


# -- classkit log -----------------------------------------------------------

def test_cli_appends_an_entry(course_root: Path, capsys):
    code = main([
        "log", "/ingest, run approved",
        "--changed", "M0001..M0012 ingested",
        "--why", "first ingest",
        "--file", "materials/manifest.yaml",
        "--date", "2026-10-05",
        "--course", str(course_root),
    ])

    assert code == 0
    last = log.parse(log_text(course_root))[-1]
    assert last.title == "/ingest, run approved"
    assert last.files == ["materials/manifest.yaml"]
    assert last.date == "2026-10-05"


def test_cli_rejects_a_malformed_date(course_root: Path):
    before = log_text(course_root)
    code = main([
        "log", "x", "--changed", "x", "--why", "x", "--date", "5/10/26",
        "--course", str(course_root),
    ])
    assert code == 2
    assert log_text(course_root) == before


def test_cli_requires_a_why(course_root: Path):
    with pytest.raises(SystemExit):
        main(["log", "x", "--changed", "x", "--course", str(course_root)])
