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

## Expected noise — do not report these as bugs

| What you will see | Why | Tracked as |
|---|---|---|
| Many `guiding_question_assessed` warnings (12 for one unit) | Only entry-quiz items exist in Core, and a short quiz cannot test every guiding question. Decided to be `off` in Core — not yet implemented | D-031c, step 5 |
| `syllabus_workload_missing` | `workload` is optional by design so a syllabus validates before credits are settled | D-031d |
| `unit_count`: "N of 13 units exist so far" | Informational while the course is being built | — |
| No `outcomes:` on unit objectives; no coverage checking | The coverage chain is step 3 | D-021, D-033 |

Anything **else**, especially any **error** on a freshly scaffolded course, is a real finding.

---

## What to do with what you find

- A defect in what was built → fix it, or note it for the next implementation session.
- Something the spec did not say → it belongs in a gap report, like
  `reviews/impl-gaps-step-0-1.md`. Gaps found by *using* the thing are worth more than gaps found by
  reading it.
- Something that works but reads badly, or does not match how you would teach → that is the
  judgement no test can make, and the main reason to do this by hand.
