# Roadmap

Ordered by risk, not by appeal: each phase exists to find out whether the phase before it was
built on a wrong assumption. Open questions referenced as `Q-nnn` and decisions as `D-nnn` live in
`_devlog/`.

Status: ✅ done · 🔨 in progress · ⬜ not started

---

## ✅ Phase 0 — Content model and tooling

*Commit `d1decee`.*

The contract everything else writes into: JSON Schemas for course, unit, study session, in-class
session, assessment item and methodology; `question-driven-25` as data rather than code; the
create-only scaffold; the validator with its semantic rules; 14 tests.

Built first because agents need a target format. An agent asked to "design a study session" with
nothing to write into produces prose nobody can check, and you cannot tell a good unit from a
plausible-sounding one.

## ✅ Phase 1 — The agent layer

*Commit `cfde55f`.*

Seven agents, two skills, six teacher-facing commands, and `GETTING-STARTED.md`. The design work
runs in the teacher's own Claude Code, inside their course repo.

**Written but unexercised.** No real course has been built with it.

## 🔨 Design-draft pass (precedes the classroom)

A deliberate pass to finish a full *draft* of the design before classroom testing, so the testing
pushes against a stable target (Session 10). Scope: complete the content model, then agent coverage,
metrics, and the course lifecycle. Runs on the design doc and `_devlog/`, not on real course content.

- **Content model** — reviewing the flipped-class part for gaps. Decided: guiding questions gain an
  `answer` field (**D-019**) — *design only, not yet in the schema/validator/templates/agents.* Open:
  Q-023 (path vs. route), Q-024 (time-budget inputs), Q-025 (course-level outcomes), Q-026 (homework
  / programming assignments — a separate section).
- Then: agent coverage, metrics, course lifecycle. See the agenda in `_devlog/03-open-questions.md`.

Implementing what this pass decides ("fill the framework gaps") is a separate step, and precedes
Phase 2's real-course work.

---

# Implementation ledger

**The design draft is finished first; this ledger is worked through afterwards.** Nothing here is
built yet, and nothing here should be built while the draft is still moving — a decision may still
change. The ledger exists so that when implementation starts, no consequence has been forgotten.

`DESIGN.md` describes the **target** design and reads as if it exists. **This ledger is authoritative
for what actually exists.** Anything listed below is designed, not built.

**Rule:** a decision marked `locked (design)` in `_devlog/01-decisions.md` must have a row here in
the same commit. Add rows as the draft continues; tick them as implementation lands.

Status: ⬜ not built · 🔨 in progress · ✅ done

