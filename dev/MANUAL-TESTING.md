# Manual testing — driving the framework as a teacher would

Automated tests build a throwaway course in `tmp_path` and check it holds together. They do **not**
tell you whether the thing is pleasant to use, whether the output reads well, or whether a teacher
following `README.md` gets where they expect. That needs a human running it in a clean environment.

This document is the procedure. It grows a section per implementation step (see `ROADMAP.md`).

Each section was checked against the step that built it. Step 1's counts and validate summary were
re-checked on 2026-10-05, after the teacher-test fixes (14 files; 14 warnings after `scaffold unit
1`); the other sections are as their steps left them.

## Work in the chat, as a teacher would (D-045)

A teacher never needs the terminal, so **test the way a teacher works: in the Claude Code chat.**
Every `classkit …` line in this document is something to **ask the chat for in plain words** — "check
the course", "show me the status", "approve the syllabus", "what does doctor say?". The command is
shown so you can see that the chat ran the right thing, and what output to expect. Two things to
check every time:

- **Did it report faithfully?** Every alert and error, the warnings counted — not "a few minor
  warnings". Ask for the full output when in doubt.
- **Did a write ask you first?** `validate`, `status`, `doctor` and `ingest --preflight` run without
  asking; anything that writes should ask.

## Set up a clean environment

The framework **is** the working environment: a course repo is a clone of the framework with
`origin` repointed (D-009). So a clean test environment is simply a **fresh clone in a scratch
directory** — never the development checkout, and never inside it.

```bash
cd ~/scratch                      # anywhere outside the framework checkout
git clone https://github.com/BGU-CSE/class-framework.git testdrive
cd testdrive

python3 -m venv .venv             # keep classkit out of your global Python
.venv/bin/python -m pip install -e .
.venv/bin/classkit --help         # sanity check
```

Prefix every command with `.venv/bin/`, or `source .venv/bin/activate` once.

Two things a real teacher does that you can **skip** when testing: repointing `origin` to their own
course repo, and pushing. Neither affects what you are testing, and both create a repo you then have
to delete.

**Throw the whole directory away afterwards** (`rm -rf ~/scratch/testdrive`). Never commit a scaffolded
course — invariant 1 says no course content in the framework repo, and the clone is still pointed at
`origin`.

---

## Step 1 — Initialize (`scaffold course`)

**What it should deliver:** the teacher's first contact with the framework produces a complete,
*valid* course skeleton, including the syllabus.

```bash
.venv/bin/classkit scaffold course \
  --code "202-1-2051" \
  --title "Introduction to Data Structures" \
  --institution "Ben-Gurion University" \
  --units 13
```

Expect **14 files created**, among them `course/syllabus/syllabus.md`, `course/course.yaml`,
`course/LOG.md`, `course/.gitignore` (step 2c-1: it keeps private material out of git) and
`course/materials/source/private/.gitkeep` — the private folder exists from the start, and the
output ends by saying what it is for. `course.yaml` has `instructors: []` when no `--instructor` was
given, and a comment on `language:` (`--language`, default `en`). If your global git config ignores
`.gitignore` files, the output ends with a **WARNING** naming the fix (`git add -f
course/.gitignore`).

```bash
.venv/bin/classkit validate
```

Expect **0 errors** and 2 warnings — `syllabus_workload_missing` (you have not set credits yet) and
`unit_count` (0 of 13 units so far). Zero errors on a fresh scaffold is invariant 6; an error here is
a real failure, not a nuisance.

Then add a unit and validate again:

```bash
.venv/bin/classkit scaffold unit 1 --title "Asymptotic analysis"
.venv/bin/classkit validate
```

Expect **6 files created** under `course/units/01-asymptotic-analysis/` (4 sessions + `unit.md` +
`in-class.md`), and again **0 errors** and **14 warnings** — the 2 above plus 12 ×
`guiding_question_assessed` (expected noise, below); the summary reads `1 unit, 12 guiding
questions` (F-02). `course/LOG.md` gets a `classkit scaffold unit 1` entry naming the six files.

> **This unit is a throwaway (F-18).** A real teacher ingests their materials (step 2b) *before*
> any unit exists, and `/plan-units` decides what unit 1 is. Here it only proves scaffolding works;
> in the hand test, "Asymptotic analysis" was really unit 3 of that course. If you go on to step 2b
> in the same course, expect the classifier to say so — or delete `course/units/` first.

