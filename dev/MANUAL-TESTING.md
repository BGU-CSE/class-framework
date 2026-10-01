# Manual testing — driving the framework as a teacher would

Automated tests build a throwaway course in `tmp_path` and check it holds together. They do **not**
tell you whether the thing is pleasant to use, whether the output reads well, or whether a teacher
following `README.md` gets where they expect. That needs a human running it in a clean environment.

This document is the procedure. It grows a section per implementation step (see `ROADMAP.md`).

Every command below was run and its output captured on 2026-09-10 against commit `b01ca57`.

## Set up a clean environment

The framework **is** the working environment: a course repo is a clone of the framework with
`origin` repointed (D-009). So a clean test environment is simply a **fresh clone in a scratch
directory** — never the development checkout, and never inside it.

```bash
cd ~/scratch                      # anywhere outside the framework checkout
git clone https://github.com/BGU-CSE/class-framework.git testdrive
cd testdrive

python3 -m venv .venv             # keep classkit out of your global Python
.venv/bin/python -m pip install -e .
.venv/bin/classkit --help         # sanity check
```

Prefix every command with `.venv/bin/`, or `source .venv/bin/activate` once.

Two things a real teacher does that you can **skip** when testing: repointing `origin` to their own
course repo, and pushing. Neither affects what you are testing, and both create a repo you then have
to delete.

**Throw the whole directory away afterwards** (`rm -rf ~/scratch/testdrive`). Never commit a scaffolded
course — invariant 1 says no course content in the framework repo, and the clone is still pointed at
`origin`.

---

## Step 1 — Initialize (`scaffold course`)

**What it should deliver:** the teacher's first contact with the framework produces a complete,
*valid* course skeleton, including the syllabus.

```bash
.venv/bin/classkit scaffold course \
  --code "202-1-2051" \
  --title "Introduction to Data Structures" \
  --institution "Ben-Gurion University" \
  --units 13
```

Expect **10 files created**, among them `course/syllabus/syllabus.md` and `course/course.yaml`.

```bash
.venv/bin/classkit validate
```

Expect **0 errors** and 2 warnings — `syllabus_workload_missing` (you have not set credits yet) and
`unit_count` (0 of 13 units so far). Zero errors on a fresh scaffold is invariant 6; an error here is
a real failure, not a nuisance.

Then add a unit and validate again:

```bash
.venv/bin/classkit scaffold unit 1 --title "Asymptotic analysis"
.venv/bin/classkit validate
```

Expect **6 files created** under `course/units/01-asymptotic-analysis/` (4 sessions + `unit.md` +
`in-class.md`), and again **0 errors**.

**Re-run scaffold to prove it never overwrites** (invariant 5):

```bash
.venv/bin/classkit scaffold unit 1 --title "Asymptotic analysis"
# → "0 created, 6 left untouched." Every file reported as `exists … (left untouched)`.
```

### What is worth your judgement here, not just green output

- **Open `course/syllabus/syllabus.md`.** Is the skeleton one you would actually want to fill in? Is
  anything a Bologna descriptor needs missing? *(D-032 already adds `level`, `course_type`, `offered`,
  `teaching_methods`, `reading` — not yet implemented, so their absence is expected.)*
- **Open a session file and `in-class.md`.** Do the TODOs tell you what to write?
- Does `validate`'s output read like something you would act on, or like noise?

---

## Step 0 — the overwrite-safe write path

**What it should deliver:** it must be *structurally impossible* for an agent to destroy your work by
forgetting to check (invariant 5, §8.6). Exit code **3** means refused, distinct from 2 (broke).

```bash
# A. new file → written
echo "hello" | .venv/bin/classkit write course/policies/test.md          # created, exit 0

# B. overwrite without permission → REFUSED, original intact
echo "DESTROYED" | .venv/bin/classkit write course/policies/test.md      # refused, exit 3
cat course/policies/test.md                                              # still "hello"

# C. ask before generating anything
echo "x" | .venv/bin/classkit write course/policies/test.md --dry-run    # refused, exit 3, nothing written

# D. explicit confirmation → replaced
echo "new content" | .venv/bin/classkit write course/policies/test.md --overwrite   # replaced, exit 0

# E. identical bytes → no-op, so re-running a command stays safe
echo "new content" | .venv/bin/classkit write course/policies/test.md    # unchanged, exit 0
```

