# Homework module decisions

Thirty-one decisions from the homework module design phase, September 2026.
Each has a full rationale. Numbered with the module's own prefix, `HW-D`,
so they can never collide with the framework's `D-` sequence (HW-D11).

HW-D01 is the primary decision (homework as a first-class content type);
HW-D02 through HW-D07 introduce supporting mechanisms and refinements.
HW-D08 records that the module carries out the framework's own D-031g rename.
HW-D09 moves homework item writing into its own agent.
HW-D10 separates the two axes: format is the framework's, class is the module's.
HW-D11 gives the module its own numbering.
HW-D12 routes every homework write through the framework's safe write path.
HW-D13 makes homework optional for the validator and for scaffolding.
HW-D14 renames the numeric answer's `units` to `measurement_units`.
HW-D15 aligns `/create-homework` with the spec and makes its two gates explicit.
HW-D16 gives `homework-defaults.yaml` a schema and a consistency rule.
HW-D17 removes `/review-homework`.
HW-D18 skips tool-dependent items and gives the teacher an aid for every skipped item.
HW-D19 adds a material-fit check to `item-critic`.
HW-D20 puts homework document export in the module's scope.
HW-D21 keeps the framework's item bank as the single question bank.
HW-D22 makes the item-bank overview an on-demand `classkit` report.
HW-D23 has an agent create the Word documents, with a leak check.
HW-D24 lets the teacher choose where the Word documents go; git never holds them.
HW-D25 drops `answer_release`.
HW-D26 targets versions at Guiding Questions from a quiz report and keeps student data out.
HW-D27 replaces the class mix with item counts per class.
HW-D28 records per-item tools in the manifest, not in the item schema.
HW-D29 drops `prerequisites` from the manifest.
HW-D30 lays out the Word documents from a course settings file.
HW-D31 keeps focus notes in the plan and approves due dates before writing.
HW-D01 has one addendum for the `/write-items homework` hand-off.

## HW-D01 — Homework as a first-class content type
**Date:** 2026-09-22 · **Status:** provisional · **Resolves Q-026.**

Homework becomes a first-class **manifest-level** content type in the
framework, symmetric with unit, session, and item. This does NOT introduce
a new item format — homework items keep whatever `format` fits their answer
shape (`open`, `code`, `numeric`, `multiple-choice`, etc.), the same as
items in any other context. What's new is the homework manifest itself:
its own schema (`homework.schema.json`), its own on-disk location
(`course/assessments/homework/HW0N.md`), and its own metadata: `purpose` (practice / graded / diagnostic), `units` it spans,
`total_minutes` budget, `allowed_tools`, `collaboration`, `open_book`,
`answer_release`, optional `versions` for grouped variants, and `source`
(unit materials or a prior quiz report).

**Item referencing, not copying.** The homework manifest carries an ordered
array of item ids from `course/assessments/items/`. Items live where they
always did; the manifest is a thin file. Reuse across homework becomes a
metadata concern (the item's `usage` array), not a duplication concern.

**Orchestration.** `/create-homework` (new command) reads the repo, runs a
short interview only for what defaults don't cover, hands to
`homework-planner` (new agent) which produces a plan behind a teacher
approval gate, then to `assessment-writer` (existing) for item writing,
then to `classkit validate`, and finally a second teacher gate before the
manifest is finalized. Learned defaults in
`course/assessments/homework-defaults.yaml` shrink the interview over time.

**Why:** Homework carries metadata that doesn't belong on any single item —
purpose, budget, tools, versioning, source. Modeling it as a view over the
item bank was considered and rejected: the "view" would need to carry this
metadata somewhere, and putting it on items pollutes item metadata with
things that aren't about the item. First-class type is honest about the
distinction.

**Consequence:**
- New validator rules govern the homework object (see §8.4):
  `homework_schema`, `homework_id_consistency`, `homework_item_reference`,
  `homework_item_usage`, `homework_units_declared`, `homework_coverage`,
  `homework_prerequisites_precede`, `homework_budget_fits`,
  `homework_versions_fair`, `graded_requires_rubric`,
  `graded_answer_release_safe`, `homework_source_quiz_exists`,
  `assessment_scheme_complete`.
- Q-029 (entry-quiz-checks-homework) becomes tractable now that homework
  has a schema-representable identity. Still open, still Assessment-slice.
- Programming assignments — the sharp case cited in the original Q-026 —
  are handled by choosing the appropriate `format` (`code` for autograded,
  `open` for human-graded submissions where the student's answer includes
  code) plus `item_class: Coding` (or `Research` for AI-assisted non-code
  work) — see HW-D02. A multi-part programming assignment is a set of code
  items in one homework, not a new content type.

**Files landed:**
- `schemas/homework.schema.json`
- `schemas/assessment-item.schema.json` (updated for the new axes)
- `.claude/commands/create-homework.md`
- `.claude/commands/new-hw-type.md`
- `.claude/commands/review-homework.md`
- `.claude/agents/homework-planner.md`
- `.claude/agents/interviewer.md` (see HW-D04)
- `.claude/agents/item-critic.md`
- `.claude/agents/item-solver.md`
- `.claude/agents/assessment-writer.md` (updated for class-branching)
- `.claude/skills/writing-code-items/SKILL.md`
- `.claude/skills/writing-research-items/SKILL.md`

**Deferred:** Python implementation of the 18 §8.4 validator rules (build
work in `src/classkit/validate.py`, not design). Teacher-mode content
(per-course `course.yaml`, `homework-defaults.yaml`, `item-classes.yaml`,
and homework files) — handled separately from the framework code. Item
ingest (HW-Q02) and item-format extensibility (HW-Q01). Rendering the
manifest to a student handout (never designed).



### Addendum (2026-09-22) — `/write-items homework` hand-off

`/write-items <unit> homework` no longer writes homework items itself; it hands
off to `/create-homework` with the unit pre-filled. Homework items are produced
only through the `/create-homework` pipeline, so they always carry an
`item_class` and pass through the critic/solver loops. The hand-off keeps the
old command's ergonomics working while routing all homework flow through the
single canonical pipeline.

The command adds only a minimal guard: it tells the teacher that homework uses
its own planning and review pipeline, invokes `/create-homework` with the unit,
and stops before Chen's item-writing steps. For `/write-items <unit> quiz`
and `/write-items <unit> exam`, behavior is unchanged from the framework's
command; whether critic/solver should extend to them is HW-Q04.

---

## HW-D02 — Item classes as pedagogical bundles
**Date:** 2026-09-22 · **Status:** provisional

Introduces a new axis on assessment items: `item_class`, an optional
teacher-defined string. Independent of `format`. Where `format` describes
the *answer shape* (multiple-choice, open, numeric, code), `item_class`
describes the *task envelope* — tool policy, typical time, typical Bloom
range.

**Per-course taxonomy.** Classes live in
`course/assessments/item-classes.yaml`, one file per course. Each class
carries `typical_minutes`, `default_tools`, `typical_bloom`, and a
`description` shown on the student handout when items are grouped by class.

**Class is a hint, not a lock.** Per-item fields override the class
defaults. A DIY item labeled `est_minutes: 10` is fine; the class typical
is 3, and a new warn rule `item_class_bundle_drift` flags deviations
outside the class's typical range for review.

**Pilot course's four classes (Shira's data structures course):**
- **DIY** — short, no AI, remember/understand
- **Practicing** — longer, no AI, apply/analyze
- **Research** — mini-research task, AI-assisted, longer, analyze/evaluate/create
- **Coding** — programming task, AI-assisted, longer, analyze/evaluate/create

