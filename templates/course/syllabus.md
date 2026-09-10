---
# The course-level top layer (D-021). Front matter is the machine-readable contract;
# the prose below it is for humans.
#
# Identity — title, code, institution, textbooks — is NOT repeated here. It lives in
# course.yaml, and a rendered syllabus pulls it in along with a live overview of the
# units, so the two can never drift apart.

# One paragraph: what this course is for.
goal: "TODO"

# COURSE OUTCOMES — the roof of the coverage chain.
#
# What a student who passes can DO. "Analyse the running time of a recursive algorithm"
# is an outcome; "Recursion" is a subject label. Every Unit Objective rolls up to at
# least one outcome, and every outcome must be covered by at least one Unit Objective,
# so the units together can be checked against what the course promised.
#
# Two are scaffolded to match the two objectives in a scaffolded unit. A real course
# usually has four to eight — add them here as the semester takes shape.
outcomes:
  - id: CO1
    statement: "TODO"
    bloom: understand
  - id: CO2
    statement: "TODO"
    bloom: apply

# WORKLOAD — optional (D-031d), so the syllabus can be drafted and validated before
# credits are settled. `classkit validate` warns while it is absent; fill it in and the
# warning goes. No credit system is assumed: name yours in `credit_system`.
# workload:
#   credits: 5
#   credit_system: "ECTS"
#   total_hours: 150

# Course-level prerequisites: free text, or the codes of other courses.
prerequisites: []

# RESERVED for the Assessment phase — the grading scheme, e.g.
#   - { type: exam, weight: 0.6 }
# Leave it empty in Core.
assessment: []
---

# Syllabus

## Aim

The narrative version of `goal` above: what the course is about, who it is for, and what a
student should be able to do at the end that they could not do at the start.

## Course outcomes

The list in the front matter is the machine-readable one — it is what unit objectives
reference, and what `classkit validate` checks the units against. Use this section for the
prose a reader needs: how the outcomes fit together, and what is deliberately out of scope.

## Prerequisites

What a student is assumed to arrive with, and where they were meant to acquire it.

## How the course runs

This is a flipped course: each week is one unit of about 150 minutes of student time —
roughly 100 minutes of at-home study in short sessions, and one 50-minute meeting that
builds on what was studied rather than repeating it. The exact numbers come from the
methodology named in `course.yaml`.

## Workload

Fill in once credits are settled, and keep it consistent with the `workload` block above.
