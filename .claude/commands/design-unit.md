---
description: Design one unit end to end — study sessions, guiding questions, study paths, and the in-class hour
argument-hint: "<unit number>"
---

Design unit **$1** completely.

Work in this order; each step depends on the one before.

1. **Ground yourself.** Read `course/course.yaml`, the methodology it names in `methodologies/`,
   the unit's `unit.md` (objectives), the units before it (so you know what students already have),
   and anything in `course/materials/source/` about this subject.

   If the unit directory doesn't exist, run `classkit scaffold unit $1` first.

2. **Home study** — use the **study-session-designer** agent. It writes the study sessions: the
   guiding questions and the candidate study paths to answering them.

3. **The meeting** — use the **lesson-planner** agent, *after* the sessions exist. It cannot plan
   the hour without knowing the questions.

4. **Assessment** — use the **assessment-writer** agent for the entry quiz items at minimum. The
   entry quiz is what makes the hour depend on the prework.

5. **Check.** Run `classkit validate` and fix every error. Warnings are advisory; read them and
   decide.

6. **Report** to the teacher: the guiding questions you wrote, what the hour does with them, any
   place you guessed because the source materials were thin, and anything you cut for time.

Do not design more than this one unit. The teacher should review unit-by-unit — the agents learn
this course's subject and level from what's already in the repo, so a reviewed unit 1 makes unit 2
better, and an unreviewed bad one propagates.
