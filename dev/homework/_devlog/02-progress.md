# Homework module development progress

Chronological log of what happened during the module's design phase.
Mirrors the framework's own `02-progress.md`.

## September 2026 — design phase

### Week 1 — Core design

- **HW-D01 drafted:** homework as a first-class manifest-level content
  type; resolves Q-026. Own schema (`homework.schema.json`), own on-disk
  location (`course/assessments/homework/HW*.md`), own metadata. Homework
  items keep the framework's original formats — no new item format.
- **Homework schema written** with fields for units, purpose, budget,
  source, items (references only), tools, collaboration, open_book,
  answer_release, prerequisites, versions.
- **HW-D02 drafted:** item classes as pedagogical bundles. Third axis
  alongside format (answer shape) and usage (context). Per-course
  taxonomy in `item-classes.yaml`. Four pilot classes: DIY, Practicing,
  Coding, Research.
- **HW-D03 drafted:** tools as open course-declared strings. Retires the
  fixed enum in favor of a `tools:` map in `course.yaml`. Homework and
  item classes reference tools by key.
- **First bundle produced.** Schemas, agents, commands, skills, templates,
  devlog inserts.

### Week 2 — Refinement and evaluation

- **HW-D04 drafted:** interviewer as a general-purpose agent. Any command
  needing structured teacher input invokes it. Returns
  `{status, data, unfilled, defaults_used, follow_ups}`. Never writes
  files or invokes other agents.
- **HW-D05 drafted:** evaluation strategy declared per item class. Four
  strategies: `persona_attempt`, `execute`, `skip`, `custom`. Replaces
  hardcoded class table in `item-solver`. Fallback if absent.
- **First external review.** Identified 10 issues across format:homework
  confusion, class-branching gaps, schema-extension notes. All fixed;
  bundle republished.

### Week 3 — Audits and hardening

- **Second review round.** Reviewer correctly identified that
  `format: homework` collapsed two orthogonal axes. Reverted; homework
  items use existing formats plus `item_class`.
- **Third review round.** Caught nine blockers:
  1. HW-D05 didn't actually land in `item-solver.md` (silent edit failure)
  2. `create-homework` skipped critic/solver in orchestration
  3. Adapt mutated shared items with the same id
  4. Plan files clashed with the `HW*.md` validator glob
  5. Schema laxity (uniqueItems, conditional requireds)
  6. Gate 2 not transactional
  7. Code items had ambiguous reference-answer field
  8. HW-D05 appeared before HW-D04 in the devlog
  9. Bash sandbox concern
  All fixed. **HW-Q04 and HW-Q05 logged** for future work.
- **`/write-items homework` hand-off decision.** Decided against
  deprecation; command now hands off to `/create-homework` with a visible
  notice. **HW-D01 addendum recorded.**
- **HW-D06 drafted:** item time estimates are class-dependent.
  `typical_minutes` becomes a range `{min, max}`; new `time_variance`
  field on classes. Coding and Research items don't need per-item
  `est_minutes` — fake precision would mislead the budget check.
- **Templates added.** Four new item templates (code, numeric,
  multiple-select, true-false), `item-multiple-choice` replacement with
  `item_class` field, homework manifest template, `homework-defaults`
  and `item-classes` templates, `course.yaml` replacement with tools map.

### Week 4 — Final polish and module packaging

- **Fourth review round.** Five blockers found:
  1. Template used `source.kind: standalone`, schema allows only
     `material | quiz_report`
  2. Version item ids used invalid pattern (`U03-I06A`)
  3. Schemas forbade additional properties but pipeline wrote
     `status: draft`
  4. `reuse_policy` in planner vs `reuse` in defaults template
  5. Gate 2 rejection didn't handle already-written draft files
  All fixed. **HW-D07 added** for per-item `evaluation_strategy` override,
  addressing the reviewer's conceptual concern about Coding + open format.
- **Fifth review round.** Four remaining problems:
  1. Gate 2 rejection wording still stale
  2. Gate 2 approval never promoted draft → shipped explicitly
  3. Schema descriptions overclaimed draft-aware validation
  4. README numbers stale (said HW-D04, was HW-D07)
  All fixed. Design phase complete.
