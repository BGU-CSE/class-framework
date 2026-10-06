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

## Session 13 — 2026-08-28 — Reshape the plan into vertical slices (→ D-022)

Synced first: pulled the other session's commit `48c7a73` (the implementation ledger + the rule that
a `locked (design)` decision needs a ledger row in the same commit). Fast-forward, no conflict.

Avin reshaped how we proceed (**D-022**): instead of finishing the whole design draft then
implementing, we go **design → implement → test → update one vertical slice at a time**. Slices:

1. **Core** (now) — course init, syllabus, outcomes, units, study sessions, in-class, **and the entry
   quiz end to end** (Avin pulled question-generation + gradeable quizzes into Core, so Core can
   *generate and run* the learning phase, not just author it). Content model already locked as
   D-019/20/21. So the Assessment Item type + assessment-writer are **split**: entry-quiz items are
   Core; homework/exam items defer.
2. **Assessment** — homework, programming assignments, exams (Q-026).
3. **Exports** — Gem *builder* + PPTX (Gem-as-path stays Core).
4. **Metrics** — later (to improve a course/activities).
5. **Lifecycle** — much later (after first teaching).

Naming settled: "Core", then "Assessment" and "Exports" (chosen over the broad "Extensions" so each
name is specific; the Gem builder is a generator, so it belongs with exports, not with assessment).
Metrics and lifecycle explicitly **not** in Core.

Recorded D-022, rewrote ROADMAP's build-plan section (vertical slices + how they map onto the
risk-ordered phases), no DESIGN.md change (this is process/roadmap, not framework spec). Still no
code.

### Also decided (D-023) — D-019's open item closed

The judgment-question escape: a study-session question either carries a recorded `answer`, or is
marked **`defer_to_class: true`** — a pre-class thinking prompt whose answer/discussion is deferred to
the meeting (Avin wanted to keep the ability to ask a question that provokes thinking before class).
The discipline that keeps it honest: a deferred question **must** be referenced by ≥1 in-class
activity, so deferring costs contact time. New rule `deferred_question_resolved_in_class`. Recorded
D-023 + ledger rows (11), DESIGN §2, and marked D-019's ledger open-item resolved.

### Next

Core design draft now has **one** open item left: write the `est_minutes`-honesty responsibility into
`course-critic` + it's already noted in DESIGN §10 (just needs the critic prompt when we implement).
Then Q-027 minors (optional), and Core is ready to implement (work its ledger rows) and test. Q-026
opens the **Assessment** slice afterwards.

---

## Session 14 — 2026-08-28 — Move dev docs under `dev/`; rename the spec (→ D-024)

Repo hygiene, no design change. The spec, roadmap, and build log are framework-*development*
artifacts that land in every teacher's clone (D-009). Moved them under one directory so the teacher's
workspace stays clean and they are clearly ignorable:

- `DESIGN.md` → `dev/FRAMEWORK-SPEC.md` (renamed — "Design" was ambiguous; the new name states its
  role as the framework's spec).
- `ROADMAP.md` → `dev/ROADMAP.md`; `_devlog/` → `dev/_devlog/`.
- Root keeps only teacher/product-facing + load-bearing files (README, GETTING-STARTED, LICENSE,
  CLAUDE.md [auto-loaded agent context — must stay], pyproject.toml, product dirs).

Honest caveat recorded in D-024: a clone still copies `dev/`; true exclusion would need sparse-checkout
or a separate repo, both worse. `dev/` also improves merge hygiene (teachers never edit it).

Used `git mv` (history preserved). Updated living references in README, CLAUDE.md, and the moved
files' cross-links; left historical progress/decision entries as-is. Tests unaffected (no code
touched).

### Next

Unchanged: close Core's last design item — write the `est_minutes`-honesty responsibility into
`course-critic` (noted in `dev/FRAMEWORK-SPEC.md §10`). Then Q-027 (minor), then implement + test
Core. Q-026 opens the Assessment slice.

---

## Session 15 — 2026-08-28 — `est_minutes` honesty gets a yardstick (→ D-025); Core spec finalized

