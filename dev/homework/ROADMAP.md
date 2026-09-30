# Homework module — roadmap

The homework module's plan and ledger, in the same format as the framework's `dev/ROADMAP.md`.
Decisions are `HW-Dnn` and open questions `HW-Qnn` (in `_devlog/`); plain `D-nnn` / `Q-nnn`
are the framework's own.

Status: ✅ done · 🔨 in progress · ⬜ not started

---

## Where homework sits in the framework's phases

Homework is the **homework part of the framework's Assessment phase** (`FRAMEWORK-SPEC.md`
phase table; exams and the grading scheme stay deferred), developed as a separate module.

- ✅ **Design** — `HOMEWORK-SPEC.md`, HW-D01…HW-D32, HW-Q01…HW-Q08. The agents, commands,
  skills, schemas and templates are written.
- ⬜ **Implementation** — the Python side: loaders, the 21 validator rules, scaffolding, tests.
  The plan below.
- ⬜ **First real homework** — run `/create-homework` on a real course. As with the framework's
  Phase 2, this is where assumptions break: no homework agent has run against real material yet.
  It is also the only test of the agent pipeline itself — the gates, writing, and the critic
  and solver loops — which H6 does not cover.

---

# Implementation plan — the order to work the ledger

The ledger below is grouped **by decision**; this is the order to build it. Same principle as
the framework: within a step, work layer by layer — schema → template → loader → validator rule
→ agent / command → test — and leave the suite green (framework invariant 6).

| Step | Delivers | Ledger rows drawn from |
|---|---|---|
| **H0. Module content** ✅ | Agents, commands, skills, schemas and templates in place. | all decisions (content rows) |
| **H1. Load** | `model.py` loads `HW*.md` (excluding `.plans/`), `item-classes.yaml`, `homework-defaults.yaml`, `homework-document.yaml`; `Homework`, `ItemClass`, `HomeworkDefaults`, `HomeworkDocument` models; `Item` gains the optional homework fields. `validate.py` registers the four new schemas in `SCHEMA_FOR`. | HW-D01, HW-D02, HW-D16, HW-D30 |
| **H2. Manifest rules** | The 6 structural rules on a homework manifest, plus budget, versions and source. | HW-D01, HW-D06 |
| **H3. Class, tool and defaults rules** | Item-class, tool and defaults rules, and `code_execution_reference_present`. | HW-D02, HW-D03, HW-D05, HW-D07, HW-D16 |
| **H4. Graded and completeness rules** | `graded_requires_rubric`; `assessment_scheme_complete` (skipped until the framework designs the syllabus `assessment` block). | HW-D01, HW-D13 |
| **H5. Scaffold and CLI** | `classkit scaffold homework`; `scaffold item --class`; all shipped format templates; `classkit bank` with human and JSON output. `scaffold course` stays unchanged (HW-D13). | HW-D01, HW-D02, HW-D10, HW-D22 |
| **H6. Integration tests** | `tests/test_homework_integration.py`: fixture courses loaded and validated, with the fixtures listed in `_devlog/04-handoff.md`. Covers loading and validation only — not the agents, the gates or the writer/critic/solver loops. | all |
| **H7. Docs** | Switch "validation not built" to "implemented": search `homework-module` in the root docs; the Assessment row in `FRAMEWORK-SPEC.md`. | — |

**Scope of "homework is optional"** (HW-D13): a pristine course with no homework artifacts
produces no homework findings. Manifest-dependent rules are silent without manifests;
configuration rules (item classes, tools, defaults) run whenever their configuration file
exists — for example after an abandoned first `/create-homework` — and still report
malformed configuration. Every rule in H2–H4 needs a test for its own silent case. Implementation notes for the tricky rules are in
`_devlog/04-handoff.md`.

**Prerequisites from the framework:** the overwrite-safe write path (framework step 0 ✅) is
needed by every homework command (HW-D12). `assessment_scheme_complete` cannot become active
until the framework specifies the syllabus `assessment` block.

---

# Implementation ledger

`HOMEWORK-SPEC.md` describes the **target** design and reads as if it exists. **This ledger is
authoritative for what actually exists.** Anything still ⬜ is designed, not built; tick a row in
the commit that lands it. When the framework locks a homework decision, this ledger is where its
rows live.

