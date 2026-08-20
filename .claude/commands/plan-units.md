---
description: Plan the semester — the unit map, unit objectives, prerequisites and sequencing
---

Plan the whole semester's structure using the **curriculum-architect** agent.

Run `/ingest` first if it hasn't been run; this command needs to know what the course currently
covers.

The architect should produce, for every unit: its subject, 2–4 unit objectives, and its
prerequisites. Scaffold any missing unit directories with `classkit scaffold unit N` before
writing.

Write only `unit.md` files. Study sessions and lesson plans are `/design-unit`'s job — leave the
scaffolded placeholders alone.

When done, show the teacher the full map as a table (week, subject, objectives, prerequisites) and
call out explicitly:

- anything cut or moved relative to the current course, and why
- any load spike — consecutive heavy weeks with no consolidation
- any unit whose prerequisites aren't satisfied by earlier units

Then run `classkit validate`. Expect warnings about missing sessions and unassessed questions at
this stage — that's normal, the units aren't designed yet. Errors are not.