- **Module packaging.** Reorganized as a self-contained module mirroring
  the framework's structure: HOMEWORK-SPEC.md, `_devlog/` with brief,
  decisions, progress, open questions, handoff. Code files kept in
  standard paths (`.claude/`, `schemas/`, `templates/`) so they overlay
  onto a framework repo at install time.

## Metrics

- 31 decisions (HW-D01..HW-D31, plus HW-D01 addendum)
- 8 open questions logged (HW-Q01..HW-Q08)
- 19 validator rules specified (all tagged `target` pending Python
  implementation)
- 5 audit rounds, all specific issues addressed
- Estimated ~2000 lines of documentation across SPEC, devlog, and README
- Estimated ~3000 lines of design content across agents, commands, skills,
  schemas, templates

## Not done in this phase

See `04-handoff.md` for the full task list.

- Python runtime updates (`src/classkit/model.py`, `validate.py`,
  `scaffold.py`)
- Homework-specific pytest tests
- Public status document update

## 2026-09-28 — Separating the module from main

- Tools: `display_name` dropped (HW-D03 note). `course.schema.json` restored
  to Chen's version plus only the `tools` block; the `course.yaml` template
  restored to Chen's version exactly. Framework tests pass again (42/42).
- **HW-D08 recorded:** the module carries out the framework's D-031g rename
  (`answer` → `model_answer`) ahead of roadmap step 5.
- **HW-D09 recorded:** homework items get their own agent,
  `homework-item-writer`. The framework's `assessment-writer.md` is restored
  to Chen's version exactly; the new agent follows its craft sections by
  reference.
- `/write-items` reduced to a 4-line guard that hands homework to
  `/create-homework`; everything else is Chen's original.
- **HW-D10 recorded:** formats belong to the framework. The item schema is
  now Chen's file plus optional fields and the D-031g rename, with no new
  format rules. `item-code.md` reframed as the Coding-class template; the
  numeric, multiple-select and true-false templates now sit at their final
  framework paths for direct approval or removal during review.
- **HW-D11 recorded:** module decisions and open questions renumbered to
  `HW-D01`…`HW-D11` and `HW-Q01`…`HW-Q05` (mapping in `_devlog/README.md`).
- **Framework docs linked (Decision 8, option B):** Chen's Q-026 marked
  resolved by HW-D01, Q-029 update note, a cross-reference note in his
  decisions log, the Assessment row and `model_answer` entry in
  `FRAMEWORK-SPEC.md`, and two ledger rows in `ROADMAP.md`.
- **`install.md` removed (Decision 9):** the branch is the install. README,
  spec file map and handoff task 1 updated to describe the branch layout.
- **Teacher docs (Decision 10, option A):** homework added to the root
  `CLAUDE.md` (vocabulary, `HW01` id, 3 commands), `GETTING-STARTED.md`
  (section 6, `tools` setting) and `README.md` (status), each marked
  `homework-module` and stating that validation is not built yet.
- **HW-D12 recorded:** every homework write goes through `classkit write`;
  overwrites only for changes approved at a gate.
- **HW-D13 recorded:** homework is optional. Rule states added to spec
  §7.2 (19 consistency, 1 completeness); config files created on first
  `/create-homework`, not by `scaffold course`.
- **Vocabulary (Decision 13):** banned words removed from module files. The
  interviewer's `Topic` input is now `Subject`; "question" kept only where it
  means a Guiding Question, an open question, a research question, or
  something asked of the teacher.
- **HW-D14 recorded:** numeric answer units renamed `units` → `measurement_units`.
- **HW-D15 recorded:** `/create-homework` renumbered to the spec's 13 steps,
  Gate 1 given its four outcomes, continuous run between the gates stated.
- **HW-D16 recorded:** `schemas/homework-defaults.schema.json` added, plus rule
  `homework_defaults_consistent` (21 rules in total).
- **HW-Q06 logged:** where homework is graded and what must stay hidden
  depends on class and purpose (VPL, manual, none); linked to Q-002.