## HW-D01 — Homework as a first-class content type

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework.schema.json` | the manifest schema |
| ✅ | `templates/assessment/homework.md` | manifest template |
| ✅ | `.claude/commands/create-homework.md`, `.claude/agents/homework-planner.md` | the pipeline and its planner |
| ✅ | `.claude/commands/write-items.md` | 4-line guard handing homework to `/create-homework` (addendum) |
| ⬜ | `src/classkit/model.py` | load `course/assessments/homework/HW*.md`, excluding `.plans/` |
| ⬜ | `src/classkit/validate.py` | register `homework.schema.json` in `SCHEMA_FOR` |
| ⬜ | `src/classkit/validate.py` | `homework_schema`, `homework_id_consistency`, `homework_item_reference`, `homework_item_usage`, `homework_units_declared`, `homework_coverage` |
| ⬜ | `src/classkit/validate.py` | `homework_versions_targeted` (HW-D26), `homework_source_quiz_exists` |
| ⬜ | `src/classkit/validate.py` | `graded_requires_rubric` (only when `purpose: graded`) |
| ⬜ | `src/classkit/scaffold.py`, `cli.py` | `classkit scaffold homework` |
| ⬜ | `tests/` | one test per rule, both directions |

## HW-D02 — Item classes as pedagogical bundles

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/item-classes.schema.json` | the class taxonomy schema |
| ✅ | `templates/course/item-classes.yaml` | DIY, Practicing, Coding, Research |
| ✅ | `schemas/assessment-item.schema.json` | optional `item_class` |
| ✅ | `.claude/commands/new-hw-type.md` | add a class through an interview |
| ✅ | `.claude/skills/writing-code-items/`, `writing-research-items/` | class-specific writing skills |
| ⬜ | `src/classkit/model.py` | load `item-classes.yaml` |
| ⬜ | `src/classkit/validate.py` | register `item-classes.schema.json` in `SCHEMA_FOR` |
| ⬜ | `src/classkit/validate.py` | `item_class_declared`, `item_class_bundle_drift` |
| ⬜ | `src/classkit/scaffold.py`, `cli.py` | `scaffold item --class` |
| ⬜ | `tests/` | rule tests |

## HW-D03 — Tools as open course-declared strings

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/course.schema.json` | optional `tools` map (`description`, `availability`, `url`) |
| ⬜ | `src/classkit/validate.py` | `homework_tools_declared`, `class_tools_declared` |
| ⬜ | `tests/` | rule tests, including a new course with no tools and no homework → no finding |

## HW-D04 — Interviewer as a general-purpose agent

| | Artifact | Change |
|---|---|---|
| ✅ | `.claude/agents/interviewer.md` | the agent (input `Subject`, not `Topic`) |
| ✅ | `.claude/skills/interviewing-teachers/SKILL.md` | the rulebook |

## HW-D05 — Evaluation strategy declared per item class

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/item-classes.schema.json` | `evaluation.strategy` |
| ✅ | `.claude/agents/item-solver.md` | strategy lookup and branching |
| ⬜ | `src/classkit/validate.py` | `item_class_evaluation_declared` |
| ⬜ | `tests/` | rule test |

## HW-D06 — Item time estimates are class-dependent

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/item-classes.schema.json` | `typical_minutes` as a range; `time_variance` |
| ✅ | `.claude/agents/item-critic.md`, `homework-planner.md` | variance-aware time checks and budget |
| ⬜ | `src/classkit/validate.py` | `homework_budget_fits` (range midpoint for `time_variance: high`) |
| ⬜ | `src/classkit/validate.py` | `item_class_bundle_drift` is range-aware |

## HW-D07 — Evaluation strategy overridable per item

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/assessment-item.schema.json` | optional `evaluation_strategy` |
| ✅ | `.claude/agents/item-solver.md` | override and the `execute` → `persona_attempt` fallback |
| ⬜ | `src/classkit/validate.py` | `code_execution_reference_present` |

## HW-D08 — The framework's D-031g rename, carried out by the module

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/assessment-item.schema.json` | `answer` → `model_answer` |
| ✅ | `templates/assessment/item-open.md` | same rename |
| ✅ | framework `dev/ROADMAP.md` | the two D-031g rows ticked |

## HW-D09 — Homework items get their own writer agent

| | Artifact | Change |
|---|---|---|
| ✅ | `.claude/agents/homework-item-writer.md` | the agent |
| ✅ | `.claude/agents/assessment-writer.md` | unchanged from `main` |

## HW-D10 — Formats belong to the framework

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/assessment-item.schema.json` | optional fields only; the framework's format rules unchanged |
| ✅ | `templates/assessment/item-code.md` | the Coding-class template |
| ✅ | `templates/assessment/` | numeric, multiple-select and true-false templates at their framework target paths for review |

## HW-D11 — Module-local numbering

| | Artifact | Change |
|---|---|---|
| ✅ | all module files | `HW-Dnn` / `HW-Qnn`; old → new mapping in `_devlog/README.md` |

## HW-D12 — All homework writes go through `classkit write`