Closed the last Core design item (D-020's open item + Q-024). The budget rides on a teacher-typed
`est_minutes` per question; code checks only the sum, so honesty is a human-judgment step owned by the
`course-critic`. Decision (**D-025**, Avin's "option 2", with an explicit fallback to option 1 if it
gets fiddly): the time-constants return as an **advisory yardstick** — the designer *proposes*
`est_minutes` from them, the critic *sanity-checks* against them, shared via the `estimating-study-time`
skill. No validator rule; advisory only, so a bad constant guides rather than breaks. Kept, not
deleted (resolves Q-024). Caveat: constants are still placeholders (Q-005), so calibration is rough.

Recorded D-025, wove its changes into the D-020 ledger rows (no new artifacts), softened
`FRAMEWORK-SPEC.md §10`, resolved Q-024. Docs only.

**Core spec is now finalized** — content model D-019/20/21/23/25, both open items closed; only the
optional Q-027 minors remain. Next up is a choice: knock out Q-027, or declare Core done and start
**implementing** it (work the ledger rows) + test.

### Next

Either the Q-027 minors, or begin Core implementation from the ledger (schemas → validator →
templates → agents/skills → tests, kept green each step). Then Q-026 opens the Assessment slice.

---

## Session 16 — 2026-08-28 — Consolidate the spec into a standalone normative Core spec (→ D-026)

Avin wants the spec usable by a memory-less agent to implement or verify Core from one file, before
handing it to an independent reviewer. Rewrote `dev/FRAMEWORK-SPEC.md` (D-026):

- Added a **scope banner** (Core defined; Assessment/Exports/Metrics/Lifecycle named as deferred) and
  kept the target-vs-built note.
- Revised §1–§10 for Core scope; §5 control flow rewritten to the real Core sequence
  (`/ingest` → `/plan-units` → `/design-unit` incl. the entry quiz → `/review-unit`); §4 and §6 mark
  Core-active vs deferred agents/data.
- Added **§11 — Core specification reference (normative):** 11.1 ID conventions (incl. `CO`); 11.2
  field specs for every Core artifact (`course.yaml`, `syllabus.md` [target], `unit.md`,
  `sessions/NN.md`, `in-class.md`, entry-quiz assessment item, `methodologies/*.yaml`); 11.3 time &
  feasibility model; 11.4 the full validation-rule table with default severities; 11.5 the
  methodology contract. Fields not yet in `schemas/` are tagged **(target)**.

Read `schemas/assessment-item.schema.json` to spec the entry-quiz item accurately. Docs only; the
decision log's normative outcomes are now duplicated into the spec by design (D-026).

### Next

Avin reviews the consolidated spec; then hand it to an independent agent using the review brief
(prompt drafted earlier). Fold review findings into the spec, then implement Core from the ledger.
Open: whether to keep `workload` required in the syllabus, and that `guiding_question_assessed`
(warn) fires broadly in Core since only entry-quiz items exist — both good review-bait.

---

## Session 17 — 2026-09-10 — Split out `VISION.md`; restructure the spec top-down (→ D-027)

Avin reviewed the consolidated spec: the technical content was there, but the big picture was
missing — *"the goal of the project and the framework we are developing is not clear enough"*, and
§1/§2 "are not expressing my goals well". Diagnosis: those sections argued for *flipping a lecture
course* and for the *Guiding Question mechanism* — one pedagogical instantiation — while nothing said
what the framework itself is for. The project-level statement lived only in `README.md`'s first line.

**The goal, corrected by Avin (the substantive change).** The driver is **AI-native course
development**, not mechanical validation — that is a feature. A teacher building, re-methodologising,
or (annually) revising a course should have structure + agents a coding tool can use, making the
recurring jobs easier: write a quiz, add a unit, change goals, search content. Ends: better courses →
better learning and teaching. *Course-as-software-project is the means, not the driver.* Also settled:
scope is flipped-classroom now (pluggability is an open door, not a present claim); the audience is
teachers comfortable with git and an AI tool; VISION is for developers/agents, teachers read README.

**Written:**

- **`dev/VISION.md`** (new) — Project outcome (the deliverable is a git repo you clone and work in
  with an AI tool, and what it contains) · Motivation · Approach · Scope and audience · How the
  framework is used (7-step teacher workflow) · Specification and development process.
- **`dev/FRAMEWORK-SPEC.md`** restructured top-down: §1 Scope (phase table, spec-ahead-of-code, doc
  map) · §2 Framework architecture (framework-wide) · §3 The Core phase (coverage, pedagogy, the
  Guiding Question) · §4–§7 content model / control flow / data flow / invariants · §8 normative
  reference · §9 known weaknesses. Old §1/§2 survive as §3.2/§3.3, demoted to *Core's* pedagogy and
  mechanism. Normative field tables kept at full detail.

References updated in `README.md` (developers start at VISION, then SPEC), `CLAUDE.md`, and the
handoff reading order. Docs only; no code.

### Next

Avin reviews the restructured spec. Then the independent review (brief drafted in Session 16 — needs
VISION.md added to its reading list), fold findings, then implement Core from the ledger.

---

## Session 18 — 2026-09-10 — Avin's spec review: four changes (→ D-028, D-029, D-030)

Avin approved `VISION.md` unchanged and gave four comments on the spec. All four were acted on.

**1. Activity → guiding question was too strong (→ D-028).** *"An in-class activity doesn't* must
*reference a guiding question… I can discuss the final exam, or present something from the news."*
Rather than plainly downgrading the rule — which would have gutted the lecture-reversion guarantee,
since an entire unmapped hour would then pass with warnings — Avin chose the **capped** design:
per-activity `warn` with an optional `reason`, plus a new **error** rule
`in_class_unmapped_time_cap` against `in_class.max_unmapped_minutes` (default 15 of 50). Invariant 4
reworded in both the spec and `CLAUDE.md`. Recorded as a weakness in §9: the guarantee is now a
number someone chose rather than a bright line.

**2. The syllabus needs its own agent (→ D-029).** New `syllabus-designer`, but run **in one flow**
with `curriculum-architect` under `/plan-units` — outcomes and unit objectives form the coverage
chain, so splitting the flow would let them drift. "Testing it" split into mechanical (existing
coverage rules) and judgment (new critic responsibilities). Partial update deferred to D-030.

**3. Commands should be stepwise and must not overwrite (→ D-030).** New spec **§5.2 "How commands
behave"**: (a) stepwise with an approval gate per step — `/design-unit` becomes sessions → approve →
hour → approve → items → approve → validate; (b) **never overwrite without permission**, which
generalizes invariant 5 from `scaffold` to every agent and command (agents write files directly, so a
re-run could silently destroy a teacher's edits); (c) **revision, not regeneration** — update in
place and report the diff, which is what makes partial edits and year-to-year maintenance work.

**4. The flipped-class structure was not stated plainly.** Correct — §4's tree carried the numbers but
mixed them with file paths, and §3 argued about failure modes without ever drawing the shape. New
**§3.2 "The shape of a flipped course"**: unit = one week = 150 min = 100 home + 50 class; home = 4 ×
25-min sessions of 3–5 guiding questions; class = 3–6 activities opening with the entry quiz — **with
the goal of each part stated** (home = acquisition, class = application, not re-explanation). Adds
what the README cannot: *the shape is Core, the numbers are the methodology's* (invariant 2). Old §3.2
and §3.3 became §3.3 and §3.4. Avin's principle recorded: **the README should be a result of the
spec** — it needs re-deriving once the spec settles.

Ledger: 19 new artifact rows across D-028/29/30 (now 8 decisions, 70 changes, 0 built).

### Next

Independent review of `VISION.md` + `FRAMEWORK-SPEC.md` (update the Session-16 brief: add VISION.md,
and the spec's new section numbers). Then fold findings and implement Core from the ledger. Note the
README and GETTING-STARTED now contradict D-028/D-030 in places — ledger rows exist for both.

---

## Session 19 — 2026-09-10 — Independent review, and its findings adopted (→ D-031)

An independent agent (Gemini 3.1 Pro) reviewed `VISION.md` + `FRAMEWORK-SPEC.md` with full repo
access, using the brief drafted in Session 16. Verdict: **yes with changes**. Review kept at
`dev/reviews/core-spec-review-01.md`. All findings accepted; one re-diagnosed. Recorded as **D-031**,
lettered (a)–(i) so the spec can cite them.

**The re-diagnosis worth remembering.** The review's headline BLOCKING finding — a circular dependency
where `lesson-planner` references quiz items that `assessment-writer` has not written yet — was right
about the problem and **wrong about the mechanism**. It claimed validation would fail at step 3 via
`item_reference`. Checking the code: `item_reference` only iterates over items that *exist* and checks
*their* fields, and **nothing validates `activity.items` at all**. So an invented id does not fail — it
validates clean and leaves a dangling reference. A silent hole, not a deadlock, and worse than
reported. Fixed by both swapping the flow order *and* adding the missing rule.

Adopted: **(a)** assessment-writer now runs before lesson-planner + new `activity_item_reference`
rule · **(b)** never-overwrite enforced in `classkit` code, not by prompt (upgraded from a
"(consider)" ledger row — a negative constraint agents violate on long runs, guarding an
unrecoverable failure) · **(c)** `guiding_question_assessed` off in Core (would fire on every valid
unit and teach teachers to ignore warnings) + new `unit_has_entry_quiz_items` · **(d)** syllabus
`workload` optional + warn · **(e)** `max_unmapped_minutes` default 15 → **10**, and now **overridable
in `course.yaml`** — Avin: *"some teacher may decide to put it 50 and ignore it altogether, which is
also fine"* · **(f)** unit directory `NN-slug` naming specified (was implemented, never written down)
· **(g)** assessment item `answer` → `model_answer` (killing the one-key-two-meanings collision) ·
**(h)** approval gates live in the orchestrating command — a subagent cannot ask the teacher anything
· **(i)** `/plan-units` handoff is sequential and file-based.

Also updated `CLAUDE.md` invariant 5. Ledger: 20 new rows (9 decisions, 90 changes, 0 built). Docs
only; tests still pass (14).

### Next

**Implement Core** — see Session 20 for the agreed order, and Q-028 for the gap found while planning
it.

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

---

## Session 20 — 2026-09-10 — Implementation order agreed; Q-028 (ingest) found

### The order to build Core

Avin asked whether to implement by **workflow step** or **by layer**, and what the trade-offs are.
Agreed: **workflow order outside, layer order inside each step** (schema → template → rule → agent →
test, green each step), with one deliberately thin shared foundation first.

The deciding argument: building layer-by-layer defers every agent to the end, and **the agent layer
is the riskiest part** — no prompt has ever run against real materials (spec §9). Layer-first would
complete the parts we are most confident about (schemas, validator — already written and tested) and
only then expose the uncertain one. Workflow order surfaces the risk early, on a small surface. Same
vertical-slice reasoning as D-022, one level down. Written into `ROADMAP.md` as an implementation
plan sitting above the ledger (the ledger is grouped by decision, which is right for traceability and
wrong as a work plan).

Steps: 0 foundation (overwrite-safe write path only) · 1 initialize (`scaffold course`) · 2 ingest ·
3 syllabus + units · 4 study sessions · 5 entry quiz · 6 in-class hour · 7 review + gates · 8 docs.
Step 5 before 6 is forced by D-031a. A real course can be attempted after step 4.

### The gap Avin found (→ Q-028)

**Correction to Session 19's claim that "no open design items remain for Core".** That was wrong.
Avin: *"the course starts (after clone) with a script and the ingest… I suspect the ingest will not
be simple."* Both were missing from the proposed order, and more importantly **ingest is barely
specified at all** — one line in §5.1, one data-flow row in §6, and nothing about how materials are
organized, what formats arrive, how material added later is folded in, or what post-processing later
agents need.

Missed by the author *and* by the independent review — the review checked what the spec said, and
nothing said anything here to check. Worth remembering as a limit of document review: it cannot flag
a section that does not exist.

Raised as **Q-028**, deliberately not answered this session (Avin: *"don't answer me now"*). One
connection worth recording: `answer` locators (D-019) demand precision like *"slide 18"*, so if raw
materials are not processed into something addressable, the locator design has nothing solid to point
at. Overlaps **Q-004** (what format the pilot materials are in) — answer them together.

### Next

Steps 0 and 1 are unblocked and can start whenever. Step 2 needs Q-028 designed first.

---

## Session 21 — 2026-09-10 — Implementation starts: steps 0 and 1 built

First session where the ledger moves. Implemented steps 0 and 1 of the plan agreed in Session 20,
working from the spec alone (the decision log deliberately not read — the session doubled as a test
of the spec's self-containment claim). Suite: 14 → 36 tests, green at every commit.

### Step 0 — the overwrite-safe write path (D-031b) — commit `d346fee`

New `src/classkit/write.py`. `write()` cannot replace a file that already has content: it returns a
`refused` outcome and touches nothing, so **a caller that ignores the return value still loses
nothing**. That was the design choice worth making — an exception protects only callers who catch
it. Replacing needs a deliberate second act (`overwrite=True` / `--overwrite`).

Two cases deliberately *not* refusals: whitespace-only files, and byte-identical rewrites
(`unchanged`, a no-op) — otherwise a command could not safely re-emit its own approved output.
Writes go temp-file + `os.replace`, because a truncating crash is the same unrecoverable loss the
invariant exists to prevent.

`classkit write PATH [--from FILE] [--overwrite] [--dry-run]` is the surface agents reach it
through — **the spec never said there had to be one**, and without it the mechanism is code nothing
can call (see the gap report, G-1). Exit 3 = refused, distinct from 2 = broke.
`scaffold.write_new()` refactored onto the same primitive as its create-only special case.
Specified as the new spec **§8.6**.

**Not done, and it matters:** every writing agent still has `Write`/`Edit` in its front-matter tool
list, so it can bypass this entirely. The guarantee becomes structural only when those tools come
*off* the agents — which no ledger row currently says (G-4). The per-agent rows should be amended
before step 3 lands, or D-031b quietly ships as a better prompt.

### Step 1 — scaffold the syllabus (D-021, D-031d) — commit `2eb4311`

`schemas/syllabus.schema.json` + `templates/course/syllabus.md` + model loading (`Course.syllabus`,
`Course.outcomes`) + schema-layer wiring + `syllabus_workload_missing` (warn). `syllabus/.gitkeep` is
gone; the slot holds a real file. A fresh `scaffold course` validates with **zero errors** and one
warning — the workload it is waiting for, which is exactly what D-031d designed.

The template ships `CO1`/`CO2`, matching the two objectives a scaffolded unit gets, and `workload`
commented out.

**Step boundary decided (G-8):** step 1 took the syllabus *artifact* end to end; the *coverage
chain* (`outcomes` on objectives, `objective_maps_to_outcome`, `outcome_coverage`) stays in step 3,
because those rules check a field on the unit that step 3 adds.

### The gap report — `../reviews/impl-gaps-step-0-1.md`

16 points where the spec did not determine the answer. Three need Avin's call before step 3:

- **G-9 — nothing catches a *missing* syllabus.** §8.4 has `in_class_missing` for units and no
  equivalent here. Worse, once step 3 lands, a course with no syllabus has no Course Outcomes and
  `outcome_coverage` is *vacuously satisfied* — the rule that closes the coverage chain passes
  loudest when the roof is gone. I did not invent the rule code (that edits the normative table);
  `syllabus_workload_missing` fires on the missing file so the absence is at least visible.
- **G-12 — `outcome_coverage` on a course that is not finished yet.** A freshly scaffolded course
  has outcomes and *zero units*, so read literally every outcome is uncovered → error → invariant 6
  breaks at the first commit of step 3. Probably the rule should be scoped to a complete unit map.
- **G-15 — the "rendered syllabus" is referenced three times and specified nowhere.** No command, no
  path, no phase, no ledger row — and it is the whole anti-drift argument for not repeating identity
  fields in the syllabus. Specify it or move it to the deferred list.

The through-line: the spec held up on *what to build* (nothing in §8 was wrong) and was thin on
**interactions with half-built courses**, **absence**, and **mechanism for what it delegates to
code**. G-15 and Q-028 are the same failure twice — a component named in passing, never specified,
invisible to document review.

### Next

Step 2 (ingest) is still blocked on **Q-028**. Step 3 is unblocked *except* for G-9 and G-12, which
should be answered first — both are about rules step 3 introduces.

---

## Session 21 — 2026-09-10 — Implementation gap report triaged (→ D-032)

Read `reviews/impl-gaps-step-0-1.md` (16 gaps from implementing steps 0 and 1 against the spec
alone). Avin's instruction: make simple technical fixes directly, discuss anything pedagogical.

**Closed without discussion (13).** Nine the implementer had already resolved and specced (the write
CLI surface, "has content" semantics incl. the whitespace-file case Avin cited as exactly the sort of
corner case not worth his time, confirmation mechanics, refusal-returns-not-raises, atomicity,
methodology-vs-DEFAULT_SEVERITY, syllabus body structure, the step 1/3 boundary, `workload`
sub-field requiredness). Four fixed this session: **G-6** test file location; **G-11** a spec clause
protecting the deliberately-open `assessment` item shape so a later implementer does not "fix" it;
**G-16** a ledger row for the stray `gem` block; **G-4** — the per-agent ledger row now says writing
agents must **drop `Write`/`Edit` from their tool front matter**, since availability of
`classkit write` is not enforcement, and without that D-031b delivers only a better prompt.

**Resolved by Avin (→ D-032), from G-15.** The "rendered syllabus" was referenced three times and
specified nowhere. Avin split it: *"if by rendering you mean creating a PDF for students then we can
defer it — but the .md file needs to contain potentially all the information the Bologna style has
(even if we fill it in steps, or decide to skip some)."*

- **Rendering → Exports.** It is a generator, like PPTX and the Gem. Added to the Exports row in
  §1.1; the three references that implied it already existed were reworded.
- **`syllabus.md` becomes a complete Bologna descriptor now.** Added optional `level`,
  `course_type`, `offered`, `teaching_methods`, `reading`. Only `goal` and `outcomes` stay required.
  `teaching_methods` is the one that earns its place pedagogically — for a flipped course it is the
  field that says what the course actually *is*.
- **Stated the rule that decides what belongs in the file:** *authored content is a field in
  `syllabus.md`; derived content is assembled at render time.* Identity/config stays in
  `course.yaml`; the unit overview stays derived from `unit.md`. Copying either in would create the
  drift D-021 exists to prevent.

**Still open — asked, not yet answered:** G-9 (`syllabus_missing` rule — recommended `error`) and
G-12 (`outcome_coverage` on a half-built course — recommended: apply only once the unit map is
complete, plus a spec clause saying which course *state* each rule applies to). **Both block step 3.**

### Next

Avin to settle G-9 and G-12, then step 3 (`/plan-units`). Step 2 (ingest) still blocked on Q-028.
D-032 reopens step 1's schema/template — fold it into the next implementation session.

---

## Session 21b — 2026-09-10 — G-9 and G-12 settled (→ D-033); step 3 unblocked

Avin accepted both recommendations.

**Rules must declare which course state they judge.** The underlying omission: §8.4 defined every
rule against a *finished* course, while a course is half-built for almost all of its life — every
implementation step, and a teacher's whole authoring semester — and invariant 6 *requires* a fresh
scaffold to validate clean. Now split explicitly:

- **Consistency rules** (always active): schema, ids, dangling references, duration sums, counts.
- **Completeness rules** (only once units on disk == `course.yaml` units): `outcome_coverage`.
  While incomplete the rule does not fire and `validate` reports it as *skipped, and why* — visible
  rather than silent.

A deliberate asymmetry falls out of this, worth remembering: *objective → outcome* is a consistency
rule (wrong the moment it is written), *outcome → objective* is a completeness rule (merely
unfinished). Both directions are still checked; they become meaningful at different times.

**`syllabus_missing` = error.** `scaffold` always creates the syllabus, so absence means deletion,
not drafting — and a course with no syllabus has no Course Outcomes, making `outcome_coverage`
*vacuously true*: the rule that closes the coverage chain would pass most confidently exactly when
the roof is gone. Same class of silent hole as D-031a's dangling `activity.items`.

Also added the consistency/completeness instruction to `CLAUDE.md`'s "Adding a validation rule", so
the next rule author does not repeat the omission.

### Next

**Step 3 (`/plan-units`) is unblocked** — no open questions remain for it. Its implementation session
should also fold in D-032 (the Bologna syllabus fields, which reopen step 1's schema and template).
Step 2 (ingest) remains blocked on **Q-028**, still unanswered by choice.

---

## Session 21c — 2026-09-10 — Manual-testing procedure written and verified

Avin will hand-test steps 0 and 1 next, from a possibly different machine, and asked how to do it in
a clean environment.

Wrote **`dev/MANUAL-TESTING.md`**, and **verified every command in it** by actually doing the run:
cloned the repo into a scratch directory, made a venv, `pip install -e .`, scaffolded a course and a
unit, validated, and exercised the write path. The document carries the real output, not
reconstructed output.

Points worth keeping:

- **A clean environment is just a fresh clone in a scratch directory** — the framework *is* the
  working environment (D-009), so there is nothing else to set up. Repointing `origin` and pushing
  are the two things a real teacher does that a tester should skip.
- **An "expected noise" table** was the most necessary part. A scaffolded course with one unit emits
  **14 warnings**, 12 of them `guiding_question_assessed` — already decided to be `off` in Core
  (D-031c) but not built until step 5. Without that table the tester reasonably reports a working
  framework as broken. Anything *else*, especially any error on a fresh scaffold, is a real finding.
- Verified live: scaffold is create-only on re-run (0 created, 6 untouched); the write path refuses
  an unconfirmed overwrite with exit 3 and leaves the original intact, treats identical bytes as a
  no-op, and `--dry-run` answers "may I write here?" without writing.

Also pointed `CLAUDE.md`'s "Running things" at the new document.

### Next

Unchanged: Avin hand-tests steps 0–1; step 3 is unblocked (fold in D-032); step 2 waits on Q-028.

---

## Session 22 — 2026-09-12 — Two ideas parked for later slices (Q-029, Q-030)

Avin noted two ideas to keep for after Core. Recorded so they are not lost, and cross-referenced from
the slices they belong to in `ROADMAP.md` so they surface at the right moment rather than only if
someone re-reads the questions file.

**Q-029 — the entry quiz could check homework, not only study sessions** (Assessment slice). It would
give homework the accountability loop it currently lacks: homework is not mandatory every week and
nothing structurally notices whether it was done, whereas the entry quiz is an accountability
mechanism that already exists on already-budgeted class time. Recorded the concrete collision:
homework spans several units, but `activity_references_guiding_question` *errors* on a Guiding
Question that is not of the current unit — so this needs either a cross-unit exception or a different
referencing route, decided deliberately rather than discovered as a validation failure.

**Q-030 — the class Gem as a repository students clone and open with Claude Code** (Exports slice).
It is the project's own thesis applied one audience further: `VISION.md` argues structure makes a
course something agents can operate on, and today that benefit lands only on the teacher's side.
Recorded two constraints to settle first — **confidentiality** (a student-clonable repo must not
carry answer keys, distractor rationales, rubrics or exam material; it needs an *allow*-list and a
clean git history, and interacts with Q-002), and **audience** (VISION §4 scopes the framework to
people comfortable with git and an AI tool, which students broadly are not — so it must be an
additional study path, never a required one, per D-010). Also flagged that it is the first idea to
touch ROADMAP's "not planned: student-facing anything" line, and should cross it deliberately if at all.

Neither affects Core. No spec change.

### Next

Unchanged: Avin hand-tests steps 0–1 (`dev/MANUAL-TESTING.md`); step 3 is unblocked and should fold
in D-032; step 2 waits on Q-028.

---

## Session 23 — 2026-09-12 — Two hats in one repo (→ D-034); two-repo split deferred (Q-031)

Preparing to hand-test as a teacher, Avin noticed a fresh clone hands the teacher the *developer's*
`CLAUDE.md`, and proposed splitting the project into two repositories. He asked for a rigorous
argument before changing anything.

**Checked the premise first, and it was half right — which decided the question.** `.claude/` is
*entirely teacher-facing* and correct: `curriculum-architect`, `/design-unit`,
`writing-guiding-questions` are the teacher's. `dev/` was already accepted clutter (D-024);
`tests/`, `src/`, `pyproject.toml` are required or invisible. **Only `CLAUDE.md` was misaddressed** —
one file, not a topology problem. Also worth noting: steps 0–1 are CLI-only, so this never blocked
the pending test drive; it bites from step 3, when agents are first exercised.

**Two repos rejected for now (D-034), recorded fairly and revisitable (Q-031).** The decisive
argument: it would destroy **spec↔code atomicity** — "update the spec in the same commit" and
"ledger row in the same commit" *cannot exist* across two repos — which is the one discipline that
has kept this project coherent, and this project's own history (the ledger existing at all) is the
evidence that conventions rot. It would also invent a release process mid-implementation, and hollow
the dev repo out to documents only, since code and agents must live where teachers clone. Deferred to
release (Q-031), where the trade-offs genuinely invert.

**Done instead:** root `CLAUDE.md` rewritten teacher-facing (vocabulary, IDs, commands, how commands
should behave, agent rules); new `dev/CLAUDE.md` holds invariants, layout, spec-update rule, how to
add a rule, agent-editing rules. Vocabulary and IDs live in the root only — both hats need them and
two copies would drift.

**Hat detection.** The constraint that rules out the obvious answer: a teacher's repo *is* a clone,
so anything shipped also lands there — a committed marker cannot discriminate, nor can "`dev/`
exists". So: **default teacher** (right by base rate, and fails safe), a **gitignored
`dev/.developer`** marker (never clones, so it is a reliable developer signal), and **task
escalation** for framework work.

**Mode reporting** (Avin's addition) uses two mechanisms because they fail differently: a
`SessionStart` hook that both prints a line and *injects the mode into the model's context* — so the
model is told its hat rather than inferring it — and a `CLAUDE.md` instruction to state the mode,
which is the fallback and the only thing that can announce a *mid-session* change.

Verified by simulating a clone from the staged tree: teacher clone → 🎓 TEACHER; this checkout → 🔧
FRAMEWORK-DEVELOPER. Hook emits valid JSON in both modes. Also fixed the last dev-only leak in
`.claude/` (`write-items.md` cited `dev/_devlog`).

### Next

Unchanged: hand-test steps 0–1 (`dev/MANUAL-TESTING.md`) — now with a correctly-addressed
`CLAUDE.md`. Step 3 unblocked (fold in D-032). Step 2 waits on Q-028.

---

## Session 23b — 2026-09-12 — `classkit mode`: switching hats is a command now

Avin: *"maybe we should have a skill or a command that makes sure you start a session as a teacher
(no `.developer` file), and if you want to switch you run a special command that adds the file and
makes sure it is ignored?"* Yes — and the "makes sure it is ignored" half is the point, because that
is precisely the bug this session hit: `.gitignore` was untracked on this machine, so the rule
existed only locally.

Built `classkit mode` (`src/classkit/mode.py`): report the current hat; `developer` **verifies the
ignore rule before creating the marker** and refuses with an explanation if it is missing; `teacher`
removes it. Idempotent both ways, and it prints that a running session must be restarted — the
SessionStart hook reads the marker once, at startup.

**Code rather than a slash command**, deliberately: the ignore check is mechanical and must not be
skippable (D-018, code verifies), and a `/developer-mode` command would live in `.claude/commands/`
and therefore appear in every teacher's command list.

Six tests (`tests/test_mode.py`), suite now **42**. The one that earns its place asserts the marker
is ignored **in the real framework checkout**, not a fixture — so if `.gitignore` is ever dropped or
untracked again, the suite fails instead of the framework silently mis-hatting every teacher.
Verified by hand that the CLI and the hook agree in both directions.

Documented as step 1 of `dev/CLAUDE.md`'s developer setup, and referenced from the root `CLAUDE.md`
hat section.

### Next

Unchanged: hand-test steps 0–1 (`dev/MANUAL-TESTING.md`). Step 3 unblocked (fold in D-032). Step 2
waits on Q-028.

---

## Session 24 — 2026-09-12 — Root docs re-derived from the spec (step 8, pulled forward)

Avin is about to hand-test steps 0–1 and will **follow `GETTING-STARTED.md` while doing it**, so the
root docs have to be true now rather than at step 8. Checked both against the spec and found real
misalignments — most of them places where the docs still described the design as it stood *before*
D-020/D-028/D-031.

**Wrong in `README.md`:**
- "Every in-class Activity **must** reference at least one Guiding Question" — D-028 relaxed this to
  a warning with a capped total.
- "Every Study Session must have at least one *complete* Study Path … that fits inside the session's
  time budget" — D-020 replaced that with the sum of per-question `est_minutes`.
- Study Paths drawn under Guiding Questions — D-020 moved them to the session.
- No Syllabus or Course Outcomes anywhere — the top layer (D-021) was missing from the model.
- Status said "Phase 1"; `gem-builder` and `/build-gem` unmarked as deferred.

**Wrong in `GETTING-STARTED.md`:**
- *"`time_constants` … decides whether the validator believes a 25-minute session is doable"* — no
  longer true since D-020/D-025: it is **advisory**, used to *propose* an estimate the teacher
  approves and to help the critic spot a bad one. The validator sums `est_minutes`.
- `/design-unit` described as designer → lesson-planner → assessment-writer; **D-031a swapped the
  last two** (the planner needs real quiz-item ids).
- `/plan-units` described as writing unit skeletons only — it writes the syllabus first (D-029/i).
- Both "what the validator will not let you get away with" bullets were the pre-D-020/D-028 wording.
- The stepwise / never-overwrite / revise-not-regenerate protocol (D-030) was absent, although it is
  teacher-visible behaviour they should hold the commands to.
- The `gem` setting was documented for a deferred phase.

**Also fixed, because he will read the file it produces:** `templates/course/course.yaml` shipped a
`gem:` block for a phase that does not exist (G-16, now ticked) — removed, and `time_constants`
annotated in the template as advisory. The optional field stays in `course.schema.json`, so a course
that sets it still validates. Fresh scaffold still validates with 0 errors.

**Spec change this surfaced (§3.1):** `/write-items`' role in Core was ambiguous — it was listed
only under deferred work, yet `/design-unit` already writes the entry quiz. Now stated explicitly:
in Core `/write-items N` is scoped to entry-quiz items (adding to or reworking what `/design-unit`
produced); its homework and exam roles defer to Assessment.

**Honesty about what is built:** `GETTING-STARTED.md` gained a banner saying the `/` commands are
being implemented one at a time and the ledger is authoritative, and the one documented setting that
does not exist yet (`in_class.max_unmapped_minutes`) is marked *not built yet*. Without that, a
teacher following step 5 during this test would hit commands that are not there and reasonably
conclude the framework is broken.

### Next

Unchanged: hand-test steps 0–1 with `dev/MANUAL-TESTING.md` (and now `GETTING-STARTED.md`). Step 3
unblocked (fold in D-032). Step 2 waits on Q-028.

---

## Session 25 — 2026-09-29 — Ingest and the course log designed (→ D-035, D-036); Q-028 resolved

Avin returned after hand-testing steps 0–1 in a clean clone ("I believe it went fine").

**Sequencing disagreement, resolved in Avin's favour.** Claude recommended step 3 (`/plan-units`)
next, deferring ingest design until step 4, on the grounds that step 3 has no structural dependency
on ingest and would reveal what ingest needs. Avin: settle ingest first — how it works, what it
does, how data is organized, how it runs incrementally — and anyway a teacher can't test step 3
without having done ingest. Conceded: the materials layout is the input contract for every
downstream agent, so building on an unspecified heap means rework; testing step 3 without ingest
tests a workflow no teacher follows; and "workflow order outside" was our own principle.

**Design (D-035, spec §8.7), built up with Avin:**
- General, not DS&A-shaped (Avin caught Claude assuming the pilot course). Teachers are not assumed
  organized: flat or nested, duplicates (PPTX + its PDF), any format, added over time.
- `source/` (the teacher's, never modified) vs `ingested/` (derived, one `.md` per material, flat,
  keyed by `M<NNNN>` — `M` because `S` already means Study Session). Flat so a rename or move never
  breaks a locator; the manifest re-matches by hash.
- Explicit anchors (`## Slide 18`, `## Page 34`, document headings) and a new rule
  `material_locator_resolves` — which makes invariant 7 **partly mechanical** for the first time:
  a fabricated "slide 18" in a 12-slide deck now fails validation.
- Links: `links.md` + `classkit add-url` (Avin's suggestion), plus URLs harvested from documents.
- Extraction is code (reproducible anchors): built-in md/txt/pptx/pdf/docx, optional pandoc and
  LibreOffice, everything else `unsupported` and reported — proactive for common formats, reactive
  for the rest. Scanned PDFs and media flagged, not handled.
- Pre-flight report and approval gate before a long run (Avin's point); incremental and resumable
  by hash; hand edits to ingested text detected and preserved (Avin wanted them editable).

**Course log (D-036, spec §8.8)** — Avin's idea: `LOG.md` records what changed in the course and
why, which git's byte history does not. Course only, never framework development. Every approved
step of every command is an entry; written by `classkit log`; agents read recent entries first.

Ledger: 18 new rows (13 decisions, 121 changes). GETTING-STARTED's materials step updated. Docs only.

### Next

Implement step 2 (ingest + course log) in a fresh session, from the spec, with a gap report. Then
Avin hand-tests `/ingest` against real materials. Then step 3.

---

## Session 25b — 2026-09-29 — The teacher is the authority (→ D-037)

Avin raised a concern about the whole validation direction: *"you over-push for validation tools…
the teacher is the authority, and it is his responsibility to check everything he delivers… I don't
want the framework to be too strict in preventing out-of-the-box solutions or some inconsistencies
(which are sometimes ok in class)."*

Claude agreed and owned the drift: `VISION.md` already framed validation as a feature for catching
*agent* mistakes, yet successive decisions kept promoting pedagogical checks to `error`.

**Resolution (D-037):** validation informs, never overrules. Rules split mechanically — *names
something that doesn't exist* → integrity → `error`; *missing or unconventional* → advisory → `warn`.
New severity **`alert`** for coverage (Avin: advisory, "could be a temporary glitch… but a
HIGH-priority alert"). Twelve pedagogical rules demoted from error to warn — including
`in_class_missing` (a holiday week is legitimate). Teachers override course-wide in `course.yaml`
`rules:` and accept single exceptions with `accepted:` in front matter, which then stops nagging but
stays counted and logged. Agents fix what they caused and never overrule the teacher. Schemas check
shape, not pedagogy. Never-overwrite stays hard — it protects the teacher rather than constraining them.

Written into VISION, the spec (§2.2, §8.2, §8.4 rewritten, invariant 4), both CLAUDE files, README
and GETTING-STARTED. Ledger: 8 rows. Docs only; the re-classification of already-built rules is
implementation work.

### Next

Implement step 2 (ingest + course log) — and fold D-037 in, since step 2 touches the validator
anyway.

---

## Session 25c — 2026-09-29 — Working stance: honest, rigorous, unbiased

Avin noticed Claude had been too agreeable — "good call", "good catch", fast concessions — and asked
that the default behaviour, for both teachers and developers, be honest, rigorous, unbiased and
critical, recorded in `CLAUDE.md`.

The pattern was real, and it had a concrete cost: when agreeing to D-037 (validation advisory),
Claude did not point out that it contradicts spec §3.3's founding claim that both failure modes
"fail loudly at design time". Fixed now: §3.3 says the bet is that they are made *visible*, not
fatal, states that this is a knowing weakening, and §9 lists the residual risk (a teacher who ignores
warnings gets none of the protection).

Recorded as "How to work — for both hats" in the root `CLAUDE.md` (loaded in every session; pointed
to from `dev/CLAUDE.md`, not duplicated), in the handoff's working agreements, and in Claude's
memory.

---

## Session 26 — 2026-09-29 — Step 2a built: validation re-classified (D-037), the course log (D-036)

A fresh, context-free implementation session working from the spec, with the required gap report:
`../reviews/impl-gaps-step-2a.md` (24 entries, 6 flagged ⚑ for Avin). Step 2 was split: **2a**
(D-037 + D-036, this session) and **2b** (ingest, D-035).

**Built** (three commits, each green):
- **Severities.** New `alert`: printed first, never fails. `validate` exits 1 only on errors,
  `--strict` also on alerts and warnings. `DEFAULT_SEVERITY` is now a *complete* table: an
  unregistered rule raises, and a test pins that only integrity rules default to `error`. Ten
  pedagogical rules demoted to `warn`; `objective_coverage` → `alert`.
- **Splits.** `activity_without_guiding_question` and `activity_references_other_unit` (warn) split
  from `activity_references_guiding_question` (error: exists nowhere); `item_no_correct_choice`
  (warn) split from `item_reference`. Activity `guiding_questions` no longer schema-required.
- **Teacher overrides.** `course.yaml` `rules:` over the methodology; `accepted: [{rule, reason}]` on
  all five front-matter schemas, suppressing per file and counted (including entries that no longer
  match anything); `unknown_rule` (warn) for a mistyped rule name.
- **`outcome_reference`** (error), with objective `outcomes` added to the unit schema *optional*.
- **Course log.** `classkit log TITLE --changed --why [--file]…`, append-only by construction;
  `scaffold course` starts `LOG.md` with an entry listing what it created.

**Found by a test, not by reading:** YAML 1.1 parses a bare `off` as `false`, so the spec's own
`rules: {x: off}` failed the schema. It is normalised on load (G-5).

**Housekeeping:** the ledger's count line was wrong before this session (said 14/1/88, table had
16/1/112); recounted: **27 built, 3 in progress, 99 not started**. Ledger rows for steps 3/4/6 that
still prescribed `error`/schema-`required` for rules D-037 demoted are struck through and annotated.
§8.2's `Req` column contradicted §8.4 on `outcomes` and `answer`; fixed toward §8.4.

Suite: 42 → 92 tests.

### Next

Avin: the ⚑ items in the gap report — the split rule names (G-1, now teacher-facing API), whether
`accepted:` requires `reason` (G-6), `unknown_rule` at warn despite the mechanical line (G-10), who
logs an acceptance (G-13), and two step-4/5 schema questions (G-19 `rubric`, G-20 `est_minutes`).
Then step 2b (ingest) in a fresh session.

---

## Session 27 — 2026-09-29 — Step 2a reviewed and its outcomes applied (→ D-038)

Step 2a (D-037 validation re-classification + D-036 course log) was implemented by a fresh session
(gap report `reviews/impl-gaps-step-2a.md`, 24 entries, 6 needing a decision) and reviewed
independently by Gemini (`reviews/impl-review-step-2a.md`; verdict "needs fixes first", one BLOCKING
finding: G-6). Avin asked whether to review or triage gaps first; Claude advised review first — the
flagged gaps were small, and the implementer had edited the spec in 13 places without author
approval, which the review should see before Avin ratified them.

Claude's assessment of the review, before acting on it: the BLOCKING finding verified in the schema
and reached independently; but the review skipped test quality, touched only one invariant, reported
no nits, mislabelled a couple of edits — and missed two defects found by reading one schema file (a
documented example naming a rule that does not exist yet; the `rule` pattern re-creating the G-6
inconsistency for capitalised typos).

Avin accepted the consolidated recommendations; applied in this session (details in D-038): `reason`
optional + `accepted_without_reason`; no pattern on `rule`; `write.append()` / `--append` and the log
now writes through it; examples use `in_class_missing`; G-13 wording; G-7/9/11/14/15/16 ratified;
G-19/G-20 recorded for steps 5/4; unit `objectives` kept required, deliberately. Spec §8.2, §8.4,
§8.6, §8.8 updated. **99 tests green** (+7).

### Next

**Step 2b — ingest (D-035).** Implementation prompt and review prompt use the 2b scope block. Then
Avin hand-tests `/ingest` on real, messy materials — the check no document or code review can do.


## Session 28 — 2026-10-01 — Step 2b built: ingest (D-035)

A fresh session implemented step 2b from the spec, with the 2b scope block as its brief. Gap report:
`reviews/impl-gaps-step-2b.md` — 30 entries, **8 needing a decision (⚑)**. Suite: **163 tests,
green** (+64: 51 in the new `tests/test_ingest.py`, 13 rule tests in `test_course_lifecycle.py`).

Built, layer by layer:

- **Schema** — `schemas/manifest.schema.json`. The spec's table plus `source_hashes`, `removed_at`,
  `merged_into`, `note`, `duration` (⚑ G-2: each closes a hole the spec's own text opens).
- **Templates and scaffold** — `materials/source/links.md` (instructions in an HTML comment, so it
  parses to no links) and `materials/ingested/`. The materials README is rewritten for both layers.
- **Tooling** — `src/classkit/ingest/`:
  - `extract.py`: a registry keyed by extension. md, txt, pptx, pdf and docx are built in; pandoc
    and LibreOffice are used if installed. Statuses `unsupported` / `no-text` / `media`, always with
    a hint.
  - `links.py`: parse links.md, `add-url`, best-effort metadata.
  - `manifest.py`: load, save, never-reused ids.
  - `core.py`: scan, then **one `reconcile()` shared by pre-flight, the run and the validator**.
    It handles moves, exact duplicates, detached copies, removals and restores. The manifest is saved
    after each material, and an orphaned `.md` is adopted on resume.
  - Hand edits are refused through the write path. `--overwrite ID` and `--keep ID` are the
    teacher's answers, and the run exits 3.
- **CLI** — `classkit ingest [--preflight]`, `classkit add-url`, and `classkit material
  set|merge|duplicates` (⚑ G-1: how the classifier records anything without Write/Edit).
- **Validator** — `material_locator_resolves` (error, integrity) over the fields in `LOCATOR_FIELDS`:
  study-path `ref` and activity `materials`. Step 4 adds `answer` as one line. Also
  `materials_not_ingested` (warn, one finding), and the manifest is schema-checked.
- **Agent layer** — `/ingest` rewritten as four gated steps, each logged with `classkit log`. New
  agent `material-classifier` (Read, Grep, Glob, Bash): it sets kind and units through `classkit
  material set` and *proposes* merges. The command merges only what the teacher confirms.
- **Docs** — spec §8.7 carries every mechanic decided (listed in the gap report, ⚑ ones marked as
  provisional). Also updated: `CLAUDE.md`, `GETTING-STARTED.md`, `README.md`, `dev/CLAUDE.md`, and
  `dev/MANUAL-TESTING.md`, which has a new 2b section for Avin's hand test.

Self-review caught three defects before commit (gap report, last section): a module-level hack for
found links, a retry loop on corrupt files, and a test passing for the wrong reason. Commits were
reordered before pushing so each is green on its own, checked in a scratch worktree.

**Untested:** pandoc and LibreOffice when *installed* (neither is on this machine), real-site
metadata fetching, PDFs from real tools, and scale. **The classifier prompt has never run.**

### Next

1. **Independent review of 2b**, given the same scope block (`reviews/impl-review-step-2b.md`).
2. **Avin decides the ⚑ entries** G-1 … G-8. The spec edits that write them in are provisional.
3. **Avin hand-tests `/ingest` on real, messy materials** (`dev/MANUAL-TESTING.md`, "Step 2b").
4. Then **step 3** (`/plan-units`, folding in D-032). It must also point `curriculum-architect` at
   `materials/ingested/` rather than `source/` (gap G-30).

## Session 29 — 2026-10-01 — Step 2b reviewed and its outcomes applied (→ D-039)

Read the implementer's gap report and the independent review, verified the review's claims against
the code, and took Avin through the open items one at a time. Findings on the review: the blocking
finding (classifier has Bash) pointed at a real hole but overstated it — invariant 5 guarantees the
write path, not a sandbox, and four other agents have Bash; both missing-test findings were real; it
accepted G-6 and G-7 without engaging the case against. Avin decided:

- **G-1 (b)** — classifier read-only; returns YAML; new `classkit material apply`, all or nothing.
- **G-7 (b)** — `classkit ingest` logs every run that changes something; `--why`, `--no-log`.
- **G-3 (a)** — physical pages, plus: every book citation's `note` gives section, exercise/question
  number and printed page.
- **G-6 (b)** — `/plan-units` re-maps materials' `units` (step 3).
- G-2, G-4, G-5, G-8 ratified.

Built: `material apply`, ingest logging (`log_summary`), the read-only agent and the reworked
`/ingest` step 3; the two review test gaps (moved/removed sources warn; locators read hand-edited
anchors). Spec §3.1, §5.1, §6, §8.2, §8.7, §9; `CLAUDE.md`, `GETTING-STARTED.md`, `README.md`,
`MANUAL-TESTING.md`; D-039 in the decisions and the ledger. 173 tests (+10).

### Next

1. **Avin hand-tests `/ingest`** on real, messy materials (`dev/MANUAL-TESTING.md`, "Step 2b").
2. Then **step 3** (`/plan-units`, D-032, the `units` re-map, G-30).

## Session 30 — 2026-10-01 — Avin's hand test of 0–2b; private and instructor material (→ D-040)

Avin hand-tested steps 0–2b with real material and wrote `reviews/manual-test-step-0-2b.md`. His
main concern was privacy, copyright and book PDFs. Claude found that no course file is gitignored,
so a push publishes every PDF and its full text — not flagged by the report or by earlier sessions.
Decided with Avin, one at a time: `source/private/` with a committed index and a local full text;
`audience` with an alert and a hard refusal at export; missing private ≠ removed; a scaffolded
`course/.gitignore` and `private_material_committed`; `classkit doctor` (Avin's idea) and the
principle that `validate` judges the course and `doctor` the machine. Spec, D-040, ledger (11 rows),
handoff; interim warning in `GETTING-STARTED.md`. Nothing built. The rest of the report is still to
be gone through.
Continued the same day: went through the rest of the report's design items with Avin — F-11/F-15
(duplicate detection dropped), F-13 (no link harvesting), F-17 (`units: all`), F-19 (coverage report
persisted; partial material and the `unit_map` in the syllabus), F-21 (one resource-kind vocabulary),
F-24 (diff on refusal), F-26 (locators in prose), P-2 (invariant 5's scope; `write --diff`). All
added to D-040, the spec and the ledger (169 changes; 51 / 5 / 113). Checked F-21's side note
(schema errors print as warn) — does not reproduce. Remaining: Avin's go-ahead on the plain fixes,
then step 2c.


## Session 31 — 2026-10-01 — Step 2c-1 built: private and instructor-only material; `classkit doctor` (D-040)

A fresh implementation session, working from the spec. Scope: the ten D-040 ledger rows tagged
[2c-1]. All built.

- **Scaffold:** `course/.gitignore` (create-only, written first). A re-scaffold that creates
  something on a course that already has a log appends an entry.
- **Ingest — private material:**
  - anything under `source/private/` (in any case) is private;
  - its committed `ingested/` file is an index: `text: index`, every anchor with one-line labels
    (printed page, outline sections, slide titles, headings), no body text, and no body-derived
    title;
  - its full text goes to `materials/private-text/`, protected by `private_text_hash`; both files
    are checked before either is written;
  - a missing private source is "not on this machine", never removed;
  - a source appearing on a machine gets its full text without changing anything committed or
    writing to the log;
  - moves into and out of `private/` rewrite the committed copy;
  - `classkit material remove`;
  - `audience` in `apply` and `set --audience`;
  - no link harvesting from private text.
- **Validator:** `instructor_material_cited` (alert, over `STUDENT_FACING_FIELDS`) and
  `private_material_committed` (warn, `git ls-files`, `:(icase)`, skipped outside git).
  `materials_not_ingested` reconciles with `local=False`.
- **`classkit doctor`** (`src/classkit/doctor.py`): read-only; `ok` / `note` / `ACTION`, each action
  with its fix; exit 0/1.
- **Agents:** the classifier proposes `audience` with reasons, flags published books outside
  `private/`, and reads private text or says "index only here". `/ingest` gains a step 0
  (`doctor`).
- **Docs:** `CLAUDE.md`, `GETTING-STARTED.md` (the interim warning replaced), README, the
  scaffolded `source/README.md`, `dev/CLAUDE.md`, and a 2c-1 section in `MANUAL-TESTING.md`.
- **Spec:** "(target, D-040)" removed from what was built; the decided details are written into
  §8.4, §8.7 and §8.8 and into the naming and data-flow tables.
- **Ledger:** 61 / 5 / 104 of 170.
- **Tests:** 233, up from 173. New files `test_private_material.py` and `test_doctor.py`, plus
  lifecycle rule tests. Every fixture, including a PDF with an outline and printed labels written by
  pypdf, is generated in `tmp_path`.

Running the real CLI end to end in a scratch git repo found two things no unit test had:

- **Avin's `~/.gitignore_global` ignores `.gitignore` itself.** So `course/.gitignore` is never
  committed and no clone is protected. Locally everything looked fine. `doctor` now checks it (G-4).
- **A copy (not a move) of a public book into `private/`** leaves the material public. `doctor` says
  so (G-5).

The test for "no body text in the index" also caught a PDF's first line leaking as its title (G-9).

Gap report: `reviews/impl-gaps-step-2c-1.md` — 23 entries, six ⚑. The weightiest:

- **G-1:** `private_text_hash` is committed, but extraction differs across library versions.
  Recommended: a self-certifying hash in the full text's own front matter.
- **G-2:** two machines with different copies of a book.
- **G-3:** a stale full text is refused, because it cannot be told apart from an edited one.

### Next

1. **Avin:** remove `.gitignore` from `~/.gitignore_global` (or force-add it per course repo), and
   decide the ⚑ entries G-1 … G-6.
2. **Step 2c-2** — the rest of the hand test's fixes. Then **one independent review of 2c-1 and
   2c-2 together**, then Avin re-tests (`MANUAL-TESTING.md`, "Step 2c-1"), then step 3.

## Session 32 — 2026-10-01 — Step 2c-1's gap report decided (→ D-041); 2c-2 prepared

Read the 2c-1 gap report, checked it (233 tests green; G-4's global excludes file, G-22's `0600`
files and the one `unlink` outside the write path all confirmed). Claude's own spec error surfaced:
"extraction is the same on every machine" holds for one library version only. Avin decided: G-1/G-3
(b) self-certifying full text; G-2 (c) last machine wins + `doctor` note; G-4 `course_gitignore_missing`;
G-5 as built; G-6 (a). Plain fixes added: `write.remove()`, kept permissions, `.DS_Store`, the mode
check. Avin deleted `~/.gitignore_global`. Spec §8.6/§8.7/§8.4, D-041, ledger (177 changes).


## Session 33 — 2026-10-01 — Step 2c-2 built: the rest of the hand test's fixes, and D-041

Built every ledger row tagged [2c-2] (D-040 and D-041 blocks), in four groups, each its own
commits and green. **289 tests** (+56; new `tests/test_extraction_quality.py`).

- **D-041.**
  - The private full text certifies itself: `body_hash` = the file's hash without that line. A stale
    or other-library full text that still matches is refreshed; an edited one is refused.
    `private_text_hash` is retired (the schema accepts it; a pre-D-041 text is judged by it once).
  - Ingest's one deletion goes through the new `write.remove(path, expected_hash)`.
  - Replacing a file keeps its mode; new files get `0666 & ~umask`, not `0600`.
  - `doctor` reports a differing private copy as a note.
  - `course_gitignore_missing` (warn, consistency).
  - `classkit mode developer` refuses when `.gitignore` is untracked.
  - `.DS_Store` is ignored in both `.gitignore`s.
- **Removals (D-040).**
  - Gone: suspected-duplicate detection (name and content), `material duplicates`, and the gate-3
    question.
  - Gone: link harvesting. A link harvested by an older version is marked removed by the next ingest,
    and `add-url` restores its id.
  - Hyperlinks stay readable in the ingested text as `[text](url)` (the spec had assumed they
    already were).
- **Additions (D-040).**
  - `units: all`.
  - The coverage report states its scope and is saved by `/ingest` to `materials/coverage.md` through
    the write path.
  - `material_locator_in_text` (warn) over Markdown bodies.
  - A hand-edit refusal shows the diff by anchor.
  - `classkit write --diff`.
  - Path kinds `slides` and `notes`.
  - The classifier mentions two-format relations ("cite the deck") and course-resource links.
- **Plain fixes.**
  - F-06: DOCX text boxes, Choice or Fallback.
  - F-07: Office Math as linear text.
  - F-08: empty slides/pages and low yield, under "Check these extractions".
  - F-03/F-10: reader noise captured, reported once by name.
  - F-09: ligatures expanded, fonttools added.
  - F-12: file-name metadata titles rejected; no PDF first-line titles.
  - F-14: the time estimate.
  - F-23: the pre-flight names what changed.
  - F-25: validate names `--keep`/`--overwrite`.
  - F-02: plurals.
  - F-20: template wording.
  - Docs: F-01, F-18 and a 2c-2 section in `MANUAL-TESTING.md`; F-27 in `GETTING-STARTED.md`.
- **Spec:** "(target …)" removed from everything built; the decided details are written into §8.4,
  §8.6 and §8.7. **Ledger:** 76 / 6 / 95 of 177.

Gap report: `reviews/impl-gaps-step-2c-2.md`. Three ⚑:

- **G-1:** harvested links in an old manifest are retired on the next ingest. Avin's M0011–M0021
  go; the Gem comes back with `add-url`.
- **G-2:** a changed private source is now a `doctor` note, not an ACTION.
- **G-3:** re-ingest never replaces a title, so `manual.dvi` survives in an existing course.

Not verified, and only the re-test can do it: fontTools repairing CLRS's broken characters (F-09);
the low-yield thresholds; the classifier prompt's new behaviour.

### Next

**One independent review of 2c-1 and 2c-2 together.** Then Avin decides the ⚑ entries of this
report and re-tests (`MANUAL-TESTING.md`, "Step 2c-1" and "Step 2c-2"; a fresh course shows the
extraction fixes), then step 3.

## Session 34 — 2026-10-01 — Step 2c-2 checked; its ⚑ entries accepted; review prepared

Pulled 2c-2, 289 tests green. Avin accepted G-1/G-2/G-3 as built (D-041 addendum). G-6 showed a
second unverified claim of Claude's in the spec (hyperlinks "readable" in the ingested text) — now
a working rule: verify before writing a claim about the code. Next: one review of 2c-1 + 2c-2.

## Session 35 — 2026-10-01 — The 2c review checked; D-042 built; step 2 ready for re-test

The independent review of 2c-1 + 2c-2 (Gemini) found nothing blocking. Claude checked it: no write
or delete outside `classkit.write` (only `mode.py`'s developer marker, which is framework-side); the
removals complete; but a real gap missed by both implementers and the reviewer — agents read a
private book's full text and write committed files, and nothing stopped them quoting it. Avin chose
both layers → **D-042**: the rule (root `CLAUDE.md`, classifier, spec §8.7/§9) and
`doctor.check_quotation` (12-word shingles; ~2.8 s and ~150 MB on a 600k-word text, measured).
Two test-expectation errors of Claude's own were caught by running the tests (a "short phrase" that
shared exactly 12 words; a sentence miscounted as 25 words). 294 tests. Step 2 marked built and
reviewed in the ROADMAP, closing after Avin's re-test.

## Session 36 — 2026-10-02/03 — Core re-oriented; the syllabus increment specified (→ D-043)

Avin proposed moving on from tooling and corner cases to the agents, finishing Core's spec in
increments he can check on a real course. Claude agreed, with evidence (the classifier was the
strongest part of the hand test; the class-hour agents have never run) and with its own share of the
drift named. Found: no syllabus agent or command exists (D-029/D-032 designed, never built). Decided
with Avin (D-043): `/plan-syllabus` as its own milestone (supersedes D-029's one flow), grading
draftable, approvals recorded in the file with a hash + `classkit status` (over a progress file),
one verb per meaning (`/write-items` retired), best effort over completeness, the front-matter/body
rule, four gated steps. Also fixed a stale order in §5.2 (quiz before the class hour, D-031a). Spec,
D-043, ledger (rows [3-syllabus], [units]; 194 changes).

## Session 37 — 2026-10-03 — The syllabus increment built ([3-syllabus], D-043)

Built every [3-syllabus] row (18) from a fresh session. Tooling: the syllabus schema (`unit_map`,
`reading`, `approved {on, hash}`, `assessment` draftable) and template (front matter with commented
examples; a default body skeleton of descriptor sections, AI-use policy included; the template's
hardcoded minutes removed, invariant 2); `classkit approve syllabus` (`approve.py`: record in the
file, hash over parsed front matter + body, textual edit re-parsed before writing, logged);
`classkit status` (`status.py`: syllabus state, unit map with units present or not, materials,
last log entry; read-only, committed files only). Found by testing: YAML 1.1 reads the spec's
`on:` key as `True` — the loader normalises it (gap G-1 ⚑, rename suggested).

The product: `syllabus-designer` (read-only; tasks evidence / draft / revise; returns the whole file;
TBD rather than invention; AI-use policy always proposed where an AI study path is used; D-042),
`/plan-syllabus` (status → evidence → draft through the write path → revision rounds by `--diff` →
`classkit approve syllabus`), `/review-syllabus` and the critic's syllabus section. Narrowed
`curriculum-architect`'s description; `/ingest` shows status first. Docs, spec (§3.1, §5.1, §5.2,
§8.2, §8.9 — target marks removed, §8.9's hash and write refined), MANUAL-TESTING section, gap
report (`reviews/impl-gaps-step-3-syllabus.md`, two ⚑). 318 tests. Ledger 98 / 6 / 91 of 195.

### Next

Avin runs `/ingest` + `/plan-syllabus` on a real course (`MANUAL-TESTING.md`, "Step 3-syllabus") and
judges the agent's output; prompts revised from what he finds. Decide G-1 and G-2. Meanwhile, the
spec of the [units] increment.

## Session 38 — 2026-10-03 — Commands vs agents vs skills (→ D-044); the syllabus increment adjusted

Avin asked for the command/agent distinction to be laid out and tightened. Agreed: command =
procedure in the conversation, agent = fresh context or independence, skill = shared craft; the agent
drafts, the chat revises. The syllabus build (Session 37) predated it, so Claude adjusted it here: new
`writing-a-syllabus` skill (craft moved out of the agent and the critic), `rework` replaces `revise`,
`/plan-syllabus` step 3 revises in the chat. Gap report ⚑: `approved.on` → `date` (Claude's YAML-1.1
trap, again), unit-map evidence locators warn. Spec §2.1, §5.1, §8.4; D-044; ledger; 320 tests.

## Session 38b — 2026-10-03 — The teacher works in the chat (→ D-045)

Avin preferred working only in the chat UI. Agreed the chat runs `classkit`; made it explicit: spec
§5.2 principle, root `CLAUDE.md` instructions (how to run it, report faithfully), read-only commands
pre-allowed in `.claude/settings.json`, `GETTING-STARTED.md` and `MANUAL-TESTING.md` chat-first.

## Session 39 — 2026-10-03 — The units increment specified (→ D-046)

Remaining Core increments laid out (units, home study, class hour with entry quiz, review). Units
decided with Avin: optional `difficulties` with origin; *planned*/*designed* states; the materials
re-map moved to `/plan-syllabus`; `unit_map_mismatch` built now; `planning-units` skill. Spec §3.1,
§5.1, §8.2, §8.4, §8.9; D-046; ledger (219 changes).


## Session 40 — 2026-10-03 — The units increment built (every [units] row)

Built from D-046, with the syllabus increment as the model (D-044). **The product:** the
`planning-units` skill (objectives assessable, few and broad — the methodology's number — each naming
the Course Outcome it serves and never stretched to fit; prerequisites and home-study order; what a
lecture week cannot fit, the cut left to the teacher; difficulties specific enough to design against,
`teacher` vs `proposed`; revising; the rules); `curriculum-architect` rewritten read-only (Read, Grep,
Glob; tasks `draft` / `rework`; reads `ingested/` and `coverage.md`, never `source/`; returns per unit a
report, its questions — always "what do your students find hard?" — and the complete `unit.md`;
proposed difficulties in the report, not the file); `/plan-units N…` rewritten (status → architect →
gate, corrections and accepted difficulties applied by the chat → scaffold with the map's title + write
through the write path → validate → revision rounds in the chat → `classkit approve unit N --stage
planned`); `/plan-syllabus` step 5 (re-map the materials' unit hints against the approved map, the
teacher's own hints kept, `classkit material apply`); `course-critic` gains a unit-plan section loading
the skill, and `/review-unit` routes a planned unit to it.

**The tooling:** `unit.md` schema and template (`difficulties`, `approved {date, stage, hash?}`; the
placeholders name `CO1`/`CO2`, as the D-021 ledger planned); `classkit approve unit N [--stage]` (the
syllabus's record mechanism generalised; *designed* hashes unit.md, sessions, in-class and entry-quiz
items in a fixed order, slug-independent); `classkit status` per unit (not started / drafted / planned /
designed, edited since, a count line); `unit_map_mismatch` (warn) and `objective_maps_to_outcome`
(alert), both consistency rules. Docs (README, GETTING-STARTED, both CLAUDE.md, spec — targets removed,
§8.4 and §8.9 made precise), a chat-style MANUAL-TESTING section. Gap report
`reviews/impl-gaps-step-3-units.md` (three ⚑: the default stage's trap, `objective_coverage` noise on
planned units, hint provenance). 352 tests (+32). Ledger 127 / 5 / 87 of 219.

Claude's own miss, caught mid-build: it first left the unit template's objectives without `outcomes`
(so a scaffolded unit alerted), then found the D-021 ledger's recorded plan to scaffold `CO1`/`CO2`
and followed it.

### Next

One independent review of the syllabus and units builds together (both gap reports; the code from
`d8a1351`, the syllabus increment's spec, to now). Then Avin checks both on a real course: `/plan-syllabus` to approval, step
5, then `/plan-units` for the first units with material (`MANUAL-TESTING.md`, "Step 3-syllabus" and
"Step 3-units"). Decide the three ⚑.

## Session 41 — 2026-10-04 — Step 3 finalized (→ D-047)

Checked the units gap report and the review of both builds (its blocking finding real but overstated;
one nit stale). Applied with Avin's go-ahead: step 2 split into 2a/2b in both commands, `approve unit`
requires `--stage`, `objective_coverage` skipped for planned units, CO1-only placeholders. Spec §5.1,
§8.4, §8.9; D-047; ledger (225); 353 tests. Ready for Avin's real-course check.

## Session 42 — 2026-10-05 — A developer audit's findings verified and applied

Avin ran a read-only audit in another session (at `9d0aa31`) and passed its findings here. Each was
verified before acting. **All eight held; one causal claim did not.**

1. **Q-005** asserted the pre-D-020 feasibility mechanism → annotated "Narrowed by D-020 and D-025":
   not a blocker; what remains is calibrating the advisory constants.
2. **Q-004** (pilot materials' format; "ingestion design depends on this") → **resolved** against
   D-035/D-040/D-042: ingest discovers formats itself; Avin's real materials were ingested in the
   hand test.
3. **Process gap** → `_devlog/README.md` gains the companion rule: a decision that resolves, narrows
   or re-frames a question annotates it in the same commit.
4. **Q-002** re-framed against D-040/D-042's private-material machinery (which covers source material,
   not generated exam items).
5. **Q-006** partly answered by events (org, private course repos, a second contributor's work on
   homework); the branch itself untouched.
6. **Q-003** notes that `python-pptx` is now a hard dependency (for extraction).
7. **`schema_unavailable` and `unit_count`** had no test → four tests added (fewer, more and as many
   units as declared; the schema layer skipped without jsonschema). 357 tests.
8. **`.claude/settings.local.json`** not ignored → added to `.gitignore`. **Correction to the audit:**
   it says "the rewritten .gitignore dropped the line". `git log -S` shows the line was **never** in
   the repo's `.gitignore`; the file was covered only by Avin's global excludes file, deleted on
   2026-10-01 (D-041, G-4). Same mechanism that surfaced `.DS_Store`. The stale copy on Avin's machine
   is left for him to delete.

**The sweep found what the audit missed:** **Q-029** still described the cross-unit collision as an
*error*; D-037 had made it the warning `activity_references_other_unit` — annotated. **Q-021**'s code
sizes were from August; **Q-027** item 2 is partly covered by D-020 — both annotated. Q-007, Q-022,
Q-026, Q-030 and Q-031 checked and still accurate.

**Not touched, as instructed:** the `homework-by-shira` branch; the [design] increment.

## Session 43 — 2026-10-05 — Avin's real-course test triaged (→ D-048); the plain fixes built and merged

Avin's teacher report (`reviews/TEACHER-TESTING-ingest.md`) triaged into ~25 plain fixes and five
decisions. The plain fixes ([2d-A]) were built by a background agent in its own worktree (16 commits,
391 tests) while the decisions were taken with Avin (D-048: annotations extracted; `roles: [scope,
reference]`; per-item `accepted:`; ECTS stays in the body; `code` optional and placeholders in
`status`; Q-032 and Q-033 opened). Claude reviewed the branch before merging: tests, the prompt
diffs against the report, and the agent's own flags. Changed in review: the `û` → `fi` repair ran per
word and would have turned a real "flûte" into "flfite" — it now runs only when the substitution is
systematic across the document; a "1 materials changed" plural. **Open, for Avin:** the new
`scaffold course --language` flag conflicts with D-001 (English only, for now) — keep it or not.
Recorded the agent's other flags: the time estimate follows the teacher test's machine (an older one
may overrun it); the probe flags real French or German text, and says so; the refusal text keeps
"only if its author agrees". Spec §8.7 updated (titles, the repair and probe, DOCX bold labels,
`private/` scaffolded). 392 tests.

## Session 44 — 2026-10-05 — `--language` removed (D-001); worktrees ignored; [2d-B] built

Avin chose (b): no `--language` scaffold option (D-001), the comment kept. Asked about
`.claude/worktrees/`: it is Claude Code's location for agent worktrees; it was **not ignored** and
showed as untracked — now gitignored; the merged worktree and branch removed. Then [2d-B], built
here: the teacher's PDF annotations (highlights with the text under them, notes, free-text, stamps)
as a block per page — private: text only locally, counts in the index; `roles: [scope, reference]`
(schema, apply, `set --role`), proposed by the classifier, and `/plan-units`'s "book only — scope not
confirmed"; `accepted:` for one item (`id:`), findings carrying the item they are about (the first id
the message names, explicit for `unit_map_mismatch`, pinned by a test); `code` optional;
placeholders in `classkit status`; the ECTS line in the skill; prompts and docs; a MANUAL-TESTING
section. One reversal of my own: rewriting the schemas through `json.dump` reflowed them (421-line
diff) — reverted and re-done as text edits (32 lines). 405 tests.

## Session 44b — 2026-10-06 — Brought up to date for a fresh developer session

Avin will run the "Step 2d" re-test together with the unit-design test. Handoff's "Current state"
rewritten for a cold start (where the project is, what is built and checked, what is next — the
[design] increments' spec, home study first — and the known staging gaps not to fix early);
working agreements extended (decisions one at a time, simple fixes done directly, the chat-first
teacher, verify claims about code before the spec, check reviews before acting, when to push).
ROADMAP: a 2d step row and the count paragraph's "next".

