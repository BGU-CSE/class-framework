"""Private and instructor-only material (D-040, spec §8.7).

A file under `materials/source/private/` is gitignored; its committed `ingested/` file is an
*index* — anchors and one-line labels, no body text — and its full text goes to the gitignored
`materials/private-text/`, this machine only. A missing private source is "not on this machine",
never "removed". `audience` says who may be pointed at a material.

Every source is generated in `tmp_path` (materials_fixtures.py); no test touches the network.
The validator's two rules are tested in test_course_lifecycle.py, `classkit doctor` in
test_doctor.py.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import jsonschema
import pytest
import yaml
from materials_fixtures import make_book, make_docx, make_pdf, make_pptx

from classkit import ingest, log
from classkit.cli import main
from classkit.frontmatter import parse as parse_front_matter
from classkit.ingest import extract
from classkit.ingest.manifest import load, private_text_file
from classkit.model import load_course
from classkit.scaffold import scaffold_course, scaffold_unit
from classkit.validate import validate

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]

#: Sentences that exist only in the body of the private fixtures — none may reach the index.
BODY = [
    "Preface: the quick brown fox studies algorithms",
    "A max-heap satisfies the heap property at every node",
    "To maintain the heap property call MAX-HEAPIFY on the root",
    "Heapsort runs in O(n log n) time in the worst case",
]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise OSError("no network in tests")

    monkeypatch.setattr("urllib.request.urlopen", refuse)


def scaffold(root: Path):
    return scaffold_course(root, FRAMEWORK_ROOT, code="T-1", title="Test", institution="U",
                           instructor="", units=13, methodology="question-driven-25")


@pytest.fixture
def course(tmp_path: Path) -> Path:
    root = tmp_path / "course"
    scaffold(root)
    return root


def source(course: Path) -> Path:
    return course / "materials" / "source"


def private(course: Path) -> Path:
    return source(course) / "private"


def run(course: Path, **kwargs):
    return ingest.run(course, fetch=False, **kwargs)


def record(course: Path, material_id: str = "M0001") -> dict:
    return {r["id"]: r for r in load(course)}[material_id]


def index_of(course: Path, material_id: str = "M0001") -> str:
    return ingest.ingested_file(course, material_id).read_text(encoding="utf-8")


def full_text_of(course: Path, material_id: str = "M0001") -> str:
    return private_text_file(course, material_id).read_text(encoding="utf-8")


def anchors(text: str) -> list[str]:
    return extract.anchors(parse_front_matter(text)[1])


def book(course: Path, name: str = "clrs.pdf", pages: list[str] = BODY) -> Path:
    return make_book(private(course) / name, pages, front_matter=1,
                     outline=[("6 Heapsort", 1), ("6.1 Heaps", 1), ("6.2 Maintaining the heap property", 2)])


def snapshot(directory: Path) -> dict[str, bytes]:
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in sorted(directory.rglob("*")) if p.is_file()}


# -- scaffold: course/.gitignore ---------------------------------------------------

def test_scaffold_writes_a_gitignore_covering_private_material(course: Path):
    lines = (course / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "materials/source/private/" in lines
    assert "materials/private-text/" in lines


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_git_really_ignores_private_material(course: Path):
    subprocess.run(["git", "init", "-q"], cwd=course.parent, check=True)
    for path in ("materials/source/private/clrs.pdf", "materials/private-text/M0001-clrs.md"):
        assert subprocess.run(["git", "check-ignore", "-q", path], cwd=course).returncode == 0, path
    assert subprocess.run(["git", "check-ignore", "-q", "materials/ingested/M0001-clrs.md"],
                          cwd=course).returncode == 1


def test_rescaffolding_adds_the_gitignore_to_an_older_course_and_logs_it(course: Path):
    (course / ".gitignore").unlink()  # a course scaffolded before D-040

    result = scaffold(course)

    assert [p.name for p in result.created] == [".gitignore"]
    last = log.parse((course / "LOG.md").read_text(encoding="utf-8"))[-1]
    assert last.title == "classkit scaffold course"
    assert last.files == [".gitignore"]


def test_rescaffolding_never_replaces_a_teachers_gitignore(course: Path):
    (course / ".gitignore").write_text("my own rules\n", encoding="utf-8")
    scaffold(course)
    assert (course / ".gitignore").read_text(encoding="utf-8") == "my own rules\n"


# -- the committed index ------------------------------------------------------------

def test_a_private_pdf_is_committed_as_an_index_with_no_body_text(course: Path):
    book(course)
    run(course)

    index = index_of(course)
    front, _body = parse_front_matter(index)
    assert front["text"] == "index"
    for sentence in BODY:
        assert sentence not in index  # the proof: no private text in the committed file
    assert record(course)["private"] is True


def test_the_index_has_every_anchor_with_printed_pages_and_sections(course: Path):
    book(course)
    run(course)

    index = index_of(course)
    assert anchors(index) == anchors(full_text_of(course)) == ["page-1", "page-2", "page-3", "page-4"]
    assert "*(printed page i)*" in index and "*(printed page 3)*" in index
    page_2 = index.split("## Page 2")[1].split("## Page 3")[0]
    assert "*(section: 6 Heapsort)*" in page_2 and "*(section: 6.1 Heaps)*" in page_2
    assert "*(section: 6.2 Maintaining the heap property)*" in index.split("## Page 3")[1]


def test_without_an_outline_the_index_has_pages_and_labels_only(course: Path):
    make_pdf(private(course) / "scan-ish.pdf", BODY)
    run(course)
    index = index_of(course)
    assert anchors(index) == ["page-1", "page-2", "page-3", "page-4"]
    assert "section:" not in index and not any(s in index for s in BODY)


def test_a_private_deck_is_indexed_by_slide_titles(course: Path):
    make_pptx(private(course) / "publisher-slides.pptx",
              [("Heaps", BODY[1]), ("Heapsort", BODY[3])], notes={1: "speaker notes stay private"})
    run(course)

    index = index_of(course)
    assert anchors(index) == ["slide-1", "slide-2"]
    assert "**Heaps**" in index and "**Heapsort**" in index
    assert BODY[1] not in index and "speaker notes stay private" not in index
    assert BODY[1] in full_text_of(course)


def test_a_private_document_is_indexed_by_its_headings(course: Path):
    make_docx(private(course) / "solutions.docx",
              [("h1", "Solutions"), ("p", BODY[1]), ("h2", "Exercise 6.1-1"), ("p", BODY[2])])
    run(course)

    index = index_of(course)
    assert anchors(index) == ["solutions", "exercise-6-1-1"]
    assert BODY[1] not in index and BODY[2] not in index


def test_a_long_label_is_cut_to_one_short_line():
    assert len(extract.label("word " * 100)) <= extract.LABEL_CHARS
    assert "\n" not in extract.label("two\nlines")
    assert extract.label("# not a heading").startswith("\\#")


# -- the local full text -------------------------------------------------------------

def test_the_full_text_is_written_only_to_private_text(course: Path):
    book(course)
    run(course)

    full = private_text_file(course, "M0001")
    assert full.parent == course / "materials" / "private-text"
    assert full.name == ingest.ingested_file(course, "M0001").name  # same name, same anchors
    front, body = parse_front_matter(full.read_text(encoding="utf-8"))
    assert front["source_hash"] == record(course)["source_hash"]
    assert all(sentence in body for sentence in BODY)
    assert record(course)["private_text_hash"].startswith("sha256:")
    # Nowhere committed holds the text.
    committed = [p for p in course.rglob("*") if p.is_file() and "private-text" not in p.parts
                 and "private" not in p.relative_to(course).parts]
    assert not any(BODY[2] in p.read_text(encoding="utf-8", errors="replace") for p in committed)


def test_the_manifest_with_private_fields_conforms_to_its_schema(course: Path):
    book(course)
    run(course)
    ingest.set_fields(course, "M0001", audience="student")
    schema = json.loads((FRAMEWORK_ROOT / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(load(course), schema)


def test_a_second_run_rewrites_nothing(course: Path):
    book(course)
    run(course)
    before = snapshot(course / "materials")

    report = run(course)

    assert report.converted == [] and report.plan.outstanding() == []
    assert snapshot(course / "materials") == before


def test_a_hand_edit_of_the_full_text_is_protected(course: Path, capsys):
    book(course)
    run(course)
    full = private_text_file(course, "M0001")
    full.write_text(full.read_text(encoding="utf-8") + "\nFixed by the teacher.\n", encoding="utf-8")
    book(course, pages=[*BODY[:3], "Heapsort, revised"])

    code = main(["ingest", "--no-fetch", "--course", str(course)])

    assert code == 3
    assert "Fixed by the teacher." in full.read_text(encoding="utf-8")
    assert "edited by hand" in capsys.readouterr().out
    assert "revised" not in index_of(course) + full.read_text(encoding="utf-8")  # neither written

    run(course, overwrite=["M0001"])
    assert "Fixed by the teacher." not in full_text_of(course)
    assert "Heapsort, revised" in full_text_of(course)


# -- another machine: a TA's clone ------------------------------------------------------

def clone_without_private(course: Path, tmp_path: Path) -> Path:
    """What a clone has: everything committed — not source/private/, not private-text/."""
    other = tmp_path / "ta" / "course"
    shutil.copytree(course, other, ignore=shutil.ignore_patterns("private", "private-text"))
    return other


def test_a_missing_private_source_is_not_on_this_machine_never_removed(course: Path, tmp_path: Path):
    book(course)
    run(course)
    ta = clone_without_private(course, tmp_path)
    before = snapshot(ta / "materials")

    report = run(ta)

    assert report.plan.removed == [] and not record(ta).get("removed_at")
    assert snapshot(ta / "materials") == before  # nothing committed changes on the TA's machine


def test_a_private_source_appearing_gets_its_full_text_and_changes_nothing_committed(
        course: Path, tmp_path: Path):
    book(course)
    run(course)
    ta = clone_without_private(course, tmp_path)
    shutil.copytree(private(course), private(ta))  # the TA copies the book in
    log_before = (ta / "LOG.md").read_text(encoding="utf-8")
    committed = {k: v for k, v in snapshot(ta / "materials").items() if not k.startswith("source/")}

    code = main(["ingest", "--no-fetch", "--course", str(ta)])

    assert code == 0
    assert BODY[2] in full_text_of(ta)
    after = {k: v for k, v in snapshot(ta / "materials").items()
             if not k.startswith(("source/", "private-text/"))}
    assert after == committed  # index and manifest byte-for-byte the same
    assert (ta / "LOG.md").read_text(encoding="utf-8") == log_before  # not a change to the course


def test_a_stale_full_text_is_refused_not_silently_replaced(course: Path, tmp_path: Path, capsys):
    book(course)
    run(course)
    stale = full_text_of(course)
    book(course, pages=[*BODY[:3], "Heapsort, second printing"])
    run(course)  # the teacher's machine moves on to the new version
    full = private_text_file(course, "M0001")
    full.write_text(stale, encoding="utf-8")  # a TA's copy, made from the first version

    code = main(["ingest", "--no-fetch", "--course", str(course)])

    assert code == 3
    assert "another version of the source" in capsys.readouterr().out
    run(course, overwrite=["M0001"])
    assert "second printing" in full_text_of(course)


# -- moving into and out of private/ -------------------------------------------------------

def test_moving_a_file_into_private_turns_its_committed_copy_into_an_index(course: Path):
    make_pdf(source(course) / "clrs.pdf", BODY)
    run(course)
    assert BODY[1] in index_of(course)

    private(course).mkdir()
    (source(course) / "clrs.pdf").rename(private(course) / "clrs.pdf")
    report = run(course)

    assert [m for m, _old, _new in report.plan.moved] == ["M0001"]
    assert BODY[1] not in index_of(course) and parse_front_matter(index_of(course))[0]["text"] == "index"
    assert BODY[1] in full_text_of(course)
    assert record(course)["private"] is True


def test_moving_a_file_out_of_private_commits_its_full_text_and_drops_the_local_copy(course: Path):
    book(course)
    run(course)

    (private(course) / "clrs.pdf").rename(source(course) / "clrs.pdf")
    run(course)

    assert BODY[1] in index_of(course)
    assert "text" not in parse_front_matter(index_of(course))[0]
    assert private_text_file(course, "M0001") is None
    assert "private" not in record(course) and "private_text_hash" not in record(course)


def test_a_private_folder_in_another_case_is_still_private(course: Path):
    # macOS git ignores `Private/` too; committing its full text would be the leak.
    make_pdf(source(course) / "Private" / "clrs.pdf", BODY)
    run(course)
    assert record(course)["private"] is True
    assert BODY[1] not in index_of(course)


# -- removing a private material is explicit ---------------------------------------------

def test_remove_marks_a_missing_private_material_removed(course: Path, capsys):
    book(course)
    run(course)
    (private(course) / "clrs.pdf").unlink()

    assert main(["material", "remove", "M0001", "--course", str(course)]) == 0

    assert record(course)["removed_at"]
    assert ingest.ingested_file(course, "M0001") is not None  # the index is kept
    assert "removed M0001" in capsys.readouterr().out


def test_remove_refuses_while_the_source_is_still_here(course: Path, capsys):
    book(course)
    run(course)
    assert main(["material", "remove", "M0001", "--course", str(course)]) == 2
    assert "still on this machine" in capsys.readouterr().err
    assert not record(course).get("removed_at")


def test_remove_refuses_a_material_that_is_not_private(course: Path, capsys):
    make_pdf(source(course) / "notes.pdf", ["Notes"])
    run(course)
    (source(course) / "notes.pdf").unlink()
    assert main(["material", "remove", "M0001", "--course", str(course)]) == 2
    assert "delete its source" in capsys.readouterr().err


def test_a_removed_private_material_is_cited_as_removed(course: Path):
    book(course)
    run(course)
    scaffold_unit(course, FRAMEWORK_ROOT, 1, "Heaps")
    session = next(course.glob("units/01-*/sessions/01.md"))
    text = session.read_text(encoding="utf-8")
    session.write_text(text.replace('ref: "U01"', 'ref: "M0001#page-3"', 1), encoding="utf-8")
    assert "M0001#page-3" in session.read_text(encoding="utf-8"), "fixture drifted"

    def locator_errors():
        return [f for f in validate(load_course(course, FRAMEWORK_ROOT), FRAMEWORK_ROOT)
                if f.code == "material_locator_resolves"]

    assert locator_errors() == []  # resolves against the index
    (private(course) / "clrs.pdf").unlink()
    assert locator_errors() == []  # not on this machine: still resolves
    ingest.remove(course, "M0001")
    assert locator_errors() and "removed" in locator_errors()[0].message


# -- audience ---------------------------------------------------------------------------

def test_audience_is_recorded_by_apply_and_set(course: Path, capsys):
    make_pdf(source(course) / "manual.pdf", ["Solutions"])
    make_pdf(source(course) / "notes.pdf", ["Notes"])
    run(course)

    ingest.apply(course, [{"id": "M0001", "kind": "exercise", "audience": "instructor"},
                          {"id": "M0002", "audience": "student"}])
    assert record(course, "M0001")["audience"] == "instructor"
    assert record(course, "M0002")["audience"] == "student"

    assert main(["material", "set", "M0001", "--audience", "student", "--course", str(course)]) == 0
    assert record(course, "M0001")["audience"] == "student"
    assert "audience=student" in capsys.readouterr().out


def test_an_unknown_audience_is_rejected_and_nothing_is_recorded(course: Path):
    make_pdf(source(course) / "manual.pdf", ["Solutions"])
    run(course)
    with pytest.raises(ingest.MaterialError, match="audience"):
        ingest.apply(course, [{"id": "M0001", "kind": "exercise", "audience": "teachers"}])
    assert "audience" not in record(course) and record(course)["kind"] == "other"


def test_apply_reads_audience_from_the_cli(course: Path, monkeypatch):
    import io

    make_pdf(source(course) / "manual.pdf", ["Solutions"])
    run(course)
    monkeypatch.setattr("sys.stdin", io.StringIO(yaml.safe_dump([{"id": "M0001", "audience": "instructor"}])))
    assert main(["material", "apply", "--course", str(course)]) == 0
    assert record(course)["audience"] == "instructor"


def test_links_inside_a_private_material_are_not_recorded(course: Path):
    """A URL in a private book's text is its text; the manifest is committed."""
    make_pdf(private(course) / "clrs.pdf", ["See https://example.org/errata for the errata"])
    run(course)
    assert [r["id"] for r in load(course)] == ["M0001"]
