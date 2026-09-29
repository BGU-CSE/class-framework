# Homework module specification

What the Homework module must contain, and the exact fields, rules, agents,
and identifiers an implementation must produce. This is the source from which
the module is built.

**Why the module exists and what it is for is in [`README.md`](README.md).**
This document assumes that and specifies the *what*. It is written to be
**self-contained**: an agent with no memory of the design conversations
should be able to implement or verify the module from this file alone.
Rationale is stated in a sentence or two and tagged `HW-Dnn` — those tags
are breadcrumbs into `_devlog/01-decisions.md`, which holds the history.
They are traceability, not required reading.

---

## 1. Scope of this specification

### 1.1 What Homework is

Homework is a **first-class manifest-level content type** in the class-framework
(HW-D01), symmetric with unit, session, and item. It has its own schema, its own
on-disk location, and its own metadata. A homework manifest references items
from the shared item bank; it does not copy them.

### 1.2 What this module covers

- The homework manifest schema and on-disk location
- The item-class taxonomy (a new axis on items)
- The `/create-homework` pipeline (planning, writing, review, gates)
- One complementary command (`/new-hw-type`)
- One command hand-off (`/write-items homework` → `/create-homework`)
- 19 validator rules
- Templates for the new content types and files

### 1.3 What this module does NOT cover

- Programming assignments as a separate content type — they are homework
  items with `item_class: Coding` (HW-D01, Q-026)
- Exam confidentiality — remains open in the base framework (Q-002)
- The Python runtime that loads, scaffolds, and validates the above — that
  is build work in `src/classkit/`, planned and tracked in `ROADMAP.md`
  (implementation notes in `_devlog/04-handoff.md`)

### 1.4 Relationship to the base framework

The module extends the framework in specific, minimal ways. See section 2.4
for the delta.

---

## 2. Module architecture

### 2.1 The three axes of an item

Every item file carries three orthogonal axes:

| Axis | What it answers | Values | Extensible? |
|---|---|---|---|
| `format` | What shape is the student's answer? | `multiple-choice`, `multiple-select`, `true-false`, `open`, `numeric`, `code` (framework's original enum) | HW-Q01 (proposed) |
| `usage` | Where may this item be used? | `in-class-quiz`, `homework`, `exam`, `self-check`, `gem-practice` | No (fixed enum) |
| `item_class` | What pedagogical envelope? | Teacher-defined per course | Yes — via `/new-hw-type` (HW-D02) |

These axes are independent. A `format: open, item_class: Practicing, usage:
[homework]` item is legal. So is `format: multiple-choice, item_class: DIY,
usage: [in-class-quiz, homework]`. Reuse across contexts is by having
multiple values in the `usage` array — not by duplicating the file.

### 2.2 Content model

```
course/
├── course.yaml                          # Framework file, adds tools: map (HW-D03)
├── assessments/
│   ├── items/*.md                       # Framework's item bank, shared
│   ├── item-classes.yaml                # NEW — class taxonomy (HW-D02)
│   ├── homework-defaults.yaml           # NEW — learned defaults for pipeline
│   ├── homework-document.yaml           # NEW — how the Word documents look (HW-D30)
│   └── homework/
│       ├── HW01.md                      # NEW — homework manifests (HW-D01)
│       ├── HW02.md
│       ├── ...
│       └── .plans/                      # NEW — internal plan files (HW-D01 fix)
│           ├── HW01.md                  # NOT part of HW*.md manifest glob
│           └── ...
```

### 2.3 Component overview

- **5 agents:** `interviewer` (HW-D04), `homework-planner` (HW-D01),
  `homework-item-writer` (HW-D09), `item-critic` (HW-D01),
  `item-solver` (HW-D01, HW-D05, HW-D07)
- **3 commands:** `/create-homework` (main pipeline), `/new-hw-type` (add
  class), `/write-items` (extended with hand-off, HW-D01 addendum)
- **3 skills:** `interviewing-teachers`, `writing-code-items`,
  `writing-research-items`
- **4 new schemas:** `homework.schema.json`, `item-classes.schema.json`,
  `homework-defaults.schema.json`, `homework-document.schema.json`
- **1 modified schema:** `assessment-item.schema.json` (additive fields only)
- **1 modified schema:** `course.schema.json` (adds `tools:` map)
- **10 templates:** 7 assessment templates (2 of them framework files with small
  changes) + 3 course-level templates

### 2.4 Delta with the base framework

