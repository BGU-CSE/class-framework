# Decision log

Newest decisions appended at the bottom. Status: `locked` | `provisional` | `superseded`.

---

## D-001 — Content language: English
**Date:** 2026-08-18 · **Status:** locked (for now)

All framework and course content in English. Hebrew/RTL and bilingual support are explicitly
deferred, not rejected.

**Why:** Simplifies the toolchain (slides, question export, templates) for the first phases.

**Consequence:** Avoid baking in LTR-only assumptions where it's cheap not to — e.g. don't
hardcode text direction in templates. Revisit before any Hebrew-language course joins the project.

---

## D-002 — Hard separation between framework and course content
**Date:** 2026-08-18 · **Status:** locked · **Priority: this is a load-bearing constraint**

The framework (agents, skills, schemas, templates, tooling) and any individual teacher's
course content must live in cleanly separated trees, so that:

- multiple teachers can run their own courses on the same framework;
- a teacher can pull framework updates without touching their content;
- a teacher can improve an agent and contribute it back without dragging their course along;
- no course's materials leak into the framework repo.

**Why:** Joint project. Avin's pilot is *Intro to Data Structures and Algorithms*, but other
teachers will bring their own courses during the build and will want to update agents.

**Consequence / open design point:** the exact mechanism is still open — candidates are
(a) framework repo + course repo, course as consumer; (b) one repo, `framework/` vs `course/`
top-level split with a documented contract; (c) framework as a git submodule inside a course repo.
See Q-001. Whatever we pick, the rule is: **nothing under the framework tree may name a specific
course, and nothing under a course tree may be required for the framework to function.**

---

## D-003 — Claude Code native, for now
**Date:** 2026-08-18 · **Status:** locked (for now)

Agents/skills/commands implemented as Claude Code primitives (`.claude/agents/`,
`.claude/skills/`, `.claude/commands/`). Not a standalone CLI or app.

**Why:** Fastest iteration. Extraction into a portable CLI stays possible later.

**Consequence:** Keep pedagogical logic in data files and skill instructions rather than in
Claude Code-specific plumbing, so the extraction path stays open.

---

## D-004 — Moodle integration deferred
**Date:** 2026-08-18 · **Status:** locked

Moodle synchronization is a later phase. Not designed or built now.

**Consequence:** Don't shape the question-bank schema *around* Moodle, but do keep items
atomic and well-tagged so a Moodle/GIFT/QTI exporter is a straightforward later addition.

---

## D-005 — Google Gem as the student-facing AI artifact
**Date:** 2026-08-18 · **Status:** locked

Export target is a Google Gemini Gem (instructions + knowledge files), per class and/or per unit.

**Why:** Students have free access to Gemini.

**Consequence:** Gem export needs a bundle format: a generated instruction prompt plus a
curated set of knowledge files, scoped to a course or a single unit.

---

## D-006 — Slides: PPTX, and deliberately few
**Date:** 2026-08-18 · **Status:** locked

Slide output is PPTX for now. Explicit design intent: **the 1-hour in-class session should not
be slide-heavy.**

**Consequence:** The session template should treat slides as an optional, minimal supporting
asset — not the backbone of the hour. Whatever generates slides should make it easy to produce
few, and awkward to produce many.

---

## D-007 — Learning objectives are the spine
**Date:** 2026-08-18 · **Status:** provisional (proposed, pending confirmation)

Every artifact — prework item, session activity, quiz question, homework task, exam item —
carries an explicit objective reference in its front matter. Course-level outcomes (CLO) and
unit-level objectives (ULO) are first-class, addressable entities.

**Why:** Makes coverage auditable, makes the flip transform checkable (each objective needs a
home-side acquisition slot *and* a class-side application slot), and makes content reusable
across semesters and teachers.

---

## D-008 — Temporary build log at `_devlog/`
**Date:** 2026-08-18 · **Status:** locked

This folder. Tracks progress and carries context across sessions and agents. Deleted before
first release.

---

## D-009 — Two repos, with shared git history (resolves Q-001)
**Date:** 2026-08-18 · **Status:** locked

**Model:** one framework repo (this one) + one repo per course. A course repo is created by
**cloning the framework repo and repointing `origin`** to a new, private course repo — keeping
the framework as a second remote named `framework`.

```bash
git clone https://github.com/<you>/class-framework.git <course-dir>
cd <course-dir>
git remote rename origin framework
git remote add origin https://github.com/<you>/<course-repo>.git    # private
git push -u origin main

git fetch framework && git merge framework/main   # pull framework updates
git push framework HEAD:<branch>                  # contribute a fix back → PR
```

