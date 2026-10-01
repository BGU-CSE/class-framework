# Cold-start handoff

For a new agent session, or a different coding agent, or a human collaborator picking this up.

## Read in this order

**Start with the two primary documents** — they describe the current state directly. The devlog is
chronological, and several decisions supersede earlier ones, so reading it first gets the current
state wrong.

1. `../VISION.md` — why the project exists, what it produces, how it is developed.
2. `../FRAMEWORK-SPEC.md` — what the framework must contain (Core is specified; later phases named).
3. `../ROADMAP.md` — the phases, and the implementation ledger: what is actually built.

Then, for history and what is still open:

4. `00-brief.md` — the original brief.
5. `01-decisions.md` — what's already settled, with rationale. **Do not relitigate locked decisions.**
6. `02-progress.md` (last block) — where we stopped.
7. `03-open-questions.md` — what's unresolved.

## Current state — 2026-10-01 (after Avin's hand test of steps 0–2b)

**Avin hand-tested steps 0–2b on real material** (CLRS 4e, its instructor's manual and solutions,
syllabus docx, three decks): `../reviews/manual-test-step-0-2b.md`, findings F-01 … F-27 and P-1 … P-4.
Mechanics held; the classifier was the strongest part. **We are going through the report with Avin
one item at a time.**

- **Decided — D-040 (design, not built):** `source/private/` (gitignored; committed index only, full
  text in gitignored `materials/private-text/`); `audience: student | instructor` with an
  `instructor_material_cited` **alert** and a hard refusal at export; a missing private source is
  "not on this machine", removal explicit; scaffold writes `course/.gitignore`;
  `private_material_committed` (warn); **`classkit doctor`** — `validate` judges the course (same on
  every clone), `doctor` this machine. Written into spec §2.2, §3.1, §8.4, §8.7, §9, §1.1 (Exports).
  Interim warning in `GETTING-STARTED.md`: don't commit book PDFs yet.
- **Also decided with Avin, all added to D-040** (spec and ledger updated):
  - F-11/F-15 — **two-format duplicates are no longer detected** (reverses part of D-035); exact
    copies still merge silently; `material merge` optional; agents cite the deck over its PDF.
  - F-13 — **links are not harvested** from materials; only `links.md` / `add-url`.
  - F-17 — `units: all` for course-wide material.
  - F-19 — the coverage report is persisted, `materials/coverage.md`, stating its scope; **partial
    material is the normal case**: a `unit_map` in the syllabus, units planned incrementally
    (`/plan-units 4 5`, step 3), the course level from evidence or the teacher, never from memory.
  - F-21 — one resource-kind vocabulary; `slides`/`notes` path kinds now, the rest in step 4.
  - F-24 — a refusal shows the diff against a fresh extraction, by anchor.
  - F-26 — `material_locator_in_text` (warn) over Markdown bodies; locators always fully qualified.
  - P-2 — invariant 5's scope is the framework's commands and agents; `classkit write --diff`.
- **Plain fixes (no design question)** — proposed to Avin; build in 2c unless he objects: F-01, F-02,
  F-03/F-09/F-10 (pypdf noise; verify fontTools), F-06 (docx text boxes) with F-08 (a low-yield /
  empty-slide count per material), F-07 (OMML equations), F-12 (metadata titles like `manual.dvi`),
  F-14 (time estimate), F-18 (MANUAL-TESTING: ingest before scaffolding a unit), F-20 (template says
  "fails"), F-23 (pre-flight names what changed), F-25 (after a refusal, `validate` names
  `--keep`/`--overwrite`), F-27 (note in docs: choose `--overwrite` once after F-06 is fixed).
  P-1 (a loosely worded instruction bent gate 1) stays a known limit of prompt-level gates (D-030).
- **Then:** build D-040 and the report's fixes as one step ("2c", fresh session + review as before),
  then step 3.

## State after step 2b's review — 2026-10-01 (kept for history)

**Steps 0, 1, 2a and 2b are built and independently reviewed.** Suite: **173 tests**, green.
Ledger: 51 built, 5 in progress, 91 not started — `../ROADMAP.md` is authoritative.