(The earlier draft named a single `WithAI` class covering both Research
and Coding; splitting into two classes gave each its own writing skill
and clarified rubric expectations.)

**Why:** `format` and Bloom together weren't the taxonomy teachers actually
think in. "2 DIY, 2 Practicing, 1 Research, 1 Coding" is the natural handle for
describing a homework; forcing that into format-plus-Bloom loses the
tool-policy dimension entirely and requires the teacher to reason across
three axes when they think in one.

**Consequence:** Homework-planner reads `default_class_mix` in
`homework-defaults.yaml` to propose slot mixes. Assessment-writer reads the
class of a slot to inherit tool defaults and Bloom range. Class taxonomy
is per-course by design — Shira's DIY/Practicing/Research/Coding won't be a
networking course's classes, and shouldn't need to be.

**Files landed:**
- `schemas/item-classes.schema.json`
- `schemas/assessment-item.schema.json` (adds optional `item_class` field)

Teacher-mode files (per-course `item-classes.yaml`) are handled
separately, not in this framework-side bundle.

---

## HW-D03 — Tools as open course-declared strings
**Date:** 2026-09-22 · **Status:** provisional

Introduces tools as open strings (the framework has no tool list of its
own). Each course
declares its own tools in `course.yaml`'s new `tools:` map. Any tool named
in a homework, item, or item class must be declared there.

**Shape.** Each entry: `description` (one-line, shown on the student
handout), optional `availability` (universal / student_download / lab_only
/ provided_dataset), optional `url`.

**Universal tools live in every course's `tools:` map, not in the
framework.** The framework doesn't need to know what pen and paper is.
When a teacher scaffolds a course, they populate their own `course.yaml`'s
`tools:` map with the tools that course uses — pen and paper, language
reference, code editor, AI assistant, class gem, plus any subject-specific
tools. A future update to `templates/course/course.yaml` could seed
common tools as starter examples; not part of this bundle.

**Why:** A networking course adds Wireshark, a chemistry course adds
PhysioEx, a stats course adds R. Framework-side enum can't cover this and
shouldn't try. In-class activity types are already open strings gated by
methodology (D-020ish); item tools should follow the same extensibility
principle.

**Consequence:**
- `homework.allowed_tools`, `item-classes.default_tools`, and any
  downstream tool reference become open strings.
- New validator rule `homework_tools_declared` warns when a homework
  names a tool not in `course.yaml`.
- Agents interviewing teachers about a new tool must follow the
  `interviewing-teachers` skill: draft the entry from what they know
  about the tool, ask only about course-specific facts (availability,
  house-style description). Never ask a teacher what a public tool is.

**Files landed:**
- `schemas/course.schema.json` (adds `tools:` map)
- `schemas/homework.schema.json` (allowed_tools is an open string)
- `schemas/item-classes.schema.json` (default_tools is an open string)
- `.claude/skills/interviewing-teachers/SKILL.md` (governs how agents
  propose new tool entries)

Teacher-mode content (per-course `course.yaml` populated with declared
tools) is handled separately, not in this framework-side bundle.

**Deferred — tool labels.** An earlier draft gave each tool a
`display_name` label. Dropped (2026-09-28): nothing reads it, and the
handout already uses `description`. A label may return with the
student-handout rendering design, e.g. to show tool names in Hebrew while
the key stays a stable English id.

---

## HW-D04 — Interviewer as a general-purpose agent
**Date:** 2026-09-22 · **Status:** provisional

Introduces a single `interviewer` agent used by any command that needs to
collect structured input from the teacher. Replaces per-command interview
logic in `/create-homework`, `/new-hw-type`, and (over time) any future
command that would otherwise implement its own interview flow.

**Contract.** The caller passes four things: a **subject** (what is being
interviewed about, in plain language), a list of **grounding files** the
agent reads before drafting, a **shape example** (an existing entry of
the same kind that carries the structure the caller wants back), and
optional **pre-filled fields** (values from command arguments the
teacher already gave).

The interviewer returns a structured object with five top-level fields:
`status` (`complete` | `partial` | `declined`), `data` (the filled
shape), `unfilled` (fields left blank), `defaults_used` (map of
defaults applied and why), and `follow_ups` (things the teacher raised
outside the subject that need caller action — e.g. "teacher also wants
to add Wireshark to course.yaml").

**The one rule that keeps the pattern reusable:** interview, then
return. The agent never writes files, never runs validation, never
invokes other agents. Every temptation to be helpful in-line is what
turns a reusable agent into a specialized one. The caller decides
what to do with the returned data.

**Why:** The interview shape recurs across the framework — new item
class, new tool entry, new textbook citation, homework spec, material
label. Before this decision each command handled it inline or had its
own drafter agent (see the earlier `class-drafter` proposal, now
retired). That produced inconsistent behavior — agents forgetting to
load `interviewing-teachers`, follow-ups swallowed silently, defaults
applied without record. One agent with a strict contract fixes all
three.

**Why not extend it to every teacher-facing interaction?** Some
interactions are inherently multi-round and open-ended — plan review
with `homework-planner`, for instance — and don't fit the "one round,
return structured object" shape. The pattern is right for
information collection, not for iterative negotiation. `homework-planner`
does its own back-and-forth for good reason; may migrate parts to the
interviewer later if the shape fits.

**Consequence.**

- Interviewing rules stay consistent across commands — the
  `interviewing-teachers` skill is loaded once, in one place. Adding
  a new command that needs teacher input becomes a matter of composing
  existing agents rather than writing new interview flows.
- Follow-ups become first-class. A teacher's stray "and also add X"
  during an interview is captured in the return value; the calling
  command decides whether to act on it, defer, or block. Previously
  such asides either got acted on inconsistently or were lost.
- The "shape example" input carries structure implicitly rather than
  requiring a formal schema. Simpler for callers; fragile if the
  example has fields the caller doesn't want (interviewer will ask
  about them). Move to formal schemas later if this friction shows up
  in practice.

