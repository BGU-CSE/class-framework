# Implementation gap report — step 2c-2 (the rest of the hand test's fixes, and D-041)

**Date:** 2026-10-01
**Implementer:** Claude Opus 5.5, working from `FRAMEWORK-SPEC.md` (§5.1, §7, §8.2, §8.4, §8.6,
§8.7), both `CLAUDE.md` files, `VISION.md`, `ROADMAP.md`, `_devlog/04-handoff.md`,
`reviews/manual-test-step-0-2b.md` and `reviews/impl-gaps-step-2c-1.md`. I did not need the decision
log: the spec and the ledger rows were enough for every item.
**Scope built:** every ledger row tagged **[2c-2]** in the D-040 and D-041 blocks, in four groups:

1. **D-041.** The self-certifying full text (`body_hash`; `private_text_hash` retired), the `doctor`
   note on a differing copy, `course_gitignore_missing`, `write.remove()`, kept permissions, the
   `mode developer` tracking check, `.DS_Store`.
2. **Removals (D-040).** Suspected-duplicate detection, the `material duplicates` verb and the
   gate-3 question; link harvesting (`found_in` retired).
3. **Additions (D-040).** `units: all`, the scoped coverage report saved to
   `materials/coverage.md`, `material_locator_in_text`, the refusal diff by anchor,
   `classkit write --diff`, path kinds `slides` and `notes`, and the classifier's mentions.
4. **The plain fixes.** F-01, F-02, F-03/F-09/F-10, F-06 + F-08, F-07, F-12, F-14, F-18, F-20, F-23,
   F-25, F-27.

**289 tests, green** (+56). New file `tests/test_extraction_quality.py`; the rest extend the existing
files. Six commits: five for the four groups (group 1 in two), plus the record.

Every entry below is a point where the spec did not settle the answer and I decided. **⚑ = needs a
decision from the author**, with its cost. Entries marked "spec updated" are already written into
`FRAMEWORK-SPEC.md`.

**Verdict on the self-containment claim.** For *what* to build, the spec was sufficient on every
row. It ran out in three predictable places:

- **Upgrades of existing courses.** The spec describes a course ingested under the new rules. It
  does not say what happens to a manifest and `ingested/` files written under the old ones:
  harvested links, `private_text_hash`, titles, old extractions (G-1, G-5, G-14).
- **Thresholds.** "Far smaller than its source" and the time estimate are qualitative (G-9, G-16).
- **One claim that was not true of the code.** "A link inside a deck is already readable in the
  deck's ingested text": hyperlinks were not in the text (G-6).

---

## ⚑ Needs a decision

### G-1. Links harvested by an earlier version, in an existing manifest (§8.7 `links.md`, `found_in`) — ⚑

**What the spec doesn't say.** It retires `found_in` "so a manifest written before D-040 still
validates". It does not say what becomes of those link materials. Avin's manifest has eleven
(M0011–M0021), ten from the book's bibliography and one the course Gem.

