# Teacher testing — findings for the framework developer

Hand test of the framework following `dev/MANUAL-TESTING.md`, done in the Claude Code chat as a
teacher would (D-045).

- **Tester:** Chen Avin (teacher)
- **Date started:** 2026-10-04
- **Framework commit:** `9d0aa31` (fresh clone of `BGU-CSE/class-framework`)
- **Environment:** macOS (Darwin 25.3.0), Python venv in `.venv`, Claude Code in VS Code

Each finding gives: what happened, what was expected, severity, and a recommendation.
Severity: **bug** (wrong behaviour), **gap** (the spec/docs did not say), **friction** (works but
reads badly or slows a teacher down), **ok** (checked and fine — recorded so the result is known).

---

## Summary

*(Interim — 2026-10-05. Steps 1, 0, 2b, the core of 2c-1/2c-2, 3-syllabus and 3-units were run on
the teacher's real course — last year's BGU syllabus, four decks, CLRS 4e, its Instructor's
Manual and the teacher's annotated publisher lecture notes. The TA-clone and hand-edit checks are
deferred; see "Not yet tested".)*

**Overall:** the framework did what a teacher needs. From real, messy material it produced an
approved syllabus and two approved unit plans that the teacher accepted, with **nothing invented
that survived review**, every locator checked landing on the right page, and the gates holding at
every step. The tooling's safety guarantees all held: scaffold and write never overwrote,
`source/` was left byte-identical, private text never reached git, and instructor material cited
to students raised an alert.

**Fix first (in order):**

1. **Ingest drops PDF annotations** — the teacher's highlights and margin comments on the lecture
   notes (140 highlights + 16 comments in ch. 2 alone), which the teacher uses to set each unit's
   scope and level. No agent ever saw them. *(Step 3-units.)*
2. **CLRS 4e text is garbled** — every "fi" ligature extracts as `û` (4,670 words), despite
   fontTools; F-09 is not fixed for this book, **and "Check these extractions" does not flag it**.
   *(Step 2b.)*
3. **The scaffolded `links.md` says links in slides are "collected automatically"** — the opposite
   of D-040; a teacher who believes it never adds their links. *(Step 2b.)*
4. **The teacher's answers live only in the conversation.** The step-1 log summarised them; the
   critic, reading the log, then flagged three of the teacher's own facts as "invented".
   `/plan-syllabus` should log every answer (or save them to a file the agents read).
   *(Step 3-syllabus.)*
5. **Wrong deck title from a later slide** ("In Memoriam: Michael O. Rabin" for the Unit 4 deck).
   *(Step 2b.)*

**Gaps the teacher's way of working exposed** (not bugs; decisions for the spec):

