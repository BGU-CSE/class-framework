---
description: Adversarially review the syllabus for the problems the validator cannot catch (optional)
argument-hint: "[optional: what to focus on]"
---

Review `course/syllabus/syllabus.md` using the **course-critic** agent — an agent that did not write
it. Optional: `/plan-syllabus` offers it once a full draft exists, before or after approval.

This command writes nothing. Fixes go back through `/plan-syllabus` (its revision step), only the
ones the teacher picks.

1. Run `classkit status` and show it — the critic should know whether it is reading a draft, an
   approved syllabus, or one edited since approval.
2. Run `classkit validate` and hand its output to the critic, so it does not spend effort
   re-deriving what the tooling already found. Run `classkit doctor` and tell it which private
   materials are index-only on this machine.
3. Run the **course-critic** on the **syllabus** (its "Reviewing the syllabus" section), with
   anything the teacher asked it to focus on (`$1`).

Present its findings ordered by how much damage each does if the syllabus is approved and built on
— or uploaded to the university — separating **"this is broken"** from **"I would have done this
differently"**.

Then ask the teacher which, if any, to act on. Do not apply them: several depend on knowing the
students and the institution. The ones the teacher picks become revision requests in
`/plan-syllabus`, which logs them. A review that changes nothing is not logged.