**Decided.**
- The next ingest marks a harvested link **removed** unless `links.md` lists it, like any unlisted
  link. The run report gives it its own line ("a link found inside a material, not in links.md —
  links come only from links.md now; `classkit add-url` brings it back under this id"), and the log
  entry records it as removed.
- `classkit add-url` for one of them **restores it under its old id** (the existing
  removed-link match), and drops its `found_in`. A locator to the Gem keeps working once it is
  listed.

**Cost.** On Avin's course the next ingest removes eleven materials in one go. Anything citing
M0021 errors until it is re-added. The alternative was to leave them, but nothing could ever remove
them then: `material remove` is for private material only, and they have no line in `links.md` to
delete.

**Spec updated** (§8.7 `links.md`). Confirm, or choose "leave them".

### G-2. A changed private source is a `note` in `doctor`, no longer an `ACTION` (§8.7, D-041) — ⚑

**What the spec says.** D-041: "`doctor` reports, as a note, when this machine's copy differs from
the one the committed index was built from". The 2c-1 `doctor` reported the same situation as an
ACTION ("source changed since it was last converted → `classkit ingest`").

**Decided.** The note replaces the ACTION, for private material only. It says what ingesting here
would do ("rebuilds the committed index from this copy — the last machine to ingest wins"), and its
fix line is conditional.

**Why.** From inside a checkout, "I updated the book" and "my copy is older" look the same. An
ACTION would tell a TA with an old PDF to overwrite the teacher's index.

**Cost.**
- The teacher who *did* update their book gets no ACTION. `doctor` exits 0, so a script gating on
  it does not notice.
- `validate` never judges private material, so nothing else flags it.

The cost is small while one person ingests, which D-041 already assumes. **Spec updated**
(§8.7 doctor paragraph).

### G-3. Re-ingest never replaces a title — including ingest's own bad ones (§8.7 `title`, F-12) — ⚑

**What the spec says.** The title is "Editable; re-ingest keeps it". F-12 fixes how a title is
*chosen*.

**The problem.** The manifest does not record whether a title is the teacher's or ingest's own. So
in an existing course, `manual.dvi` and `public.dvi` survive every re-ingest, even with
`--overwrite`. Only `classkit material set --title` or a fresh course shows the fix.

**Decided.** Unchanged. Re-ingest keeps every title, which is what the spec says. MANUAL-TESTING
tells the teacher, and recommends a fresh course for the re-test.

**Options.**
- **(a)** As is. Cost: an old course keeps its bad titles until each is set by hand.
- **(b)** Record a `title_source: ingest` marker, and let re-ingest re-derive a title that ingest
  chose. Cost: one more bookkeeping field, and a rule for when the marker is cleared (`set --title`,
  `apply` with a title, a hand edit of the manifest — the last one is undetectable).

**Recommendation:** (a). The real cost is one hand test.

---

## Decided and written into the spec

### G-4. What `body_hash` covers (§8.7 private full text)

**What the spec says.** Two things that conflict:
- "`body_hash`, the hash of its body as ingest wrote it";
- "Editing the front matter itself breaks the self-check".

A hash of the body alone would not notice a front-matter edit.

**Decided.** `body_hash` is the hash of **the whole file without its own `body_hash:` line**. It is
inserted as the last front-matter line and checked as text, with no YAML round trip.

**Result.** Any edit, to the body or the front matter, breaks the match, and the file then counts as
edited (the safe direction). Tested both ways.

**Spec updated.**

### G-5. A full text written before D-041 (§8.7)

**What the spec doesn't say.** How to judge a full text that has no `body_hash`. Every full text
2c-1 wrote is one.

**Decided.**
- It is unedited if it matches the retired `private_text_hash` that its record still carries.
  Otherwise it counts as edited.
- Ingest drops `private_text_hash` from a record whenever it converts that material.
- The schema still accepts the field. Tested with a schema check on an old-style manifest.

**Spec updated.**

### G-6. Links inside materials were *not* readable in the ingested text (§8.7 `links.md`)

**What the spec says.** "A link inside a deck is already readable in the deck's ingested text."
That was false: PPTX and DOCX hyperlinks extracted as their anchor text only, so "(more)" with no
URL. The classifier could not have mentioned the course Gem.

**Decided.**
- Run and paragraph hyperlinks are written as `[text](url)`.
- A PPTX shape's click action, and a PDF's URI link annotation that is not already in the page's
  text, are written as `*(link: url)*`.
- Never recorded as materials.

**Spec updated** (`links.md` paragraph and the extension-point line).

### G-7. The extractor contract lost `links` (§8.7 "Adding a format")

**What changed.** The spec named "the links found" as part of what an extractor returns.
`Extraction.links`, `Probe.links` and every URL-finding helper are gone with harvesting.

**Spec updated.**

### G-8. `course_gitignore_missing` details (§8.4, §8.7)

**Decided.**
- **Where it reports.** Against `course/.gitignore`. It has no front matter, so the rule is adjusted
  course-wide with `rules:`.
- **How it reads the file.** By line: comments are ignored, and a leading `/` or a missing trailing
  `/` is accepted.
- **What it reports.** One finding naming whichever of the two paths is missing.
- **What it cannot see.** Negation rules elsewhere. `doctor` asks git.

**Spec updated** (rules table).

### G-9. "Far smaller than its source" — the low-yield measure (§8.7 Extraction quality, F-06/F-08)

**What the spec doesn't say.** Any threshold.

**Decided.**
- **DOCX and PPTX:** text characters per byte of the document's own XML (`word/document.xml`,
  `ppt/slides/slide*.xml`), so pictures do not count. Flagged under **0.005**, once the XML is over
  **20 KB**. Ordinary documents run about 0.02–0.1. The hand test's syllabus was 13 characters.