**Why shared history rather than a GitHub template repo:** a template gives a clean copy with
no common ancestor, which forces manual re-application of every framework update — the exact
cost we're trying to avoid. A fork has shared history but GitHub permits only one fork per
account per repo, which breaks on the second course. Clone-and-repoint has neither limitation.

**Consequences — these are binding on the Phase 0 layout:**

1. **Course repos add, never edit.** Adding a new file under `.claude/agents/` (or anywhere in
   the framework tree) is merge-conflict-free. *Editing* a framework-owned file in a course repo
   guarantees a conflict on every subsequent pull and strands the improvement in one course.
   Framework changes are made as framework commits and pulled down.
2. **The framework must never ship files into the course content tree.** If `course/` contains
   framework-supplied files, every template update collides with teacher content. Templates live
   under the framework tree and are **copied** into `course/` by a scaffold command. In the
   framework repo, `course/` is a skeleton only.
3. **Framework and course trees must be file-disjoint.** This is what makes `git merge
   framework/main` clean. It is now a testable property — the validator should check it.
4. **Course repos are private** (exam confidentiality, Q-002 — partially addressed).
5. Avin's original plan (duplicate, then manually copy agent changes back) is superseded by the
   push-a-branch flow above; the manual path remains available as a fallback.

---

## D-010 — Flipped-class time model and the default study-session methodology
**Date:** 2026-08-18 · **Status:** locked (for Avin's course; see D-011 for other teachers)

A week/unit is **3 academic hours = 150 min** (a university "hour" is 50 min):

```
Week / Unit = 150 min
├── AT HOME  100 min = 2 × 50
│   └── 4 × Study Session, ~25 min each
│       └── 3–5 Study Goals per session, EACH PHRASED AS A QUESTION
│           the student is expected to be able to answer
│           └── student picks their own path: class Gem, video,
│               textbook chapter, article, exercise …
└── IN CLASS  ~50 min (confirm — Q-009): short quiz, discussion,
    critical thinking, worked examples, small-group work
```

**The guiding question is the atomic addressable unit — it supersedes abstract objectives as the
spine (refines D-007).** A question is student-facing, directly assessable, and unambiguous about
what "done" means, in a way that "the student can explain amortized analysis" is not. Everything
else — quiz items, class activities, homework, Gem instructions — references question IDs.

**Consequences:**

1. **The question is the join key between home and class.** ~12–20 guiding questions per week.
   The entry quiz samples them; the discussion agenda is built from the ones students missed;
   group work extends one. The "class hour must not re-lecture the prework" property becomes a
   validator rule: *every in-class activity must reference ≥1 guiding question from that week.*
2. **Resources attach to questions, not sessions.** Each question carries *candidate* paths
   (book+pages, video, Gem prompt, exercise), typed and time-estimated, none mandatory —
   the student's path is their own choice.
3. **Validator rule:** every study session must have ≥1 *complete* path covering all its
   questions within 25 min. Otherwise the "2 hours at home" budget is fiction.
4. **The Gem becomes load-bearing, not an export nicety** (upgrades D-005). If "ask the class
   chatbot" is a first-class study path, the Gem must know that week's guiding questions and be
   instructed to tutor *toward* them rather than answer them outright. Argues for per-unit Gems
   and moves Gem-building earlier in the roadmap.
5. **Terminology, to be used consistently by all agents:** *study session* (the ~25-min at-home
   unit, formerly "topic"), *guiding question* (a study goal), *assessment item* (a quiz/exam
   question). "Topic" and bare "question" are ambiguous — avoid both.

---

## D-011 — The study-session methodology is a pluggable strategy
**Date:** 2026-08-18 · **Status:** locked

D-010 describes **Avin's default methodology**, not the framework's only one. Other teachers will
want different pedagogies, supplied as their own designer agents. The framework therefore defines
a **contract**; `question-driven-25` is the default implementation.

Declared per-course in config, so switching methodology is a config change plus a re-run, not a fork.

**The hard part is the output schema, not the plugin mechanism.** Downstream agents (in-class
session planner, assessment writer, Gem builder) must consume the designer's *output*, never its
methodology. Too tailored to questions and no other pedagogy fits; too generic and downstream
agents can do nothing useful. Proposed shape:

```
StudySession
  duration_minutes: 25
  items[]:                    # 3–5, for question-driven
    id: stable — referenced by quizzes, class activities, Gem
    type: question | task | reading | exercise
    prompt: "<guiding question, or task statement>"
    paths[]: { kind, ref, est_minutes }
```

`question-driven-25` emits `type: question`, 3–5 per session, 4 sessions per unit. Another
methodology emits a different mix. Downstream agents key off `items[]` generically and may
specialize on `type`.

**Consequence:** no downstream agent may hardcode "4 sessions", "25 minutes", or "3–5 questions".
Those are methodology parameters, read from config.

---

## D-012 — Canonical course model and glossary (resolves Q-009, Q-010, Q-011)
**Date:** 2026-08-20 · **Status:** locked

**This is the vocabulary. All agents, schemas, directory names, and docs use these terms and no
synonyms.** Ambiguous words to avoid: "topic" (previously meant both a subtopic and the 25-min
home unit) and bare "question" (meant both a study goal and a quiz item).

```
Semester = 12 or 13 Units          (count is per-course config)
└── Unit — one week's subject, 150 min total
    ├── Unit Objectives — 2–4, abstract layer
    │     for syllabus text, accreditation, cross-unit prerequisites.
    │     Guiding Questions map up to these. NOT the working layer.
    ├── HOME STUDY — 100 min = 2 × 50
    │   └── 4 × Study Session, ~25 min, together covering the subject
    │       └── Session Goals — 3–5 Guiding Questions
    │           (default methodology; other item types allowed, D-011)
    │           └── Study Paths — candidate routes to the answer:
    │               class Gem, video, textbook chapter, article, exercise.
    │               Typed, time-estimated, none mandatory — the student chooses.
    └── IN-CLASS SESSION — default 50 min. Also called the Lesson Plan.
        └── built from Activities — quiz, discussion, critical thinking,
            worked example, small-group work, synthesis.
            Each Activity references ≥1 Guiding Question from that Unit.
```

**Resolutions folded in:**
- **Q-009 → in-class session is 50 min**, matching the 50-min academic hour. Week = 100 home + 50
  class = 150 min.
- **Q-010 → the in-class session is per Unit**, not per Study Session. One weekly meeting covering
  all four of that week's study sessions. (The original brief's "each topic, a Lesson Plan" would
  have implied four lesson plans per week with no time to deliver them.)
