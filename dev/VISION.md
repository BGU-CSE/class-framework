# Vision

Why this project exists, what it produces, and how it is developed. Written for developers and
agents working on the framework. Teachers should read `../README.md` instead.

## 1. Project outcome

The deliverable is a **git repository — the framework — that a teacher clones and works in with an
AI coding tool.** It contains everything needed to develop and maintain a course that way:

- a **content model and schemas** — the structure a course is written into;
- **specialized agents** for the recurring jobs (planning units, designing study sessions, building
  the class hour, writing quiz items, reviewing the result);
- **teacher-facing commands** that orchestrate those agents;
- **skills** holding craft shared by several agents;
- **templates and scaffolding** that create a course's files;
- **validation tooling** that checks the course holds together.

A teacher adopts the framework by cloning the repository, pointing it at their own course
repository, and opening it with Claude Code (or a comparable tool). The framework is the working
environment; their course content lives in their own repository.

## 2. Motivation

Developing and maintaining a university course is repetitive, effortful, and largely unsupported. A
course is revised every year. A change of methodology means reworking a semester of material by
hand. Writing a quiz, adding a unit, revising goals, or finding material for a subject are all jobs
done manually, one file at a time.

AI should be able to carry much of that load. But a general-purpose chatbot cannot work on *a
course* — it can help write a paragraph, but it has no map of what the course is, what unit 7
contains, or what changing one goal would affect. A course that exists as a folder of slide decks
gives an agent nothing to reason about.

## 3. Approach

**AI-native course development.** Give the course an explicit structure — on disk, in git, with a
defined content model — and the course becomes something agents can operate on: navigable,
checkable, and revisable. The structure exists to make the agents effective.

Treating a course as a software project is the **means**, not the goal: version control, a
schema-defined content model, specialized agents, and automated checks. The **end** is making course
development something a teacher and an AI can do well together, and through that, better courses —
better learning and better teaching.

Because agents author the content, something has to catch what agents get wrong. That is why the
framework validates: not rigor for its own sake, but the safety net that makes agent-authored course
material trustworthy. Code verifies; agents judge. **The teacher decides.** Validation catches
what agents get wrong and informs the teacher; it never overrules a teacher's deliberate choice —
the teacher is the authority, and is responsible for what reaches students.

## 4. Scope and audience

The framework currently targets **flipped-classroom courses**. The architecture keeps the pedagogy
pluggable so it can be extended to other methodologies later, but that is an open door, not a
present claim.

It is for teachers comfortable with git and an AI coding tool — knowledgeable teachers and
developers, not every teacher.

## 5. How the framework is used

At a high level, a teacher's path through the framework:

1. **Adopt** — clone the framework, repoint it at their own (private) course repository, keeping the
   framework as a second remote so improvements can be pulled later.
2. **Initialize** — scaffold the course structure and set its configuration.
3. **Ingest** — point the framework at existing course materials and have it report what the course
   actually covers.
4. **Plan the semester** — produce the syllabus: course goal, course outcomes, the unit map, and
   each unit's objectives.
5. **Design unit by unit** — for each unit, design the at-home study sessions, the in-class hour
   built on them, and the entry quiz.
6. **Review and validate** — an independent agent reviews what it did not write; the tooling checks
   the structure mechanically.
7. **Teach, then revise** — carry what was learned into the next revision or the next offering.

Steps 3–6 are where the agents do the work. Step 1 is what makes framework improvements reach an
existing course later.

## 6. Specification and development process

**`FRAMEWORK-SPEC.md` specifies what the framework must contain** — its content model, components,
agents, validation rules, and the contracts between them. It is the source from which the framework
is implemented.

The specification is written and implemented in phases:

- **Core** — the basic framework: course initiation, syllabus, outcomes, units, the at-home study
  sessions, and the in-class hour including the entry quiz. Enough to generate and run the learning
  part of a course.
- **Later phases** extend it — assessment (homework, programming assignments, exams), exports,
  metrics, and course lifecycle.

Development is **spec-driven and iterative**: specify a phase, implement it, then test it on a real
course and update both the specification and the implementation where reality disagrees. The
specification is expected to change during development; it is a living document, not a fixed
contract.
