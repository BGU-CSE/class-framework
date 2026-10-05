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


def test_a_deck_and_its_pdf_export_stay_two_materials_and_nobody_is_asked(course: Path, capsys):
    """D-040: same material in two formats is not detected. Both are valid to cite; asking about
    it at every run cost more than the problem — the hand test's 13 suspected pairs were all false."""
    words = " ".join(f"word{n}alpha" for n in range(40))
    make_pptx(source(course) / "lecture3.pptx", [("Heaps", words)])
    make_pdf(source(course) / "lecture3.pdf", [f"Heaps {words}"])

    main(["ingest", "--preflight", "--no-fetch", "--course", str(course)])
    report = run(course)
    main(["ingest", "--no-fetch", "--course", str(course)])

    out = capsys.readouterr().out
    assert len(records(course)) == 2  # never merged
    assert not hasattr(report, "suspected_duplicates")
    assert "uspected" not in out and "~" not in out
    assert not hasattr(ingest, "suspected_duplicates")


def test_the_duplicates_verb_is_gone(course: Path):
    with pytest.raises(SystemExit):
        main(["material", "duplicates", "--course", str(course)])


def test_ingest_asks_no_duplicate_question():
    """D-040: the gate-3 duplicate question is gone from the command and the agent."""
    command = (FRAMEWORK_ROOT / ".claude" / "commands" / "ingest.md").read_text(encoding="utf-8")
    agent = (FRAMEWORK_ROOT / ".claude" / "agents" / "material-classifier.md").read_text(encoding="utf-8")
    assert "material duplicates" not in command and "suspected" not in command.lower()
    assert "suspected" not in agent.lower() and "proposed merges" not in agent.lower()
    assert "cite the deck" in agent and "add-url" in agent


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


def test_links_inside_documents_are_not_harvested_but_stay_readable(course: Path):
    """D-040: a link becomes a material only when the teacher lists it. One inside a deck or a
    document is kept, as a Markdown link, in that material's ingested text."""
    make_pptx(source(course) / "deck.pptx", [("A", "a"), ("B", "b")],
              link=(2, "https://gemini.google.com/gem/course-tutor"))
    make_docx(source(course) / "syllabus.docx", [("h1", "Syllabus")], link="https://example.org/ref")
    make_pdf(source(course) / "book.pdf", ["See https://arxiv.org/abs/1504.01234 for more"])

    run(course)

    assert [r for r in load(course) if r["format"] == "url"] == []
    by_format = {r["format"]: r["id"] for r in load(course)}
    assert "[ (more)](https://gemini.google.com/gem/course-tutor)" in ingested_text(course, by_format["pptx"])
    assert "[the reference](https://example.org/ref)" in ingested_text(course, by_format["docx"])
    assert "https://arxiv.org/abs/1504.01234" in ingested_text(course, by_format["pdf"])


