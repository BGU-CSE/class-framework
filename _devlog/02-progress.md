# Progress log

Append a new session block at the bottom. Keep it factual: what was decided, what was built,
what's next.

---

## Session 1 — 2026-08-18

**Participants:** Avin + Claude (Opus 5), Claude Code in VSCode.

### What happened

- Avin described the project: an agentic framework for building/maintaining a university
  course as a git-style software project. See `00-brief.md`.
- Claude proposed an initial architecture: objectives-as-spine content model, capability-based
  agents (rather than one agent per directory), a flip pipeline
  (`ingest → plan-flip → author-prework → author-session → qa-review → export`), a validator,
  and a 5-phase roadmap.
- Claude raised 6 clarifying questions; Avin answered all of them.

### Decisions locked this session

D-001 English · D-002 framework/course separation (load-bearing) · D-003 Claude Code native ·
D-004 Moodle deferred · D-005 Google Gem · D-006 PPTX + few slides · D-008 `_devlog/`.
D-007 (objectives-as-spine) proposed, pending confirmation. Full text in `01-decisions.md`.

### Built

- `_devlog/` — this folder. Nothing else. Repo is otherwise empty; **git not yet initialized.**

### Notable design positions taken (not yet ratified)

- **Against one-agent-per-directory.** Folder-scoped agents duplicate craft — a homework agent
  and a quiz agent both need to write good MCQs. Proposal: capability agents + per-directory
  `CLAUDE.md` context files + shared skills.
- **Pedagogical policy as data, not prompt.** Home/class time split ratios, minimum assessment
  items per objective, etc. live in a versioned policy file so they're tunable and reviewable.
- **Generated artifacts separated from sources** (`build/`, `exports/` vs authored content).
- **Validation as a hook**, built in Phase 1 rather than late — this is what makes it a
  software project rather than a folder of markdown.

### Next

1. Resolve Q-001 (framework/course separation mechanism) — blocking the repo layout.
2. Avin has a **clarification to the plan** still to deliver. Wait for it before scaffolding.
3. Then: Phase 0 — repo skeleton, YAML schemas, `git init`.

---

## Session 2 — 2026-08-18

### What happened

- **Q-001 resolved → D-009.** Avin chose the two-repo model. Claude refined it: keep shared git
  history (clone + repoint `origin`, retain `framework` remote) rather than a disconnected
  duplicate, so framework updates merge in and fixes push back as branches instead of being
  hand-copied. Rejected alternatives noted in D-009: GitHub template repo (no common ancestor),
  fork (one-per-account limit breaks on the second course).
- Three binding layout constraints fell out of it: course repos *add, never edit*; the framework
  never ships files into `course/` (templates are copied in by a scaffold command); framework and
  course trees stay file-disjoint so merges are clean.
- New questions raised by D-009: **Q-007** (where course-local agent/template variants live,
  given "never edit") and **Q-008** (scaffold command scope and idempotency).

### Built

- `_devlog/` updates only. Repo still otherwise empty; **git still not initialized.**

### Next

1. Avin's clarification to the plan — still pending, still the gate before scaffolding.
2. Phase 0: repo skeleton honoring D-009's three constraints, YAML schemas, `git init`.
3. Q-007 and Q-008 need answers as part of the Phase 0 layout, not after it.

---

## Session 3 — 2026-08-18

### What happened

Avin delivered the clarification to the plan: the concrete structure of the at-home half.
Recorded as **D-010** (time model + default methodology) and **D-011** (methodology is pluggable).

- 100 at-home minutes = **4 study sessions × ~25 min**; each session carries **3–5 study goals,
  each phrased as a question** the student is expected to be able to answer; the student chooses
  their own path to the answer (class Gem, video, textbook, …).
- This is Avin's **default** methodology. Other teachers get other methodologies via their own
  designer agents → the framework defines a contract, `question-driven-25` is one implementation.

### Design shifts this caused

- **The guiding question replaces the abstract objective as the spine (refines D-007).** It is
  student-facing, directly assessable, and unambiguous about "done" in a way an abstract ULO isn't.
- **The question is the home↔class join key**, which turns "the class hour must not re-lecture the
  prework" from an aspiration into a validator rule.