- **Step 2b — ingest (D-035, spec §8.7).** Session 28 built it (gap report
  `../reviews/impl-gaps-step-2b.md`); Session 29 applied the review (`../reviews/impl-review-step-2b.md`)
  and Avin's decisions, **D-039**:
  - `classkit ingest [--preflight]` turns `materials/source/` into `materials/ingested/M<NNNN>-slug.md`
    with anchors (`## Slide N`, `## Page N` — physical pages — own headings), plus
    `materials/manifest.yaml`. Stable ids, incremental, resumable; hand edits refused and asked
    (`--overwrite` / `--keep`, exit 3).
  - **`material-classifier` is read-only** (Read, Grep, Glob — no Bash). It returns a YAML block;
    `/ingest` shows it, applies the teacher's corrections, records it with
    **`classkit material apply`** (all or nothing). Merges only on the teacher's confirmation.
  - **`classkit ingest` logs every run that changes something** (`--why`; `/ingest` passes
    `--no-log` and logs its own steps).
  - **Book citations carry the book's coordinates in `note`** — section, exercise/question number,
    printed page — because `page-N` is the physical page.
  - Ratified: G-2, G-4, G-5, G-8. G-22/G-26 left until the hand test.
- **Next:** Avin hand-tests `/ingest` on real, messy materials (`../MANUAL-TESTING.md`, "Step 2b") —
  the check no review can do; the classifier prompt has never run. Then step 3 (`/plan-units`, with
  D-032). Step 3 must also: point `curriculum-architect` at `ingested/` (G-30); add a gated step that
  **re-maps materials' `units`** to the approved unit map, and decide how a hand-corrected hint is
  protected (D-039).
- **Pre-decided for later steps — don't re-argue:**
  - a goal's `est_minutes` is optional, and a missing one makes the session budget *unverifiable*
    (step 4);
  - step 4 adds `answer` to `LOCATOR_FIELDS` (one line), and moves `goals[].paths[].ref` to
    `paths[].ref` with D-020;
  - step 4: agents citing books give section / exercise / printed page in `note`; proposed advisory
    rule — a locator to a `textbook` material with no `note` warns;
  - an `open` item's rubric becomes an advisory rule (step 5);
  - a unit's `objectives` stays schema-required, deliberately;
  - agents keep or lose `Bash` as each is rewritten (G-4) — the classifier lost it because it reads
    the most untrusted text.

## State after step 2a — 2026-09-29 (kept for history)

**Steps 0, 1 and 2a are built, and 2a has been independently reviewed.** Suite: **99 tests**, green.
Ledger: 33 built, 3 in progress, 101 not started — `../ROADMAP.md` is authoritative.

- **Step 2a — validation re-founded (D-037) and the course log (D-036).** Only integrity findings
  are errors; `alert` exists and prints first; the teacher overrides any rule in `course.yaml`
  `rules:` and accepts single exceptions with `accepted:` in front matter (counted, never
  invisible). `classkit log` appends to `LOG.md`, which `scaffold course` starts.
- **Its review, applied as D-038:** a missing `reason` in `accepted:` and a mistyped rule code are
  both *advice*, never schema errors (`accepted_without_reason`, `unknown_rule`); the write path
  gained an append mode and the log goes through it; the documented `accepted:` example uses a rule
  that exists today (`in_class_missing`, "holiday week", in `unit.md`). Session 27 in
  `02-progress.md`; reports in `../reviews/impl-gaps-step-2a.md` and `impl-review-step-2a.md`.
- **Not built yet, deliberately:** agent/command wiring (log each approved step; never add
  `accepted:`) lands as each is rewritten; `syllabus_missing` and the coverage alerts are step 3;
  `guiding_question_assessed: off` is step 5.
- **Pre-decided for later steps — don't re-argue:** a goal's `est_minutes` is optional and a missing
  one makes the session budget *unverifiable* (step 4); an `open` item's rubric becomes an advisory
  rule (step 5); a unit's `objectives` stays schema-required, deliberately.
- **Next: step 2b — ingest (D-035, spec §8.7).** A fresh session from the spec with a gap report
  (`../reviews/impl-gaps-step-2b.md`); then an independent review **given the same scope block as
  the implementer** (`impl-review-step-2b.md`); then Avin hand-tests `/ingest` on real, messy
  materials — the check no document or code review can do. Then step 3 (`/plan-units`, with D-032).

## Earlier state — 2026-09-10

**Implementation has started.** Steps 0 and 1 of the plan in `../ROADMAP.md` are built and
committed; the suite is 36 tests, green. `dev/ROADMAP.md`'s ledger is ticked: 13 of 90 rows built.

