---
description: Adversarially review a designed unit for the problems the validator cannot catch
argument-hint: "<unit number>"
---

Review unit **$1** using the **course-critic** agent.

Run `classkit validate` first and hand the critic its output, so it doesn't spend effort
re-deriving structural problems the tooling already found.

The critic looks for what the validator cannot see:

- guiding questions that are topic labels with a question mark on the end
- activities that reference the prework without depending on it — the test is *which activities
  would still work if the students had done nothing at home?*
- time estimates that pass validation while being obviously unrealistic against the actual reading
- questions whose own study paths can't get a student to the answer
- assessment that tests recall of a guiding question rather than the capability it names

Present the findings ordered by how much damage each does if shipped, separating **"this is
broken"** from **"I'd have done this differently"**.

Then ask the teacher what to fix. Do not apply the fixes automatically — this is their course, and
several of these judgements depend on knowing the students.