- **The Gem became load-bearing** (upgrades D-005) — it is a first-class study path, must know the
  week's guiding questions, and must tutor toward them rather than answer them. Moves earlier in
  the roadmap; argues for per-unit Gems.
- **Resources attach to questions, not sessions**, with a feasibility check: ≥1 complete path per
  session within 25 min.
- **No downstream agent may hardcode 4 / 25 / 3–5** — those are methodology parameters (D-011).
- Terminology standardized to *study session* / *guiding question* / *assessment item*, resolving
  two collisions ("topic" now meant the 25-min unit; "question" meant two different things).

### Built

- `_devlog/` updates only. Repo still otherwise empty; **git still not initialized.**

### Next

1. Awaiting answers to **Q-009** (in-class 50 vs 60 min), **Q-010** (in-class per unit vs per
   study session — assumed per unit), **Q-011** (keep a thin abstract objective layer above the
   questions?).
2. Then Phase 0 scaffolding. The schema work is now the critical path: `StudySession` /
   `items[]` (D-011) is the contract every downstream agent depends on, and it must survive a
   second, non-question-driven methodology.

---

## Session 4 — 2026-08-20

### What happened

Avin answered Q-009 / Q-010 / Q-011 and supplied the canonical course vocabulary. Recorded as
**D-012**, which is now the single source of truth for terminology and structure:

- In-class session is **50 min** (Q-009); it is **per Unit**, not per Study Session (Q-010);
  **Unit Objectives are kept** as a thin abstract layer above the Guiding Questions (Q-011).
- Full model: Semester (12–13 Units) → Unit (150 min: 100 home + 50 class) → 4 Study Sessions
  (~25 min, 3–5 Guiding Questions each, with Study Paths) + 1 In-Class Session / Lesson Plan
  (built from Activities, each referencing ≥1 Guiding Question).
- Glossary fixed in D-012. Two ambiguous words are now banned: **"topic"** and bare
  **"question"** (use *Guiding Question* vs *Assessment Item*).

### New questions raised, all gating the first push or the layout

- **Q-012** repo host / name / visibility — recommend personal account, public, `class-framework`.
- **Q-013** license — recommend MIT (Apache-2.0 if contribution-back matters more than adoption).
- **Q-014** does the framework ship a synthetic example course as a test fixture? Recommend yes,
  tiny and obviously fake, under `examples/`, excluded from the scaffold — D-002 forbids real
  course content in the framework tree, but the validator needs something to run against.

Q-005 sharpened: the time-budget constants are what make the 25-min feasibility check real rather
than theater. Blocking the validator, not the first push.

### Built

- `_devlog/` updates only. Repo still otherwise empty; **git still not initialized.**

### Next

Awaiting answers on the five gating questions — **Q-012** (host/name/visibility), **Q-013**
(license), **Q-007** (course-local customization without editing framework files), **Q-008**
(scaffold scope + idempotency), **Q-014** (example fixture). Recommendations are written for all
five, so these can be ratified quickly. Then: `git init`, Phase 0 skeleton, first push.

---

## Session 5 — 2026-08-20

### What happened

Avin answered the five gating questions. Three resolved cleanly; two need follow-up.

- **Q-012/Q-013 → D-013.** GitHub account `chenavin`, repo `class-framework`, **MIT**. Visibility
  left ambiguous ("private git account") → split out as **Q-016**, defaulting to private.
- **Q-007 → D-014.** Avin's answer covered **governance**: the framework repo is
  permission-controlled (developers only, edits included); a teacher's course repo is **sovereign**
  — they may do whatever they want in it. This is a *different question* from the one Q-007 was
  asking, which was about **merge hygiene**. Resolution: D-009's "add, never edit" is **demoted
  from a binding rule to documented guidance with its cost stated** (edit freely, but
  `git merge framework/main` will then conflict on exactly those files). The framework cannot
  enforce anything inside a sovereign repo, so guidance is the honest form.
