# Cold-start handoff

For a new agent session, or a different coding agent, or a human collaborator picking this up.

## Read in this order

1. `00-brief.md` — what we're building and why.
2. `01-decisions.md` — what's already settled. **Do not relitigate locked decisions.**
3. `02-progress.md` (last block) — where we stopped.
4. `03-open-questions.md` — what's unresolved.
5. `../DESIGN.md` — how the system works now. Read this before the decision log; the log is
   chronological and several decisions supersede earlier ones.
6. `../ROADMAP.md` — the phases, what's done, and what each remaining one is for.

## Current state — 2026-08-27

- Working dir `/Users/avin/Antigravity-Code/class-framework` (moved from `/Users/avin/Claude/...`
  when the project was picked up on a **different machine**). Git repo on branch `main`.
- **Machine setup:** Python is python.org 3.13; `pip install -e ".[dev]"` works. A local `.venv`
  (gitignored) is the cleaner option to keep `classkit` out of global site-packages. Tests pass (14).
- **Now in a design-draft pass** (Session 10): finishing a full *draft* of the design before any
  classroom testing, so the testing has a stable target. Order: content model → agent coverage →
  metrics → course lifecycle. Agenda + open items in `03-open-questions.md`.
  - **Decided this session:** guiding questions gain an `answer` field (**D-019**) — *design only;
    not yet in schema/validator/templates/agents.* Implementation is the later "fill the gaps" step.
  - **Next:** Gap 2 = Q-023 (is a Study Path per-question or a per-session route?), then Q-024/Q-025,
    then homework (Q-026).
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
- **DESIGN.md scope:** the framework itself (content model, components, agents, metrics, lifecycle),
  **not** the development process (merges, a developer's teacher-vs-developer hats). Keep process
  out of DESIGN.md.

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
