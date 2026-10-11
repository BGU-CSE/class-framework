---
description: Plan the units named — each unit's objectives (each serving a Course Outcome), prerequisites and difficulties, against the approved syllabus
argument-hint: "<unit numbers, e.g. 1 2> [optional: what to change, or what to focus on]"
---

Plan the units the teacher names — `/plan-units 1 2` — **a few at a time, as their material
arrives**. For each: a summary, its prerequisites, its unit objectives (each naming the Course
Outcome it serves), and — optionally — the difficulties students meet. The **curriculum-architect**
agent drafts the plans from each unit's own material; the teacher revises them, in conversation or
by hand, and approves each one. The milestone is a **planned** unit — approved, not perfect:
`/design-unit` then builds its study sessions and class hour on it. Units without material stay on
the syllabus's map, unplanned, until it arrives.

**How this command behaves.** It runs in steps. At each step: say what you are about to do, do only
that, show the result, and **wait for the teacher's approval or correction** before the next one.
The gates live here, between steps — a subagent cannot ask the teacher anything, so the agent
returns its questions and you ask them. Every approved step is logged with `classkit log`. Never
write a file directly: the agent returns text, and `classkit write` (which refuses to overwrite
without consent) puts it on disk.

**Load the `planning-units` skill** before step 1's gate: it is the standard the agent drafts to,
and you will apply the teacher's corrections — and later revisions — to that same standard.

---

## Step 0 — Where the course stands, and which units.

```bash
classkit status
```

Show it to the teacher. Then read `course/course.yaml`, the syllabus's Course Outcomes and unit map
(`course/syllabus/syllabus.md`), and the recent entries in `course/LOG.md`.

- **Which units.** The numbers are in `$ARGUMENTS` (`1 2`, or `4-6`); anything after them is what
  the teacher wants changed or focused on. If none were given, ask — and suggest the units the
  materials reach (`materials/coverage.md`, the map's `evidence`) that are still *not started*.
- **The syllabus is not approved** (status says DRAFT or NOT STARTED): say so — units are planned
  against its outcomes and map, which may still change — and **ask whether to go on**. Do not
  refuse (D-043). If it is *approved, edited since*, mention it; that is normal.
- **A unit not on the unit map:** say so. The map is where a unit is added (`/plan-syllabus`);
  planning it anyway leaves `unit_map_mismatch` warning until the map has it. Ask.
- **A unit already planned or designed:** this run is a **revision** of it (§5.2 rule 3) — go to
  step 3 for that unit with what the teacher wants changed. Re-planning from scratch only on the
  teacher's explicit word, and still through step 2's diff. A designed unit's sessions reference
  its objectives by id: say that renumbering or removing an objective will break them.
- **A unit with no material** (coverage says "no material yet", the map entry has no `evidence`):
  say so. The agent will not plan it from memory; the teacher may give the subject in their own
  words, or plan it later, when the material arrives.
- **A unit with only the book — scope not confirmed** (D-048). Check `materials/manifest.yaml`: does
  some material with `scope` in its `roles` reach this unit (its `units` include it, or a `scope`
  material is cited in the map's `evidence`)? If only `reference` material does — the textbook,
  `units: all` — the book says what *could* be taught, not what *this teacher* teaches or how deep.
  Say "U07: book only — scope not confirmed" and offer: **wait** for the teacher's material (their
  deck or annotated notes), or **plan provisionally**, every objective then labelled
  *provisional — scope not confirmed* in the plan notes. The teacher decides; log the choice.
  (No `roles` recorded at all — an older manifest — ask the teacher which materials are theirs.)

Run `classkit doctor` and note which private materials are **index-only on this machine** — the
agent must be told.

## Step 1 — The draft plans.

Run the **curriculum-architect** agent with task **`draft`**, naming the units. Tell it which
private materials are index-only here, whether the syllabus is approved, and anything the teacher
said they care about or already told you about their students — **in their own words**.

Show the teacher, unit by unit, what it returns:

1. the **objectives against outcomes** table — and, plainly, any objective that serves no outcome,
   and any outcome the map says the unit builds that no objective serves;
2. the **prerequisites**, and anything assumed that no earlier unit teaches;
3. **the week's load** — what does not fit the methodology's budget and what the agent proposes to
   cut, make optional or move (the teacher decides), and any load spike across weeks;
4. the **difficulties**: those already known, and the agent's **proposals** — ask which to accept;
5. the agent's **questions**, each with what the plan does if it stays unanswered — always including
   what their students find hard here, unless that is known;
6. what it **guessed**, and which materials it read only by index on this machine.

**Wait.** Collect the teacher's answers and corrections; "none yet" and "leave it" are valid
answers. Then apply them to the returned files yourself (with the skill): the corrections; each
difficulty the teacher gives, as `origin: teacher`; each **accepted** proposal, as `origin:
proposed` (one not accepted is not recorded anywhere). A change too large to make here — a unit
re-planned around different material — goes back to the architect as a **`rework`**.

## Step 2 — Write each unit.

For each unit, in order:

1. **If it has no directory yet**, create it with the map entry's title (so `unit.md` and the map
   agree from the start):

   ```bash
   classkit scaffold unit 3 --title "Heaps"
   ```

   This also scaffolds the unit's study sessions and class hour as placeholders — `/design-unit`
   fills them; leave them alone.