- **Q-014 → D-015.** No example course. Developers test on their own real courses.
  - *Welcome consequence:* the framework repo now needs **no `course/` directory at all** — the
    course tree is created entirely by scaffold. File-disjointness becomes structural rather than
    policed.
  - *Cost, flagged:* no fixture means no CI signal; a framework change breaks courses silently
    until teachers pull. Mitigation proposed as **Q-017** — ship *schema test fixtures* (tiny
    valid/invalid YAML as validator unit-test data), which is test data rather than an example
    course and so does not conflict with D-015.
- **Q-008** — Avin didn't follow the question; it was badly phrased and is *not* answered by Q-007.
  **Rewritten in `03-open-questions.md`** with a concrete example of what the scaffold command is
  and the two sub-decisions (granularity; create-only vs overwrite on re-run).

### New questions

**Q-016** visibility · **Q-017** testing without fixtures · **Q-018** tooling language (recommend
Python, mainly because `python-pptx` is the realistic path to D-006) · **Q-019** authoring file
format (recommend Markdown + YAML front matter for prose, pure YAML for config).

### Built

- `_devlog/` updates only. Repo still otherwise empty; **git still not initialized.**

### Next

Five open, all with written recommendations: **Q-008** (rewritten), **Q-016**, **Q-017**, **Q-018**,
**Q-019**. Then `git init`, Phase 0 skeleton, first commit for review.

---

## Session 6 — 2026-08-20 — PHASE 0 BUILT

### Decisions

- **Q-007 deliberately left open.** Governance is settled (D-014); the *update mechanism* is not.
  Interim rule now stated in README and D-014: *a teacher who wants future framework updates cannot
  edit framework files.* Revisit once a second teacher actually hits the problem.
- **Q-008 → D-016.** Scaffold covers course/unit/session/item and is create-only.
- **Q-017 closed better than proposed.** No fixture files: the test suite builds a throwaway course
  in `tmp_path` with the scaffold itself, asserts it validates clean, then mutates it to prove each
  rule fires. Side benefit — it tests the templates, so template/schema drift fails CI.
- **Q-018 / Q-019 → D-017.** Python (`classkit`); Markdown + YAML front matter for prose, pure YAML
  for config.
- **Q-016 still open** — recommended private now, public at Phase 1 (the repo still carries
  `_devlog/`). Blocks only the push.

### Built — Phase 0 complete

```
LICENSE  README.md  CLAUDE.md  .gitignore  pyproject.toml
schemas/          6 JSON Schemas: course, unit, study-session,
                  in-class-session, assessment-item, methodology
methodologies/    question-driven-25.yaml — the default, D-010 encoded as data
defaults/         time-constants.yaml (PROVISIONAL values — Q-005)
templates/        course.yaml, unit.md, session.md, in-class.md, 2 item templates
src/classkit/     frontmatter, model, scaffold, validate, cli
tests/            14 tests, all passing
```

`git init` done on branch `main`. **Not pushed** — no remote configured yet.

### Verified, not assumed

- `scaffold course` → `scaffold unit 1` → `validate` produces **0 errors** with full schema checking.
- Re-running scaffold overwrites nothing; deleting one session and re-running restores only that file.
- Deliberately breaking a course fires the right rules: dangling activity reference, infeasible
  25-min session, activities overrunning the hour, missing entry quiz, goal pointing at a
  nonexistent objective, wrong session count, disallowed goal type.
- The schema layer caught a real bug in the `course.yaml` template during testing (a commented-out
  `textbooks:` parses as `None`, not `[]`). Fixed.

### Notes for whoever picks this up

- The two failure modes that matter are now mechanically enforced, not merely documented:
  `activity_references_guiding_question` (the hour cannot revert to a lecture) and
  `session_path_feasibility` (the 2 home hours cannot be fiction).
- `defaults/time-constants.yaml` holds **placeholder numbers**. The feasibility check is only as
  honest as those constants — Q-005 is now the highest-value open question.
- No agent layer yet. That is Phase 1, and `CLAUDE.md` says so explicitly so no agent assumes
  otherwise.

### Next

1. Avin reviews the first commit; decide Q-016; create the GitHub repo; push.
2. **Q-005** — real time constants.
3. **Q-004** — pilot course materials (format + location), which gates ingest design.
4. Phase 1 — the agent layer and the flip pipeline.

---