- `source/private/` should be created by scaffold — *the teacher's explicit request*.
- Home study that crosses a week boundary (a light unit absorbing a heavy one's load); the
  teacher's U02/U03 trade can only be recorded in prose.
- A class meeting repeated for groups (three identical one-hour meetings, ≈40 students each), a
  weekly TA session per student, protective ("magen") quizzes — none has a field.
- "A unit with no material" vs. "a unit with only the book": `/plan-units` cannot tell them apart,
  so it would plan at the book's depth.
- `accepted:` is per file and rule, not per item.
- `/plan-syllabus` step 1 should ask its open questions one (or a few) at a time.

**What worked notably well:** `doctor` caught a real machine problem (a global gitignore that
would leave every clone of the course unprotected); the classifier read content, not file names
(it found a misnamed deck and the publisher notes' exact page mapping in the manual); the
syllabus-designer's questions led the teacher to find their own missing syllabus; both critics
found real problems (an outcome nothing delivered; the true load in units 10–11); approval and
"edited since" behaved exactly as specified.

Severity tally for this pass: see the per-step sections; each finding is tagged **bug**, **gap**,
**friction** or **ok**.

---

## Setup

- ok — `classkit --help` runs; all subcommands listed.

---

## Step 1 — Initialize (`scaffold course`)

Ran: `scaffold course --code "202-1-2051" --title "Introduction to Data Structures" --institution
"Ben-Gurion University" --units 13`, then `scaffold unit 1 --title "Asymptotic analysis"`.

- ok — **13 files created**; `validate`: 0 alerts, 0 errors, 2 warnings (`syllabus_workload_missing`,
  `unit_count` "0 of 13"). Exactly as the manual says.
- ok — unit 1: **6 files created**; `validate`: 0 errors, summary `1 unit, 12 guiding questions`,
  14 warnings = the 2 above + 12 × `guiding_question_assessed` (listed as expected noise).
- ok — re-running `scaffold unit 1`: `0 created, 6 left untouched`, every file `exists … (left
  untouched)`. Invariant 5 holds for scaffold.
- ok — `LOG.md` got a `classkit scaffold course` entry with what changed and why.
- ok — the syllabus skeleton reads well: the front-matter comments say what each block is for, and
  the body has the Bologna-style sections (description, aim, outcomes, level/type, prerequisites,
  teaching methods, schedule, workload, grading, reading, AI policy, integrity, staff).
- **friction — `--code` is required at scaffold time.** A teacher setting up a course before
  digging out the old syllabus may not have the code to hand (I didn't — the manual's code was
  used). *Recommendation:* make `--code` optional (validate can warn while it is empty), or have
  the chat ask for it; the code is identity, not structure.
- **friction — no `--language`.** `course.yaml` is scaffolded `language: en`, with no flag and no
  comment saying what it affects. For a BGU course possibly taught in Hebrew, it is not clear
  whether the agents would then write in Hebrew. *Recommendation:* a comment on `language:` saying
  what it controls (agent output language? syllabus body?), and a `--language` flag.
- **friction — `instructors: [""]`.** Without `--instructor`, the list holds one empty string rather
  than being empty or a `TODO`. Harmless, but it looks like a bug when you open the file.
- **friction — scaffolded CO2 is served by nothing.** The syllabus comment says the two outcomes
  are scaffolded "to match the scaffolded unit", but the unit's two objectives both point at `CO1`.
  *Recommendation:* point `U01-O2` at `CO2`, or reword the comment.
- **gap — placeholders validate silently.** A textbook path with `ref: "TODO — e.g. 'CLRS ch.3
  pp.45-52'"`, `statement: "TODO"`, `goal: "TODO"` all pass with no finding. That is right for
  invariant 6 (a fresh scaffold must validate), but nothing in `validate` tells a teacher *how much
  is still placeholder*. (`classkit status` may cover this — check in Step 3.) *Recommendation:* an
  info-level count ("N TODO placeholders remain") in the summary line.
- ok — the session file's TODOs say what to write (question, not topic label, with an example) and
  the in-class file explains the "builds on home study" rule. Clear enough to act on.

## Step 0 — the overwrite-safe write path

On `course/policies/test.md`:

| Case | Result | Exit | File after |
|---|---|---|---|
| A new file | `created` | 0 | `hello` |
| **B overwrite, no permission** | **`refused`**, prints what is there | **3** | `hello` — intact |
| C `--dry-run` on existing | `refused`, prints what is there | 3 | `hello` |
| D `--overwrite` | `replaced` | 0 | `new content` |
| E identical bytes | `unchanged` | 0 | `new content` |

- ok — all five exactly as specified. **B holds.**
- ok — the refusal shows the existing content, so the chat can show it to the teacher before asking.
- **friction — the refusal text is addressed to an agent**, not the person running it ("…write again
  with overwrite=True (`--overwrite`)", "Show the teacher…"). Fine while only agents see it, but a
  teacher who asks "show me the full output" reads instructions about themselves in the third
  person. *Recommendation:* neutral wording, e.g. "already has content (shown below). Re-run with
  `--overwrite` to replace it."
- **gap — logging is inconsistent between scaffold commands.** `scaffold course` wrote a `LOG.md`
  entry; `scaffold unit 1` (6 files) wrote none. If the log is meant to say "what changed and why",
  a new unit is a change. (`write` not logging is presumably by design — the calling command logs.)
  *Recommendation:* either log `scaffold unit`, or document that only course-level scaffolding is
  logged.
- not tested — how much of a long existing file the refusal prints (does it truncate?).

## Step 2b — ingest

**Deviation from the manual (teacher's choice):** the throwaway unit 1 was deleted before ingest
(the F-18 note allows this), and the textbook / solutions manual go **straight into
`source/private/`** rather than into `source/` first and moved later. A teacher who has read
`source/README.md` would do exactly this, so it is the realistic path; the manual's 2c-1 "move
into `private/` → `moved … (same id)`" is then a migration case, not the main one.

- **friction (teacher's request) — `source/private/` should exist from the start.** Scaffold
  creates every other directory (`ingested/`, `policies/`, `assessments/*`, …) but not
  `private/`; the README says "(create the folder)". The teacher's view: **it should be created
  with all the other directories**, so the private option is visibly there from day one — moving a
  file in later is fine as a fallback, but the teacher should not have to discover the folder
  from a README. Every course with a textbook needs it, and the `.gitignore` rule already exists.
  Created by hand in this test (`mkdir`; `git check-ignore` confirms it is ignored).
  *Recommendation:* `scaffold course` creates `materials/source/private/` (and lists it in its
  output and the README's tree). Note: since the folder is ignored, a `.gitkeep` inside it will not
  be committed, so a fresh clone (a TA's) will not have it either — re-running `scaffold course`
  or `classkit doctor` should create or point at it.
- **gap — the docs do not say what belongs in `private/` beyond the book and the manual.** A
  teacher's own decks, past exams, the old syllabus: private or not? The cost of over-using
  `private/` (a TA's clone, or an agent on another machine, sees only an index of the teacher's
  own decks) is not stated anywhere a teacher reads. *Recommendation:* one line in the README:
  "Put here only what must not be in the repo; your own slides belong outside it."
- **MANUAL-TESTING:** Step 2b should say whether to start with the book in `private/` (the normal
  case) and treat the move as a separate migration test.

**Materials uploaded** (last year's course): in `source/` — `syllabus data-structures-2025
2026.docx`, `Detailed_Syllabus.docx`, `Detailed_Syllabus_Exam.docx`, `class-units.docx`, four unit
decks (`Unit_1_Algorithms.pptx` … `Unit_4_Divide-and-Conquer_board.pptx`); in `private/` — CLRS
4th ed. (book PDF), the CLRS Instructor's Manual, selected solutions, and publisher lecture notes
for chapters 1–4. Not in this set: a deck together with its PDF export, an unreadable format, a
link — so those manual checks are not exercised.

- ok — `add-url "not a url"` → `error: … not a single URL`, exit 2, `links.md` untouched.
- ok — `ingest --preflight` (2 s, writes nothing): 15 files, 71 slides, 2204 PDF pages, "Private:
  7 file(s) under private/", every new file listed by name; **no library noise above the report**
  — pypdf's complaints are grouped per file with a count and one example (F-03, F-10 fixed);
  estimate "about 3 minutes" for ~2200 pages (F-14). `README.md` and `links.md` are correctly not
  counted as materials.
- **bug — the scaffolded `links.md` contradicts D-040.** Its comment says *"Links inside your
  slides and documents are collected automatically; you do not need to copy them here."* The
  pre-flight output says the opposite — *"a link becomes a material only when it is listed
  there"* — and so do `CLAUDE.md` and the manual (F-13: links are no longer harvested). A teacher
  who trusts the template will never add their course Gem / video links. Source:
  `templates/course/links.md:12-14`. *Recommendation:* replace the sentence with "Links inside
  your slides are not collected — add the ones students should use here; `/ingest` will mention
  any it notices."
- friction — the reader warnings ("Previous trailer cannot be read: ('NumberObject' object is not
  subscriptable',)", "Ignoring wrong pointing object 8 0") are pypdf internals. Grouped and counted
  is a big improvement, but a teacher cannot tell whether "2 problems" in the textbook matters.
  *Recommendation:* add one plain line — "usually harmless; check the extraction of these files
  after ingest" — and have the post-ingest "check these extractions" list say whether these files
  actually came out degraded.

### `/ingest` run

Link added: `classkit add-url https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/
--note "CLRS … 4th ed. … the course textbook"` → `added`, exit 0. (The URL was verified by web
search; the page returns HTTP 403 to scripts, so ingest cannot fetch its title — expected noise.)

**`status` and `doctor` (step 0):**

- **ok, and valuable — `doctor` caught a real machine problem.** My global git config
  (`~/.gitignore_global`) ignores every file named `.gitignore`, so `course/.gitignore` — the file
  that keeps `private/` out of git — would never be committed, and every clone of the course
  (a TA's) would be unprotected. `doctor`: `ACTION course/.gitignore is itself ignored by git
  (/Users/avin/.gitignore_global:3:.gitignore) … fix: git add -f course/.gitignore, and commit it`.
  Clear, specific, with the fix. This would have gone unnoticed otherwise.
  *Recommendation:* since a global ignore of `.gitignore` is not rare, `scaffold course` could warn
  at creation time too, not only `doctor`.
- friction — **`status` and the pre-flight count differently.** `status`: "9 outstanding since the
  last ingest" (the 8 non-private files + the link); pre-flight: "To convert: 16 materials". The 7
  private files are left out of `status`'s count (they appear only as `doctor` ACTIONs). A teacher
  reading both sees two different numbers for the same thing. *Recommendation:* `status` counts
  private files too ("16 outstanding, 7 of them private").
- friction — before the first ingest, `doctor` shows 7 `ACTION … is new and not ingested` lines,
  and exits 1 ("8 to fix"). Every one is fixed by the very next step of `/ingest`; on a first run
  they bury the one ACTION that matters (`.gitignore`). *Recommendation:* collapse into one line
  ("7 private files not ingested yet — `classkit ingest`"), or make it a note when nothing was
  ever ingested.

**Conversion (`classkit ingest --no-log`, step 2):** 16 new (M0001–M0016), 0 refused, exit 0.

- ok — every private file written twice: index to `ingested/`, full text to `private-text/`.
  `git status` shows nothing under `source/private/` or `private-text/`; `git check-ignore`
  confirms both are ignored.
- ok — **the CLRS index is genuinely useful**: every PDF page with its printed page label (`Page 40`
  → `printed page 18`) and the book's sections from its bookmarks (`6.2 Maintaining the heap
  property`, …). No body text in the index. An agent can cite "§6.2, printed p. N" from it.
- ok — "Check these extractions" lists the picture-heavy decks (e.g. M0004: 10 of 19 slides have
  no text) and the PDFs the reader complained about. Hidden slides are marked `*(hidden slide)*`.
- ok — the Rabin slide's Wikipedia link appears in the ingested text as `[…](https://…)`; no link
  was harvested as a material (F-13).
- **bug — F-09 is NOT fixed on the CLRS 4th-edition PDF. fontTools is installed** (`doctor`:
  "dependencies import: fonttools, …") **and the text is still broken:** every "fi" ligature
  came out as `û` — `deûnite`, `ûnd`, `efûcient`. In `private-text/M0010-…md`: **4,670 `û`**,
  `efûcient` 325 times vs. `efficient` 3 times. There are also spurious spaces inside words
  (`th e keys`, `( the satellite data)`, `pseu- docode`). The other six private PDFs (instructor's
  manual, solutions, lecture notes) have zero `û`. So the hypothesis "fontTools fixes the
  ligatures" is falsified for this book; the cause is likely this PDF's font encoding / ToUnicode
  map. *Recommendation:* (1) investigate with this PDF (CLRS 4e, 1312 pp.); (2) a targeted
  repair — `û` inside an otherwise-ASCII English word → `fi` (and the same for `ﬂ`/`ﬀ`
  substitutes) — guarded so real `û` in French names survives; (3) **regardless of the fix**, see
  next item.
- **bug — "Check these extractions" did not flag the damage.** For M0010 it says only "the reader
  reported 2 problem(s)… the text may be degraded" — the same wording as the lecture notes, whose
  text is fine. Nothing says one in three pages has broken words. Agents will read this text and
  may quote "efûcient". *Recommendation:* a cheap quality probe after extraction — rate of
  non-ASCII letters in otherwise-English words, or of known ligature substitutes — reported as
  "M0010: ~4,700 words look garbled (e.g. `efûcient`) — ligature problem".
- **bug (F-12 heuristic) — wrong title for the Unit 4 deck.** M0006 (`Unit_4_Divide-and-
  Conquer_board.pptx`) is titled **"In Memoriam: Michael O. Rabin (1931–2026)"** — the bold title
  of slide 2, a tribute slide. Slide 1 holds only a bullet ("Last Week"), so the heuristic fell
  through to the next slide. The file name was far more informative. Similarly M0004/M0005 are
  titled just "Unit 2" / "Unit 3" while their file names say "Introduction" / "Characterizing".
  *Recommendation:* take a title only from slide 1 (title placeholder); otherwise use the file
  name. A title from a later slide is more likely a section or a digression than the deck's name.
- friction — titles from file names keep their punctuation: M0010 is titled
  `Introduction.to.Algorithms.4th.Edition.2022.4`, M0011 `Lecture-Notes-for-Chapter-1`.
  *Recommendation:* turn `.`/`-`/`_` into spaces when titling from a file name.
- friction — **time estimate 6× too high**: "about 3 minutes", actual 30 s (2,204 pages, M-series
  Mac). Harmless direction to err in, but worth recalibrating.

**Classification (step 3, `material-classifier`):**

- **ok, impressive — the classifier read the material, not the file names.** It found that
  `private/Lecture-Notes-for-Chapter-1.pdf` (M0011) is *not* the publisher's notes but an older PDF
  of the teacher's own Unit 1 deck; that M0012–M0014 are the same text as page ranges of the
  Instructor's Manual (M0008), with exact page mappings; that the old official syllabus (M0015)
  names a different lecturer and course code and cites the 3rd edition, while the unit list cites
  the 4th; that one deck says "Third Edition" and the others "Fourth". All spot-checked: true.
- ok — `audience: instructor` proposed for exactly the right six (working plan, instructor's
  manual, solutions, publisher lecture notes), each with a reason; it noted that the selected
  solutions are publicly posted by MIT Press, so `student` is defensible — the right kind of
  caveat.
- ok — it proposed better **titles** (fixing M0006's "In Memoriam" title) and `material apply`
  accepts them. This partly compensates for the F-12 title bug above — but only because the
  classifier noticed.
- ok — it found the course Gem link on M0003#slide-2 and suggested `add-url` with a "check it's
  still the one you want" caveat (the teacher declined: a new Gem this year).
- ok — `material apply` recorded 16 materials in one call; the classification was shown before
  anything was recorded (D-039 gate held).
- **gap — D-042 does not cover a teacher's own decks adapted from publisher notes, and `doctor`'s
  "ok" line overstates.** The classifier warned that the teacher's decks M0004–M0006 follow the
  publisher notes closely. Measured: committed `ingested/M0006-…md` shares **a run of 30+
  consecutive words** with the private `M0014` (publisher lecture notes, ch. 4). `doctor` still
  prints `ok  no committed course file copies text from a private material`, because
  `materials/ingested` is in `NOT_SCANNED` (`src/classkit/doctor.py:52`). Excluding the teacher's
  own sources is defensible (the teacher owns their slides), and **the teacher's view is that it
  is not a problem as long as students are pointed to the teacher's slides** — this year there may
  be no slides given to students at all. But the `ok` line claims more than was checked.
  *Recommendation:* reword to "no course file outside `materials/` copies …" (or "… — ingested
  copies of your own materials not checked"), and consider an informational note when an
  ingested non-private material overlaps a private one, since that text *is* committed.
- friction — `material apply`'s echo omits `kind` for materials whose kind was already guessed
  (M0003–M0006, M0008), so the teacher cannot see from the output that `slides` / `other` was
  confirmed. *Recommendation:* echo every field set, or say "kind unchanged (slides)".

**Coverage report (step 4):**

- ok — the report put **scope first** ("units 5–12: no material yet", not "thin") and separated
  thin *extraction* from thin teaching. Volume check and ordering problems were concrete and
  located (printed pages, slide numbers).
- ok — saved to `materials/coverage.md` through the write path after the teacher read it, with the
  teacher's corrections in a section of their own; `validate` after: **no
  `material_locator_in_text` warning** — every one of ~50 locators in it resolves. `doctor`: no
  copying from private text.
- **friction — the report leaned on last year's "weeks" column** (1.5, 0.5, "1+") as if it were the
  load to plan for. The teacher's position: ignore it — **every unit is one teaching week** in the
  flipped course, with much less variation in class time. The flipped methodology already fixes
  one week per unit, so the classifier should treat an old schedule's week counts as history, not
  as a target. *Recommendation:* say so in the classifier's instructions.
- **gap (teacher's idea) — home study that crosses a week boundary.** The teacher wants the option
  that students *start unit N+1's study once unit N's is done* (e.g. a light unit 3 absorbing some
  of a heavy unit 4). The methodology fixes 4 × 25-min sessions per unit, one unit per week; there
  is no notion of a session being studied in an earlier week, or of balancing load across units.
  *Recommendation:* decide whether a session may carry a "can be started in week N−1" flag, and
  whether the workload check may be per-week rather than per-unit.
- note — the teacher deliberately **follows the book's order** ("standing on the shoulders of
  giants"). The classifier's "ordering problems" were useful as *signposts for home study*, not as
  reasons to reorder; the agents should present them that way by default.

**A late addition (second `/ingest` run, during `/plan-syllabus` step 1):** the teacher realised
their *own* 2025/26 syllabus was missing (M0015 turned out to be a predecessor's text in the same
BGU form) and added `syllabus data-structures-2026.docx` → **M0017**.

- ok — incremental ingest: pre-flight "1 new … 15 unchanged", conversion of just that file, under
  a second.
- friction — the pre-flight **re-lists the reader warnings for the four unchanged PDFs** every run.
  They were reported at their conversion; repeating them on files that will not be touched is
  noise. *Recommendation:* show reader warnings only for files about to be converted.
- **gap — classifying one added file.** `/ingest` step 3 always sends the classifier agent (≈2–5
  min, re-reading the corpus). For a single new syllabus the chat proposed the row itself and
  showed it to the teacher for confirmation. The command does not say whether that is allowed.
  *Recommendation:* allow the chat to classify a small increment itself (still gated by the
  teacher), and keep the agent for bulk or ambiguous material.
- **gap — `coverage.md` is now silently stale.** It lists "Materials covered: M0001–M0016";
  M0017 changes what the course's evidence is (the real staff, the AI policy). Nothing flags that
  the saved report predates a material. *Recommendation:* `status` could say "coverage report
  predates M0017".
- friction — **a Word syllabus with no heading styles has no anchors**, so the official syllabus
  can only be cited whole (`M0017`), never its Assessment or AI section. BGU's form is bold labels
  ("Assessment:", "Learning outcomes of the module:"), not Word headings. *Recommendation:* treat a
  short bold paragraph ending in ":" as a heading for anchoring.
- note — the syllabus-designer had already spotted that M0015 "may be a predecessor's text" (it
  names another lecturer); the evidence step's questions are what prompted the teacher to find the
  right file. Good behaviour.

**`course.yaml` edit (D-041 write path):** `classkit write course/course.yaml --diff` showed exactly
the two changed lines (code `202-1-2051` → `371-1-0341`, units 13 → 12); `--overwrite` wrote it;
file mode stays `-rw-r--r--` (G-22 ok). `validate` after: 0 errors; `materials_not_ingested`
silent.

## Step 2c-1 — private and instructor-only material; `doctor`

## Step 2c-2 — hand-test fixes, D-041

## Step 3-syllabus — `/plan-syllabus`, approval, `status`

Run on the real course. Steps 2c-1's second-machine checks and 2c-2's hand checks (refusal diff,
prose-locator warning, `.gitignore` deletion) were **not yet run** — the teacher chose to keep
moving on the course; to be done before the end of the test.

**Step 0.** ok — `status` before: `NOT STARTED: the scaffolded placeholders — run /plan-syllabus`;
materials "16 ingested, 7 private, 6 instructor-only", "coverage report: materials/coverage.md".

**Step 1 — evidence (syllabus-designer, `evidence`).**

- ok — it named the evidence by id, said how far each reaches, chose the form to mirror (the old
  syllabus's sections, in order) and said why and at what cost ("if BGU has a newer form…").
- ok — it noticed things a teacher would want flagged: the old syllabus names another lecturer
  (it was a predecessor's — the teacher then found and added their own); the old outcomes cover
  data structures but not the algorithmic half of the units; unit 11 is the heaviest unit, so
  "B-trees if there is room" is unlikely; randomized algorithms (units 6–8) depend on CLRS ch. 5,
  which the course skips.
- ok — 12 open questions, **each with what the draft does if unanswered**, ordered by how much they
  shape the draft. The teacher asked to go **one question at a time**; the chat did, and resolved
  three questions from earlier answers instead of asking them again. This worked well.
- **gap — the command has no "one at a time" mode.** Step 1 presents the open questions as a block;
  a teacher answering a list of 12 in one message gives worse answers than 12 short exchanges (the
  teacher's choice here). *Recommendation:* step 1 should say to ask the questions one (or a few)
  at a time, most draft-shaping first, and to skip any already answered.
- **friction — the evidence step leaned on "lecture hours" again** (same as the classifier's
  "weeks"): it took M0015's 3-hour Sunday slot as the class format. The teacher's real format —
  the teacher teaches the same one-hour class **three times** to groups of ≈40, so each student has
  one hour — is not something the methodology file can express, and only a question surfaced it.
  *Recommendation:* the methodology / `course.yaml` could record "class meeting repeated N times
  for groups of size M" — it matters for the lesson planner (an activity that needs whole-class
  discussion behaves differently at 40) and for the syllabus body.
- note — the teacher's answers included things the framework has no field for: a **weekly
  one-hour TA session per student**, **no phones in class**, **protective quizzes** ("magen": up to
  50% of the exam weight, only when it helps). They went into the body as prose, which is right;
  but the TA session is part of the weekly workload and the lesson planner may want to know it
  exists. *Recommendation:* consider an optional `weekly_components` (or similar) in the syllabus
  front matter.

**Step 2 — draft (syllabus-designer, `draft`).**

- ok — **the first write was refused** (exit 3) and the refusal quoted the placeholders; the chat
  said so and asked before replacing them (2a turn boundary held).
- ok — after `--overwrite`: `validate` 0 errors, 1 warning (`unit_count`; `syllabus_workload_missing`
  gone because the credits were known). `doctor`: no copying from private text.
- **ok, excellent — all 24 CLRS locators in the unit map are right**, not merely existing: each
  `M0010#page-N` lands on the claimed chapter/section start (e.g. `page-595` = §20.4 Topological
  sort, `page-213` = §7.3 randomized quicksort). Checked against the index's section labels.
- ok — **nothing invented** that I could find: credits, prerequisite, emails, office hours, grading
  all trace to M0017 or the teacher; where the teacher had not decided, the body says
  `**TBD:** … — the teacher`. Last year's bonus presentation and reservist wording were
  *deliberately not* carried over and the report said so.
- ok — the report gave the outcomes **original vs. proposed side by side, with reasons** (as the
  teacher asked: "let's decide together"), and the outcomes-against-units table.
- ok — the teacher's instruction "students don't need to know the 100-min calculation" was
  respected ("about four study sessions"), and the report noted that this overrides the skill's
  "use the methodology's numbers".
- friction — `workload` allows **one** credit system; BGU syllabi state both BGU credits (3.5) and
  ECTS (5.25). ECTS ended up only in the body. *Recommendation:* allow a list, or `ects` alongside.
- friction — a syllabus `assessment` entry with no `weight` (the protective quiz) validates, which
  is good — but there is no way to express "counts only if it helps" except prose.
- friction — the M0017 docx has no anchors, so the unit map's evidence cites `M0002`, `M0007`,
  `M0017` bare — `/plan-units` will be sent to a whole file.

**Step 3 — revision round 1** (TA office hours, "exam ≥ 56" confirmed): ok — the chat re-read the
file first (no hand edits), showed a 3-line `--diff`, wrote on OK, logged. Nothing else changed.

- friction — `status` after the draft says `DRAFT: not approved`, which is right, but still says
  nothing about `coverage.md` being older than M0017 (see Step 2b).

**`/review-syllabus` (course-critic).**

- ok — independent, thorough, wrote nothing; findings split into "broken" / "should fix" /
  "would have done differently", with costs named; re-verified all 24 locators; checked
  instructor-only and private-text rules.
- ok — **real findings a teacher needs**: CO5 ("design and implement") has nothing to build or
  assess it unless programming homework stays (and the AI policy's "coding assignments" bullet
  depends on it); **units 10 and 11 are the real load problem** (≈40 and ≈50 printed pages vs. ≈12
  for unit 1; unit 10 had not been flagged by anyone); hashing is the most probability-heavy unit
  but missing from the "probability is signposted" list; the weekly TA session lacks a when/where
  TBD; the "Time required" section now holds no quantity, which is what a committee reads it for.
- **bug (process) — three false "invented" findings, caused by an incomplete course log.** The
  critic flagged as *invented*: the lecturer's office hours "Sundays 19:00", the programming
  prerequisite sentence, and "stays in the same group all semester / size-limited". **All three
  came from the teacher in the chat** ("Keep office hours right after the class (at 19)"; "to study,
  they need to finish programming"; "enroll in one of the sessions and stay there for the entire
  semester … every session is limited by size"). The critic checks against `LOG.md`, and the chat's
  step-1 log entry (mine) summarised the answers and **left those three out**. So the critic was
  right to distrust them given what it could see — the defect is that the teacher's answers live
  only in the conversation. *Recommendations:* (1) `/plan-syllabus` step 1 should log **every**
  teacher answer, not a summary line — or save them to a file (e.g. `syllabus/answers.md`) the
  designer and the critic both read; (2) the critic should phrase such a finding as "not in the
  evidence or the log — confirm with the teacher" rather than "invented", since the conversation
  is invisible to it.

**Acting on the review (step 3 rounds, one finding at a time, each decision logged).** The teacher
answered every finding; the chat logged each answer as it came (`classkit log`, decision-only
entries), then showed **one diff** for all the resulting edits. The teacher then asked to redo the
outcomes as 6 shorter ones; the chat proposed a table (old → new, units per outcome, costs) and
wrote after approval.

- ok — the diff touched only what was decided; the chat re-read the file first (no hand edits).
- **bug (mine, caught before writing) — a carried-over fact slipped into a revision.** Drafting
  the homework edit, the chat wrote "They include theoretical ('dry') assignments" — from last
  year's syllabus, never said this year. Caught on reading its own diff and removed before asking.
  Worth noting because the same failure the critic hunts (last year's facts presented as this
  year's) also happens in the chat's revision rounds, where no critic looks.
  *Recommendation:* the writing-a-syllabus skill's Revising section could say: "every new factual
  sentence must trace to the teacher's words in this conversation or the log".
- note — the teacher's own wording in the chat ("year 3 or 4 EE students", "probability learned
  earlier", groups 16–17/17–18/18–19) produced better syllabus text than anything inferable from
  the evidence. The question-at-a-time flow is what surfaced them.

**Step 4 — approval.**

- ok — `classkit approve syllabus --why …` showed its diff, wrote `approved: {date, hash}`, logged;
  `status` → `APPROVED: approved 2026-10-05`.
- ok — edit one body word → `APPROVED, EDITED SINCE`; reword only a YAML comment → still
  `APPROVED`; hand-written `approved: {date: …}` without hash → `APPROVED, EDITS UNTRACKED … (by
  hand: edits since cannot be tracked)`, and `validate` gives no error.
- ok — re-approve after an edit → one `approved` block, replaced in place; log: "syllabus
  re-approved (sha256:…); was approved 2026-10-05".
- ok — re-approve an unchanged file → `unchanged … not edited since — nothing to record` (no log
  noise). Sensible; the manual does not mention this case.
- friction — **restoring a file outside the tools leaves the log wrong.** After the test, the file
  was restored by copying (as `git checkout` would); it carries its old `approved` block, `approve`
  correctly says "nothing to record" — but the log's last approval entry names a hash the file no
  longer has. A hand-written log entry fixed it. *Recommendation:* `status` could cross-check the
  file's approval hash against the last logged approval and say when they disagree.
- **MANUAL-TESTING:** step 4's "approve the syllabus again → re-approved" should say *after an edit*;
  on an unchanged file it is (correctly) a no-op.

## Step 3-units — `/plan-units`, unit states, `approve unit`

- **bug / gap — HIGH — ingest drops PDF annotations: the teacher's highlights and margin comments
  are lost.** The teacher: *"Usually, the lecture notes files signal what I want to teach in the
  unit and at what level (they contain less than the Book). You need to read them with comments
  and marks highlighting important points."* The publisher lecture notes M0012–M0014 carry the
  teacher's annotations — ch. 2: **140 highlights, 16 comments**; ch. 3: 66 highlights, 8
  comments; ch. 4: 110 highlights, 10 comments, 15 stamps — e.g. "Show on Cards", "On board",
  "Ask in class what is the running time of merge", "How to prove lg n+1 levels", "Do on slide for
  n=11". `extract.py` reads only link annotations (`_link_annotations`); highlights (`/Highlight`)
  and comments (`/FreeText`, `/Text`) are discarded, so **none of this reached the ingested text,
  the classifier, the syllabus-designer or the curriculum-architect**. The architect's first U02
  draft proposed making the pseudocode conventions reference-only — which the teacher's
  highlights contradict — and asked two scope questions the highlights answer. Recovered by hand
  in this test with pypdf (highlight QuadPoints → text under them; FreeText `/Contents`).
  *Recommendations:* (1) extract annotations into the ingested / private-text file per page —
  highlighted spans marked (e.g. `==…==`), comments as `> [comment] …` — and for a private
  material keep both out of the committed index (the teacher's comments are the teacher's, but
  they sit on publisher text); (2) "Check these extractions" should report "N highlights, M
  comments" per file, so their presence is visible; (3) the classifier should flag an annotated
  document as a likely **scope signal**; (4) the planning-units skill should list "the teacher's
  annotated notes" as evidence of scope and level, above the book.
- **gap — the teacher's own lecture notes as the scope signal.** The teacher's rule — the notes
  say *what* and *at what level*; the book is the fuller reference — is a standing course-level
  preference with nowhere to live except the log. *Recommendation:* a course-level field (e.g.
  `scope_sources` in `course.yaml`, or a materials `role: scope`) that agents read before the book.
**`/plan-units 1 2` run.**

- ok — step 0: status, doctor; syllabus approved, so no "go on?" question. *(Not tested: the
  manual's "try once with the syllabus not approved".)*
- ok — the curriculum-architect read the real material (CLRS ch. 1–2 full text, the decks, the
  publisher notes) and cited it precisely; two locator spot-checks held (termination step on
  `M0010#page-42`; best case = already sorted on `M0010#page-52`). It said which outcome links
  were weak (U01-O1 → CO3 gives only the definition a proof needs) and refused to attach the §1.1
  "landscape" material to an outcome — exactly the planning standard.
- ok — load: it noticed U01 is light and U02 over budget, proposed cuts and a move, and **left the
  decision to the teacher**. The teacher kept U02 whole and decided to balance it against U03 — a
  cross-unit trade the plan can only record in prose (see the "home study across weeks" gap).
- ok — 5 proposed difficulties, specific and classic, each with evidence; recorded `origin:
  proposed` only after the teacher accepted them.
- ok — the teacher wanted U01's landscape material (NP-completeness, parallel/online, what the
  course leaves out) as an objective; the chat offered (a) an honest objective with no outcome vs.
  (b) folding it into U01-O1, recommended (a), and the alert `objective_maps_to_outcome` fired as
  predicted.
- ok — step 2: `scaffold unit N --title <map title>`; the first `unit.md` write refused (exit 3,
  placeholders); one go-ahead for both; `validate` after: 0 errors; alerts exactly the predicted
  ones (`objective_maps_to_outcome` U01-O3; `objective_coverage` U01-O3, U02-O3, U02-O4); 24 ×
  `guiding_question_assessed` + `unit_count`; no `unit_map_mismatch`.
- **friction — `objective_maps_to_outcome`'s advice is the forbidden fix.** It says "Add `outcomes:
  [CO…]` — the outcome(s) it serves", for an objective the teacher deliberately left without one.
  The planning standard says *never* attach to the nearest outcome to silence it. *Recommendation:*
  "…or, if no outcome fits, say so: add an outcome in the syllabus, or record an accepted exception".
- **gap — `accepted:` is per file and rule, not per item.** Accepting U01-O3's missing outcome
  silences `objective_maps_to_outcome` for **every** objective in U01, including future ones that
  forget their outcome by mistake. *Recommendation:* an optional `id:` on an accepted entry
  (`{rule: objective_maps_to_outcome, id: U01-O3}`).
- ok — `validate` reports "1 finding suppressed by 1 accepted exception in 1 file" — never
  invisible. Good.

**Approval (`approve unit N --stage planned`):**

- ok — `approved: {date, stage: planned, hash}`; status `2 planned, 10 not started`, `U01 …
  planned 2026-10-05`; **the `objective_coverage` alerts vanished on approval** (D-047).
- ok — edit an objective's wording → `planned … — edited since`; edit a placeholder session → not
  edited since (a planned unit's hash is `unit.md` only); title differing from the map →
  `unit_map_mismatch` with a clear message; hand `approved: {date, stage: planned}` without hash →
  "(by hand: edits since cannot be tracked)", no error; without `stage` → **schema error**
  `approved: 'stage' is a required property`, and status says "its `approved` record is
  malformed — `classkit validate` says how". All as specified.

**`/plan-units 7` — a unit without the teacher's material.**

- **MANUAL-TESTING / gap — "a unit with no material" barely exists when the textbook is ingested.**
  The manual expects `/plan-units 7` to find no material. But the textbook is `units: all`, the
  syllabus's unit map cites its ch. 8 pages for U07, and the Instructor's Manual holds the
  publisher's ch. 8 notes — so by the command's own test ("coverage says 'no material yet', the
  map entry has no `evidence`") U07 *has* material. What it lacks is the **teacher's** material
  (deck, annotated notes) — the evidence of scope and level. The command has no notion of this
  difference, so an architect would plan U07 confidently from the book alone, at the book's depth.
  The chat raised it and offered: (a) wait for the teacher's annotated notes, or (b) plan
  provisionally, labelled "scope not confirmed". **The teacher chose (a)**; logged; U07 stays not
  started. *Recommendation:* `/plan-units` step 0 should distinguish "book only" from "teacher's
  material"; the manual's step 5 should say which kind of "no material" it tests.

- note — the publisher lecture notes are `audience: instructor` (correctly), yet they are *the*
  scope document for planning. The rules handle this (instructor material may inform a plan);
  worth stating in the classifier's report so nobody reads "instructor-only" as "ignore".

---

## Cross-cutting checks run at the end (2026-10-05)

- ok — **`source/` untouched.** `shasum` snapshot before ingest vs. after everything: all 15
  original files byte-identical. The only differences are the teacher's own added file and
  `links.md`, changed by `classkit add-url` (by design).
  - friction — the docs say "**Nothing** modifies, moves or deletes anything in `source/`", while
    `add-url` writes `source/links.md`. Say "nothing except `classkit add-url`, which appends to
    `links.md`".
- ok — **`instructor_material_cited`** (2c-1): a study path citing `M0009#page-9` (selected
  solutions, instructor-only) → ALERT, with both ways out named ("cite it from the in-class plan
  instead; or … `--audience student`"); the same locator in an in-class activity's `materials` →
  no alert. The guard that matters most for students works.
- ok — **`material_locator_in_text`** (F-26): `M0010#page-99999` in `coverage.md` → warning "M0010
  has no anchor 'page-99999' (it has page-1 … page-1312)". *(Not run: the same in `LOG.md`.)*
- ok — `/review-unit 2` on a **planned** unit reviewed the plan, not the placeholder sessions; it
  checked the plan against the teacher's annotations (from the by-hand extraction), found it
  matched, and raised real issues: the scope source survives only in a temp file; U02's overrun
  is unquantified (≈40–80 min), which makes a promise on behalf of an unplanned U03; the
  pseudocode conventions are undecided; no difficulty covers the analysis half; the teacher's
  "ask in class" cues from a lecture may belong in the entry quiz in a flipped hour. Nothing
  written; the teacher deferred all of them; logged.

**Not yet tested (deferred by the teacher to a later phase):** the TA clone / second machine
(2c-1, 2c-2 D-041), the hand-edit refusal with per-slide diff (F-24/F-25), `git add -f` of a
private file (`private_material_committed`), renaming a source (`moved … (same id)`), deleting
`course/.gitignore` (`course_gitignore_missing`), `classkit mode developer` refusing in a clone,
`/plan-units` with the syllabus not approved, `/design-unit` and later steps (not in the manual
yet).

## Findings on `MANUAL-TESTING.md` itself

- **Step order:** "Step 1" comes before "Step 0" in the document. Fine once you notice, but a
  one-line note ("Step 0 needs a course, so it is tested after Step 1") would help.
- **Step 1 note on D-032 is stale:** it says `level`, `course_type`, `offered`, `teaching_methods`,
  `reading` are "not yet implemented, so their absence is expected" — but the scaffolded syllabus
  body already has "Level, type and when offered", "Teaching methods" and "Reading" sections, and a
  commented `reading:` block. The note should say what is and is not there now.
- **Step 1 gives no warning count after `scaffold unit 1`** (it is 14). Stating it would make the
  check mechanical.