def test_a_link_harvested_before_d040_is_retired_and_add_url_brings_it_back(course: Path):
    """An older manifest holds links found inside materials (`found_in`). Links come only from
    links.md now, so the next ingest marks them removed — and listing one restores its old id,
    so a locator citing it keeps working."""
    make_pptx(source(course) / "deck.pptx", [("A", "a")])
    run(course)
    records_ = load(course)
    records_.append({"id": "M0002", "title": "Course Gem", "kind": "link", "format": "url",
                     "status": "link", "sources": ["https://gemini.google.com/gem/x"],
                     "canonical": "https://gemini.google.com/gem/x",
                     "source_hash": ingest.core.link_hash("https://gemini.google.com/gem/x"),
                     "found_in": "M0001#slide-1"})
    ingest.manifest.save(course, records_)
    schema = json.loads((FRAMEWORK_ROOT / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(load(course), schema)  # `found_in` retired, still accepted

    report = run(course)
    assert report.plan.unharvested == ["M0002"] and records(course)["M0002"].get("removed_at")
    assert "links come only from links.md" in ingest.report.run_text(report)

    links.add_url(source(course), "https://gemini.google.com/gem/x", "course Gem")
    run(course)
    restored = records(course)["M0002"]
    assert not restored.get("removed_at") and "found_in" not in restored


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
    assert "~" not in out and "uspected" not in out  # two formats: not looked for (D-040)
    assert "embedded" not in out  # links are not harvested
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


def test_the_classifying_agent_cannot_write_or_run_anything():
    """Invariant 5, and D-039: Write or Edit bypasses the write path; Bash can write anything.
    The agent reads the most untrusted text of any agent, so it only reads and returns."""
    agent = (FRAMEWORK_ROOT / ".claude" / "agents" / "material-classifier.md").read_text(encoding="utf-8")
    front = yaml.safe_load(agent.split("---")[1])
    tools = {t.strip() for t in front["tools"].split(",")}
    assert tools <= {"Read", "Grep", "Glob"}


def test_apply_records_a_batch_of_classifications(course: Path):
    for name in ("a", "b"):
        make_pdf(source(course) / f"{name}.pdf", [name.upper()])
    run(course)

    changes = ingest.apply(course, [
        {"id": "M0001", "kind": "textbook", "units": ["u06"]},
        {"id": "m0002", "kind": "exam", "units": [], "title": "Final  2024"},
    ])

    assert [mid for mid, _ in changes] == ["M0001", "M0002"]
    assert (records(course)["M0001"]["kind"], records(course)["M0001"]["units"]) == ("textbook", ["U06"])
    assert (records(course)["M0002"]["kind"], records(course)["M0002"]["title"]) == ("exam", "Final 2024")


def test_apply_is_all_or_nothing(course: Path):
    """A typo in the last entry must not leave the first ones recorded."""
    for name in ("a", "b"):
        make_pdf(source(course) / f"{name}.pdf", [name.upper()])
    run(course)
    before = (course / "materials" / "manifest.yaml").read_text(encoding="utf-8")

    for bad in (
        {"id": "M0002", "kind": "lecture"},
        {"id": "M0099", "kind": "exam"},
        {"id": "M0002", "units": ["week 3"]},
        {"id": "M0002", "kinds": "exam"},
        {"id": "M0001", "kind": "exam"},  # a duplicate id
    ):
        with pytest.raises(ingest.MaterialError):
            ingest.apply(course, [{"id": "M0001", "kind": "textbook"}, bad])
        assert (course / "materials" / "manifest.yaml").read_text(encoding="utf-8") == before


def test_apply_reads_yaml_from_the_cli(course: Path, monkeypatch, capsys):
    import io

    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    monkeypatch.setattr("sys.stdin", io.StringIO("- id: M0001\n  kind: notes\n  units: [U02]\n"))

    assert main(["material", "apply", "--course", str(course)]) == 0
    assert records(course)["M0001"]["kind"] == "notes"

    monkeypatch.setattr("sys.stdin", io.StringIO("- id: M0001\n  kind: [oops\n"))
    assert main(["material", "apply", "--course", str(course)]) == 2


def test_apply_echoes_every_field_including_unchanged_ones(course: Path, monkeypatch, capsys):
    """Teacher test: a kind already guessed right was not echoed, so its confirmation was invisible."""
    import io

    make_pdf(source(course) / "a.pdf", ["A"])
    run(course)
    kind = records(course)["M0001"]["kind"]
    monkeypatch.setattr("sys.stdin", io.StringIO(f"- id: M0001\n  kind: {kind}\n  units: [U02]\n"))

    assert main(["material", "apply", "--course", str(course)]) == 0
    out = capsys.readouterr().out
    assert f"M0001  kind={kind} (unchanged)  units=U02\n" in out
    assert "1 material changed, 0 already so." in out


def log_text(course: Path) -> str:
    return (course / "LOG.md").read_text(encoding="utf-8")


def test_a_hand_run_that_changes_the_course_is_logged(course: Path):
    """§8.8: each ingest run is an entry — including one nobody ran through /ingest (D-039)."""
    make_pdf(source(course) / "a.pdf", ["A"])
    before = log_text(course)

    assert main(["ingest", "--no-fetch", "--course", str(course)]) == 0

    added = log_text(course)[len(before):]
    assert "classkit ingest" in added and "new M0001" in added and "run by hand" in added


def test_a_hand_run_that_changes_nothing_is_not_logged(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    main(["ingest", "--no-fetch", "--course", str(course)])
    before = log_text(course)

    main(["ingest", "--no-fetch", "--course", str(course)])

    assert log_text(course) == before


def test_ingest_run_by_the_command_does_not_log_twice(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    before = log_text(course)

    main(["ingest", "--no-fetch", "--no-log", "--course", str(course)])

    assert log_text(course) == before


def test_a_logged_run_names_removals_and_moves(course: Path):
    make_pdf(source(course) / "a.pdf", ["A"])
    make_pdf(source(course) / "b.pdf", ["B"])
    main(["ingest", "--no-fetch", "--no-log", "--course", str(course)])
    (source(course) / "a.pdf").unlink()
    (source(course) / "sub").mkdir()
    (source(course) / "b.pdf").rename(source(course) / "sub" / "b2.pdf")
    before = log_text(course)

    main(["ingest", "--no-fetch", "--why", "reorganized", "--course", str(course)])

    added = log_text(course)[len(before):]
    assert "removed M0001" in added and "moved M0002" in added and "reorganized" in added


def test_installing_a_converter_later_retries_the_file(course: Path, monkeypatch):
    monkeypatch.setattr(extract, "pandoc", lambda: None)
    (source(course) / "notes.odt").write_bytes(b"PK\x03\x04")
    run(course)
    assert run(course).plan.pending == []  # no converter: nothing to retry, nothing to nag about

    monkeypatch.setattr(extract, "pandoc", lambda: "/usr/bin/pandoc")
    plan = ingest.reconcile(course, load(course), ingest.scan(course), links.read(source(course)))[1]
    assert plan.pending == [("M0001", "a converter for it is now available")]


# -- units: all (D-040) ------------------------------------------------------------------

def test_units_all_marks_a_course_wide_material(course: Path, monkeypatch, capsys):
    make_pdf(source(course) / "book.pdf", ["Heaps"])
    make_pdf(source(course) / "notes.pdf", ["Sorting"])
    run(course)
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO("- id: M0001\n  units: all\n"))
    assert main(["material", "apply", "--course", str(course)]) == 0
    assert main(["material", "set", "M0002", "--unit", "all", "--course", str(course)]) == 0
    assert records(course)["M0001"]["units"] == "all" == records(course)["M0002"]["units"]
    schema = json.loads((FRAMEWORK_ROOT / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(load(course), schema)
    assert ingest.core.units_of(records(course)["M0001"], ["U01", "U02"]) == ["U01", "U02"]


def test_units_all_cannot_be_mixed_with_unit_ids(course: Path):
    make_pdf(source(course) / "book.pdf", ["Heaps"])
    run(course)
    with pytest.raises(ingest.MaterialError, match="use it alone"):
        ingest.apply(course, [{"id": "M0001", "units": ["all", "U03"]}])
    with pytest.raises(ingest.MaterialError, match="unit ids look like U03"):
        ingest.set_fields(course, "M0001", units=["every"])


# -- the hand-edit refusal shows what --overwrite would change (D-040, F-24) ---------------

def test_a_refusal_shows_the_diff_by_anchor_not_the_front_matter(course: Path, capsys):
    deck = make_pptx(source(course) / "deck.pptx", [("Intro", "a"), ("Heaps", "b"), ("Sorting", "c")])
    run(course)
    path = ingest.ingested_file(course, "M0001")
    path.write_text(path.read_text(encoding="utf-8").replace("- b", "- b, corrected by the teacher"),
                    encoding="utf-8")
    make_pptx(deck, [("Intro", "a"), ("Heaps", "b"), ("Sorting", "c, now with merge sort")])

    code = main(["ingest", "--no-fetch", "--course", str(course)])

    out = capsys.readouterr().out
    assert code == 3
    section = out[out.index("What --overwrite would change"):]
    assert "Slide 2:" in section and "- - b, corrected by the teacher" in section and "+ - b" in section
    assert "Slide 3:" in section and "+ - c, now with merge sort" in section
    assert "Slide 1:" not in section
    assert "source_hash" not in section and "id: M0001" not in section


# -- roles: scope and reference (D-048) ------------------------------------------------

def test_roles_are_recorded_by_apply_either_or_both(course: Path):
    for name in ("notes", "book"):
        make_pdf(source(course) / f"{name}.pdf", [name])
    run(course)
    ingest.apply(course, [{"id": "M0001", "roles": ["scope"]},
                          {"id": "M0002", "roles": ["reference", "scope"]}])
    assert records(course)["M0001"]["roles"] == ["scope"]
    assert records(course)["M0002"]["roles"] == ["scope", "reference"]  # a fixed order


def test_set_role_and_no_roles_from_the_cli(course: Path, capsys):
    make_pdf(source(course) / "notes.pdf", ["notes"])
    run(course)
    assert main(["material", "set", "M0001", "--role", "scope", "--course", str(course)]) == 0
    assert "roles=scope" in capsys.readouterr().out
    assert main(["material", "set", "M0001", "--no-roles", "--course", str(course)]) == 0
    assert not records(course)["M0001"].get("roles")  # absent = neither


def test_an_unknown_role_is_refused_and_nothing_is_recorded(course: Path):
    make_pdf(source(course) / "notes.pdf", ["notes"])
    run(course)
    with pytest.raises(ingest.MaterialError, match="a role is one of scope, reference"):
        ingest.apply(course, [{"id": "M0001", "roles": ["syllabus"]}])
    assert "roles" not in records(course)["M0001"]


def test_the_manifest_schema_accepts_roles(course: Path):
    from classkit.model import load_course
    from classkit.validate import validate

    make_pdf(source(course) / "notes.pdf", ["notes"])
    run(course)
    ingest.apply(course, [{"id": "M0001", "roles": ["scope", "reference"]}])
    assert not [f for f in validate(load_course(course, FRAMEWORK_ROOT), FRAMEWORK_ROOT) if f.level == "error"]