**Additive** (module adds these; framework does not need to change):
- All 5 agents (`interviewer`, `homework-planner`, `homework-item-writer`,
  `item-critic`, `item-solver`). `homework-item-writer` follows the craft
  sections of the framework's `assessment-writer.md` by reference, without
  changing it (HW-D09).
- All 3 commands (existing `/write-items` is extended, not replaced in
  behavior for quiz/exam)
- All 3 skills
- All four new schemas
- The Coding-class item template (`item-code.md`) and three framework-format
  templates (`item-numeric.md`, `item-multiple-select.md`,
  `item-true-false.md`). The latter live at their final framework paths for
  review; accepting or removing them is a framework decision (HW-D10).
- The three new course templates (`homework-defaults.yaml`, `item-classes.yaml`,
  `homework-document.yaml`)
- Both new item templates (`homework.md` manifest)

**Replaces** (module supersedes existing framework files):
- `.claude/commands/write-items.md` — adds hand-off for `$2 == homework`
- `schemas/assessment-item.schema.json` — adds optional fields (below)
- `schemas/course.schema.json` — adds `tools:` map
- `templates/assessment/item-open.md` — renames `answer` → `model_answer`
- `templates/assessment/item-multiple-choice.md` — adds a comment on `item_class`
  for homework items

**Rationale for shared assessment-item schema (not extended):** the
framework's item bank is meant for cross-context reuse (HW-D01). A separate
homework-item schema would either fragment items across two files or force
per-item schema declarations. Optional field additions to the shared schema
preserve the reuse property while adding what homework needs. See HW-D01 and
section 8.1 below.

---

## 3. Content model — normative

### 3.1 The homework manifest

A homework manifest is a Markdown file with YAML front matter at
`course/assessments/homework/HW{NN}.md`. It validates against
`schemas/homework.schema.json`.

**Required fields:**

| Field | Type | Notes |
|---|---|---|
| `id` | string | matches `^HW\d{2}$` |
| `units` | array<string> | unit ids the homework covers; `uniqueItems: true` |
| `purpose` | enum | `practice` \| `graded` \| `diagnostic` |
| `total_minutes` | number | time budget for the whole homework |
| `items` | array<string> | item ids to include; `uniqueItems: true` |

**Conditionally required:**
- Every item id in `items` must match `^U\d{2}-I\d{2}$` and resolve to a
  real file under `course/assessments/items/`

**Optional fields:**

| Field | Type | Notes |
|---|---|---|
| `source` | object | `{kind: material \| quiz_report, ref?: string}` |
| `due_date` | date | YYYY-MM-DD; printed on the student document (HW-D30) |
| `allowed_tools` | array<string> | tools declared in `course.yaml`; policy for the whole homework |
| `item_tools` | map item id → array<string> | tools a specific item needs (HW-D28); several allowed; a programming language counts |
| `collaboration` | enum | `forbidden` \| `discussion_only` \| `allowed` |
| `open_book` | boolean | |
| `versions` | array<object> | targeted versions (HW-D26); requires `source.kind: quiz_report` with `ref` |
| `status` | enum | `draft` \| `shipped` (HW-D01 addendum, HW-Q03) |

**Version objects** (when `versions` is set; HW-D26):
- `label`: string, unique within the homework; never a student name or identifier
- `targets`: array<string>, ≥1 Guiding Question id from the declared `units` —
  what this version remediates
- `items`: array<string>, ≥1 version-specific item id; each tests at least one
  of the version's targets and no other Guiding Question; once per version,
  never also in the shared `items`; reuse across versions is allowed
- The manifest's top-level `items` array holds the shared items; every student
  gets the shared items plus their version's items
- The source quiz report holds aggregated Guiding Question results only. Student
  names, identifiers, grades and assignments to versions never enter the repository

### 3.2 The item-classes taxonomy

At `course/assessments/item-classes.yaml`. A single YAML object where each
key is a class name and each value describes the class. Validates against
`schemas/item-classes.schema.json`.

**Required per class:**

| Field | Type | Notes |
|---|---|---|
| `typical_minutes` | object | `{min: number, max: number}` (HW-D06) |
| `typical_bloom` | array<enum> | subset of Bloom's taxonomy levels |
| `default_tools` | array<string> | tool ids from `course.yaml` |
| `description` | string | one paragraph for future-teacher-you |

**Optional per class:**

| Field | Type | Notes |
|---|---|---|
| `time_variance` | enum | `low` \| `high` (HW-D06) |
| `evaluation` | object | how `item-solver` treats items of this class |