## D-019 — `answer` field on every Guiding Question

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/study-session.schema.json` | `answer` on each goal: required, `minItems: 1`, items `{kind, ref, note?}`, `kind ∈ textbook \| slide \| video \| article \| web \| other` |
| ⬜ | `src/classkit/validate.py` | new rule `answer_reference_present`, severity `error` |
| ⬜ | `methodologies/question-driven-25.yaml` | list the new rule in `rules:` so other methodologies can re-tune its severity |
| ⬜ | `templates/unit/session.md` | an `answer:` block per goal, with a locator example rather than `TODO` |
| ⬜ | `.claude/agents/study-session-designer.md` | write answer locators; invariant 7 applies — no invented section or slide numbers |
| ⬜ | `.claude/agents/gem-builder.md` | tutor *toward* the answer refs; they are the Gem's ground truth |
| ⬜ | `.claude/agents/assessment-writer.md` | answer refs are the correct-answer / rubric basis |
| ⬜ | `.claude/agents/course-critic.md` | judge whether locators are precise and reachable — free text, so not code-checkable |
| ⬜ | `.claude/skills/writing-guiding-questions/SKILL.md` | the craft of a good locator; and the escape case (see open item below) |
| ⬜ | `CLAUDE.md` | glossary: a Guiding Question now carries prompt + est_minutes + answer |
| ⬜ | `tests/test_course_lifecycle.py` | removing `answer` from a scaffolded goal fires the rule |

**Open before implementing:** a required field at error severity has no honest filler. A judgment
question — *"how would you choose between a heap and a sorted array here?"* — may have no single
locator, and the pressure to fill the field is exactly what produces the fabricated reference
invariant 7 forbids. Decide: a documented escape (`kind: other` plus a note saying why), or rule that
such questions belong in the in-class hour rather than home study. Either is defensible; discovering
it when the validator won't go green is not.

## D-020 — Study Paths move to the session; `est_minutes` moves to the question

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/study-session.schema.json` | remove `paths` from goal; add optional session-level `paths`; add required `est_minutes` to each goal |
| ⬜ | `src/classkit/validate.py` | rewrite the budget rule: `sum(goal.est_minutes) + overhead ≤ session_minutes`, **with tolerance** (D-020 calls the estimate approximate, so a hard cliff misreads it) |
| ⬜ | `src/classkit/validate.py` | **rename `session_path_feasibility`** — paths no longer enter the sum, so the name now misdescribes the rule |
| ⬜ | `src/classkit/validate.py` | retire `_estimate_path` and `path_estimate_missing`; both exist only to derive per-path times |
| ⬜ | `src/classkit/validate.py` | `min_paths_per_goal` → a soft per-session minimum |
| ⬜ | `methodologies/question-driven-25.yaml` | `study_paths.min_paths_per_goal` → per-session; add the budget tolerance |
| ⬜ | `defaults/time-constants.yaml` | no longer load-bearing for the guarantee — annotate as advisory, or delete if nothing proposes estimates from it (ties to Q-024) |
| ⬜ | `templates/unit/session.md` | goals gain `est_minutes`; session gains a `paths:` pool |
| ⬜ | `.claude/agents/study-session-designer.md` | rewrite path/time guidance: estimate per question, propose paths per session |
| ⬜ | `.claude/agents/course-critic.md` | **new responsibility — see below** |
| ⬜ | `.claude/skills/estimating-study-time/SKILL.md` | substantial rewrite: it is built entirely around per-path derivation, which no longer exists |
| ⬜ | `.claude/agents/topic-researcher.md` | its durations now feed an untimed pool; revisit why it loads the estimating skill |
| ⬜ | `CLAUDE.md` | glossary — "Study Path: a candidate route… typed and time-estimated" is now wrong on both counts |
| ⬜ | `GETTING-STARTED.md` | `time_constants` is described as load-bearing for the 25-minute check; it no longer is |
| ⬜ | `tests/test_course_lifecycle.py` | feasibility tests are written against per-path times |

**The responsibility shift this creates.** The budget is now one teacher-typed number per question.
Code can check that the arithmetic adds up; it cannot check that the numbers are honest. That makes
`course-critic` the **only** check on whether an `est_minutes` is real — and its prompt does not
currently say so. This must be written into the critic explicitly, and stated in `DESIGN.md §10`,
or the guarantee silently weakens with nobody owning it.

