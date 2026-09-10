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

If your textbook isn't a file, record it in `course/course.yaml` under `textbooks:` — study
paths cite it by key.

## 4. Set your settings

The course's *aim* — its goal, outcomes, prerequisites and workload — lives in
`course/syllabus/syllabus.md`, which you edit directly. Everything *tunable* is in
**`course/course.yaml`**:

| Setting | What it controls |
|---|---|
| `units` | How many weeks (12 or 13) |
| `methodology` | The study-session design. Default `question-driven-25` |
| `textbooks` | Keys that study paths cite, e.g. `CLRS` |
| `gem` | Whether to build one Gem per unit, per course, or both |
| `time_constants` | How long you think students take to read a page, watch a video, work an exercise |

**`time_constants` matters more than it looks.** It decides whether the validator believes a
25-minute session is actually doable in 25 minutes. The shipped defaults are placeholders —
adjust them to your students.

To use a different pedagogy entirely, add a file to `methodologies/` and name it here. The rest
of the framework keeps working.

## 5. Let Claude Code build the course

Open Claude Code in your course repo and run these in order:

| Command | What it does |
|---|---|
| `/ingest` | Reads `materials/source/`, reports what your course covers and proposes a unit map |
| `/plan-units` | Writes the 12–13 unit skeletons with objectives |
| `/design-unit 3` | The main event: 4 study sessions with guiding questions and study paths, then the in-class hour |
| `/write-items 3` | Assessment items for the entry quiz and homework |
| `/review-unit 3` | An adversarial critic — checks the hour genuinely depends on the prework |
| `/build-gem 3` | The Gem bundle for that unit |

### What's actually happening

You only ever type commands. Each one is a short script that pulls in **agents** — specialists with
their own instructions, working in their own context.

`/design-unit 3`, for example, runs three of them in order: the **study-session-designer** writes
the week's guiding questions and study paths, then the **lesson-planner** builds the hour around
them (it cannot run first — it needs the questions), then the **assessment-writer** produces the
entry quiz.

`/review-unit 3` runs the **course-critic**, which is deliberately a *different* agent from the ones
that did the work. An agent reviewing its own output is systematically generous.

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

- An in-class activity that doesn't build on a guiding question. If the hour doesn't depend on
  the home study, it's a lecture with extra steps.
- A study session whose fastest complete path exceeds its time budget. That's how "two hours at
  home" quietly becomes four.
- A unit objective no guiding question addresses.
- An assessment item testing something students were never asked to learn.

Warnings are advisory. Errors mean the design is broken, not that the tool is fussy.

## What you still have to do yourself

The agents draft; they don't know your students. Expect to rewrite guiding questions that are
too easy, cut a study session that's overstuffed, and replace distractors that don't match the
misconceptions you actually see in office hours. The framework's job is to make that editing
cheap and to stop structural mistakes reaching your students.
