# Handoff — implementation task list

Whoever picks up the module for Python implementation, read this first.
Complements `HOMEWORK-SPEC.md` (the what) with the how, in order.

## State at handoff

- Design: complete and reviewed across five audit rounds.
- Python runtime: unchanged. `classkit` does not load homework manifests,
  item classes, or the new templates. Scaffolding creates the homework
  directory but no files in it.
- Validator: unchanged. None of the 21 rules exist in `validate.py`.
- Tests: no homework-specific tests exist.
- All content files (agents, commands, skills, schemas, templates) ship
  in the module and are ready to drop into their target paths.

## Task list, in order

### 1. Module content — done

The agents, commands, skills, schemas and templates are already in place
in the `homework-by-shira` branch; merging it into `main` installs them.
Start at task 2.

### 2. Update `src/classkit/model.py`

Currently loads only course, syllabus, units, sessions, items. Add:

- Loader for `course/assessments/homework/HW*.md` (parse frontmatter and
  body; exclude `.plans/` per `homework_schema` rule)
- Loader for `course/assessments/item-classes.yaml`
- Loader for `course/assessments/homework-defaults.yaml`, validated against
  `schemas/homework-defaults.schema.json` (add it to `SCHEMA_FOR`)
- New model classes: `Homework`, `ItemClass`, `HomeworkDefaults`
- Extend `Course` to hold `homework: List[Homework]`, `item_classes:
  Dict[str, ItemClass]`, `homework_defaults: Optional[HomeworkDefaults]`
- Extend `Item` model with the new optional fields (per §3.3 of SPEC)

Tests to add: `tests/test_model_homework.py` — fixtures for each new
loader, error cases for malformed files.

### 3. Update `src/classkit/validate.py`

**Rule states (D-033, HW-D13).** 20 of the 21 rules are *consistency*
rules: they judge only homework manifests, item classes and defaults that exist, and
must produce nothing on a course with no homework. `assessment_scheme_complete`
is the one *completeness* rule: report it as skipped until the course is
complete, and silent unless the syllabus declares homework. Severity is
fixed per rule (`DEFAULT_SEVERITY`); the two `graded_*` rules are errors
that only apply when `purpose: graded`. Each rule needs a test in both
directions, including "no homework → no finding".

Implement all 21 rules from HOMEWORK-SPEC §7.2. Each rule as a Python
function returning `List[Diagnostic]` (or the framework's existing
diagnostic type). Function names should match rule names.

Grouping (proposed):

- `validate_homework_structure()` — schema, id_consistency, item_reference,
  item_usage, units_declared, coverage, prerequisites_precede
- `validate_homework_budgets_and_versions()` — budget_fits, versions_fair,
  source_quiz_exists
- `validate_graded_homework()` — requires_rubric, answer_release_safe
- `validate_tools()` — homework_tools_declared, class_tools_declared
- `validate_item_classes()` — item_class_declared, item_class_bundle_drift,
  item_class_evaluation_declared, item_source_resolvable,
  code_execution_reference_present
- `validate_assessment_scheme()` — assessment_scheme_complete

Tests: `tests/test_validate_homework.py` — one test per rule, positive
and negative cases.

**Notes for tricky rules:**
- `homework_defaults_consistent`: only when the file exists. Compare the
  class-mix sum with a tolerance (±0.01) — the shipped template sums to
  0.9999999999999999 in floating point.
- `homework_budget_fits`: per HW-D06, missing `est_minutes` on
  `time_variance: high` classes uses midpoint of `typical_minutes` range.
- `homework_schema`: file glob `HW*.md` MUST exclude `.plans/`.
- `graded_requires_rubric`: only applies when `purpose: graded`, and only
  to items whose format requires a rubric (`open`, `code`).
- `graded_answer_release_safe`: `purpose: graded` + `answer_release:
  with_homework` = error.
- `code_execution_reference_present`: resolve the per-item strategy override,
  then the class strategy. When the result is `execute` and the item format is
  `code`, require both `expected_solution` and `tests`.
- Draft-aware validation (excluding `status: draft` from
  `assessment_scheme_complete`) is TARGET behavior. Ship the rules as-is
  first (they treat draft and shipped identically); layer draft-awareness
  as a second pass. HW-Q03 tracks.

### 4. Update `src/classkit/scaffold.py`

- Add `scaffold homework` subcommand — creates a new `HW{NN}.md` from
  template
