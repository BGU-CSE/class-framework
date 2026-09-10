# Working in this repo

Agent-facing context. Read `README.md` for what the project is; this file is about how to
work on it without breaking its invariants.

## Vocabulary — use these words, no synonyms

Two words are **banned** because each used to mean two things: **"topic"**, and bare
**"question"** (say *Guiding Question* or *Assessment Item*).

| Term | Meaning |
|---|---|
| **Unit** | One week's subject. 12–13 per semester. |
| **Unit Objective** | Abstract, teacher-facing goal. 2–4 per unit. Not the working layer. |
| **Study Session** | The ~25-min at-home unit. 4 per Unit. |
| **Guiding Question** | A session goal phrased as a question the student should be able to answer. 3–5 per session. **The atomic addressable unit.** |
| **Study Path** | A candidate route to answering a Guiding Question (gem / video / textbook / article / exercise), typed and time-estimated. |
| **In-Class Session** | The weekly 50-min meeting. Synonym: **Lesson Plan**. One per Unit. |
| **Activity** | A component of an In-Class Session. Has a duration; references ≥1 Guiding Question. |
| **Assessment Item** | A single quiz/homework/exam question. |

## ID conventions

Mechanically checked by the schemas and the validator.

```
U01              Unit
U01-O1           Unit Objective
U01-S02          Study Session
U01-S02-G1       Guiding Question   ← referenced by everything else
U01-IC           In-Class Session
U01-A1           Activity
U01-I01          Assessment Item
```

## Invariants — do not break these

1. **No course content in this repo.** No `course/` directory, no real units, no example
   course. Course content lives only in course repos, created by `classkit scaffold`. Tests
   build a throwaway course in `tmp_path` instead.
2. **Nothing hardcodes methodology numbers.** "4 sessions", "25 minutes", "3–5 questions",
   "50 minutes" are read from `methodologies/*.yaml`. A second methodology with different
   numbers must work without code changes.
3. **Downstream consumes `goals[]`, never the methodology.** The study-session schema is the
   contract between a methodology and everything else. Code that branches on
   `methodology.id == "question-driven-25"` is a bug.
4. **The class hour is built on the home study.** Activities reference that unit's Guiding
   Questions. An activity referencing none is permitted but flagged, and the **total unmapped
   time in an hour is capped** (`in_class.max_unmapped_minutes`). Legitimate exceptions exist —
   exam logistics, a current-events hook — but an hour made of them is a lecture. Never raise the
   cap to make a validation pass (D-028).
5. **Nothing overwrites a teacher's work without permission — enforced in code, not by prompt.**
   Scaffolding is create-only (`write_new()` is the only way scaffold touches disk), and **every
   agent and command writes through `classkit.write.write()` / `classkit write`, which structurally
   refuses to overwrite existing content** without explicit confirmation (`--overwrite`) — see
   `dev/FRAMEWORK-SPEC.md` §8.6 (D-030, D-031b). Silent loss of a teacher's
   authored work is unrecoverable — this is the one place the framework does not trust a prompt.
6. **Templates must validate.** A fresh scaffold has to produce a course with zero errors,
   or `tests/test_course_lifecycle.py` fails. Change a schema → change the template.

## Where things live

```
schemas/*.schema.json     the content contract (JSON Schema draft 2020-12)
methodologies/*.yaml      pluggable study-session designs
defaults/time-constants.yaml   how long a study path is assumed to take
templates/                what scaffold copies into a course repo
.claude/                  agents, skills, teacher-facing commands
GETTING-STARTED.md        the teacher's entry point — materials, settings, workflow
src/classkit/
  frontmatter.py          Markdown + YAML front-matter parsing
  model.py                locating and loading a course tree
  scaffold.py             create-only content generation
  write.py                the overwrite-safe write path — every agent and command writes here
  validate.py             schema layer + semantic rules
  cli.py                  argparse entry point
tests/                    scaffold → validate round-trip
dev/                      framework-development docs — NOT part of a teacher's course:
  VISION.md                 why the project exists, what it produces, how it is developed
  FRAMEWORK-SPEC.md         the spec — what the framework must contain; read before structural changes
  ROADMAP.md                phases + the implementation ledger (authoritative for what is built)
  _devlog/                  build log — decisions, progress, open questions (deleted before release)
```

## Before changing anything structural

Read `dev/FRAMEWORK-SPEC.md` first — it explains the layering, the contracts between layers, and
which constraints are load-bearing. **If your change alters structure or flow, update
`dev/FRAMEWORK-SPEC.md` in the same commit**; it is the document that survives `dev/_devlog/` being
deleted.

Then read `dev/_devlog/01-decisions.md`. Locked decisions are not to be relitigated; several
constraints that look arbitrary have a recorded reason. `dev/_devlog/03-open-questions.md`
lists what is genuinely undecided.

## Adding a validation rule

Add the check to `Validator`, give it a code, and put its default severity in
`DEFAULT_SEVERITY` if it is not an error. Methodologies override severities in their
`rules:` block. Every rule needs a test in `tests/test_course_lifecycle.py` that breaks a
scaffolded course and asserts the code fires — a rule that never fires is worse than no rule.

## Running things

```bash
pip install -e ".[dev]"
pytest
```

`classkit validate` needs a course, so it does nothing useful in this repo. Test against a
throwaway scaffold in a temp directory.

## The agent layer

The design work is done by agents in `.claude/`, running in the *teacher's* Claude Code inside
their course repo. They ship to course repos through the clone (D-009), so an agent improvement
made here reaches every course on the next `git merge framework/main`.

```
.claude/agents/     curriculum-architect, study-session-designer, lesson-planner,
                    assessment-writer, topic-researcher, gem-builder, course-critic
.claude/skills/     writing-guiding-questions, estimating-study-time
.claude/commands/   /ingest /plan-units /design-unit /write-items /review-unit /build-gem
```

When editing agents:

- **Read the methodology, never hardcode it.** An agent that assumes 4 sessions of 25 minutes
  breaks every other teacher's course (D-011, invariant 2).
- **Craft shared by more than one agent belongs in a skill**, so the designer and the critic judge
  by the same standard rather than drifting apart.
- **Agents must not fabricate resources.** No invented URLs, page numbers, or video titles. A
  fabricated study path validates cleanly and fails a student mid-session.
- **Agents finish by running `classkit validate`** and fixing what it reports.

## Not built yet

PPTX export (D-006) and Moodle sync (D-004). Do not assume either exists.

`dev/ROADMAP.md` has the phases: what is done, what is next, and why each remaining phase exists.
Phase 2 (first real course) is the one that will invalidate assumptions — the agent layer has
never been run against real materials.
