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

## 🔨 Build plan — vertical slices, Core first (D-022)

We design → implement → test → update **one coherent slice at a time**, rather than designing the
whole framework before building any of it. Each slice is finished end to end before the next is
designed, so we reach the implement-and-test loop — where the real risk lives — sooner, and each
later slice is designed against a Core that has actually been exercised rather than against
assumptions.

1. **Core** — *design nearly complete.* Course initiation, syllabus, Course Outcomes, units, and the
   whole learning part: study sessions (guiding questions, `answer`, `est_minutes`, the study-path
   pool) and the in-class hour, **including the entry quiz end to end** — generating its questions
   and producing gradeable quizzes. The bar: Core delivers everything needed to *generate and run*
   the learning phase. Content-model decisions locked as **D-019, D-020, D-021** (see the ledger).
   Remaining design: the two open items beside D-019/D-020, and the minors in Q-027.
2. **Assessment** — homework, programming assignments, exams (**Q-026**); fills the syllabus's
   reserved grading block. Depends on Core's guiding questions. (Entry-quiz items are Core; homework
   and exam items are here.)
3. **Exports** — the Gem *builder* and PPTX. "Generate an artifact from the designed course."
   (Gem-as-a-study-path is Core; only the builder defers.)
4. **Metrics** — *later.* Measures to improve a course or its activities, once Core has been built
   and taught enough to know which signals matter.
5. **Lifecycle** — *much later,* after the course has been taught at least once: the semester arc,
   revision, re-offering.

**How this maps to the risk-ordered phases below:** Core's implement-and-test step *is* "Phase 2 —
First real course"; the **Exports** slice is "Phase 4". Pluggability (Phase 3), Moodle (Phase 5) and
multi-teacher hardening (Phase 6) stay as independent later concerns, unchanged.

---

# Implementation plan — the order to work the ledger

The ledger below is grouped **by decision**, which is right for traceability and wrong as a work
plan. This is the order to actually build it.

**Principle: workflow order outside, layer order inside.** Steps follow the teacher's workflow
(`VISION.md` §5); within a step, work layer by layer — schema → template → validator rule → agent /
command → test — and leave the suite green (invariant 6: a fresh scaffold must validate).

*Why not build layer-by-layer across the whole framework?* Because that defers every agent to the
end, and **the agent layer is the riskiest part** — no prompt in `.claude/` has ever run against real
materials (§9). Layer-first would finish the parts we are most confident about and only then expose
the uncertain one. This is the same vertical-slice reasoning as D-022, one level down.

Each step should end in something runnable and inspectable, not just green tests.

| Step | Delivers | Ledger rows drawn from |
|---|---|---|
| **0. Foundation** | The overwrite-safe write path. Nothing else — this is deliberately thin. | D-031b |
| **1. Initialize** | `classkit scaffold course` produces a complete, valid course skeleton *including* `syllabus/syllabus.md`. The teacher's first contact with the framework. | D-021 (template + scaffold rows) |
| **2. Ingest** ⚠️ | Reading the teacher's real materials. **Design not settled — see Q-028.** Cannot start until it is. | *(none yet — the spec does not specify ingest)* |
| **3. Syllabus and units** | `/plan-units` end to end: syllabus schema and rules, `outcomes` on objectives, `syllabus-designer` + `curriculum-architect`, the file-based handoff. | D-021, D-029, D-031d, D-031i |
| **4. Study sessions** | `answer`, `est_minutes`, `defer_to_class`, session-level `paths`, the budget rule, `study-session-designer`, the rewritten `estimating-study-time` skill. | D-019, D-020, D-023, D-025 |
| **5. Entry quiz** | `model_answer` rename, `usage` scoping, `unit_has_entry_quiz_items`, `assessment-writer` scoped to the entry quiz. | D-031c, D-031g |
| **6. In-class hour** | Optional `guiding_questions` + `reason`, the unmapped-time cap and its course override, `activity_item_reference`, `lesson-planner`. | D-028, D-031a, D-031e |
| **7. Review and gates** | `course-critic` updates (estimate honesty, deferral abuse, syllabus judgment), approval gates in every command. | D-025, D-029, D-030, D-031h |
| **8. Docs** | Re-derive `README.md` and `GETTING-STARTED.md` **from the spec** — they currently contradict D-028 and D-030. | D-028, D-030 rows |