## Session 7 — 2026-08-20 — PHASE 1: AGENT LAYER

### What happened

Avin, reasonably: *"I got a bit lost. Where are the skills we discussed — the main work of building
the class should be done by Claude Code of the teacher. Where is all this information?"*

Fair. Phase 0 built the plumbing and left the visible product missing. The ordering was defensible
(agents need a target format and a validator, or you can't tell a good unit from a plausible one)
but it was never going to *feel* like progress to the person who wants the agents.

### Built

**Teacher entry point** — `GETTING-STARTED.md`. Answers the question directly: where materials go
(`course/materials/source/`), what settings exist (`course.yaml`), which commands to run in what
order, and what the teacher still has to do themselves.

**Agents** (`.claude/agents/`):

| Agent | Job |
|---|---|
| `curriculum-architect` | Semester map, unit objectives, sequencing |
| `study-session-designer` | Guiding questions + study paths; reads the methodology |
| `lesson-planner` | The 50-min meeting |
| `assessment-writer` | Items with diagnostic distractors, rubrics |
| `topic-researcher` | Real, verified resources — read-only tools |
| `gem-builder` | Gem bundles, with exclusion rules |
| `course-critic` | Adversarial review, read-only |

**Skills** (`.claude/skills/`): `writing-guiding-questions`, `estimating-study-time`. Both are craft
used by more than one agent — putting them in skills stops the designer and the critic drifting to
different standards.

**Commands** (`.claude/commands/`): `/ingest`, `/plan-units`, `/design-unit N`, `/write-items N`,
`/review-unit N`, `/build-gem N`.

**Scaffold**: now creates `course/materials/source/` with a README explaining what to drop there —
an unexplained empty directory gets ignored, and it is the primary input to `/ingest`.

### Positions encoded in the agent prompts

- **No fabricated resources.** Stated in `topic-researcher` and `study-session-designer`. A made-up
  URL passes every check and fails a student mid-session.
- **Referencing ≠ depending on.** The critic's sharpest test: *which activities would still work if
  the students had done no prework?* The validator can enforce the reference; only a reader can
  judge the dependency.
- **Never shave estimates to fit the budget.** Called out in `estimating-study-time` as the one move
  that turns the feasibility check into theatre.
- **The Gem tutors toward the answer**, and must exclude assessment items, teacher misconception
  notes, and homework solutions — with exclusions stated out loud, since silence isn't assurance.
- **Design one unit at a time.** Agents infer subject and level from what's in the repo, so a
  reviewed unit 1 improves unit 2 and an unreviewed bad one propagates.

### Verified

`scaffold course` now creates the source README; fresh scaffold still validates with **0 errors**;
14 tests still pass.

### Honest status

The agent layer is **written but unexercised** — no real course has been built with it. Expect the
prompts to need revision after the first genuine unit. That is the next thing that will teach us
something.

### Next

1. Run `/ingest` then `/design-unit 1` on the real Intro to Data Structures materials (Q-004 —
   still need to know where they are and what format).
2. **Q-005** — real time constants. The feasibility check is placeholder-backed until then.
3. Revise agent prompts based on what unit 1 exposes.

---

## Session 8 — 2026-08-25 — Why is there Python at all?

### What happened

Avin: *"Can you remind me why we need the Python code and scripts? Can't we do it all with commands
or agents (.md files)?"*

A fair challenge, and one nobody had written an answer to — the rationale existed only in the
original plan discussion, never in the repo. Session spent answering it properly rather than
building.

### Measured, so the argument rests on numbers rather than assertion

A full 13-unit course was generated to check the scale the tooling actually operates at:

| | |
|---|---|
| Markdown files | 79 |
| Guiding questions | 156 |
| Guiding-question ID references that must all resolve | 221 |
| Validator rules | 18 |
| Python, total | 1,097 lines (462 validator, 257 scaffold) |
| Time for a full validation | **0.09 s** |

### Outcome — the answer splits in two

**`validate` stays code → D-018 "Code verifies, agents judge."** Five reasons, recorded in full:
exhaustive cross-referencing (221 references across 79 files, every run); arithmetic (hundreds of
small sums, which models approximate); testability (14 tests prove each rule fires — you cannot
unit-test a prompt, and a rule that silently stops firing manufactures false confidence);
independence (the agent that designed a unit must not certify it); and cost (0.09 s and no tokens
means it runs after every edit — a check nobody runs is not a check).

The complementary half matters as much: **agents do the judgment code cannot attempt** — is this
guiding question a topic label in disguise, would this activity work if nobody did the prework, is
8 minutes honest for 8 pages of proofs. That is why `course-critic` exists and why it is told not
to repeat the validator.

**`scaffold` is genuinely open → Q-021.** Avin is right that an agent could read a template and
write files; that is what agents do. 257 lines against: byte-identical output, create-only enforced
mechanically rather than remembered, works offline with no model call. To decide before Phase 2
starts producing real course content, since that is when an overwrite bug starts costing a teacher
real work.

### Conceded honestly

- The install tax (`pip install -e .`) is a real barrier for a non-technical colleague, paid by
  every adopter. It was glossed over when Python was chosen (D-017).
- Phase 4's PPTX export needs `python-pptx` regardless, so dropping scaffold shrinks the Python
  surface but does not remove the dependency.

### Built

Nothing. Documentation only: D-018, Q-021, this entry.

### Next

Unchanged — Phase 2 still blocked on **Q-004** (pilot course materials) and **Q-005** (real time
constants). **Q-021** now sits alongside them, and should be answered before Phase 2 writes content.

### Addendum — repo transferred to BGU-CSE (same day)

Discovered mid-push: GitHub reported *"This repository moved"*. The framework now lives at
`github.com/BGU-CSE/class-framework`, still private. **Q-020 resolved** — organization roles make
D-014's permission model implementable for the first time (Read for teachers who only clone, Write
for developers), which a personal repo structurally could not do.

