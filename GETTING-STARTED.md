<!--
  Written for the state this document ships in: the framework repo PUBLIC, teachers' course repos
  PRIVATE. The framework is private during development, so the clone below will not work for
  someone without access yet. That is expected — do not add an "ask for access" note; this file is
  only handed to teachers once the repo is public (ROADMAP Phase 6).
-->

# Getting started — for teachers

How you turn your existing course into a flipped one. You supply materials and settings;
Claude Code does the design work; the validator catches what went wrong.

You need [Claude Code](https://claude.com/claude-code) and Python 3.10+.

> **The framework is still being built.** The workflow below is the design; not all of it exists
> yet. `classkit scaffold`, `classkit validate`, `classkit log` and the materials tools
> (`/ingest`, `classkit ingest`, `classkit add-url`) work today. The `/` commands in step 5 are
> being implemented one at a time — `dev/ROADMAP.md`'s ledger is the authoritative list of what is
> actually built. Expect this document to change as they land.

---

## 1. Make your course repo

Your course lives in **its own private repo**, created by cloning the framework. Keeping the
framework as a second remote is what lets you pull improvements later without redoing them.

Create your course repo on GitHub first, and make it **private** — it will hold your assessment
material. Leave every "initialize this repository" box unchecked: a repo that starts with its own
README or licence has a separate history you would then have to merge.

```bash
git clone https://github.com/BGU-CSE/class-framework.git my-course
cd my-course
git remote rename origin framework
git remote add origin https://github.com/<owner>/my-course.git   # your private course repo
git push -u origin main

pip install -e .
```

Your course repo stays private; the framework it came from is public. Pulling framework updates
later works exactly the same either way.

## 2. Create the course tree

```bash
classkit scaffold course --code "202-1-2051" --title "Introduction to Data Structures"
```

That creates `course/`: the settings in `course.yaml`, an empty `units/`, a place for your existing
material, and **`course/syllabus/syllabus.md`** — the course's top layer. The syllabus holds the
course goal and its **Course Outcomes** (`CO1`, `CO2`, …): what a student who passes can do. Those
outcomes are the roof of everything below them — each unit's objectives roll up to them, so the
validator can ask whether your units together deliver what the course promised.

It also starts **`course/LOG.md`, the course log**: what changed in the course and *why* — the part
git's history does not record. The commands add an entry at each step you approve, and the agents
read the recent entries before they start work, so next year's revision knows what this year's
decided. Add your own entries by hand whenever something worth remembering happens ("taught U03 —
students found S02 too long"), or with `classkit log "taught U03" --changed "…" --why "…"`.

The syllabus is a **Bologna-style course descriptor**: alongside the goal and outcomes it has room
for level, course type, when it is offered, teaching methods, reading, workload and the assessment
scheme. Fill it in over time, or leave parts out — only the goal and the outcomes are required.

It is scaffolded with placeholders and is yours to edit. Its `workload` block is left commented out
deliberately, so you can draft a syllabus before credits are settled; `classkit validate` warns
until you fill it in. That is a reminder, not a failure.

Scaffolding never overwrites. Re-run it whenever you want the pieces you are missing — everything
you have already written is left exactly as it is.

## 3. Add your existing material

Drop whatever you already have into **`course/materials/source/`** — slides, PDFs, the syllabus,
past exams, reading lists, lecture notes. Any format. Nothing is required, and more is better:
the agents read this to work out what your course actually covers instead of inventing a
generic version of it.

It doesn't need to be organized — one folder of everything is fine, and duplicates (a deck and its
PDF export) are detected. For videos and web pages, list them in
`course/materials/source/links.md`, one per line with an optional note, or run:

```bash
classkit add-url "https://www.youtube.com/watch?v=…" --note "heaps explained, 12 min"
```

PowerPoint, PDF, Word, Markdown and plain text are read out of the box. OpenDocument, RTF, HTML
and EPUB need [pandoc](https://pandoc.org) installed; old `.ppt`/`.doc` need LibreOffice. Anything
else — and a scanned PDF with no text, or a video file — is recorded and listed, never silently
dropped; export it to PDF if you want it read.

Then run **`/ingest`** in Claude Code. It first shows you a **pre-flight report** — how many files of
each kind, slides and pages, duplicates, links, what it can't read, roughly how long it will take —
and waits for your go-ahead. It then turns everything into a readable, citable copy in
`course/materials/ingested/`, one file per source with every slide and page marked, and lists them in
`course/materials/manifest.yaml` under a stable id (`M0007`). An agent then proposes what each one is
(slides, exam, textbook, …, and which units it serves) — **you see and correct that before it is
recorded** — asks you before merging anything it thinks is the same material twice (a deck and its
PDF export), and reports what your course actually
covers and where it is thin. Each step you approve is recorded in the course log.

What that buys you: an answer reference can point at **`M0007#slide-18`**, and `classkit validate`
reports an error if that slide does not exist — a made-up "slide 18" of a 12-slide deck is caught
before it reaches a student. (It cannot tell whether the answer is *on* slide 18; that is still a
human's or the reviewing agent's call.)

- **Your originals are never touched.** Nothing in `materials/source/` is modified, moved or deleted.
- **⚠ Before you commit: everything in `materials/` goes into git** — the source files *and* their
  full extracted text in `ingested/`. A published book's PDF or a solutions manual pushed to GitHub
  stays in the repository's history even if deleted later. A `source/private/` folder that is kept
  out of git is designed but not built yet (D-040); until then, keep such files out of the course
  repo, or do not commit `materials/`.
- **Reorganize freely.** A renamed or moved file keeps its id, so nothing that cites it breaks.
- **Fix a bad extraction by hand** in `ingested/`. A later ingest notices your edit and asks before
  replacing it — you choose to keep your edit or take a fresh extraction.
- **Add material any time** and run `/ingest` again — only what's new or changed is processed, and
  an interrupted run picks up where it stopped. Until you do, `classkit validate` warns that some
  material is not ingested yet.
- **A deleted file** stays in the manifest, marked removed, so anything still citing it is reported.
- **Running `classkit ingest` yourself** is fine; it adds an entry to the course log saying what
  changed (`--why "…"` to say why).
- **Citing a book:** `M0003#page-63` is the 63rd page of the PDF, which may not be the page printed
  "63". So a book citation also says, in its note, the section, the exercise or question number, and
  the printed page — `CLRS §6.2, Exercise 6.2-3 (printed p. 45)`.

If your textbook isn't a file, record it in `course/course.yaml` under `textbooks:` — study
paths and answer references cite it by key.

## 4. Set your settings

The course's *aim* — its goal, outcomes, prerequisites and workload — lives in
`course/syllabus/syllabus.md`, which you edit directly. Everything *tunable* is in
**`course/course.yaml`**:

| Setting | What it controls |
|---|---|
| `units` | How many weeks (12 or 13) |
| `methodology` | The study-session design. Default `question-driven-25` |
| `textbooks` | Keys that study paths and answers cite, e.g. `CLRS` |
| `in_class.max_unmapped_minutes` | How much of the class hour may be spent on activities that build on no guiding question — exam logistics, a news item. Default 10 of 50. *Not built yet* |
| `time_constants` | Assumed reading, watching and exercise rates, used to *propose* study times |

Two of these are worth understanding rather than just setting.

**`time_constants` is advisory.** It does not decide whether a session fits its budget. The
session's time is the sum of a per-question `est_minutes` that **you approve** — the constants only
help the agents propose a sensible number in the first place, and help the reviewing agent notice
one that looks wrong. The shipped defaults are placeholders; adjust them to your students.

**`in_class.max_unmapped_minutes` is the guardrail on the class hour.** Most activities should build
on the week's guiding questions. A few legitimately do not, and those are fine — but if they add up
past this cap, the validator warns you, because an hour made of them is a lecture again. Raise it if your
teaching genuinely needs more; set it to the full hour to switch the guardrail off entirely. It is
your course.

To use a different pedagogy entirely, add a file to `methodologies/` and name it here. The rest
of the framework keeps working.

## 5. Let Claude Code build the course

Open Claude Code in your course repo and run these in order:

| Command | What it does |
|---|---|
| `/ingest` | Reads `materials/source/` and `links.md` — pre-flight, convert, classify — and reports what your course covers |
| `/plan-units` | Writes the syllabus — goal, Course Outcomes — then the unit map, each unit's objectives rolling up to those outcomes |
| `/design-unit 3` | The main event: the week's study sessions with their guiding questions, the entry quiz, then the in-class hour built on both |
| `/review-unit 3` | An adversarial critic — checks the hour genuinely depends on the prework |
| `/write-items 3` | More assessment items for the entry quiz |

*Homework, programming assignments and exams (`/write-items` in its full form) and the class Gem
(`/build-gem`) are later phases. They are not built.*

### How the commands behave

Hold them to this — it is how they are specified to work:

- **Stepwise, with your approval.** A command tells you what it is about to do, produces that one
  step, shows you the result, and waits. It does not design a whole unit and hand you the finished
  article. A correction at a checkpoint is applied before it moves on.
- **Never overwrite without asking.** If something is already written, you are shown what is there
  and asked first. This one is enforced by the tooling, not merely by instruction — losing work you
  authored is the one failure the framework must never have.
- **Revise rather than regenerate.** Where output already exists, the default is to change the part
  you asked about and leave everything else alone.

### What's actually happening

You only ever type commands. Each one is a short script that pulls in **agents** — specialists with
their own instructions, working in their own context.

`/design-unit 3` runs three of them in order: the **study-session-designer** writes the week's
guiding questions, their answer references and their study times; the **assessment-writer** then
produces the entry quiz; and the **lesson-planner** builds the hour last, because it needs both the
questions *and* the real quiz items it will refer to.

`/review-unit 3` runs the **course-critic**, which is deliberately a *different* agent from the ones
that did the work. An agent reviewing its own output is systematically generous. It is also the only
thing that can judge whether your study-time estimates are honest — the validator can check that
they add up, not that they are true.

You don't invoke agents directly, though you can — ask Claude Code to "use the topic-researcher to
find videos for unit 4" and it will.

Then, always:

```bash
classkit validate
```

Work **one unit at a time**. Review unit 1 properly before generating twelve more — the agents
learn your subject from what's already in the repo, so a good unit 1 makes unit 2 better, and a
bad unit 1 propagates.

## What the validator tells you

**You are the authority.** The validator catches what the agents get wrong and tells you what it
sees; it does not overrule you. It reports three kinds of finding:

- **Errors — broken data.** A reference to something that doesn't exist: a guiding question an
  activity names but nobody wrote, a quiz item that isn't there, a study path pointing at
  `M0007#slide-18` of a 12-slide deck. These are almost never intentional, and the agents can't work correctly over them.
- **Alerts — high priority, shown first.** Coverage: a Course Outcome no unit delivers, an objective
  no guiding question addresses, an objective that rolls up to no outcome, a missing syllabus. Often
  a temporary state while you build — but worth looking at.
- **Warnings — departures from good practice.** A session over its time budget, a guiding question
  with no recorded answer, a class hour drifting off the home study, a week with no class meeting.
  Sometimes that is exactly what you meant.

When a departure is deliberate, mark it so it stops nagging — in the front matter of the file the
finding is reported against. A week with no class meeting is reported against the unit's `unit.md`:

```yaml
accepted:
  - rule: in_class_missing
    reason: "holiday week — no class meeting"
```

— or change a rule for the whole course under `rules:` in `course.yaml` (e.g.
`session_count: off`). Agents never do this on their own; only you do. The rule's name is the one
`classkit validate` prints in brackets; a name it does not recognise gets a warning, because a
mistyped exception silently does nothing. A missing `reason` is allowed but also gets a warning —
the reason is what explains the exception to you, or a colleague, next year. Accepted exceptions are still counted at the end of the
report, so they never disappear from view.

Some checks only run once your unit map is complete — a half-built course is a normal state, and
the validator says when it has skipped something for that reason.

## What you still have to do yourself

The agents draft; they don't know your students. Expect to rewrite guiding questions that are
too easy, cut a study session that's overstuffed, and replace distractors that don't match the
misconceptions you actually see in office hours. The framework's job is to make that editing
cheap and to stop structural mistakes reaching your students.