- **Q-011 → yes, keep Unit Objectives** as a thin abstract layer above the Guiding Questions.
  Guiding Questions remain the working, addressable layer that quizzes, activities, homework, and
  the Gem all reference.

**Glossary — canonical terms:**

| Term | Meaning |
|---|---|
| **Unit** | One week's subject. 12–13 per semester. The top-level content container. |
| **Unit Objective** | Abstract, teacher-facing goal. 2–4 per unit. |
| **Study Session** | ~25-min at-home unit. 4 per Unit. |
| **Guiding Question** | A session goal phrased as a question the student should be able to answer. 3–5 per session. **The atomic addressable unit.** |
| **Study Path** | A candidate route to answering a Guiding Question (Gem / video / textbook / exercise), typed and time-estimated. |
| **In-Class Session** | The weekly 50-min meeting. Synonym: **Lesson Plan**. One per Unit. |
| **Activity** | A component of an In-Class Session (quiz, discussion, worked example, group work). Has a duration; references ≥1 Guiding Question. |
| **Assessment Item** | A single quiz/homework/exam question. Never called just "question". |

---

## D-013 — Repo home and license (resolves Q-012, Q-013)
**Date:** 2026-08-20 · **Status:** locked

- **Host:** GitHub, personal account **`chenavin`**. Repo name `class-framework`.
- **Visibility:** *see Q-016* — "private git account" was ambiguous between "personal account" and
  "private repo". Defaulting to **private** until confirmed; private→public is trivial later,
  public→private does not un-distribute what was already cloned.
- **License:** **MIT.**

**Consequence:** if the repo is private, every collaborating teacher needs explicit read access
before they can run the clone-and-repoint flow in D-009.

---

## D-014 — Governance: protected framework, sovereign course repos (resolves Q-007, amends D-009)
**Date:** 2026-08-20 · **Status:** locked

Two separate things, previously conflated:

**Governance (decided).** The `class-framework` repo is **permission-controlled** — only
designated developers may push, including edits. Outside contributions arrive as pull requests.
Course repos are **sovereign**: once a teacher duplicates the framework into their own repo, they
may do whatever they like with it, including editing framework files in place.

