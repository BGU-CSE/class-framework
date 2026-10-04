# Manual test — steps 0–2b (teacher hand test)

Hand test of the framework as a teacher, following `dev/MANUAL-TESTING.md`, with real materials.
**Scope: Steps 0, 1 and 2b (scaffold, write path, ingest) only** — `/plan-units` onward is known
to be unbuilt (ROADMAP steps 3–7) and was deliberately not run.

| | |
|---|---|
| Tester | Chen Avin (teacher), with Claude Code |
| Date | 2026-10-01 |
| Framework commit | `79dccac` (level with `origin/main`) |
| Environment | macOS (Darwin 24.6.0), Python 3.13.1, fresh clone in `scratch/testdrive02`, `.venv` |
| Optional tools | pandoc **not** installed; LibreOffice **not** installed |
| Course | `371-1-0341` Data Structures, BGU School of ECE, 12 units (scaffolded first with the testing doc's example `202-1-2051` / 13 units, then corrected) |
| Materials | CLRS 4e PDF (1312 pp.), CLRS 4e Instructor's Manual (746 pp.), selected solutions (83 pp.), 3 syllabus `.docx`, Unit 1–3 `.pptx` decks (37 slides), 1 link |

Severity: **bug** (built thing behaves wrongly) · **gap** (the spec does not cover it) ·
**docs** (documentation wrong or stale) · **ux** (works, but reads badly) · **note** (no action needed).

---

## Summary for the developer

**What works well.** The write path (Step 0) is solid. Scaffold validates clean. Ingest's
*mechanics* are right: stable ids, exact page anchors (all three PDFs, page count = anchor count,
printed page recorded), incremental change detection, hand-edit refusal with exit 3, the locator
rule, append-only logging, and `source/` byte-identical throughout. The **material-classifier is
the strongest part of the run** — it out-judged the tool's duplicate detector on every pair and
produced a coverage report the teacher found true of the course.

**Fix first (in this order):**
1. **F-06** — Word text boxes not extracted; the official syllabus came out as 13 characters and was
   reported `[ingested]` with no warning. Add a low-yield warning regardless of the fix.
2. **F-04 / F-16 / F-22** — no way to mark a material instructor-only; a solutions manual cited in a
   student study path validates silently. Real risk for any course that owns an instructor's manual.
3. **F-11 / F-15** — duplicate detection is size-biased (13 of 13 pairs false) and a false pair
   cannot be dismissed, so the teacher re-answers it every run.
4. **F-09 / F-10** — broken PDF characters (likely missing `fonttools`) and 180 lines of library
   warnings drowning the summary.
5. **F-19** — the coverage report is not persisted, though `/plan-units` depends on it.
6. **F-07, F-13** — equations dropped from slides; bibliography links flood the manifest.

The rest are smaller UX/docs items. Process observations about the agent's own conduct are in
their own section near the end (P-1 … P-4).

---

## Findings

### F-01 · docs · MANUAL-TESTING.md Step 1 file count is stale
- **Step:** 1 — `classkit scaffold course`
- **Expected (per doc):** 10 files created.
- **Observed:** 12 created. The additions are `course/materials/source/links.md`,
  `course/materials/ingested/.gitkeep`, and `course/LOG.md` (step 2 artifacts).
- **Also:** the header line "Every command below was run … against commit `b01ca57`" is no longer
  true of the Step 1 section.
- **Suggest:** update the count and the commit line.

### F-02 · ux · "1 units" in the validate summary
- **Step:** 1 — `classkit validate` after `scaffold unit 1`
- **Observed:** `Introduction to Data Structures — 1 units, 12 guiding questions, 0 assessment items`
- **Suggest:** pluralise ("1 unit"). Probably the same for "1 guiding questions", "1 assessment items".

### F-03 · ux · PDF library warnings leak into the pre-flight report
- **Step:** 2b — `classkit ingest --preflight`
- **Observed:** printed above the report, twice:
  ```
  Previous trailer cannot be read: ("'NumberObject' object is not subscriptable",)
  parsing for Object Streams
  ```
  These are pypdf warnings about a slightly malformed (but readable) PDF. To a teacher they read like
  a failure.
- **Suggest:** capture pypdf's logger/warnings; if a file is genuinely degraded, report it once, by
  file name, inside the report.

### F-04 · gap · No way to mark a material instructor-only
- **Step:** 2b — materials include *Cormen 4e Instructor's Manual* and *selected solutions*.
- **Observed:** the manifest records kind and units only. The only confidentiality concept in the
  design is for exam **items** (`usage`, Q-002); nothing covers **materials**. Nothing prevents an
  agent from citing the solutions manual in a student-facing study path, or a future Gem builder
  from bundling it.
- **Suggest:** a per-material audience/visibility field (e.g. `audience: instructor`), set by the
  classifier and confirmed by the teacher at gate 3; a validator rule that errors when a study path
  or Gem knowledge file cites an instructor-only material.

### F-05 · note · Copyrighted textbook extraction
- **Step:** 2b — the full CLRS PDF is in `source/`.
- **Observed:** ingest will write its full text into `ingested/`. Fine in a private course repo, but
  it becomes relevant to Q-030 (student-clonable repo) and the Gem builder, which would distribute
  derived content.
- **Suggest:** consider this alongside F-04 when designing exports.

### F-06 · bug · Word text boxes are not extracted — a whole syllabus silently lost
- **Step:** 2b — gate 2, `classkit ingest`
- **Source:** `syllabus data-structures-2026.docx` (45 KB; the official BGU course descriptor:
  module number, credits, ECTS, prerequisites, grading, lecturer…).
- **Observed:** `ingested/M0009-…md` body is the single line `eeeeeeeeeeeee`. The document's
  text is entirely inside text boxes (`w:txbxContent`, 10 of them, wrapped in
  `mc:AlternateContent`); the extractor reads only body paragraphs and tables.
- **Worse:** reported as `[ingested]` with **no warning** — nothing tells the teacher the most
  important document in the course came out empty.
- **Suggest:** (a) extract `w:txbxContent` (de-duplicating the `mc:Choice`/`mc:Fallback` copies);
  (b) a low-yield warning for any material whose extracted text is tiny relative to its source size
  (here 13 characters from 45 KB).

### F-07 · bug · Office math (OMML equations) dropped from slides
- **Step:** 2b — gate 2, `.pptx` extraction
- **Observed:** `Unit_2_Introduction.pptx` slide 7 has 30 `m:oMath` objects, slide 15 has 18;
  `Unit_1` slide 11 has 2. None appear in the ingested text (slide 7 reads only "Loop invariant:").
  For an algorithms course the equations *are* the content.
- **Suggest:** extract OMML as linear text / LaTeX (or at least a `[equation]` placeholder so the
  classifier knows something is there).

### F-08 · note · Image-only slides extract as empty headings
- **Observed:** of 37 slides, ~20 are pictures (screenshots of the book's figures/pseudocode) and come
  out as a bare `## Slide N`. Expected without OCR — but nothing in the summary says "N of 37 slides
  have no text", so the teacher cannot tell thin extraction from thin teaching.
- **Suggest:** per-material count of empty slides/pages in the ingest summary (pairs with F-06b).

### F-09 · bug · PDF text has broken characters (ligatures, dashes, quotes)
- **Source:** CLRS 4e PDF. **Observed** (`M0005#page-40`): `efûcient` (ﬁ), `ûrst`, `engineering4such`
  (em-dash → `4`), `<coded=` (curly quotes → `<` `=`). Also spurious spaces (`th e keys`, `y our`).
- **Effect:** text search for "efficient", "first", "find" misses; an agent quoting the book quotes
  garbage.
- **Likely cause:** pypdf printed 180× "fontTools is required to fully parse the encoding of a CFF
  Type1 font … but is not installed". `fontTools` is not in the project's dependencies.
- **Also:** math in PDFs is unreadable — the instructor's manual renders ⟨a₁, a₂, …, aₙ⟩ as
  `ha1; a2; : : : ; ani` and `X_ij = I{z_i is compared with z_j}` as `X ij D I f´ i …` (M0001#page-13,
  M0005#page-219). Probably not fixable in general, but worth knowing: agents cannot quote formulas.
- **Suggest:** add `fonttools` to dependencies and re-test; normalise known ligatures.

### F-10 · ux · 108 KB of warnings during ingest (F-03, much worse)
- **Observed:** `classkit ingest` printed 180 `fontTools is required…` lines, each dumping a full PDF
  font dictionary, plus the trailer warnings — ~220 lines burying a 30-line summary.
- **Suggest:** silence third-party loggers; summarise as one line per affected material.

### F-11 · bug · Duplicate detection: 12 suspected pairs, all or nearly all false
- **Observed:** containment metric "N% of the shorter one's words appear in the other". Against a
  1312-page textbook (M0005) or 746-page manual (M0001), *any* short document scores 84–98%:
  e.g. a 12-row syllabus table "duplicates" the textbook at 97%, a slide deck "duplicates" the
  instructor's manual at 96%.
- **Real relationship:** none is the same material in two formats. M0003/M0004 are two versions of
  the same plan (related, not duplicates); M0002 (selected solutions) is a subset of M0001.
- **Suggest:** compare only when sizes are comparable (e.g. length ratio within 2×), use shingles /
  Jaccard rather than vocabulary containment, and require structural agreement (slide count ≈ page
  count) for a deck/PDF pair.

### F-12 · ux · Titles from PDF metadata are meaningless
- **Observed:** `M0001 title: manual.dvi`, `M0002 title: public.dvi` — the TeX output names in the
  PDF metadata won over the file names (*Cormen_4e_Instructor's Manual*, *…selected-solutions*).
  `M0007`/`M0008` are titled "Unit 2"/"Unit 3", losing the subject in the file name.
- **Suggest:** reject metadata titles that look like file names (`*.dvi`, `*.tex`, `Microsoft Word -
  …`); prefer the file name over them.

### F-13 · gap · Links embedded in books flood the manifest
- **Observed:** 11 links recorded as course materials (M0011–M0021), 10 of them from the textbook
  and manual's front matter/bibliography: `cs.dartmouth.edu`, `lccn.loc.gov`, `csrc.nist.gov`,
  arXiv papers… None is a course resource. Two are truncated by line-wrapping:
  `http://arxiv.org/abs/1504`, `http://arxiv.org/abs/1509`.
- **The one that matters** — the course's own Gemini Gem link (M0021) from the Unit 1 deck — is
  lost among them.
- **Suggest:** don't harvest links from materials of kind textbook/reference (or put them in a
  separate, unlisted pool); detect URLs broken across lines.

### F-14 · docs · Ingest time estimate off by >2×
- **Observed:** pre-flight "about 1 minute"; actual 2 min 20 s (126 s CPU) for 2141 PDF pages.
- **Suggest:** recalibrate the per-page rate for large PDFs.

### F-15 · gap · A suspected duplicate cannot be dismissed
- **Step:** 2b — gate 3. `classkit material` has `set`, `merge`, `apply`, `duplicates` — nothing to
  record "teacher says: not the same material".
- **Effect:** the 13 false pairs (F-11) will presumably be re-listed on every `/ingest`, and the
  teacher re-answers the same question each time. (After hand-correcting M0009 a 13th pair appeared:
  M0005~M0009.)
- **Suggest:** `classkit material distinct M0003 M0004` recorded in the manifest; `duplicates`
  skips recorded pairs.

### F-16 · gap · Instructor-only status can only be smuggled into the title (follow-up to F-04)
- **Observed:** the classifier, told the solutions manual must never reach students, had no field to
  say so and proposed `kind: other` with "(INSTRUCTOR ONLY)" appended to the title — a convention no
  later agent or validator is obliged to honour. It also flagged two consequences no field captures:
  78 manual solutions are "also posted publicly" (so those exercises are unsafe as graded homework),
  and the course Gem (M0021) may have been built from the manual.
- **Suggest:** as F-04 — a real `audience` field plus a validator rule.

### F-17 · gap · `units` cannot say "course-wide"
- **Observed:** the course Gem (M0021) and the textbook serve every unit; the classifier had to choose
  between `[]` (looks like "no unit") and listing all 12 (looks like a per-unit resource).
- **Suggest:** an explicit `units: all` (or `scope: course`).

### F-18 · note · Scaffold-first order of the manual test conflicts with the real course
- MANUAL-TESTING Step 1 scaffolds `unit 1 "Asymptotic analysis"` before ingest. In this course
  asymptotic notation is Unit 3; the classifier rightly flagged the placeholder. Harmless in a test,
  but a teacher following the same order gets a wrong U01 that `/plan-units` must undo.

### F-19 · gap · The coverage report is not saved anywhere
- **Step:** 2b — gate 4. `/ingest` presents the classifier's coverage report and logs one line; the
  report itself (coverage per unit, volume check, ordering problems, open questions, proposed unit
  map) exists only in the chat transcript.
- **Effect:** `/plan-units` says it "needs to know what the course currently covers", but has
  nothing to read; the report must be regenerated or is lost when the session ends.
- **Suggest:** `/ingest` step 4 writes it through `classkit write` (e.g.
  `materials/coverage-report.md`), revised on later runs, and `/plan-units` reads it.

### F-20 · docs · Session template still says the budget check "fails"
- `templates/unit/session.md` comment: "At least one complete path … must fit inside
  duration_minutes, **or the validator fails**." Since D-037 it is a warning. (The template's
  per-goal `paths` model is itself due to change in step 4, D-020.)

### F-21 · gap · A study path cannot be of kind "slide"
- **Observed:** a path `kind: slide, ref: "M0006#slide-2"` fails the schema:
  `'slide' is not one of ['gem', 'video', 'textbook', 'article', 'exercise', 'other']`. The
  teacher's own decks — the material most likely to be cited — must be filed as `other`. Material
  kinds (`slides`) and the planned `answer` kinds (D-019: `slide`) both have it.
- **Note:** schema violations in session files print as `warn`, not `error` — confirm intended.
- **Suggest:** align path kinds with material kinds when D-020 reworks paths.

### F-22 · gap · Citing the instructor-only manual in a student study path passes silently (confirms F-04)
- **Observed:** a study path `ref: "M0001#page-13"` (the solutions manual, titled INSTRUCTOR ONLY)
  validates with no finding of any kind.

### F-23 · ux · Pre-flight says "1 changed" but not which
- **Step:** 2b — after the teacher edited `Unit_1_Algorithms.pptx`.
- **Observed:** `Since the last ingest: 0 new, 1 changed, … 8 unchanged` — no file name or id. With
  one change it is guessable; with twenty it is not.
- **Suggest:** list changed / moved / removed sources by name and id (the validator's
  `materials_not_ingested` message already does: "not converted: M0006 — source changed").

### F-24 · ux · Hand-edit refusal previews the front matter, not the edit
- **Step:** 2b — `classkit ingest` refused M0006 (exit 3) ✅, but the preview printed was the first
  lines of the file: the YAML front matter and `…`. The teacher's actual edit (slide 9) is not shown.
- **Effect:** the teacher is asked "keep or replace?" without seeing what would be lost — the very
  thing the refusal exists to show (cf. Step 0, where `classkit write` shows the existing content).
- **Suggest:** show a diff between the recorded extraction and the current file (store the original
  extraction, or regenerate it from the old source hash's cache).

### F-25 · ux · After a refusal, validate says "Run /ingest" — which refuses again
- **Observed:** `[materials_not_ingested] … not converted: M0006 — source changed … Run /ingest (or
  `classkit ingest`).` Running it repeats the refusal. The pending decision is not mentioned.
- **Suggest:** for a refused material, say "awaiting your decision: `classkit ingest --keep M0006`
  or `--overwrite M0006`".

### F-26 · gap · Locators outside schema-backed files are never checked
- **Observed:** the saved coverage report (65 locators) and `LOG.md` entries cite materials, but
  `material_locator_resolves` only reads front-matter fields of course artifacts. The first draft
  of the report also used shorthand (`#page-39` meaning `M0005#page-39`), which a reader — human or
  tool — resolves against the wrong material. Caught by a hand-written check; all 65 now resolve.
- **Suggest:** (a) define locators as always fully qualified (`M0005#page-39`) in agent
  instructions; (b) optionally scan Markdown bodies under `course/` for `M\d{4}#…` and resolve them.

### F-27 · note · A hand-corrected extraction is "hand-edited" forever
- The F-06 workaround (M0009) makes that file a teacher edit. Every future change to the source
  `.docx` will be refused until the teacher answers keep/overwrite — correct by design, but after
  F-06 is fixed the teacher will need to know to choose `--overwrite` once.

---

## Process observations — the agent's own conduct

Included so the developer can judge what prompts alone do and do not enforce.

- **P-1 · Gate approval inferred.** At `/ingest` gate 1 the teacher said "I add more sources so run
  what is needed"; the agent treated that as approval to convert rather than showing the pre-flight
  and waiting. Defensible here (conversion writes only derived files), but the command's gate is
  prompt-only (D-030 unbuilt) and was bent by a loosely worded instruction.
- **P-2 · `course.yaml` edited without the write path.** The agent edited `course.yaml` twice
  (textbook entry; course identity) with its own file tools / `sed`, not `classkit write`. Both
  edits were requested by the teacher, but they bypassed invariant 5's mechanism — exactly gap G-4
  (agents still hold `Write`/`Edit`). `classkit write` replaces whole files only, which makes a
  one-line change to a YAML file awkward through it; an "edit a key" path may be needed.
- **P-3 · Agent error, caught.** The first coverage report used shorthand locators (F-26); the
  agent's own check flagged them and the file was corrected before the teacher relied on it.
- **P-4 · Instructor-only material read in full.** The classifier necessarily read the solutions
  manual to classify it. Harmless at ingest, but it shows that "instructor only" cannot mean
  "agents never see it" — it has to mean "never cited to students" (F-04).

---

## Test coverage limits in this run

- **Not exercised:** deck + its PDF export (true-positive duplicate detection and merge), an
  unreadable format (unsupported-file report), exact-duplicate auto-merge, and **rename → "moved
  (same id)"** — the teacher chose not to add test files to `source/`. The false-positive side of
  duplicate detection *was* exercised heavily (F-11).
- pandoc and LibreOffice not installed, so their extractors were not exercised.

---

## Results log — what passed

### Step 1 — Initialize
- `scaffold course` → `validate`: **0 errors**, 2 expected warnings (`syllabus_workload_missing`,
  `unit_count`). ✅
- `scaffold unit 1 --title "Asymptotic analysis"`: 6 files, 0 errors, 12 `guiding_question_assessed`
  warnings (documented noise). ✅
- Re-run: `0 created, 6 left untouched`. ✅

### Step 0 — Overwrite-safe write path
- A created/0 · **B refused/3, original intact, refusal shows existing content** · C dry-run
  refused/3 · D `--overwrite` replaced/0 · E identical → unchanged/0. ✅ All five as specified.

### Step 2b — Ingest
- `add-url "not a url"` → rejected, exit 2. ✅
- `add-url <MIT Press CLRS page> --note "…"` → appended to `links.md`; `validate` then reports
  `materials_not_ingested` for the new link. ✅
- Textbook recorded in `course.yaml` `textbooks:` as `CLRS` with `url`; validates. ✅
- `ingest --preflight`: 6 files (3 docx, 3 pdf, 15.7 MB), 2141 PDF pages, 1 link + 4 embedded,
  no duplicates, nothing unsupported, estimate "about 1 minute"; wrote nothing. ✅ (but see F-03)
- Source snapshot taken (`shasum` of every file) for the after-ingest integrity diff.
- Second pre-flight after adding 3 `.pptx` decks: 9 files (3 docx, 3 pdf, 3 pptx), 37 slides,
  2141 pages, 6 embedded links, 10 materials to convert. ✅
- Gate 2 `classkit ingest --no-log`: exit 0, 21 new materials (M0001–M0009 files, M0010 the
  `links.md` link, M0011–M0021 embedded links), 0 refused. Ids stable and sequential. ✅
  Content problems: F-06 … F-14.
- F-06 workaround: text-box content recovered by script into `ingested/M0009-…md` through
  `classkit write --overwrite` (7.2 KB, faithful). `validate` silent on it (source unchanged). ✅
- `classkit log` for conversion + course-identity change: entries well-formed in `LOG.md`. ✅
- Gate 3 `material-classifier`: **strong.** Rejected all 13 duplicate pairs with per-pair evidence;
  found the M0001→M0007 derivation (deck goals copied from manual p. 2-1); computed the textbook's
  printed→PDF page offset (+22) and checked it on 40 section starts; produced a coverage report with
  a volume check (≈8 of 12 units over budget), ordering problems (probability used before taught),
  an edition inconsistency (3rd vs 4th ed. across syllabus, decks), and full URLs for the truncated
  links. Three claims spot-checked against the files (78 "posted publicly" markers; manual p.13 =
  deck goals; §5.2 dependency at M0005#page-219) — all correct.

- Hand-edit protection: teacher edited `Unit_1_Algorithms.pptx`; agent hand-edited
  `ingested/M0006-…md` (slide 9). `ingest --preflight`: "1 changed" (F-23). `classkit ingest`:
  **REFUSED, exit 3, 1 refused**, edit byte-identical afterwards ✅; `validate` warns
  `materials_not_ingested` naming M0006 ✅ (F-25); refused run wrote no log entry (nothing changed)
  ✅. Preview shows front matter, not the edit (F-24). Keep/overwrite decision left to the teacher.
- Coverage report written to `course/materials/coverage-report.md` through `classkit write`
  (created/0, then `--overwrite` replaced/0 after the F-26 fix), and logged. ✅
- `source/` integrity: byte-identical to the snapshot after every ingest run; the only change in
  the whole session is the teacher's own edit to `Unit_1_Algorithms.pptx`. ✅

---

## Pending checks

- [x] Link note containing ` — ` (the note separator) survives intact — ✅ split on the first ` — `.
- [x] Link title for a bot-blocking site falls back to the note — ✅ (documented noise).
- [x] Gate 2: page anchors — ✅ `## Page N` count equals the PDF page count for all three PDFs
  (1312 / 746 / 83), and the printed page is recorded (`M0005#page-40` → "printed page 18").
  Readability — see F-06…F-09. Titles — F-12.
- [x] Time estimate — F-14.
- [x] Gate 3: recorded with `material apply` (21 changed, all-or-nothing); teacher corrections
  applied (M0001/M0002 `units: []`, M0021 marked last year's). Syllabus `.docx` files *were*
  proposed as duplicates by the tool (F-11) but rejected by the classifier. ✅
- [x] Gate 4: coverage report reviewed by the teacher; true of the course (edition mix confirmed and
  resolved: 4th ed. throughout this year). Logged. Not persisted — F-19.
- [x] Locator check: `M0006#slide-2`, `M0005#page-40` pass; `M0006#slide-999`, `M0005#page-1313`,
  `M0099#page-1` each **error** with a precise message ("it has slide-1 … slide-11"; "not in
  materials/manifest.yaml"); `validate` exit 1. ✅ (See F-21, F-22.)
- [x] Hand-edit → refused/3, edit intact; `LOG.md` entries well-formed. ✅ (F-23, F-24, F-25)
- [x] `source/` unchanged by any tool or agent (shasum diff). ✅
- [ ] Rename → "moved (same id)" — **not run** (teacher declined test files in `source/`).
- [ ] Teacher's keep/overwrite answer for M0006, then `ingest --keep|--overwrite M0006` → logged.
- [ ] Deck + PDF export; unreadable format; exact duplicate — not run (see coverage limits).
