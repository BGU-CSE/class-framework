"""`classkit doctor` — this machine's copy of the course (D-040, spec §2.2, §8.7).

`validate` judges the course and gives the same answer on every clone; `doctor` judges this
machine. Each test builds the situation in `tmp_path` and asserts the line doctor reports, its
status, and the exit code: 1 when something needs action, 0 otherwise. Doctor is read-only.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from materials_fixtures import make_book, make_pdf

from classkit import doctor, ingest
from classkit.cli import main
from classkit.ingest.manifest import private_text_file
from classkit.scaffold import scaffold_course

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise OSError("no network in tests")

    monkeypatch.setattr("urllib.request.urlopen", refuse)


@pytest.fixture
def course(tmp_path: Path) -> Path:
    root = tmp_path / "course"
    scaffold_course(root, FRAMEWORK_ROOT, code="T-1", title="Test", institution="U",
                    instructor="", units=13, methodology="question-driven-25")
    return root


def private(course: Path) -> Path:
    return course / "materials" / "source" / "private"


def with_book(course: Path) -> Path:
    path = make_book(private(course) / "clrs.pdf", ["Heaps body", "Heapsort body"], front_matter=1,
                     outline=[("6 Heapsort", 1)])
    ingest.run(course, fetch=False)
    return path


def lines(course: Path) -> list[doctor.Line]:
    return doctor.diagnose(course, FRAMEWORK_ROOT)


def find(course: Path, status: str, *words: str) -> list[doctor.Line]:
    return [line for line in lines(course)
            if line.status == status and all(w in line.what for w in words)]


def actions(course: Path) -> list[doctor.Line]:
    return [line for line in lines(course) if line.status == doctor.ACTION]


def exit_code(course: Path) -> int:
    return main(["doctor", "--course", str(course)])


# -- a healthy machine -------------------------------------------------------------

def test_a_fresh_course_needs_nothing(course: Path, capsys):
    assert actions(course) == []
    assert exit_code(course) == 0
    out = capsys.readouterr().out
    assert "course/.gitignore keeps" in out and "Nothing to fix" in out


def test_doctor_is_read_only(course: Path):
    with_book(course)
    private_text_file(course, "M0001").unlink()  # something to fix — doctor must not fix it
    before = {p: p.read_bytes() for p in course.rglob("*") if p.is_file()}
    exit_code(course)
    assert {p: p.read_bytes() for p in course.rglob("*") if p.is_file()} == before


def test_a_private_book_with_its_current_full_text_is_ok(course: Path):
    with_book(course)
    assert find(course, doctor.OK, "M0001", "current full text here")
    assert actions(course) == []


# -- the .gitignore --------------------------------------------------------------------

def test_a_missing_gitignore_needs_action(course: Path, capsys):
    (course / ".gitignore").unlink()
    assert find(course, doctor.ACTION, ".gitignore is missing")
    assert exit_code(course) == 1
    assert "classkit scaffold course" in capsys.readouterr().out  # the line says how to fix it


def test_a_gitignore_without_the_private_text_rule_needs_action(course: Path):
    (course / ".gitignore").write_text("materials/source/private/\n", encoding="utf-8")
    (found,) = find(course, doctor.ACTION, "materials/private-text/", "not gitignored")
    assert "materials/private-text/" in found.fix


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_in_a_repository_git_itself_is_asked(course: Path):
    subprocess.run(["git", "init", "-q"], cwd=course.parent, check=True)
    assert find(course, doctor.OK, "course/.gitignore keeps")
    assert not find(course, doctor.NOTE, "not in a git repository")
    # A rule elsewhere that re-includes the folder defeats the course's own .gitignore.
    (course / "materials" / "source" / ".gitignore").write_text("!private/\n", encoding="utf-8")
    assert find(course, doctor.ACTION, "materials/source/private/", "not gitignored")


def test_outside_git_doctor_says_why_the_commit_check_is_skipped(course: Path):
    assert find(course, doctor.NOTE, "not in a git repository", "private_material_committed")


def test_a_private_folder_in_another_case_must_be_renamed(course: Path):
    make_pdf(course / "materials" / "source" / "Private" / "clrs.pdf", ["Heaps"])
    (found,) = find(course, doctor.ACTION, "Private/", "case-sensitive")
    assert "rename it" in found.fix


# -- private material on this machine ------------------------------------------------------

def test_a_private_source_not_on_this_machine_is_a_note_not_a_failure(course: Path):
    """A TA's clone without the textbook is normal: the line says so, and how to get it."""
    path = with_book(course)
    path.unlink()
    (found,) = find(course, doctor.NOTE, "M0001", "not on this machine", "index only")
    assert "classkit material remove M0001" in found.fix
    assert exit_code(course) == 0


