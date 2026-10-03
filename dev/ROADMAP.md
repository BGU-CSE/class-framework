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
   and exam items are here.) Also consider **Q-029**: using the entry quiz to check *homework*, which
   would give homework the accountability loop it currently lacks — note the cross-unit referencing
   collision recorded there.
3. **Exports** — the Gem *builder*, PPTX, and the **rendered syllabus** (D-032). "Generate an artifact
   from the designed course." (Gem-as-a-study-path is Core; only the builder defers.) Also consider
   **Q-030**: shipping the Gem as a repository students clone and open with Claude Code — read its
   confidentiality constraint before starting.
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
| **0. Foundation** ✅ | The overwrite-safe write path. Nothing else — this is deliberately thin. | D-031b |
| **1. Initialize** ✅ | `classkit scaffold course` produces a complete, valid course skeleton *including* `syllabus/syllabus.md`. The teacher's first contact with the framework. | D-021 (schema, template, model, scaffold rows), D-031d |
| **2. Ingest + course log** ✅ — **2a ✅** validation re-classification (D-037) + course log (D-036); **2b ✅** ingest (awaiting independent review and Avin's hand test on real materials) | `/ingest` end to end: pre-flight report, `classkit ingest` (extractors, anchors, manifest, incremental, hand-edit detection), classification and duplicate confirmation, `classkit add-url`, `material_locator_resolves`. Plus the course log — `classkit log` — since ingest is its first user. **Designed** (Q-028 → D-035, D-036). D-037 folded in as 2a, since it reworks the validator ingest's rule lands in. | D-035, D-036, D-037 |
| **2c. The hand test's fixes** — **2c-1 ✅** privacy and `classkit doctor` (gap report `reviews/impl-gaps-step-2c-1.md`); **2c-2 ✅** the rest (gap report `reviews/impl-gaps-step-2c-2.md`); **reviewed ✅** (`reviews/impl-review-step-2c.md`; its outcome is D-042). **Step 2 closes after Avin's re-test** with a fresh course | From Avin's hand test of 0–2b (`reviews/manual-test-step-0-2b.md`). 2c-1: `source/private/` (committed index, local full text), `audience` and `instructor_material_cited`, `course/.gitignore`, `private_material_committed`, `classkit doctor`. 2c-2: D-041 (the self-certifying full text, `course_gitignore_missing`, `write.remove()`, permissions, `.DS_Store`), duplicate detection and link harvesting dropped, `units: all`, `materials/coverage.md`, prose locators, refusal diff, `write --diff`, path kinds, and the plain extraction/UX fixes. Two implementation rounds, **one review after 2c-2**. Rows tagged **[2c-1]** / **[2c-2]** in the D-040 ledger block. | D-040 |
| **3. Syllabus** — the first increment of the re-oriented Core (D-043) | `/plan-syllabus` (syllabus-designer, best effort, gated), `/review-syllabus`, `unit_map`, `classkit approve syllabus`, `classkit status`. **Build, then Avin checks it on a real course.** Rows tagged **[3-syllabus]**. Then the units increment (`/plan-units N…`, rows **[units]**), specified next. | D-029, D-032, D-040, D-043 |
| **4. Study sessions** | `answer`, `est_minutes`, `defer_to_class`, session-level `paths`, the budget rule, `study-session-designer`, the rewritten `estimating-study-time` skill. | D-019, D-020, D-023, D-025 |
| **5. Entry quiz** | `model_answer` rename, `usage` scoping, `unit_has_entry_quiz_items`, `assessment-writer` scoped to the entry quiz. | D-031c, D-031g |
| **6. In-class hour** | Optional `guiding_questions` + `reason`, the unmapped-time cap and its course override, `activity_item_reference`, `lesson-planner`. | D-028, D-031a, D-031e |
| **7. Review and gates** | `course-critic` updates (estimate honesty, deferral abuse, syllabus judgment), approval gates in every command. | D-025, D-029, D-030, D-031h |
| **8. Docs** 🔨 | Re-derive `README.md` and `GETTING-STARTED.md` **from the spec**. Done once (Session 24) ahead of schedule, because Avin follows `GETTING-STARTED.md` when hand-testing — so it has to be true *now*, not at the end. Revisit as later steps land. | D-028, D-030 rows |

**Step 5 must precede step 6** — that is D-031a: the entry-quiz items have to exist before the lesson
plan can reference their ids.

**A real course can be attempted after step 4** (or step 6 for a full unit). That is the first
opportunity to test against real material, which is where the useful information is.

---

# Implementation ledger

**The design draft is finished first; this ledger is worked through afterwards.** The draft is
finished and implementation has started, working the steps in the plan above. The ledger exists so
that no consequence of a decision is forgotten; tick a row in the commit that lands it.

`FRAMEWORK-SPEC.md` describes the **target** design and reads as if it exists. **This ledger is authoritative
for what actually exists.** Anything still marked ⬜ below is designed, not built; when a row lands,
the matching **(target)** tag comes off §8 of the spec in the same commit.

**Rule:** a decision marked `locked (design)` in `_devlog/01-decisions.md` must have a row here in
the same commit. Add rows as the draft continues; tick them as implementation lands.

Status: ⬜ not built · 🔨 in progress · ✅ done

## D-019 — `answer` field on every Guiding Question

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/study-session.schema.json` | `answer` on each goal: ~~required, `minItems: 1`~~ **optional — D-037: presence is advisory, checked by the rule below**, items `{kind, ref, note?}`, `kind ∈ textbook \| slide \| video \| article \| web \| other` |
| ⬜ | `src/classkit/validate.py` | new rule `answer_reference_present`, severity ~~`error`~~ **`warn` (D-037)** |
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
| ⬜ | `schemas/study-session.schema.json` | remove `paths` from goal; add optional session-level `paths`; add `est_minutes` to each goal — ~~required~~ **optional** (D-038): a missing estimate makes the budget rule report the session as *unverifiable* (warn) |
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
| ✅ | `schemas/syllabus.schema.json` | **new** — `goal`, `outcomes[]` (`CO1…`, statement, optional bloom), `workload` (credits, credit_system, total_hours), `prerequisites`, reserved `assessment` block |
| ✅ | `schemas/unit.schema.json` | `outcomes: [CO1…]` on each Unit Objective — **optional**, per D-037; landed in step 2a because `outcome_reference` needs it. The template does not set it yet (step 3) |
| ✅ | `src/classkit/model.py` | load `syllabus/syllabus.md` into the course model — `Course.syllabus` and `Course.outcomes` |
| ✅ | `src/classkit/validate.py` | `SCHEMA_FOR` entry so the syllabus is schema-checked |
| ⬜ | `src/classkit/validate.py` | two rules: `outcome_coverage` (no orphan Course Outcome) and `objective_maps_to_outcome` (no orphan objective) — both **alert** (D-037). The integrity half, `outcome_reference`, landed in step 2a |
| ✅ | `templates/course/syllabus.md` | **new** — Bologna-style default, generic (ECTS is one instantiation, not hardcoded — invariant 2). Scaffolds `CO1`/`CO2` to match a scaffolded unit's two objectives, so the step-3 coverage rules land on a clean skeleton |
| ✅ | `src/classkit/scaffold.py` | write the syllabus into the reserved `syllabus/` slot, create-only (the `syllabus/.gitkeep` it replaced is gone) |
| ✅ | `CLAUDE.md` | `CO1` ID convention; glossary entries for Syllabus and Course Outcome |
| ⬜ | `.claude/agents/curriculum-architect.md` | authors the syllabus; sets `outcomes` on the objectives it writes |
| ⬜ | `.claude/commands/plan-units.md` | the syllabus is part of planning the semester |
| ✅ | `GETTING-STARTED.md` | the syllabus is a thing teachers edit; the settings section names only `course.yaml` |
| 🔨 | `tests/test_course_lifecycle.py` | scaffold produces a valid syllabus ✅; both coverage rules fire when broken ⬜ (step 3) |

**Later, not now:** `workload.total_hours` enables a course-scope workload check — all home-study
`est_minutes` + in-class + homework against the declared workload. It needs homework (Q-026) first.

## D-023 — A question has a recorded answer, or is explicitly deferred to the in-class meeting

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/study-session.schema.json` | `defer_to_class: boolean` (default false) on each goal; `answer` ~~required~~ *expected* unless `defer_to_class` is true — **the rule checks it, not the schema (D-037)** |
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
| 🔨 | `schemas/in-class-session.schema.json` | `guiding_questions` no longer required on an activity ✅ (step 2a, as D-037 pedagogical presence); add optional `reason` string ⬜ (step 6) |
| ✅ | `src/classkit/validate.py` | `activity_references_guiding_question` → **warn** when empty; still **error** when a referenced id is not of this unit. *Amended by D-037 and built so:* empty → `activity_without_guiding_question` (warn); another unit's id → `activity_references_other_unit` (warn); an id that exists nowhere → `activity_references_guiding_question` (error) |
| ⬜ | `src/classkit/validate.py` | new rule `in_class_unmapped_time_cap` (~~error~~ **warn, D-037**): Σ duration of activities with no guiding question ≤ `in_class.max_unmapped_minutes` |
| ⬜ | `methodologies/question-driven-25.yaml` | add `in_class.max_unmapped_minutes: 15`; severities for both rules |
| ⬜ | `.claude/agents/lesson-planner.md` | most activities build on guiding questions; unmapped ones need a `reason` and cost against the cap |
| ⬜ | `.claude/agents/course-critic.md` | judge whether an unmapped activity's `reason` is legitimate, and whether the hour leans on the cap |
| ✅ | `CLAUDE.md` | invariant 4 reworded (done in the same commit as the spec) |
| ⬜ | `README.md` | "every in-class Activity must reference at least one Guiding Question" is now wrong |
| 🔨 | `tests/test_course_lifecycle.py` | an unmapped activity warns ✅; exceeding the cap ~~errors~~ **warns (D-037)** ⬜ (step 6); a foreign-unit reference ~~still errors~~ **warns (D-037)** ✅ |

## D-029 — `syllabus-designer` agent

| | Artifact | Change |
|---|---|---|
| ⬜ | `.claude/agents/syllabus-designer.md` | **[3-syllabus]** **new** — owns `syllabus/syllabus.md`: goal, Course Outcomes, workload, prerequisites (scope widened by D-043) |
| ⬜ | `.claude/commands/plan-units.md` | ~~run syllabus-designer and curriculum-architect as one flow~~ — **superseded by D-043**: `/plan-syllabus` is its own command; `/plan-units N…` plans unit objectives (units increment) |
| ⬜ | `.claude/agents/curriculum-architect.md` | scope narrowed to the unit map and unit objectives; consumes the outcome list |
| ⬜ | `.claude/agents/course-critic.md` | **[3-syllabus]** syllabus judgment: outcomes that are real outcomes not topic labels, a meaningful goal, plausible workload — run by `/review-syllabus` |

## D-030 — Command interaction protocol

| | Artifact | Change |
|---|---|---|
| ⬜ | `.claude/commands/*.md` (all) | stepwise execution with an approval gate per step; announce → produce → show → wait |
| ⬜ | `.claude/agents/*.md` (all writers) | before writing, detect existing content and ask; never silently overwrite |
| ⬜ | `.claude/agents/*.md` (all writers) | revision mode: when output exists, update in place and report the diff; regeneration is explicit |
| ✅ | `CLAUDE.md` | invariant 5 reworded (done in the same commit as the spec) |
| ⬜ | `GETTING-STARTED.md` | describe the stepwise/approval workflow a teacher should expect |
| ✅ | `src/classkit/` | a write path that detects existing content, so the check is not prompt-only. **Upgraded from "consider" to required by D-031b — see its rows below**, where it landed. |

## D-031 — Core spec review findings

Source: `_devlog/../reviews/core-spec-review-01.md`. Some rows amend rows above; implement together.

| | Artifact | Change |
|---|---|---|
| ⬜ | `.claude/commands/design-unit.md` | **(a)** swap the order: assessment-writer (entry quiz) runs *before* lesson-planner |
| ⬜ | `.claude/agents/lesson-planner.md` | **(a)** read the existing entry-quiz items; put their real ids in the quiz activity's `items`; never invent an id |
| ⬜ | `src/classkit/validate.py` | **(a)** new rule `activity_item_reference` (error): every id in `activity.items` resolves to an existing item of that unit |
| ✅ | `src/classkit/write.py` (new) | **(b)** a write path that structurally refuses to overwrite existing content without explicit confirmation — generalizes `write_new()` beyond scaffold. **Required, not optional** (supersedes the "(consider)" row under D-030). Built with the `classkit write` CLI surface agents use, and `scaffold.write_new()` refactored onto it; specified in `FRAMEWORK-SPEC.md` §8.6. Tests in `tests/test_write_path.py` |
| ⬜ | `.claude/agents/*.md` (all writers) | **(b)** must write through that path — **and drop `Write`/`Edit` from their `tools:` front matter** (G-4). Removing the tools is what makes the guarantee structural; leaving them makes `classkit write` merely *available*, which is the prompt-only situation D-031b exists to replace. Each agent is amended in the step where it is touched |
| ⬜ | `methodologies/question-driven-25.yaml` | **(c)** `guiding_question_assessed: off`, with a comment that it turns on in the Assessment phase |
| ⬜ | `src/classkit/validate.py` | **(c)** new rule `unit_has_entry_quiz_items` (warn) |
| ✅ | `schemas/syllabus.schema.json` | **(d)** `workload` optional (amends the D-021 row) |
| ✅ | `src/classkit/validate.py` | **(d)** new rule `syllabus_workload_missing` (warn) — also fires when there is no syllabus at all |
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
| ⬜ | `tests/test_course_lifecycle.py` | tests for `activity_item_reference` and the course-level cap override |
| ✅ | `tests/test_write_path.py` (new) | the overwrite-refusal path — its own file, not the scaffold→validate round-trip (G-6) |

## D-032 — Syllabus completeness (Bologna); rendering deferred

Reopens step 1's artifact — the schema and template exist, these extend them.

| | Artifact | Change |
|---|---|---|
| ⬜ | `schemas/syllabus.schema.json` | **[3-syllabus]** add optional `reading {required[], recommended[]}`. ~~`level`, `course_type`, `offered`, `teaching_methods`~~ — **superseded by D-043**: body sections, not fields |
| ⬜ | `templates/course/syllabus.md` | **[3-syllabus]** see D-043's template row (it replaces this one) |
| ⬜ | `GETTING-STARTED.md` | **[3-syllabus]** the syllabus is where course-descriptor information lives |
| ⬜ | `.claude/agents/syllabus-designer.md` | **[3-syllabus]** authors the full descriptor; leaves unknown fields out rather than inventing them (invariant 7) — see D-043 |
| ⬜ | *(Exports slice)* | the **rendered syllabus** — one document combining `syllabus.md` + identity fields from `course.yaml` + a unit overview derived from the units. Deferred; listed here so it is not lost |

## D-033 — Rule states; `syllabus_missing`

All land in **step 3**, with the coverage chain.

| | Artifact | Change |
|---|---|---|
| ⬜ | `src/classkit/validate.py` | a course-complete predicate (`units on disk == course.yaml units`) that completeness rules gate on |
| ⬜ | `src/classkit/validate.py` | `outcome_coverage` runs only when the course is complete; when skipped, `validate` reports it as skipped and why |
| ⬜ | `src/classkit/validate.py` | new rule `syllabus_missing` (~~error~~ **alert, D-037**) |
| ⬜ | `src/classkit/validate.py` | validator output can express "skipped" alongside error/alert/warn |
| ⬜ | `tests/test_course_lifecycle.py` | a fresh scaffold does not fire `outcome_coverage`; a *complete* course with an uncovered outcome does; deleting the syllabus fires `syllabus_missing` |
| ⬜ | `CLAUDE.md` | "Adding a validation rule" must say to declare consistency vs completeness |

## D-035 — Materials and ingest

| | Artifact | Change |
|---|---|---|
| ✅ | `src/classkit/ingest/` (new) | scan `materials/source/` recursively; hash; detect exact duplicates; pre-flight report (counts, pages/slides, duplicates, links, unsupported, time estimate) |
| ✅ | `src/classkit/ingest/` extractors | built-in `md`, `txt`, `pptx`, `pdf`, `docx` → `.md` with anchor headings (`## Slide N`, `## Page N`, own headings); optional pandoc / LibreOffice; registry keyed by extension; `unsupported` / `no-text` / `media` statuses. *Caveat:* the pandoc / LibreOffice **installed** path is written but not exercised — neither tool is on the build machine; the missing-tool path is tested |
| ✅ | `src/classkit/ingest/` manifest | `materials/manifest.yaml`: stable `M<NNNN>` ids, re-match renamed files by hash, merged duplicates, `ingested_hash` for hand-edit detection, removed sources marked not deleted; resumable |
| ✅ | `src/classkit/cli.py` | `classkit ingest [--preflight]`, `classkit add-url URL [--note]`. Also `--overwrite ID` / `--keep ID` (the teacher's answer to a refused hand edit) and `classkit material set\|merge\|duplicates` (how the classifier records without Write/Edit) |
| ✅ | `schemas/manifest.schema.json` (new) | the manifest's fields (spec §8.7), plus `source_hashes`, `removed_at`, `merged_into`, `note`, `duration` (gap report 2b) |
| ✅ | `src/classkit/validate.py` | `material_locator_resolves` (error, consistency) and `materials_not_ingested` (warn). Locators read from `LOCATOR_FIELDS`: study-path `ref`, activity `materials`; the manifest is schema-checked |
| ⬜ | `src/classkit/validate.py` (step 4) | add the goal's `answer[].ref` to `LOCATOR_FIELDS`; and when D-020 moves study paths to the session, change `goals[].paths[].ref` (checked today) to `paths[].ref` — one line each, no rule change |
| ✅ | `src/classkit/scaffold.py`, `templates/course/` | scaffold `materials/source/links.md` and `materials/ingested/`; update `materials-source-README.md` |
| ✅ | `pyproject.toml` | extraction dependencies (pptx, pdf, docx readers) — `python-pptx`, `python-docx`, `pypdf` |
| ✅ | `.claude/commands/ingest.md` | pre-flight → gate → convert → classify → confirm duplicates → report; log each approved step |
| ✅ | `.claude/agents/` (ingest classification) | set `kind` and `units`; propose same-material duplicates for confirmation; never modify `source/`. **`material-classifier`**, no Write/Edit — records through `classkit material set` |
| ⬜ | `.claude/agents/*` that cite material | prefer `M<NNNN>#anchor` locators (study-session-designer, assessment-writer, topic-researcher, course-critic) — land with each agent's own step |
| ✅ | `GETTING-STARTED.md`, `CLAUDE.md` | materials, `links.md`, `add-url`, locators (also `README.md`, `dev/MANUAL-TESTING.md`) |
| ✅ | `tests/` | extraction anchors per format; incremental re-run; rename keeps id; hand edit refused; duplicate merge; locator rule fires on a missing anchor — `tests/test_ingest.py`, rule tests in `test_course_lifecycle.py` |

## D-036 — The course log

| | Artifact | Change |
|---|---|---|
| ✅ | `src/classkit/log.py` (new), `cli.py` | `classkit log` — append a structured entry (date, actor, changed IDs, why, files) to `LOG.md`. The actor is part of the title, as in the spec's example heading |
| ✅ | `src/classkit/scaffold.py` | create `LOG.md` with a first entry when a course is scaffolded |
| 🔨 | `.claude/commands/*.md` (all) | log each approved step (with the D-030 gates). Done: `/ingest`. The other five land with their steps |
| 🔨 | `.claude/agents/*.md` (writers) | read recent log entries before starting work. Done: `material-classifier` |
| ✅ | `tests/` | append-only; format parseable — `tests/test_course_log.py` |

## D-037 — Teacher authority: integrity vs advisory

| | Artifact | Change |
|---|---|---|
| ✅ | `src/classkit/validate.py` | new severity `alert`: reported first, marked `ALERT`, does not fail; exit 1 only on `error`; `--strict` counts alerts and warnings. `DEFAULT_SEVERITY` is now a **complete** table (errors included) |
| ✅ | `src/classkit/validate.py` | re-classify existing rules per spec §8.4 (demote pedagogical errors to warn/alert); split `activity_references_guiding_question` and `item_reference`; new `outcome_reference`. Split codes: `activity_without_guiding_question`, `activity_references_other_unit`, `item_no_correct_choice`. Also new: `unknown_rule` (warn) — a mistyped rule name in `rules:` or `accepted:` |
| ✅ | `src/classkit/validate.py`, `model.py` | read `course.yaml` `rules:` (wins over methodology); honour `accepted:` per file; print a count of accepted exceptions (and of entries that no longer match anything). A bare YAML `off` — parsed as `false` — is read as `"off"` |
| ✅ | `schemas/*.schema.json` | `accepted: [{rule, reason}]` on every front-matter artifact; `rules:` on course; move pedagogical presence out of `required` (e.g. `answer`, objective `outcomes`). Built: activity `guiding_questions` relaxed; objective `outcomes` added *optional*; `answer` does not exist yet — step 4 must add it optional |
| ✅ | `methodologies/question-driven-25.yaml` | severities consistent with §8.4 — the block now lists only departures from the defaults; `methodology.schema.json` accepts `alert` |
| ⬜ | `.claude/agents/*.md`, `.claude/commands/*.md` | fix what you caused; never add `accepted:` / change `rules:` / raise a threshold unless asked; never overrule a teacher decision; log accepted exceptions |
| ✅ | `tests/` | each demoted rule warns, not errors; alert ordering and exit code; `rules:` override; `accepted:` suppresses and is counted |
| ✅ | `dev/VISION.md`, `FRAMEWORK-SPEC.md`, `CLAUDE.md`, `dev/CLAUDE.md`, `README.md`, `GETTING-STARTED.md` | the principle and the new model, written down (this commit) |

## D-038 — Step 2a review outcomes

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/*.schema.json` (5 with `accepted:`) | `reason` optional; `rule` not pattern-checked; examples use `in_class_missing` |
| ✅ | `src/classkit/validate.py` | new advisory rule `accepted_without_reason` (warn); blank reason counts as missing |
| ✅ | `src/classkit/write.py`, `cli.py` | `append()` / `classkit write --append` — the write path's append mode |
| ✅ | `src/classkit/log.py` | the course log appends through the write path, not beside it |
| ✅ | `tests/` | reason-less and blank-reason acceptances warn; a capitalised typo is `unknown_rule`, not a schema error; append never rewrites, creates via `write()`, dry-runs, refuses a directory; `--append` and `--overwrite` are exclusive |
| ✅ | `dev/FRAMEWORK-SPEC.md`, `CLAUDE.md`, `dev/CLAUDE.md`, `GETTING-STARTED.md` | §8.2, §8.4, §8.6, §8.8 and the teacher docs; the `accepted:` example uses a rule that exists today |
| ⬜ | `src/classkit/validate.py` (step 4) | the budget rule reports a session with a missing `est_minutes` as *unverifiable* (warn), instead of requiring the field |
| ⬜ | `schemas/assessment-item.schema.json`, `validate.py` (step 5) | move `rubric`-for-`open` from schema `required` to an advisory rule |

## D-039 — Step 2b review outcomes

| | Artifact | Change |
|---|---|---|
| ✅ | `.claude/agents/material-classifier.md` | read-only (`Read, Grep, Glob`); returns its classification as a YAML block; cites books with section / exercise / printed page |
| ✅ | `src/classkit/ingest/core.py`, `cli.py` | `classkit material apply` — a batch of `{id, kind, units, title}`, all or nothing |
| ✅ | `.claude/commands/ingest.md` | passes the suspected pairs to the agent; shows the classification, applies corrections, records with `material apply`; `--no-log` on its `classkit ingest` calls |
| ✅ | `src/classkit/ingest/report.py`, `cli.py` | `classkit ingest` logs every run that changes something (`--why`, `--no-log`) |
| ✅ | `tests/` | the agent's tools; `apply` records, is all or nothing, reads YAML; a hand run is logged, a no-op run and a `--no-log` run are not; moved/removed sources warn; locators read hand-edited anchors |
| ✅ | `dev/FRAMEWORK-SPEC.md`, `CLAUDE.md`, `GETTING-STARTED.md`, `README.md` | §3.1, §5.1, §6, §8.2 (book citations), §8.7 (classify, logging, `units` re-map), §9 |
| ⬜ | `.claude/commands/plan-units.md` (step 3) | a gated final step: re-map materials' `units` to the approved unit map, through `classkit material apply`; decide how a teacher's hand-corrected hint is protected |
| ⬜ | `.claude/agents/*` that cite books (step 4) | a book citation's `note` gives section, exercise/question number, printed page |
| ⬜ | `src/classkit/validate.py` (step 4, proposed) | advisory: a locator to a `textbook` material with no `note` → warn |

## D-040 — Private and instructor-only material; `classkit doctor`; the hand test's fixes

Tags: **[2c-1]** privacy and `doctor` · **[2c-2]** the rest of the hand test's fixes · **[step 3]**, **[step 4]**, **[Exports]** land with those steps.

| | Artifact | Change |
|---|---|---|
| ✅ | `src/classkit/scaffold.py`, `templates/course/` | **[2c-1]** scaffold `course/.gitignore` covering `materials/source/private/` and `materials/private-text/` (create-only; added to existing courses on re-scaffold) — done; a re-run on a course with a log appends an entry naming what it created |
| ✅ | `src/classkit/ingest/` | **[2c-1]** `private` from the canonical path; a private material's committed `.md` is an index (anchors, printed page labels, sections from the PDF outline or detected headings; `text: index`); full text to `materials/private-text/`; moving into/out of `private/` rewrites both — done; `private/` matched in any case (macOS git ignores `Private/`); a private title is never body text; both files checked before either is written; an unedited local copy is dropped on a move out |
| ✅ | `src/classkit/ingest/` | **[2c-1]** a missing private source is never marked removed; `classkit material remove ID` — done; `remove` refuses a non-private material and one whose source is still here |
| ✅ | `schemas/manifest.schema.json` | **[2c-1]** `private` (boolean), `private_text_hash`, `audience` (`student \| instructor`) |
| ✅ | `src/classkit/ingest/core.py`, `cli.py` | **[2c-1]** `audience` in `material apply` / `material set --audience` |
| ✅ | `src/classkit/validate.py` | **[2c-1]** `instructor_material_cited` (alert) over student-facing locators; `private_material_committed` (warn, via git); `materials_not_ingested` ignores `private/` — done; `STUDENT_FACING_FIELDS`; `git ls-files` with `:(icase)`; `reconcile(local=False)` |
| ✅ | `src/classkit/doctor.py` (new), `cli.py` | **[2c-1]** `classkit doctor` — gitignore, private sources/full texts present or stale, leftovers, dependencies importable, optional converters, mode; read-only — done; also: `course/.gitignore` itself committed (a global excludes file listing `.gitignore` was found on the developer's machine), a `Private/` in another case, a committed copy that is not an index |
| ✅ | `.claude/agents/material-classifier.md`, `.claude/commands/ingest.md` | **[2c-1]** propose `audience` with a reason; flag a published book outside `private/`; `/ingest` runs `doctor` first; agents told when a material is index-only here — done; other agents are told through the root `CLAUDE.md` until their own prompts are rewritten (steps 3, 4) |
| ⬜ | exporters (Exports phase) | **[Exports]** refuse, in code, to bundle or publish `audience: instructor` or private material |
| ✅ | `.claude/commands/ingest.md`, `material-classifier` | **[2c-2]** the coverage report states its scope ("no material yet" ≠ "thin"); `/ingest` writes it to `materials/coverage.md` after the teacher has read it, through the write path |
| ✅ | `src/classkit/write.py`, `cli.py` | **[2c-2]** `classkit write --diff`: a unified diff of what `--overwrite` would change, writing nothing (invariant 5's scope already written into the spec and `dev/CLAUDE.md`) |
| ✅ | `src/classkit/validate.py`, `CLAUDE.md`, agents | **[2c-2]** `material_locator_in_text` (warn) over Markdown bodies (not `LOG.md`, `ingested/`); locators always fully qualified |
| ✅ | `src/classkit/ingest/core.py`, `report.py` | **[2c-2]** a hand-edit refusal shows the diff between the current file and a fresh extraction, grouped by anchor |
| 🔨 | `schemas/study-session.schema.json` | **[2c-2; the rest step 4]** path kinds gain `slides` and `notes` (now) — ✅ done in 2c-2; step 4: one resource-kind vocabulary for paths and `answer`, `kind` optional when `ref` is a material locator |
| ⬜ | `schemas/syllabus.schema.json`, template (step 3) | **[3-syllabus]** `unit_map` (number, title, summary, evidence) |
| ⬜ | `src/classkit/validate.py` (step 3) | **[step 3]** `unit_map_mismatch` (warn, consistency) |
| ⬜ | `.claude/commands/plan-units.md`, `syllabus-designer`, `curriculum-architect` (step 3) | **[step 3]** course level whole, from evidence (asks when there is none); the unit map in the syllabus; units planned incrementally — `/plan-units 4 5`; reads `materials/coverage.md` |
| ✅ | `schemas/manifest.schema.json`, `ingest/core.py`, `cli.py`, agent | **[2c-2]** `units: all` (course-wide) in the schema, `apply`, `set --unit all`; the classifier uses it; consumers (designers, the D-039 re-map) treat `all` as every unit |
| ✅ | `src/classkit/ingest/` (extract, core, report), schema, agent | **[2c-2]** stop harvesting URLs from materials; links only from `links.md` / `add-url`; `found_in` retired (kept in the schema for old manifests); the classifier mentions links that look like course resources and suggests `add-url` |
| ✅ | `src/classkit/ingest/`, `cli.py`, `.claude/commands/ingest.md`, agent | **[2c-2]** drop suspected-duplicate detection (name and content), the `material duplicates` verb and the gate-3 duplicate question; exact copies still merge silently; `material merge` stays, optional; the classifier may mention a two-format relation; agents cite the deck over its PDF |
| ✅ | `src/classkit/ingest/` (extract, report), `cli.py`, `pyproject.toml`, templates, docs | **[2c-2]** the hand test's plain fixes: F-01 (MANUAL-TESTING count/commit line), F-02 (plurals), F-03/F-09/F-10 (silence PDF-library noise to one line per file; add fontTools and verify; normalise ligatures), F-06 + F-08 (DOCX text boxes; low-yield warning and empty slide/page counts per material), F-07 (OMML equations as linear text or `[equation]`), F-12 (reject metadata titles like `*.dvi`; prefer the file name), F-14 (time estimate for large PDFs), F-18 (MANUAL-TESTING: ingest before scaffolding a unit), F-20 (session template: "warns", not "fails"), F-23 (pre-flight names what changed), F-25 (after a refusal, `validate` names `--keep`/`--overwrite`), F-27 (docs: `--overwrite` once after F-06) |
| ✅ | `CLAUDE.md`, `GETTING-STARTED.md`, `dev/MANUAL-TESTING.md` | **[2c-1]** private/, audience, doctor (the interim "don't commit book PDFs" warning is in `GETTING-STARTED.md` now) — done; also README, the scaffolded `source/README.md`, `dev/CLAUDE.md` |
| ✅ | `tests/` | **[2c-1]** gitignore scaffolded; private index has no body text and its locators resolve; full text only in `private-text/`; missing private source not removed; `remove`; both rules at their severity; `doctor` reports each case — done: `tests/test_private_material.py`, `tests/test_doctor.py`, lifecycle rule tests |

## D-041 — Step 2c-1 outcomes

| | Artifact | Change |
|---|---|---|
| ✅ | `src/classkit/ingest/`, `schemas/manifest.schema.json` | **[2c-2]** the full text certifies itself (`body_hash` in its front matter); a stale unedited full text is refreshed, not refused; `private_text_hash` retired (kept in the schema for old manifests) — done; `body_hash` covers the whole file but its own line, so a front-matter edit counts too; a pre-D-041 full text is judged by the old hash once |
| ✅ | `src/classkit/doctor.py` | **[2c-2]** a note when this machine's private copy differs from the one the committed index was built from — done; it replaces the earlier ACTION "source changed" for private material |
| ✅ | `src/classkit/validate.py` | **[2c-2]** `course_gitignore_missing` (warn, consistency) |
| ✅ | `src/classkit/write.py`, `ingest/` | **[2c-2]** `write.remove(path, expected_hash)`; ingest's one deletion goes through it; replacing a file keeps its permissions, new files get the umask default (not `0600`) |
| ✅ | `src/classkit/mode.py` | **[2c-2]** `classkit mode developer` also verifies `.gitignore` itself is tracked |
| ✅ | `.gitignore`, `templates/course/` (course `.gitignore`) | **[2c-2]** add `.DS_Store` |
| ✅ | `tests/` | **[2c-2]** a full text from another library version is not an edit; a stale unedited one is refreshed; an edited one refused; the differing-copy note; `course_gitignore_missing` at warn; `remove()` refuses a changed file; permissions kept; mode check refuses an untracked `.gitignore` |

## D-042 — Agents never copy private text into course files

| | Artifact | Change |
|---|---|---|
| ✅ | `src/classkit/doctor.py` | `check_quotation`: a committed course Markdown file sharing 12+ consecutive words with a private full text on this machine is an ACTION (file, material, anchor); the course log included; `source/`, `ingested/`, `private-text/` excluded; skipped where no full text is present |
| ✅ | `CLAUDE.md`, `.claude/agents/material-classifier.md` | the rule: cite by locator, own words, at most a short quoted phrase |
| ✅ | `dev/FRAMEWORK-SPEC.md`, `dev/MANUAL-TESTING.md` | §8.7 and §9; a re-test check |
| ✅ | `tests/test_doctor.py` | a copied sentence flagged with its length and anchor; a paraphrase and a short phrase pass; the log is checked; the index and full text are not; skipped without the full text |
| ⬜ | `.claude/agents/` that read material (study-session-designer, lesson-planner, assessment-writer, course-critic, topic-researcher) | state the rule in each, as each is rewritten (steps 4–7); the root `CLAUDE.md` carries it until then |

## D-043 — The syllabus as its own milestone; approvals and status; one verb scheme

Tags: **[3-syllabus]** the first spec-and-build increment of the re-oriented Core (build, then Avin
checks it on a real course) · **[units]** the next increment.

| | Artifact | Change |
|---|---|---|
| ⬜ | `.claude/agents/syllabus-designer.md` (new) | **[3-syllabus]** best effort; reads the evidence (old syllabus, `materials/coverage.md`, the book's index, `course.yaml`); drafts goal, outcomes, unit map, workload, prerequisites, reading, grading and the descriptor body mirroring the institution's form; asks rather than invents; always proposes an AI-use policy where AI study paths are used; never copies private text (D-042); read-only — returns, the command writes (like D-039) |
| ⬜ | `.claude/commands/plan-syllabus.md` (new) | **[3-syllabus]** shows `classkit status`; evidence → gate → full draft (write path) → gate → revision rounds → approval via `classkit approve syllabus`; each approved step logged |
| ⬜ | `.claude/commands/review-syllabus.md` (new) | **[3-syllabus]** runs `course-critic` on the syllabus; optional |
| ⬜ | `schemas/syllabus.schema.json` | **[3-syllabus]** `unit_map` (D-040 row), `approved {on, hash?}`, `assessment` description updated (draftable) |
| ⬜ | `templates/course/syllabus.md` | **[3-syllabus]** front matter: `unit_map`, `reading`, grading (commented); a default body skeleton of descriptor sections — description, aim, outcomes prose, teaching methods, level/type/when offered, schedule (from the map), workload, grading, reading, policies incl. AI use, staff and office hours |
| ⬜ | `src/classkit/approve.py` (new), `cli.py` | **[3-syllabus]** `classkit approve syllabus` — writes `approved {on, hash}` through the write path, logs it |
| ⬜ | `src/classkit/status.py` (new), `cli.py` | **[3-syllabus]** `classkit status` — read-only overview: syllabus approved / edited since / draft; the unit map with each unit's state (units: present or not, until the units increment defines states); materials ingested / outstanding |
| ⬜ | `.claude/commands/ingest.md` | **[3-syllabus]** shows `classkit status` first (the other commands as each is rewritten) |
| ⬜ | `CLAUDE.md`, `GETTING-STARTED.md`, `README.md`, `dev/MANUAL-TESTING.md` | **[3-syllabus]** `/plan-syllabus`, `/review-syllabus`, approval and status; a hand-test section |
| ⬜ | `tests/` | **[3-syllabus]** approve writes on/hash and logs; status reads approved / edited since / no-hash; schema accepts the new fields; a fresh scaffold still validates with 0 errors |
| ⬜ | `.claude/commands/plan-units.md`, `curriculum-architect` | **[units]** `/plan-units N…`: objectives for the named units against the approved syllabus; asks (does not refuse) when the syllabus is unapproved |
| ⬜ | `.claude/commands/write-items.md`, `design-unit.md` | **[units]** retire `/write-items` from Core; `/design-unit N [session K \| quiz \| class]` |

## Cross-cutting

| | Artifact | Change |
|---|---|---|
| ⬜ | `FRAMEWORK-SPEC.md §10` | add: parts of this document are designed and not built; the critic now owns estimate honesty |
| ✅ | `templates/course/course.yaml`, `GETTING-STARTED.md` | the `gem` block was scaffolded and documented although Exports is deferred (G-16). **Removed from the template and the settings table** — shipping configuration for a feature that does not exist confuses a teacher reading their own `course.yaml`. The optional field stays in `course.schema.json`, so a course that sets it still validates |
| ⬜ | `tests/` | the scaffold→validate round-trip must stay green at every step — invariant 6 means templates and schemas move together |

**Count as of 2026-10-03 (after D-043, the syllabus increment designed):** 19 decision blocks, 194 artifact
changes, **80 built, 6 in progress, 108 not started** — counted from the table. Step 2 is built and
reviewed; it closes after Avin's re-test with a fresh course. (After step 2c-2: 177; 76 / 6 / 95.) Step 2c-2 (every [2c-2] row in
the D-040 and D-041 blocks) is built; the path-kinds row is 🔨 because its step-4 half remains. Next:
one independent review of 2c-1 and 2c-2 together. (After step 2c-1 and D-041: 61 / 5 / 111 of 177.
After step 2c-1 alone: 170; 61 / 5 / 104.)
(After D-040 was designed: 51 / 5 / 114. After step 2b's review, D-039: 147 changes, 51 / 5 / 91.) Steps 0, 1, 2a and 2b
are done (D-032 reopens step 1's syllabus; that lands in step 3), except the rows that belong to
agents and commands of later steps (logging in the other five commands; agents that cite material
prefer `M<NNNN>#anchor`; D-039's step 3 and step 4 rows). Avin's hand test of steps 0–2b is done
(`reviews/manual-test-step-0-2b.md`); D-040 came from it and is designed, not built. Next: finish
going through that report, then build its fixes and D-040 (a step "2c"), then step 3. (Previous count, after step 2b before its review: 45 / 5 / 88 of 138, in 14 blocks — that
line said "15 decisions". After step 2a: 33 / 3 / 101 of 137. The count before that, "14 built, 1 in progress, 88 not
started", did not match its own table — 16/1/112 — and is superseded. D-025 refines D-020 rows and D-031 amends several — no double-counting intended;
D-026/D-027 are documentation decisions, already executed. D-031 rows supersede the "(consider)"
overwrite-helper row under D-030. Rows struck through ~~like this~~ were amended by D-037.)

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