**Files landed:**
- `.claude/agents/interviewer.md`
- `.claude/commands/create-homework.md` (interview step delegated)
- `.claude/commands/new-hw-type.md` (interview + skill-drafting delegated)

**Open question raised by this decision:** the interviewer's ability
to draft new skill files (via the second invocation in `/new-hw-type`)
introduces agent-authored artifacts into a framework that has assumed
hand-authored ones. See HW-Q03.

---

---

## HW-D05 — Evaluation strategy declared per item class
**Date:** 2026-09-22 · **Status:** provisional

Introduces `evaluation.strategy` on each entry in
`course/assessments/item-classes.yaml`. This is how `item-solver`
(added in HW-D01's pipeline) decides what to do with an item: attempt
as personas, execute code, skip and defer to the teacher, or load a
custom skill.

**Four strategies:**

- `persona_attempt` — solver attempts as class-average and struggling
  personas, compares to `model_answer` and `rubric`. Default for
  classes with a checkable key (DIY, Practicing).
- `execute` — solver runs the item's `tests` via Bash. Autograded
  Coding.
- `skip` — solver returns `not_applicable`; the item surfaces at
  Gate 2 for human review. Research and similar open-ended classes
  where automated attempts would fabricate signal.
- `custom` — solver loads a class-specific skill named in
  `evaluation.custom_skill`. Advanced.

**When absent** — `item-solver` falls back to a safe heuristic:
attempt if `model_answer` and `rubric` are present, skip otherwise.
A new validator rule `item_class_evaluation_declared` warns on
absence to encourage explicit declaration without breaking older
class files.

**Interaction with `/new-hw-type`.** The command's interview asks
about strategy alongside the other class metadata. The interviewer
proposes a strategy based on the description (a "reading" task
suggests `persona_attempt`; anything AI-heavy suggests `skip`;
anything with tests suggests `execute`); the teacher confirms or
edits.

**Why:** the four built-in classes (DIY, Practicing, Coding,
Research) each had implicit evaluation behavior hardcoded in
`item-solver.md`'s class-branching table. This does not scale: when
`/new-hw-type` adds a fifth class, the solver has no way to know
what to do with it, so it falls back to a heuristic. Making
evaluation strategy an explicit per-class property lets teacher-added
classes participate in the solver pipeline the same way the built-ins
do, without patching solver code.

**Why not extend to quiz/exam items too?** The framework's current
design has no per-item critic or solver for quiz/exam items; the
teacher reviews them directly. Whether the multi-agent evaluation
pipeline should generalize beyond homework is open — see HW-Q04
(added below).

**Consequence:**

- `item-classes.schema.json` adds optional `evaluation` object with
  `strategy`, `notes`, and (optional) `custom_skill` fields.
- `item-solver.md` replaces its hardcoded class-branching table
  with a lookup: read class → read strategy → branch.
- `/new-hw-type.md` interview drafts a proposed `evaluation.strategy`
  for each new class the teacher creates.
- New validator rule `item_class_evaluation_declared` (warn).

**Files landed:**
- `schemas/item-classes.schema.json` (adds `evaluation` object)
- `.claude/agents/item-solver.md` (lookup-based branching)
- `.claude/commands/new-hw-type.md` (interview covers strategy)

**Deferred:** whether the framework's built-in four classes' pilot
`item-classes.yaml` should carry pre-filled `evaluation` blocks
(teacher-mode content, handled separately).

---

## HW-D06 — Item time estimates are class-dependent
**Date:** 2026-09-22 · **Status:** provisional

Not every item class can be reliably time-estimated. DIY and Practicing
items are closed problems with predictable duration; Coding and Research
items are unbounded — the same problem takes a proficient student 30
minutes and a struggling student 4 hours, and AI assistance adds another
dimension of variance. Making up an `est_minutes` for a Coding item is
fake precision that misleads teachers into trusting a budget check that
is theatre.

**Two changes to encode this:**

1. **`typical_minutes` on an item class becomes a range** — `{min, max}`
   instead of a bare number. Low-variance classes have tight ranges (DIY
   2-4, Practicing 10-20); high-variance classes have wide ranges (Coding
   30-90, Research 30-120).

2. **New `time_variance: low | high` field on each item class.** Determines
   whether individual items are expected to declare `est_minutes` and how
   validators/critic treat time:
   - `low` — item's `est_minutes` is expected; item-critic sanity-checks
     against the class's range; validator flags drift.
   - `high` — item's `est_minutes` is optional; item-critic does not
     enforce a specific number; homework-planner's budget check uses the
     midpoint of the class's `typical_minutes` range as a proxy.

**Where this shows up:**

- `item-classes.schema.json` — `typical_minutes` is now an object with
  `min` and `max`; `time_variance` is a new field.
- `assessment-item.schema.json` — `est_minutes` description clarifies
  when it is expected vs. optional based on class.
- `item-critic.md` — "time-budget realism" check branches on the class's
  `time_variance`; strict for low, shape-only for high.
- `homework-planner.md` — budget check sums per-item `est_minutes` where
  present and midpoint of class range otherwise; the brief notes when the
  plan is heavy on high-variance classes so the teacher knows the sum
  is approximate.
- `homework_budget_fits` and `item_class_bundle_drift` rules — updated
  to accept absent `est_minutes` on high-variance classes.

**Why not derive high-variance estimates from `time-constants.yaml`?**
Considered and rejected. Time-constants (D-025) advise session-level
sizing based on reading rates and video playback. For a Coding item,
the reasoning time is not decomposable into constants — the variance
comes from the student's fluency, not the problem's shape. Trying to
compute a "correct" time estimate imports the same fake precision the
raw number had. Better to say: this class has this rough range,
individual items don't get a fake number.

**Why not extend time-constants to reading portions of Practicing items?**
Legitimate but small. A Practicing item that includes "read section
3.2 (about 4 pages) and answer these questions" could sanity-check its
`est_minutes` against `textbook_pages_per_minute × 4 + writing time`.
This is compatible with the change here — Practicing is `time_variance:
low`, so `est_minutes` is expected, and the critic can use time-constants
as one input to the sanity check. Not required for the current design;
worth adding when a real course pushes on it.

**Interaction with existing:**

- D-025 (time-constants advisory): unchanged. Sessions still use
  time-constants; homework classes with `time_variance: low` may
  reference them as one input to critic's sanity check.
- HW-D02 (item classes as bundles): extended. Classes now carry their
  time-variance shape alongside typical_bloom, typical_minutes,
  default_tools.
- Q-005 (defensible time-constants values): still open; unrelated to
  this change.

**Files landed:**
- `schemas/item-classes.schema.json` (typical_minutes as range;
  time_variance field)
- `schemas/assessment-item.schema.json` (est_minutes description)
- `.claude/agents/item-critic.md` (branch on time_variance)
- `.claude/agents/homework-planner.md` (budget check uses range midpoint
  for high-variance classes)
- `dev/FRAMEWORK-SPEC.md` §8.4 (updated rules)

**Deferred:** Pilot course's own `item-classes.yaml` populating the
per-class `time_variance` and range values (teacher-mode content,
handled separately).

---

## HW-D07 — Evaluation strategy overridable per item
**Date:** 2026-09-24 · **Status:** provisional

Refines HW-D05. The class-level `evaluation.strategy` is the default for
items in the class, but individual items can override it via an optional
`evaluation_strategy` field on the item itself. This exists because a
class's default strategy does not always fit every item in the class —
most concretely, a Coding class defaults to `execute` (autograded via
tests), but a Coding item with `format: open` (human-graded, code
submitted inside prose) has no runnable test suite and must not be
executed.

**Two mechanisms:**

- **Explicit override** — the item declares `evaluation_strategy:
  persona_attempt` (or any of the four strategies). item-solver uses
  the item's value in preference to the class default. Teachers use
  this when they know the item needs different treatment.

- **Automatic override for Coding + open** — item-solver checks: if the
  resolved strategy is `execute` but the item's `format` is not `code`,
  fall back to `persona_attempt`. Logs the auto-override in the solver
  report so the teacher sees it. This is a safety net for items that
  didn't declare an override but need one.

**Why not split the Coding class?** Considered creating two classes
(`Coding-Autograded` and `Coding-Human`), one per strategy. Rejected
because the pedagogical envelope is the same — same typical_minutes,
same typical_bloom, same default_tools, same target of "student writes
code with AI assistance." Only the evaluation method differs. Splitting
the class over that would create two classes that behave identically to
teachers, students, and every other agent — only item-solver would
notice. Per-item override is smaller and matches where the actual
distinction lives (in the item's format).

**Why not select strategy by (class, format) tuple?** Considered making
the class declare a mapping like `{code: execute, open: persona_attempt}`.
Rejected because it front-loads combinatorial complexity into the class
declaration; most classes have one dominant strategy and don't need the
mapping. The Coding + open case is the only known pair where automatic
override is needed. Item-level override handles this case and any future
one; the auto-fallback handles it without teacher intervention when the
distinction is obvious.

**Files landed:**
- `schemas/assessment-item.schema.json` — adds optional `evaluation_strategy`
- `.claude/agents/item-solver.md` — lookup order now checks item field
  first; describes the auto-fallback for Coding + open

**Consequence:** item-solver's report should surface whether strategy
came from the item override, the class default, or the auto-fallback.
The teacher needs to know which of the three was in play, especially
when an item was auto-overridden to persona_attempt.

**Interaction:**
- HW-D05 (evaluation strategy per class): unchanged; class default is
  still the primary declaration.
- HW-D02 (item classes as bundles): unchanged; the class stays a
  pedagogical bundle, not a strategy dispatch table.
- Coding-class items with format: code continue to use `execute` as
  before. No breaking change to existing items.

---

## HW-D08 — The homework module carries out the framework's D-031g rename
**Date:** 2026-09-28 · **Status:** provisional · **Needs Chen's confirmation.**

The framework already decided (D-031g) to rename the assessment item's
`answer` field to `model_answer`: a guiding question's `answer` is a *list
of locators*, an item's `answer` was a *string*, and one key should not mean
two things. The framework's roadmap schedules the rename for **step 5
(Entry quiz)**, not yet started.

**Decision.** The homework module does not wait for step 5. It
carries out D-031g for the parts it touches, and uses `model_answer`
everywhere. This is not a new design; the name and the reason are Chen's.

**Why:** homework items are the first real users of the field (open and
numeric items both need a reference answer). Writing the module against
`answer` would force a second rename across every homework agent and
document once step 5 lands.

**Scope — framework files the module changes for this:**
- `schemas/assessment-item.schema.json` — `answer` → `model_answer`
- `templates/assessment/item-open.md` — same rename in the template

Nothing else in the framework uses the item's `answer` field (checked
2026-09-28: no Python code, test, or agent reads it).

**One refinement over D-031g.** `FRAMEWORK-SPEC.md` describes
`model_answer` as the model answer for `open`/`numeric`/`code`. The module
uses it for `open` and `numeric` only; a `code` item's reference is the
runnable `expected_solution`, which the autograder executes. Chen should
confirm this split.

**For Chen (not edited by the module):**
- `dev/ROADMAP.md`'s two ledger rows for the rename (schema, `item-open.md`)
  are ticked; step 5 no longer needs to do them.
- If step 5 work on `assessment-item.schema.json` starts before
  the homework module lands, the two changes touch the same lines — coordinate
  first.

---

## HW-D09 — Homework items get their own writer agent
**Date:** 2026-09-28 · **Status:** provisional · **Supersedes** the part of HW-D01
that extended `assessment-writer` with a homework mode.

**Decision.** Homework items are written by a new module agent,
`homework-item-writer`. The framework's `assessment-writer.md` is not
changed at all and keeps writing entry-quiz, in-class-quiz and exam items.

**Why:** the earlier version rewrote `assessment-writer.md` into a
two-mode agent. That changed Chen's quiz behavior as a side effect (it
dropped the `writing-guiding-questions` skill for every mode), and it
edited the file his roadmap step 5 plans to rewrite ("`assessment-writer`
scoped to the entry quiz"). A separate agent keeps the module independent
and removes that conflict.

**How the craft stays shared.** Framework rule: craft used by more than
one agent belongs in one place. `homework-item-writer` does not copy the
multiple-choice and rubric guidance; it reads `assessment-writer.md` and
follows its "distractors are the item" and "the rubric is the item"
sections by reference. It also loads `writing-guiding-questions`, as
Chen's writer does.

**Consequence:**
- `/create-homework`, `item-critic`, `item-solver`, `homework-planner`,
  `/new-hw-type` and the two class skills name `homework-item-writer`.
- The module now changes five framework files instead of six.
- If Chen later moves the shared craft into a skill, `homework-item-writer`
  should load that skill instead of reading `assessment-writer.md`.

---

## HW-D10 — Formats belong to the framework; the module adds only the class axis
**Date:** 2026-09-28 · **Status:** provisional

**Decision.** An item's `format` (how the student answers: multiple-choice,
numeric, open, code, …) is the framework's concept, the same for quiz,
homework and exam. The homework module *uses* formats but does not define or
constrain them. What the module adds is the **item class** (DIY, Practicing,
Coding, Research, and classes teachers add): the homework context of time,
tools, AI policy and Bloom range.