- **`dev/homework/ROADMAP.md` added:** phase position, implementation plan
  (steps H0–H7, moved from the handoff) and a per-decision ledger. It sits
  outside `_devlog/` so it survives the devlog's removal at release.
- **Roadmap review fixes:** "homework is optional" scoped precisely (config
  rules still run when their file exists); `SCHEMA_FOR` rows moved to
  `validate.py`; H6 renamed to integration tests (the agent pipeline is
  exercised only by the first real homework); remaining "task list" pointers
  now go to `ROADMAP.md`; branch/merge wording removed from module docs.
- **Audience separation:** teacher-facing homework instructions
  (`create-homework.md`, root `CLAUDE.md` teacher note, `GETTING-STARTED.md`
  §6) no longer depend on `dev/homework/` documents; root `README.md` keeps a
  developers-only link to the spec.
- **Developer guide:** framework `dev/CLAUDE.md` gains a tree line and a marked
  "Homework module" section (design, status, history, inventory, integration
  point, rules for changing homework files). Chen's inventory is unchanged.
- **HW-D17 recorded:** `/review-homework` removed (not part of the intended
  flow; it also borrowed the framework's unit-oriented `course-critic`).
  Re-review before reuse kept as HW-Q07.
- **HW-D18 recorded:** tool-dependent items skipped (never invented tool
  output); every skipped item gets a teacher aid (Research: references and a
  short summary; tools: expected approach), with no-invented-resources rules.
- **HW-D18 correction:** the teacher aid is returned in the solver report and
  shown at Gate 2; it is not saved (storage is HW-Q06).
- **HW-D19 recorded:** `item-critic` checks material fit against what students
  were assigned; the writer revises items, never learning materials.
- **HW-D20 recorded (scope only):** homework document export — a student Word
  document and a separate teacher answers document — is designed in the module.
- **HW-D21 recorded:** the framework's item bank is the single question bank;
  overviews are generated, usage history derived. HW-Q08 logged (id capacity,
  provenance — proposals for Chen).
- **HW-D22 recorded:** `classkit bank` generates the overview on demand;
  human output is the default, JSON is the stable agent contract, declared
  and actual use stay separate, and no file is stored unless requested.
- **HW-D23 recorded:** an agent creates the student and teacher Word documents
  after Gate 2, with a leak check; both stay editable, agent edits go through
  the bank first. Pipeline is now fourteen steps.
- **HW-D24 recorded and tightened:** Word documents are saved outside the
  repository or in a dedicated untracked output directory. An inside-repo
  destination is checked with `git ls-files` and `git check-ignore`; only its
  exact anchored path may enter `.git/info/exclude`.
- **HW-D25 recorded:** `answer_release` dropped; the teacher decides about
  publishing solutions outside the pipeline. 20 validator rules remain.
- **HW-D26 recorded:** versions are targeted at Guiding Questions from a quiz
  report (label, targets, items; `quiz_report` source required);
  `homework_versions_fair` replaced by `homework_versions_targeted`, still 20
  rules. Quiz reports are aggregated only; no student data in the repository.
- **HW-D27 recorded:** item counts per class (`default_class_counts`) replace
  the fractional class mix; shared and per-version counts asked separately for
  targeted homework; `homework_defaults_consistent` checks counts, classes and
  budget. Still 20 rules.
- **HW-D28 recorded:** per-item tools in the manifest (`item_tools`), several
  per item, programming languages included; Chen's item schema unchanged.
  Two existing rules extended; still 20.
- **HW-D29 recorded:** `prerequisites` dropped with its rule
  `homework_prerequisites_precede`; 19 validator rules remain.
- **HW-D30 recorded:** Word documents laid out from
  `homework-document.yaml` (course title, instructor, semester, title with
  homework number, due date, submission instructions, header/footer, logo,
  language/direction, font); manifest gains optional `due_date`.
- **HW-D31 recorded:** `focus_notes` flow from the interview into the plan and
  Gate 1 only; `due_date` is collected and approved before the manifest is
  written, never added during document generation.
