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

## Q-022 — Where do *course* repos live now that BGU-CSE exists?
**Partially answered 2026-08-25.** Avin: course repos are **private**, one per teacher. That
settles visibility (and confirms D-009). **Ownership — organization vs personal account — is still
open**, so `GETTING-STARTED.md` uses a neutral `<owner>` placeholder rather than presuming either.

Also decided the same day: `GETTING-STARTED.md` is written for the state it ships in — framework
**public**, course repos **private** — not for the current development state. It is only handed to
teachers after the repo goes public (ROADMAP Phase 6). An HTML comment at the top of the file says
so, to stop a well-meaning developer re-adding an "ask for access" note.

**Raised 2026-08-25 by the org transfer (Q-020).** `GETTING-STARTED.md` still tells a teacher to
create their course repo under their **personal account**, which was the only sensible option when
the framework itself was personal. It is now a real choice.

| | Course repos under `BGU-CSE` | Course repos under personal accounts |
|---|---|---|
| Continuity | Course survives a teacher leaving the university | Course leaves with them, or has to be transferred by hand |
| TA / co-teacher access | Managed with org roles | Ad-hoc collaborator invitations per repo |
| Exam confidentiality (**Q-002**) | Org owners and anyone with org-wide read can reach exam content and its full git history | Exposure limited to people the teacher explicitly invites |
| Teacher autonomy | Org admins can change or remove the repo | The teacher owns it outright |
| Discoverability across the project | All courses visible in one place — useful for a joint project | Scattered |

**The tension is real:** the same property that makes an org good for continuity and collaboration
(other people can see it) is what makes it worse for exam material. D-009 already requires course
repos to be private; that is necessary either way but not sufficient here, since "private" inside an
org still means visible to org owners.

**Possible middle path:** course repos in the org, but exam content in a separate repo owned by the
teacher — which is roughly what Q-002 was heading towards anyway. Worth deciding the two together.

**Blocks nothing yet**, but should be answered before a second teacher creates a course repo, since
moving one later means moving its history too.

---

## Q-021 — Should `scaffold` stay Python, or move into a command/agent?
**Raised 2026-08-25 by Avin: "why do we need the Python code and scripts — can't we do it all with
commands or agents?"** Good question. The answer splits, and only the scaffold half is genuinely open.

**`validate` stays code — settled, see D-018.** Exhaustive cross-referencing, arithmetic,
testability, independence from the agent that wrote the content, and it must be free enough to run
after every edit.

**`scaffold` is the weak case.** 257 of 1,097 lines of Python. An agent could read a template and
write files perfectly well — that *is* what agents do.

| Keep as Python | Move to a command |
|---|---|
| Byte-identical output every time; no drift between runs or teachers | ~257 fewer lines to maintain |
| Create-only guarantee enforced mechanically (D-016), not remembered | Templates could carry prose guidance an agent interprets, e.g. "name the unit after its subject" |
| Works with no model call, in CI, offline | One less reason a teacher needs the Python toolchain at all |
| Already written and tested | Scaffolding a unit is naturally part of `/design-unit` anyway |

**Considerations:**

- The install tax is real. `pip install -e .` is a barrier for a non-technical colleague, paid by
  every teacher who adopts this. But Phase 4's PPTX export needs `python-pptx` regardless, so
  Python arrives eventually either way — dropping scaffold does not remove the dependency, it only
  shrinks it.
- Losing create-only-by-construction matters more than it looks. "Never overwrite" as a prompt
  instruction is a rule that holds until an agent has a plausible reason to break it, and the
  failure destroys a teacher's work silently.
- The templates themselves stay either way. They are the thing being copied; only the copier is
  in question.

**Not blocking anything.** Decide before Phase 2 generates real course content, since that is when
teacher work starts being at risk from an overwrite bug.

---

## ~~Q-020 — Personal account or a GitHub Organization?~~ RESOLVED
**Resolved 2026-08-25.** The repo was transferred to the **`BGU-CSE` organization**
(`github.com/BGU-CSE/class-framework`), still private. GitHub redirects the old personal-account
URL, but existing local clones should `git remote set-url` to the new location. All in-repo
references were updated in the same commit.

**What this unlocks — D-014 can now be implemented as written.** Organization repos have real
roles, so the two audiences can finally be separated:

- **Read** for teachers who only clone the framework to start a course (D-009). This was impossible
  on a personal repo, where the only collaborator level is write.
- **Write** for the developers who maintain agents and tooling.

**Follow-up, not yet done:** assign those roles (or create teams for them), and check whether
branch protection on `main` is available under the organization's plan — it was unavailable for a
private repo on a personal free account, which left `main` unprotected against force-pushes.

Original analysis below.

### (superseded) Q-020
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

---

## ~~Q-023 — "Study Path": per-Guiding-Question route, or per-Study-Session route?~~ RESOLVED
**Resolved 2026-08-28 → D-020.** Per **session**, an open optional pool; feasibility rides on a
teacher-approved `est_minutes` per question, not on paths. Original framing below.

