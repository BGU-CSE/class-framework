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