- Do NOT make `scaffold course` create `homework-defaults.yaml`,
  `item-classes.yaml` or `homework/.plans/` (HW-D13: homework is optional).
  `/create-homework` creates them on first use. `scaffold course` already
  creates the empty `assessments/homework/` directory; leave that as is.
- Update `scaffold item` to accept `--class <name>` and set `item_class`
  in the item's frontmatter

Tests: extend `tests/test_course_lifecycle.py` to cover the new files.

### 5. Update `src/classkit/cli.py`

- Add `scaffold homework` argument parser
- Extend `scaffold item` with `--class`, and let `--format code` use the
  Coding-class template `item-code.md` (templates for other formats are
  the framework's call — see `dev/homework/for-chen/`)

### 6. Write end-to-end tests

New file: `tests/test_homework_pipeline.py`. Fixtures:

- Practice homework, small (single unit, 3 items)
- Graded homework, multi-unit (2 units, 5 items, mix of classes)
- Diagnostic homework tied to a `quiz_report` source
- Grouped homework with two versions
- Homework with reused items (usage array extension)
- Homework with adapted items (new id + source_ref)
- Coding homework (autograded via `execute` strategy)
- Research homework (skipped via `skip` strategy)

Each fixture: load the fixture course, run `classkit validate`, assert
expected errors/warnings.

### 7. Update public status documentation

The design-phase part is done: `FRAMEWORK-SPEC.md` (Assessment row),
`ROADMAP.md`, the root `CLAUDE.md`, `GETTING-STARTED.md` and `README.md`
already describe homework as *specified, validation not built* (every
addition in the root docs is marked `homework-module`).

Only after (2)-(6) pass:

- Change those notes from "validation not built" to "implemented" — search
  for `homework-module` in the root docs
- Change the Assessment row in `FRAMEWORK-SPEC.md` to "Implemented"
- Add the homework milestone to the framework's `dev/_devlog/02-progress.md`

## Not to do in this phase

- **Do not implement the sandbox for `execute` strategy.** HW-Q05 is
  unresolved. Ship with a warning and require explicit `--allow-execution`
  flag on `classkit validate`, OR delegate to the `item-solver` agent's
  runtime (Claude Code sandbox), OR mark autograded Coding as
  experimental.
- **Do not extend `item-critic` or `item-solver` to quiz/exam items.**
  HW-Q04 tracks the decision. Homework-only for now.
- **Do not implement rendering** (manifest → student PDF/Moodle export).
  Never designed.
- **Do not implement item bank ingest** (`/ingest-items` command). HW-Q02
  logged as open.

## Estimated effort

Rough estimates, assuming Python developer with framework familiarity:

- Task 1 (module content): done
- Task 2 (model updates): 3-4 hours
- Task 3 (validator rules): 6-8 hours (many rules, each simple; setup dominates)
- Task 4 (scaffolding): 2 hours
- Task 5 (CLI): 1 hour
- Task 6 (end-to-end tests): 4-6 hours (fixtures take time)
- Task 7 (docs): 30 minutes

Total: **17-22 hours** of focused work. Plus review time and iteration.

## Failure modes to watch for

- **Silent field drops:** JSON Schema allows unknown properties by default
  unless `additionalProperties: false` is set. All three new schemas
  (`homework`, `item-classes`) set it — validators must produce actionable
  errors, not silent truncation.
- **Path handling on Windows:** `course/assessments/homework/.plans/`
  uses forward slashes in glob patterns. Test on Windows or use
  `pathlib.PurePosixPath` for globs.
- **Version conflicts:** if a course has both a `homework/HW01.md` and
  a `homework/.plans/HW01.md`, the loader must include the shipped file
  and exclude the plan. Explicit filter, not implicit.
- **item_class case sensitivity:** class names in `item-classes.yaml` are
  case-sensitive. `DIY` and `Diy` are different classes. Enforce or
  normalize; don't guess.

## Design points worth re-reading before you start

- **HW-D01 addendum** — why `/write-items homework` hands off rather than
  deprecates
- **HW-D06** — why Coding and Research items don't need `est_minutes`
- **HW-D07** — the `evaluation_strategy` override and auto-fallback for
  Coding + open
- **HW-Q05** — sandbox options for `execute` strategy

## When you're done

- Update `HOMEWORK-SPEC.md` §7.2 to drop the `target` tag from implemented
  rules
- Update `_devlog/02-progress.md` with a new "Implementation phase" entry
- Send a PR with the implementation for review