**Raised 2026-08-27 (Session 10, Gap 2).** The vocabulary (CLAUDE.md) defines a Study Path as a
route to answering **a Guiding Question** — per-question. But README/templates promise "one **route**
through all its questions that fits the budget" — a coherent per-session route (all-video, or
all-textbook). The validator implements neither: `check_session_feasibility` takes the *cheapest
path of each goal independently and sums them*, so a session passes on a cherry-picked mix (video
for G1, textbook for G2, Gem for G3) even if no single coherent route fits 25 min. A student who
says "I'll just watch the videos" has no guarantee that route was ever checked. **Decide whether a
path is per-question or a per-session route, and make the feasibility check match.**

---

## Q-024 — The study-time budget is not actually automated
**Narrowed 2026-08-28 by D-020.** The *core* 25-min guarantee no longer needs derived constants — it
now sums one teacher-approved `est_minutes` per question. What remains of this question is optional:
whether agents should *derive a proposed* `est_minutes` (or an optional per-path time to help
students choose) from structured quantity fields, or whether teacher-entered estimates are enough.
Much lower stakes than when raised. Original framing below.

**Raised 2026-08-27 (Session 10, Gap 3).** `defaults/time-constants.yaml` defines reading rate,
words/min and a video multiplier, but the validator **never uses them**: `_estimate_path` only has
fallbacks for `gem` and `exercise`; for `textbook`/`video`/`article` it returns `None` unless
`est_minutes` is typed by hand, because there is no structured page-count / word-count / duration
field to multiply against (the `ref` is free text like `"CLRS ch.3 pp.45-52"`). So the constants are
dead and the feasibility check is only as honest as hand-entered numbers. **Decide: give paths
structured quantity fields (pages / words / minutes) so derivation works, or make `est_minutes`
mandatory and admit the constants file is theater.** Overlaps Q-005 (which is about the *numbers*);
this is about the *schema* that would let them be used.

---

## ~~Q-025 — Nothing sits above Unit Objectives~~ RESOLVED
**Resolved 2026-08-28 → D-021.** The course-level top layer is `syllabus/syllabus.md` (a Bologna-style
document); **Course Outcomes** (`CO1…`) are the roof, and every Unit Objective rolls up to ≥1 of them.
Original framing below.

**Raised 2026-08-27 (Session 10, Gap 4).** Objectives are unit-local; there are no course-level
outcomes for units to roll up to. So "do the 13 units *together* cover what the course promised?" is
unanswerable and uncheckable — the two-way coverage guarantee we enforce inside a unit stops at the
unit boundary. For a framework whose selling point is mechanical coherence, the top of the pyramid is
missing. **Decide whether to add a course-outcomes layer (and a coverage rule objectives→outcomes).**

(The minor sibling gaps once parked here — session `duration_minutes` unconstrained, no home-study
sum check, no goal priority marker — moved to Q-027 so they survive this resolution.)

---

## Q-026 — Homework (including programming assignments) is undesigned
**Raised 2026-08-27 (Session 10).** Homework is a **distinct section** from the flipped-class study,
and the content model has no first-class notion of it. Avin's framing: homework is at-home work *in
addition to* the study sessions; it can span **several units/topics**; it is **not** per-unit or
mandatory every week; its purpose is to **test what has already been learned** (contrast: study
sessions are the week's material, done *before* the in-class meeting). Programming assignments are
the sharp case — multi-part, multi-day, with a spec, starter code, test cases and a grading scheme —
which neither a Study Path (`type: exercise`, an optional *learning* route) nor an Assessment Item (a
single quiz/exam question) models. Whether it needs its own schema, and its own agent (a "homework"
or "programming-assignment" agent — none exists today), is open. To be taken up after the
flipped-class content model is settled.

---

## Q-027 — Minor flipped-class checks (parked)
**Raised 2026-08-27, relocated here 2026-08-28.** Small structural checks the flipped-class model
does not yet make, none blocking: (1) a session's `duration_minutes` is unconstrained — nothing ties
it to the methodology's `session_minutes`; (2) nothing checks that the sessions' `est_minutes` budgets
*sum* to the declared home-study total (100 min); (3) goals have no core-vs-stretch priority marker.
Pick up after the main content-model and homework passes.

---

## Design-draft agenda — superseded by the vertical-slice plan (D-022, Session 13)
The Session-10 agenda (content model → agent coverage → metrics → lifecycle) is **reorganized** into
vertical slices, each taken design → implement → test → update in turn (see ROADMAP "Build plan" and
D-022). Agent coverage is now settled *within* each slice, not as a separate pass.

- **Core** (now) — content model **done** (Gap 1 D-019, Gap 2 D-020, Gap 3 D-021; D-019's open item
  closed by D-023). Remaining: the D-020 critic-honesty item, and Q-027 (minor). Then implement + test.
- **Assessment** — Q-026 (homework, programming assignments, exams).
- **Exports** — Gem builder + PPTX.
- **Metrics** — later; to improve a course/activities once Core is built and taught.
- **Lifecycle** — much later; after the course is taught once.

Q-024 (narrowed) rides along with whichever slice next touches study-time estimation.
