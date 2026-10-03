---
description: Draft, revise and approve the syllabus — goal, Course Outcomes, the unit map, workload, grading, and the descriptor
argument-hint: "[optional: what to change, or what to focus on]"
---

Establish the course's syllabus, `course/syllabus/syllabus.md` — the top layer every unit builds
on, and often the document the teacher uploads to the university. The **syllabus-designer** agent
drafts it **best effort** from the evidence the course has; the teacher revises it, in conversation
or by hand, and approves it. The milestone is an **approved** syllabus — not a perfect one: unit
work builds on what was approved, and the syllabus may keep changing all semester.

**How this command behaves.** It runs in steps. At each step: say what you are about to do, do only
that, show the result, and **wait for the teacher's approval or correction** before the next one.
The gates live here, between steps — a subagent cannot ask the teacher anything, so the agent
returns its questions and you ask them. Every approved step is logged with `classkit log`. Never
write a file directly: the agent returns text, and `classkit write` (which refuses to overwrite
without consent) puts it on disk.

---

## Step 0 — Where the course stands.

```bash
classkit status
```

Show it to the teacher. Then read `course/course.yaml` and the recent entries in `course/LOG.md`.

- **Materials not ingested, or no coverage report** (`materials/coverage.md`): say so, and suggest
  `/ingest` first — the draft is only as good as its evidence. If the teacher wants to go on
  anyway, go on.
- **The syllabus is already a draft or approved:** this run is a **revision** (§5.2 rule 3) — go to
  step 3 with what the teacher wants changed (`$1`, if given; otherwise ask). Re-drafting from
  scratch is only on the teacher's explicit word, and still goes through step 2's diff.
- **Not started** (the scaffolded placeholders): steps 1 → 4.

Run `classkit doctor` and note which private materials are **index-only on this machine** — the
agent must be told (a book's table of contents is in its index, so this is rarely a problem).

## Step 1 — Evidence and open questions.

Run the **syllabus-designer** agent with task **`evidence`**. Tell it which private materials are
index-only here, and anything the teacher said they care about (`$1`).

Show the teacher what it returns: the evidence it found and how far it reaches, the form it will
mirror (the old syllabus's sections, or the default skeleton), what it can already see, and its
**open questions** — each with what the draft will do if it stays unanswered.

If the agent found **no evidence that spans the course** (no old syllabus, no table of contents, no
deck series), say so plainly: the unit map and the outcomes must then come from the teacher. Ask for
the units, in order, with a line each. Do not let a draft be built from memory as though it were
fact.

**Wait.** Collect the teacher's answers; "leave it TBD" is a valid answer. Then log:

```bash
classkit log "/plan-syllabus, step 1 approved" --changed "evidence: M0002 (old syllabus), M0003 (book index), coverage.md" \
  --why "<the teacher's answers that shape the draft — credits, grading, units — in a line>"
```

The answers are worth logging even though no file changed yet: next year's revision reads why the
syllabus says what it says.

## Step 2 — A full draft.

Run the **syllabus-designer** with task **`draft`**, giving it the teacher's answers **in their own
words** and the index-only list. It returns a report and the complete file in one ````markdown
block.

Write the file through the write path — its content exactly as returned:

```bash
classkit write course/syllabus/syllabus.md <<'SYLLABUS'
---
goal: "…"
…
SYLLABUS
```

**It will exit with code 3** when the file already has content — always true here, since scaffold
wrote the placeholders. Nothing is written. Then:

- if step 0 said **not started**, the file holds only the scaffolded placeholders: tell the teacher
  so (the refusal quotes the opening) and, on their go-ahead, write again with `--overwrite`;
- otherwise the teacher has content there — show `classkit write course/syllabus/syllabus.md --diff`
  with the same content, and write with `--overwrite` only on their word.

Run `classkit validate`. **Fix what the draft caused** — a schema error, a locator that does not
resolve (`material_locator_in_text`) — by correcting the draft and writing it again (`--diff`, then
`--overwrite`), and say what you fixed. Expect `syllabus_workload_missing` if workload is TBD:
that is information, not something to fix. Never add `accepted:` or change `rules:`.

Show the teacher:

1. the agent's overview and **where each part came from**;
2. the outcomes and the **unit map** as a table — the outcomes-against-units table, and any outcome
   no unit builds;
3. **what is still open** — every TBD, every field left out, every guess;
4. that the file is on disk, `course/syllabus/syllabus.md`, to read and edit by hand as they like.

**Wait.** Then log:

```bash
classkit log "/plan-syllabus, step 2 approved — draft" --changed "syllabus drafted: goal, CO1–CO6, unit map (13 units), grading; TBD: credits" \
  --why "<the evidence it rests on, and the teacher's main decisions>" --file syllabus/syllabus.md
```

## Step 3 — Revision, as many rounds as the teacher wants.

Each round: the teacher says what to change. **You revise it yourself, in this conversation**
(D-044) — you have what the teacher said, and an agent sent off again would start cold, re-read
everything and lose that. **Load the `writing-a-syllabus` skill** before the first round: it is the
standard the draft was written to, and its **Revising** section is how you change it. **Re-read the
file first** — the teacher may have edited it by hand, and those edits are theirs.

Run the **syllabus-designer** with task **`rework`** only when the teacher asks for it, or when the
change is structural: the unit map restructured, the body re-mirrored to a different form, a
re-draft from new evidence. Give it the teacher's request in their words.

Either way, show the change before writing it:

```bash
classkit write course/syllabus/syllabus.md --diff <<'SYLLABUS'
…the revised file…
SYLLABUS
```

On the teacher's OK, write it with `--overwrite`, run `classkit validate` and fix what the change
caused. Log each approved round:

```bash
classkit log "/plan-syllabus, revision approved" --changed "CO3 reworded; U07 and U08 swapped" \
  --why "<why the teacher wanted it>" --file syllabus/syllabus.md
```

Offer **`/review-syllabus`** (optional) once a full draft exists: an independent critic reads what
neither of you wrote. Its findings come back here as revision requests — only the ones the teacher
picks.

## Step 4 — Approval, when the teacher says so.

The teacher decides when the syllabus is good enough to build on — at this gate, or later in
conversation ("approve the syllabus"). Never approve on your own, and never propose approval as a
formality: say what is still TBD, so they approve knowingly.

```bash
classkit approve syllabus --why "<in a line: what was approved, and what is knowingly still TBD>"
```

It records `approved: {on, hash}` in the syllabus's front matter through the write path and logs
the approval itself — no separate `classkit log`. `classkit approve syllabus --diff` shows the change
first, if the teacher wants to see it. Show `classkit status` afterwards: the syllabus now reads
"approved".

Tell the teacher:

- **Edits after approval are normal.** Nothing un-approves; `classkit status` will say "edited
  since", and approving again records the new version.
- **Next:** `/plan-units N…` plans unit objectives for the units named, against this syllabus — the
  units with material first.
- **Uploading to the university:** for now, copy from `syllabus.md` — the body is written for that.
  A formatted document is a later export.

---

**Later runs.** Run `/plan-syllabus` again at any time — next semester, or when the course changes.
It starts from the approved syllabus and revises it (step 3); it never regenerates what was
approved unless the teacher asks.
