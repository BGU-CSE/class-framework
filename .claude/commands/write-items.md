---
description: Write assessment items for a unit — entry quiz, homework, or exam
argument-hint: "<unit number> [quiz|homework|exam]"
---

Write assessment items for unit **$1**, for `$2` (default: the entry quiz).

If `$2` is `homework`, stop this command and run `/create-homework $1` instead.
Tell the teacher that homework uses its own planning and review pipeline. Do not
continue with the item-writing steps below; `/create-homework` owns that flow.

Use the **assessment-writer** agent. Read the unit's study sessions first — every item must test a
specific guiding question, and the validator rejects items that don't.

Check `course/assessments/items/` for what already exists so you extend the bank rather than
duplicating it.

**For an entry quiz**, aim at diagnosis rather than difficulty: 3–5 short items whose *wrong*
answers tell the teacher which misconception to spend the debrief on. Keep the total inside the
entry-quiz slot in the lesson plan, and wire the item IDs into that activity's `items` list.

**For exam items** — stop and ask the teacher where they should live before writing. The course
repo is shared with collaborators and git history is permanent; exam content in it is a leak
waiting to happen. This is an open question in the framework, not a settled one.

Finish with `classkit validate`, then show the teacher the items with their distractor rationales
visible — the rationales are where the quality actually is, and they're what the teacher needs to
check against the misconceptions they see in office hours.
