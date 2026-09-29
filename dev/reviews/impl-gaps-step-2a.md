# Implementation gap report — step 2a

**Date:** 2026-09-29
**Implementer:** Claude Opus 5.5, working from `FRAMEWORK-SPEC.md` (plus `VISION.md`, both
`CLAUDE.md` files, `ROADMAP.md`, `_devlog/04-handoff.md`). From the decision log I read only D-036
and D-037, the two this step implements.
**Scope built:** D-037 (validation re-classification, `alert`, `course.yaml` `rules:`,
`accepted:`, rule splits, `outcome_reference`, pedagogical presence out of `required`) and D-036
(`classkit log`, `LOG.md` on scaffold). Ingest (D-035) is step 2b.

Every entry is a point where the spec did not settle the answer and I decided. Nothing here was
guessed silently. **⚑ = needs a decision from the author**; the rest are recorded for the record
and, where marked, already written into the spec.

**Verdict on the self-containment claim:** mostly held. The spec said *what* clearly enough to
build without the decision log. The gaps are about **naming** (the split rules had no codes),
**mechanics** (where a unit-level finding lives, so it can be accepted), and one **internal
contradiction**: §8.2's `Req` column still said `outcomes` and `answer` are required, while §8.4 says
they must not be. One gap is a real bug the spec's own example would have hit (G-5).

---

## ⚑ Needs a decision

### G-1. The split rules had no codes (§8.4) — ⚑ confirm the names

§8.4 said `activity_references_guiding_question` and `item_reference` split, with the advisory halves
at `warn`, but named no code for those halves. Severity is per code, so a split needs new codes.

**Decided:** `activity_without_guiding_question` (names none), `activity_references_other_unit`
(names one from another unit), `item_no_correct_choice`. The original codes keep the integrity half:
an id that exists **nowhere in the course** is an error.

**Why flag it:** these names are now teacher-facing API. Teachers type them into `accepted:` and
`rules:`. Renaming later breaks their files. `unknown_rule` would warn, but it is still churn.
Cheap to rename now, costly after Phase 2. **Spec:** added to §8.4.

### G-6. Is `reason` required in `accepted:`? (§8.4) — ⚑

The spec writes `accepted: [{rule, reason}]` and marks neither as optional; elsewhere it writes
`note (opt)` for optional keys. So I read both as required, and the schema enforces that.

**The cost, stated before it is decided:** an `accepted:` entry with no `reason` is a **schema
error**, which fails `validate`. That is a shape error on a teacher's own exception, which sits a
little oddly with D-037. The case for keeping it: an acceptance with no reason is a silenced warning
nobody can later explain, and `accepted:` is where that reason lives. The log only records it when
an agent made the change. **Alternative:** make `reason` optional and add an advisory
`accepted_without_reason` warning. My recommendation is to keep it required. It is one line to
write, and the schema error names the missing key.

### G-10. `unknown_rule` is new, and departs from the mechanical line (§8.4) — ⚑

The spec does not say what happens to a rule name in `rules:` or `accepted:` that matches no rule.
Silently ignoring it is the worst outcome. The teacher believes they switched something off or
accepted it, and the entry does nothing.

**Decided:** a new rule, `unknown_rule`, at **warn**. By D-037's own mechanical line ("names
something that does not exist" → integrity → error) it should be an error. I departed from that
deliberately. The only consequence of the typo is that the entry has no effect, and that is already
visible, because the finding the teacher meant to silence still prints. Making a typo in an
exception fail the build would be the framework overruling the teacher over its own configuration.
**Spec:** added to §8.4. If the author prefers `error`, it is a one-word change.

### G-13. Who logs an accepted exception? (§8.4, §8.8) — ⚑ clarify wording

§8.4 says "each acceptance is recorded in the course log". But `accepted:` is typed into front
matter, often by hand, and `validate` is read-only. Making it write to `LOG.md` on every run would
spam the log and make a read-only check write files.