**Merge hygiene (amends D-009 rule 1) — REMAINS OPEN, see Q-007.** Avin: *"I'm not sure yet how
exactly the framework update should work after a teacher did some edits or additions. Let's leave
it open for now."* The **interim rule**, which is what the docs currently state:

> A teacher who wants future framework updates cannot edit framework files.

"Course repos add, never edit" is therefore **demoted from a binding rule to documented guidance**,
because course repos are sovereign and the framework cannot enforce anything there. The trade-off
is stated honestly in the teacher-facing docs:

> Editing a framework file in place is allowed and sometimes right. The cost is that
> `git merge framework/main` will conflict on exactly those files. If you want painless framework
> updates, add new files instead of editing existing ones. If you never intend to pull framework
> updates, edit freely.

D-009 rule 3 (file-disjointness) survives, and is now *structural* rather than policed — see D-015.

---

## D-015 — No example course; the framework tree contains no course content at all (resolves Q-014)
**Date:** 2026-08-20 · **Status:** locked

The framework repo ships **no example course**. Avin and the other developers will test against
their own real courses in their own course repos.

**Consequence — a welcome simplification:** combined with D-009 rule 2 (the framework never ships
files into the course tree), the framework repo needs **no `course/` directory at all**, not even
an empty skeleton. The course tree is created entirely by the scaffold command in the course repo.
File-disjointness (D-009 rule 3) becomes structurally guaranteed instead of something the validator
has to check.

**Consequence — a real cost, flagged:** with no fixture in the repo, there is nothing for CI to run
the validator and agents against. A framework change can break every course and nobody learns until
they pull. Mitigation proposed in Q-017: ship *schema test fixtures* (a handful of tiny valid and
deliberately-invalid YAML files as unit-test data) rather than an example course — test data, not a
course, so it doesn't conflict with this decision.

**Resolved in Session 6 — better than the proposal:** `tests/test_course_lifecycle.py` builds a
throwaway course in `tmp_path` **using the scaffold itself**, asserts it validates clean, then
mutates it to prove each rule fires. No fixture files, no example course, and it additionally tests
the templates: if a template drifts out of line with a schema or methodology, a fresh scaffold stops
validating clean and CI fails. Q-017 closed.

---

## D-016 — Scaffold: four granularities, create-only (resolves Q-008)
**Date:** 2026-08-20 · **Status:** locked

`classkit scaffold` supports **course / unit / session / item**, and is **create-only — it never
overwrites**. Re-running it produces whatever files are missing, leaves everything that exists
untouched, and reports what it skipped.

**Why create-only:** the teacher will re-run `scaffold unit 5` months later, after hand-editing
unit 5, because the framework added a template field. Overwriting would destroy their work;
attempting a merge is complexity nobody asked for. Create-only makes re-running safe at any time,
which is the property that matters.

Enforced in code by routing every write through `scaffold.write_new()`, and in
`tests/test_course_lifecycle.py::test_scaffold_never_overwrites`.

---

## D-017 — Implementation language and authoring format (resolves Q-018, Q-019)
**Date:** 2026-08-20 · **Status:** locked

- **Tooling: Python** (≥3.10), packaged as **`classkit`** under `src/`, deps PyYAML + jsonschema,
  installed with `pip install -e .`. Chosen mainly because `python-pptx` is the realistic route to
  the PPTX requirement (D-006), and YAML/JSON-Schema tooling is mature.
- **Authoring format: Markdown with YAML front matter** for anything containing prose a teacher
  edits (units, study sessions, in-class sessions, assessment items); **pure YAML** for pure
  configuration (`course.yaml`, methodologies, time constants).

The validator degrades gracefully if `jsonschema` is missing — semantic rules still run, and it
warns that the schema layer was skipped.

---

## D-018 — Code verifies, agents judge
**Date:** 2026-08-25 · **Status:** locked (for `validate`; `scaffold` is Q-021)

The division of labour between the Python tooling and the agent layer, written down because it had
never been recorded and Avin reasonably asked why the Python exists at all.

**Code does verification** — things that must be exhaustive, deterministic, arithmetic, and cheap:

- **Exhaustive cross-referencing.** A 13-unit course is 79 Markdown files with 221 guiding-question
  ID references that must all resolve. An agent re-reading all of them burns context and misses
  references in the middle of long lists — and you cannot tell which ones it missed.
