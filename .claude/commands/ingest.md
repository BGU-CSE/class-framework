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

---

## Step 1 — Pre-flight. No processing.

```bash
classkit ingest --preflight
```

Show the teacher the report: files by format, slides and pages, links, exact duplicates (merged
automatically), suspected duplicates (they will be asked), what cannot be read and why, and the
time estimate.

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
added (with ids), updated, moved (same id), removed (marked, not forgotten), and the links found.

**If it exits with code 3**, some ingested files were **edited by hand** and their source has since
changed. For each one, show the teacher their edit (`git diff` on the file, or the preview in the
output) and ask: replace it with a fresh extraction, or keep the edit? Then run exactly what they
chose:

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

## Step 3 — Classify, and confirm duplicates.

First list the suspected duplicates:

```bash
classkit material duplicates
```

Then use the **material-classifier** agent. Tell it which ids are new or updated this run, give it
the suspected pairs, and pass on anything the teacher said they care about (`$1`). It has no tool
that writes or runs anything: it **returns** a classification table with the same values as a YAML
block, proposed same-material merges with its evidence, and the coverage report for step 4.

Show the teacher the classification table and **ask for corrections**. Then record the block —
with the teacher's corrections applied to it — in one call. It is all or nothing: if it is rejected,
fix the entry it names and run it again.

```bash
classkit material apply <<'YAML'
- id: M0007
  kind: slides
  units: [U03, U04]
YAML
```

**Ask the teacher to confirm each proposed merge.** Merge only what they confirm, into the material
whose anchors to keep (a deck over its PDF export):

```bash
classkit material merge M0012 --into M0007
```

Then log:

```bash
classkit log "/ingest, classification approved" --changed "kinds and units set for M…; M0012 merged into M0007" \
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