- **Step 0 — the overwrite-safe write path (D-031b).** `src/classkit/write.py`: `write()` returns a
  `refused` outcome rather than raising, so a caller that ignores the return value still cannot
  destroy a teacher's file. `classkit write PATH [--from FILE] [--overwrite] [--dry-run]` is the
  agent-facing surface (exit 3 = refused). `scaffold.write_new()` now rides on it. Specified as
  spec **§8.6**. **Caveat:** every writing agent still declares `Write`/`Edit` in its front matter,
  so it can bypass the path — the guarantee is structural only once those tools come off, which no
  ledger row yet says (gap G-4).
- **Step 1 — the syllabus (D-021, D-031d).** `classkit scaffold course` now writes
  `syllabus/syllabus.md`: goal, `CO1`/`CO2`, prerequisites, reserved `assessment`, `workload`
  commented out. New `schemas/syllabus.schema.json`; `Course.syllabus` / `Course.outcomes` in the
  model; schema-checked; `syllabus_workload_missing` (warn). A fresh scaffold validates with **zero
  errors** and that one warning.
- **All 16 gaps from `../reviews/impl-gaps-step-0-1.md` are now closed** (Sessions 21 / 21b). The
  three that needed Avin: **G-15 → D-032** (rendering a syllabus for people to read defers to
  Exports, but `syllabus.md` itself must be a complete **Bologna descriptor** — adds optional
  `level`, `course_type`, `offered`, `teaching_methods`, `reading`); **G-12 + G-9 → D-033** (rules
  now declare which course *state* they judge — *consistency* rules always run, *completeness* rules
  like `outcome_coverage` only once units on disk == declared units and are reported as **skipped**
  until then; plus `syllabus_missing` as an error). **G-4** (agents still hold `Write`/`Edit` and can
  bypass the write path) is a ledger row now: each agent drops those tools in the step that touches
  it.

## What was next — 2026-09-29 (before step 2a; kept for history)

1. **Steps 0–1 were hand-tested by Avin** in a clean clone (after a two-week break) — reported fine.
2. **Step 2 is next: ingest + the course log.** Its design is now settled (Q-028 → **D-035**, spec
   §8.7; course log **D-036**, spec §8.8). Order was debated: Claude proposed doing step 3 first;
   Avin correctly insisted on ingest first, because the materials layout is the input contract for
   every later agent, and a teacher never reaches step 3 without step 2.