- **Arithmetic.** Fastest-path sums per session against the budget; activity durations against the
  hour. Hundreds of small sums per course. Models approximate, and an approximate feasibility check
  is precisely the failure the check exists to prevent.
- **Testability.** 14 tests prove each rule fires when its defect is present. You cannot unit-test a
  prompt this way, and a rule that silently stops firing is worse than no rule because it
  manufactures confidence.
- **Independence.** The agent that designed a unit must not be the one certifying it; self-review is
  systematically generous and the bias is invisible from the inside.
- **Cost.** Full validation takes 0.09s and no tokens, so it can run after every edit. A check
  nobody runs is not a check.

**Agents do judgment** — things code cannot attempt: whether a guiding question is a topic label in
disguise, whether an activity would still work if nobody did the prework, whether 8 minutes is
honest for 8 pages of proofs. This is why `course-critic` exists and why it is explicitly told not
to repeat what the validator already does.

**The premise this serves:** a course managed like a software project. What makes it one, rather
than a well-organised folder of Markdown, is that something can *fail* — reproducibly, and with a
reason. Remove the validator and you keep a good content model and useful agents, but you lose the
ability to *know* the course holds together as distinct from believing it after something said so.

---

## D-019 — Every Guiding Question carries an `answer`: precise references to where the answer lives
**Date:** 2026-08-27 · **Status:** locked (design) · **implementation pending** (schema, validator,
templates, agents)

The atomic unit stored the *question* (`prompt`) and *routes to learn it* (`paths`) but nothing
recording what answering it looks like. That is a real hole: the guiding-questions skill demands a
question be "answerable and checkable" with "a real answer", the Gem's `tutoring_stance: socratic`
promises to "tutor toward the answer", and the assessment writer needs a ground truth — yet the
answer was written nowhere. The only check on "did the student get it" was the in-class entry quiz,
a separate artifact by a different agent.

**Decision.** Add an `answer` field to each goal: a list of **precise references to where the
correct answer is found**, not the answer in prose.

- Not prose, by design. A written answer would put course content in the repo (against D-002),
  invite the fabrication invariant 7 forbids, and drift from the source. A locator stays checkable
  and content-free. Avin's framing: *"a reference to where the answer can be found — a subsection in
  the textbook, a slide, a Wikipedia page, a video."*
- **Separate field, not a flag on a path** (Avin chose this for clarity). `paths` are *optional*
  learning routes, coarse and time-budgeted, one of which the student picks; `answer` is the
  *authoritative* location of the correct answer, precise (slide 18, §2.3.1, a timestamp), with **no
  time estimate**. They may point at the same resource at different granularity, but answer
  different questions: "how do I get there / how long" vs. "where is the correct answer, exactly".
- **Shape:** each entry is `{ kind, ref, note? }`. `kind` ∈ `textbook | slide | video | article |
  web | other` — `slide` added (teachers have decks), `gem`/`exercise` dropped (an answer is
  *located*, not tutored or practiced).
- **Required, ≥1 per goal.** New validator rule `answer_reference_present` (severity `error`). A
  guiding question with no locatable answer signals the question or the materials are thin — exactly
  what we want to fail loudly.

**Consequence.** Three downstream consumers gain a shared ground truth: the **gem-builder** tutors
toward it, the **assessment-writer** uses it as the correct-answer / rubric basis, the
**course-critic** checks it is precise and reachable. Whether the answer's location is *reachable
from at least one study path* (answer on slide 18 but no path covers those slides — the skill's
"unanswerable-from-its-own-paths" failure mode) stays a **critic-level judgment**, not a code rule,
because locators are free text.

**Not changed:** the name "Guiding Question" was reconsidered this session (it undersells that
knowing the answer is *mandatory* after the session) and deliberately **kept** — reaffirming D-012.

**Amended by D-020:** the time budget now lives on the question (`est_minutes`), not on study paths,
and study paths move to the session. D-019's core (the `answer` field, untimed pointers) stands.

**Open item resolved by D-023:** the escape for a question with no single locator is an explicit
`defer_to_class: true`, not a fabricated reference.

---

## D-020 — Study Path is a per-session optional pool; the 25-min budget rides on per-question study time
**Date:** 2026-08-28 · **Status:** locked (design) · **implementation pending** · resolves Q-023,
narrows Q-024, amends D-019

