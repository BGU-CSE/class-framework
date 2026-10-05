---
name: planning-units
description: The standard for a planned unit (units/NN-slug/unit.md) — unit objectives that are assessable, broad and few, each naming the Course Outcome it serves; prerequisites and home-study order; the load across weeks and what a lecture week loses when it is flipped; the difficulties students meet and where each came from; and how to revise a plan without undoing the teacher's edits. Use when planning, revising or reviewing a unit's plan — by curriculum-architect, by the chat during /plan-units revision rounds, and by course-critic when it reviews a unit's plan.
---

# Planning a unit

A unit is one week's subject. Planning it decides **what** that week teaches — its objectives, what
it builds on, and what students will find hard — before anyone designs **how** they learn it (the
study sessions and the class hour, `/design-unit`). This skill is the one standard for a plan: the
agent that drafts it, the chat that revises it with the teacher, and the critic that reviews it all
work to what is written here, so the teacher never gets contradictory advice.

**Units are planned a few at a time, as their material arrives** (D-040, D-046). The syllabus is
whole from the start — its Course Outcomes and its unit map cover the semester — but a unit's
objectives come from **that unit's own material**: its slides, the book's chapters read in depth.
A unit with no material yet stays on the map, unplanned. Plan from evidence, ask the teacher where
there is none, and never plan from memory as though it were fact.

**Best effort, approved, not perfect.** Draft as well as the evidence allows; the teacher revises
and approves (`classkit approve unit N --stage planned`). Downstream builds on what was approved.

The shape is `schemas/unit.schema.json`. The numbers — how many objectives a unit has, the minutes
of home study, the sessions, the class meeting — come from `methodologies/<name>.yaml` (`unit`,
`home_study`, `in_class`); never assume them.

## What a planned unit holds

### `title` and `number` — from the syllabus's unit map

The unit map in `syllabus/syllabus.md` is authoritative for which units exist, their order and
their titles (D-040). Copy the map entry's `title` exactly. If the unit's material suggests a
different title or scope — the deck covers heaps *and* priority queues, the map says only heaps —
that is a change to the syllabus: say so, and leave both files as they are until the teacher
decides (`classkit validate` warns while they differ: `unit_map_mismatch`).

### `summary` — a line or two, for the teacher

What the week is about and what it is for in the course: "Heaps as the structure behind priority
queues and heapsort; sets up the greedy graph algorithms of U08." Not a list of subtopics.

### `objectives` — what a student can do after this week

The methodology sets how many (`unit.objectives`: min–max). **Few and broad, on purpose.** Unit
objectives are the abstract, teacher-facing layer — what accreditation paperwork and prerequisite
tracking read. The working layer is the guiding questions that `/design-unit` writes under them,
several per objective. If you find yourself writing eight objectives, you are writing guiding
questions in the wrong layer.

Each objective is a **capability statement** a teacher could assess:

| Not an objective | An objective |
|---|---|
| Heaps | Implement the heap operations and argue their running times |
| Understand heapsort | Explain why heapsort runs in O(n log n) in every case, and when it is chosen over quicksort |
| Be familiar with priority queues | Choose a priority-queue implementation for a given workload and justify it |

Three tests, for each objective:

1. **Assessable** — could an exam item or a class activity tell whether a student has it? "Understand",
   "know", "be familiar with" fail: nothing follows from them. Use a verb something follows from —
   explain, analyse, choose and justify, implement, prove, compare.
2. **The right size** — broader than one guiding question (a single fact or step), narrower than a
   Course Outcome (which spans several units). Three to five guiding questions should fit under it.
3. **Grounded** — the unit's material actually teaches it. An objective nothing in the material
   reaches is either a gap in the material (say so) or not this unit's objective.

`bloom` where it is clear; leave it out rather than guess.

**`outcomes` — every objective names the Course Outcome(s) it serves.** Only ids the syllabus
declares (`CO1`, `CO2`, …); read them from `syllabus/syllabus.md` — never invent one, never assume
the numbering. An objective serves an outcome when achieving it is part of what the outcome claims.
Usually one, sometimes two; an objective that serves every outcome serves none in particular.