def test_a_missing_full_text_needs_ingest(course: Path):
    with_book(course)
    private_text_file(course, "M0001").unlink()
    (found,) = find(course, doctor.ACTION, "M0001", "full text is missing or stale")
    assert found.fix == "classkit ingest"
    assert exit_code(course) == 1


def test_a_stale_full_text_needs_ingest(course: Path):
    with_book(course)
    full = private_text_file(course, "M0001")
    full.write_text(full.read_text(encoding="utf-8").replace("source_hash: sha256:", "source_hash: sha256:0"),
                    encoding="utf-8")
    assert find(course, doctor.ACTION, "M0001", "full text is missing or stale")


def test_a_changed_private_source_needs_ingest(course: Path):
    with_book(course)
    make_book(private(course) / "clrs.pdf", ["Heaps body", "Heapsort, revised"])
    assert find(course, doctor.ACTION, "M0001", "source changed")


def test_a_new_private_file_needs_ingest(course: Path):
    make_pdf(private(course) / "manual.pdf", ["Solutions"])
    (found,) = find(course, doctor.ACTION, "private/manual.pdf", "not ingested")
    assert found.fix == "classkit ingest"


def test_a_hand_edited_full_text_is_a_note(course: Path):
    with_book(course)
    full = private_text_file(course, "M0001")
    full.write_text(full.read_text(encoding="utf-8") + "\nFixed by the teacher.\n", encoding="utf-8")
    assert find(course, doctor.NOTE, "M0001", "edited by hand")
    assert actions(course) == []


def test_a_committed_copy_that_is_not_an_index_needs_action(course: Path):
    with_book(course)
    index = ingest.ingested_file(course, "M0001")
    index.write_text(private_text_file(course, "M0001").read_text(encoding="utf-8"), encoding="utf-8")
    (found,) = find(course, doctor.ACTION, "M0001", "not an index")
    assert found.fix == "classkit ingest --overwrite M0001"


def test_a_leftover_full_text_is_listed(course: Path):
    path = with_book(course)
    path.unlink()
    ingest.remove(course, "M0001")
    (found,) = find(course, doctor.ACTION, "leftover full text", "M0001 was removed")
    assert found.fix.startswith("delete it")


# -- the machine ---------------------------------------------------------------------------

def test_a_dependency_that_does_not_import_needs_action(course: Path, monkeypatch):
    monkeypatch.setattr(doctor, "_requirements", lambda: ["PyYAML", "surely-not-installed-pkg"])
    (found,) = find(course, doctor.ACTION, "surely-not-installed-pkg", "does not import")
    assert "pip install" in found.fix


def test_the_installed_dependencies_import(course: Path):
    assert find(course, doctor.OK, "dependencies import", "pypdf")


def test_a_missing_converter_is_a_note_naming_what_waits_for_it(course: Path, monkeypatch):
    monkeypatch.setattr("classkit.ingest.extract.pandoc", lambda: None)
    (course / "materials" / "source" / "notes.odt").write_bytes(b"not really odt")
    ingest.run(course, fetch=False)
    (found,) = find(course, doctor.NOTE, "pandoc is not installed", "1 material(s)")
    assert "install" in found.fix

    monkeypatch.setattr("classkit.ingest.extract.pandoc", lambda: "/usr/bin/pandoc")
    assert find(course, doctor.OK, "pandoc is installed")


def test_the_working_mode_is_reported(course: Path):
    assert find(course, doctor.OK, "working mode:")