The original Study Path bundled three jobs: student agency (choose your route), feasibility
arithmetic (timed per-question routes summed against 25 min — the "two hours at home isn't fiction"
guarantee), and the Gem as a first-class route. Once D-019 gave every question an authoritative
`answer`, the "provide a way to reach the answer" job became redundant, and the three jobs came
apart. Avin's reshape: a study path should be *additional* resources, listed *per session* (not per
question), optional and non-exhaustive — students may bring their own (another AI, another video) —
and is teacher-facing for now (an inventory of what students can access), possibly published later.

**Decisions.**

- **The feasibility budget moves from paths onto the questions (option "a").** Each guiding question
  carries `est_minutes` — a single, teacher-approved approximate study time. The session check is
  `sum(goal.est_minutes) + overhead ≤ session_minutes`. Avin: *"an approximate time for studying it
  … approved by the teacher … to ensure the study session is about 25 min"* — and explicitly an
  approximation (students vary), so the check should carry a tolerance, not a hard cliff.
- **`est_minutes` lives on the goal, not on the answer references.** So D-019's answer refs stay pure
  untimed pointers; no conflict. The number is the teacher's estimate for studying the question, not
  a parse of the answer locator.
- **`paths` moves to the Study Session** (a sibling of `goals`), and is an open, optional,
  non-exhaustive pool of alternative resources for the session as a whole. **Not tagged to individual
  questions** (Avin confirmed session-level, not per-question). **Not time-summed** — nothing about
  the budget depends on it. Recommended ≥1 (soft), since the `answer` already guarantees a source.

**Consequences.**

- **Q-023 resolved** (path is a per-session pool; feasibility rides on per-question time).
- **Q-024 narrows sharply.** The core 25-min guarantee no longer needs derived reading-rate
  constants — it is one teacher-approved number per question. `defaults/time-constants.yaml` stops
  being load-bearing for the guarantee (it may still help agents *propose* an `est_minutes`, and
  paths may optionally carry a rough time to help students choose, but nothing sums those).
- **Schema/validator changes deferred** (design-draft phase): move `paths` to session scope; add
  required `est_minutes` to each goal; rewrite `session_path_feasibility` to sum `goal.est_minutes`;
  rename methodology `study_paths.min_paths_per_goal` → a per-session minimum (soft).

---

## D-021 — The Syllabus is the course-level top layer (Bologna-style); Course Outcomes close the coverage chain
**Date:** 2026-08-28 · **Status:** locked (design) · **implementation pending** · resolves Q-025

The framework had no layer above Unit Objectives, so "do the units *together* deliver what the course
promised?" was unanswerable and uncheckable (Q-025). Avin: the top layer of a class should be its
**syllabus**, defaulting to a **Bologna-style** descriptor.

**Decisions.**

- **Two artifacts, no `course.md`.** The syllabus is `syllabus/syllabus.md` — an authored document
  (YAML front matter + prose body), edited exactly like `unit.md`: scaffold writes the skeleton once
  into the already-reserved `syllabus/` slot (see `scaffold.py` `COURSE_DIRECTORIES`) and never
  overwrites. `course.yaml` stays the machine *wiring* (code, methodology, unit count, textbooks).
  It is not YAML-only config because a syllabus is a *document* (prose aim + structured data), which
  is what the front-matter-plus-body `.md` format is for.
- **Bologna-style default front matter, kept generic:** `goal`; `outcomes` — **Course Outcomes**,
  id `CO1…`, `statement`, optional `bloom`; `workload` — `credits`, `credit_system` (ECTS is *one*
  instantiation, not hardcoded — invariant 2), optional `total_hours`; `prerequisites`; and a
  reserved `assessment` block (the grading scheme — its details deferred to **Q-026**).
- **No duplication.** Identity fields (title, code, language, instructors, textbooks) stay in
  `course.yaml`; the *rendered* syllabus pulls them in, plus a **unit overview stitched live from the
  `unit.md` files** — so the overview is generated at render time and cannot drift. The stored
  `syllabus.md` holds only genuinely course-level content.
- **Source vs. view.** `syllabus.md` is edited, never auto-generated. The full published syllabus (for
  students / accreditation) is a generated *view* combining it with the live units.

**The coverage rule this unlocks (the point of Q-025).** Unit Objectives gain an `outcomes: [CO1…]`
reference. Two-way checks, mirroring the objective↔question checks one level up: `outcome_coverage`
(no orphan Course Outcome) and `objective_maps_to_outcome` (no orphan objective). This touches
`unit.schema.json`.

