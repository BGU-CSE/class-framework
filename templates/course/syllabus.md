---
# The syllabus — the course-level top layer (D-021, D-043). /plan-syllabus drafts it from
# your materials; you revise it in conversation or by hand, and approve it. Unit work then
# builds on what you approved. Best effort, not a form: only `goal` and `outcomes` are
# required — leave out what nobody knows yet.
#
# FRONT MATTER holds what tools and agents USE. The BODY below holds what only people read
# (the catalogue description, teaching methods, policies), in your institution's order.
# Identity — title, code, institution, instructors, textbooks — lives in course.yaml and is
# not repeated here.

# One paragraph: what this course is for.
goal: "TODO"

# COURSE OUTCOMES — the roof of the coverage chain. What a student who passes can DO:
# "Analyse the running time of a recursive algorithm" is an outcome; "Recursion" is a
# subject label. Every Unit Objective rolls up to at least one outcome. Two are scaffolded,
# to match the scaffolded unit; a real course has as many as it genuinely delivers.
outcomes:
  - id: CO1
    statement: "TODO"
    bloom: understand
  - id: CO2
    statement: "TODO"
    bloom: apply

# THE UNIT MAP — the whole semester, before most units exist: number, title, a line on
# what it covers, and the materials the plan rests on. It decides which units the course
# has and in what order; /plan-units then plans the units named, as their material arrives.
# unit_map:
#   - number: 1
#     title: "Asymptotic analysis"
#     summary: "Growth of functions; O, Ω, Θ; analysing loops."
#     evidence: ["M0007#slide-1", "M0003#page-63"]

# WORKLOAD — optional, so the syllabus can be drafted before credits are settled;
# `classkit validate` warns while it is absent. No credit system is assumed.
# workload:
#   credits: 5
#   credit_system: "ECTS"
#   total_hours: 150

# Course-level prerequisites: free text, or the codes of other courses.
prerequisites: []

# READING — a `textbooks` key from course.yaml where the book is listed there, else free text.
# reading:
#   required: ["CLRS"]
#   recommended: ["Kleinberg & Tardos, Algorithm Design, ch. 1-2"]

# GRADING — drafted from your old syllabus or from your answers, never invented. Nothing
# checks it: approving it is your call. `description` is optional.
# assessment:
#   - { type: exam, weight: 60 }
#   - { type: homework, weight: 40, description: "six problem sets; the lowest is dropped" }

# APPROVAL — written by `classkit approve syllabus` (date and hash), or by you by hand
# (`approved: {on: 2026-10-05}`). Editing afterwards is normal; `classkit status` says
# "edited since". Agents never write it.
---

<!--
The body is what people read — what you upload to the university. Its sections follow your
institution's form: /plan-syllabus mirrors your old syllabus when one is ingested, and uses the
default skeleton below otherwise. Add, rename, reorder or delete sections freely. These HTML
comments are notes for you; delete them when you like.
-->

# Syllabus

## Course description

<!-- The catalogue description: a short paragraph a student reads when choosing courses. -->

## Aim

<!-- The narrative version of `goal`: what the course is about, who it is for, and what a
student can do at the end that they could not do at the start. -->

## Learning outcomes

<!-- The prose around the outcome list in the front matter, which is the one unit objectives
reference: how the outcomes fit together, and what is deliberately out of scope. -->

## Level, type and when offered

<!-- E.g. undergraduate, year 2; compulsory for the major; autumn semester. -->

## Prerequisites

<!-- What a student is assumed to arrive with, and where they were meant to acquire it. -->

## Teaching methods

<!-- How the course runs. A flipped course: each week's unit is short at-home study sessions
built around guiding questions, then one class meeting that builds on that study rather than
repeating it. The numbers — sessions, minutes — come from the methodology named in course.yaml. -->

## Schedule

<!-- Week by week, from the unit map in the front matter. -->

## Workload

<!-- Credits and student hours, consistent with the `workload` block above. -->

## Grading

<!-- The components and their weights, consistent with `assessment` above; the rules that go
with them (late work, minimum grades, what a missed quiz costs). -->

## Reading

<!-- Required and recommended reading, consistent with `reading` above. -->

## Policies

### Use of AI tools

<!-- What students may and may not use AI for in this course, and how to acknowledge it. A course
that gives students an AI study path (a Gem) needs this section most. -->

### Attendance and academic integrity

<!-- Your institution's rules, and anything specific to this course. -->

## Staff and office hours

<!-- Who teaches the course, and how and when to reach them. -->