- **An objective that serves no outcome** — a real part of the week that the syllabus's outcomes
  do not cover. Do not attach it to the nearest outcome to make the alert go away
  (`objective_maps_to_outcome`). Say so: either the syllabus is missing an outcome (a syllabus
  change, the teacher's call) or the objective is not worth a place in the week.
- **An outcome the unit map says this unit builds, that no objective serves** — say so too.

**Ids are stable.** `U03-O1`, `U03-O2`, … in order. Once study sessions exist, their guiding
questions reference objectives by id (`goals[].objectives`); renumbering or deleting an objective
breaks those references. When revising a designed unit, add new ids rather than reusing old ones.

### `prerequisites` — the earlier units this one needs

The units whose content a student must already have — `[U01, U02]` — not every earlier unit. Read
the earlier units' plans (`units/*/unit.md`) and the map for the ones not yet planned.

- **A prerequisite on a later unit**, or a cycle, is a design error in the order: report it, do not
  paper over it.
- **A prerequisite on a unit not yet planned** is fine — the map says what it will cover — but say
  that the dependency rests on the map, not on a plan.
- **Something assumed that no earlier unit teaches** (and the course's prerequisites in the syllabus
  do not cover) is a finding: name it.

### `difficulties` — what students find hard (optional)

Misconceptions and sticking points: what students get wrong, or where they get stuck, in this
week's material. The class hour is built to repair them, and the entry quiz to detect them, so a
difficulty must be **specific enough to design against**:

| Too vague | Specific |
|---|---|
| Students find recursion hard | Students trace the recursive calls but cannot say what each call returns |
| Big-O is confusing | Students read O(n) as the exact running time rather than an upper bound |

Each records where it came from — **`origin`**:

- **`teacher`** — the teacher said so (in this conversation, an earlier unit, the course log), or it
  is already in the file. This is the valuable kind: what *these* students actually got wrong.
- **`proposed`** — an agent proposed it: a classic difficulty of a **well-known subject**, which the
  teacher **accepted**. It stays marked `proposed` — still a guess about these students — so the
  entry-quiz and class-hour agents later know which difficulties are known and which are guessed.

**Ask the teacher first.** In a newly flipped course they may not know yet; "none yet" is a full
answer, and planning goes on without (they can add difficulties after teaching the unit once).
**Propose only** what is a well-documented difficulty of the subject, a few at most, each specific;
never for a subject you know little about. **A proposed difficulty is recorded only if the teacher
accepts it.** The material may hint at one ("a common mistake is…" on a slide) — that is evidence;
cite it by locator, and it is still `proposed` until the teacher confirms it.

### The body — teacher notes

Keep the scaffolded headings (the home-study and class-meeting lines). Add a short
**`## Plan notes`** section where it helps the teacher next year: the material the plan rests on, by
locator (`M0007#slide-1`, `M0003#page-63`); what was cut or made optional, and why; open questions.
Not student-facing; never text copied from a private material.

## The week's load — a lecture week is not a flipped week

The methodology's numbers are the budget: so many minutes of home study in so many sessions, one
class meeting. Three lecture hours often cover more than that can carry. Read the unit's material
against the budget:

- **What does not fit.** Name it, and propose what to do — cut, make optional, move to another unit
  — but **cutting is the teacher's decision**. Never silently compress: a flipped unit that pretends
  to cover exactly what three lecture hours covered is how the home-study budget quietly doubles.
- **Home-study order, not lecture order.** A lecture can defer motivation ("we'll see why in three
  weeks"); a student alone with an unmotivated definition stops. The objectives' order is the order
  the week is studied in: the problem before the tool.
- **The load across weeks.** Compare with the neighbouring units, planned or on the map: three heavy
  units in a row with no consolidation is a real problem, not a scheduling detail. Say it.

## Evidence — where a plan comes from

In order of weight:

1. **The unit's map entry** — its `summary` and its `evidence` locators: what the syllabus's plan
   for this unit rests on.
2. **The unit's materials** — in `materials/manifest.yaml`, the materials whose `units` include it
   (or `all`, course-wide: the textbook, read the relevant chapter). **`roles` decide their weight
   (D-048): `scope` material — the teacher's decks and annotated notes — decides *what* the unit
   teaches and *how deep*; `reference` material — the book — fills in the detail and the exact
   places to cite, and never widens the scope on its own.** In an annotated document, the
   **Teacher's annotations on this page** blocks are the strongest signal there is: a highlight
   says "this matters", a margin note ("On board", "Ask in class", "Show on cards") says how it is
   taught — read them before the page's text, and say in the plan notes which ones shaped the plan.
   A unit with only `reference` material is planned only if the teacher chose to, and then labelled
   *provisional — scope not confirmed*. `units` is a hint, not a fact:
   a deck's title slide or a chapter's contents decide. Read the **ingested** copy
   (`materials/ingested/`), never `materials/source/`; its anchors (`## Slide 18`, `## Page 34`) are
   the only places a locator can name.
3. **`materials/coverage.md`** — `/ingest`'s dated report: what the materials reach, unit by unit.
   Input, not truth.
4. **The course log** (`LOG.md`) and earlier units — what the teacher decided, and how the units
   before this one were planned.
5. **The teacher** — for everything the material does not say.

**Private material** (a published book, `private: true`) is committed only as an index; its full
text is in `materials/private-text/` where this machine has it. Read that when it is there. Where it
is not, the book is **index-only here**: its table of contents tells you what a chapter covers, not
what it says — say so, and never present recall of the book as a reading of it.

**Instructor-only material** (`audience: instructor` — a solutions manual, a past exam) may inform a
plan — a past exam shows what the course has assessed — since the plan is the teacher's. Say when
you used it.

## Revising — change what was asked, leave the rest

Most of a plan's life is revision: during `/plan-units`, after the teacher teaches the week, next
year.

- **Re-read the file first.** The teacher may have edited it by hand; their edits are theirs — never
  revert them.
- **Change what was asked, and whatever must change with it** (an objective reworded → its
  `outcomes` checked again). Leave everything else as it was — including YAML comments, the ids,
  and the `approved` block, which only `classkit approve unit N` (or the teacher, by hand) writes.
- **A request that conflicts with the rest** (an objective the syllabus has no outcome for, a title
  that differs from the map): make the change and say what now disagrees, rather than silently
  "fixing" the other file.
- **Show the change before writing it** (`classkit write … --diff`), then write it on the teacher's
  OK (`--overwrite`). An edit after approval is normal; `classkit status` will say "edited since".

## Rules

- **No invented outcomes or resources.** Every `outcomes` id is one the syllabus declares; every
  locator is one whose anchor you have seen in the ingested file, written in full — `M0005#page-39`,
  never `#page-39`.
- **Citing a book** — a page locator is the PDF's page (`M0003#page-63`), often not the printed one;
  also give the book's own coordinates (chapter or section, printed page).
- **Never copy text from a private material** (D-042) into any course file — say it in your own
  words, cite it by locator; at most a short phrase in quotation marks. `classkit doctor` flags 12 or
  more consecutive words shared with a private text.
- **No difficulty recorded as known that the teacher did not give**: a proposal is `origin:
  proposed`, and recorded only once accepted.
- **Say what you guessed.** The teacher judges the plan on their real course; an honest "the
  material does not say" is what lets them correct it.