3. **Validation re-founded (D-037):** the teacher is the authority. Only *integrity* findings
   (references to things that don't exist) are errors; everything pedagogical is advice — `warn`, or
   `alert` for coverage — and a teacher can accept any exception. Fold this into step 2, which
   touches the validator anyway.
4. **Then step 3** (`/plan-units`), folding in D-032 (Bologna syllabus fields).

**How implementation sessions are run:** a *fresh, context-free* session, working from
`../FRAMEWORK-SPEC.md` alone, which doubles as a test of the spec's self-containment claim (D-026).
The kickoff prompt pattern and the required "spec-gap report" deliverable are described in Session
18's block in `02-progress.md`; the two reports so far are in `../reviews/`.

## Earlier state — 2026-08-27

- Working dir `/Users/avin/Antigravity-Code/class-framework` (moved from `/Users/avin/Claude/...`
  when the project was picked up on a **different machine**). Git repo on branch `main`.
- **Machine setup:** Python is python.org 3.13; `pip install -e ".[dev]"` works. A local `.venv`
  (gitignored) is the cleaner option to keep `classkit` out of global site-packages. Tests pass (14).
- **Working in vertical slices now** (D-022, Session 13): design → implement → test → update one
  slice at a time. Order: **Core** (course init, syllabus, outcomes, units, study sessions, in-class,
  *and* the entry quiz end to end) → **Assessment** (homework, programming assignments, exams) →
  **Exports** (Gem builder + PPTX) → **Metrics** (later) → **Lifecycle** (much later). See ROADMAP's
  "Build plan" section.
  - **Core content model is locked:** `answer` field on guiding questions (**D-019**); study paths →
    per-session pool, budget sums per-question `est_minutes` (**D-020**); **Syllabus** top layer
    `syllabus/syllabus.md` (Bologna-style) with Course Outcomes `CO1…` (**D-021**). All **design
    only** — nothing in schema/validator/templates/agents yet. The **implementation ledger** in
    ROADMAP.md is authoritative for what exists vs. is merely designed; a `locked (design)` decision
    needs a ledger row in the same commit.
  - Also **D-023** (a question has a recorded `answer` *or* `defer_to_class: true`, a pre-class
    thinking prompt resolved by an in-class activity) and **D-025** (`est_minutes` honesty is critic
    judgment, aided by the time-constants as an *advisory yardstick*). Both earlier open items closed.
  - Dev-doc reorg: spec/roadmap/log moved under `dev/`; the spec is now `FRAMEWORK-SPEC.md` (**D-024**).
  - **Core spec is finalized, consolidated, and restructured** (D-026, D-027). `dev/VISION.md` holds
    the *why* — the driver is **AI-native course development**, not mechanical validation (that is a
    feature); course-as-software-project is the means. `dev/FRAMEWORK-SPEC.md` holds the *what*,
    top-down: scope/phases → framework architecture → the Core phase → content model, flows,
    invariants → §8 normative reference (exact fields, IDs, rules, time model, methodology
    contract). A memory-less agent can implement/verify Core from the spec alone. Fields not yet in
    `schemas/` are tagged **(target)**; the ledger says what's built.
  - Avin reviewed it and four changes followed (**D-028/029/030**): the activity→guiding-question
    link is relaxed to a warning with a **capped** total of unmapped in-class minutes (invariant 4
    reworded); a **`syllabus-designer`** agent, run in one flow with `curriculum-architect`; a
    **command interaction protocol** (§5.2 — stepwise with approval gates, never overwrite without
    permission, revise rather than regenerate; invariant 5 reworded); and a new **§3.2 "The shape of a
    flipped course"** stating the 150/100/50 structure and the goal of each part.
  - **Independently reviewed** (Session 19): an outside agent reviewed the spec — verdict *yes with
    changes*, review kept at `dev/reviews/core-spec-review-01.md`, all findings adopted as **D-031**
    (a)–(i). Biggest: the entry quiz is now written *before* the lesson plan (+ a new
    `activity_item_reference` rule closing a silent dangling-reference hole), and never-overwrite is
    **enforced in `classkit` code rather than by prompt**.
  - **Next: implement Core.** *(Started — see "Current state" above.)* No open design items remain beyond the optional Q-027 minors. Work the
    ledger rows in `dev/ROADMAP.md` by layer — schemas → validator → templates →
    agents/skills/commands → tests — keeping the suite green at each step. Then re-derive `README.md`
    and `GETTING-STARTED.md` from the spec. Q-026 (Assessment slice) comes after.
  - **Known doc debt:** `README.md` still says every activity must reference a guiding question
    (contradicts D-028) and `GETTING-STARTED.md` does not describe the stepwise workflow (D-030).
    Both have ledger rows. Avin's principle: the README should be *derived from* the spec.
- **Phases 0 and 1 are built**: schemas, methodology, templates, scaffold, validator (14 passing
  tests at the time; 36 now), plus the agent layer — 7 agents, 2 skills, 6 commands,
  `GETTING-STARTED.md`.
- Remote is `github.com/BGU-CSE/class-framework`, **private**. Transferred from the personal
  account `chenavin` on 2026-08-25 (see Q-020); GitHub redirects the old URL, but local clones
  should still `git remote set-url` to the new location.
- **The agent layer has never been run on a real course.** Expect the prompts to need real
  revision after the first one. This is Phase 2 and it is where the useful information is.
- `defaults/time-constants.yaml` contains **placeholder numbers** (Q-005), and the validator does
  not even use most of them yet (Q-024). The feasibility check is only as honest as hand-entered
  `est_minutes` — right now that is arithmetic over a guess, worse than no check because it looks
  like verification.
- **FRAMEWORK-SPEC.md scope:** the framework itself (content model, components, agents, metrics,
  lifecycle), **not** the development process (merges, a developer's teacher-vs-developer hats). Keep
  process out of FRAMEWORK-SPEC.md.

## The two things most likely to be got wrong

1. **Framework/course separation (D-002).** This is a joint project with multiple teachers and
   multiple courses. Never put course-specific content into the framework tree. Avin's pilot
   course (*Intro to Data Structures and Algorithms*) is a test subject, not the product.
2. **The flip is about dependency, not just relocation.** Moving lecture content to video and
   keeping the class hour as a lecture is the failure mode. The 1-hour session must consume
   the output of the 2 home hours — entry tickets, misconception data, unfinished exercises.

## Working agreements with Avin

- **Be honest, rigorous and unbiased — no reflexive agreement** (2026-09-29, now in the root
  `CLAUDE.md` for both hats). Avin noticed a pattern of "good call" / "good catch" and quick
  concessions. Assess on the merits, name the cost of each decision *before* it is made, and when
  conceding say what argument changed your mind.

- Propose a plan before building. He'll critique and clarify.
- He answers direct questions directly — ask them.
- Keep this `_devlog/` current; it is the continuity mechanism, deleted before release.