**Step 5 must precede step 6** — that is D-031a: the entry-quiz items have to exist before the lesson
plan can reference their ids.

**A real course can be attempted after step 4** (or step 6 for a full unit). That is the first
opportunity to test against real material, which is where the useful information is.

---

# Implementation ledger

**The design draft is finished first; this ledger is worked through afterwards.** Nothing here is
built yet, and nothing here should be built while the draft is still moving — a decision may still
change. The ledger exists so that when implementation starts, no consequence has been forgotten.

`FRAMEWORK-SPEC.md` describes the **target** design and reads as if it exists. **This ledger is authoritative
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

**Open item — RESOLVED → D-023.** A required field had no honest filler for a judgment question with
no single locator. Resolution: the escape is `defer_to_class: true` (a pre-class thinking prompt whose
answer is deferred to, and resolved in, the meeting), not a fabricated reference. See the D-023 rows
below.

## D-020 — Study Paths move to the session; `est_minutes` moves to the question

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/study-session.schema.json` | remove `paths` from goal; add optional session-level `paths`; add required `est_minutes` to each goal |
| ⬜ | `src/classkit/validate.py` | rewrite the budget rule: `sum(goal.est_minutes) + overhead ≤ session_minutes`, **with tolerance** (D-020 calls the estimate approximate, so a hard cliff misreads it) |
| ⬜ | `src/classkit/validate.py` | **rename `session_path_feasibility`** — paths no longer enter the sum, so the name now misdescribes the rule |
| ⬜ | `src/classkit/validate.py` | retire `_estimate_path` and `path_estimate_missing`; both exist only to derive per-path times |
| ⬜ | `src/classkit/validate.py` | `min_paths_per_goal` → a soft per-session minimum |
| ⬜ | `methodologies/question-driven-25.yaml` | `study_paths.min_paths_per_goal` → per-session; add the budget tolerance |
| ⬜ | `defaults/time-constants.yaml` | keep as an **advisory yardstick**, not a validator input: the designer proposes `est_minutes` from it, the critic sanity-checks against it. Annotate as advisory. (D-025, resolves Q-024) |
| ⬜ | `templates/unit/session.md` | goals gain `est_minutes`; session gains a `paths:` pool |
| ⬜ | `.claude/agents/study-session-designer.md` | rewrite path/time guidance: estimate `est_minutes` per question, *proposing* it from the advisory constants; propose paths per session (D-020/D-025) |
| ⬜ | `.claude/agents/course-critic.md` | **new responsibility:** judge each `est_minutes` for plausibility against the material, using the constants as a yardstick (D-020 open item, resolved by D-025) |
| ⬜ | `.claude/skills/estimating-study-time/SKILL.md` | substantial rewrite: drop per-path derivation; describe estimating per question and using the constants as an advisory yardstick — the shared standard for both the designer and the critic (D-025) |
| ⬜ | `.claude/agents/topic-researcher.md` | its durations now feed an untimed pool; revisit why it loads the estimating skill |
| ⬜ | `CLAUDE.md` | glossary — "Study Path: a candidate route… typed and time-estimated" is now wrong on both counts |
| ⬜ | `GETTING-STARTED.md` | `time_constants` is described as load-bearing for the 25-minute check; it no longer is |
| ⬜ | `tests/test_course_lifecycle.py` | feasibility tests are written against per-path times |

**The responsibility shift this creates.** The budget is now one teacher-typed number per question.
Code can check that the arithmetic adds up; it cannot check that the numbers are honest. That makes
`course-critic` the **only** check on whether an `est_minutes` is real — and its prompt does not
currently say so. This must be written into the critic explicitly, and stated in `FRAMEWORK-SPEC.md §10`,
or the guarantee silently weakens with nobody owning it. **Resolved by D-025:** the check stays human
judgment, but the critic (and the designer) get the time-constants as an *advisory yardstick*, so it
is calibrated rather than pure vibes.

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

## D-023 — A question has a recorded answer, or is explicitly deferred to the in-class meeting

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/study-session.schema.json` | `defer_to_class: boolean` (default false) on each goal; `answer` required *unless* `defer_to_class` is true |
| ⬜ | `src/classkit/validate.py` | `answer_reference_present` fires only when `defer_to_class` is not set |
| ⬜ | `src/classkit/validate.py` | new rule `deferred_question_resolved_in_class` — a deferred goal must be referenced by ≥1 in-class activity, so deferring costs contact time |
| ⬜ | `methodologies/question-driven-25.yaml` | severities for both; optional cap on deferred goals per session |
| ⬜ | `templates/unit/session.md` | one goal shown with `defer_to_class: true` and no `answer`, picked up by an in-class activity |
| ⬜ | `.claude/agents/study-session-designer.md` | default to answerable questions; use `defer_to_class` sparingly, as a pre-class thinking prompt |
| ⬜ | `.claude/agents/lesson-planner.md` | every deferred question must be resolved by an activity |
| ⬜ | `.claude/agents/course-critic.md` | judge deferrals are genuine thinking prompts, not answer-dodges, and not overused |
| ⬜ | `.claude/skills/writing-guiding-questions/SKILL.md` | refine "the question that needs the class hour" — allowed only if deferred *and* resolved in class |
| ⬜ | `CLAUDE.md` | glossary: a Guiding Question has an `answer` **or** `defer_to_class: true` |
| ⬜ | `tests/test_course_lifecycle.py` | a goal with neither fires `answer_reference_present`; a deferred goal not referenced in-class fires the new rule |

