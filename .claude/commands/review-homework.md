---
description: Second-pass review of a finished homework — pedagogical issues the auto-pipeline can't catch. Not part of /create-homework's default flow.
argument-hint: "[homework-id]"
---

Review the homework manifest **$1** (e.g. `HW02`) for pedagogical issues
that the auto-pipeline in `/create-homework` did not catch. This is a
manual second pass — used when the teacher wants a fresh review before
assigning, or when revisiting an older homework before reusing it.

Not part of the auto-pipeline. `/create-homework` ends at teacher gate 2;
this command is invoked separately.

1. **Ground yourself.** Read:
   - `course/assessments/homework/$1.md` — the manifest under review
   - Every item file referenced in the manifest's `items` array (and
     each version's items, if the homework is grouped)
   - `course/assessments/item-classes.yaml` — for class typical
     Blooms and descriptions
   - `course/units/*/unit.md` for each unit in the homework's `units`
     array — objectives to check coverage against
   - Any prior `course/assessments/homework/HW*.md` — to catch
     unintentional overlap with other homework
   - `course/assessments/homework-defaults.yaml` — the teacher's
     `default_class_mix` and other norms

2. **Invoke the `course-critic` agent** with a homework-review focus.
   Pass it:
   - The homework manifest and all its items
   - The homework-review checklist (below) as the criteria to apply

   Homework-review checklist — the checks `course-critic` applies:

   - **Purpose match.** Does the item set actually serve the declared
     `purpose`? A `diagnostic` homework whose items don't reveal
     misconceptions is mis-purposed. A `graded` homework whose items
     are all `DIY` is under-weighted.
   - **Class mix quality.** Is the mix pedagogically sound, not just
     numerically balanced? A homework of six `DIY` items covers the
     right count but under-uses homework time. A homework with a
     single 45-minute `Coding` item as slot 1 and five `DIY` items
     after is front-loaded oddly.
   - **Difficulty progression.** Does the item order create a
     reasonable ramp, or does it jump abruptly? Students hit a hard
     item first and lose an hour; students hit an easy item last and
     finish 20 minutes early. Neither is graded, but both signal a
     mis-ordered homework.
   - **Coverage of declared units.** Every unit in `units[]` is
     addressed by at least one item (the validator checks this
     mechanically); does the coverage feel proportional? A homework
     declaring three units but with five items on U03 and one on U01
     is nominally covering U01 and effectively skipping it.
   - **Tone and register consistency.** Do the items sound like they
     were written for the same course? Formal + casual mix reads as
     ChatGPT sludge (this is a real problem for agent-written items).
   - **Redundancy.** Are two items testing the same Guiding Question
     in the same way? One is redundant.
   - **Overlap with prior homework.** Does this homework repeat items
     or misconceptions from HW01…HW(N-1) in ways the teacher didn't
     intend? Deliberate reuse is fine; accidental reuse is a signal
     the planner missed context.
   - **For grouped homework:** do the versions genuinely differ in
     effort, or does one version look substantially harder? Fairness
     is a validator-warned concern; this is the qualitative version.

3. **Present findings to the teacher** as prose, grouped by concern.
   Not a table; not a slot-by-slot dump. One paragraph per finding
   that matters, with the specific item ids called out.

   Each finding carries a suggested action, one of:
   - `revise` — the finding is worth addressing before assigning
     (or before reusing, if this is a retrospective review)
   - `note` — worth knowing about but not blocking
   - `defer` — a real issue but not this homework's to fix (e.g.
     "the class mix defaults may need updating")

4. **The teacher decides what to act on.** This command does NOT
   revise the homework or its items. If the teacher wants changes,
   they either edit files directly or re-run `/create-homework` for a
   fresh iteration. Review and revision are separate — same principle
   as `/review-unit` versus `/design-unit`.

5. **On completion, report** to the teacher: the homework id, the
   number of findings by category, and a one-line overall verdict
   (`ship-as-is` | `minor-revisions` | `substantive-revisions`).

**Do not modify the homework file or any item file.** This command is
read-only. The absence of edit capability is what makes it useful for
review of an existing, already-assigned homework — the teacher can
run it without fear of accidentally changing history.

**Retrospective use is a real case.** Reviewing HW03 that ran last
semester before deciding whether to reuse it in HW03 this semester
is a valid workflow. The findings then feed into a `/create-homework`
adaptation next.
