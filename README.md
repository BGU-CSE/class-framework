# class-framework

A framework for developing and maintaining a university course **with AI agents as working
partners** — versioned in git, structured on disk, authored with specialized agents, and checked by
tooling that catches structural mistakes before students see them.

A general-purpose chatbot can help you write a paragraph, but it cannot work on *your course*: it
has no map of what the course is, what unit 7 contains, or what changing one goal would affect. Give
the course an explicit structure and it becomes something agents can operate on.

Its first purpose is a specific transformation — taking a conventional course of **three weekly
lecture hours across 13 weeks** and turning it into a **flipped course**:

```
COURSE
├── Syllabus — goal, Course Outcomes (CO1, CO2 …), workload, prerequisites
│     Every unit objective rolls up to an outcome, so "do the units together
│     deliver what the course promised?" is a question the tooling can ask.
│
└── UNIT = one week = 150 min
    ├── AT HOME  100 min = 2 × 50        goal: acquisition
    │   └── 4 × Study Session (~25 min)
    │       ├── 3–5 Guiding Questions — each a question the student should be
    │       │     able to answer, carrying:
    │       │       · answer — where the correct answer is found (a textbook
    │       │         section, a slide, a video timestamp). Never the answer
    │       │         itself: course content stays out of the repo.
    │       │       · est_minutes — teacher-approved study time. The session's
    │       │         25 minutes is the sum of these.
    │       └── Study Paths — an optional pool of alternative resources for the
    │             session. Not exhaustive; students may use their own instead.
    └── IN CLASS  50 min                 goal: application, not re-explanation
        └── Activities, opening with the entry quiz — misconception debrief,
            worked examples, small-group work, synthesis
```

The **Guiding Question** is the atomic unit of the whole system. Assessment items and in-class
activities reference question IDs. That is what lets the tooling check the design rather than merely
store it.

## What the tooling actually enforces

A flipped course fails in two predictable ways. Both are caught mechanically:

- **The class hour quietly becomes a lecture again.** In-class activities are built on that unit's
  guiding questions. An activity that references none is allowed — exam logistics, a current-events
  hook — but the **total time spent on such activities is capped**, because an hour made of them is
  a lecture.
- **"Two hours at home" turns out to be fiction.** Each guiding question carries a teacher-approved
  study time, and a session's questions have to sum to roughly its length. The budget is arithmetic,
  not an assertion.

Alongside those: every guiding question records where its answer can be found, objectives roll up to
Course Outcomes and are covered by questions, references resolve, IDs are consistent, activity
durations sum to the hour, and assessment items test something somebody was asked to learn.

Because agents author the content, something has to catch what agents get wrong. That is why the
framework validates — not rigour for its own sake. **Code verifies; agents judge.**

## Status

**Core is being implemented.** Its design is complete and independently reviewed; the schemas,
templates, scaffolding, validator and the overwrite-safe write path exist and are tested. The
agent layer — agents, skills and the `/` commands — is written but **has never been run against a
real course**, and is being brought up to the current design one step at a time.

`dev/ROADMAP.md` carries the implementation plan and a ledger which is **authoritative for what
actually exists**. Not built: exams, the Gem builder, PPTX export, Moodle sync.
<!-- homework-module:start -->
Homework is designed as a separate module ([`dev/homework/HOMEWORK-SPEC.md`](dev/homework/HOMEWORK-SPEC.md));
its agents and commands exist, but `classkit validate` does not check homework yet.
<!-- homework-module:end -->

**Teachers start at [GETTING-STARTED.md](GETTING-STARTED.md).** **Developers start at
[dev/VISION.md](dev/VISION.md)** — why the project exists and what it produces — then
[dev/FRAMEWORK-SPEC.md](dev/FRAMEWORK-SPEC.md), which specifies what the framework must contain. The
rest of this file is a summary.

## Starting a course

A course lives in **its own repo**, created by cloning this one and repointing `origin`.
Keeping this repo as a second remote is what lets you pull framework improvements later
without re-applying them by hand.