**Evaluation object:**
- `strategy`: `persona_attempt` \| `execute` \| `skip` \| `custom` (HW-D05)
- `notes`: string, one line explaining the choice
- `custom_skill`: string, required when strategy is `custom`

### 3.3 Extensions to the assessment-item schema

The module ADDS these optional fields to the framework's item schema. It adds
**no** format rules: the framework's own rules (`choices` for multiple-choice and
multiple-select, `rubric` for `open`) are unchanged, so quiz and exam items
behave exactly as before. What homework requires is enforced by the module's
validator rules, which apply only to homework items (HW-D10).

| Field | Type | Purpose | Required when |
|---|---|---|---|
| `item_class` | string | Third axis; class from `item-classes.yaml` | Advisory; validator warns if absent (HW-D02) |
| `tolerance` | number | For `format: numeric` items | Optional |
| `tolerance_pct` | number | Percent tolerance for numeric items; use this or `tolerance` | Optional |
| `measurement_units` | string | Measurement units for numeric items (not `units`, which means course units; HW-D14) | Optional |
| `starter_code` | string | Skeleton for code items | Optional |
| `source_ref` | string | Original item id for an adapted item | On adapted items |
| `expected_solution` | string | Runnable reference for `format: code` | When strategy resolves to `execute` (rule `code_execution_reference_present`) |
| `tests` | array | Autograder tests for `format: code` | When strategy resolves to `execute` (rule `code_execution_reference_present`) |
| `evaluation_strategy` | enum | Per-item override of class strategy | Optional (HW-D07) |
| `status` | enum | `draft` \| `shipped` lifecycle marker | Optional (HW-D01 addendum) |

The module also RENAMES `answer` → `model_answer` on the framework's item
schema — carrying out the framework's own D-031g ahead of its roadmap step 5
(HW-D08) — to disambiguate from the guiding-question's own `answer`
field (a list of locators).

**Format enum is unchanged** — six values from the framework's original
schema (`multiple-choice`, `multiple-select`, `true-false`, `open`,
`numeric`, `code`). Homework does NOT introduce a `homework` format.

### 3.4 Extensions to course.yaml

The module ADDS one field to the course schema:

- `tools`: map of tool ids to `{description, availability?, url?}` objects (HW-D03)

Tools are open course-declared strings. Every tool named in a homework's
`allowed_tools` or `item_tools`, or in an item class's `default_tools`, must
resolve to a key in this map. Items themselves carry no tools field (HW-D28).

The module does not change the `course.yaml` template: a new course starts with
no tools declared, and the teacher adds the ones the course uses. Until then,
`class_tools_declared` warns for the tools the starter item classes name.

### 3.5 Homework defaults

At `course/assessments/homework-defaults.yaml`. Read by `homework-planner`
and `/create-homework`'s interviewer; updated at Gate 2 approval. Not
created by `classkit scaffold course`: the first `/create-homework` run
creates it, and `item-classes.yaml`, from their templates (HW-D13).
Validated against `schemas/homework-defaults.schema.json` (keys and allowed
values); the cross-file checks are the rule `homework_defaults_consistent` (HW-D16).

Keys: `total_minutes`, `default_class_counts` (items per class for an
ordinary homework, HW-D27), `allowed_tools`, `collaboration`,
`open_book`, `reuse_policy`, `budget_tolerance_minutes`.

### 3.5a Homework document settings

At `course/assessments/homework-document.yaml` (HW-D30). Says how the Word
documents of step 12 look; holds no answers and is committed with the course.
Created from its template by the first `/create-homework` (HW-D13). Validated
against `schemas/homework-document.schema.json`.

Required: `course_title`, `semester`, `title_format`, `language`, `direction`.
Optional: `instructor`, `due_date_format`, `submission_instructions`, `header`,
`footer`, `logo`, `font`, `font_size`, `show_est_minutes`.

`title_format` placeholders: `{course_title}`, `{semester}`, `{number}` (from
the homework id, `HW03` → 3), `{id}`, `{units}`. The due date is per homework:
the manifest's optional `due_date` (YYYY-MM-DD).

### 3.6 Generated item-bank overview

`classkit bank` generates an on-demand view of the shared item bank (HW-D22).
It writes nothing by default. `--output <file>` saves the selected output only
when the caller asks; `--format human` (the default) is for teachers and
`--format json` is a stable machine-readable contract for agents.