| | Artifact | Change |
|---|---|---|
| ✅ | `create-homework.md`, `homework-item-writer.md`, `homework-planner.md`, `new-hw-type.md` | the rule, where each writes |
| ⬜ | — | confirmed in practice on the first real homework (the agents have never run) |

## HW-D13 — Homework is optional

| | Artifact | Change |
|---|---|---|
| ✅ | `HOMEWORK-SPEC.md` §7.2 | rule states: all consistency except 1 completeness |
| ✅ | `create-homework.md`, `new-hw-type.md` | create the config files on first use |
| ✅ | `src/classkit/scaffold.py` | nothing to change: `scaffold course` does not create homework config |
| ⬜ | `src/classkit/validate.py` | `assessment_scheme_complete` — completeness; blocked until the syllabus `assessment` block exists |
| ⬜ | `tests/` | each rule's silent case: manifest rules without manifests; configuration rules without their file; a pristine course has no homework findings |

## HW-D14 — Numeric answer units are `measurement_units`

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/assessment-item.schema.json` | the field |
| ✅ | `homework-item-writer.md`, `templates/assessment/item-numeric.md` | use the new name |

## HW-D15 — `/create-homework` matches the spec

| | Artifact | Change |
|---|---|---|
| ✅ | `create-homework.md`, `HOMEWORK-SPEC.md` §4.1 | same step numbers (now 14, HW-D23), Gate 1 with four outcomes |

## HW-D16 — `homework-defaults.yaml` gets a schema and a rule

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework-defaults.schema.json` | the schema |
| ✅ | `templates/course/homework-defaults.yaml` | points to its schema |
| ⬜ | `src/classkit/model.py` | load the file |
| ⬜ | `src/classkit/validate.py` | register `homework-defaults.schema.json` in `SCHEMA_FOR` |
| ⬜ | `src/classkit/validate.py` | `homework_defaults_consistent` (checks as amended by HW-D27) |
| ⬜ | `tests/` | rule tests |

## HW-D17 — `/review-homework` removed

| | Artifact | Change |
|---|---|---|
| ⬜ | `.claude/commands/review-homework.md` | delete (by hand) |
| ✅ | spec, roadmap, root `CLAUDE.md`, `GETTING-STARTED.md`, `dev/CLAUDE.md` | references removed |

## HW-D18 — Tool-dependent items skipped; teacher aid for skipped items

| | Artifact | Change |
|---|---|---|
| ✅ | `item-solver.md` | tool check, `teacher_aid` (in the report and at Gate 2; not saved), reference rules |
| ✅ | `homework-item-writer.md` | set `evaluation_strategy: skip` on tool-dependent items |
| ✅ | `create-homework.md` | Gate 2 lists teacher aids and "check by hand" items |
| ✅ | `writing-research-items` | what the teacher gets for Research items |
| ⬜ | — | confirmed on the first real homework |

## HW-D19 — Material fit checked by `item-critic`

| | Artifact | Change |
|---|---|---|
| ✅ | `item-critic.md` | material-fit check: answer locators, then assigned study paths |
| ✅ | `homework-item-writer.md` | revise the item, never the learning material |
| ✅ | `create-homework.md` | Gate 2 lists unverified material fit and material-change suggestions |
| ⬜ | — | depends on the framework's answer locators (D-019), not built yet |

## HW-D20 — Homework document export in scope (scope only)

| | Artifact | Change |
|---|---|---|
| ⬜ | — | design: generator (code or agent), contents and paths, edit flow |
| ⬜ | — | implementation, after the design decisions |

## HW-D21 — One shared item bank

| | Artifact | Change |
|---|---|---|
| ✅ | — | nothing to build for the decision itself: homework already writes into `course/assessments/items/` |
| ⬜ | `classkit bank` | generated bank overview (human default, stable JSON for agents, optional explicit output file) |
| ⬜ | — | ingestion (HW-Q02), identifier capacity and provenance (HW-Q08, for the framework) |

## HW-D22 — On-demand item-bank overview

| | Artifact | Change |
|---|---|---|
| ✅ | `HOMEWORK-SPEC.md`, `homework-planner.md` | report contract and planner use designed |
| ⬜ | `src/classkit/cli.py` and supporting code | implement `classkit bank`, `--format human|json`, and `--output` |
| ⬜ | `tests/` | declared vs actual use, missing manifest types, drafts, gaps, stdout and explicit output |

## HW-D23 — Agent-created Word documents with a leak check

| | Artifact | Change |
|---|---|---|
| ✅ | `create-homework.md` | step 12: create both documents, leak check, edit and sync rules |
| ✅ | `HOMEWORK-SPEC.md` §4.1, `GETTING-STARTED.md` §6 | fourteen steps; the teacher-facing summary |
| ✅ | `create-homework.md` | save outside the repo or in a dedicated untracked, locally ignored output directory; never committed (HW-D24) |
| ⬜ | — | confirmed on the first real homework |