**B is the one that matters.** If it ever writes, the guarantee is broken and that is a stop-everything
bug — the failure it prevents (silent loss of authored work) is unrecoverable.

Note the refusal message prints *what is already there*, which is what lets a command show you the
existing content and ask.

**Known limitation, already tracked (gap G-4):** agents still declare `Write`/`Edit` in their tool
front matter, so an agent *could* bypass `classkit write`. The guarantee becomes structural only when
those tools are removed, which happens per-agent in the steps where each agent is touched. So this
test proves the mechanism, not yet the enforcement.

---

## Step 2b — ingest (`/ingest`)

The test no code review can do: **your real, messy materials.** Copy (do not move) a real course's
slides, PDFs, Word files, past exams and a few odd files into `course/materials/source/` — unsorted,
with at least one deck *and* its PDF export, and one file in a format nothing reads. Then:

```bash
.venv/bin/pip install -e .                       # new dependencies: python-pptx, python-docx, pypdf
.venv/bin/classkit add-url "https://www.youtube.com/watch?v=…" --note "a real video"
.venv/bin/classkit add-url "not a url"           # rejected, exit 2
.venv/bin/classkit ingest --preflight            # counts, duplicates, unsupported, time — writes nothing
```

Then run **`/ingest`** in Claude Code and follow it through its four gates. At step 3 you should see
the classification table **before** anything is recorded, and be able to correct it (D-039).
Afterwards, by hand:

```bash
find course/materials/source -type f -exec shasum {} + | sort > /tmp/before   # snapshot source/
mv course/materials/source/<a deck>.pptx course/materials/source/renamed.pptx
.venv/bin/classkit ingest                        # "moved … (same id)", nothing re-converted
# edit one file in course/materials/ingested/, then change its source and re-run:
.venv/bin/classkit ingest                        # REFUSED, exit 3, your edit intact
.venv/bin/classkit validate                      # materials_not_ingested until you answer
tail -12 course/LOG.md                           # each hand run that changed something: "classkit ingest", "run by hand"
```

Point one study path's `ref` at a real anchor (`"M0001#slide-2"`) and one at a made-up one
(`"M0001#slide-999"`): `validate` passes the first and errors on the second.

### What is worth your judgement here

- **Is the extraction readable?** Open a few `ingested/` files. Slides that are mostly pictures will
  be thin — is it thin enough to mislead the classifier?
- **Are the titles sensible?** They come from the first slide title or heading, else metadata, else
  the file name.
- **Did the duplicate detection catch your deck/PDF pairs — and nothing else?**
- **Are the kinds and units right?** Units are guessed before any unit map exists, from "Lecture 3"
  and the like; how often is the guess wrong? (`/plan-units` will re-map them — D-039.)
- **Do book citations in the report give section / exercise / printed page**, not only `page-N`?
- **Is the coverage report true of your course?** That is the whole point of step 2b.
- **Did anything in `source/` change?** It must not: re-run the `find … | sort` line into
  `/tmp/after` (adjusting for the file you renamed) and `diff` the two.

---

## Expected noise — do not report these as bugs

| What you will see | Why | Tracked as |
|---|---|---|
| Many `guiding_question_assessed` warnings (12 for one unit) | Only entry-quiz items exist in Core, and a short quiz cannot test every guiding question. Decided to be `off` in Core — not yet implemented | D-031c, step 5 |
| `syllabus_workload_missing` | `workload` is optional by design so a syllabus validates before credits are settled | D-031d |
| `unit_count`: "N of 13 units exist so far" | Informational while the course is being built | — |
| No `outcomes:` on unit objectives; no coverage checking | The coverage chain is step 3 | D-021, D-033 |
| A material's `kind` is `other` right after `classkit ingest` | Kind is only guessed from the format; the classifier sets it in `/ingest` step 3 | D-035 |
| Link titles are their URL or note | Metadata fetching is best-effort; offline, or a site that blocks it, gives no title | D-035 |

Anything **else**, especially any **error** on a freshly scaffolded course, is a real finding.

---

## What to do with what you find

- A defect in what was built → fix it, or note it for the next implementation session.
- Something the spec did not say → it belongs in a gap report, like
  `reviews/impl-gaps-step-0-1.md`. Gaps found by *using* the thing are worth more than gaps found by
  reading it.
- Something that works but reads badly, or does not match how you would teach → that is the
  judgement no test can make, and the main reason to do this by hand.
