# class-framework

An agentic framework for building and maintaining a university course as if it were a
software project: versioned in git, structured on disk, checked by tooling, and authored
with the help of specialized agents.

Its first purpose is a specific transformation — taking a conventional course of **three
weekly lecture hours across 13 weeks** and turning it into a **flipped course**:

```
Unit = one week = 150 min
├── AT HOME  100 min = 2 × 50
│   └── 4 × Study Session (~25 min)
│       └── 3–5 Guiding Questions — each a question the student
│           should be able to answer
│           └── Study Paths: class Gem, video, textbook, exercise.
│               The student chooses their own route. None is mandatory.
└── IN CLASS  50 min — entry quiz, misconception debrief, worked
    examples, small-group work, synthesis
```

The **Guiding Question** is the atomic unit of the whole system. Assessment items, in-class
activities, and the class Gem all reference question IDs. That is what lets the tooling
check the design rather than merely store it.

## What the tooling actually enforces

A flipped course fails in two predictable ways. Both are caught mechanically:

- **The class hour quietly becomes a lecture again.** Every in-class Activity must reference
  at least one Guiding Question from that unit's home study. An activity with nothing to
  reference does not belong in the hour.
- **"Two hours at home" turns out to be fiction.** Every Study Session must have at least one
  *complete* Study Path — one route through all its questions — that fits inside the session's
  time budget.

Alongside those: objective coverage, dangling references, ID consistency, activity durations
summing to the hour, assessment items that test something nobody was asked to learn.

## Status

**Phase 0.** Schemas, templates, scaffolding, and the validator are working and tested.
The agent layer is Phase 1 and not built yet. Nothing here is stable.

## Starting a course

A course lives in **its own repo**, created by cloning this one and repointing `origin`.
Keeping this repo as a second remote is what lets you pull framework improvements later
without re-applying them by hand.

```bash
git clone https://github.com/chenavin/class-framework.git my-course
cd my-course
git remote rename origin framework
git remote add origin https://github.com/chenavin/my-course.git   # create it first, PRIVATE
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

## Commands

| Command | What it does |
|---|---|
| `classkit scaffold course` | Create the course tree |
| `classkit scaffold unit N` | Create a unit with its study sessions and lesson plan |
| `classkit scaffold session U05 5` | Add one more study session to a unit |
| `classkit scaffold item U05` | Add an assessment item |
| `classkit validate` | Check the course against its methodology and schemas |

Scaffolding **never overwrites**. Re-run it any time — you get whatever is missing and keep
everything you wrote. Skipped files are reported.

## Layout

```
schemas/          JSON Schema for every content type — the contract
methodologies/    pluggable study-session designs; question-driven-25 is the default
defaults/         time constants used to estimate how long a study path takes
templates/        what scaffold copies into a course repo
src/classkit/     the tooling
tests/            scaffold → validate round-trip
_devlog/          temporary build log; deleted before release
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
