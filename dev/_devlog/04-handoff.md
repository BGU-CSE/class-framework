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

## Current state — 2026-08-27

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
  - **Next:** independent review of `VISION.md` + `FRAMEWORK-SPEC.md` (a review brief was drafted in
    Session 16 — update it for VISION.md and the new section numbers). Fold findings, then
    **implement Core** from the ledger rows in `dev/ROADMAP.md` (schemas → validator → templates →
    agents/skills → tests, green each step). Q-027 minors and Q-026 (Assessment) come after.
  - **Known doc debt:** `README.md` still says every activity must reference a guiding question
    (contradicts D-028) and `GETTING-STARTED.md` does not describe the stepwise workflow (D-030).
    Both have ledger rows. Avin's principle: the README should be *derived from* the spec.
- **Phases 0 and 1 are built**: schemas, methodology, templates, scaffold, validator (14 passing
  tests), plus the agent layer — 7 agents, 2 skills, 6 commands, `GETTING-STARTED.md`.
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

- Propose a plan before building. He'll critique and clarify.
- He answers direct questions directly — ask them.
- Keep this `_devlog/` current; it is the continuity mechanism, deleted before release.