The overview groups items by unit and Guiding Question and reports format,
item class, Bloom spread, declared `usage`, and actual references from
available homework, quiz, and exam manifests. Declared use and actual use are
separate: `usage: [homework]` means eligible, while a manifest reference means
assigned. Missing manifest types are reported as unavailable, never inferred.
It also shows Guiding Questions with no items, those with no homework-eligible
items, items never referenced by an available manifest, and draft items in a
separate section so abandoned runs do not inflate shipped coverage.

`homework-planner` consumes `classkit bank --format json` at the start of
planning. Until the H5 implementation exists, it falls back to scanning the
same source files directly.

---

## 4. Control flow — the `/create-homework` pipeline

Fourteen steps, gated twice by the teacher. `.claude/commands/create-homework.md`
uses the same numbers (the command does not cite this spec — teacher-facing
homework instructions do not depend on `dev/homework/` documents); this section is the normative summary.

**Two gates, continuous in between (HW-D15).** The teacher decides at Gate 1
(step 5) and Gate 2 (step 11). Between them the pipeline runs without
stopping, announcing each step as it goes; writer, critic and solver rounds
need no separate approval. This is the module's reading of the framework's
"stepwise, with your approval" rule.

### 4.1 Steps

1. **Ground.** Read `course.yaml`, syllabus, units, sessions, item bank,
   prior homework, defaults, item-classes.
2. **Interview via `interviewer`.** Collect the spec shape (units,
   purpose, minutes, source, item count per class, tools, collaboration,
   open_book, optional due date, optional `focus_notes`). The due date is
   collected before planning rather than during document generation.
   `focus_notes` is run-only free text: it may guide emphasis or exclusions,
   contains no personal student data, and is saved only in the plan file.
   Interviewer returns `{status, data, unfilled,
   defaults_used, follow_ups}`.
3. **Handle follow-ups.** Undeclared class → STOP, direct to
   `/new-hw-type`. Undeclared tool → note for report. Other → save for
   step 14.
4. **Plan via `homework-planner`.** Writes `course/assessments/homework/
   .plans/HW0N.md` — internal plan with coverage skeleton, per-slot intent,
   slot metadata, reuse decisions, budget check, approved due date and
   `focus_notes`.
5. **GATE 1 — Teacher approves the brief.** Only the plan file exists; no
   items, manifest or reuse edits are written before approval. The brief shows
   the due date and any `focus_notes`. With targeted
   versions (HW-D26) the brief shows each version's targets, item coverage and
   approximate workload; on graded homework, differing versions need the
   teacher's explicit approval.
   - **Approve** → step 6.
   - **Revise** → the planner re-plans and shows a new brief; back to Gate 1.
   - **Show table** → the teacher edits slots by number; back to Gate 1.
   - **Reject** → stop. Nothing but the plan file was written.
6. **Write items via `homework-item-writer`** (per slot). `reuse <id>` appends
   `homework` to usage; `adapt <id>` creates a NEW item id with `source_ref`
   to original; `fresh` creates a new item. Files land with `status: draft`.
7. **Review each item via `item-critic`.** Rubric quality, alignment,
   Bloom match, class fit, giveaway detection, and material fit (HW-D19):
   what the item needs must be in the material students were assigned —
   answer locators first, then the session's study paths; the writer revises
   the item, never the learning material; unverifiable cases go to Gate 2. Cap 3 iterations with
   writer. Deadlock surfaces at Gate 2.
8. **Attempt each item via `item-solver`.** Strategy lookup: item's
   `evaluation_strategy` → class's `evaluation.strategy` → fallback.
   Auto-override: `execute` on non-`code` format falls back to
   `persona_attempt`. Cap 3 iterations.
9. **Write the manifest.** `course/assessments/homework/HW0N.md` with
   `status: draft` frontmatter. Item references, not copies. Include the
   Gate-1-approved due date when supplied; never include `focus_notes`.
10. **Validate.** Run `classkit validate`. Errors block; warnings note.
11. **GATE 2 — Teacher approves final.**
    - **Approve** → strip `status: draft` from every pipeline-authored
      file (fresh items, adapted items, manifest). Reused items untouched.
      Proceed to step 12.
    - **Revise items** → named items back through writer + critic + solver.
      Return to Gate 2.
    - **Reject** → files stay with `status: draft`. Print explicit list
      for teacher; no auto-delete. Skip steps 12 and 13.
