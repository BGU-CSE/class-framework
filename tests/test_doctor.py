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


def test_a_differing_private_copy_is_a_note_not_an_instruction(course: Path):
    """D-041: a changed private source may be the teacher's newer printing or a TA's older copy —
    from inside a checkout the two look the same. Doctor says what ingesting here would do (the
    last machine to ingest rebuilds the committed index) and leaves the call to the person."""
    with_book(course)
    make_book(private(course) / "clrs.pdf", ["Heaps body", "Heapsort, revised"])
    (found,) = find(course, doctor.NOTE, "M0001", "differs from the one the committed index was built from")
    assert "last machine to ingest wins" in found.what
    assert not find(course, doctor.ACTION, "M0001")
    assert exit_code(course) == 0


def test_a_full_text_from_another_library_version_is_not_an_edit(course: Path):
    """D-041: another machine's extraction differs, but certifies itself — so it is not an edit."""
    with_book(course)
    full = private_text_file(course, "M0001")
    other = full.read_text(encoding="utf-8").split("\nbody_hash: ")[0]
    rest = full.read_text(encoding="utf-8").split("\n---\n", 1)[1]
    full.write_text(ingest.core.certify(other + "\n---\n" + rest.replace("Heaps body", "Heaps  body")),
                    encoding="utf-8")
    assert not find(course, doctor.NOTE, "M0001", "edited by hand")
    assert find(course, doctor.OK, "M0001", "current full text")


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


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_a_gitignore_that_git_itself_ignores_protects_no_clone(course: Path, tmp_path: Path, monkeypatch):
    """Found on the developer's own machine: a global excludes file listing `.gitignore`. The
    rules work here — and the file is never committed, so no clone has them."""
    excludes = tmp_path / "global-excludes"
    excludes.write_text(".gitignore\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=course.parent, check=True)
    subprocess.run(["git", "config", "core.excludesFile", str(excludes)], cwd=course.parent, check=True)

    assert find(course, doctor.OK, "course/.gitignore keeps")  # true on this machine…
    (found,) = find(course, doctor.ACTION, "itself ignored")  # …and on no other
    assert found.fix.startswith("git add -f course/.gitignore")


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_an_uncommitted_gitignore_is_a_note_until_committed(course: Path):
    def run_git(*args):
        subprocess.run(["git", *args], cwd=course.parent, check=True, capture_output=True)

    run_git("init", "-q")
    run_git("config", "core.excludesFile", "/dev/null")  # whatever this machine's global rules are
    assert find(course, doctor.NOTE, "not committed yet")
    run_git("add", "-f", "course/.gitignore")
    run_git("-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-qm", "gitignore")
    assert not find(course, doctor.NOTE, "not committed yet")


def test_a_private_copy_of_a_committed_file_does_not_make_it_private(course: Path):
    """Copying (not moving) a book into private/ merges it as an identical copy: the material
    stays public and its source stays committed. Doctor says so, and how to fix it."""
    make_pdf(course / "materials" / "source" / "clrs.pdf", ["Heaps body"])
    ingest.run(course, fetch=False)
    private(course).mkdir()
    shutil.copy(course / "materials" / "source" / "clrs.pdf", private(course) / "clrs.pdf")
    ingest.run(course, fetch=False)

    (found,) = find(course, doctor.ACTION, "identical copy", "not private")
    assert "delete materials/source/clrs.pdf" in found.fix

    (course / "materials" / "source" / "clrs.pdf").unlink()  # the teacher follows the fix
    ingest.run(course, fetch=False)
    assert not find(course, doctor.ACTION, "identical copy")
    assert ingest.load(course)[0]["private"] is True


# -- quotation of private material (D-042) ------------------------------------------

BOOK_SENTENCE = ("a heap is a nearly complete binary tree in which the key of every node is at "
                 "least as large as the keys of its children")


def with_text_book(course: Path) -> None:
    private(course).mkdir(parents=True, exist_ok=True)
    (private(course) / "book.md").write_text(
        f"# The book\n\n## Heaps\n\n{BOOK_SENTENCE.capitalize()}. More text follows here.\n",
        encoding="utf-8")
    ingest.run(course, fetch=False)


def coverage(course: Path, text: str) -> None:
    (course / "materials" / "coverage.md").write_text(f"# Coverage\n\n{text}\n", encoding="utf-8")


def test_a_course_file_copying_a_private_book_needs_action(course: Path):
    with_text_book(course)
    coverage(course, f'The book says: "{BOOK_SENTENCE.upper()}." (M0001#heaps)')

    found = find(course, doctor.ACTION, "coverage.md", "M0001#heaps")
    assert len(found) == 1
    assert "26 consecutive words" in found[0].what  # the whole sentence
    assert exit_code(course) == 1


def test_a_paraphrase_and_a_short_phrase_pass(course: Path):
    with_text_book(course)
    coverage(course, "Heaps keep the largest key at the root; see M0001#heaps. The book calls "
                     "it a nearly complete binary tree, and so do we.")

    assert not find(course, doctor.ACTION, "copies")
    assert find(course, doctor.OK, "no committed course file copies")


def test_the_course_log_is_checked_too(course: Path):
    with_text_book(course)
    with (course / "LOG.md").open("a", encoding="utf-8") as log:
        log.write(f"\n## note\n- **Why:** {BOOK_SENTENCE}\n")

    assert find(course, doctor.ACTION, "LOG.md", "M0001")


def test_the_index_and_the_full_text_themselves_are_not_flagged(course: Path):
    with_text_book(course)
    assert not find(course, doctor.ACTION, "copies")


def test_without_the_full_text_the_check_says_it_was_skipped(course: Path):
    with_text_book(course)
    coverage(course, BOOK_SENTENCE)
    private_text_file(course, "M0001").unlink()

    assert find(course, doctor.OK, "quotation check skipped")
    assert not find(course, doctor.ACTION, "copies")
