# Roadmap

Ordered by risk, not by appeal: each phase exists to find out whether the phase before it was
built on a wrong assumption. Open questions referenced as `Q-nnn` and decisions as `D-nnn` live in
`_devlog/`.

Status: ✅ done · 🔨 in progress · ⬜ not started

---

## ✅ Phase 0 — Content model and tooling

*Commit `d1decee`.*

The contract everything else writes into: JSON Schemas for course, unit, study session, in-class
session, assessment item and methodology; `question-driven-25` as data rather than code; the
create-only scaffold; the validator with its semantic rules; 14 tests.

Built first because agents need a target format. An agent asked to "design a study session" with
nothing to write into produces prose nobody can check, and you cannot tell a good unit from a
plausible-sounding one.

## ✅ Phase 1 — The agent layer

*Commit `cfde55f`.*

Seven agents, two skills, six teacher-facing commands, and `GETTING-STARTED.md`. The design work
runs in the teacher's own Claude Code, inside their course repo.

**Written but unexercised.** No real course has been built with it.

## 🔨 Design-draft pass (precedes the classroom)

A deliberate pass to finish a full *draft* of the design before classroom testing, so the testing
pushes against a stable target (Session 10). Scope: complete the content model, then agent coverage,
metrics, and the course lifecycle. Runs on the design doc and `_devlog/`, not on real course content.

- **Content model** — reviewing the flipped-class part for gaps. Decided: guiding questions gain an
  `answer` field (**D-019**) — *design only, not yet in the schema/validator/templates/agents.* Open:
  Q-023 (path vs. route), Q-024 (time-budget inputs), Q-025 (course-level outcomes), Q-026 (homework
  / programming assignments — a separate section).
- Then: agent coverage, metrics, course lifecycle. See the agenda in `_devlog/03-open-questions.md`.

Implementing what this pass decides ("fill the framework gaps") is a separate step, and precedes
Phase 2's real-course work.

## 🔨 Phase 2 — First real course

**The phase that will teach us the most, and the one most likely to invalidate earlier work.**

- Run `/ingest` and `/design-unit 1` against the real *Introduction to Data Structures and
  Algorithms* materials. **Blocked on Q-004** — where those materials are and in what format.
- Replace the placeholder numbers in `defaults/time-constants.yaml` with defensible ones
  (**Q-005**). Until then the feasibility check is arithmetic over a guess, which is worse than no
  check because it looks like verification.
- Revise agent prompts against what unit 1 actually exposes. Expect this to be substantial.
- Add validator rules for whatever goes wrong that nothing currently catches.

Exit criterion: one unit good enough to teach, not one unit that validates.

## ⬜ Phase 3 — Prove the methodology is really pluggable

D-011 claims any teacher can supply a different study-session design and the rest keeps working.
**That claim is currently untested**, and it is load-bearing for the whole multi-teacher premise.

Write a genuinely different second methodology — problem-set-first, or case-study, with different
session counts and a non-`question` goal type — and find out what breaks. Anything that has to
change in `src/` to accommodate it is a bug against invariant 3.

Cheapest possible way to discover the contract is wrong. Worth doing before more teachers commit
to it.

## ⬜ Phase 4 — Exports

- **PPTX** (D-006), via `python-pptx`. Deliberately minimal: the 50-minute hour should not be
  slide-driven, so the generator should make few slides the easy path and many slides awkward.
- **Gem bundles** — `gem-builder` drafts them today; this hardens the format and the exclusion
  rules once a real one has been used by real students.

## ⬜ Phase 5 — Moodle

Deferred at D-004. Quiz and item export first (the item schema is already atomic and tagged for
it); full sync only if it proves worth the maintenance.

## ⬜ Phase 6 — Multi-teacher hardening

The questions deliberately left open until someone actually hits them:

- **Q-007** — how framework updates should work once a teacher has edited or added things. The
  interim rule ("want updates? don't edit framework files") is a placeholder, not an answer.
- **Q-020** — move to a GitHub Organization. A personal repo has one permission level, so read-only
  access for teachers who merely clone is impossible, and D-014 cannot be implemented as written.
- **Q-002** — exam confidentiality. Decide before real exam content is committed anywhere; git
  history is permanent.
- Delete `_devlog/`, then make the repo public (**Q-016**).

---

## Not planned

Student-facing anything — submissions, grades, LMS replacement. The framework designs a course; it
does not run one.