12. **Create the documents** (HW-D23). Laid out from
    `homework-document.yaml` (HW-D30), the agent creates a student Word
    document (no answers) and a separate teacher answers document from the
    approved manifest and items — with targeted versions, one student document
    per version (shared items plus that version's items) and one teacher
    document with every version labeled (HW-D26). The due date already came
    from the Gate-1-approved plan and was written with the manifest at step 9;
    this step does not add or overwrite manifest metadata. The agent then runs
    a **leak check**: none of the
    items' answer fields may appear in the student document. Both documents
    stay editable by teacher and agent; agent edits change the item file
    first, then both documents; manual teacher edits are synced back into
    the items only on request, with the teacher confirming each change.
    **Saving (HW-D24):** the teacher chooses the folder; the files are never
    committed. Any location outside the repository is allowed. Inside it, the
    destination must be a dedicated generated-output directory containing no
    tracked files — never the repository root or a broad course directory.
    The agent checks `git ls-files`, adds only the exact anchored relative
    directory to `.git/info/exclude` when needed, verifies it with
    `git check-ignore`, and reports the local exclusion. A tracked target is a
    stop condition, not something ignore rules can repair.
13. **Update defaults.** Compare accepted spec to `homework-defaults.yaml`;
    write changed fields.
14. **Report.** Prose summary of guiding questions touched, reuse decisions,
    time vs budget, unresolved follow-ups.

### 4.2 Loop mechanics

Both `item-critic` and `item-solver` run bounded loops with `assessment-
writer`:

- Cap: 3 iterations per item, per agent
- If still `revise` after iteration 3 → verdict `deadlocked`
- Deadlocked items surface at Gate 2 with a one-sentence summary
- **Never silently converge by lowering standards.** The human breaks the tie.

### 4.3 Strategy lookup (item-solver)

For each item, resolve strategy in this order (HW-D05, HW-D07):

1. Item's `evaluation_strategy` field, if present (item-level override)
2. Otherwise, look up item's `item_class` in `item-classes.yaml`, read
   `evaluation.strategy`
3. Otherwise, fallback: `persona_attempt` if item has `model_answer` and
   `rubric`; `not_applicable` otherwise

**Auto-override:** if resolved strategy is `execute` but item's format is
not `code`, fall back to `persona_attempt` and log it. Prevents executing
a human-graded Coding item as if it were autograded.

**Tool-dependent items (HW-D18).** An item whose answer needs a tool or data
the pipeline cannot run (Wireshark, lab-only software, a provided dataset)
carries `evaluation_strategy: skip`, set by the writer; the solver also
refuses to attempt one it meets under `persona_attempt`. Tool output is never
invented.

**Teacher aid (HW-D18).** For every skipped item the solver writes a
`teacher_aid`, returned in its report and shown at Gate 2 (not saved — where
confidential teacher material is stored is HW-Q06): for Research, up to
3–5 references and a short summary of what a strong answer covers; for
tool-dependent items, the expected approach. References come from the
course's own materials first; anything else must be verifiable or is marked
"unverified — check before use" (framework rule: no invented resources).

### 4.4 Draft convention

Pipeline-authored files land with `status: draft` in frontmatter (HW-Q03
convention). Gate 2 approval promotes to shipped (strips the field).
Rejection leaves them draft for manual salvage or deletion.

**Target behavior** (not yet implemented in the Python validator): draft
files are excluded from shipped-homework completeness checks. Today the
marker is documentary.

---

## 5. Data flow

### 5.1 Files each agent reads and writes

| Agent | Reads | Writes |
|---|---|---|
| `interviewer` | Files passed as `grounding_files` | None (returns data) |
| `homework-planner` | course.yaml, syllabus, units, sessions, item bank, prior homework, defaults, item-classes; if source is quiz_report, the referenced quiz and its aggregated report | `.plans/HW0N.md` (internal) |
| `homework-item-writer` | Plan slot, unit sessions, item bank, item-classes, homework-defaults, `assessment-writer.md` (craft sections) | `items/U0N-I0M.md` (fresh, or edits to existing on reuse) |
| `item-critic` | Item file, plan slot, guiding questions, item-classes, class-specific skill; for material fit, the Guiding Questions' `answer` locators and the session's study paths with the resources they reference | None (returns feedback) |
| `item-solver` | Item file, plan slot, item-classes, class-specific skill; for teacher aids, course materials, `textbooks`, Guiding Question `answer` locators | None (returns findings and teacher aids); may execute Bash for `execute` strategy |
| `/create-homework` | All ground files; results from every agent | Homework manifest, defaults file, promotes drafts on approval |

### 5.2 Skill loading

`homework-item-writer` and `item-critic` load class-specific skills based on
item's `item_class`:

- `Coding` → `.claude/skills/writing-code-items/SKILL.md`
- `Research` → `.claude/skills/writing-research-items/SKILL.md`
- `DIY`, `Practicing`, teacher-added classes → no extra skill
- Custom skill via class `evaluation.custom_skill` when strategy is `custom`

---

## 6. Invariants

The module maintains these invariants; validators enforce them.

- Every file the pipeline writes goes through `classkit write` (framework
  invariant 5). A change to an existing file uses `--overwrite` only after the
  teacher approved that change at a gate: reuse edits at Gate 1; draft
  promotion and defaults updates at Gate 2; `/new-hw-type` appends at its
  change-set approval (process rule, HW-D12)

- Every homework item's `usage` array contains `homework` (validator:
  `homework_item_usage`)
