# Homework module

The Homework feature for the class-framework. Separate module, consistent with
the framework's conventions, developed in the `homework-by-shira` branch.

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

Sixteen decisions (HW-D01 through HW-D16) and six open questions (HW-Q01 through
HW-Q06) capture the design; the module's own devlog holds them.

## Module structure

The module lives in the `homework-by-shira` branch of the framework repo and
merges into `main` after approval. Its documents live under `dev/homework/`;
its runtime files sit at their normal framework paths.

```
dev/homework/                  Module documents
├── README.md                  This file
├── HOMEWORK-SPEC.md           The module specification (source of truth)
├── _devlog/                   Module's design history
│   ├── README.md              Devlog index (and old → new number mapping)
│   ├── 00-brief.md            One-page brief of what this module is
│   ├── 01-decisions.md        HW-D01 through HW-D16
│   ├── 02-progress.md         Development log
│   ├── 03-open-questions.md   HW-Q01 through HW-Q06
│   └── 04-handoff.md          Handoff notes for implementers
└── for-chen/                  Suggested framework templates (not part of the module)

.claude/                       5 agents, 4 commands, 3 skills (see HOMEWORK-SPEC §7.1)
schemas/                       3 new schemas, 2 framework schemas with small additions
templates/                     4 new templates, 2 framework templates with small changes
```

The module has **31 files**: 8 documents under `dev/homework/` and 23
runtime files. Of the runtime files, 5 change existing framework files and
18 are new. In addition, 7 framework documents carry short cross-references
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

There is no separate install step: the branch *is* the module. Merging
`homework-by-shira` into `main` puts every file in place. After merging, run
`pip install -e ".[dev]"`, then `pytest`, to confirm the framework still
validates. The Python implementation is the next phase (see `04-handoff.md`).

## Current status

- Design: **complete and reviewed**. Sixteen decisions recorded, six open
  questions logged as future work.
- Implementation: **not started**. The Python runtime (`classkit`) does
  not yet load homework manifests, item classes, or the new templates.
  Scaffolding does not create the homework files. The 21 validator rules
  are specified but unimplemented.
- Tests: **not started**. No homework-specific tests exist.

See `_devlog/04-handoff.md` for the implementation task list.