## D-028 — Activity/guiding-question link relaxed; unmapped in-class time capped

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/in-class-session.schema.json` | `guiding_questions` no longer required on an activity; add optional `reason` string |
| ⬜ | `src/classkit/validate.py` | `activity_references_guiding_question` → **warn** when empty; still **error** when a referenced id is not of this unit |
| ⬜ | `src/classkit/validate.py` | new rule `in_class_unmapped_time_cap` (error): Σ duration of activities with no guiding question ≤ `in_class.max_unmapped_minutes` |
| ⬜ | `methodologies/question-driven-25.yaml` | add `in_class.max_unmapped_minutes: 15`; severities for both rules |
| ⬜ | `.claude/agents/lesson-planner.md` | most activities build on guiding questions; unmapped ones need a `reason` and cost against the cap |
| ⬜ | `.claude/agents/course-critic.md` | judge whether an unmapped activity's `reason` is legitimate, and whether the hour leans on the cap |
| ⬜ | `CLAUDE.md` | invariant 4 reworded ✅ (done in the same commit as the spec) |
| ⬜ | `README.md` | "every in-class Activity must reference at least one Guiding Question" is now wrong |
| ⬜ | `tests/test_course_lifecycle.py` | an unmapped activity warns; exceeding the cap errors; a foreign-unit reference still errors |

## D-029 — `syllabus-designer` agent

| | Artifact | Change |
|---|---|---|
| ⬜ | `.claude/agents/syllabus-designer.md` | **new** — owns `syllabus/syllabus.md`: goal, Course Outcomes, workload, prerequisites |
| ⬜ | `.claude/commands/plan-units.md` | run syllabus-designer and curriculum-architect as **one flow** sharing the outcome list |
| ⬜ | `.claude/agents/curriculum-architect.md` | scope narrowed to the unit map and unit objectives; consumes the outcome list |
| ⬜ | `.claude/agents/course-critic.md` | syllabus judgment: outcomes that are real outcomes not topic labels, a meaningful goal, plausible workload |

## D-030 — Command interaction protocol

| | Artifact | Change |
|---|---|---|
| ⬜ | `.claude/commands/*.md` (all) | stepwise execution with an approval gate per step; announce → produce → show → wait |
| ⬜ | `.claude/agents/*.md` (all writers) | before writing, detect existing content and ask; never silently overwrite |
| ⬜ | `.claude/agents/*.md` (all writers) | revision mode: when output exists, update in place and report the diff; regeneration is explicit |
| ⬜ | `CLAUDE.md` | invariant 5 reworded ✅ (done in the same commit as the spec) |
| ⬜ | `GETTING-STARTED.md` | describe the stepwise/approval workflow a teacher should expect |
| ⬜ | `src/classkit/` | a write path that detects existing content, so the check is not prompt-only. **Upgraded from "consider" to required by D-031b — see its rows below.** |

## D-031 — Core spec review findings

Source: `_devlog/../reviews/core-spec-review-01.md`. Some rows amend rows above; implement together.

| | Artifact | Change |
|---|---|---|
| ⬜ | `.claude/commands/design-unit.md` | **(a)** swap the order: assessment-writer (entry quiz) runs *before* lesson-planner |
| ⬜ | `.claude/agents/lesson-planner.md` | **(a)** read the existing entry-quiz items; put their real ids in the quiz activity's `items`; never invent an id |
| ⬜ | `src/classkit/validate.py` | **(a)** new rule `activity_item_reference` (error): every id in `activity.items` resolves to an existing item of that unit |
| ⬜ | `src/classkit/` (new) | **(b)** a write path that structurally refuses to overwrite existing content without explicit confirmation — generalizes `write_new()` beyond scaffold. **Required, not optional** (supersedes the "(consider)" row under D-030) |
| ⬜ | `.claude/agents/*.md` (all writers) | **(b)** must write through that path |
| ⬜ | `methodologies/question-driven-25.yaml` | **(c)** `guiding_question_assessed: off`, with a comment that it turns on in the Assessment phase |
| ⬜ | `src/classkit/validate.py` | **(c)** new rule `unit_has_entry_quiz_items` (warn) |
| ⬜ | `schemas/syllabus.schema.json` | **(d)** `workload` optional (amends the D-021 row) |
| ⬜ | `src/classkit/validate.py` | **(d)** new rule `syllabus_workload_missing` (warn) |
| ⬜ | `methodologies/question-driven-25.yaml` | **(e)** `in_class.max_unmapped_minutes: 10` (was 15 in D-028) |
| ⬜ | `schemas/course.schema.json` | **(e)** new optional `in_class` block with `max_unmapped_minutes` |
| ⬜ | `src/classkit/model.py` | **(e)** course-level override wins over the methodology default |
| ⬜ | `src/classkit/validate.py` | **(e)** the cap rule reads the effective (overridden) value |
| ⬜ | `schemas/assessment-item.schema.json` | **(g)** rename `answer` → `model_answer` |
| ⬜ | `templates/assessment/item-open.md` | **(g)** same rename |
| ⬜ | `.claude/agents/assessment-writer.md` | **(g)** same rename |
| ⬜ | `.claude/commands/*.md` (all) | **(h)** approval gates sit in the command, between agent invocations — never inside an agent |
| ⬜ | `.claude/commands/plan-units.md` | **(i)** sequential file-based handoff: syllabus written first, architect reads it |
| ⬜ | `.claude/agents/curriculum-architect.md` | **(i)** read outcome ids from `syllabus.md`; never invent one |
| ⬜ | `tests/test_course_lifecycle.py` | tests for `activity_item_reference`, the course-level cap override, and the overwrite-refusal path |

## Cross-cutting

| | Artifact | Change |
|---|---|---|
| ⬜ | `FRAMEWORK-SPEC.md §10` | add: parts of this document are designed and not built; the critic now owns estimate honesty |
| ⬜ | `tests/` | the scaffold→validate round-trip must stay green at every step — invariant 6 means templates and schemas move together |

**Count as of 2026-09-10:** 9 decisions, 90 artifact changes, 0 built. (D-025 refines D-020 rows and
D-031 amends several — no double-counting intended; D-026/D-027 are documentation decisions, already
executed. D-031 rows supersede the "(consider)" overwrite-helper row under D-030.)

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