2. **Write `unit.md`** through the write path, its content exactly as revised in step 1:

   ```bash
   classkit write course/units/03-heaps/unit.md <<'UNIT'
   ---
   id: U03
   …
   UNIT
   ```

   **It will exit with code 3** — the file always exists by now. Nothing is written.

### Step 2a — ask before writing. (A turn boundary: end your turn here.)

For each unit: if the file holds **only the scaffolded placeholders** (`statement: "TODO"`; status
said *drafted, not approved* and nobody has edited it), say so — the refusal quotes the opening;
otherwise the teacher has content there: show `classkit write <path> --diff` with the same content.
Ask for the go-ahead — one question for all the units written in this run.

**Wait for the teacher's answer.** Nothing else happens in this turn.

### Step 2b — on the go-ahead: write, check, show.

Write each `unit.md` with `--overwrite`.
Then run `classkit validate` and **fix what the plans caused** — a schema error, an outcome id the
syllabus does not declare (`outcome_reference`), a locator that does not resolve, a title differing
from the map (`unit_map_mismatch`), an objective naming no outcome (`objective_maps_to_outcome`)
unless the teacher decided to leave it so — by correcting the plan and writing it again (`--diff`,
then `--overwrite`), and say what you fixed. Report every alert and error, and count the warnings.
**Expected at this stage** — the unit is planned, not designed, so say what these are rather than
fixing them: `objective_coverage` for an objective no guiding question addresses yet (the
placeholder sessions name only the first objectives) — **it stops once the plan is approved in step
4**: a *planned* unit is not checked for it (D-047) — `guiding_question_assessed` on the placeholder
sessions, `unit_count`. Never add `accepted:` or change `rules:`.

Show the teacher that the files are on disk — `course/units/NN-slug/unit.md` — to read and edit by
hand as they like. **Wait.** Then log, once for the units written:

```bash
classkit log "/plan-units 3 4, step 2 approved — plans written" \
  --changed "U03: 3 objectives (CO2, CO4), prereq U01, 2 difficulties (1 proposed); U04: …" \
  --why "<the evidence the plans rest on, and the teacher's main decisions — what was cut, what they said students find hard>" \
  --file units/03-heaps/unit.md --file units/04-…/unit.md
```

## Step 3 — Revision, as many rounds as the teacher wants.

Each round: the teacher says what to change. **You revise it yourself, in this conversation**
(D-044) — you have what the teacher said, and an agent sent off again would start cold and lose it.
Work to the **planning-units** skill's **Revising** section. **Re-read the file first** — the
teacher may have edited it by hand, and those edits are theirs. Keep the ids; keep the `approved`
block exactly as it is.

Run the **curriculum-architect** with task **`rework`** only when the teacher asks for it, or when
the change is structural: a unit re-planned from material that has just arrived, content moved
between units, a unit split. Give it the teacher's request in their words.

A change that belongs to the **syllabus** — a new outcome an objective needs, a different title or
order for the unit — is not made here: say so, and offer `/plan-syllabus` (or make it there, in
conversation, if the teacher asks).

Either way, show the change before writing it (`classkit write <path> --diff`), write it with
`--overwrite` on the teacher's OK, run `classkit validate` and fix what the change caused. Log each
approved round:

```bash
classkit log "/plan-units, revision approved" --changed "U03-O2 reworded; U03 prerequisites: + U02" \
  --why "<why the teacher wanted it>" --file units/03-heaps/unit.md
```

An independent review of a plan is optional: `/review-unit N` on a planned unit reviews the plan.

## Step 4 — Approval, unit by unit, when the teacher says so.

The teacher decides when a plan is good enough to build on — at this gate, or later in conversation
("approve unit 3"). Never approve on your own, and never propose approval as a formality: say what
is still open (an objective serving no outcome, a prerequisite resting only on the map, difficulties
not yet known), so they approve knowingly.

```bash
classkit approve unit 3 --stage planned --why "<in a line: what was approved, and what is knowingly still open>"
```

Always pass `--stage planned` here. It records `approved: {date, stage: planned, hash}` in the
unit's `unit.md` through the write path and logs the approval itself — no separate `classkit log`.
`--diff` shows the change first, if the teacher wants to see it. Show `classkit status` afterwards:
the unit now reads "planned".

Tell the teacher:

- **Edits after approval are normal.** Nothing un-approves; `classkit status` will say "planned … —
  edited since", and approving again records the new version.
- **Next:** `/design-unit N` designs the unit — its study sessions, entry quiz and class hour — on
  this plan; approving the finished unit records it as *designed*. Plan the next units when their
  material is in.

---

**Later runs.** Run `/plan-units N` again at any time — after teaching the week (to record the
difficulties students actually met), next year, or when the material changes. It starts from the
unit's plan and revises it (step 3); it never regenerates what was approved unless the teacher asks.
