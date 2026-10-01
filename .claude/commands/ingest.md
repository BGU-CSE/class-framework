---
description: Read the teacher's existing course materials and report what the course actually covers
argument-hint: "[optional: what to focus on]"
---

Turn the teacher's existing materials into something every later agent can read and cite, then
report what the course actually is — before anything is designed.

The materials are in `course/materials/source/`, in any state: one folder of everything or a tidy
tree, any formats, duplicates included. Links are in `course/materials/source/links.md`.
**Nothing in `source/` is ever modified, moved or deleted** — by you, by an agent, or by a tool.

**How this command behaves.** It runs in steps. At each step: say what you are about to do, do
only that, show the result, and **wait for the teacher's approval or correction** before the next
one. The gates live here, between steps — a subagent cannot ask the teacher anything. Every approved
step is logged with `classkit log`. Never write a file directly: the tools below are the only way
anything is recorded.

First read `course/course.yaml` and the recent entries in `course/LOG.md`, so you know what was
ingested and decided last time.

**Private material.** Files the teacher must not commit — a published textbook's PDF, a solutions
manual — go in `course/materials/source/private/`, which `course/.gitignore` keeps out of git. For
each, ingest commits only an **index** (its pages or slides with their labels, no body text) and
writes the full text to `course/materials/private-text/`, on this machine only. Never move a file
into or out of `private/` yourself; suggest it, and the teacher moves it.

---

## Step 0 — Check this machine.

```bash
classkit doctor
```

It is read-only, and each line that needs action names the fix. Show the teacher every `ACTION`
line — above all a missing or ineffective `.gitignore`, which would let private material be
committed — and fix nothing yourself: anything that changes a file is the teacher's call. `note`
lines are information. Remember which private materials are **not on this machine** ("index only
here"): you pass that on in step 3. The pre-flight below does not repeat these checks.

If doctor lists a private source as not on this machine and the teacher says it is **gone for
good**, remove it on their confirmation (only then — on a TA's clone a missing book is normal):

```bash
classkit material remove M0005
classkit log "/ingest, M0005 removed" --changed "M0005 marked removed" --why "<what the teacher said>" \
  --file materials/manifest.yaml
```

## Step 1 — Pre-flight. No processing.

```bash
classkit ingest --preflight
```

Show the teacher the report: files by format, slides and pages, how many are private, the links
in `links.md`, what changed since the last ingest (by name and id), exact copies (merged
automatically), what cannot be read and why, and the time estimate.

- If `source/` is empty and `links.md` lists nothing, **stop**. Ask the teacher to add their
  syllabus, slides or notes first. Do not invent a course.
- If files cannot be read, say what would fix each (export to PDF; install pandoc or LibreOffice;
  OCR a scan). The teacher may fix them first or go ahead without them.

**Wait for approval to convert.**

## Step 2 — Convert.

```bash
classkit ingest --no-log
```

`--no-log` because this command writes its own, fuller log entry below; run by hand, `classkit
ingest` logs itself. Only new or changed sources are converted; an interrupted run resumes. Show the summary: what was
added (with ids), updated, moved (same id), and removed (marked, not forgotten). Links are recorded
only from `links.md` — nothing is harvested from inside slides or documents.
A private material is written twice: its index to `ingested/` and its full text to `private-text/`
(this machine only). A `full text` line means only this machine's copy was written — nothing
committed changed, so it is not part of the log entry.

**If it exits with code 3**, some files may hold **edits made by hand** — an ingested file, or a
private material's full text — and replacing them would lose those edits. Each refusal says why
(edited, and its source changed; or a full text made from another version of the source). For each
one, show the teacher their edit (`git diff` on a committed file, the preview in the output for a
full text, which git does not track) and ask: replace it with a fresh extraction, or keep it? Then
run exactly what they chose:

```bash
classkit ingest --no-log --overwrite M0007    # replace the edit
classkit ingest --no-log --keep M0007         # keep the edit; mark the changed source as seen
```

Never choose for them.

Log the approved step:

```bash
classkit log "/ingest, conversion approved" --changed "M0001..M0023 ingested (…); M0004 moved; …" \
  --why "<what the teacher added and why>" --file materials/manifest.yaml
```

## Step 3 — Classify.

Use the **material-classifier** agent. Tell it which ids are new or updated this run, **tell it which private materials are index-only on this machine** (from step
0), and pass on anything the teacher said they care about (`$1`). It has no tool that writes or
runs anything: it **returns** a classification table with the same values as a YAML block —
including each material's `audience`, with a reason for every `instructor` — any published book it
noticed outside `private/`, two-format relations it noticed ("M0012 is the PDF of M0007"), links
inside materials that look like course resources, and the coverage report for step 4.

Show the teacher the classification table and **ask for corrections — and ask them to confirm each
`audience: instructor`** (a solutions manual, a past exam): that is what keeps it from being cited
to students. If the agent flagged a published book outside `private/`, tell the teacher; moving it
is their decision (then run `classkit ingest --no-log` again, which turns its committed copy into an
index). Then record the block —
with the teacher's corrections applied to it — in one call. It is all or nothing: if it is rejected,
fix the entry it names and run it again.

```bash
classkit material apply <<'YAML'
- id: M0007
  kind: slides
  units: [U03, U04]
  audience: student
- id: M0012
  kind: exam
  units: []
  audience: instructor
YAML
```

**Two formats of one material** (a deck and its PDF export) stay two materials, and you do not ask
about them: both are valid to cite. Pass the agent's remark on as information — later agents cite the
deck. `classkit material merge ID --into ID` exists, optional, for a teacher who asks for it; never
prompt it.

**Links the agent noticed** inside materials (the course Gem in a deck): show them, and add one only
if the teacher says so — `classkit add-url URL --note "…"`, then `classkit ingest --no-log` records it.

Then log:

```bash
classkit log "/ingest, classification approved" --changed "kinds, units and audience set for M…" \
  --why "…" --file materials/manifest.yaml
```

## Step 4 — Report what the course covers.

Present the agent's report: what the course covers, in the order taught, with its weight; where it
is thin; the volume reality check; ordering problems; what you need from the teacher; and a
proposed unit map for `/plan-units`, clearly marked as a proposal. Cite materials by locator
(`M0007#slide-3`), never by a page or slide you have not seen in the ingested file.

Run `classkit validate`. Nothing should cite materials yet, but `materials_not_ingested` must now be
silent; if it is not, say why.

When the teacher has read the report, log it:

```bash
classkit log "/ingest, coverage report reviewed" --changed "coverage report; proposed unit map" \
  --why "<the main finding — e.g. 'weeks 7–9 thin; volume ~1.5× the budget'>"
```

---

**Later runs.** Run `/ingest` again whenever material is added or changed. Only what is new or
changed is converted; a renamed or moved file keeps its id, so nothing that cites it breaks.
To add a link: `classkit add-url URL --note "…"`.
