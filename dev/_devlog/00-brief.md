# Project brief

**Owner:** Avin (avin@bgu.ac.il), Ben-Gurion University
**Started:** 2026-08-18
**Working dir:** `/Users/avin/Claude/class-framework`

## What we're building

An **agentic framework for building and maintaining a university-level course**, in which
a course is treated like a software project: versioned in git, structured in directories,
validated by tooling, and authored/maintained with the help of specialized agents.

A teacher clones the framework, fills in information about their existing course, and uses
the agents to (re)design it.

## The initial flagship goal

Transform a **standard in-class course** — 3 hours of lecture per week, 13 weeks — into a
**mixed / flipped classroom**:

- **2 hours/week at home** per student, per unit: acquisition of material.
- **1 hour/week in class** with faculty, focused on application: short quiz, discussion,
  critical thinking, worked examples, small-group work.

The classic failure mode this must avoid: an in-class hour that re-lectures the prework.
The class hour must *depend* on the home hours.

## Structural shape of a course

- 13 units (weeks) → each unit has topics → each topic has a lesson plan.
- Directories for homework, quizzes, exams.
- Directories for class materials (slides, textbooks, links).
- A place for syllabus, guidelines, goals.
- Agents attached to the relevant areas/tasks.

## Agent capabilities envisioned

Build question types (multiple-choice, open), make a lesson plan, make homework,
research a topic, connect to Moodle, create a Google Gem for the class or a unit.

## Collaboration context

This is a **joint project**. Avin's pilot course is *Introduction to Data Structures and
Algorithms*, but other teachers will use their own courses while the framework is being
built and designed, and may want to update agents. Framework/course separation is therefore
a hard requirement, not a nicety. See D-002.