All in-repo URLs updated, including the six schema `$id` fields. Local remote repointed; the old
URL still redirects, but other clones should `git remote set-url`.

Outstanding: assign the org roles, and check whether branch protection on `main` is available under
the organization's plan.

### Addendum 2 — `GETTING-STARTED.md` after the move

Avin asked whether the teacher-facing doc needed changing after the transfer. Two things, beyond
the URL that was already updated:

- **Added an access prerequisite.** The framework is private inside an org, so step 1 fails with
  `repository not found` for anyone who has not been granted Read on `BGU-CSE/class-framework`.
  Previously the clone just worked for the owner and there was nothing to say. Also spelled out
  that the teacher's own course repo must be created empty — no README, `.gitignore` or licence —
  since an initialized repo starts a second history that has to be merged.
- **Raised Q-022:** where course repos should now live. The doc still says personal account, which
  was the only option before. Org placement buys continuity and managed TA access but exposes exam
  content and its history to org owners, which pulls against Q-002. Left as the teacher's decision.

### Addendum 3 — GETTING-STARTED is written for the public state

Avin: *"The GETTING-STARTED will be given to teachers only after we make the project public. For
now it is private as we are in development mode. So write as it is public. For now, the plan is for
each teacher's course repo to be private."*

So the access prerequisite added in Addendum 2 was **removed again** — it described the development
state, not the state the document ships into. The file now assumes framework public / course repos
private, and carries an HTML comment saying so, so the note does not get re-added by someone
noticing that the clone currently fails.

**Q-022 partially answered:** course repos are private (visibility settled). Ownership — org vs
personal account — remains open, so the doc uses a neutral `<owner>` placeholder.

---

## Session 9 — 2026-08-25 — DESIGN.md

### What happened

Avin: *"I don't think we have a clear design document... The design document is for developers and
should provide an overview of the system design and flow, as well as our current status. Do we need
it? Do we have it?"*

Correct on both counts. We had four top-level docs and none of them was a design document: README is
a front door, CLAUDE.md is rules for agents editing the framework, ROADMAP is status,
GETTING-STARTED is teacher-facing.

### The sharper reason it was needed

The system's design existed **only in `_devlog/`** — 1,254 chronological, decision-shaped lines. To
reconstruct the current system you had to read 18 decisions in order *and* reconcile the ones that
overwrite each other (D-007 superseded by D-010; D-009 rule 1 amended and demoted by D-014; D-015
amended by its own addendum). A new developer doing that gets the current state wrong.