```bash
git clone https://github.com/BGU-CSE/class-framework.git my-course
cd my-course
git remote rename origin framework
git remote add origin https://github.com/<owner>/my-course.git   # create it first, PRIVATE
git push -u origin main

pip install -e .

classkit scaffold course --code "202-1-2051" --title "Introduction to Data Structures"
classkit scaffold unit 1 --title "Asymptotic analysis"
classkit validate
```

Later, to pick up framework improvements:

```bash
git fetch framework && git merge framework/main
```

> **Editing framework files in your own repo is allowed** — it is your repo. The cost is that
> `git merge framework/main` will then conflict on exactly those files. If you want painless
> updates, add new files rather than editing existing ones. If you never plan to pull, edit freely.

## Who does the work

The design work is done by **agents running in the teacher's own Claude Code**, inside their course
repo. The tooling exists to give those agents a target format and to catch them when they get it
wrong.

| Agent | Responsible for |
|---|---|
| `syllabus-designer` | The syllabus: course goal, Course Outcomes, workload |
| `curriculum-architect` | The semester map — units, objectives, sequencing |
| `study-session-designer` | Home study: guiding questions, their answers and study times |
| `assessment-writer` | Items with diagnostic distractors and real rubrics |
| `lesson-planner` | The 50-minute meeting, built from activities |
| `topic-researcher` | Finding **real**, verified study resources |
| `course-critic` | Adversarial review of what the validator can't see |
| `gem-builder` | The class Gem bundle — *later phase* |

Teacher-facing commands: `/ingest`, `/plan-units`, `/design-unit N`, `/write-items N`,
`/review-unit N`. (`/build-gem N` is a later phase.)

Commands are **stepwise**: each announces a step, produces it, shows you the result and waits for
your approval before the next. Nothing overwrites work you authored without asking you first — that
one is enforced in code, not by instruction.

Shared craft lives in skills — `writing-guiding-questions`, `estimating-study-time` — so the
designer, the critic and the assessment writer apply the same standard.

## Commands

| Command | What it does |
|---|---|
| `classkit scaffold course` | Create the course tree, including the syllabus |
| `classkit scaffold unit N` | Create a unit with its study sessions and lesson plan |
| `classkit scaffold session U05 5` | Add one more study session to a unit |
| `classkit scaffold item U05` | Add an assessment item |
| `classkit validate` | Check the course against its methodology and schemas |
| `classkit write` | The write path agents use — refuses to replace existing content without explicit confirmation |

Scaffolding **never overwrites**. Re-run it any time — you get whatever is missing and keep
everything you wrote. Skipped files are reported.

## Layout

```
.claude/agents/     the agents that do the design work
.claude/skills/     shared craft: writing guiding questions, estimating study time
.claude/commands/   teacher-facing workflow: /ingest, /plan-units, /design-unit ...
.claude/hooks/      reports whether a session is in teacher or framework-developer mode
schemas/            JSON Schema for every content type — the contract
methodologies/      pluggable study-session designs; question-driven-25 is the default
defaults/           advisory time constants, used to propose study-time estimates
templates/          what scaffold copies into a course repo
src/classkit/       the tooling
tests/              scaffold → validate round-trip, and the write path
dev/                framework-development docs (vision, spec, roadmap, build log);
                    not a teacher's concern
```

There is deliberately **no `course/` directory here**. Course content lives only in course
repos, created entirely by `classkit scaffold`. That is what keeps framework updates and
teacher content from colliding.

## Methodologies

`question-driven-25` — four 25-minute sessions per unit, 3–5 guiding questions each — is one
implementation of a contract, not a fixed rule. Another teacher can drop a different YAML file
into `methodologies/` and select it in `course.yaml`. Downstream tooling consumes the *output*
(`goals[]`), never the methodology that produced it, so the rest of the framework keeps working.

No tool or agent may hardcode "4 sessions", "25 minutes", or "3–5 questions". Those are read
from the methodology file.

## License

MIT. See [LICENSE](LICENSE).
