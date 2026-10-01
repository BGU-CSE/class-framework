"""Ingest (D-035, spec §8.7): extraction, the manifest, incremental runs, and the guarantees.

Every source file is generated in `tmp_path` (materials_fixtures.py) — no real course material
and no binary samples in the repo. No test touches the network: `urlopen` is replaced for the
whole module, so a link whose metadata cannot be fetched is the normal case here, and must
still be recorded.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml
from materials_fixtures import make_docx, make_pdf, make_pptx

from classkit import ingest
from classkit.cli import main
from classkit.frontmatter import parse as parse_front_matter
from classkit.ingest import extract, links
from classkit.ingest.manifest import load
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


def source(course: Path) -> Path:
    return course / "materials" / "source"


def run(course: Path, **kwargs):
    return ingest.run(course, fetch=kwargs.pop("fetch", False), **kwargs)


def records(course: Path) -> dict[str, dict]:
    return {r["id"]: r for r in load(course)}


def ingested_text(course: Path, material_id: str) -> str:
    return ingest.ingested_file(course, material_id).read_text(encoding="utf-8")


def anchors_of(course: Path, material_id: str) -> list[str]:
    return extract.anchors(parse_front_matter(ingested_text(course, material_id))[1])


def snapshot(directory: Path) -> dict[str, bytes]:
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in sorted(directory.rglob("*")) if p.is_file()}


# -- extraction: the same anchors every time, per format -----------------------

def test_pptx_has_one_anchor_per_slide(course: Path):
    make_pptx(source(course) / "deck.pptx", [("Heaps", "A heap is a tree"), ("Sift down", "Swap")],
              notes={1: "draw it on the board"})
    run(course)

    assert anchors_of(course, "M0001") == ["slide-1", "slide-2"]
    text = ingested_text(course, "M0001")
    assert "**Heaps**" in text and "A heap is a tree" in text
    assert "draw it on the board" in text  # speaker notes are kept
    assert records(course)["M0001"]["title"] == "Heaps"
    assert records(course)["M0001"]["kind"] == "slides"


def test_pdf_has_one_anchor_per_page(course: Path):
    make_pdf(source(course) / "chapter.pdf", ["Binary heaps", "Heap sort", "Priority queues"])
    run(course)

    assert anchors_of(course, "M0001") == ["page-1", "page-2", "page-3"]
    assert "Heap sort" in ingested_text(course, "M0001")
    assert records(course)["M0001"]["status"] == "ingested"


def test_docx_anchors_are_its_own_headings(course: Path):
    make_docx(source(course) / "hw.docx", [("h1", "Homework 1"), ("p", "Answer all."),
                                           ("h2", "Question 1"), ("p", "Prove it."),
                                           ("h2", "Question 1")])
    run(course)
    # A repeated heading is numbered as GitHub's renderer does, so a preview shows the same anchor.
    assert anchors_of(course, "M0001") == ["homework-1", "question-1", "question-1-1"]


def test_markdown_anchors_ignore_headings_inside_code(course: Path):
    (source(course) / "notes.md").write_text(
        "# Notes\n\n## Amortized analysis\n\n```python\n# not a heading\n```\n", encoding="utf-8")
    run(course)
    assert anchors_of(course, "M0001") == ["notes", "amortized-analysis"]


def test_plain_text_has_no_anchors_and_invents_none(course: Path):
    (source(course) / "readme.txt").write_text("Reading list\n# not a heading\n", encoding="utf-8")
    run(course)
    assert anchors_of(course, "M0001") == []
    assert records(course)["M0001"]["status"] == "ingested"


def test_the_ingested_file_carries_the_specified_front_matter(course: Path):
    make_pdf(source(course) / "chapter.pdf", ["Binary heaps"])
    run(course)
    front, _body = parse_front_matter(ingested_text(course, "M0001"))
    record = records(course)["M0001"]
    assert front == {"id": "M0001", "title": record["title"], "format": "pdf",
                     "canonical": "chapter.pdf", "source_hash": record["source_hash"]}


def test_a_scanned_pdf_is_no_text_but_its_pages_are_anchored(course: Path):
    make_pdf(source(course) / "scan.pdf", ["", ""])
    run(course)
    record = records(course)["M0001"]
    assert record["status"] == "no-text"
    assert "OCR" in record["status_reason"]
    assert anchors_of(course, "M0001") == ["page-1", "page-2"]


def test_unknown_formats_are_recorded_unsupported_never_dropped(course: Path):
    (source(course) / "grades.xyz").write_bytes(b"\x00\x01")
    (source(course) / "lecture.mp4").write_bytes(b"\x00\x00")
    run(course)
    by_source = {r["canonical"]: r for r in load(course)}
    assert by_source["grades.xyz"]["status"] == "unsupported"
    assert "export it to PDF" in by_source["grades.xyz"]["status_reason"]
    assert by_source["lecture.mp4"]["status"] == "media"
    assert ingest.ingested_file(course, by_source["grades.xyz"]["id"]) is None


def test_a_pandoc_format_without_pandoc_says_how_to_fix_it(course: Path, monkeypatch):
    monkeypatch.setattr(extract, "pandoc", lambda: None)
    (source(course) / "notes.odt").write_bytes(b"PK\x03\x04 not really")
    run(course)
    record = load(course)[0]
    assert record["status"] == "unsupported"
    assert "install pandoc" in record["status_reason"]


def test_a_corrupt_file_is_unsupported_not_fatal(course: Path):
    (source(course) / "broken.pptx").write_bytes(b"this is not a zip file")
    make_pdf(source(course) / "fine.pdf", ["Still converted"])
    run(course)
    by_source = {r["canonical"]: r for r in load(course)}
    assert by_source["broken.pptx"]["status"] == "unsupported"
    assert by_source["fine.pdf"]["status"] == "ingested"


def test_a_format_is_added_by_registering_one_extractor(course: Path, monkeypatch):
    monkeypatch.setitem(extract.EXTRACTORS, ".foo", extract.Extractor(
        lambda path: extract.Extraction(extract.INGESTED, body="## Part 1\n\nfoo\n", title="Foo"),
        lambda path: extract.Probe(),
    ))
    (source(course) / "x.foo").write_text("whatever", encoding="utf-8")
    run(course)
    assert anchors_of(course, "M0001") == ["part-1"]


# -- the manifest: stable ids, incremental, resumable ---------------------------

def test_the_manifest_conforms_to_its_schema(course: Path):
    make_pptx(source(course) / "deck.pptx", [("A", "a")])
    make_pdf(source(course) / "scan.pdf", [""])
    (source(course) / "clip.mp4").write_bytes(b"\x00")
    links.add_url(source(course), "https://example.org/x", "a note")
    run(course)
    schema = json.loads((FRAMEWORK_ROOT / "schemas" / "manifest.schema.json").read_text())
    jsonschema.validate(load(course), schema)


def test_a_second_run_converts_nothing(course: Path):
    make_pptx(source(course) / "deck.pptx", [("A", "a")])
    run(course)
    before = snapshot(course / "materials")

    report = run(course)

    assert report.converted == [] and report.plan.outstanding() == []
    assert snapshot(course / "materials") == before


def test_a_changed_source_is_reconverted_under_the_same_id(course: Path):
    deck = source(course) / "deck.pptx"
    make_pptx(deck, [("A", "a")])
    run(course)
    make_pptx(deck, [("A", "a"), ("B", "b")])

    report = run(course)

    assert [c.id for c in report.converted] == ["M0001"]
    assert anchors_of(course, "M0001") == ["slide-1", "slide-2"]


def test_a_renamed_file_keeps_its_id(course: Path):
    make_pptx(source(course) / "lecture3.pptx", [("Heaps", "h")])
    run(course)
    (source(course) / "lecture3.pptx").rename(source(course) / "03-heaps.pptx")

    report = run(course)

    assert report.plan.moved == [("M0001", "lecture3.pptx", "03-heaps.pptx")]
    assert list(records(course)) == ["M0001"]
    assert records(course)["M0001"]["canonical"] == "03-heaps.pptx"


def test_a_file_moved_into_a_subdirectory_keeps_its_id(course: Path):
    make_pdf(source(course) / "ch6.pdf", ["Heaps"])
    run(course)
    (source(course) / "textbook").mkdir()
    (source(course) / "ch6.pdf").rename(source(course) / "textbook" / "ch6.pdf")

    run(course)

    assert records(course)["M0001"]["sources"] == ["textbook/ch6.pdf"]


def test_a_removed_source_is_marked_not_deleted(course: Path):
    make_pdf(source(course) / "old.pdf", ["Old"])
    run(course)
    (source(course) / "old.pdf").unlink()

    run(course)

    record = records(course)["M0001"]
    assert record.get("removed_at")
    assert ingest.ingested_file(course, "M0001") is not None  # the derived file is kept too


def test_ids_are_never_reused(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    (source(course) / "a.pdf").unlink()
    run(course)
    make_pdf(source(course) / "b.pdf", ["B"])

    run(course)

    assert sorted(records(course)) == ["M0001", "M0002"]


def test_a_removed_file_put_back_gets_its_id_back(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    data = (source(course) / "a.pdf").read_bytes()
    (source(course) / "a.pdf").unlink()
    run(course)
    (source(course) / "restored.pdf").write_bytes(data)

    run(course)

    record = records(course)["M0001"]
    assert not record.get("removed_at") and record["sources"] == ["restored.pdf"]


def test_an_interrupted_run_resumes_where_it_stopped(course: Path, monkeypatch):
    for name in ("a", "b", "c"):
        make_pdf(source(course) / f"{name}.pdf", [f"Material {name}"])
    real = extract.extract
    calls = []

    def dies_on_the_second(path):
        calls.append(path.name)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return real(path)

    monkeypatch.setattr(extract, "extract", dies_on_the_second)
    with pytest.raises(KeyboardInterrupt):
        run(course)
    assert [r["canonical"] for r in load(course)] == ["a.pdf"]  # saved before the interruption

    monkeypatch.setattr(extract, "extract", real)
    report = run(course)

    assert sorted(c.path for c in report.converted) == ["b.pdf", "c.pdf"]
    assert sorted(records(course)) == ["M0001", "M0002", "M0003"]


def test_an_orphaned_ingested_file_is_adopted_not_duplicated(course: Path):
    """A run that wrote M0001's .md but died before saving the manifest leaves an orphan; the
    next run must reuse M0001 rather than mint M0002 beside it."""
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    (course / "materials" / "manifest.yaml").unlink()

    run(course)

    assert list(records(course)) == ["M0001"]
    assert len(list((course / "materials" / "ingested").glob("M*.md"))) == 1


# -- hand edits are preserved -----------------------------------------------------

def hand_edit(course: Path, material_id: str) -> Path:
    path = ingest.ingested_file(course, material_id)
    path.write_text(path.read_text(encoding="utf-8") + "\nFixed by the teacher.\n", encoding="utf-8")
    return path


def test_a_hand_edit_survives_a_rerun(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    edited = hand_edit(course, "M0001")
    run(course)
    assert "Fixed by the teacher." in edited.read_text(encoding="utf-8")


def test_a_hand_edit_is_refused_when_its_source_changes(course: Path, capsys):
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    edited = hand_edit(course, "M0001")
    make_pdf(source(course) / "a.pdf", ["A, revised"])

    code = main(["ingest", "--no-fetch", "--course", str(course)])

    assert code == 3  # "ask the teacher", as `classkit write` signals it
    assert "Fixed by the teacher." in edited.read_text(encoding="utf-8")
    assert "REFUSED" in capsys.readouterr().out
    # Still outstanding: the source has not been converted.
    assert ("M0001", "source changed since it was last converted") in ingest.reconcile(
        course, load(course), ingest.scan(course), links.read(source(course)))[1].pending


def test_the_teacher_may_replace_a_hand_edit(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    edited = hand_edit(course, "M0001")
    make_pdf(source(course) / "a.pdf", ["A, revised"])

    report = run(course, overwrite=["M0001"])

    assert report.refused == []
    text = edited.read_text(encoding="utf-8")
    assert "A, revised" in text and "Fixed by the teacher." not in text


def test_the_teacher_may_keep_a_hand_edit(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    edited = hand_edit(course, "M0001")
    make_pdf(source(course) / "a.pdf", ["A, revised"])

    report = run(course, keep=["M0001"])

    assert report.kept == ["M0001"]
    assert "Fixed by the teacher." in edited.read_text(encoding="utf-8")
    assert run(course).plan.outstanding() == []  # no longer nagging


# -- duplicates ---------------------------------------------------------------------

def test_exact_duplicates_merge_without_asking(course: Path):
    make_pdf(source(course) / "ch6.pdf", ["Heaps"])
    (source(course) / "copies").mkdir()
    (source(course) / "copies" / "ch6 (1).pdf").write_bytes((source(course) / "ch6.pdf").read_bytes())

    run(course)

    assert list(records(course)) == ["M0001"]
    assert sorted(records(course)["M0001"]["sources"]) == ["ch6.pdf", "copies/ch6 (1).pdf"]


def test_a_later_identical_copy_joins_the_existing_material(course: Path):
    make_pdf(source(course) / "ch6.pdf", ["Heaps"])
    run(course)
    (source(course) / "again.pdf").write_bytes((source(course) / "ch6.pdf").read_bytes())

    report = run(course)

    assert report.plan.duplicates == [("M0001", "again.pdf")]
    assert list(records(course)) == ["M0001"]


def test_deleting_one_copy_keeps_the_material(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    (source(course) / "b.pdf").write_bytes((source(course) / "a.pdf").read_bytes())
    run(course)
    canonical = records(course)["M0001"]["canonical"]
    (source(course) / canonical).unlink()

    run(course)

    record = records(course)["M0001"]
    assert not record.get("removed_at") and record["canonical"] != canonical


def test_a_deck_and_its_pdf_export_are_suspected_not_merged(course: Path):
    words = " ".join(f"word{n}alpha" for n in range(40))
    make_pptx(source(course) / "lecture3.pptx", [("Heaps", words)])
    make_pdf(source(course) / "lecture3.pdf", [f"Heaps {words}"])

    report = run(course)

    assert len(records(course)) == 2  # never merged without the teacher
    assert [(a, b) for a, b, _why in report.suspected_duplicates] == [("M0001", "M0002")]


def test_same_content_under_different_names_is_suspected(course: Path):
    """The content check, not the name check: a PDF export saved under another name."""
    words = " ".join("w" + "".join(chr(97 + int(d)) for d in str(n)) + "x" for n in range(40))
    make_pptx(source(course) / "lecture3.pptx", [("Heaps", words)], notes={1: "speaker only"})
    make_pdf(source(course) / "handout-for-students.pdf", [words])

    report = run(course)

    assert len(report.suspected_duplicates) == 1
    assert "words appear in the other" in report.suspected_duplicates[0][2]


def test_a_confirmed_duplicate_is_merged_and_its_id_retired(course: Path):
    make_pptx(source(course) / "lecture3.pptx", [("Heaps", "h")])
    make_pdf(source(course) / "lecture3.pdf", ["Heaps h"])
    run(course)
    deck, pdf = (r["id"] for r in sorted(load(course), key=lambda r: r["format"] != "pptx"))

    ingest.merge(course, pdf, into=deck)
    report = run(course)

    merged = records(course)
    assert merged[pdf]["merged_into"] == deck
    assert sorted(merged[deck]["sources"]) == ["lecture3.pdf", "lecture3.pptx"]
    assert merged[deck]["canonical"] == "lecture3.pptx"  # anchors stay the deck's slides
    assert report.plan.outstanding() == []


# -- links ---------------------------------------------------------------------------

def test_the_scaffolded_links_file_has_no_links_and_no_complaints(course: Path):
    parsed = links.read(source(course))
    assert parsed.links == [] and parsed.rejected == []


def test_add_url_appends_a_line_with_its_note(course: Path):
    before = (source(course) / "links.md").read_text(encoding="utf-8")
    links.add_url(source(course), "https://www.youtube.com/watch?v=abc", "heaps, 12 min")
    after = (source(course) / "links.md").read_text(encoding="utf-8")
    assert after.startswith(before)  # appended; nothing rewritten
    assert after.endswith("https://www.youtube.com/watch?v=abc — heaps, 12 min\n")


@pytest.mark.parametrize("url", ["notaurl", "ftp://example.org/x", "https://", "https://exa mple.org"])
def test_add_url_rejects_a_malformed_url(course: Path, url: str):
    with pytest.raises(links.BadURL):
        links.add_url(source(course), url)


def test_add_url_rejects_a_url_already_listed(course: Path, capsys):
    links.add_url(source(course), "https://example.org/heaps")
    code = main(["add-url", "https://EXAMPLE.org/heaps/", "--course", str(course)])
    assert code == 2
    assert "already listed" in capsys.readouterr().err


def test_a_link_whose_metadata_cannot_be_fetched_is_still_recorded(course: Path):
    links.add_url(source(course), "https://www.youtube.com/watch?v=abc", "heaps explained")
    run(course, fetch=True)  # urlopen raises in every test
    record = load(course)[0]
    assert record["status"] == "link" and record["kind"] == "video"
    assert record["title"] == "heaps explained" and record["note"] == "heaps explained"


def test_fetched_metadata_is_recorded_when_available(course: Path, monkeypatch):
    monkeypatch.setattr(links, "fetch_metadata", lambda url: links.Metadata("Binary heap", "12:03"))
    links.add_url(source(course), "https://www.youtube.com/watch?v=abc")
    run(course, fetch=True)
    record = load(course)[0]
    assert (record["title"], record["duration"]) == ("Binary heap", "12:03")


def test_links_inside_documents_are_recorded_with_where_they_were_found(course: Path):
    make_pptx(source(course) / "deck.pptx", [("A", "a"), ("B", "b")],
              link=(2, "https://en.wikipedia.org/wiki/Heap"))
    run(course)
    link = next(r for r in load(course) if r["format"] == "url")
    assert link["found_in"] == "M0001#slide-2"
    assert link["sources"] == ["https://en.wikipedia.org/wiki/Heap"]


def test_a_link_removed_from_links_md_is_marked_removed(course: Path):
    links.add_url(source(course), "https://example.org/heaps")
    run(course)
    path = source(course) / "links.md"
    path.write_text(path.read_text(encoding="utf-8").replace("https://example.org/heaps\n", ""),
                    encoding="utf-8")
    run(course)
    assert load(course)[0].get("removed_at")


def test_a_non_link_line_in_links_md_is_reported_not_guessed(course: Path):
    (source(course) / "links.md").write_text("good stuff about heaps\nhttps://example.org/a — ok\n",
                                             encoding="utf-8")
    parsed = links.read(source(course))
    assert [link.url for link in parsed.links] == ["https://example.org/a"]
    assert parsed.rejected == [(1, "good stuff about heaps")]


# -- the guarantees -----------------------------------------------------------------

def test_ingest_never_modifies_source(course: Path):
    make_pptx(source(course) / "deck.pptx", [("A", "a")])
    make_pdf(source(course) / "chapter.pdf", ["B"])
    make_docx(source(course) / "hw.docx", [("h1", "C")], link="https://example.org/c")
    (source(course) / "x.xyz").write_bytes(b"\x00")
    links.add_url(source(course), "https://example.org/d")
    before = snapshot(source(course))

    run(course)
    (source(course) / "chapter.pdf").rename(source(course) / "renamed.pdf")
    before["renamed.pdf"] = before.pop("chapter.pdf")
    run(course)

    assert snapshot(source(course)) == before


def test_preflight_writes_nothing(course: Path, capsys):
    make_pptx(source(course) / "deck.pptx", [("A", "a"), ("B", "b")])
    make_pdf(source(course) / "deck.pdf", ["A", "B"])
    make_pdf(source(course) / "scan.pdf", ["", "", ""])
    (source(course) / "x.xyz").write_bytes(b"\x00")
    (source(course) / "y.xyz").write_bytes(b"\x00")  # identical to x.xyz
    before = snapshot(course)

    code = main(["ingest", "--preflight", "--no-fetch", "--course", str(course)])

    out = capsys.readouterr().out
    assert code == 0 and snapshot(course) == before
    assert "2 slides, 5 PDF pages" in out
    assert "x.xyz = y.xyz" in out  # exact duplicates
    assert "deck.pdf ~ deck.pptx" in out  # suspected
    assert "Cannot be read" in out and "Estimated time" in out


def test_preflight_on_an_empty_source_says_so(course: Path, capsys):
    main(["ingest", "--preflight", "--course", str(course)])
    assert "materials/source/ is empty" in capsys.readouterr().out


def test_classify_records_kind_and_units_through_classkit(course: Path):
    make_pdf(source(course) / "final-2024.pdf", ["Exam"])
    run(course)

    code = main(["material", "set", "M0001", "--kind", "exam", "--unit", "U03", "--unit", "U04",
                 "--course", str(course)])

    assert code == 0
    assert (records(course)["M0001"]["kind"], records(course)["M0001"]["units"]) == ("exam", ["U03", "U04"])


def test_a_teachers_correction_in_the_manifest_survives_a_rerun(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    ingest.set_fields(course, "M0001", kind="textbook", title="CLRS chapter 6")
    make_pdf(source(course) / "a.pdf", ["A, revised"])
    run(course)
    assert (records(course)["M0001"]["kind"], records(course)["M0001"]["title"]) == ("textbook", "CLRS chapter 6")


def test_set_rejects_an_unknown_material_or_kind(course: Path):
    with pytest.raises(ingest.MaterialError):
        ingest.set_fields(course, "M0099", kind="exam")
    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    with pytest.raises(ingest.MaterialError):
        ingest.set_fields(course, "M0001", kind="lecture")


def test_the_classifying_agent_cannot_write_files():
    """Invariant 5: an agent with Write or Edit can bypass the write path entirely."""
    agent = (FRAMEWORK_ROOT / ".claude" / "agents" / "material-classifier.md").read_text(encoding="utf-8")
    front = yaml.safe_load(agent.split("---")[1])
    tools = {t.strip() for t in front["tools"].split(",")}
    assert not tools & {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def test_installing_a_converter_later_retries_the_file(course: Path, monkeypatch):
    monkeypatch.setattr(extract, "pandoc", lambda: None)
    (source(course) / "notes.odt").write_bytes(b"PK\x03\x04")
    run(course)
    assert run(course).plan.pending == []  # no converter: nothing to retry, nothing to nag about

    monkeypatch.setattr(extract, "pandoc", lambda: "/usr/bin/pandoc")
    plan = ingest.reconcile(course, load(course), ingest.scan(course), links.read(source(course)))[1]
    assert plan.pending == [("M0001", "a converter for it is now available")]
