# Brief — Homework module for the class-framework

## What this module is

The Homework feature for the class-framework. It adds a first-class homework
content type (its own manifest schema, its own on-disk location), a third
axis on items (`item_class` — pedagogical envelope), and a multi-agent
pipeline (`/create-homework`) that plans, writes, critiques, and solves
items with two teacher gates.

## Why it exists

The base framework specifies the **Core** phase — course initiation,
syllabus, units, at-home study sessions, in-class hour including the entry
quiz. Assessment (homework, programming assignments, exams, grading scheme)
was deferred to a later phase.

This module implements the homework portion of Assessment. Exams and
grading scheme remain deferred.

## Timeline

The module's design phase ran September 2026, produced thirty-two decisions
(HW-D01 through HW-D32) and eight open questions (HW-Q01 through HW-Q08), and
was reviewed across multiple audit rounds. See `02-progress.md` for the
detailed log.

The design is complete and internally consistent. Implementation (Python
runtime, scaffolding, validator rules, tests) has not started. See
`../ROADMAP.md` for the implementation plan, and `04-handoff.md` for
implementation notes.

## Scope

**In scope:**
- Homework as a first-class manifest content type
- Item classes as a per-course taxonomy (DIY, Practicing, Coding, Research
  as pilot defaults; teachers may add more)
- The `/create-homework` pipeline with plan → gate → write → review → gate
  → report flow
- Tool declarations as course-declared open strings
- A general-purpose `interviewer` agent (usable beyond homework)
- Class-based dispatch for evaluation (persona attempt, execute, skip,
  custom)
- Time-variance awareness on items

**Out of scope (deferred):**
- Exam confidentiality — Q-002 still open in framework
- Grading scheme — not yet designed
- Autograding infrastructure beyond design (sandbox is HW-Q05)
- Moodle export (the Word documents are in scope, HW-D20)

## Key design commitments

1. **The item schema stays shared** with the base framework. Homework items
   live in the shared item bank, tagged with `usage: homework`. See HW-D01.
2. **The three axes are independent.** Format (answer shape), usage
   (context), and item_class (pedagogy) never encode each other.
3. **Homework is a manifest that references items.** Never a copy or a
   duplication.
4. **Adaptation creates a new item id.** In-place mutation of shared items
   is forbidden.
5. **Two teacher gates.** Plan approval (Gate 1) and final approval (Gate 2).
6. **Cap and surface, don't converge.** Critic and solver loops cap at 3
   iterations; deadlocks surface to the teacher, they don't silently
   resolve by lowering standards.

## Where the module fits in the framework

The framework's phases (from `FRAMEWORK-SPEC.md`):

| Phase | Status |
|---|---|
| Core | Specified |
| **Assessment (homework part)** | **Specified by this module** |
| Assessment (exams, grading) | Deferred |
| Exports | Deferred |
| Metrics | Deferred |
| Lifecycle | Deferred |