- **PDF:** its empty pages count instead, and a scan is `no-text` already.
- **What counts as empty.** An empty slide has no text at all: no title, body, table or notes. A
  title-only slide is not empty. An empty page has no non-blank character.

**Confidence: low on the numbers.** They come from reasoning about OOXML, not measured on real
files beyond the one example. The re-test is where they are tuned.

**Spec updated.**

### G-10. Library noise (§8.7, F-03/F-10)

**Decided.**
- **What is captured.** The loggers `pypdf`, `PyPDF2`, `pptx`, `docx` and `fontTools`, and Python
  `warnings`, during both extraction and the pre-flight probe.
- **What is reported.** Every message is counted. The first is shown, cut to one line of 120
  characters (pypdf's can dump a whole font dictionary).
- **Where.** In the pre-flight ("Read with warnings from the reader") and in the run summary ("Check
  these extractions"), once per file.

**Tested** with a real malformed PDF (a broken `startxref`): nothing on stderr, and the warning is
named in the report.

**Spec updated.**

### G-11. Equations (§8.7, F-07)

**Decided.**
- **Form.** Linear text in a code span, so `^` and `_` are not read as Markdown: `` `(n)/(2)+x^(2)` ``.
- **Elements.** A practical subset of Office Math: fraction, super- and subscripts, radical, n-ary,
  delimiters, function, limits, accent/bar, matrix and equation array. Anything else contributes its
  text. An equation with no text becomes `[equation]`.
- **PPTX.** The equation in `mc:AlternateContent`'s `Choice` (`a14:m`), else the `Fallback`'s text.
- **DOCX.** `m:oMath` and `m:oMathPara` in a paragraph.

**Spec updated.**

### G-12. DOCX text boxes, exactly (§8.7, F-06)

**Decided.**
- A text box's paragraphs follow the paragraph that anchors it.
- Only the outermost `w:txbxContent` is read; a box inside a box is reached by recursion.
- From `mc:AlternateContent`, the `Fallback` is read only when the `Choice` has no text box.
  "Never both" is tested.

**Not done** (no row asked for them): text boxes inside table cells, headers, footers, footnotes.

**Incidental.** Paragraph text now also includes runs inside tracked insertions (`w:ins`), smart tags,
content controls and simple fields. python-docx's `paragraph.text` dropped them. This changes the
extraction of documents with tracked changes, for the better.

### G-13. `material_locator_in_text`: what counts as a locator in prose (§8.4, §8.7)

**Decided.**
- **What is read.** Only **anchored** locators (`M0007#slide-3`), as the spec's wording says. A bare
  `M0007` in a sentence is not checked.
- **What is skipped.** HTML comments, where templates keep their instructions. **Code spans are not
  skipped**, because agents write locators in backticks.
- **Which files.** The bodies of every front-matter document (syllabus, units, sessions, in-class,
  items) and `materials/coverage.md`.
- **Reporting.** Each distinct locator once per file. It shares one resolution function with
  `material_locator_resolves`, so the two cannot disagree.

**Spec updated.**

### G-14. Existing extractions are not refreshed by an upgrade (§8.7)

**What the spec doesn't say.** Whether a framework upgrade re-converts. It does not: an unchanged
source is never re-converted. `--overwrite ID` re-converts one material (it already did), and F-27's
note tells the teacher when to use it.

**Recorded** in MANUAL-TESTING and GETTING-STARTED. No spec change: the spec's "only new or changed"
already implies it.

### G-15. The refusal diff (§8.7, F-24)

**Decided.**
- **What is compared.** The current file against the fresh extraction, section by section under each
  anchor. The front matter and the opening note are left out.
- **Display.** An anchor present on only one side is labelled. At most 10 anchors of 14 lines each
  are shown, with a count of the rest.
- **Scope.** The same for a full text's refusal. An index's refusal shows only labels, since it has
  no body.

**Spec updated.**

### G-16. Smaller decisions, each recorded

- **`write.remove()`.**
  - A missing file is `unchanged`, a directory is refused, and `dry_run` is supported.
  - It has no CLI verb (tested).
  - The caller computes the expected hash after the full text has certified itself, and `remove()`
    re-checks it at deletion time.
- **Permissions.**
  - A replaced file keeps its mode; a new file gets `0666 & ~umask`.
  - The umask is read with `os.umask` twice, which is not thread-safe. That is fine for a CLI.
- **`write --diff`.**
  - It always exits 0, says "unchanged" for identical content, and prints a one-line message for an
    unreadable file.
  - With `--append`, the diff still describes an overwrite.
- **`mode developer`.**
  - "Tracked" means in git's index (`git add` is enough).
  - It is checked only inside a repository, after the ignore check passes.
- **`units: all`.**
  - It is accepted as the string or as `[all]` (from `--unit all`). Mixing it with unit ids is
    refused, and a merge with an `all` side yields `all`.
  - `core.units_of()` expands it, but no code consumer exists yet: the designers and the step-3
    re-map are prompts. The root `CLAUDE.md` tells agents.
- **`materials/coverage.md`.**
  - It is plain Markdown with no front matter: a dated heading and a "Materials covered:" line.
    Nothing checks that heading.
  - `/ingest` writes it with `classkit write`; on a refusal it shows `--diff` and asks.
- **Path kinds.** `slides` and `notes` are added to the per-goal path enum, which is the field that
  exists today. `kind` stays required; "optional for a locator" is step 4. The row is 🔨 for that
  half.
- **F-12.**
  - A metadata title is rejected as a file name when it is one token ending in a document extension
    (`dvi`, `tex`, `pdf`, …), or when it is a path.
  - A plain-text file is still titled by its first line (the spec's rule names PDFs), except a
    private one.
  - The file-name fallback reads `_` as a space everywhere, media and unsupported files included.
- **F-14.** 0.07 s per PDF page and 0.03 s per slide, from one data point (2141 pages in 126 s CPU,
  before fontTools), and the estimate now says "(rough)".
- **F-23.** Up to 15 items per kind (new, link, changed, moved, removed, back), then "… and N more".
- **F-25.** *Awaiting* means the source changed **and** the ingested file differs from
  `ingested_hash`. Private material is excluded, since `validate` does not judge it. "Run /ingest"
  is dropped only when everything outstanding is awaiting.
- **F-02.** Plurals in the `validate` summary, the accepted-exceptions line and the ingest
  summaries. Not every message in the codebase.
- **`doctor`.** fontTools joins the fallback requirements list.

---

## Not verified — for the teacher's re-test

- **fontTools fixes F-09's broken characters** (`efûcient`, `ûrst`, `engineering4such`). That is
  the hypothesis behind the dependency. The tests check only what they can: fontTools imports,
  ligatures (`ﬁ` → `fi`) are expanded, and reader warnings never reach the terminal. **Whether CLRS
  page 40 now reads correctly can only be seen on the real book.** `MANUAL-TESTING.md`, "Step 2c-2",
  says how. If it does not, the cause is elsewhere (pypdf's text layout, or the font's own
  encoding), and the next step is a different extractor for PDFs, which is a decision.
- **The low-yield thresholds** (G-9) on real decks and documents.
- **The classifier's new behaviour** — `units: all`, the scoped report, the mentions of two-format
  relations and course-resource links — is prompt text that has not been run. Only the command and
  agent wording are tested (no duplicate question remains; "cite the deck" and `add-url` are there).

## Not built (out of scope, untouched)

Every row tagged [step 3], [step 4] or [Exports]: the syllabus `unit_map`, `unit_map_mismatch` and
`/plan-units` (including reading `coverage.md`), the full resource-kind vocabulary, `answer`, and
the exporters' refusal.

Gap G-4 of step 0–1 is also still open. Agents other than the classifier keep `Write` and `Edit`,
so P-2's bypass is still possible. `--diff` now gives them a write-path way to make a partial
change.