**Why:** the earlier schema added format rules (true-false → `choices`;
numeric and open → `model_answer`; code → `expected_solution`, `tests`,
`rubric`). Those rules applied to every item, so Chen's quiz and exam items
would have changed behavior. That contradicted section 3.3's own claim that
the module only adds optional fields.

**Consequence:**
- `assessment-item.schema.json` is Chen's file plus optional fields and the
  D-031g rename (HW-D08). Its `allOf` rules are exactly Chen's.
- Homework requirements are enforced by the module's validator rules, which
  only apply to homework items: `code_execution_reference_present`,
  `graded_requires_rubric`, `homework_item_usage`.
- `homework-item-writer` asks for a reference answer per format, as writing
  guidance rather than as a schema rule.
- `item-code.md` stays, reframed as the **Coding-class** template (it sets
  `item_class: Coding` and carries the Coding fields; `est_minutes` removed
  per HW-D06).
- The numeric, multiple-select and true-false templates are plain framework
  format templates. They live at their final paths under
  `templates/assessment/` so review can approve or remove each one directly;
  their presence does not make those formats homework-owned.

---

## HW-D11 — Module-local numbering for decisions and open questions
**Date:** 2026-09-28 · **Status:** provisional

**Decision.** The module's decisions are numbered `HW-D01`, `HW-D02`, … and
its open questions `HW-Q01`, `HW-Q02`, …. Plain `D-` and `Q-` numbers always
refer to the framework's own devlog (for example D-031g, Q-002, Q-026).

