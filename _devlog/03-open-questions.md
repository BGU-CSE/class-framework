# Open questions

When one is answered, move it to `01-decisions.md` as a numbered decision and strike it here.

---

## ~~Q-001 — What is the concrete mechanism for framework/course separation?~~ RESOLVED
**Resolved 2026-08-18 → D-009.** Two repos (option A), with shared git history: a course repo is
a clone of the framework repo with `origin` repointed and `framework` kept as an update remote.
Original analysis kept below for context.

Candidates:

| Option | Shape | Pros | Cons |
|---|---|---|---|
| A. Two repos | `class-framework` (this) + `course-<name>` per teacher | Cleanest separation; each teacher owns their repo; framework updates are a version bump | Two clones; need a documented contract + a way for the framework to find the course |
| B. One repo, split trees | `framework/` and `courses/<name>/` side by side | Single clone, easiest to start | Teachers' content lands in a shared repo; merge pain; contributions get entangled |
| C. Framework as submodule | Course repo contains framework as a submodule | Teacher-centric; natural update path | Submodules are a known usability tax for non-git-expert faculty |

Related sub-questions:
- How does a teacher pull framework updates without a merge conflict in their content?
- Where do *teacher-authored agent improvements* live so they can flow back upstream?
- Should there be a `course.config` at a known path that the framework resolves?

---

## Q-002 — Exam confidentiality
Live exam items in a repo that other teachers clone is a leak risk, and git history makes it
permanent. Separate private repo/submodule for active exams? Decide before any real exam
content is committed.

---

## Q-003 — PPTX generation toolchain
PPTX is decided (D-006), the mechanism isn't. Options: `python-pptx` from markdown, a template
deck + content injection, or Marp/Quarto → PPTX. Also: must the output be *editable* by the
teacher in PowerPoint, and does BGU have a required template?

---

## Q-004 — Pilot course source materials
What format are the existing *Intro to Data Structures and Algorithms* materials (PPTX / PDF /
Word / Moodle export), and where are they? Ingestion design depends on this.

---

## Q-005 — Time-budget constants for the flip
Need realistic constants to budget home study: reading rate (pages or words/min for technical CS
material), video watch rate, exercise time. Per-course tunable in a policy file (proposed: yes).
**Sharpened by D-010/D-012:** these constants are what make the validator's feasibility check real
— *every Study Session must have ≥1 complete Study Path covering all its Guiding Questions within
25 min.* Without defensible constants that check is theater. Not blocking the first push; blocking
the validator.

---

## Q-007 — How should framework updates work after a teacher has edited or added things?
**Deliberately left open (Avin, 2026-08-20):** *"I'm not sure yet how exactly the framework update
should work."* Governance is settled (D-014: framework repo is permission-controlled, course repos
are sovereign); the *update mechanism* is not.

**Interim rule, currently stated in README.md and D-014:**
> A teacher who wants future framework updates cannot edit framework files. Add new files instead.
> Edit freely only if you never plan to pull.

Still to decide: whether the framework should offer something better than "don't edit" — e.g. a
documented override directory, a config-driven agent-substitution table (`agents:` already exists in
`course.schema.json` for this), or a merge-assist command. Revisit once a second teacher has
actually hit the problem.

Original framing below.

### (original) Q-007 — Course-local customization without editing framework files
D-009 rule 1 says course repos add, never edit. So: where does a teacher put a course-specific
*variant* of an existing framework agent or template? Options: a naming convention
(`.claude/agents/<course>-lesson-planner.md`), a documented override directory the framework
agents defer to, or a config file that selects among framework-provided variants. Needs deciding
alongside the Phase 0 layout.

---

## ~~Q-008 — Scaffold command scope and overwrite behavior~~ RESOLVED
**Resolved 2026-08-20 → D-016.** Avin accepted both recommendations: all four granularities,
create-only. Restated analysis below.

### (superseded) Q-008

The *scaffold* is a framework command a teacher runs **inside their own course repo** to create
new content skeletons from framework templates — e.g. `scaffold unit 5` writes `units/05/unit.yaml`
plus four empty study-session files and an in-class-session file, pre-filled with the right
front-matter fields. It exists because D-009 rule 2 forbids the framework from *shipping* files
into the course tree; templates must be copied in on demand instead. D-015 strengthens this: the
course tree is created **entirely** by scaffold.

Two things to decide:

1. **Granularity** — which of these does it support? `new course` / `new unit` / `new study
   session` / `new assessment item`. Recommendation: all four.
2. **Re-run behavior** — the teacher runs `scaffold unit 5` again six months later, after editing
   unit 5 by hand, because the framework added a new template field. Does it (a) overwrite and
   destroy their work, (b) skip anything that exists, creating only what's missing, or (c) attempt
   a merge? Recommendation: **(b) — create-only, never overwrite.** Safe to re-run at any time;
   the teacher gets any newly-added files and keeps everything they wrote. Report what was skipped.

---

