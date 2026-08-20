---
description: Read the teacher's existing course materials and report what the course actually covers
argument-hint: "[optional: path to materials]"
---

Read the teacher's existing materials and work out what this course actually is, before anything
is designed.

Materials are in `course/materials/source/` (or `$1` if given). Read `course/course.yaml` for
context. If the directory is empty, say so and stop — ask the teacher to add their syllabus,
slides, or lecture notes first. Do not invent a course.

Produce a report, not files. The teacher approves the picture before any structure is built.

Cover:

1. **What the course covers** — the topic inventory as it exists today, in the order currently
   taught, with the weight each currently gets.
2. **Existing structure** — how many weeks, what the assessment scheme is, which textbook.
3. **Volume reality check.** This is the important part. Three lecture hours per week typically
   carry more material than 100 minutes of home study plus a 50-minute application hour. Estimate
   how much of the current content actually fits, and name what would have to be cut, made
   optional, or moved. Be specific and be honest — a cheerful "it all fits" here is how the
   home-study budget silently doubles later.
4. **Ordering problems.** Lectures can defer motivation; independent home study cannot. Flag
   anything currently introduced before the reason it matters.
5. **Gaps.** What you'd need from the teacher that the materials don't say — assumed
   prerequisites, which topics are examinable, which weeks are already known to be hard.

End with a proposed unit map (week → subject) as a suggestion for `/plan-units`, clearly marked as
a proposal for the teacher to correct.
