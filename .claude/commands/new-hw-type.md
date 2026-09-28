---
description: Add a new homework type (item class) to this course. Teacher describes it, agent drafts the entry, teacher approves.
argument-hint: "[type-name] [short-description]"
---

Add a new item class named **$1** to the course's homework type taxonomy,
based on the description **$2** (or interview the teacher if either is
missing).

An item class is a pedagogical bundle — typical time, tool policy, and
Bloom range — that the teacher references when planning homework. Adding
a class is a per-course operation; no framework change needed.

1. **Ground.** Read:
   - `course/assessments/item-classes.yaml` — existing classes; the new
     one must not collide by name
   - `course/assessments/homework-defaults.yaml` — the `default_class_mix`
     block, which will get a new line
   - `course/course.yaml` — declared tools; the new class's
     `default_tools` must reference tools declared there

   If `item-classes.yaml` or `homework-defaults.yaml` does not exist yet,
   create it from its template in `templates/course/` through
   `classkit write` before continuing (HW-D13).

2. **Invoke the `interviewer` agent** with:
   - **Subject:** "a new item class called $1" (or "a new item class" if $1
     is missing)
   - **Grounding files:** the three files listed above
   - **Shape example:** one of the existing entries in
     `item-classes.yaml` (pick one closest in kind — Practicing for a
     no-AI class, Research for an investigation-style class)
   - **Pre-filled:** `{name: $1, description_hint: $2}` if either arg
     was given

   The interviewer returns a completed item-classes entry, plus its
   `follow_ups` list.

3. **Decide whether a writing skill is needed.** This decision stays in
   the command — it's a workflow choice, not part of the interview.
   Rough rule: yes if the class has specialized concerns the base
   `homework-item-writer` doesn't know (Coding → test-writing guidance,
   Research → source-citation guidance); no if the class is a simple
   task envelope (DIY, Practicing).

   If yes, invoke `interviewer` a second time with:
   - **Subject:** "a writing skill for the $1 item class"
   - **Grounding files:** the drafted class entry from step 2, and one
     existing skill file (e.g. `.claude/skills/writing-code-items/SKILL.md`)
     as the shape example
   - **Pre-filled:** the class name and description

   The interviewer returns a drafted skill file. It carries
   `status: draft` in its front matter — the flag signals the skill
   should be improved through use before being trusted as load-bearing.

4. **Show the change set to the teacher.** All proposed changes together
   in one message:
   - The new `item-classes.yaml` entry
   - The new line in `default_class_mix` (defaulting to 0)
   - The drafted skill file, if any

   Teacher approves, edits inline, or rejects.

5. **On approval, write the files atomically** — either all changes land
   or none do. Write through `classkit write` (HW-D12): the two YAML files
   already exist, so they need `--overwrite`, which the teacher's approval
   of the change set in step 4 covers; the new skill file is written plainly.
   - Append to `item-classes.yaml`
   - Append to `default_class_mix` in `homework-defaults.yaml`
   - Create `.claude/skills/writing-<slug>-items/SKILL.md` if drafted

6. **Validate.** Run `classkit validate` and confirm no rules broke.

7. **Report** to the teacher: the class name, files updated, and — if a
   skill was created — a note to read it once and edit as needed. The
   class is available to `homework-planner` on the next `/create-homework`.

**Do not modify existing classes** — this command only adds. Editing an
existing class is manual for now (a future `/edit-hw-type` could
formalize it).

**One class per invocation.** If the teacher describes several, ask
which to add first.