## ~~Q-009 / Q-010 / Q-011~~ RESOLVED
**Resolved 2026-08-20 → D-012.** In-class session is **50 min**; it is **per Unit**; **Unit
Objectives are kept** as a thin abstract layer above the Guiding Questions. D-012 also fixes the
canonical glossary.

---

## Q-020 — Personal account or a GitHub Organization?
**Raised 2026-08-20 when sharing came up. Blocks proper implementation of D-014.**

A repo owned by a **personal account** has exactly one collaborator permission level: **write**.
Read-only, triage and maintain are organization features. Two consequences:

1. **D-014 cannot be implemented as written.** "Permission-controlled, only developers may update"
   is not expressible — adding someone *is* granting push access to `main`.
2. **The D-009 clone flow has no read-only tier.** A teacher who only wants to clone the framework
   and start a course must be given write access to get any access at all.

Additionally, on the free plan **branch protection is unavailable for private repos** (it is
available for public ones), so `main` currently cannot require PRs or block force-pushes.

**Recommendation:** fine as-is for 2–4 trusted co-developers with a convention that `main` changes
go through a PR. Move to a **free GitHub Organization** as soon as consuming-only teachers appear —
free orgs give real roles (Read for teachers, Write for developers), which is what D-014 actually
describes. Transfer preserves history and redirects existing clones.

Interacts with Q-016: going public would also solve read access and restore branch protection, at
the cost of exposing `_devlog/`.

---

## ~~Q-016 — Repo visibility: public or private?~~ RESOLVED (with a correction)
**Resolved 2026-08-20 → private.** Avin chose private. **Note:** the repo was initially created
public and pushed; caught by an unauthenticated API check (`private: false`) during verification and
flipped afterwards. Nothing sensitive was exposed — `_devlog/` holds design notes only, no
credentials, student data, or exam content. Original analysis below.

### (superseded) Q-016
**Open — Avin asked for a recommendation. Blocks the first push only.** Account confirmed as
personal (`chenavin`); Avin is open to public.

**Recommendation: start private, go public at Phase 1.** The repo currently carries `_devlog/` —
internal design notes, half-settled decisions, open questions — and the design is still churning.
Private→public is a two-click change later; public→private does not un-distribute anything already
cloned. Flip it when `_devlog/` is deleted and the framework is worth being judged on.
If private, collaborators need explicit read access before they can clone-and-repoint (D-009).

---

## ~~Q-017 — How is the framework tested, given no example course?~~ RESOLVED
**Resolved 2026-08-20 → D-015 addendum.** No fixture files were needed: the test suite builds a
throwaway course in `tmp_path` with the scaffold itself, asserts it validates clean, then mutates it
to prove each rule fires. Also tests the templates as a side effect.

---

## ~~Q-018 / Q-019~~ RESOLVED
**Resolved 2026-08-20 → D-017.** Python (`classkit`, `src/` layout, PyYAML + jsonschema);
Markdown + YAML front matter for prose, pure YAML for configuration.

---

## ~~Q-012 — Where does the framework repo live, and under what name/visibility?~~ RESOLVED
**Resolved 2026-08-20 → D-013** (host `chenavin`, name `class-framework`, MIT). Visibility split
out into Q-016. Original analysis below.
**Blocking the first push.** Needed: GitHub account or organization (personal vs a BGU//project
org — matters because other teachers will contribute), repository name (`class-framework`?), and
initial visibility. Recommendation: **personal account, public, named `class-framework`** — the
framework holds no student data and no exam content (course repos are private per D-009), and
public makes the clone-and-repoint flow trivial for collaborators. Move to an org later if the
project grows; transferring a repo preserves history and redirects clones.

---

## ~~Q-013 — License~~ RESOLVED
**Resolved 2026-08-20 → D-013. MIT.** Original analysis below.

### (superseded) Q-013 — License
**Blocking the first push** (adding a license later is messy once others have contributed).
Two different things need covering: framework **code/tooling** and **templates/docs**.
Recommendation: **MIT** for the whole repo — maximally permissive, so any teacher can adapt it and
keep their course content unencumbered. Alternative if contribution-back matters more than
adoption: Apache-2.0 (adds a patent grant and requires change notices).

---

## ~~Q-014 — Does the framework ship an example course as a test fixture?~~ RESOLVED
**Resolved 2026-08-20 → D-015. No.** Developers test against their own real courses. Testing gap
this creates is tracked as Q-017. Original analysis below.

### (superseded) Q-014 — Does the framework ship an example course as a test fixture?
**Blocking the layout.** The validator and agents need something to run against, but D-002 forbids
course-specific content in the framework tree. Recommendation: ship a **tiny synthetic example
course** (2 units, obviously fake subject matter — not Data Structures) under something like
`examples/` or `fixtures/`, clearly marked as a test fixture and excluded from the scaffold. Real
courses never live here.

---

## Q-006 — Other teachers / other courses
Who else is on the project, what courses, and on what timeline? Affects how soon the
separation mechanism (Q-001) has to be real rather than planned.