**Decided:** the validator does not log. Logging belongs to whoever *adds* the entry. An agent
adding one at the teacher's request logs it through `classkit log` (the D-037 agents row, still ⬜).
A teacher editing by hand logs it if they choose. **Spec should say:** "each acceptance an agent
adds, at the teacher's request, is recorded in the course log".

### G-19. Item `rubric` is schema-required for `open` items — pedagogical presence? — ⚑ (step 5)

`assessment-item.schema.json` requires `rubric` when `format: open` (an `allOf`). §8.2 says only
"✓ in practice for `open`". By D-037 ("schemas check shape, not pedagogy") a rubric's *presence* is
pedagogy. A tool can read an open item without one. **Left in place.** Removing it silently would
lose a check, and adding an advisory replacement is step 5's work (the entry quiz). `choices`
required for multiple-choice stays: an MC item without choices cannot be read. **Decide in step 5:**
move `rubric` to an advisory rule, or record it as a deliberate exception to the principle.

### G-20. Goal `est_minutes` is `✓` in §8.2 — shape or pedagogy? — ⚑ (step 4)

I did not touch it (step 4), but step 4's implementer will face the question G-2 answered for
`answer`. My view: a missing `est_minutes` is closer to pedagogy (a teacher who hasn't estimated
yet) than to shape. `session_budget_feasibility` can report "budget unverifiable" instead of
requiring the field. Decide before step 4.

---

## Decided, spec updated (no decision needed)

### G-2. §8.2 contradicted §8.4 on `outcomes` and `answer` — fixed

§8.2's unit-objective table said `outcomes` is `✓ (≥1)`, and the goal table said `answer` is
`✓ (≥1) unless defer_to_class`. §8.4 and D-037 say both move *out* of `required`. The normative
reference contradicted itself. I followed §8.4, because it is the later decision and states the
principle explicitly, and rewrote both `Req` cells.

Also: `outcome_reference` (in scope) cannot fire unless objectives can carry `outcomes`, a D-021
field scheduled for step 3. **Decided:** land that one schema field now, **optional**, and leave the
template and the presence alert (`objective_maps_to_outcome`) to step 3. Without it, the rule could
only fire alongside a schema error. Ledger row ticked with that note.

### G-3. Rules in the code that §8.4 no longer lists

`session_path_feasibility`, `path_estimate_missing` and `min_paths_per_goal` are the pre-D-020 rules
that step 4 renames or retires. §8.4 only gives severities for their successors. **Decided:** they
take their successors' severity, `warn`. `min_paths_per_goal` previously defaulted to *error*
because it was missing from `DEFAULT_SEVERITY`, a latent over-strictness D-037 exists to remove.

### G-5. A bare `off` in YAML is boolean `false` — bug in the spec's own syntax, fixed

PyYAML implements YAML 1.1, where unquoted `off` (and `no`) parse as `False`. So
`rules: {session_count: off}`, exactly as §8.2 and §8.4 tell a teacher to write it, **failed the
schema**. This would also have hit step 5's `guiding_question_assessed: off` in the methodology.
Found by a test, not by reading. **Decided:** `load_course` normalises `False` → `"off"` in both
`rules:` blocks. **Spec:** noted in the `course.yaml` `rules` row.

### G-7. Findings about a unit as a whole had no file to be accepted in

`session_count` and `in_class_missing` were reported against the unit *directory*. `accepted:` lives
in front matter, and a missing `in-class.md` has none to put it in. **Decided:** unit-level findings
are reported against `unit.md`, which is where they are accepted ("holiday week" →
`in_class_missing` on `unit.md`). **Spec:** §8.4.

### G-8. `course.yaml` has no front matter

"`accepted:` is a field on every artifact that has front matter" excludes `course.yaml`, so
course-level findings (`unit_count`) cannot be accepted per instance. **Decided:** that is correct.
Course-wide `rules:` covers them. **Spec:** made explicit in §8.4.

### G-9. What "a one-line count of accepted exceptions" counts

