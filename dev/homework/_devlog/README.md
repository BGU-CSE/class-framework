# Homework module devlog

Design history for the homework module of the class-framework. Mirrors the
base framework's devlog structure (`dev/_devlog/`). Read `00-brief.md`
first if you're new to the module.

## Files

| File | What it holds |
|---|---|
| `00-brief.md` | One-page brief — what the module is, why it exists, its scope |
| `01-decisions.md` | Every design decision (HW-D01..HW-D16) with rationale |
| `02-progress.md` | Development log — what was done when, in what order |
| `03-open-questions.md` | Open questions (HW-Q01..HW-Q06) with framing and options |
| `04-handoff.md` | Handoff notes for the next implementer |

## Relationship to the framework devlog

The base framework's devlog at `dev/_devlog/` is the primary devlog for the
framework itself. This module's devlog covers homework-specific decisions
and questions, numbered with the module's own prefixes `HW-D` and `HW-Q`
(HW-D11). Plain `D-` and `Q-` numbers always mean the framework's own
entries (e.g. D-031g, Q-026). The module's devlog stays in `dev/homework/_devlog/`; the framework's
devlog carries only a cross-reference note.

## Reading order for a new implementer

1. `README.md` (module root) — 5 minutes
2. `HOMEWORK-SPEC.md` (module root) — 30 minutes
3. `_devlog/00-brief.md` — 5 minutes
4. `_devlog/04-handoff.md` — 15 minutes (what to do next)
5. `_devlog/01-decisions.md` (as needed, for rationale on specific fields)
6. `_devlog/03-open-questions.md` (as needed, when hitting ambiguity)

## Renumbering (2026-09-28)

Before HW-D11 the module continued the framework's numbering. Old numbers
may still appear in chat logs or reviews:

| Old | New | | Old | New |
|---|---|---|---|---|
| D-035 | HW-D01 | | D-040 | HW-D06 |
| D-036 | HW-D02 | | D-041 | HW-D07 |
| D-037 | HW-D03 | | D-042 | HW-D08 |
| D-038 | HW-D04 | | D-043 | HW-D09 |
| D-039 | HW-D05 | | D-044 | HW-D10 |
| Q-032 | HW-Q01 | | Q-035 | HW-Q04 |
| Q-033 | HW-Q02 | | Q-036 | HW-Q05 |
| Q-034 | HW-Q03 | | | |