**Bonus.** `workload.total_hours` enables a later *course-scope* workload check — the sum of all
home-study `est_minutes` + in-class + homework against the declared workload, the course-level twin
of the 25-minute session check.

**Consequences / implementation pending** (design-draft phase — no code this session): a new
`syllabus.schema.json`; a Bologna-default `templates/course/syllabus.md`; scaffold writing it into
`syllabus/`; the `outcomes` field on `unit.schema.json` objectives; the two coverage rules; the `CO`
id convention added to `CLAUDE.md`; `curriculum-architect` set to author the syllabus. **Resolves
Q-025;** grading-scheme details stay open under **Q-026**.

---

## D-022 — Design and build in vertical slices; Core first
**Date:** 2026-08-28 · **Status:** locked (process/roadmap) · no ledger row (organizes artifacts,
adds none)

Avin reshaped the plan: rather than finish the whole design draft before any implementation, we run
**design → implement → test → update one coherent slice at a time.** Each slice is completed end to
end before the next is designed, so we reach the implement-and-test loop (where the framework's real
risk lives — untested agents) sooner and on a small surface, and later slices are designed against a
Core that has actually been exercised rather than against assumptions.

**The slices, in order:**

1. **Core** — course initiation, syllabus, Course Outcomes, units, and the whole learning part:
   study sessions (guiding questions, `answer`, `est_minutes`, the study-path pool) and the in-class
   hour, **including the entry quiz end to end** — generating its questions and producing *gradeable*
   quizzes (the items carry answer keys / rubrics; running grading over live submissions stays out,
   per "designs a course, does not run one"). The bar: Core delivers everything needed to *generate
   and run* the learning phase. Its content model is locked as D-019/D-020/D-021.
2. **Assessment** — homework, programming assignments, exams (Q-026); fills the syllabus's reserved
   grading block. The entry quiz's items are Core; homework/exam items are here.
3. **Exports** — the Gem *builder* and PPTX. (Gem-as-a-study-path stays Core; only the builder
   defers.) Named "Exports" so each phase name is honest — a generator, not assessment.
4. **Metrics** — *later*, to improve a course or its activities once Core is built and taught.
5. **Lifecycle** — *much later*, after the course is taught once: semester arc, revision, re-offering.

**Why the split is safe:** the later slices all hang off Core (they consume its guiding questions,
answers, and the syllabus's reserved blocks), so Core does not depend on them. **Naming:** Avin chose
"Core"; "Assessment" and "Exports" over the broader "Extensions" so each name is specific (Session
13). Maps onto the risk-ordered ROADMAP phases: Core's test step is "first real course" (old Phase
2), Exports is old Phase 4; pluggability/Moodle/multi-teacher (Phases 3/5/6) are unchanged.

---

## D-023 — A study-session question either has a recorded answer, or is explicitly deferred to the in-class meeting
**Date:** 2026-08-28 · **Status:** locked (design) · **implementation pending** · resolves D-019's
open item

