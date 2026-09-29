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
> yet. `classkit scaffold` and `classkit validate` work today. The `/` commands in step 5 are
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
`course/materials/source/links.md`, one per line with an optional note, or run
`classkit add-url URL --note "…"` *(not built yet)*.

`/ingest` then turns all of it into a readable, citable copy in `course/materials/ingested/` —
one file per source, with every slide and page marked — so that an answer can point at
`M0007#slide-18` and the validator can check that slide exists. Your originals are never touched,
and you can correct a badly extracted file by hand; a later ingest won't overwrite your fix without
asking. Add material any time and run `/ingest` again — only what's new or changed is processed.

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
past this cap, validation fails, because an hour made of them is a lecture again. Raise it if your
teaching genuinely needs more; set it to the full hour to switch the guardrail off entirely. It is
your course.

To use a different pedagogy entirely, add a file to `methodologies/` and name it here. The rest
of the framework keeps working.

## 5. Let Claude Code build the course

Open Claude Code in your course repo and run these in order:

| Command | What it does |
|---|---|
| `/ingest` | Reads `materials/source/`, reports what your course covers |
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

## What the validator will not let you get away with

- **A class hour that has drifted off the home study.** Activities reference the week's guiding
  questions; ones that don't are flagged, and if their total time passes
  `max_unmapped_minutes`, that's an error. If the hour doesn't depend on the prework, it's a
  lecture with extra steps.
- **A study session that doesn't fit its budget.** The session's guiding questions carry study
  times, and they have to sum to roughly the session length. That's how "two hours at home"
  quietly becomes four.
- **A guiding question with nowhere to find the answer.** Every question records where its answer
  lives — a textbook section, a slide, a video timestamp — unless you deliberately mark it as one
  to be resolved in class, in which case an activity has to pick it up.
- **A unit objective no guiding question addresses**, and an objective that rolls up to no Course
  Outcome.
- **An assessment item testing something students were never asked to learn.**

Warnings are advisory. Errors mean the design is broken, not that the tool is fussy. Some checks
only run once your unit map is complete — a half-built course is a normal state, not a failing one,
and the validator says when it has skipped something for that reason.

## What you still have to do yourself

The agents draft; they don't know your students. Expect to rewrite guiding questions that are
too easy, cut a study session that's overstuffed, and replace distractors that don't match the
misconceptions you actually see in office hours. The framework's job is to make that editing
cheap and to stop structural mistakes reaching your students.
