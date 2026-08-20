# Cold-start handoff

For a new agent session, or a different coding agent, or a human collaborator picking this up.

## Read in this order

1. `00-brief.md` — what we're building and why.
2. `01-decisions.md` — what's already settled. **Do not relitigate locked decisions.**
3. `02-progress.md` (last block) — where we stopped.
4. `03-open-questions.md` — what's unresolved. Q-001 is blocking.

## Current state — 2026-08-20

- Working dir `/Users/avin/Claude/class-framework`. Git repo on branch `main`.
- **Phase 0 is built and tested**: schemas, methodology, templates, scaffold, validator,
  14 passing tests. See `README.md` and `CLAUDE.md`.
- **Committed locally, never pushed.** No remote is configured; repo visibility undecided (Q-016).
- **No agent layer yet** — that is Phase 1. `CLAUDE.md` states this so no agent assumes otherwise.
- `defaults/time-constants.yaml` contains **placeholder numbers** (Q-005). The validator's
  feasibility check is only as honest as those constants.

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