## HW-D25 — `answer_release` dropped

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework.schema.json`, `homework-defaults.schema.json` | field and its graded condition removed |
| ✅ | `templates/assessment/homework.md`, `templates/course/homework-defaults.yaml`, `item-code.md` | field and comments removed |
| ✅ | `create-homework.md`, spec | no longer asked or validated; rule `graded_answer_release_safe` removed (20 rules) |

## HW-D26 — Targeted versions

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework.schema.json` | version objects: `label`, required `targets`, unique `items`; versions require a `quiz_report` source with `ref` |
| ✅ | `templates/assessment/homework.md` | targeted versions example and privacy note |
| ✅ | `create-homework.md`, `homework-planner.md`, spec | Gate 1 shows targets, coverage and workload per version; graded differences need explicit approval; one student document per version; aggregated reports only |
| ⬜ | `src/classkit/validate.py` | `homework_versions_targeted` replaces `homework_versions_fair` (still 20 rules) |
| ⬜ | `tests/` | valid targeted versions plus the failing cases listed in the handoff |

## HW-D27 — Item counts per class

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework-defaults.schema.json`, `templates/course/homework-defaults.yaml` | `default_class_counts` (integers) replaces `default_class_mix` |
| ✅ | `create-homework.md`, `new-hw-type.md`, `homework-planner.md`, spec, `GETTING-STARTED.md` | counts per class; shared and per-version counts for targeted homework; targeted runs don't update the counts |
| ⬜ | `src/classkit/validate.py` | `homework_defaults_consistent`: positive count, classes exist, estimated work within budget tolerance |
| ⬜ | `tests/` | defaults with all-zero counts, unknown class, over-budget counts |

## HW-D28 — Per-item tools in the manifest

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework.schema.json`, `templates/assessment/homework.md` | optional `item_tools` map (item id → tools) |
| ✅ | `create-homework.md`, `homework-planner.md`, `homework-item-writer.md`, `item-solver.md`, spec | tools asked per item; slot carries them; solver uses them for the skip check |
| ⬜ | `src/classkit/validate.py` | `homework_tools_declared` covers `item_tools`; `homework_item_reference` checks its keys |
| ⬜ | `tests/` | undeclared tool in `item_tools`; key that is not an item of the homework |

## HW-D29 — `prerequisites` dropped

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework.schema.json`, `templates/assessment/homework.md`, spec | field and rule `homework_prerequisites_precede` removed (19 rules) |

## HW-D30 — Word document settings

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework-document.schema.json`, `templates/course/homework-document.yaml` | new settings file for the Word documents |
| ✅ | `schemas/homework.schema.json`, `templates/assessment/homework.md` | optional `due_date` |
| ✅ | `create-homework.md` (steps 1 and 12), spec, `GETTING-STARTED.md` | created on first use; documents laid out from it |
| ⬜ | `src/classkit/model.py`, `validate.py` | load it; register `homework-document.schema.json` in `SCHEMA_FOR` |

## HW-D31 — Plan-only focus notes and pre-approved due dates

| | Artifact | Change |
|---|---|---|
| ✅ | `create-homework.md`, `homework-planner.md`, spec | collect `focus_notes` and `due_date` before planning; show both at Gate 1; keep focus notes only in the plan; never add manifest metadata during document generation |

## HW-D32 — Aligned with framework D-036, D-037, D-038

| | Artifact | Change |
|---|---|---|
| ✅ | `schemas/homework.schema.json` | `accepted: [{rule, reason?}]` (same definition as the framework) |
| ✅ | spec §7.2, `create-homework.md`, `homework-item-writer.md` | severities per D-037; version and defaults rules split (21 rules); step 10 wording |
| ✅ | `create-homework.md`, `new-hw-type.md` | `classkit log` entry after each approval |
| ⬜ | `src/classkit/validate.py` | register all 21 rules in `DEFAULT_SEVERITY`; `homework_version_reference`, `homework_defaults_class_reference` |
| ⬜ | module wording on `open` rubrics | update when the framework's D-038 G-19 lands (schema untouched until then) |


| | Artifact | Change |
|---|---|---|
| ✅ | root `CLAUDE.md`, `GETTING-STARTED.md`, `README.md` | homework sections, marked `homework-module` |
| ✅ | framework `FRAMEWORK-SPEC.md`, `ROADMAP.md`, `_devlog/` | cross-references to the module |
| ⬜ | the same root docs | switch to "implemented" after H1–H6 (step H7) |
