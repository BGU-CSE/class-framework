---
description: Create a homework — plan first, teacher approves, then write. Spans one or more units.
argument-hint: "[units-csv] [purpose]"
---

Create a homework covering **$1** with purpose **$2** (interview the
teacher for anything else).

Homework spans one or more units and is driven either by unit materials
or by a prior quiz report. What you take as input decides everything
downstream, so the first thing to settle is the spec — not fifteen
questions, one interview.

**Every file this pipeline writes goes through `classkit write`** — never a
raw file write (framework invariant 5; HW-D12). New files are written
plainly. Changing a file that already exists needs `--overwrite`, and only
for a change the teacher approved at a gate:

- reuse — appending `homework` to an existing item's `usage` — approved at Gate 1
- promoting drafts (removing `status: draft`) — approved at Gate 2
- updating `homework-defaults.yaml` — approved at Gate 2
- rewriting the plan file after a Gate 1 revision request

If `classkit write` refuses an overwrite that was not approved, stop and
show the teacher; never retry with `--overwrite` on your own.

**Two gates, continuous in between (HW-D15).** The teacher decides at
Gate 1 (step 5) and Gate 2 (step 11). Between them the pipeline runs without
stopping, but announces each step as it goes ("writing item 3 of 6",
"critic, round 2", "solver"). Writer, critic and solver rounds need no
separate approval. This is how this command applies the framework's
"stepwise, with your approval" rule. The steps are numbered 1–13, exactly as
in `dev/homework/HOMEWORK-SPEC.md` §4.1.

1. **Ground.** Read:
   - `course/course.yaml` and the methodology
   - `course/syllabus/syllabus.md`
   - `course/units/*/unit.md` for the units the teacher named
   - `course/units/*/sessions/*.md`
   - `course/assessments/items/`
   - Any prior `course/assessments/homework/HW*.md`
   - `course/assessments/homework-defaults.yaml` and `item-classes.yaml`

   **First homework in this course?** If either file is missing, create it
   from `templates/course/homework-defaults.yaml` / `item-classes.yaml`
   through `classkit write` (new files, no overwrite), tell the teacher
   they were created and can be edited, then continue (HW-D13). Homework
   is optional, so a course only gets these files once it uses homework.

2. **Interview via the `interviewer` agent** with:
   - **Subject:** "the spec for the next homework"
   - **Grounding files:** the list above
   - **Shape example:** a prior `HW0N.md` if one exists, otherwise
     the fields the manifest schema expects (`units`, `purpose`,
     `total_minutes`, `source`, `items` [as a slot count + class mix,
     not concrete ids yet], `allowed_tools`, `collaboration`,
     `open_book`, `answer_release`)
   - **Pre-filled:** `{units: $1, purpose: $2}` if given

   The interviewer returns a completed spec. Fields it left as defaults
   are noted in `defaults_used`; anything the teacher raised outside the
   spec is in `follow_ups`.

3. **Handle follow-ups.** For each `follow_up` the interviewer returned:
   - If it names an undeclared tool → do NOT block; suggest the teacher
     run whatever command exists for adding tools, or just note in the
     report at step 13.
   - If it names an undeclared item class → the plan cannot proceed
     with that class. Stop and tell the teacher to run `/new-hw-type`
     first, then re-run this command.
   - If it's something else (a stylistic note, a scheduling comment),
     record for the report at step 13.

4. **Plan.** Invoke `homework-planner` with the spec. It writes its internal
   plan to `course/assessments/homework/.plans/HW0N.md` and shows the
   teacher a prose brief.

5. **Gate 1 — the teacher approves the brief.** Nothing but the plan file
   exists yet: no items, no manifest, no reuse edits are written before this
   approval. Four outcomes:

   - **Approve** → continue to step 6.
   - **Revise** → the teacher says what to change; `homework-planner`
     re-plans (rewriting its plan file) and shows a new brief. Return to
     Gate 1.
   - **Show the table** → show the slot table (`#`, class, format,
     difficulty, Bloom, minutes, decision); the teacher edits slots by
     number. Return to Gate 1 with the updated brief.
   - **Reject** → stop. No items, manifest or reuse edits are written.
     Tell the teacher the plan file is left under `.plans/` for reference.

6. **Write items.** Invoke `homework-item-writer` per plan slot. Where the
   plan calls for reuse, append `homework` to the item's `usage` array
   — do not duplicate. Where the plan calls for `adapt`, the writer
   creates a NEW item id (not editing the original in place); the
   plan slot is updated to reference the new id. Files land with
   `status: draft` frontmatter until Gate 2 approves the homework.