**Why:** the module first continued the framework's sequence (D-035…D-044,
Q-032…Q-036). The framework's next decision on `main` would also have been
D-035, so once both were in the framework, two different decisions would have shared a number.
A prefix removes the collision without asking Chen to reserve numbers, and
shows at a glance which entries belong to the homework module.

**Consequence:** every module file was renumbered in one pass. The mapping
from old to new numbers is in `_devlog/README.md`. New module decisions
continue from HW-D12; new open questions from HW-Q06.

---

## HW-D12 — All homework writes go through `classkit write`
**Date:** 2026-09-28 · **Status:** provisional

**Decision.** Every file the homework pipeline writes goes through
`classkit write`, never a raw file write. New files are written plainly. A
change to an existing file uses `--overwrite`, and only after the teacher
approved that exact change at a gate:

| Change to an existing file | Approved at |
|---|---|
| reuse — append `homework` to an item's `usage` | Gate 1 (the plan) |
| promote drafts — remove `status: draft` | Gate 2 |
| update `homework-defaults.yaml` | Gate 2 |
| rewrite the plan file | Gate 1 revision request |
| `/new-hw-type` appends to `item-classes.yaml`, `homework-defaults.yaml` | its change-set approval |
| revise a draft this run created, after critic/solver feedback | the pipeline's own draft |

If `classkit write` refuses an overwrite that was not approved, the agent
stops and shows the teacher; it never retries with `--overwrite` on its own.

**Why:** framework invariant 5 (D-030, D-031b) — "nothing overwrites a
teacher's work without permission — enforced in code, not by prompt". The
homework pipeline is the part of the framework that edits the most existing
files, so it follows the rule explicitly. Each overwrite is tied to a gate the
teacher already passes, so it adds no extra questions.

**Consequence:** `create-homework.md`, `homework-item-writer.md`,
`homework-planner.md` and `new-hw-type.md` state the rule where they write.

---

## HW-D13 — Homework is optional: config on first use, rules silent without it
**Date:** 2026-09-28 · **Status:** provisional

**Decision.** A course may never use homework, and nothing in the framework
may complain about that.

- `classkit scaffold course` does **not** create `homework-defaults.yaml`,
  `item-classes.yaml` or `homework/.plans/`. The first `/create-homework`
  (or `/new-hw-type`) run creates them from their templates.
- 20 of the 21 validator rules are **consistency** rules (D-033): they judge
  only homework files and item classes that exist, and are silent when there
  are none.
- `assessment_scheme_complete` is the one **completeness** rule. It runs only
  when the course is complete **and** the syllabus declares homework.
- "error on graded" is not a severity: the two `graded_*` rules are errors
  that apply only when `purpose: graded`.

**Why:** a scaffolded course has no tools declared (HW-D03). If scaffolding
created `item-classes.yaml`, `class_tools_declared` would warn on every new
course, including ones that will never have homework — the "rule teachers
switch off" that D-033 warns about.

**Consequence:** spec §7.2 gains a *State* column; handoff tasks 3–5 are
updated; `/create-homework` and `/new-hw-type` create the config files when
missing.

---

## HW-D14 — Numeric answer units are `measurement_units`
**Date:** 2026-09-28 · **Status:** provisional

**Decision.** The optional item field for the units of a numeric answer
(ms, bytes, …) is named `measurement_units`, not `units`.

**Why:** on a homework manifest, `units` means the course units it covers,
and every item already has `unit` (e.g. `U03`). A numeric item carrying both
`unit: U03` and `units: "ms"` would use one word for two unrelated things —
the problem the framework's D-031g fixed for `answer`. `metric` was
considered and rejected: the framework has a *Metrics* phase, and in CS
courses "metric" usually means what is measured (accuracy, F1), not its unit.

**Consequence:** renamed in `assessment-item.schema.json`, spec §3.3,
`homework-item-writer.md`, and the numeric template at
`templates/assessment/item-numeric.md`.
Nothing used the old name yet.

---

## HW-D15 — `/create-homework` matches the spec: 13 steps, two explicit gates
**Date:** 2026-09-28 · **Status:** provisional

**Decision.**
- The command and spec §4.1 use the same 13 step numbers.
- **Gate 1** (step 5) has four outcomes: approve, revise (the planner
  re-plans), show the slot table (the teacher edits slots by number), and
  reject (stop). Before Gate 1 only the planner's internal plan file exists:
  no items, manifest or reuse edits are written.
- **Gate 2** (step 11) keeps its three outcomes: approve, revise named items,
  reject.
- Between the gates the pipeline runs continuously and announces each step;
  writer, critic and solver rounds need no separate approval.

**Why:** the command numbered its steps 1–10 while the spec listed 13, and
Gate 1 was a single sentence with no revise, table or reject path — so the
agent that actually runs did not know what to do when a teacher said
"revise". The framework's root `CLAUDE.md` asks commands to be "stepwise,
with your approval"; the two gates are where the teacher decides, and the
continuous run between them is the module's deliberate reading of that rule.

**Consequence:** `create-homework.md` rewritten to steps 1–13 with a Gate 1
step; spec §4.1 states the gate outcomes and the continuous-run rule.

---

## HW-D16 — `homework-defaults.yaml` gets a schema and a consistency rule
**Date:** 2026-09-28 · **Status:** provisional