- Every referenced item id resolves to a real file (validator:
  `homework_item_reference`)
- Every referenced item's `unit` is in the homework's `units` (validator:
  `homework_units_declared`)
- Every declared unit has at least one referenced item (validator:
  `homework_coverage`)
- Graded homework has a rubric on every rubric-requiring format (validator:
  `graded_requires_rubric`)
- All `allowed_tools` and `item_tools` are declared in `course.yaml`'s tools map (validators:
  `homework_tools_declared`, `class_tools_declared`)
- Adaptation creates a new item id, never mutates the original in place
  (design rule enforced by `homework-item-writer`; no validator, as it's a
  process constraint)
- Manifest files under `course/assessments/homework/HW*.md` do not include
  `.plans/` — the plan file namespace is separate (validator:
  `homework_schema` file glob)
- Targeted versions have unique labels and ≥1 target each; targets are in the
  declared units; each version item tests one of its version's targets and no
  other Guiding Question; every target is covered; the source is a resolvable
  `quiz_report` (validator: `homework_versions_targeted`, HW-D26)
- No student data in the repository: quiz reports are aggregated per Guiding
  Question; names, identifiers, grades and version assignments stay outside
  (process rule enforced by `/create-homework` and `homework-planner`, HW-D26)
- Sum of item minutes fits `total_minutes` within tolerance; missing per-
  item `est_minutes` on `time_variance: high` classes falls back to
  class range midpoint (validator: `homework_budget_fits`)

---

## 7. Specification reference (normative)

### 7.1 Files the module ships

**Agents (5):** `interviewer.md`, `homework-planner.md`,
`homework-item-writer.md`, `item-critic.md`, `item-solver.md`

**Commands (3):** `create-homework.md`, `new-hw-type.md`, `write-items.md`

**Skills (3):** `interviewing-teachers/SKILL.md`,
`writing-code-items/SKILL.md`, `writing-research-items/SKILL.md`

**Schemas (6, 4 new + 2 modified):**
- `homework.schema.json` (new)
- `item-classes.schema.json` (new)
- `homework-defaults.schema.json` (new)
- `homework-document.schema.json` (new)
- `assessment-item.schema.json` (modified — see section 3.3)
- `course.schema.json` (modified — see section 3.4)

**Templates (10):**
- Assessment: `homework.md`, `item-code.md` (Coding class),
  `item-multiple-choice.md`, `item-multiple-select.md`, `item-numeric.md`,
  `item-open.md`, `item-true-false.md`
- Course: `homework-defaults.yaml`, `homework-document.yaml`, `item-classes.yaml`

### 7.2 Validator rules — 19 total

The module adds 19 rules to the framework's validator. Every rule is
tagged `target` pending Python implementation (build work, not design);
[`ROADMAP.md`](ROADMAP.md)'s ledger is authoritative for which exist.

