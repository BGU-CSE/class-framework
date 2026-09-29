# Homework module

The Homework feature for the class-framework. Separate module, consistent with
the framework's conventions.

## What this module adds

- A first-class homework content type with its own manifest schema
- A three-axis item model: `format` (answer shape), `usage` (context),
  `item_class` (pedagogical envelope) — the third axis is new
- A multi-agent pipeline (`/create-homework`) that plans, writes, critiques,
  and solves items with two teacher gates
- Class-based dispatch for item review (persona attempts, code execution,
  skip, custom)
- Time-variance awareness — low-variance classes (DIY, Practicing) require
  per-item time estimates; high-variance classes (Coding, Research) do not
- A general-purpose interview agent, tools as course-declared strings, and
  a hand-off from `/write-items homework` to the pipeline

Thirty decisions (HW-D01 through HW-D30) and eight open questions (HW-Q01 through
HW-Q08) capture the design; the module's own devlog holds them.

## Module structure

Its documents live under `dev/homework/`; its runtime files sit at their
normal framework paths.

```
dev/homework/                  Module documents
├── README.md                  This file
├── HOMEWORK-SPEC.md           The module specification (source of truth)
├── ROADMAP.md                 Implementation plan and ledger (what is built)
├── _devlog/                   Module's design history
│   ├── README.md              Devlog index (and old → new number mapping)
│   ├── 00-brief.md            One-page brief of what this module is
│   ├── 01-decisions.md        HW-D01 through HW-D30
│   ├── 02-progress.md         Development log
│   ├── 03-open-questions.md   HW-Q01 through HW-Q08
│   └── 04-handoff.md          Implementation notes (the plan is in ROADMAP.md)

.claude/                       5 agents, 3 commands, 3 skills (see HOMEWORK-SPEC §7.1)
schemas/                       4 new schemas, 2 framework schemas with small additions
templates/                     8 new templates, 2 framework templates with small changes
```

The module has **36 files**: 9 documents under `dev/homework/` and 27
runtime files. Of the runtime files, 5 change existing framework files and
22 are new. In addition, 7 framework documents carry short cross-references
to the module: `CLAUDE.md`, `GETTING-STARTED.md` and `README.md` at the
root, `FRAMEWORK-SPEC.md`, `ROADMAP.md`, and the framework's decisions and
open-questions logs. In the three root documents every homework addition is
marked `homework-module` (an HTML comment pair around sections, or
*(homework module)* on table rows), so a search finds all of them.

## Relationship to the base framework

**The module shares the framework's item schema** (`schemas/assessment-item.
schema.json`) rather than extending it into a homework-specific variant.
Homework-relevant fields (`item_class`, `source_ref`, `expected_solution`,
`tests`, `tolerance`, `measurement_units`, `starter_code`, `evaluation_strategy`, `status`) are added as
optional fields on the shared schema. Quiz and exam items simply don't set
them. This preserves the three-axis independence: an item can be reused
across quiz, homework, and exam contexts by having multiple values in its
`usage` array, without file duplication or schema branching. See HW-D01 and
the schema section of `HOMEWORK-SPEC.md`.

**The module adds three of its own schemas:** `homework-defaults.schema.json`
(for the teacher's learned defaults), `homework.schema.json` (for
homework manifests, a new content type) and `item-classes.schema.json` (for
the class taxonomy, a new configuration file).

**Framework replacements:** the module changes five framework files with
homework-aware versions:
- `.claude/commands/write-items.md` — adds hand-off to `/create-homework`
- `schemas/assessment-item.schema.json` — adds homework-aware optional fields
- `schemas/course.schema.json` — adds the course tools map
- `templates/assessment/item-open.md`, `item-multiple-choice.md` — add
  `item_class` field and rename `answer` → `model_answer`

Otherwise the module is additive.

## Install

There is no separate install step: the files are already at their
framework paths. Run `pip install -e ".[dev]"`, then `pytest`, to confirm the
framework still validates. The Python implementation is the next phase: the plan and
ledger are in `ROADMAP.md`, the implementer's notes in `_devlog/04-handoff.md`.

## Current status

- Design: **complete and reviewed**. Thirty decisions recorded, eight open
  questions logged as future work.
- Implementation: **not started**. The Python runtime (`classkit`) does
  not yet load homework manifests, item classes, or the new templates.
  Scaffolding does not create the homework files. The 19 validator rules
  are specified but unimplemented.
- Tests: **not started**. No homework-specific tests exist.

See `ROADMAP.md` for the implementation plan and what is built, and
`_devlog/04-handoff.md` for the implementer's notes.