**Decision.** Add `schemas/homework-defaults.schema.json` (keys and allowed
values, `additionalProperties: false`) and a 21st rule,
`homework_defaults_consistent` (warn, consistency): `default_class_mix` sums
to 1.0 within ±0.01, and every class in it exists in `item-classes.yaml`.
Both apply only when the file exists (HW-D13).

**Why:** the manifest and the class list had schemas; the defaults file,
which the planner reads on every `/create-homework`, had none. A typo
(`colaboration`), a bad value (`answer_release: sometimes`), a mix that does
not sum to 1, or a class that does not exist would silently skew every
homework. The schema catches the first two; the rule catches the cross-file
ones a schema cannot.

**Consequence:** spec §3.5, §7.1, §7.2 (21 rules) and §11 updated; handoff
tasks 2 and 3 name the loader, `SCHEMA_FOR` entry and the tolerance.

---

## HW-D17 — `/review-homework` removed
**Date:** 2026-09-29 · **Status:** provisional

**Decision.** The module has no `/review-homework` command. Homework is
checked inside `/create-homework`: the planner against the teacher's
expectations (Gate 1), `item-critic` and `item-solver` on every item, the
validator, and the teacher at Gate 2.

**Why:** the command was not part of the intended flow (interview → create →
check → teacher approval → output). It also did its review by borrowing the
framework's `course-critic`, an agent written for units, which the framework's
roadmap step 7 plans to change — a hidden dependency like the one HW-D09
removed.

**Consequence:** the command file is deleted; the spec, roadmap, root
`CLAUDE.md`, `GETTING-STARTED.md` and `dev/CLAUDE.md` no longer mention it.
Its unique use — re-reviewing a finished or old homework as a whole (item
order, redundancy, overlap with earlier homework) — is kept as HW-Q07.

---

## HW-D18 — Tool-dependent items are skipped; skipped items get a teacher aid
**Date:** 2026-09-29 · **Status:** provisional

**Decision.**
- An item whose answer needs a tool or data the pipeline cannot run
  (Wireshark, lab-only software, a teacher-provided dataset) is not
  attempted. `homework-item-writer` sets `evaluation_strategy: skip` on it
  (reusing HW-D07); `item-solver` also refuses to attempt one it meets under
  `persona_attempt`. Tool output is never invented.
- Every skipped item — Research or tool-dependent — gets a **teacher aid**
  from `item-solver`, returned in its report and shown at Gate 2. It is not
  saved yet — storing confidential teacher material is HW-Q06: for Research, up to 3–5 references and a short summary of what a
  strong answer covers; for tool-dependent items, the expected approach and
  "check by hand".
- References come from the course's own materials first (`materials/source/`,
  `textbooks`, Guiding Question `answer` locators). An outside reference
  must be verifiable, or it is marked "unverified — check before use". No
  invented URLs, pages or DOIs (framework rule).

**Why:** the solver chose its check by class only, so a Practicing item
needing Wireshark would have been "answered" with invented tool output —
the fake signal HW-D05 forbids for Research. And a plain skip left the
teacher with nothing for exactly the items they must grade by hand.

**Consequence:** instruction changes only, no schema changes:
`item-solver.md`, `homework-item-writer.md`, `create-homework.md` (Gate 2),
`writing-research-items`, and spec §4.3 and §5.1. `item-solver` has no web
tools, so outside references it proposes will usually be marked unverified.

---

## HW-D19 — `item-critic` checks material fit
**Date:** 2026-09-29 · **Status:** provisional

**Decision.** `item-critic` checks that what an item needs is in the
material students were actually assigned.

- Evidence, in order: the `answer` locators of the Guiding Questions the item
  tests; otherwise the session's study paths and the resources they
  reference. A file merely existing in `materials/source/` is not evidence —
  only what was assigned counts.
- Missing concept → `should-fix`, naming the concept and the session.
- No evidence to check against → "couldn't verify material fit", listed at
  Gate 2. Never a guess.
- `homework-item-writer` revises the **item** to fit the material; it never
  changes learning materials. If the material should change, that is the
  teacher's decision at Gate 2.
- Research items are exempt from the material containing their answer; the
  critic checks only that students got enough course context to begin.

**Why:** the critic checked that an item tests its Guiding Question, but not
that students studied what the item requires. An item could match its
Guiding Question and still need something no assigned material covers.

**Consequence:** `item-critic.md`, `homework-item-writer.md`,
`create-homework.md` (Gate 2), spec §4.1 step 7 and §5.1. Answer locators
are the framework's D-019, not built yet, so early courses will rely on study
paths — and often on "couldn't verify".

---

## HW-D20 — Homework document export is in the module's scope
**Date:** 2026-09-29 · **Status:** provisional · **Scope only.**

**Decision.** The module designs its own output: a **student homework
document** (Word) and a **separate, editable teacher answers document**.
Homework rendering is homework-specific (student vs teacher versions,
`answer_release`), so it belongs here rather than in the framework's generic
Exports phase.

Boundaries:
- The item files and the homework manifest remain the **canonical source**;
  the Word documents are **generated artifacts**.
- Rendering happens only **after Gate 2 approval**.
- The student document must enforce `answer_release` and confidentiality.
- Where the teacher document is stored cannot be final until HW-Q06 is
  resolved.

**This decision sets scope only.** Still to decide, separately: code versus
agent generation; the contents and paths of each document; whether edits to
the documents flow back into the items.

**Why:** a Word homework and a separate answers file are the deliverables the
teacher's workflow ends with. Without them the teacher receives framework
source files, not usable documents.

---

## HW-D21 — One shared item bank
**Date:** 2026-09-29 · **Status:** provisional

**Decision.** The question bank for quizzes, homework and exams is the
framework's existing item bank. Homework is a *usage* of an Assessment Item,
not a separate kind of item.

- `course/assessments/items/` remains the single canonical item bank.
- Homework manifests reference bank items; they never embed copies.
- Fresh and adapted homework items enter the shared bank. Adaptation creates
  a new item with `source_ref`; the original is never modified.
- No hand-maintained map is added. Links already exist (item → Guiding
  Questions → session → unit → objectives → Course Outcomes); any overview is
  **generated** by `classkit` from the items, the manifests and those links.
- Usage history is derived from homework, quiz and exam manifests (and course
  offering metadata), not stored as a growing list inside each item. Only
  provenance that cannot be derived — uploaded vs generated, the original
  source — may justify new item fields.
- Importing past quizzes, homework and exams remains HW-Q02 (and framework
  Q-028); mapping an imported item to current Guiding Questions needs the
  teacher's confirmation. Importing confidential assessments stays blocked by
  framework Q-002 and HW-Q06.
- Changes to identifiers or shared item metadata are proposed to the framework
  (Chen), not introduced by the homework module (HW-Q08).

**Why:** a separate homework bank would duplicate storage, stop items being
reused across quiz, homework and exam, and undo HW-D01. Word files are an
output (HW-D20), not the storage: they cannot be validated, diffed, or
reliably read and written by agents.