| Rule | Severity | State (D-033) | Checks |
|---|---|---|---|
| `homework_schema` | error | consistency | Each `HW*.md` (excluding `.plans/`) matches `homework.schema.json` |
| `homework_id_consistency` | error | consistency | Filename stem matches id |
| `homework_item_reference` | error | consistency | Every item id resolves; every `item_tools` key is an item of this homework (HW-D28) |
| `homework_item_usage` | error | consistency | Referenced items have `homework` in `usage` |
| `homework_units_declared` | error | consistency | Every item's unit is in homework's units |
| `homework_coverage` | error | consistency | Every declared unit has ≥1 item |
| `homework_budget_fits` | warn | consistency | Sum of item minutes within tolerance of `total_minutes` (see HW-D06 for high-variance handling) |
| `homework_versions_targeted` | error | consistency | Only if `versions` exist: unique labels; ≥1 target per version, all in declared units; each version item tests ≥1 of its targets and no other Guiding Question, appears once per version and not in the shared items; every target covered; `source` is a `quiz_report` whose `ref` resolves (HW-D26) |
| `homework_source_quiz_exists` | warn | consistency | `quiz_report` source resolves to a real assessment |
| `graded_requires_rubric` | error | consistency | Only when `purpose: graded`: every rubric-requiring format has one |
| `homework_tools_declared` | warn | consistency | `allowed_tools` and `item_tools` all in `course.yaml` |
| `class_tools_declared` | warn | consistency | Class `default_tools` all in `course.yaml` |
| `item_class_declared` | warn | consistency | Item's `item_class` is defined in taxonomy |
| `item_class_bundle_drift` | warn | consistency | Item's bloom/minutes within class range (range-aware per HW-D06) |
| `item_class_evaluation_declared` | warn | consistency | Class has `evaluation.strategy` (HW-D05) |
| `item_source_resolvable` | warn | consistency | An adapted item's `source_ref` resolves to an existing item |
| `code_execution_reference_present` | error | consistency | A `format: code` item resolved to `execute` has both `expected_solution` and `tests` |
| `homework_defaults_consistent` | warn | consistency | Only if `homework-defaults.yaml` exists: `default_class_counts` has at least one positive count, every class in it exists in `item-classes.yaml`, and the estimated work (count × class `typical_minutes` midpoint) is within `budget_tolerance_minutes` of `total_minutes` (HW-D16, HW-D27) |
| `assessment_scheme_complete` | warn | **completeness** | Course has the homework count its syllabus declares. Runs only when the course is complete (D-033) **and** the syllabus declares homework; silent otherwise. Inactive until the framework designs the syllabus `assessment` block (reserved in Core) |

**Homework is optional** (HW-D13). A course may never have a homework, so
every consistency rule checks only homework files, item classes and
defaults that exist, and is silent when there are none. A fresh scaffold therefore
validates with no homework findings at all. The one completeness rule stays
silent unless the syllabus promises homework.

### 7.3 Identifier patterns

- Homework id: `^HW\d{2}$` (HW01..HW99)
- Item id: `^U\d{2}-I\d{2}$` (unchanged from framework)
- Guiding question id: `^U\d{2}-S\d{2}-G\d+$` (unchanged from framework)
- Version label: no strict pattern (A, B, `gq1-2`…); unique within the homework; never identifies a student

---

## 8. Design decisions — index

Each decision has a full entry in `_devlog/01-decisions.md`.

| ID | Title | Status |
|---|---|---|
| HW-D01 | Homework as a first-class content type | provisional |
| HW-D01 addendum | `/write-items homework` hand-off | provisional |
| HW-D02 | Item classes as pedagogical bundles | provisional |
| HW-D03 | Tools as open course-declared strings | provisional |
| HW-D04 | Interviewer as a general-purpose agent | provisional |
| HW-D05 | Evaluation strategy declared per item class | provisional |
| HW-D06 | Item time estimates are class-dependent | provisional |
| HW-D07 | Evaluation strategy overridable per item | provisional |
| HW-D08 | Module carries out the framework's D-031g rename (`answer` → `model_answer`) | provisional — needs Chen's confirmation |
| HW-D09 | Homework items get their own writer agent; `assessment-writer` stays unchanged | provisional |
| HW-D10 | Formats belong to the framework; the module adds only the class axis | provisional |
| HW-D11 | Module-local numbering (`HW-D`, `HW-Q`) | provisional |
| HW-D12 | All homework writes go through `classkit write`; overwrites only after a gate | provisional |
| HW-D13 | Homework is optional: config created on first use; rules silent without homework | provisional |
| HW-D14 | Numeric answer units are `measurement_units`, not `units` | provisional |
| HW-D15 | `/create-homework` matches the spec: same step numbers, two explicit gates | provisional |
| HW-D16 | `homework-defaults.yaml` gets a schema and a consistency rule | provisional |
| HW-D17 | `/review-homework` removed | provisional |
| HW-D18 | Tool-dependent items are skipped; skipped items get a teacher aid | provisional |
| HW-D19 | `item-critic` checks material fit against what students were assigned | provisional |
| HW-D20 | Homework document export (student Word + teacher answers) is in scope — scope only | provisional |
| HW-D21 | One shared item bank; no separate homework bank; generated overviews only | provisional |
| HW-D22 | `classkit bank` generates the item-bank overview on demand | provisional |
| HW-D23 | An agent creates the student and teacher Word documents after Gate 2, with a leak check; both stay editable | provisional |
| HW-D24 | The Word documents are saved where the teacher chooses and never committed | provisional |
| HW-D25 | `answer_release` dropped; publishing solutions is the teacher's call | provisional |
| HW-D26 | Versions are targeted at Guiding Questions from a quiz report; no student data in the repository | provisional |
| HW-D27 | Item counts per class replace the class mix (`default_class_counts`) | provisional |
| HW-D28 | Per-item tools live in the manifest (`item_tools`), not in the item schema | provisional |
| HW-D29 | `prerequisites` dropped from the manifest | provisional |
| HW-D30 | The Word documents are laid out from `homework-document.yaml` | provisional |
| HW-D31 | Focus notes are plan-only; due date is approved before writing | provisional |

