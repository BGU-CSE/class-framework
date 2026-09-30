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
"stepwise, with your approval" rule.

1. **Ground.** Read:
   - `course/course.yaml` and the methodology
   - `course/syllabus/syllabus.md`
   - `course/units/*/unit.md` for the units the teacher named
   - `course/units/*/sessions/*.md`
   - `course/assessments/items/`
   - Any prior `course/assessments/homework/HW*.md`
   - `course/assessments/homework-defaults.yaml`, `item-classes.yaml` and
     `homework-document.yaml`

   **First homework in this course?** If any of these files is missing, create
   it from its template in `templates/course/`
   through `classkit write` (new files, no overwrite), tell the teacher
   they were created and can be edited, then continue (HW-D13). Homework
   is optional, so a course only gets these files once it uses homework.

2. **Interview via the `interviewer` agent** with:
   - **Subject:** "the spec for the next homework"
   - **Grounding files:** the list above
   - **Shape example:** a prior `HW0N.md` if one exists, otherwise
     the fields the manifest schema expects (`units`, `purpose`,
     `total_minutes`, `source`, `items` [as a count per item class, e.g.
      "1 DIY, 1 Coding" (HW-D27), not concrete ids yet], `allowed_tools`, `collaboration`,
      `open_book`, optional `due_date`, optional `focus_notes`); when the source is a quiz report, also whether the
     teacher wants **targeted versions** (HW-D26); then the counts are
     asked for the shared items and for each version separately
   - **Pre-filled:** `{units: $1, purpose: $2}` if given

   `focus_notes` is free text for this creation run (for example, "focus on
   hashing; avoid chaining"). It is saved only in the plan file, never in the
   manifest or generated documents, and must not contain student names,
   grades, identifiers or other personal data. Ask for `due_date` here; do not
   defer it until document generation.
   If `homework-document.yaml`'s `semester` looks out of date, confirm it in
   this interview and retain the confirmed value in the plan.

   The interviewer returns a completed spec. Fields it left as defaults
   are noted in `defaults_used`; anything the teacher raised outside the
   spec is in `follow_ups`.

3. **Handle follow-ups.** For each `follow_up` the interviewer returned:
   - If it names an undeclared tool → do NOT block; suggest the teacher
     run whatever command exists for adding tools, or just note in the
     report at step 14.
   - If it names an undeclared item class → the plan cannot proceed
     with that class. Stop and tell the teacher to run `/new-hw-type`
     first, then re-run this command.
   - If it's something else (a stylistic note, a scheduling comment),
     record for the report at step 14.

4. **Plan.** Invoke `homework-planner` with the spec. It writes its internal
   plan to `course/assessments/homework/.plans/HW0N.md` and shows the
   teacher a prose brief. The plan retains `focus_notes`; the brief shows them
   explicitly together with `due_date`.

5. **Gate 1 — the teacher approves the brief.** Nothing but the plan file
   exists yet: no items, no manifest, no reuse edits are written before this
   approval. The brief includes the due date and focus notes (if any). For a
   homework with **targeted versions** (HW-D26), the brief
   shows for every version its target Guiding Questions, which items cover
   each target, and its approximate workload next to the other versions. On
   **graded** homework, versions whose workload or targets differ need the
   teacher's explicit approval of that difference; a plain "approve" of the
   brief is not enough. Four outcomes:

   - **Approve** → log it (see **Course log** below), then continue to step 6.
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
   references, not copies. Include the Gate-1-approved `due_date` when one was
   supplied. Never copy `focus_notes` into the manifest.

10. **Validate.** Run `classkit validate`. Errors are broken data — a
    reference to something that does not exist, or a Coding item set to
    `execute` without its reference solution or tests — and must be fixed
    before Gate 2. Warnings and alerts are advice (framework D-037): fix the
    ones this pipeline caused (for example `graded_requires_rubric` on a
    graded homework), and show the rest to the teacher at Gate 2. Never add
    `accepted:` or change `rules:` yourself (HW-D32).

11. **Gate 2 — the teacher approves the result.** All items and the
    manifest are on disk with `status: draft` frontmatter (written in
    steps 6 and 9). Show the teacher:
    - The final manifest as prose (item summaries, total time, item count per class)
    - Any critic or solver deadlocks — "critic thinks X, writer thinks Y,
      you decide"
    - Any validator warnings still standing after step 10
    - Any `follow_ups` from step 3 the pipeline did not resolve
    - For Research items: a note that the class has no automated key
      check and the teacher should read each item themselves, with the
      solver's `teacher_aid` — references (marked if unverified) and a
      short summary of what a strong answer covers
    - Material fit (HW-D19): items `item-critic` could not verify against
      the assigned material, and any case where the writer suggests the
      course material should change instead of the item — that choice is
      the teacher's
    - **Check by hand:** every tool-dependent item (skipped because it
      needs Wireshark, lab-only software, a provided dataset…), with the
      expected approach from its `teacher_aid`
    - For Coding items: a note that the reference solution and tests
      were executed by `item-solver` and passed (or, if they didn't,
      what failed and why the pipeline is still surfacing this)
    - An explicit list of every file created or modified in this run

    Three outcomes:

    - **Approve** → log it (see **Course log** below), then the pipeline promotes every draft file to shipped:
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
      No documents are created and defaults are NOT updated (steps 12
      and 13 are skipped). The pipeline does
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

12. **Create the documents** (HW-D23). After Gate 2 approval, create two
    Word files from the approved manifest and item files, laid out as
    `course/assessments/homework-document.yaml` says (HW-D30): course title,
    instructor, semester, the title built from `title_format` (`{number}` is
    the homework number from its id), due date, submission instructions,
    header, footer, logo, language and direction, font. The due date was
    collected before Gate 1 and written with the manifest at step 9; step 12
    never introduces or overwrites manifest metadata. Use the semester value
    confirmed before Gate 1 (with targeted
    versions, HW-D26: one student document **per version** — the shared items
    plus that version's items — and a single teacher answers document with
    every version clearly labeled):
    - a **student document** — the homework as students receive it: stems,
      choices, starter code, tools and collaboration rules; **no answers**;
    - a separate **teacher answers document** — model answers, rubrics,
      correct choices, reference solutions and tests, and the solver's
      teacher aids.

    Then run the **leak check** on every student document: confirm that none
    of the items' answer fields (`model_answer`, choices marked `correct`,
    `expected_solution`, `tests`, `rubric`) appear in it. Anything suspicious
    is shown to the teacher, never delivered silently.

    **Where to save (HW-D24).** The bank — manifest and item files — is the
    homework; the Word files are outputs. Ask the teacher where to save them.
    Any folder **outside** the course repository is fine. Inside the repository,
    use only a dedicated generated-output directory that contains no tracked
    files; never use the repository root or a broad existing directory such as
    `course/`, `assessments/`, `materials/`, or `units/`.

    Before writing inside the repository:
    1. Resolve the repository root and the requested destination. Refuse if the
       destination is not the exact dedicated directory the teacher approved.
    2. Check the destination with `git ls-files`. If the directory or either
       target document is already tracked, stop and ask the teacher to choose
       another location. Ignoring a path does not untrack it.
    3. Check the repository-relative destination with `git check-ignore`. If it
       is not ignored, add only that exact, anchored directory pattern to
       `.git/info/exclude` (local to this clone; never `.gitignore`), then run
       `git check-ignore` again to verify it.
    4. Tell the teacher what local exclusion was added. Never run `git rm`,
       alter tracked files, or exclude a parent directory to make this work.

    For later edits, ask the teacher where the files are.

    **Later edits.** Both documents stay editable by the teacher and by you.
    When the teacher asks you to change something, change the **item file in
    the bank first** (through `classkit write`, HW-D12), then update both
    documents and repeat the leak check. When the teacher edits a document
    by hand, the bank is not updated until they ask you to sync it; then read
    each change back into its item file and confirm it with the teacher.