**Still to decide, separately:** ingestion (HW-Q02), identifier capacity and
provenance (HW-Q08).

---

## HW-D22 — The item-bank overview is generated on demand
**Date:** 2026-09-29 · **Status:** provisional

**Decision.** `classkit bank` generates the shared-bank overview when a
teacher or agent asks for it. It prints a human-readable report by default;
`--format json` provides a stable contract for agents. `--output <file>` saves
the selected representation only when explicitly requested. No overview file
is maintained in the repository by default.

The report is derived from items, their Guiding Question links, and the
manifests that actually exist. It shows:

- Per unit and Guiding Question: counts by format, item class, declared
  `usage`, and Bloom level.
- Coverage gaps: no items, or no homework-eligible items.
- Declared use separately from actual use. A `usage` value means eligible;
  only a manifest reference proves assignment. Missing quiz or exam manifests
  produce unavailable data, not an inference.
- Which available manifests reference each item, plus items never referenced.
- Draft items separately, so abandoned runs do not inflate shipped counts.

`homework-planner` runs `classkit bank --format json` before planning to find
gaps and reuse candidates. Until H5 implements the command, it scans the same
files directly rather than blocking homework creation.

**Why:** an on-demand report cannot drift when items are edited by hand and
does not add noisy generated diffs. Human and machine outputs serve teachers
and agents without making presentation text an integration contract.

---

## HW-D23 — An agent creates the Word documents; both stay editable
**Date:** 2026-09-29 · **Status:** provisional

**Decision.**
- `/create-homework` gains step 12, after Gate 2 approval: an agent creates a
  **student document** (Word, no answers) and a separate **teacher answers
  document** (Word) from the approved manifest and item files.
- **Leak check:** the agent confirms that none of the items' answer fields
  (`model_answer`, choices marked `correct`, `expected_solution`, `tests`,
  `rubric`) appear in the student document; anything suspicious is shown to
  the teacher. The check is repeated after every edit to the student document.
- **Both documents stay editable** by the teacher and the agent. An agent edit
  changes the item file in the bank first (through `classkit write`), then
  both documents. A manual teacher edit reaches the bank only when the teacher
  asks for a sync; each change is confirmed with the teacher.
- The item files and the manifest remain the canonical source (HW-D20).
- Where the documents are saved is not decided (HW-Q06); until then the agent
  asks the teacher.

**Why:** the teacher wants the agent to produce the final Word files once
everything is approved, and both teacher and agent to keep working on them.
An agent-written student document has no structural guarantee against
leaking answers, so the leak check replaces the guarantee code would give.

**Consequence:** `create-homework.md` (new step 12; defaults become step 13,
the report step 14), spec §4.1 (fourteen steps), `GETTING-STARTED.md` §6.

---

## HW-D24 — The Word documents go where the teacher chooses, never into git
**Date:** 2026-09-29 · **Status:** provisional

**Decision.** The homework is kept in the bank — the manifest and the item
files. The two Word documents (HW-D23) are outputs, so they have no fixed
location: the agent asks the teacher where to save them. They are never
committed. Any folder outside the repository is acceptable. Inside the
repository, the teacher must choose a dedicated generated-output directory
that contains no tracked files — never the repository root or a broad existing
directory such as `course/`, `assessments/`, `materials/`, or `units/`.

The agent checks the repository-relative destination with both `git ls-files`
and `git check-ignore`. If anything at the destination is tracked, it stops and
asks for another location: an ignore rule cannot untrack a file. If the
dedicated directory is untracked but not ignored, the agent adds only its exact
anchored directory pattern to `.git/info/exclude`, verifies the result with
`git check-ignore`, and tells the teacher. It never changes `.gitignore`, runs
`git rm`, or excludes a broader parent directory. For later edits the agent
asks where the files are.

**Why:** everything needed to rebuild or reuse the homework is already in the
bank, so the documents need no canonical place. Keeping them out of git keeps
the confidential answers file out of the repository's permanent history, and
avoids binary files in version control. The dedicated-directory and tracked-
file checks prevent a convenient local exclusion from hiding unrelated course
work. Using `.git/info/exclude` rather than `.gitignore` changes no framework
file.

**Consequence:** `create-homework.md` step 12 and spec §4.1. This settles
where the *Word documents* live; HW-Q06 still covers whether answers may be
kept in the item files in the repository at all.

---

## HW-D25 — `answer_release` dropped
**Date:** 2026-09-29 · **Status:** provisional · **Supersedes** the
`answer_release` parts of HW-D01, HW-D20 and the defaults (HW-D16).

**Decision.** Homework has no `answer_release` field. The pipeline always
gives the answers to the **teacher** (the teacher answers document, HW-D23);
whether and when **students** see solutions is the teacher's decision, made
outside the pipeline (for example by publishing solutions on Moodle).

**Why:** the field only described when students would see answers, but
nothing in the design produced a student solution sheet — the teacher answers
document holds rubrics and teacher aids and is not meant for students. Its
only effect was one validator rule. The student document's protection is the
leak check (HW-D23), which applies whatever the teacher later publishes.

