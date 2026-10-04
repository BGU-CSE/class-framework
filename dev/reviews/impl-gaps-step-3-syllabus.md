# Implementation gap report — the syllabus increment ([3-syllabus], D-043)

**Date:** 2026-10-03 · **Implementer:** Claude Opus 5.5 (Session 37) · **Scope:** every ledger row
tagged [3-syllabus] (18). **318 tests, green** (+24, `tests/test_approve_status.py`).

Only the points where the spec did not say and I decided. **⚑ = needs the author**, with its cost.
"Spec updated" = already written into `FRAMEWORK-SPEC.md`.

## ⚑ For the author

**G-1 ⚑ The key `on:` is a YAML 1.1 boolean.** PyYAML reads `approved: {on: 2026-10-05}` — exactly
what §8.9 tells a teacher to write — as `{True: date}`, which failed the schema. Built: the loader
maps `True` → `"on"` and a date → ISO string (`model.normalize_approved`), and `approve` writes an
unquoted `on:`. Spec updated (§8.2). *Cost of keeping `on`:* every other YAML 1.1 reader (a future
exporter, a script) must repeat the trick. *Alternative:* rename to `date:` now, before any course
has a record — a one-line change in schema, loader, approve and spec. My lean: rename; it is cheap
only now.

**G-2 ⚑ `unit_map[].evidence` locators are not checked.** The schema takes them as strings; I did
not add them to `material_locator_resolves`, because the brief said no new validation and nothing
about the syllabus's content is an error. *Cost:* an agent's wrong or invented locator — the failure
the framework most fears — goes unnoticed until `/plan-units` follows it; the agent is told to check
anchors, and the hand test (MANUAL-TESTING) asks Avin to open a few. *Options:* (a) leave it;
(b) add the field to the existing locator check at `warn` (as prose locators are, D-040) — no new
rule code, a few lines. My lean: (b).

## Decided, no action needed

**G-3 What the hash covers.** "The file without its own approved block" — taken over the *parsed*
front matter (canonical JSON, keys sorted, `approved` excluded) plus the body, exactly. So a YAML
comment, key order or quoting is not an edit; any change to a value or the body is. A hand-written
record may sit anywhere in any style. Spec updated (§8.9).

**G-4 How `approve` writes.** The teacher's "approve" is the explicit confirmation, so
`classkit approve syllabus` writes with `overwrite` directly; `--diff` shows the change and writes
nothing (§8.9 read "`--diff`, then `--overwrite`", which would make every approval two calls). It
edits only the record's lines (comments survive), re-parses, and refuses if anything else would
differ. Approving unchanged content records nothing and logs nothing; re-approving after edits
replaces the record in place. It does not run `validate` — approved is not perfect (D-043). Spec
updated.

**G-5 "Not started".** `status` says *not started* when the syllabus is byte-identical to the
current template **or** its `goal` is empty or `"TODO"` — so a course scaffolded from the older
template (Avin's) reads right. A heuristic; it only labels.

**G-6 Unknowns in the draft.** Front matter: the field is left out. Body: a visible
`**TBD:** <what, and who decides>` — visible because the body is what gets uploaded, and an HTML
comment would vanish when rendered.

**G-7 The agent's three tasks.** `syllabus-designer` runs once per step with a task — `evidence`,
`draft`, `revise` — and returns the complete file in one four-backtick block; the command writes it.
An edit the teacher dictates exactly ("credits are 5 ECTS") the command makes itself — the teacher's
own edit (D-040's scope of invariant 5) — still shown as `--diff` before `--overwrite`.

**G-8 The first draft is always refused.** Scaffold wrote placeholders, so `classkit write` exits 3;
the command says the file holds only placeholders (when status said *not started*) and asks before
`--overwrite`, else shows `--diff`. One extra question, kept deliberately: the old template may hold
the teacher's edits under a TODO goal.

**G-9 Step 1 is logged** though no file changes: the teacher's answers (credits, grading, units) are
why the syllabus says what it says, and the critic uses the log to tell a given fact from an
invention.

**G-10 Small edits outside the rows.** `/ingest` and `material-classifier` pointed the proposed unit
map and the coverage report at `/plan-units`; they now name `/plan-syllabus` (the map is the
syllabus's, D-043). The template's body no longer states "150 / 100 / 50 minutes" — it hardcoded the
methodology (invariant 2); it now says the numbers come from the methodology.

**G-11 Staged inconsistency, until [units].** README, GETTING-STARTED and the root `CLAUDE.md` now
describe `/plan-units` as unit objectives against the approved syllabus; `plan-units.md` and
`curriculum-architect`'s body still plan every unit and the map (only the description was narrowed,
as the row said). A teacher who runs `/plan-units` before the [units] increment gets the old
behaviour.

**G-12 `status` and private material.** Materials are reconciled with `local=False`, like `validate`:
a private source on this machine is never "outstanding", so the answer is the same on every clone.
`doctor` remains where private files are reported.

## Decisions I would question — none

Nothing in D-043 looked wrong in the building. The one cost I would watch on the real course is
D-043.6's body-sections choice: the body is unchecked, so a front matter/body disagreement (the map
says 13 units, the schedule 12) is caught only by the critic.