**Re-run scaffold to prove it never overwrites** (invariant 5):

```bash
.venv/bin/classkit scaffold unit 1 --title "Asymptotic analysis"
# → "0 created, 6 left untouched." Every file reported as `exists … (left untouched)`.
# No new LOG.md entry: a run that created nothing is not a change.
```

### What is worth your judgement here, not just green output

- **Open `course/syllabus/syllabus.md`.** Is the skeleton one you would actually want to fill in? Is
  anything a Bologna descriptor needs missing? *(D-032's descriptor parts exist as **body
  sections** — "Level, type and when offered", "Teaching methods", "Reading" — and `reading:` as a
  commented-out front-matter block. `level`, `course_type`, `offered` and `teaching_methods` are
  not front-matter fields; their absence there is expected.)*
- **Open a session file and `in-class.md`.** Do the TODOs tell you what to write?
- Does `validate`'s output read like something you would act on, or like noise?

---

## Step 0 — the overwrite-safe write path

*Tested after Step 1: it needs a course to write into.*

**What it should deliver:** it must be *structurally impossible* for an agent to destroy your work by
forgetting to check (invariant 5, §8.6). Exit code **3** means refused, distinct from 2 (broke).

```bash
# A. new file → written
echo "hello" | .venv/bin/classkit write course/policies/test.md          # created, exit 0

# B. overwrite without permission → REFUSED, original intact
echo "DESTROYED" | .venv/bin/classkit write course/policies/test.md      # refused, exit 3
cat course/policies/test.md                                              # still "hello"

# C. ask before generating anything
echo "x" | .venv/bin/classkit write course/policies/test.md --dry-run    # refused, exit 3, nothing written

# D. explicit confirmation → replaced
echo "new content" | .venv/bin/classkit write course/policies/test.md --overwrite   # replaced, exit 0

# E. identical bytes → no-op, so re-running a command stays safe
echo "new content" | .venv/bin/classkit write course/policies/test.md    # unchanged, exit 0
```

**B is the one that matters.** If it ever writes, the guarantee is broken and that is a stop-everything
bug — the failure it prevents (silent loss of authored work) is unrecoverable.

Note the refusal message prints *what is already there*, which is what lets a command show you the
existing content and ask.

**Known limitation, already tracked (gap G-4):** agents still declare `Write`/`Edit` in their tool
front matter, so an agent *could* bypass `classkit write`. The guarantee becomes structural only when
those tools are removed, which happens per-agent in the steps where each agent is touched. So this
test proves the mechanism, not yet the enforcement.

---

## Step 2b — ingest (`/ingest`)

The test no code review can do: **your real, messy materials.** Copy (do not move) a real course's
slides, PDFs, Word files, past exams and a few odd files into `course/materials/source/` — unsorted,
with at least one deck *and* its PDF export, and one file in a format nothing reads. **Put a
published book and a solutions manual straight into `course/materials/source/private/`** — the
normal case, as `source/README.md` tells a teacher; moving a file into `private/` later is a
separate migration check (step 2c-1). Then:

```bash
.venv/bin/pip install -e .                       # new dependencies: python-pptx, python-docx, pypdf
.venv/bin/classkit add-url "https://www.youtube.com/watch?v=…" --note "a real video"
.venv/bin/classkit add-url "not a url"           # rejected, exit 2
.venv/bin/classkit ingest --preflight            # counts, what changed by name, unsupported, time — writes nothing
```

Then run **`/ingest`** in Claude Code and follow it through its four gates. At step 3 you should see
the classification table **before** anything is recorded, and be able to correct it (D-039).
Afterwards, by hand:

```bash
find course/materials/source -type f -exec shasum {} + | sort > /tmp/before   # snapshot source/
mv course/materials/source/<a deck>.pptx course/materials/source/renamed.pptx
.venv/bin/classkit ingest                        # "moved … (same id)", nothing re-converted
# edit one file in course/materials/ingested/, then change its source and re-run:
.venv/bin/classkit ingest                        # REFUSED, exit 3, your edit intact
.venv/bin/classkit validate                      # materials_not_ingested until you answer
tail -12 course/LOG.md                           # each hand run that changed something: "classkit ingest", "run by hand"
```