7. **Review each item via `item-critic`.** After the writer produces
   an item, invoke `item-critic` on it. If the verdict is `pass` or
   `promote-anyway`, continue to step 8. If `revise`, feed the feedback
   back to `homework-item-writer` and loop — capped at 3 iterations per
   item. If still `revise` after iteration 3, verdict flips to
   `deadlocked` and the item continues to step 8; the deadlock surfaces
   at Gate 2 for the teacher to break.

8. **Attempt each item via `item-solver`.** After the critic loop
   settles, invoke `item-solver` on the item. Solver resolves the
   strategy (item's `evaluation_strategy`, then the class's
   `evaluation.strategy`, then the fallback; HW-D05, HW-D07). If the
   solver returns `revise`, feed feedback back to `homework-item-writer`
   and re-enter the critic loop at step 7 — capped at 3 iterations per
   item. If still `revise` after iteration 3, verdict flips to
   `deadlocked` and surfaces at Gate 2. If the strategy is `skip`, the
   solver returns `not_applicable`; record this for the Gate 2 summary.

9. **Write the manifest.** Emit `course/assessments/homework/HW0N.md`
   matching `schemas/homework.schema.json`, with `status: draft`. Item
   references, not copies.

10. **Validate.** Run `classkit validate`. On `graded` homework,
    `graded_answer_release_safe` and `graded_requires_rubric` are errors
    that block the pipeline until resolved. On `practice` homework, both
    rules do not trigger. Fix every error before proceeding.

11. **Gate 2 — the teacher approves the result.** All items and the
    manifest are on disk with `status: draft` frontmatter (written in
    steps 6 and 9). Show the teacher:
    - The final manifest as prose (item summaries, total time, class mix)
    - Any critic or solver deadlocks — "critic thinks X, writer thinks Y,
      you decide"
    - Any validator warnings still standing after step 10
    - Any `follow_ups` from step 3 the pipeline did not resolve
    - For Research items: a note that the class has no automated key
      check and the teacher should read each item themselves
    - For Coding items: a note that the reference solution and tests
      were executed by `item-solver` and passed (or, if they didn't,
      what failed and why the pipeline is still surfacing this)
    - An explicit list of every file created or modified in this run

    Three outcomes:

    - **Approve** → the pipeline promotes every draft file to shipped:
      for each fresh item file, each adapted new-id item file, and the
      homework manifest itself, strip the `status: draft` line from the
      frontmatter (or set `status: shipped` explicitly — either is valid
      per the schema; stripping is preferred for minimal diffs). Reused
      items are untouched (they were already shipped and only had
      `homework` appended to their `usage` array). Then continue to step 12.

    - **Revise specific items** → the named items go back to
      `homework-item-writer` for another writer + critic + solver loop
      (steps 6–8). Other items and the manifest keep their `status: draft`.
      Return to Gate 2 when the revised items are done.

    - **Reject entirely** → files stay on disk with `status: draft`.
      Defaults are NOT updated (step 12 is skipped). The pipeline does
      NOT auto-delete: silent deletion risks losing work the teacher
      wanted to keep. Instead, print the explicit list from above so the
      teacher can decide file-by-file:
        - Keep as draft (leave alone; excluded from shipped-homework
          validators via the `status: draft` marker — target behavior,
          see HW-D01 addendum in devlog)
        - Delete manually (`git clean` for new files; `git checkout` for
          modified items where reuse appended `usage: homework` in place)
        - Salvage later by manually stripping `status: draft` when ready

      Rationale: the draft convention (per HW-Q03) makes leftover files
      safe to leave — they're marked as work-in-progress and don't
      pollute shipped-homework validation once the Python validator is
      draft-aware (deferred build work; today the marker is documentary
      and the validator ignores it).

12. **Update defaults.** Compare accepted values against
    `homework-defaults.yaml`. Fields left at the default: leave alone.
    Fields the teacher changed: update, so the next homework doesn't
    re-ask. Never update on decline or partial accept — only on a full
    Gate 2 approval.

13. **Report** to the teacher in prose: which guiding questions touched,
    which items were reused vs. fresh, total time vs. declared, any
    `follow_ups` from step 3 that need their attention, anything the
    plan cut for time.

For **graded homework**, reference answers live in different fields per format:
- `format: open` → human-readable model answer in `model_answer`; grading criteria in `rubric`.
- `format: numeric` → correct value in `model_answer` (with `tolerance` if applicable).
- `format: code` (autograded) → runnable reference in `expected_solution`; test cases in
  `tests`. `expected_solution` is what the autograder actually runs; `model_answer` is not
  used for autograded code items.
- `format: multiple-choice` / `multiple-select` / `true-false` → correct answers in
  `choices[].correct`.

All of these are in the referenced item files, whose git history is permanent. Do not
include worked solutions in the homework body; they live in the item files and are released
per `answer_release`.

For **grouped homework**, the fairness rule `homework_versions_fair`
warns rather than errors. Decide with the teacher rather than silencing.

**One homework per invocation.**