And **`_devlog/` is scheduled for deletion** (D-008, ROADMAP Phase 6). So every reason behind the
system's shape sat in a folder we had already decided to delete. `DESIGN.md` is what survives it —
that is now stated in `_devlog/README.md` as a rule: rationale worth keeping must be reflected in
DESIGN.md, because this folder is going away.

The trigger was Avin's previous question — who runs the agents and when — which had been answered in
conversation, then partially in a *teacher-facing* doc, and nowhere for developers.

### Built

`DESIGN.md`, 260 lines: the problem and the two structural failure modes; the guiding question as
the one idea everything rests on; the content model; the four layers (commands → agents → skills /
tooling → schemas) and the code-verifies/agents-judge split; control flow through `/design-unit 3`
including which orderings are load-bearing; a data-flow table; the two-repo model; extension points;
the seven invariants with reasons; and §10 "Where this design might be wrong".

Deliberately carries **no status** (ROADMAP owns that) and **no chronology** (the devlog owns that),
to stop it rotting. A documentation map at the top says where each kind of content belongs.

Cross-linked from README (developers start here), CLAUDE.md (*update DESIGN.md in the same commit as
any structural change*), and both devlog entry points.

### Next

Unchanged: Phase 2 blocked on Q-004 and Q-005. Q-021 and Q-022 still open.

---

## Session 10 — 2026-08-27 — Design-draft pass begins; Gap 1 (the answer) resolved

### Context / setup

Picked the project up on a **different machine**. New working dir
`/Users/avin/Antigravity-Code/class-framework` (was `/Users/avin/Claude/class-framework`). System
`pip` is broken (its shim points at a missing Python 3.7); worked around with a local `.venv`
(gitignored). `pip install -e ".[dev]"` + `pytest` → **14 passing**, CLI works. Repo clean, on
`main`, remote `BGU-CSE/class-framework`.

### The reframe (Avin)

Two corrections that set the agenda:

1. **DS&A is not privileged.** It is one test subject among several; other developers will test the
   framework on other courses. Hardens D-002 — nothing DS&A-specific may leak into the framework.
2. **We are not finishing the framework before the classroom** — that is impossible. The goal now is
   to **complete a full *draft* of the design document**, then fill the framework gaps (also a
   draft), then test on real classes *and update in parallel*. The design draft is the gate whose
   purpose is to give the testing a stable target.

**Scope clarification for DESIGN.md:** it is about *the framework* — content model, components,
agents, metrics, course lifecycle — **not the development process** (merges, a developer's
"teacher" vs "developer" hats). That process is a separate discussion, not part of DESIGN.md. (This
retired an earlier proposal to write the framework-update/Q-007 mechanism into DESIGN.)

### Design-draft agenda

Established four areas the draft must close, and their order (content model first, because agents,
metrics and lifecycle are all defined *over* it):

1. **Content-model completeness** — ← in progress
2. **Agent coverage** — do new components need new agents?
3. **Metrics** — do we measure agent performance and/or unit/course quality beyond pass-fail?
4. **Course lifecycle** — the semester arc, revision, re-offering.

Also separated out: **homework, including programming assignments, is a distinct section** from the
flipped-class study. It is at-home work *in addition to* the study sessions, can span several units,
is not per-unit/mandatory, and its purpose is to *test what has already been learned*. Undesigned →
Q-026.

### Flipped-class design review

Read schemas + validator + templates + the guiding-questions skill and reviewed the reverse-class
part for gaps. Verdict: the skeleton is sound (both headline failure modes genuinely enforced,
two-way coverage, ID consistency, duration sums). Four real gaps found:

- **Gap 1 — a guiding question had no answer.** Resolved this session → **D-019**.
- **Gap 2 — "Study Path" means per-question vs. per-session route**, and the feasibility check sums a
  cherry-picked cheapest path per goal rather than a coherent route → **Q-023**.
- **Gap 3 — the time budget is not really automated**: the reading/video constants in
  `time-constants.yaml` are never used (no structured page/word/duration fields; `_estimate_path`
  only has fallbacks for `gem`/`exercise`) → **Q-024**.
