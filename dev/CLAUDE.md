# Developing the framework

**You are in FRAMEWORK-DEVELOPER mode.** This file is about changing the framework itself —
schemas, tooling, templates, agents — without breaking its invariants. If you are helping a teacher
build a *course*, stop: that is the root `CLAUDE.md`.

## Setting up a developer checkout

```bash
pip install -e ".[dev]"
classkit mode developer     # step 1 — creates the gitignored dev/.developer marker
```

`classkit mode` shows the current hat; `classkit mode teacher` switches back. The marker is
**gitignored on purpose** — it must never reach a teacher's clone, which is exactly what makes its
presence a reliable signal. `classkit mode developer` **verifies that ignore rule before creating
the file** and refuses if it is missing, because a committed marker would put every teacher's clone
into framework-developer mode. A running Claude Code session reads the marker once at startup, so
restart it after switching.

Forgetting this step lands you in teacher mode — harmless, and obvious from the session's opening
line.

## Where to start reading

Start at `VISION.md` (why the project exists) and `FRAMEWORK-SPEC.md` (what the framework must
contain). `ROADMAP.md` carries the implementation plan and the ledger — **the ledger is authoritative
for what actually exists**, because the spec deliberately runs ahead of the code.

Three things live in the root `CLAUDE.md` and apply here fully: **how to work** (honest, rigorous,
unbiased — no reflexive agreement), **the vocabulary**, and **the ID conventions**. Both hats share
them, so they are deliberately not duplicated here — two copies would drift.

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
   exam logistics, a current-events hook — but an hour made of them is a lecture. An agent never raises the cap, or accepts an
   exception, on its own; the teacher may (D-028, D-037).
5. **Nothing overwrites a teacher's work without permission — enforced in code, not by prompt.**
   Scaffolding is create-only (`write_new()` is the only way scaffold touches disk), and **every
   agent and command writes through `classkit.write.write()` / `classkit write`, which structurally
   refuses to overwrite existing content** without explicit confirmation (`--overwrite`) — see
   `FRAMEWORK-SPEC.md` §8.6 (D-030, D-031b). Silent loss of a teacher's authored work is
   unrecoverable — this is the one place the framework does not trust a prompt.
6. **Templates must validate.** A fresh scaffold has to produce a course with zero errors,
   or `tests/test_course_lifecycle.py` fails. Change a schema → change the template.

## Where things live

```
schemas/*.schema.json     the content contract (JSON Schema draft 2020-12)
methodologies/*.yaml      pluggable study-session designs
defaults/time-constants.yaml   how long a study path is assumed to take
templates/                what scaffold copies into a course repo
.claude/                  agents, skills, commands — TEACHER-facing, shipped to every course
  hooks/report-mode.sh    the SessionStart hook that announces which hat a session wears
src/classkit/
  frontmatter.py          Markdown + YAML front-matter parsing
  model.py                locating and loading a course tree
  scaffold.py             create-only content generation
  write.py                the overwrite-safe write path — every agent and command writes here
  log.py                  the course log, LOG.md — `classkit log`, append-only through write.append (D-036, D-038)
  ingest/                 materials (D-035, spec §8.7): `classkit ingest`, `add-url`, `material`
    extract.py              extractors registered by extension; anchors
    links.py                links.md — parse, `add-url`, best-effort metadata
    manifest.py             materials/manifest.yaml — load, save, ids
    core.py                 scan → reconcile (shared with the validator) → convert
  mode.py                 teacher / framework-developer hat: `classkit mode` (D-034)
  validate.py             schema layer + semantic rules
  cli.py                  argparse entry point
tests/                    scaffold → validate round-trip; ingest (fixtures generated in tmp_path)
dev/                      you are here — not part of a teacher's course
  VISION.md                 why the project exists, what it produces, how it is developed
  FRAMEWORK-SPEC.md         the spec — what the framework must contain
  ROADMAP.md                phases + the implementation ledger (authoritative for what is built)
  MANUAL-TESTING.md         how to hand-test the framework as a teacher, in a clean clone
  CLAUDE.md                 this file
  _devlog/                  build log — decisions, progress, open questions (deleted before release)
```

## Before changing anything structural

Read `FRAMEWORK-SPEC.md` first — it explains the layering, the contracts between layers, and which
constraints are load-bearing. **If your change alters structure or flow, update `FRAMEWORK-SPEC.md`
in the same commit**; it is the document that survives `_devlog/` being deleted.

Then read `_devlog/01-decisions.md`. Locked decisions are not to be relitigated; several constraints
that look arbitrary have a recorded reason. `_devlog/03-open-questions.md` lists what is genuinely
undecided.

A decision marked `locked (design)` must get a row in `ROADMAP.md`'s ledger in the same commit.

## Adding a validation rule

Add the check to `Validator`, give it a code, and register its default severity in
`DEFAULT_SEVERITY` — every rule, errors included (the table is complete; an unregistered code
raises). Methodologies override severities in their `rules:` block, and a course overrides the
methodology in `course.yaml` `rules:`. Every rule needs a test in `tests/test_course_lifecycle.py`
that breaks a scaffolded course and asserts the code fires **at its severity** — a rule that never
fires is worse than no rule.

**Say which kind it is** (D-037). *Integrity* — it names something that does not exist, or a file
cannot be read — defaults to `error`. *Advisory* — something is missing or departs from the
methodology — defaults to `warn` (`alert` if it matters most). **The teacher is the authority:** do
not make a pedagogical check an error, and do not put pedagogical presence into a schema's
`required`, which would turn advice back into an error by the back door.

**Say which course state the rule judges** (D-033). A course is half-built for almost all of its
life, and invariant 6 requires a fresh scaffold to validate clean. A **consistency** rule (does
what is present hold together?) is always active. A **completeness** rule (was everything promised
delivered?) runs only once the course is complete — units on disk == `course.yaml` `units` — and is
reported as *skipped* until then. Getting this wrong produces a rule that fails every scaffolded
course and that teachers switch off.

## Running things

```bash
pip install -e ".[dev]"
pytest
```

`classkit validate` needs a course, so it does nothing useful in this repo. Test against a
throwaway scaffold in a temp directory. For **hand-testing as a teacher would** — a clean clone,
the real commands, expected output and expected noise — follow `MANUAL-TESTING.md`.

## The agent layer

The agents in `.claude/` are **teacher-facing**: they run in the *teacher's* Claude Code inside their
course repo. They ship to course repos through the clone (D-009), so an agent improvement made here
reaches every course on the next `git merge framework/main`.

```
.claude/agents/     curriculum-architect, study-session-designer, lesson-planner,
                    assessment-writer, topic-researcher, gem-builder, course-critic,
                    material-classifier
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
- **Agents write through `classkit write`**, never a raw file write (invariant 5).
- **Agents finish by running `classkit validate`** and fixing what it reports.

## Not built yet

PPTX export (D-006) and Moodle sync (D-004). Do not assume either exists.

`ROADMAP.md` has the phases: what is done, what is next, and why each remaining phase exists.
Phase 2 (first real course) is the one that will invalidate assumptions — the agent layer has
never been run against real materials.