Point one study path's `ref` at a real anchor (`"M0001#slide-2"`) and one at a made-up one
(`"M0001#slide-999"`): `validate` passes the first and errors on the second.

### What is worth your judgement here

- **Is the extraction readable?** Open a few `ingested/` files. Slides that are mostly pictures will
  be thin — is it thin enough to mislead the classifier?
- **Are the titles sensible?** A deck's comes from slide 1's title only, else the file name (`.`,
  `-`, `_` read as spaces); a document's from its first heading, else metadata, else the file name;
  never a PDF's first line.
- **A deck and its PDF export stay two materials** (D-040): nothing should ask you about them.
- **Are the kinds and units right?** Units are guessed before any unit map exists, from "Lecture 3"
  and the like; how often is the guess wrong? (`/plan-units` will re-map them — D-039.)
- **Do book citations in the report give section / exercise / printed page**, not only `page-N`?
- **Is the coverage report true of your course?** That is the whole point of step 2b.
- **Did anything in `source/` change?** It must not: re-run the `find … | sort` line into
  `/tmp/after` (adjusting for the file you renamed) and `diff` the two.

---

## Step 2c-1 — private and instructor-only material; `classkit doctor`

**What it should deliver:** a published book can be ingested, cited and validated without its text
ever entering git; a solutions manual cannot be cited to students without an alert; and `doctor`
says what this machine is missing. Work in the course you built for step 2b, or a fresh one. The
scratch clone is already a git repository, which two of the checks need; commit the course in it
(locally — never push) before the "second machine" part below, so there is something to clone.

```bash
.venv/bin/pip install -e .
.venv/bin/classkit scaffold course --code X --title Y   # creates only what is missing — nothing on a course
                                                       # scaffolded by this version
tail -5 course/LOG.md                                  # …and logs that it did
.venv/bin/classkit doctor                              # ok / note / ACTION lines; exit 0 or 1
```