- **Gap 4 — nothing sits above Unit Objectives**: no course-level outcomes, so whole-course coverage
  is uncheckable → **Q-025**.

### Decided — D-019 (Gap 1)

Every Guiding Question gets a separate `answer` field: a required list of precise references
(`{kind, ref, note?}`, `kind ∈ textbook|slide|video|article|web|other`, no time estimate) to where
the correct answer lives — not prose. New rule `answer_reference_present` (error). Grounds the Gem,
the assessment writer, and the critic. Name "Guiding Question" reconsidered and kept. Full rationale
in D-019.

### Next

Continue the content-model pass: **Gap 2 (path vs. route, Q-023)**. Then Gaps 3–4, then the homework
section (Q-026), then agenda items 2–4 (agent coverage, metrics, lifecycle). D-019 is design-only —
schema/validator/template/agent changes are the later "fill the gaps" step, not done yet.

---

## Session 11 — 2026-08-28 — Gap 2 resolved (Study Path reshape); pip fixed

### Housekeeping

Fixed the machine's `pip`: `/usr/local/bin/pip` was a dead Homebrew 3.7 shim (stale shebang →
removed interpreter). Repointed it to the working python.org 3.13 `pip3`, mirroring the existing
`pip3` symlink; no sudo needed. `pip`/`pip3`/`python3 -m pip` now all agree (24.3.1). Handoff note
corrected accordingly.

### Gap 2 — Study Path (→ D-020)

Avin questioned the Study Path's rationale. Surfaced that it bundled three jobs: student agency,
feasibility arithmetic (the load-bearing "25 min is real" check), and Gem-as-route. D-019's `answer`
made the "provide a route to the answer" job redundant, so the jobs separated.

Resolved (option "a"):