**Consequence:** removed from `homework.schema.json` (with its "graded
requires `answer_release`" condition), `homework-defaults.schema.json`, both
templates, `create-homework.md` and the spec. The rule
`graded_answer_release_safe` is removed: **20 validator rules** remain
(19 consistency, 1 completeness).

## HW-D26 — Versions are targeted at Guiding Questions from a quiz report
**Date:** 2026-09-29 · **Status:** provisional · **Replaces** the "grouped
variants" meaning of `versions` in HW-D01 and the rule `homework_versions_fair`.

**Decision.** `versions` means **targeted versions**. After a quiz, the
teacher may give different groups of students different follow-up work, each
aimed at the Guiding Questions that group struggled with. Every student gets
the shared top-level `items` plus the `items` of their version.

- Each version has a unique `label`, at least one `target` (Guiding Question
  id) and at least one item.
- Targets are valid Guiding Question ids from the homework's declared `units`.
- A homework with versions has `source.kind: quiz_report`, and its `ref` must
  resolve.
- Each version item tests at least one of its version's targets and no other
  Guiding Question; practice everyone needs goes in the shared items.
- Every target is covered by at least one of the version's items.
- An item appears at most once in a version and is not also a shared item;
  the same item may serve several versions.
- Documents: one student document per version (shared plus version items);
  one teacher document with every version clearly labeled (HW-D23).
- Gate 1 shows every version's targets, item coverage and approximate
  workload. On graded homework, differing versions need the teacher's explicit
  approval.

**Privacy.** The quiz report holds aggregated Guiding Question results only.
Student names, identifiers, grades and assignments to versions never enter the
repository. Labels never identify students. If a report contains student data,
the pipeline stops and asks for an aggregated version.

**Why:** the old model assumed parallel variants of equal content (for example
against copying), and its rule warned when versions covered different Guiding
Questions. The teacher's real use is the opposite: versions differ on purpose,
driven by the quiz report.

**Consequence:** `homework.schema.json` version objects gain required
`targets`, unique items and a "versions require a `quiz_report` source with
`ref`" condition; the template, `create-homework.md`, `homework-planner.md`
and the spec are updated. `homework_versions_fair` (warn) is replaced by
`homework_versions_targeted` (error); the count stays at **20 validator rules**
(19 consistency, 1 completeness).

## HW-D27 — Item counts per class replace the class mix
**Date:** 2026-09-29 · **Status:** provisional · **Amends** HW-D02 (how the
planner reads the typical shape) and HW-D16 (what the defaults rule checks).

**Decision.** The teacher states a homework as a count per item class ("one
DIY, one Coding"). `homework-defaults.yaml` stores `default_class_counts`
(whole numbers, class name → count) instead of `default_class_mix`
(fractions). The number of items is the sum of the counts; there is no
separate item-total setting.

- For targeted versions (HW-D26) the interviewer asks counts for the shared
  items and for each version separately; Gate 1 shows the workload per student
  for each version.
- Defaults describe an ordinary homework. Version labels and per-version
  counts are never stored in the defaults, and a targeted homework does not
  update `default_class_counts` at step 13.
- A class added with `/new-hw-type` starts at 0.

**Rule change.** `homework_defaults_consistent` (warn) now checks: every count
is a non-negative integer (also enforced by the schema); at least one count is
positive; every named class exists in `item-classes.yaml`; the estimated work
(count × class `typical_minutes` midpoint) is within `budget_tolerance_minutes`
of `total_minutes`. Still **20 validator rules**.

**Why:** counts match how teachers describe homework, avoid rounding, and
cannot disagree with a separate item total.

**Consequence:** `homework-defaults.schema.json`, the defaults template
(DIY 2, Practicing 2, Coding 1, Research 0 — about 96 minutes against 90 ± 15),
`create-homework.md`, `new-hw-type.md`, `homework-planner.md`, the spec and
`GETTING-STARTED.md`.

## HW-D28 — Per-item tools live in the manifest
**Date:** 2026-09-29 · **Status:** provisional · **Extends** HW-D03.

**Decision.** A homework manifest may carry `item_tools`: a map from item id
to the tools that item needs, for example `U03-I05: [wireshark, gns3]` or
`U03-I07: [python]`. Several tools per item are allowed, and a programming
language counts as a tool. Every tool must be declared in `course.yaml`'s
`tools` map. `allowed_tools` stays as the policy for the whole homework.

**Not on the item.** Chen's `assessment-item.schema.json` gets no tools
field. The tools are needed only while creating the homework — the planner
puts them on each slot, the writer writes for them, the solver uses them to
decide whether it can attempt the item (HW-D18) — and in the student
document. Nothing else reads them. The cost: when an item is reused, the new
homework states its tools again.

**Rules.** No new rule; still **20**. `homework_tools_declared` also checks
`item_tools`; `homework_item_reference` also checks that every `item_tools`
key is an item of this homework (shared or in a version).

**Consequence:** `homework.schema.json`, the manifest template,
`create-homework.md`, `homework-planner.md`, `homework-item-writer.md`,
`item-solver.md` and the spec.

## HW-D29 — `prerequisites` dropped
**Date:** 2026-09-29 · **Status:** provisional · **Amends** HW-D01.

**Decision.** The homework manifest has no `prerequisites` field, and the rule
`homework_prerequisites_precede` is removed.

**Why:** nothing in the pipeline used it. The planner never read it, and the
units a homework declares already say what it builds on. The module keeps only
what creating the homework needs (see HW-D28).

**Consequence:** removed from `homework.schema.json`, the manifest template and
the spec. **19 validator rules** remain (18 consistency, 1 completeness).

## HW-D30 — The Word documents are laid out from `homework-document.yaml`
**Date:** 2026-09-29 · **Status:** provisional · **Extends** HW-D23.

**Decision.** A course file, `course/assessments/homework-document.yaml`, says
how the homework Word documents look. At step 12 the agent fills the student
document and the teacher answers document from it plus the approved manifest
and items. Fields: `course_title`, `instructor`, `semester`, `title_format`
(placeholders `{course_title}`, `{semester}`, `{number}`, `{id}`, `{units}`;
`{number}` is the homework number from the id), `due_date_format`,
`submission_instructions`, `header`, `footer`, `logo`, `language`,
`direction`, `font`, `font_size`, `show_est_minutes`.

- The manifest gains an optional `due_date`. The interview collects it before
  planning, Gate 1 approves it, and step 9 writes it with the manifest. Step 12
  does not introduce or overwrite manifest metadata (clarified by HW-D31).
- If `semester` looks out of date, the agent asks before Gate 1 and records the
  confirmed value in the plan before using it.
- Created from its template on the first `/create-homework` (HW-D13);
  validated by its own schema; holds no answers, so it is committed.

**Why not a Word template:** a `.docx` template is binary, cannot be validated
like the framework's other templates, and its placeholders break easily when
edited. The teacher chooses among fields instead of designing the page in
Word; for a homework handout that is enough.

**Not included:** points per item — items have no points field.

**Consequence:** new `schemas/homework-document.schema.json` and
`templates/course/homework-document.yaml`; `due_date` in
`homework.schema.json` and the manifest template; `create-homework.md` steps 1
and 12; the spec; `GETTING-STARTED.md`. No new validator rule; still **19**.

---

## HW-D31 — Focus notes are plan-only; due date is approved before writing
**Date:** 2026-09-29 · **Status:** provisional · **Clarifies** HW-D30.

**Decision.** The homework interview may return optional `focus_notes`: free
text such as "focus on hashing" or "avoid chaining." The planner uses these
notes to shape coverage, displays them at Gate 1, and stores them only in
`course/assessments/homework/.plans/HW0N.md`. They never enter the manifest or
the generated student and teacher documents. Personal student data is not
allowed in them.

The interview also collects the optional `due_date` before planning. The plan
and Gate-1 brief show it, and step 9 writes the approved value with the
manifest. Document generation at step 12 consumes the approved manifest and
does not add or overwrite its metadata. A possibly stale `semester` is
confirmed before Gate 1 and retained in the plan.

**Why:** creation guidance needs a stable hand-off from the interview to the
planner, while publication metadata must pass a teacher gate before it is
written. Adding metadata after Gate 2 would conflict with HW-D12's overwrite
discipline.

**Consequence:** `create-homework.md`, `homework-planner.md`, and spec §4.1.
No schema or validator change.