**The migration check** — a file ingested outside `private/` and moved in later. If your 2b run
put the book straight into `private/` (the normal case), add a published PDF outside it, ingest it,
and move that instead. Move (`mv`, by hand — this is the teacher's act) the textbook PDF and the
solutions manual into `course/materials/source/private/`. Then:

```bash
.venv/bin/classkit ingest --preflight                  # "Private: 2 file(s) under private/"
.venv/bin/classkit ingest                              # "moved … (same id)"; the committed copy becomes an index
git status --short course/materials                    # nothing under source/private/ or private-text/
git check-ignore -v course/materials/private-text/*    # each ignored by course/.gitignore
head -40 course/materials/ingested/M00NN-*.md          # text: index; pages, printed labels, sections — no body text
ls course/materials/private-text/                      # the full texts, this machine only
```

Then run **`/ingest`** again: it should start with `classkit doctor`, propose an `audience` for
every material with a reason for each `instructor`, and flag any published book still outside
`private/`. Confirm the manual as `instructor`. Then point one study path's `ref` at a page of the
manual and one in-class activity's `materials` at the same page:

```bash
.venv/bin/classkit validate                            # ALERT instructor_material_cited for the study path only
```

**A second machine.** Clone the course repo next to it (`git clone <your scratch clone> ta`) — the
clone has no `private/` and no `private-text/`:

```bash
cd ta && ../.venv/bin/classkit validate                # the same findings as on your machine
../.venv/bin/classkit doctor                           # note: "… not on this machine — index only here"
../.venv/bin/classkit ingest                           # nothing to do; nothing marked removed
cp -r ../course/materials/source/private course/materials/source/
../.venv/bin/classkit ingest                           # "full text … this machine only"
git status --short                                     # clean: nothing committed changed, no LOG.md entry
```

Finally, by hand: `git add -f` one file under `private/` → `validate` warns
`private_material_committed`; `git rm --cached` it again. Delete a private PDF in the TA clone and
run `classkit material remove M00NN` there → refused while the file exists, accepted once it is gone.

### What is worth your judgement here

- **Is the index useful?** With a real book's bookmarks, does it let you (and an agent) find
  "§6.2" or "printed page 45" without the text? Is a book without bookmarks still usable?
- **Is there really no body text in it?** Read one. Titles count: a PDF's title comes from its
  metadata or the file name, never its first line.
- **Did the classifier get `audience` right**, with reasons you agree with — and did it flag a
  published book outside `private/` (and nothing else)?
- **Is `doctor`'s output clear** to a teacher who has never heard of it? Is every `ACTION` line's
  fix something you could just run?
- **Do the agents say "index only here"** on the TA clone instead of quoting the book from memory?

---

## Step 2c-2 — the rest of the hand test's fixes, and D-041

**What it should deliver:** the hand test's findings fixed where it ran — run it again on **the same
real materials** (CLRS, the instructor's manual, the text-box syllabus, the three decks). Start from
a fresh clone and course, or re-run in the old one (then read "an old course" below first).

```bash
.venv/bin/pip install -e .                      # new dependency: fonttools (F-09)
.venv/bin/classkit doctor                       # "dependencies import: …, fonttools"
.venv/bin/classkit ingest --preflight 2>&1 | less
```

Expect: **no library noise** — no `fontTools is required…`, no `Previous trailer cannot be read`
above the report; a file the reader complained about is listed once, by name, with a count (F-03,
F-10). What changed is listed **by name and id** (F-23). No "suspected duplicates" and no
"embedded links" lines (D-040). The time estimate for ~2000 PDF pages says under a minute
(recalibrated on the teacher test: 2,204 pages took ~30 s on a recent Mac; an older machine may
take a few times longer — it is "rough"). Reader warnings are listed only for files about to be
converted, with "Usually harmless; check these files' extraction after ingest."

Then `/ingest` (or `classkit ingest`) and check, in the run summary and the files:

- **The text-box syllabus (F-06)** is extracted — module number, credits, lecturer — once each, not
  twice. If you hand-corrected its `ingested/` file last time, a changed source is refused as a hand
  edit; choose `--overwrite` for it once (F-27).
- **"Check these extractions"** lists the picture-heavy decks ("20 of 37 slides have no text") and
  any document that came out far smaller than its source (F-08).
- **Equations** on the Unit 2 slides appear as linear text in backticks, or `[equation]` (F-07).
- **CLRS page 40** (`M0005#page-40` in the hand test): `efficient`, `first` — not `efûcient`,
  `ûrst`; dashes and quotes readable. *This is the hypothesis behind adding fontTools; the
  automated tests can only check ligatures and silence — this check is the real one (F-09).*
- **Titles (F-12):** the manual and the solutions are titled from their file names, not
  `manual.dvi` / `public.dvi`; no PDF is titled by its first line.
- **No link was harvested** from the book's bibliography (F-13); the course Gem link in the Unit 1
  deck is visible in its ingested text as `[…](https://…)`, and the classifier **mentions** it and
  suggests `classkit add-url`.
- **The classifier** gives the textbook `units: all` (F-17), states the report's **scope** first
  ("no material yet" for units nothing reaches, not "thin"), and the report is saved to
  `course/materials/coverage.md` after you read it (F-19). Run `/ingest` again later: it asks before
  replacing the saved report, showing a `--diff`.

**Prose locators (F-26).** Put a wrong anchor in the saved report (`M0005#page-99999`):
`classkit validate` warns `material_locator_in_text`. The same in `LOG.md` is not checked.

**The refusal (F-24, F-25).** Edit one slide's text in an `ingested/` deck, then change a different
slide in the `.pptx` and run `classkit ingest`: exit 3, and the output shows **both** changes under
their slide numbers ("Slide 9: …"), not the front matter. Then `classkit validate`: the warning
names `classkit ingest --keep M00NN` / `--overwrite M00NN`, not "Run /ingest".

**Write path (D-041, D-040).**

```bash
ls -l course/course.yaml                         # -rw-r--r-- — not -rw------- (G-22)
sed 's/units: 13/units: 12/' course/course.yaml | .venv/bin/classkit write course/course.yaml --diff
# a unified diff of the one line; nothing written. Then the same with --overwrite.
```

**Private material (D-041).** In the TA clone from step 2c-1, with the book copied in: a teacher's
newer printing on one machine and the old PDF on the other — `doctor` on each says, as a **note**,
that its copy differs from the one the committed index was built from, and that the last machine to
ingest wins. A full text extracted on the other machine (another pypdf) is not treated as an edit.

**`.gitignore` (D-041).** Delete `course/.gitignore` → `validate` warns `course_gitignore_missing`;
re-run `scaffold course` to get it back. `classkit mode developer` in a clone whose `.gitignore` is
not tracked refuses.

**An old course** (ingested before 2c-2): links harvested from materials last time (M0011–M0021 in the
hand test) are marked removed by the next ingest, each with a line saying links now come only from
`links.md`; `classkit add-url` for the one you want (the course Gem) brings it back **under its old
id**. `private_text_hash` disappears from the manifest as materials are re-converted.
The extraction fixes apply only to what is **re-converted**: an unchanged source keeps its old
`ingested/` file (`classkit ingest --overwrite M00NN` re-converts one), and **a title is never
replaced** — re-ingest keeps every title, the teacher's or ingest's own — so `manual.dvi` stays
until you `classkit material set M0001 --title "…"`. To see F-06…F-12 as a new teacher would, use a
fresh course.

### What is worth your judgement here

- **Is the CLRS text now readable** where it was not (F-09)? If not, fontTools was not the cause —
  report what you see on `M0005#page-40`.
- **Are the low-yield lines right** — do they flag the decks you know are pictures, and nothing
  that reads fine?
- **Is the refusal diff enough to decide** keep or overwrite without opening the files?
- **Does the coverage report's scope read as honest** about what is not uploaded yet?
- **Does the coverage report quote the private book?** It must not (D-042). Run
  `.venv/bin/classkit doctor` after `/ingest`: any committed file sharing 12+ consecutive words
  with a private full text is an ACTION. Also read the report yourself — the check catches copying,
  not close paraphrase.

---

## Step 3-syllabus — `/plan-syllabus`, approval and `classkit status` (D-043)

**What it should deliver:** a syllabus you would be willing to upload — drafted best effort from
your real materials, with nothing invented — revised with you, and approved. **The agent's output is
the thing under test**; the tooling around it is small. Use the real course: a fresh clone and course
(Steps 2c-1/2c-2 for ingest), with the old syllabus, the textbook (in `private/`), and the decks.

Ask the chat **"where does the course stand?"** It runs `classkit status`:

```
Syllabus  NOT STARTED: the scaffolded placeholders — run /plan-syllabus
Units     13 in course.yaml / no unit map yet; Materials: none ingested yet
```

Run `/ingest` first (status then shows the materials and "coverage report: materials/coverage.md"),
then `/plan-syllabus`. Check, step by step:

- **Step 0** shows the status, and `/ingest` now shows it too, before `doctor`.
- **Step 1 — evidence.** It names the old syllabus, the book's index and the decks by id, says how
  far each reaches, which form it will mirror (your old syllabus's sections), and asks **only** what
  the evidence does not answer — credits if the old syllabus lacks them, grading, office hours.
  Each question says what the draft will do if you leave it unanswered. It waits.
- **Step 2 — the draft** is written through the write path: the first write is refused (the
  placeholders are there); it tells you so and asks before replacing them. Then it checks the
  course — no errors; `syllabus_workload_missing` only if workload is TBD.
- **The report** says where each part came from, gives the outcomes-against-units table, and lists
  every **TBD** and guess.
- **Step 3 — revise, in the chat** (D-044). Ask for one change ("CO2 is too broad — split it"):
  the chat makes it itself, shows a diff touching only that (and its prose in the body), and writes
  on your OK; a log entry follows. Edit the file by hand between rounds — the next round keeps your
  edit. Ask for something structural ("reorder the map around graphs first") and it should send
  `syllabus-designer` off for a **rework** instead.
- **Step 4 — approve.** Say "approve". Then, in the chat:
  - "show me the status" → `Syllabus  APPROVED: approved 2026-…`
  - edit one word in the body yourself, then "show me the status" → `APPROVED, EDITED SINCE`
  - reword only a YAML comment → still `APPROVED` (comments are not part of the hash)
  - after an edit, "approve the syllabus again" → re-approved; the record replaced in place. On an
    **unchanged** file it is a no-op: `unchanged … not edited since — nothing to record`, no log entry
  - "show me the last log entries" → `classkit approve syllabus … re-approved …`

  By hand: replace the block with `approved: {date: 2026-10-05}` → status says "edits since
  cannot be tracked", and checking the course gives no error.
- **`/review-syllabus`** (optional): the critic's findings, ordered by damage, broken vs. taste;
  nothing written; fixes go back through `/plan-syllabus`.

### What is worth your judgement here

- **Would you upload the body as it is** — after filling the TBDs? Does it mirror your institution's
  form (your old syllabus's sections and order)?
- **Is anything invented?** Credits, weights, a policy, a prerequisite, a date you never gave and
  the old syllabus does not have. This is the failure that matters most.
- **Are the outcomes outcomes** — assessable capabilities, a handful, each spanning units — not
  topic labels or one per unit?
- **Is the unit map right**, and are its `evidence` locators the right slides and pages? A locator
  that does not exist is warned about (`material_locator_in_text`, D-044); one that exists but is the
  wrong slide is not — open a few.
- **The AI-use policy** — proposed, concrete, and marked as a proposal?
- **Did it quote the private book?** Ask "what does doctor say?" after the draft — any ACTION is a D-042
  breach. Read the Reading and Course description sections yourself too.
- **Did the gates hold** — one step at a time, nothing written before you saw it (except the draft,
  which is written to be read, and shown at once)?

## Step 3-units — `/plan-units`, unit states and `classkit approve unit` (D-046)

**What it should deliver:** for the units you name, plans you would teach from — objectives that are
real capabilities, each serving one of your Course Outcomes, drawn from that unit's own material,
nothing invented — revised with you and approved, unit by unit. **The agent's output is the thing
under test.** Use the same real course as the syllabus section, with the syllabus approved; plan
**two units whose material is ingested** (say 1 and 2), and later one unit with none.

Everything below is said in the chat.

1. **"Bring the materials' unit hints into line with the map"** (or accept `/plan-syllabus`'s offer
   of step 5 after approving). It shows only the rows that would change — material, units now →
   proposed, and why (a map entry's evidence, a deck's title slide); asks whether you set any hints
   yourself; keeps those unless you agree; records your confirmed rows in one `classkit material
   apply`, then logs.
2. **`/plan-units 1 2`.**
   - **Step 0** shows the status (`U01 … not started`), runs `doctor`, says which private materials
     are index-only here. Try it once with the syllabus *not* approved: it should say so and **ask**
     whether to go on — not refuse.
   - **Step 1** — per unit: an objectives-against-outcomes table (each objective → its CO, the
     locator it rests on); anything serving no outcome named plainly; prerequisites; what does not
     fit the week's budget with a proposal (cut / optional / move); **difficulties** — it asks what
     your students find hard, and may propose classic ones as `origin: proposed`. Accept one, reject
     one, add one of your own. It waits.
   - **Step 2** — it scaffolds the unit with the **map's title**, writes `unit.md` through the write
     path (refused first — the placeholders are there; it says so and asks), then checks the course:
     no errors, no `unit_map_mismatch`, no `objective_maps_to_outcome`; it **names** the expected
     `objective_coverage` alerts for objectives beyond the placeholder sessions, rather than "fixing"
     them. Open `unit.md`: your accepted proposal is `origin: proposed`, yours `origin: teacher`,
     the rejected one is nowhere.
3. **Revise in the chat.** "U01-O2 is really two things — split it": the chat does it itself, shows
   a diff touching only that, writes on your OK, logs. Edit `unit.md` by hand between rounds — the
   next round keeps your edit. Ask for an objective your syllabus has no outcome for: it should
   **say** it serves no outcome and offer `/plan-syllabus`, not attach it to the nearest CO.
4. **"Approve unit 1."** Then:
   - "where does the course stand?" → `U01  …  planned 2026-…`, and a count line (`1 planned, 1
     drafted, 11 not started`)
   - "check the course" → the `objective_coverage` alerts for unit 1 are **gone**: a planned unit is
     not checked for it (D-047)
   - the chat ran `classkit approve unit 1 --stage planned` — the stage is always named (D-047)
   - edit one objective's wording by hand → `planned … — edited since`
   - "approve unit 1 again" → re-approved as **planned** (the plan changed), the record replaced in
     place; the log says what it was
   - edit a placeholder session → unit 1 is **not** "edited since" (a planned unit's hash is
     `unit.md` only)
   - change a unit's `title` so it differs from the map → checking the course warns
     `unit_map_mismatch` against that `unit.md`; change it back
5. **`/plan-units 7`** for a unit with **none of your own material** (no deck, no notes of yours).
   With the textbook ingested (`units: all`) a unit is rarely without *any* material — the book and
   the unit map's evidence reach it — so what this tests is the difference that matters: the book
   says what *could* be taught; your material says what you teach and at what level. It should say
   which it has, and **not** draft objectives at the book's depth as though they were your plan —
   at most a sketch, labelled "scope not confirmed", if you ask. (To test a unit with no material
   at all, use a course without the book ingested.)
6. **`/review-unit 1`** (optional) on the planned unit: the critic reviews the **plan** (objectives,
   outcomes stretched to fit, load, prerequisites, difficulties), not the placeholder sessions;
   nothing is written.

By hand: `approved: {date: 2026-10-05, stage: planned}` without a hash → status says "edits since
cannot be tracked", and checking the course gives no error. Without `stage` it is a schema error.

### What is worth your judgement here

- **Would you teach from these objectives?** Assessable capabilities, the methodology's number per
  unit, broader than a guiding question and narrower than an outcome — not subject labels.
- **Are the outcome links honest?** Each objective's CO is one it really serves; an objective that
  serves none is *said*, not hidden.
- **Did it read your material, or the textbook in its head?** Open a few locators. For an index-only
  book, did it say so?
- **The load.** Did it notice what a three-hour lecture week cannot fit, and leave the cut to you?
- **Difficulties** — specific enough to design a class activity against? Were proposals few,
  classic, marked `proposed`, and recorded only when you accepted?
- **Did it quote the private book?** "What does doctor say?" after step 2.
- **Did the gates hold** — one step at a time, nothing written before you saw it?

---

## Expected noise — do not report these as bugs

| What you will see | Why | Tracked as |
|---|---|---|
| Many `guiding_question_assessed` warnings (12 for one unit) | Only entry-quiz items exist in Core, and a short quiz cannot test every guiding question. Decided to be `off` in Core — not yet implemented | D-031c, step 5 |
| `syllabus_workload_missing` | `workload` is optional by design so a syllabus validates before credits are settled | D-031d |
| `unit_count`: "N of 13 units exist so far" | Informational while the course is being built | — |
| `objective_coverage` ALERT for U0N-O3 or -O4 **before** the plan is approved | The placeholder sessions name only the first two objectives. Once you approve the plan (*planned*), the rule is skipped for that unit until it is designed | D-046, D-047 |
| No `outcome_coverage` check (an outcome no objective serves) | Parked: a completeness rule, useful only once every unit is planned | D-046 |
| A material's `kind` is `other` right after `classkit ingest` | Kind is only guessed from the format; the classifier sets it in `/ingest` step 3 | D-035 |
| Link titles are their URL or note | Metadata fetching is best-effort; offline, or a site that blocks it, gives no title | D-035 |
| `doctor`: "pandoc / LibreOffice is not installed" notes | They are optional; a note, not an action, unless you want those formats read | D-035, D-040 |
| `doctor` on a clone: "… not on this machine — index only here" | A TA's clone without the book is normal; it is a note and `doctor` still exits 0 | D-040 |
| "Check these extractions": "N of M slides have no text" for decks made of pictures | Text in images is not read without OCR; the line is there so thin extraction is not mistaken for thin teaching | D-040, F-08 |
| `doctor` note: "this machine's copy … differs from the one the committed index was built from" | Two machines with different copies of a private book; the last to ingest rebuilds the index | D-041 |

Anything **else**, especially any **error** on a freshly scaffolded course, is a real finding.

---

## What to do with what you find

- A defect in what was built → fix it, or note it for the next implementation session.
- Something the spec did not say → it belongs in a gap report, like
  `reviews/impl-gaps-step-0-1.md`. Gaps found by *using* the thing are worth more than gaps found by
  reading it.
- Something that works but reads badly, or does not match how you would teach → that is the
  judgement no test can make, and the main reason to do this by hand.