D-019 made `answer` required at error severity. That has no honest filler for a **judgment /
decision question** with no single locator (*"how would you choose between a heap and a sorted array
here?"*), and the pressure to fill the field is exactly what produces the fabricated reference
invariant 7 forbids. Resolution — a **guarded hybrid** (Avin: "the leading way is B", most questions
have a clear recorded answer, but keep the ability to ask a question that encourages thinking before
class and "defer" the answer/discussion to the meeting):

- **Rule (the norm).** A home-study guiding question carries a recorded `answer` (≥1 locator). This
  is what most study-session questions should look like.
- **Escape (the minority).** A question may instead be marked **`defer_to_class: true`** — a pre-class
  *thinking prompt* whose correct answer / discussion is deliberately deferred to the in-class
  meeting. Such a question carries **no `answer`**, and the student is not expected to know the answer
  after the session; its `est_minutes` is thinking time and still counts toward the budget.
- **Closing the loop (the discipline).** A `defer_to_class` question **must be referenced by ≥1
  in-class activity** — the class must actually resolve it. So deferring *costs contact time*; it is
  not a way to avoid writing an answer. New rule `deferred_question_resolved_in_class`.

**Consistent with existing craft.** The `writing-guiding-questions` skill already flags "the question
that needs the class hour" as a failure mode. D-023 refines it: such a question is allowed *only if*
explicitly deferred **and** resolved in class; otherwise it is a mis-filed in-class activity. The
critic also watches for overuse — a session of all-deferred questions teaches nothing at home.

**Ledger (see ROADMAP):** `defer_to_class` on the goal schema; `answer_reference_present` becomes
conditional on it; new `deferred_question_resolved_in_class` rule; methodology severities; template
example; study-session-designer, lesson-planner and course-critic guidance; the skill's failure-mode
wording; CLAUDE.md glossary; tests.

---

## D-024 — Framework-development docs live under `dev/`; the spec is renamed `FRAMEWORK-SPEC.md`
**Date:** 2026-08-28 · **Status:** locked (process/roadmap) · executed this session (no ledger row —
done, not deferred)

The spec, the roadmap+ledger, and the throwaway build log are framework-*development* artifacts, not
part of a teacher's course. But a course repo is a clone of the framework (D-009), so these files
land in every teacher's clone. To keep the teacher's workspace clean and clearly ignorable, they move
under one directory:

```
dev/
  FRAMEWORK-SPEC.md   (was DESIGN.md)
  ROADMAP.md
  _devlog/
```

- **Rename.** "Design" was ambiguous (visual design? whose design?); `FRAMEWORK-SPEC.md` names the
  role — the specification of the framework, which is how we treat it. H1 and all cross-references
  updated.
- **Honest limits.** A `git clone` still copies `dev/`; truly excluding it would need sparse-checkout
  (too advanced for non-technical teachers) or a separate repo (breaks clone-and-repoint *and* hides
  the spec from developers). `dev/` gives clear separation and a **merge-hygiene bonus** — teachers
  never edit `dev/`, so `git merge framework/main` stays conflict-free there (helps Q-007). That is
  the realistic best, not literal exclusion.
- **Persistence.** Unlike `_devlog/` (deleted at release, D-008), `FRAMEWORK-SPEC.md` and `ROADMAP.md`
  persist — the durable spec and plan.
- **Root now holds** only teacher/product-facing or load-bearing files: `README.md`,
  `GETTING-STARTED.md`, `LICENSE`, **`CLAUDE.md`** (must stay at root — Claude Code auto-loads it as
  the agents' operating context in the course repo), `pyproject.toml`, and the product dirs
  (`src/`, `schemas/`, `methodologies/`, `templates/`, `defaults/`, `.claude/`).
- References updated in `README.md`, `CLAUDE.md`, and the moved files. **Historical progress/decision
  entries were left intact** — a chronological log that said "DESIGN.md" at the time stays as it was.

---

## D-025 — `est_minutes` honesty is human judgment, aided by the time-constants as an advisory yardstick
**Date:** 2026-08-28 · **Status:** locked (design) · **implementation pending** · resolves D-020's
open item and Q-024

Since D-020 the 25-minute guarantee rides on one teacher-typed `est_minutes` per question. Code
checks the *sum*; it cannot check whether any single number is *honest* (type "3 min" for a 15-min
question and the validator still goes green). So the only guard on plausibility is human judgment —
the `course-critic`. The choice was whether that judgment stands alone, or gets a yardstick.

**Decision (Avin chose "option 2", with an explicit fallback to option 1 if it proves fiddly):** the
old time-constants come back as an **advisory yardstick — not a validator input, not a hard rule.**

- `defaults/time-constants.yaml` is **kept and annotated advisory** (not deleted — resolves Q-024's
  "annotate or delete").
- The **study-session-designer** uses the constants to *propose* an `est_minutes` (e.g. "4 pages of
  proofs ≈ 8 min"), which the teacher then approves/adjusts.
- The **course-critic** uses the same constants to *sanity-check* each `est_minutes` against the
  question's material, and flags implausible ones — the D-020 open-item responsibility, now written
  down. The shared standard lives in the `estimating-study-time` skill so designer and critic judge
  by one bar.
- **No validator rule** derives or checks time from the constants; the validator still only sums
  `est_minutes`. Advisory means a bad constant never fails a build — it only guides.

**Honest caveat.** The constants are still placeholder numbers (Q-005), so the yardstick is only
roughly calibrated. Because it is advisory, that is tolerable — a rough anchor beats pure vibes, and
a wrong constant misguides rather than breaks. **Fallback:** if wiring this into the designer/critic
proves more trouble than it is worth, revert to pure judgment (drop the yardstick) — Avin's call,
recorded now so the option is not forgotten.

**Ledger:** woven into the D-020 rows for `time-constants.yaml`, `course-critic.md`,
`study-session-designer.md`, and the `estimating-study-time` skill (tagged D-025). No new artifacts.