13. **Update defaults.** Compare accepted values against
    `homework-defaults.yaml`. Fields left at the default: leave alone.
    Fields the teacher changed: update, so the next homework doesn't
    re-ask. `default_class_counts` describes an ordinary homework: update
    it only from a homework without versions, never from a targeted one. Never update on decline or partial accept — only on a full
    Gate 2 approval.

14. **Report** to the teacher in prose: which guiding questions touched,
    which items were reused vs. fresh, total time vs. declared, any
    `follow_ups` from step 3 that need their attention, anything the
    plan cut for time, where the two documents are, and the leak-check
    result.

For **graded homework**, reference answers live in different fields per format:
- `format: open` → human-readable model answer in `model_answer`; grading criteria in `rubric`.
- `format: numeric` → correct value in `model_answer` (with `tolerance` if applicable).
- `format: code` (autograded) → runnable reference in `expected_solution`; test cases in
  `tests`. `expected_solution` is what the autograder actually runs; `model_answer` is not
  used for autograded code items.
- `format: multiple-choice` / `multiple-select` / `true-false` → correct answers in
  `choices[].correct`.

All of these are in the referenced item files, whose git history is permanent. Do not
include worked solutions in the homework body. They go to the teacher answers document;
the student document is protected by the step 12 leak check. Publishing solutions to
students is the teacher's decision outside this pipeline (HW-D25).

**Targeted versions** (HW-D26). A homework built from a quiz report may have
versions, each aimed at the Guiding Questions a group of students struggled
with. Every student gets the shared items plus their version's items. The
rule `homework_version_reference` (error) checks that labels are unique and
every target is a real Guiding Question; `homework_versions_targeted` (warn)
checks that targets are in the declared units and covered, and that each
version item tests only its version's targets; `homework_source_quiz_exists`
(error) checks the quiz report source (HW-D32).

**Student data never enters the repository.** The quiz report you work from
must hold aggregated Guiding Question results only. If what the teacher gives
you contains student names, identifiers, grades or per-student answers, stop
and ask for an aggregated version; do not copy any of it into the plan,
manifest, items or report. Which student receives which version is the
teacher's record, kept outside the repository; version labels never name or
identify students.

**One homework per invocation.**

**Course log** (HW-D32; framework D-036). After each approval — Gate 1 and
Gate 2 — append one entry to `course/LOG.md` with `classkit log`, for example:

```
classkit log "HW03 plan approved" --changed "HW03 plan: 5 slots, U03-U04" --why "<the teacher's reason, or: teacher approved the plan>" --file assessments/homework/.plans/HW03.md --course course
classkit log "HW03 approved" --changed "HW03 manifest, items U03-I12, U04-I07" --why "<the teacher's reason, or: teacher approved the homework>" --file assessments/homework/HW03.md --course course
```

Log only approvals. Revisions, rejections and briefs that were only shown are
not logged. `--why` is required: use the teacher's stated reason, or the
approval itself when no separate reason was given. Name ids and course-relative
files, never student data or focus notes.