## D-021 — Syllabus as the top layer; Course Outcomes close the coverage chain

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/syllabus.schema.json` | **new** — `goal`, `outcomes[]` (`CO1…`, statement, optional bloom), `workload` (credits, credit_system, total_hours), `prerequisites`, reserved `assessment` block |
| ⬜ | `schemas/unit.schema.json` | `outcomes: [CO1…]` on each Unit Objective |
| ⬜ | `src/classkit/model.py` | load `syllabus/syllabus.md` into the course model |
| ⬜ | `src/classkit/validate.py` | `SCHEMA_FOR` entry so the syllabus is schema-checked |
| ⬜ | `src/classkit/validate.py` | two rules: `outcome_coverage` (no orphan Course Outcome) and `objective_maps_to_outcome` (no orphan objective) |
| ⬜ | `templates/course/syllabus.md` | **new** — Bologna-style default, generic (ECTS is one instantiation, not hardcoded — invariant 2) |
| ⬜ | `src/classkit/scaffold.py` | write the syllabus into the reserved `syllabus/` slot, create-only |
| ⬜ | `CLAUDE.md` | `CO1` ID convention; glossary entries for Syllabus and Course Outcome |
| ⬜ | `.claude/agents/curriculum-architect.md` | authors the syllabus; sets `outcomes` on the objectives it writes |
| ⬜ | `.claude/commands/plan-units.md` | the syllabus is part of planning the semester |
| ⬜ | `GETTING-STARTED.md` | the syllabus is a thing teachers edit; the settings section names only `course.yaml` |
| ⬜ | `tests/test_course_lifecycle.py` | scaffold produces a valid syllabus; both coverage rules fire when broken |

**Later, not now:** `workload.total_hours` enables a course-scope workload check — all home-study
`est_minutes` + in-class + homework against the declared workload. It needs homework (Q-026) first.

## Cross-cutting

| | Artifact | Change |
|---|---|---|
| ⬜ | `DESIGN.md §10` | add: parts of this document are designed and not built; the critic now owns estimate honesty |
| ⬜ | `tests/` | the scaffold→validate round-trip must stay green at every step — invariant 6 means templates and schemas move together |

**Count as of 2026-08-28:** 3 decisions, 40 artifact changes, 0 built.

## 🔨 Phase 2 — First real course

**The phase that will teach us the most, and the one most likely to invalidate earlier work.**

- Run `/ingest` and `/design-unit 1` against the real *Introduction to Data Structures and
  Algorithms* materials. **Blocked on Q-004** — where those materials are and in what format.
- Replace the placeholder numbers in `defaults/time-constants.yaml` with defensible ones
  (**Q-005**). Until then the feasibility check is arithmetic over a guess, which is worse than no
  check because it looks like verification.
- Revise agent prompts against what unit 1 actually exposes. Expect this to be substantial.
- Add validator rules for whatever goes wrong that nothing currently catches.

Exit criterion: one unit good enough to teach, not one unit that validates.

## ⬜ Phase 3 — Prove the methodology is really pluggable

D-011 claims any teacher can supply a different study-session design and the rest keeps working.
**That claim is currently untested**, and it is load-bearing for the whole multi-teacher premise.

Write a genuinely different second methodology — problem-set-first, or case-study, with different
session counts and a non-`question` goal type — and find out what breaks. Anything that has to
change in `src/` to accommodate it is a bug against invariant 3.

Cheapest possible way to discover the contract is wrong. Worth doing before more teachers commit
to it.

## ⬜ Phase 4 — Exports

- **PPTX** (D-006), via `python-pptx`. Deliberately minimal: the 50-minute hour should not be
  slide-driven, so the generator should make few slides the easy path and many slides awkward.
- **Gem bundles** — `gem-builder` drafts them today; this hardens the format and the exclusion
  rules once a real one has been used by real students.

## ⬜ Phase 5 — Moodle

Deferred at D-004. Quiz and item export first (the item schema is already atomic and tagged for
it); full sync only if it proves worth the maintenance.

## ⬜ Phase 6 — Multi-teacher hardening

The questions deliberately left open until someone actually hits them:

- **Q-007** — how framework updates should work once a teacher has edited or added things. The
  interim rule ("want updates? don't edit framework files") is a placeholder, not an answer.
- **Q-020** — move to a GitHub Organization. A personal repo has one permission level, so read-only
  access for teachers who merely clone is impossible, and D-014 cannot be implemented as written.
- **Q-002** — exam confidentiality. Decide before real exam content is committed anywhere; git
  history is permanent.
- Delete `_devlog/`, then make the repo public (**Q-016**).

---

## Not planned

Student-facing anything — submissions, grades, LMS replacement. The framework designs a course; it
does not run one.