---

## 9. Open questions — index

Each question has a full entry in `_devlog/03-open-questions.md`.

| ID | Title | Status |
|---|---|---|
| HW-Q01 | Assessment item format extensibility | open |
| HW-Q02 | Item bank ingest — reference-only vs materialized | open |
| HW-Q03 | Agent-authored files — status draft convention | open (partially in use) |
| HW-Q04 | Should item-critic and item-solver apply to quiz/exam? | open |
| HW-Q05 | Sandbox and resource policy for code execution | open |
| HW-Q06 | Where homework is graded and what must stay hidden (per class and purpose) | open — linked to framework Q-002 |
| HW-Q07 | Re-reviewing a finished or old homework before reuse | open |
| HW-Q08 | Bank growth: identifier capacity and provenance | open — proposal for the framework |

---

## 10. Known weaknesses and open risks

- **The Python runtime does not implement any of this yet.** The design is
  coherent enough to build against, but until `classkit` loads homework
  manifests and item classes and the 19 rules are implemented, homework is
  a specification only. See `ROADMAP.md`.
- **Draft-aware validation is unimplemented.** The `status: draft`
  convention is documentary today; the validator does not exclude drafts
  from shipped-homework checks. HW-Q03 tracks the target behavior.
- **Sandbox for `execute` strategy is unresolved.** Running teacher-
  provided code via Bash without a resource policy is a real risk. HW-Q05
  tracks options.
- **Quiz and exam items receive less review than homework items.** Only
  homework runs through critic and solver. HW-Q04 tracks whether to
  generalize.
- **Time-constants integration is minimal.** Practicing-class items with
  reading portions could use `article_words_per_minute` etc. from
  `defaults/time-constants.yaml` (D-025) as one input to critic's sanity
  check. Not required; add when a real course pushes on it.
- **`assessment_scheme_complete` for homework with versions** is under-specified.
  The rule counts homework files; a homework with targeted versions counts
  once, which may not match what a syllabus expects. Refine when
  a real case with versions exists.

---

## 11. File map

Module documents live under `dev/homework/`; runtime files sit at their
framework paths.

```
dev/homework/
├── README.md
├── HOMEWORK-SPEC.md               (this file)
├── ROADMAP.md                     (plan and ledger — authoritative for what exists)
├── _devlog/
│   ├── README.md
│   ├── 00-brief.md
│   ├── 01-decisions.md            (HW-D01..HW-D31)
│   ├── 02-progress.md
│   ├── 03-open-questions.md       (HW-Q01..HW-Q08)
│   └── 04-handoff.md

.claude/
├── agents/
│   ├── homework-item-writer.md
│   ├── homework-planner.md
│   ├── interviewer.md
│   ├── item-critic.md
│   └── item-solver.md
├── commands/
│   ├── create-homework.md
│   ├── new-hw-type.md
│   └── write-items.md             (modifies framework — 4-line homework guard)
└── skills/
    ├── interviewing-teachers/SKILL.md
    ├── writing-code-items/SKILL.md
    └── writing-research-items/SKILL.md

schemas/
├── assessment-item.schema.json    (modifies framework — optional fields + rename)
├── course.schema.json             (modifies framework — adds tools)
├── homework.schema.json           (new)
├── homework-defaults.schema.json  (new)
├── homework-document.schema.json  (new)
└── item-classes.schema.json       (new)

templates/
├── assessment/
│   ├── homework.md                (new)
│   ├── item-code.md               (new — Coding-class template)
│   ├── item-multiple-choice.md    (modifies framework — comment only)
│   ├── item-multiple-select.md    (new framework-format template; review separately)
│   ├── item-numeric.md            (new framework-format template; review separately)
│   ├── item-open.md               (modifies framework — rename)
│   └── item-true-false.md         (new framework-format template; review separately)
└── course/
    ├── homework-defaults.yaml     (new)
    ├── homework-document.yaml     (new)
    └── item-classes.yaml          (new)
```