- **Budget moves onto the question.** Each guiding question gets `est_minutes`, a single
  teacher-approved study time; the session check sums them (`sum(est_minutes) + overhead ≤ ~25`, with
  tolerance — Avin stressed it's an approximation, students vary). Lives on the goal, not the answer
  refs, so D-019 is unaffected.
- **`paths` moves to the Study Session** as an open, optional, non-exhaustive pool of alternative
  resources — teacher-facing for now, not tagged to individual questions (Avin confirmed), not
  time-summed. Students may substitute their own.
- **Q-023 resolved; Q-024 narrowed hard** — the core guarantee no longer needs the reading-rate
  constants; it's one teacher number per question.

Updated DESIGN.md (§2 + §3 content model), D-019 (amendment pointer), added D-020, struck Q-023,
narrowed Q-024, advanced the agenda note. Still **docs only** — no schema/validator/agent changes;
those wait until the design draft is finalized (Avin's explicit sequencing).

### Next

Gap 3 = **Q-025** (nothing above Unit Objectives — no course-level outcomes). Then the homework /
programming-assignment section (**Q-026**). Then agenda items 2–4 (agent coverage, metrics, lifecycle).

---

## Session 12 — 2026-08-28 — Gap 3 resolved: the Syllabus top layer (→ D-021)

### The gap

Nothing sat above Unit Objectives, so whole-course coverage was uncheckable (Q-025).

### Resolution

Avin: the top layer of a class should be its **syllabus**, defaulting to a **Bologna-style**
descriptor. Decided (**D-021**):

- **Two artifacts, no `course.md`** (Avin double-checked the name). `syllabus/syllabus.md` is the
  authored top-layer document (front matter + prose), edited exactly like `unit.md` — scaffold writes
  the skeleton once into the already-reserved `syllabus/` slot, never overwrites. `course.yaml` stays
  the config wiring. Confirmed by reading the code: `frontmatter`/`model`/`scaffold` already reserve a
  `syllabus/` directory, so this fills a pre-allocated slot rather than intruding.
- **Bologna default front matter (generic):** `goal`, `outcomes` (Course Outcomes `CO1…`),
  `workload` (credits / credit_system — ECTS as one instantiation, not hardcoded; optional
  total_hours), `prerequisites`, and a *reserved* `assessment` block. Identity fields stay in
  `course.yaml`; the rendered syllabus pulls them + a **live-stitched unit overview** (anti-drift).
  Source is edited; the full published syllabus is a generated view.
- **Course Outcomes are the roof:** Unit Objectives gain `outcomes: [CO1…]`; two-way checks
  (`outcome_coverage`, `objective_maps_to_outcome`) deferred to implementation.
- **Grading deferred** to Q-026 (Avin: "we'll specify grading later"). The `assessment` block is
  reserved, not specified.

Also fixed the machine's `pip` earlier today (see Session 11). Noted a stale `(D-019)` citation in
`frontmatter.py` (predates this session, most likely meant D-017) — cleanup for when we next touch
code.

Updated DESIGN.md (§3 content model + prose, §6 data flow), added D-021, resolved Q-025, relocated its
minor sub-items to Q-027, advanced the agenda. Still **docs only**.

### Next

**Q-026** — the homework / programming-assignment section (a distinct at-home track from study
sessions; multi-unit; not mandatory; tests what's already learned; carries the grading scheme). Then
agenda items 2–4 (agent coverage, metrics, course lifecycle).

---

## Session 11 — 2026-08-28 — Implementation ledger

### What happened

Claude pulled Avin's three design-draft commits (D-019 `answer` field, D-020 study-path reshape,
D-021 syllabus) and reviewed them. The design work holds up; the problem was elsewhere.

**Four decisions were `locked (design)` with no code, and nothing tracked the gap.** The repo held
two contradictory descriptions of itself: `DESIGN.md` said paths are per-session and untimed, goals
carry `est_minutes` and `answer`, and a syllabus exists — while `schemas/`, `src/classkit/` and six
agent/skill files still implemented the previous model. `DESIGN.md` read throughout as if all of it
existed.

Avin agreed to a ledger, and confirmed the order of work: **finish the design draft first, then
change the code to match.** The ledger is therefore a record, not a work queue to start on now.

### Built

**Implementation ledger in `ROADMAP.md`** — 3 decisions, **40 artifact changes**, 0 built. Grouped
by decision so each can be implemented and tested as a unit. It captures second-order consequences
that would otherwise be missed, e.g. D-021 also requires an `outcomes` field on
`unit.schema.json`, a `CO1` ID convention in `CLAUDE.md`, and a `SCHEMA_FOR` entry; D-020 also
invalidates the `estimating-study-time` skill, the Study Path glossary entry, and the description of
`time_constants` in `GETTING-STARTED.md`.

**Two open items surfaced while enumerating**, both recorded in the ledger next to the decision they
belong to:

- **D-019's required `answer` has no honest filler.** A judgment question may have no single
  locator, and a required field at error severity is exactly the pressure that produces the
  fabricated reference invariant 7 forbids. Needs a documented escape, or a ruling that such
  questions belong in the in-class hour. Decide before implementing.
- **D-020 shifted the study-time guarantee from code to the critic.** Code can check the arithmetic;
  only `course-critic` can judge whether a teacher's `est_minutes` is plausible. Its prompt does not
  say so. Now written into `DESIGN.md §10` and queued in the ledger.

**`DESIGN.md`** gained a header note — it describes the *target* design, and the ledger is
authoritative for what exists — plus two §10 entries (designed-not-built; nobody but the critic
checks estimate honesty), and a corrected time-constants entry now that D-020 removed their
load-bearing role.

**`_devlog/README.md`** gained the rule: a `locked (design)` decision needs a ledger row in the same
commit.

### Next — design draft, continuing

1. **Q-026 homework** — the one genuinely unfinished entity in the content model.
2. **Course lifecycle** — moved ahead of agent coverage: the semester arc can still change the
   *model* (per-offering versioning, where "what went wrong last year" lives), and settling agent
   coverage first would mean redoing it.
3. **Agent coverage** — over the settled model; includes rewriting the agents the ledger already
   lists as stale.
4. **Metrics** — scoped down to deciding *where* metrics surface and whether they gate; the measures
   themselves wait for a real unit, or they will be invented wrong.

Proposed exit criterion for the draft: every entity in the content model has an ID convention, a
schema owner, an agent that writes it, and at least one validator rule that can fail on it.