**Decided:** the number of findings suppressed, the number of entries and files, and how many
entries **no longer match anything**. A stale acceptance is harmless today, but it would silently
hide a *future* regression of the same rule in that file, so the teacher should see it. **Spec:**
§8.4.

### G-11. `DEFAULT_SEVERITY` is now complete — convention change

The old convention listed only non-error rules; anything unlisted defaulted to `error`. That default
is exactly how pedagogical rules ended up as errors (see G-3), and it made `unknown_rule` (G-10)
impossible to implement. **Decided:** every rule is registered, errors included, and reporting an
unregistered code raises. A test asserts that only the integrity rules default to `error`.
**Spec:** §2.5 and `dev/CLAUDE.md`.

### G-12. May `accepted:` suppress an integrity rule?

Silent in the spec. §8.4 allows switching an integrity rule *off* in `rules:`. **Decided:** yes,
because the teacher is the authority, with the same caveat. No change needed.

### G-14. The shape of `classkit log` (§8.8)

The spec gives an example entry, not a command. The ledger listed "date, actor, changed IDs, why,
files" as separate things, but the spec's example puts the actor *in the heading*.

**Decided:** `classkit log TITLE --changed … --why … [--file …]… [--date …] [--course …]`. The
title carries the actor and event, as in the example. `--changed` and `--why` are required, because
an entry without a *why* is what git already records. Each field is collapsed to one line so the
format stays parseable. The parser tolerates hand-written entries (no date, free lines kept as
notes). **Cost:** a teacher using the CLI for "taught U03" must still pass `--changed`. Hand-editing
the file has no such constraint. **Spec:** §8.8.

### G-15. Where the `LOG.md` header lives

**Decided:** in `log.py`, not in `templates/`. `classkit log` must create the log on a course that
predates it, without needing the framework root. Minor.

### G-16. The first log entry on a course that predates the log

Re-running `scaffold course` on an older course creates `LOG.md`. An entry saying "course
scaffolded" dated today would be false. **Decided:** the first entry lists exactly the files *that
run* created, or says everything else already existed. **Spec:** §8.8.

### G-17. `classkit log` appends; it does not go through the write path

§8.6 says every command writes through `classkit.write`. That path refuses to replace content, so it
cannot append. **Decided:** the log appends directly (it opens the file in append mode and never
rewrites it), which cannot lose content. That is the property invariant 5 protects. Creating a
missing log still goes through `write()`. **Spec:** §8.8.

---

## Scope notes (what I did not do, and why)

- **G-18. `guiding_question_assessed` stays `warn`, not `off`.** §8.4 says it is off in Core, but
  that is ledger row D-031c, in step 5, together with its replacement `unit_has_entry_quiz_items`.
  Turning it off now would leave nothing in its place.
- **G-21. Activity `guiding_questions` was relaxed ahead of D-028 (step 6).** The split's
  "names none" half is unreachable while the schema requires the field, and D-037 moves
  pedagogical presence out of `required`. The `reason` field was not added (step 6). The ledger row is 🔨.
- **G-22. The D-037 agents/commands row is still ⬜.** It was not in the enumerated scope, and the
  root `CLAUDE.md` (loaded by every session, including agents') already states the rule. It should
  land as each agent is rewritten.
- **G-23. The ledger count line was already wrong** before this session ("14 built, 1 in progress,
  88 not started" against a table of 16/1/112). It is recounted from the table.
- **G-24. Ledger rows for steps 3, 4 and 6 still said `error` / schema-`required`** for rules D-037
  demoted (`answer_reference_present`, `syllabus_missing`, `in_class_unmapped_time_cap`, `answer`
  required). They are annotated in place (struck through), so the next implementer does not follow
  the stale text.
- **Doc drift fixed:** `GETTING-STARTED.md` still said the unmapped-time cap makes "validation
  fail" (contradicts D-037), and "alerts and `accepted:` are not built yet". Both corrected.
