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

---

## D-026 — `FRAMEWORK-SPEC.md` is the standalone normative spec; the decision log is rationale only
**Date:** 2026-08-28 · **Status:** locked (process/doc) · no ledger row

To let a memory-less agent implement or verify a phase from one file, `FRAMEWORK-SPEC.md` was
promoted from a design *overview* to a *normative specification*: it now carries the exact fields,
IDs, validation rules, time model, and methodology contract for the Core phase (new §11 reference
section), with narrative §1–§10 revised for Core scope and deferred parts marked.

**Division of labour going forward:** the **spec** is the normative "what" and is self-sufficient for
implementation (it survives `_devlog/` deletion); the **decision log** keeps the "why/history",
reached by `D-nnn` breadcrumbs that are traceability, not required reading. This deliberately
duplicates the decisions' *outcomes* into the spec — intended, and required by CLAUDE.md's rule that
rationale worth keeping be reflected in the spec. When a decision changes normative content, update
the spec in the same commit.

**Extended by D-027:** the "why" layer was split out into `VISION.md`; the spec keeps the "what".

---

## D-027 — `VISION.md` carries the project's purpose; the spec is restructured top-down
**Date:** 2026-09-10 · **Status:** locked (process/doc) · no ledger row

Avin read the consolidated spec and found the big picture missing: *"the goal of the project and the
framework we are developing is not clear enough — §1 The problem and §2 The one idea are not
expressing my goals well."* Correct. Those sections argued for *flipping a lecture course* and for the
*Guiding Question mechanism* — both true, but scoped to one pedagogical instantiation. Nothing stated
what the framework itself is for. The project-level statement existed only in `README.md`'s opening
line and had never reached the dev docs.

**The goal, as Avin stated it (this is the correction that matters).** The primary driver is **not**
mechanically catching mistakes — that is a *feature*. The driver is **AI-native course development**:
when a teacher builds a new course, changes its methodology, or revises it (which happens every year),
they should have a structural framework plus AI agents that a coding agent can access and use, making
the recurring jobs — writing a quiz, adding a unit, changing goals, searching content — easier and
better-structured. The hope is better courses, and so better learning and teaching. **"A course as a
software project" is the means of execution, not the driver.**

**Decisions.**

- **New `dev/VISION.md`**, for developers and agents (teachers use `README.md` to decide adoption).
  Formal top-down sections: *Project outcome* (the deliverable is a git repository a teacher clones
  and works in with an AI tool — listing what it contains) · *Motivation* · *Approach* (AI-native;
  structure exists to make agents effective; validation exists because agents author) · *Scope and
  audience* (flipped-classroom now, pluggable later as an open door not a claim; for teachers
  comfortable with git and an AI coding tool — not every teacher) · *How the framework is used* (the
  7-step teacher workflow) · *Specification and development process* (spec-driven, Core first, then
  test on a real course and update spec + implementation).
- **`FRAMEWORK-SPEC.md` restructured top-down** and scoped to the "what": §1 Scope of this
  specification (phase table, spec-ahead-of-code note, doc map) · §2 Framework architecture
  (framework-wide: four layers, code-verifies/agents-judge, repository model, authoring format,
  extension points) · §3 The Core phase (what it covers; its pedagogy; the Guiding Question) · §4–§7
  content model, control flow, data flow, invariants · §8 the normative reference · §9 known
  weaknesses.
- **Nothing was discarded.** The old §1/§2 survive as §3.2/§3.3 — demoted from "the project's mission"
  to "Core's pedagogy and Core's mechanism", which is what they always were. The validator keeps its
  design and gains a better justification: agents author, so something must catch what agents get
  wrong.
- **Detail level:** the normative field tables stay at full detail — that is what makes spec-driven
  development possible. The narrative sections carry the top-down clarity.

---

## D-028 — An in-class activity need not reference a guiding question; unmapped time is capped instead
**Date:** 2026-09-10 · **Status:** locked (design) · **implementation pending** · amends invariant 4

Avin: *"an in-class activity doesn't* must *reference a guiding question. This is the default and true
for most activities, but must is too strong. I can discuss the final exam, or present something from
the news that was not in the guiding questions. Let's not make it an error, we can flag it."*

Correct — and the absolute rule was overreaching. But a plain downgrade to `warn` would have gutted
the framework's central structural claim: a 50-minute hour of entirely unmapped activities would pass
with a few warnings, which is exactly the lecture-reversion failure §3.3 exists to catch. So the rule
is **relaxed per activity and enforced per hour** (Avin chose this over the simpler plain-warn):

- **`activity.guiding_questions` is no longer required.** An activity with none is **`warn`**, not
  error. It may carry an optional **`reason`** string (`"exam logistics"`, `"current-events hook"`);
  the critic judges whether the reason is legitimate.
- **Referencing a question from a *different* unit remains an error** — that is a dangling reference,
  not an exception.
- **New rule `in_class_unmapped_time_cap` (error):** the total duration of activities referencing no
  guiding question must be ≤ `in_class.max_unmapped_minutes` (new methodology field, default 15 of
  50). One 8-minute exam discussion is frictionless; an hour that has drifted off the home study
  still fails loudly.

**Invariant 4 is reworded** from "every Activity references ≥1 Guiding Question" to "**the class hour
is built on the home study**; unmapped time is capped — never raise the cap to make a validation
pass." Same intent, honest about exceptions.

**Recorded weakness (§9).** The guarantee moves from a bright line to a number someone chose, and a
methodology can raise it. If the cap is set generously the protection quietly disappears. Accepted
knowingly.

---

## D-029 — The syllabus gets its own agent, run in one flow with unit planning
**Date:** 2026-09-10 · **Status:** locked (design) · **implementation pending**

Avin: the syllabus needs a specific agent to create it and to test it, and a way to update it
partially.

- **New agent `syllabus-designer`** owns `syllabus/syllabus.md` — the course goal, Course Outcomes,
  workload, prerequisites. `curriculum-architect` keeps the unit map and unit objectives.
- **They run as one flow under `/plan-units`, sharing the outcome list.** The coupling is the reason:
  Course Outcomes and Unit Objectives form the coverage chain, so an agent that writes outcomes
  without seeing the unit map (or vice versa) makes the two drift apart. Splitting the *agents* is
  fine; splitting the *flow* is not.
- **Testing it has two halves.** Mechanical: the schema plus `outcome_coverage` and
  `objective_maps_to_outcome` (already specified). Judgment: `course-critic` gains syllabus
  responsibilities — are the outcomes real outcomes rather than topic labels, is the goal meaningful,
  is the declared workload plausible against the course's actual content.
- **Partial update** is not syllabus-specific; it is handled by the general revision rule in D-030.

---

## D-030 — Command interaction protocol: stepwise with approval, never overwrite, revise not regenerate
**Date:** 2026-09-10 · **Status:** locked (design) · **implementation pending** · extends invariant 5

Avin: *"I envision /design-unit as a step-by-step operation where the chat tells the teacher what it
is doing next, gets remarks or approval, produces the step and only after approval moves to the next
step. Also, when running any command, it must check if the output already exists and get permission
to overwrite."*

The spec described commands as pipelines that run start to finish and said nothing about how a
command interacts with the teacher. Three rules now bind **every** command in every phase (new §5.2):

1. **Stepwise, with approval gates.** Announce the step → produce it → show it → **wait for approval
   or correction** → next. `/design-unit N` becomes sessions → *approve* → in-class hour → *approve* →
   entry-quiz items → *approve* → validate. Corrections are applied at the gate, not deferred.
   *Why:* an agent that designs a whole unit before the teacher sees anything compounds a wrong
   assumption across four sessions, an hour and a quiz. Gates keep the blast radius one step wide.
2. **Never overwrite without permission.** Before writing, check whether the target already has
   content; if so, stop and ask, showing what exists and what would replace it. This **generalizes
   invariant 5 from `scaffold` to every agent and command** — agents write files directly, so without
   this a re-run silently destroys a teacher's edits. Silent loss of authored work is the one failure
   the framework must never have.
3. **Revision, not regeneration.** When output exists the default is *update*: change what was asked,
   leave the rest, report the diff. Regeneration is an explicit choice. This is what makes partial
   edits possible — one Course Outcome without rewriting the syllabus, session 3 without touching 1,
   2 and 4 — and it is how a course is maintained year to year (answers D-029's update question).

Invariant 5 is reworded to "nothing overwrites a teacher's work without permission".

**Strengthened by D-031b:** the never-overwrite rule is enforced in code, not by prompt.

---

## D-031 — Core spec review findings adopted
**Date:** 2026-09-10 · **Status:** locked (design) · **implementation pending** · source:
`dev/reviews/core-spec-review-01.md` (independent review, Gemini 3.1 Pro, verdict *yes with changes*)

An independent agent reviewed `VISION.md` + `FRAMEWORK-SPEC.md` with full repo access. Findings were
accepted, with one re-diagnosis. Items are lettered so the spec can cite them precisely.

**(a) The lesson planner now runs *after* the assessment writer.** The reviewer flagged a circular
dependency: `lesson-planner` writes the quiz activity's `items: [U03-I01]`, but `assessment-writer`
had not yet written those items, so the planner must invent ids.

> **Re-diagnosis — the reviewer's mechanism was wrong, and the truth is worse.** It claimed validation
> would fail at step 3 because `item_reference` requires referenced items to exist. It does not:
> `item_reference` only iterates over items that *exist* and checks *their* fields, and nothing
> validates `activity.items` at all. So an invented id does not fail — **it validates clean and leaves
> a dangling reference in the course.** A silent hole, not a workflow deadlock.

Two changes: the design flow swaps steps 3 and 4 (assessment-writer → lesson-planner, which then
reads the real ids), and a **new rule `activity_item_reference` (error)** requires every id in
`activity.items` to resolve to an existing item of that unit. Safe to swap because the entry quiz is
defined by the week's guiding questions (written in step 2), not by the hour's plan.

**(b) The never-overwrite rule is enforced in code.** It was specified as agent behaviour, with a
"(consider)" ledger row for a helper. The reviewer is right that this is too weak for a rule whose
failure is unrecoverable: "do not overwrite" is a negative constraint, and agents violate those on
long runs. `classkit` now *must* provide the write path agents use, and it structurally refuses to
overwrite without explicit confirmation — generalizing the guarantee `write_new()` already gives
`scaffold`. Stated in §5.2 and invariants (spec + `CLAUDE.md`) as the one place the framework does not
trust a prompt.

**(c) `guiding_question_assessed` is `off` in Core.** In Core the only items are entry-quiz items, and
a short quiz cannot test all ~15–20 guiding questions of a unit — so the rule would fire on every
valid unit, training the teacher to ignore all warnings. Switched off in `question-driven-25`'s
`rules:` block; turns on in the Assessment phase. New Core-appropriate `unit_has_entry_quiz_items`
(warn) checks the quiz exists at all.

**(d) Syllabus `workload` is optional.** Requiring it blocked a teacher from validating a syllabus
before credits were settled. Now optional, with `syllabus_workload_missing` (warn) while absent.

**(e) `max_unmapped_minutes`: default 10, and overridable per course.** The reviewer called 15 of 50
(30%) too generous for a guardrail. Avin set the default to **10** and required it be **a parameter in
the config file**, so a teacher can raise it — *"some teacher may decide to put it 50 and ignore it
altogether, which is also fine"*. So: methodology supplies the default, `course.yaml` `in_class:` may
override, the course has the last word (consistent with course sovereignty, D-014). Recorded in §9:
the lecture-reversion guarantee is a *default*, not something the framework can insist on.

**(f) Unit directory naming is specified.** `units/NN-slug/` was implemented in `scaffold.py` but never
written down, so an implementer would guess. Now in §8.2: two-digit number, title slugified
(lowercase, non-alphanumerics → `-`, trimmed, empty → `untitled`); the directory is found by its `NN-`
prefix, so the slug can be renamed by hand.

**(g) The assessment item's `answer` is renamed `model_answer`.** One key meant two things — a *list of
locators* on a guiding question, a *string* on an item. Renamed now because the item schema already
exists in code and renaming after implementation costs a migration.

**(h) Approval gates live in the orchestrating command.** The reviewer asked how gates work given a
command cannot suspend itself. Answer: they are conversational — but a **subagent cannot ask the
teacher anything**, so a gate placed inside an agent silently does nothing. The command runs one
agent, shows the result, waits, then runs the next. Stated in §5.2.

**(i) The `/plan-units` handoff is sequential and file-based.** "They share the outcome list" was prose,
not a mechanism. Now: `syllabus-designer` writes `syllabus.md` to disk first; `curriculum-architect`
reads it and references the outcome ids it finds there. The file is the handoff, so neither agent
invents an outcome id and either can be re-run alone.

**Not adopted:** nothing. The review raised no finding we rejected.

---

## D-034 — One repo, two hats: `CLAUDE.md` is teacher-facing, `dev/CLAUDE.md` is the developer's
**Date:** 2026-09-12 · **Status:** locked · **executed this session** · amends D-024

Preparing to hand-test as a teacher, Avin noticed that a fresh clone hands the teacher the
*developer's* `CLAUDE.md`, and asked whether the framework should be **split into two repositories**
— one for development (spec, devlog, its own `.claude`), one always-ready-to-clone for teachers, with
dev sessions writing into whichever is appropriate.

**Rejected, after a rigorous comparison. The problem is one file, not the topology.**

Checking what a clone actually contains: **`.claude/` is entirely teacher-facing and correct** —
`curriculum-architect`, `/design-unit`, `writing-guiding-questions` are the teacher's agents,
commands and skills. `dev/` was already accepted as tolerable clutter (D-024). `tests/`, `src/`,
`pyproject.toml` are either required or invisible. **Only `CLAUDE.md` was misaddressed.**

**The case for two repos** (recorded fairly, because it is not silly): a pristine teacher clone;
unambiguous hats; teacher history not polluted by ~45 framework-design commits; and it would let the
teacher repo go public while the dev repo stayed private, decoupling Q-016 from deleting `_devlog`.

**Why it loses today:**

1. **It destroys spec↔code atomicity, the discipline that has kept this project coherent.** The rule
   "alter structure → update `FRAMEWORK-SPEC.md` in the same commit", and "a locked decision gets a
   ledger row in the same commit", *cannot exist* when the schema is in one repo and the spec in
   another. A mechanical guarantee would degrade into a convention, and this project's own history
   (the spec-ahead-of-code gap needing a whole ledger to stay honest) is the evidence that
   conventions rot.
2. **It invents a release process** — cross-repo propagation for every change to code, templates or
   agents, with drift to detect and machinery to maintain, before Core is even finished.
3. **The dev repo would hollow out.** Code, schemas, templates, agents and tests must live where
   teachers clone, so repo A would hold only documents — meaning real development happens in the
   teacher repo anyway and the hats are not actually separated.
4. It duplicates the inner loop for a person who is both developer and teacher, and it is a large
   change to a model D-009, D-015 and D-024 all rest on, made mid-implementation.

**Decision: stay with one repo, fix the hat.**

- **Root `CLAUDE.md` is now teacher-facing** — vocabulary, IDs, the commands, how commands should
  behave, the rules agents follow. Correct by base rate: there is one framework repo and *many*
  course repos.
- **`dev/CLAUDE.md` is new** and holds the developer content: invariants, layout, the spec-update
  rule, how to add a validation rule, the agent-editing rules, how to run tests.
- **Vocabulary and ID conventions stay in the root file only**, with `dev/CLAUDE.md` pointing at
  them. Both hats need them; two copies would drift.

**How a session knows its hat (Avin's requirement: "every session should have a clear hat").**

The key constraint, which rules out the obvious answer: a teacher's repo *is* a clone of the
framework, so **anything the framework ships also lands in the teacher's repo** — a committed marker
file cannot discriminate, and neither can "`dev/` exists" (teachers have it too). What works:

1. **Default teacher.** Right by base rate, and it fails safe: a developer wrongly in teacher mode
   writes a course file, while a teacher wrongly in developer mode is told about pytest and the
   ledger at the moment they are most lost.
2. **A gitignored `dev/.developer` marker** — deterministic, and because gitignored files never
   clone, it exists only in a developer's checkout. Created once per checkout; forgetting it lands
   you in teacher mode, which is harmless and obvious.
3. **Task escalation** — asked to change framework internals, read `dev/CLAUDE.md` regardless.

**Mode reporting (also Avin's request).** Two mechanisms, because they fail differently:

- **A `SessionStart` hook**, `.claude/hooks/report-mode.sh` + `.claude/settings.json`: mechanical,
  fires every session. It both prints a line for the human (`systemMessage`) *and* injects the mode
  into the model's context (`additionalContext`) — so the model is *told* its hat rather than left to
  infer it. Tested in both modes; emits valid JSON.
- **An instruction in `CLAUDE.md`** to state the mode in the first reply and whenever it changes.
  This is the fallback if the hook does not run, and it is the only thing that can announce a
  *mid-session* change, which a start-of-session hook cannot see.

Honest cost: a project hook may prompt a teacher for approval on first open. Judged acceptable — it
is one "yes", the script is four lines of readable shell, and a teacher arguably *should* be told
what runs in their repo.

**Switching hats is a command, not a ritual (added 2026-09-12, Avin's suggestion).** The setup step
was `touch dev/.developer` — folklore a new developer had to find, with nothing checking that the
marker was actually ignored. That is exactly the bug this session hit: `.gitignore` turned out to be
untracked on this machine (a global exclude of `.gitignore` itself), so the rule existed only
locally. So the switch moved into the tooling:

- `classkit mode` — report the current hat
- `classkit mode developer` — **verify the ignore rule first**, then create the marker; refuse with an
  explanation if the rule is missing, because a committed marker would put every teacher's clone into
  framework-developer mode
- `classkit mode teacher` — remove it

**Code, not a slash command**, deliberately (D-018: code verifies): the ignore check is mechanical and
must not be skippable, and a `/developer-mode` command in `.claude/commands/` would also appear in
every teacher's command list. Documented as step 1 of `dev/CLAUDE.md`'s setup. Six tests in
`tests/test_mode.py`, including one that asserts the marker is ignored **in the real checkout**, so
the rule cannot be silently dropped again. The command also prints that a running session must be
restarted — the hook reads the marker once, at startup.

**Two repos revisited at release,** not discarded: see Q-031.

---

## D-032 — `syllabus.md` is a complete Bologna descriptor; *rendering* it is deferred to Exports
**Date:** 2026-09-10 · **Status:** locked (design) · **implementation pending** · amends D-021 ·
resolves gap **G-15** from `reviews/impl-gaps-step-0-1.md`

The implementation gap report found "the rendered syllabus" referenced three times in the spec and
specified nowhere — no command, no format, no phase, no ledger row — while being load-bearing in the
*argument* for why identity fields are not repeated in the syllabus.

Avin drew the distinction: *"If by rendering you mean creating a PDF for students (from the .md file)
then we can defer it to later. But the .md file needs to contain potentially all the information the
Bologna style has (even if we fill it in steps, or decide to skip some information)."*

**Two separate things, split accordingly.**

1. **Rendering — deferred to Exports.** Producing one human-readable document (PDF or similar) that
   combines `syllabus.md`, the identity fields from `course.yaml`, and a unit overview derived from
   the units. It is a *generator*, like PPTX and the Gem bundle, so it belongs with them. Added to the
   Exports row in §1.1, and the three references that implied it already exists were reworded.
2. **The `.md` itself must be a complete Bologna descriptor — now.** The previous field set (goal,
   outcomes, workload, prerequisites, reserved assessment) was short of what a Bologna course
   descriptor carries, which would have forced a teacher to keep syllabus information somewhere
   outside the framework. Added, all optional: `level`, `course_type`, `offered` (year/semester),
   `teaching_methods`, `reading` (required/recommended, preferring `textbooks[].key` references).

**`teaching_methods` is the one that earns its place pedagogically** — for a flipped course it is the
field that actually says what the course *is*, and Bologna descriptors expect it.

**Only `goal` and `outcomes` stay required**; everything else may be filled in stages or skipped
deliberately (Avin's condition).

**The rule that decides what is a field here** — worth stating because it recurs: **authored content
is a field in `syllabus.md`; derived content is assembled at render time.** So identity and
configuration (title, code, institution, instructors, language, textbook list) stay in `course.yaml`
as the single source of truth, and the unit overview stays derived from the `unit.md` files. Copying
either into the syllabus would create exactly the drift D-021 was designed to prevent.

---

## D-033 — Validation rules declare which course *state* they judge; `syllabus_missing` is an error
**Date:** 2026-09-10 · **Status:** locked (design) · **implementation pending** · resolves gaps
**G-12** and **G-9** from `reviews/impl-gaps-step-0-1.md`

Both gaps came out of implementing steps 0–1, and both are instances of one omission: **§8.4 defined
every rule against a *finished* course**, while a course spends almost all of its life half built —
every implementation step, and a teacher's whole authoring semester. Invariant 6 even *requires* a
freshly scaffolded course to validate clean.

**(1) Rules are of two kinds, and each must say which it is.**

- **Consistency rules — always active.** Does what is *present* hold together? Schema, ids, dangling
  references, duration sums, counts against methodology ranges. A half-written course can still be
  internally consistent.
- **Completeness rules — active only when the course is complete.** Has everything promised been
  delivered? Unanswerable while material is still being written.

**The course is complete when units on disk == `course.yaml` `units`** — the condition `unit_count`
already computes. While incomplete, a completeness rule does not fire and `classkit validate`
**reports that it was skipped, and why**, so the gap is visible rather than silent.

**`outcome_coverage` is the completeness case.** Read against a 3-of-13-unit course, every
not-yet-covered outcome is an error: it would fail every scaffolded course (breaking invariant 6 at
step 3's first commit) and shout through an entire authoring semester until the teacher turned it
off. A rule teachers disable protects nothing.

**The asymmetry this creates in the coverage chain is deliberate and worth keeping in mind:**
*objective → outcome* is a **consistency** rule (an objective rolling up to nothing is wrong the
moment it is written), while *outcome → objective* is a **completeness** rule (an outcome nothing
covers yet is just unfinished work). Both directions are still checked — they simply become
meaningful at different times.

**(2) `syllabus_missing` — new rule, severity `error`.** There was `in_class_missing` for a unit and
nothing for the syllabus, although §4 makes it a required artifact. Two reasons error is right rather
than warn: `scaffold course` always creates it, so absence means deletion, not drafting; and a course
with no syllabus has **no Course Outcomes**, making `outcome_coverage` *vacuously true* — the rule
that closes the coverage chain would pass most confidently exactly when the roof is gone. That is the
same class of silent hole as the dangling `activity.items` reference found in D-031a.

Both rules land in **step 3**, with the rest of the coverage chain.

---

## D-035 — Ingest: a derived, addressable layer over whatever the teacher has
**Date:** 2026-09-29 · **Status:** locked (design) · **implementation pending** · resolves **Q-028**

**Sequencing first.** Claude proposed implementing step 3 (`/plan-units`) before designing ingest,
on the grounds that step 3 does not structurally depend on it and would teach us what ingest needs.
Avin disagreed and was right: **the organization of materials is the input contract for every agent
downstream**, so building `/plan-units` against an unspecified heap means reworking it once ingest
defines the contract; and a teacher never runs step 3 without step 2, so testing it without ingest
would test a workflow nobody follows. It is also simply the "workflow order outside" principle.

**Assumptions (Avin):** the framework is general, not DS&A-shaped; the teacher is **not** assumed to
be organized — one folder of everything or a tidy tree; material may be duplicated (a PPTX and its
PDF); any format may appear; material is added over time.

**Decisions** (full normative text in spec §8.7):

- **Two layers.** `materials/source/` is the teacher's and agents never modify it;
  `materials/ingested/` is derived — **one `.md` per material, flat, keyed by a stable id `M<NNNN>`**
  (not `S`, which already means Study Session). Flat rather than mirroring `source/` so that renaming
  or moving a file never breaks a locator; the manifest re-matches it by content hash.
- **A manifest** (`materials/manifest.yaml`) records every material: id, title, format, kind,
  source paths (plural, for merged duplicates), the canonical source, hashes, status, likely units.
- **Explicit anchors** — one heading per slide or page, or the document's own headings — so a locator
  like `M0007#slide-18` names a place that demonstrably exists. **New rule
  `material_locator_resolves` (error)** makes invariant 7 *partly mechanical* for the first time: a
  fabricated "slide 18" in a 12-slide deck now fails validation instead of reaching a student.
- **Links:** `materials/source/links.md`, one URL per line with an optional note, plus **`classkit
  add-url`** (Avin's request) to append safely; URLs found *inside* documents are collected too. Core
  records links and fetchable metadata, not their content.
- **Extraction is code** (D-018 — anchors must be reproducible): built in for md/txt/pptx/pdf/docx;
  pandoc and LibreOffice used *if installed* for odt/rtf/html/epub/ppt/doc/odp; anything else is
  recorded `unsupported`, reported, never fatal. Proactive for common formats, reactive for the rest;
  a new format is one extractor registered by extension. Scanned PDFs (`no-text`) and audio/video
  (`media`) are flagged, not handled, in Core. This also keeps the install light — the heavy tools
  are optional.
- **Classification and duplicate *confirmation* are agent work**; exact duplicates merge by hash
  without asking, suspected same-material duplicates are confirmed by the teacher.
- **Pre-flight report first** (Avin's point: ingest can be long) — counts, duplicates, links,
  unsupported files, a time estimate — then an approval gate. **Incremental and resumable** by hash.
- **Ingested text is editable** (Avin): a hand edit is detected by `ingested_hash` and preserved —
  re-ingest goes through the write path, which refuses, and the teacher is asked.
- **A removed source is marked, never deleted**, so locators to it fail visibly.

---

## D-036 — The course log
**Date:** 2026-09-29 · **Status:** locked (design) · **implementation pending**

Avin's idea: a log of every non-trivial change to the course — syllabus added, unit created, session
changed, materials added — "such a log can help agents in the future". **Scope, per Avin: the course
only**, never framework development.

Why it is not redundant with git: git records *which bytes changed*; the log records **what the
change meant and why** ("reworked U03-S02 — students found it too long"). An agent revising a course
next year needs the second.

- `LOG.md` at the course root, append-only, one entry per non-trivial change: date, which command or
  who, what changed **by ID**, why, files.
- **Every approved step of every command is an entry** — the log entries and the approval gates of
  D-030 are the same moments. Each ingest run is an entry.
- Written by **`classkit log`**, so the format is consistent and parseable, not left to each agent.
- Agents read recent entries before starting work. The teacher may add entries by hand.

Cross-cutting (every command writes to it), but lands with step 2 because ingest is its first user.

---

## D-037 — The teacher is the authority: validation informs, it does not overrule
**Date:** 2026-09-29 · **Status:** locked (design) · **implementation pending** · amends D-021,
D-028, D-031e, D-033 (severities) and the wording of invariant 4

Avin: *"I think you over-push for validation tools… I'm afraid they may cause problems for a teacher
to make progress. The teacher is the authority, and it is his responsibility to check everything he
delivers to students. I don't want the framework to be too strict in preventing out-of-the-box
solutions or some inconsistencies (which are sometimes ok in class)."*

Correct, and Claude owned it: `VISION.md` already said validation is a *feature* that exists to catch
what **agents** get wrong, yet decision after decision promoted pedagogical checks to `error` —
`syllabus_missing`, the unmapped-time cap, coverage. Each looked reasonable alone; together they
turned a teacher's deliberate choices into failures.

**Principle:** validation checks the agents' work and reports on the teacher's; it never overrules
the teacher. *Code verifies; agents judge; the teacher decides.*

**Two kinds of rule, split by a mechanical line.** *Names something that does not exist, or cannot be
read* → **integrity → `error`** (dangling ids, missing items, a locator to a nonexistent slide,
unparseable front matter — almost never intentional, and agents cannot reason over them). *Something
missing, or a departure from the methodology* → **advisory → `warn`**. One concern can yield both: an
objective naming a nonexistent `CO9` is integrity; an objective naming no outcome is advisory.

**A third severity, `alert`** — high-priority advisory, reported first, never failing `validate`.
Avin's call for coverage: *"advisory, since this could be a temporary glitch and it is still the
teacher's responsibility, but a HIGH-priority alert."* Alert: `outcome_coverage`,
`objective_coverage`, `objective_maps_to_outcome`, `syllabus_missing`.

**Demoted from error to warn:** `session_count`, `goal_count`, `goal_type`, `in_class_missing` (a
holiday or online week is legitimate), `in_class_duration_match`, `activity_count`, `activity_type`,
`require_opening_quiz`, `answer_reference_present`, `deferred_question_resolved_in_class`,
`session_budget_feasibility`, `in_class_unmapped_time_cap`. Split: an activity naming a guiding
question from *another* unit becomes advisory (also unblocks Q-029's homework-checking quiz); an item
with no correct choice becomes advisory. New integrity rule `outcome_reference`.

**Exceptions stop nagging** (a warning that always fires trains the teacher to ignore all warnings):
`course.yaml` `rules:` overrides any rule course-wide — the teacher's last word, above the
methodology; and `accepted: [{rule, reason}]` in any artifact's front matter suppresses one rule for
that file. Accepted exceptions are counted in `validate`'s output (never invisible) and logged.

**Agents fix what they caused and never overrule the teacher:** they resolve or surface findings
from their own output, never add `accepted:`, change `rules:` or raise a threshold unless asked, and
never "correct" a teacher's decision. Invariant 4's "never raise the cap to make a validation pass"
becomes a rule about agents, not teachers.

**Schemas check shape, not pedagogy** — otherwise a schema `required` turns advice back into an
error by the back door (e.g. `answer` and `outcomes` presence move from schema to advisory rules).

**Unchanged and deliberately so:** never-overwrite (invariant 5) is not validation. It constrains
nothing the teacher chooses; it protects the teacher's work from an agent.

---

## D-038 — Step 2a review outcomes: the teacher's own exceptions are advice; one write path
**Date:** 2026-09-29 · **Status:** locked (design + implemented) · sources:
`reviews/impl-gaps-step-2a.md` (implementer), `reviews/impl-review-step-2a.md` (Gemini review)

Step 2a (D-037 re-classification, D-036 course log) was implemented in a fresh session and reviewed
by an independent agent. Avin accepted Claude's consolidated recommendations. Claude's assessment of
the review itself: its main finding was right and was reached independently, but it was thinner than
it looked — it skipped the test-quality check, covered only one invariant, and reported "no nits";
reading one schema file surfaced two things it missed (findings 1–2 below).

**Decided:**

- **G-6 — `reason` in `accepted:` is optional**; a missing or blank one is the new advisory rule
  `accepted_without_reason` (warn). The implementer had made it a schema error. The reviewer and
  Claude both flagged that this contradicts the implementer's own G-10 reasoning — a mistake in a
  teacher's *own exception* should not fail the build — and D-037.
- **Review miss 2 — `rule` is no longer pattern-checked.** The schema pattern made a capitalised typo
  a schema error while a lowercase typo was only an `unknown_rule` warning — the same inconsistency
  as G-6. Now every mistyped code is `unknown_rule`.
- **Review miss 1 — the documented `accepted:` example used `session_budget_feasibility`**, a rule
  that does not exist until step 4; a teacher copying it got `unknown_rule`. The example is now
  `in_class_missing` ("holiday week"), in `unit.md` — a rule that exists and the better case anyway.
- **G-17 — the course log appends *through* the write path.** Rather than document the log as an
  exception to "every write goes through `classkit.write`", the write path gained an append mode
  (`append()`, `classkit write --append`), so the rule stays literally true. The reviewer offered
  both options; Claude preferred this one as keeping a single path.
- **G-1** split-rule names kept; **G-10** `unknown_rule` stays warn; **G-13** wording — only an
  acceptance an *agent* adds at the teacher's request is logged; `validate` is read-only.
- **Ratified** the implementer's own design decisions G-7 (unit-level findings accepted in
  `unit.md`), G-9 (what the accepted count reports), G-11 (every rule registered; an unregistered
  code raises), G-14 (`classkit log` arguments; cost accepted: `--changed` is required even for a
  simple CLI entry — hand-editing `LOG.md` has no such constraint), G-15, G-16.
- **Recorded ahead of time:** G-20 — a goal's `est_minutes` is not schema-required; step 4's budget
  rule reports a missing estimate as *unverifiable*. G-19 — an `open` item's `rubric` moves from
  schema `required` to an advisory rule in step 5.
- **Kept deliberately (review question):** a unit's `objectives` stays schema-required, ≥1. Without
  objectives the coverage chain cannot even be expressed for that unit — shape, not pedagogy.

99 tests (92 + 7).

## D-039 — Step 2b review outcomes: a read-only classifier; ingest logs itself; book citations
**Date:** 2026-10-01 · **Status:** locked (design + implemented) · sources:
`reviews/impl-gaps-step-2b.md` (implementer), `reviews/impl-review-step-2b.md` (Gemini review)

Step 2b (ingest, D-035) was implemented in a fresh session and reviewed by an independent agent.
Avin decided the open items one by one. Claude's assessment of the review: its blocking finding
pointed at a real hole but overstated it ("breaks the entire safety model": the orchestrating
session has every tool anyway, and four other agents have Bash, so invariant 5 guarantees the write
path, not a sandbox). Both test gaps it named were real, and verified. It accepted G-7 and G-6
without engaging the reasons against; Claude disagreed with both, and Avin sided with Claude.

**Decided:**

- **G-1 → the classifier is read-only.** `material-classifier` has `Read, Grep, Glob` only — no
  Bash. It *returns* its classification as a YAML block; `/ingest` shows it, applies the teacher's
  corrections, and records it with the new **`classkit material apply`** (all or nothing). Why this
  agent first: it reads more untrusted text than any other (the teacher's files and what they
  quote), so it is the strongest case for a structural guarantee, and the price was small. Costs: one
  more CLI verb; the agent cannot check its own recording; the command passes it the suspected
  pairs. Side benefit: the teacher sees the classification *before* it is recorded. The other
  agents' Bash is decided as each is rewritten (G-4 carry-over), not now.
- **G-7 → `classkit ingest` logs itself.** Every run that changes something appends an entry (title
  `classkit ingest`, what changed by material id, `--why`, default "run by hand"); a run that changes
  nothing, or only refuses, does not. `/ingest` passes `--no-log` and writes its own entries. The
  implementer had argued by analogy with `validate` (D-038); that does not hold, since `validate`
  changes nothing while ingest assigns ids, adds and removes materials — and §8.8 says "so is each
  ingest run". Cost: one more flag; a forgotten `--no-log` doubles an entry (noise, not loss).
- **G-3 → PDF anchors stay physical pages**, plus Avin's rule: **every book citation carries the
  book's own coordinates in its `note`** — section, exercise or question number where there is one,
  and the printed page: `ref: "M0003#page-63"`, `note: "CLRS §6.2, Exercise 6.2-3 (printed p. 45)"`.
  Why: a wrong physical page still validates (the page exists); the note is what a student with a
  paper copy, or a teacher checking, can verify. Cost: a prompt-level convention until step 4, where
  an advisory rule (a locator to a `textbook` material without a `note` → warn) is proposed.
- **G-6 → `/plan-units` re-maps the materials' `units`** once the unit map is approved — a gated
  step, recorded through `classkit material apply`. The reviewer called this churn; Claude argued
  that a confidently wrong hint ("Lecture 3" → U03 after units were merged) is worse than none,
  because the designer agent trusts it. How to protect a hint the teacher corrected by hand is
  decided in step 3.
- **Ratified:** G-2 (five extra manifest fields), G-4 (merge keeps the target's anchors; the
  retired `.md` stays), G-5 (a changed merged copy is split off; only an identical copy inherits a
  deleted canonical's id), G-8 (lxml/Pillow wheels). G-22 (declined duplicates not remembered) and
  G-26 (manifest comments lost) left as they are until the hand test shows whether they matter.
- **Review test gaps, fixed:** `materials_not_ingested` on a moved and on a removed source; a locator
  checked against a hand-edited `.md` (an added heading resolves, a removed one fails).

173 tests (163 + 10).

## D-040 — Private and instructor-only material; `validate` judges the course, `doctor` the machine
**Date:** 2026-10-01 · **Status:** locked (design) · sources: `reviews/manual-test-step-0-2b.md`
(Avin's hand test of steps 0–2b: F-04, F-05, F-16, F-22, P-4, F-09)

The hand test ingested CLRS 4e (1312 pp.), its instructor's manual and its selected solutions.
Two problems surfaced, and a third neither the test nor earlier sessions had flagged: **nothing in a
course repo is gitignored**, so the first `git push` puts every book PDF *and its full extracted
text* on GitHub, permanently in history. Avin's question — does a famous book need an ingested
`.md` at all, given Claude cites CLRS well from memory? Claude's answer: memory is good for content
and section numbers of famous books, unreliable for pages and editions (the test itself found a
3rd/4th-edition mix), and useless for less famous material; the test's best classifier results (the
+22 page offset checked on 40 sections, the manual→deck derivation, the "posted publicly" markers)
needed the text. But citing and checking need only an **index**, and reading needs the text only
locally. Decided (Avin, one at a time):

1. **Storage — `source/private/`, gitignored.** Its materials get a committed **index** in
   `ingested/` (every anchor, printed page label, sections from the PDF outline — no body text) and
   their **full text in `materials/private-text/`**, gitignored, this machine only. Locators
   validate against the index everywhere. Cost accepted: on another clone agents can cite and
   validate a private book but not read it.
2. **Audience — `audience: student | instructor`** in the manifest, default `student`, proposed by
   the classifier and confirmed at gate 3. Independent of `private` (CLRS is private but `student`).
   Citing an instructor material from a **student-facing** place (study path, `answer`, later the
   Gem) is an **alert**, `instructor_material_cited` — not the in-class plan or a model answer.
   **The hard guarantee is at publication:** every exporter refuses, in code, to bundle instructor
   or private material. Claude first suggested an alert in `validate` alone, then argued for the
   export gate: a study path in the repo reaches no student until it is published, so that is where
   the guarantee belongs; an `error` in `validate` would add little (the teacher may accept it,
   G-12) and fail every run over something that is not yet a leak.
3. **A missing private source is "not on this machine", never "removed"** — a TA's clone and a
   deleted file are indistinguishable from inside a checkout. Removal is explicit:
   `classkit material remove ID`. Cost: a book deleted on the teacher's own machine keeps its record
   until removed.
4. **Scaffold writes `course/.gitignore`** (in `course/`, so it never conflicts with a framework
   update) covering `private/` and `private-text/`; and `private_material_committed` (warn) reports
   anything git already tracks there. Detecting is the framework's; cleaning history is the
   teacher's.
5. **`classkit doctor`** (Avin's proposal: a local-consistency check), with the principle it made
   explicit: **`validate` judges the course** — committed state, the same answer on every clone —
   **and `doctor` judges this machine**: private sources and full texts present or stale, the
   `.gitignore`, dependencies importable (would have caught F-09's missing fontTools), optional
   converters, the mode. Read-only; `/ingest` runs it first. So `materials_not_ingested` now ignores
   `private/`.

Meanwhile `GETTING-STARTED.md` warns teachers not to commit book PDFs until this is built.

**Added to D-040 the same day — two-format duplicates are no longer detected (reverses part of
D-035).** The hand test's 13 suspected pairs were all false (F-11): the content check compared
vocabularies with no size limit, so any short document "duplicated" a 1312-page book. Claude first
proposed a narrower detector plus remembered dismissals (F-15). Avin asked what a duplicate actually
breaks. Claude's analysis: nothing — `M0007#slide-18` and `M0012#page-18` are both correct citations;
the rest (a slightly less precise page, a stale export, a redundant study path, a bigger Gem) is
preference, critic territory, or an exporter's concern. Claude had treated "detect duplicates" as a
requirement because D-035 listed it, without asking what it protects. **Decided:** drop
suspected-duplicate detection (name and content) and its gate-3 question; keep the silent merge of
exact copies; keep `classkit material merge` as an optional, never-prompted tool; the classifier may
*mention* a two-format relation; agents cite the deck over its PDF. F-15 and G-22 are moot. Cost: the
manifest keeps both copies, the classifier reads both; deduplication, if ever needed, happens in the
exporter.

**Added to D-040 — links are not harvested from materials (F-13).** Ingest recorded every URL found
inside slides and documents as a material: in the hand test, 10 of 11 came from the book's and
manual's bibliography, two were truncated at line wraps, and the course Gem link was buried. Same
question as for duplicates — what does harvesting protect? Little: a link inside a deck is already
readable in its ingested text. **Decided (a):** a link becomes a material only when the teacher lists
it (`links.md` / `add-url`); the classifier *mentions* links that look like course resources and
suggests `add-url`. Rejected: (b) harvest only from the teacher's own materials — `kind` is not known
at conversion time, so it needs a second pass; (c) a separate link pool — still noise nobody asked
for. Cost: an unlisted link is not a citable material; `found_in` and the harvesting code retire.

**Added to D-040 — `units: all` (F-17).** The classifier could not say "course-wide" for the textbook
or the course Gem: `[]` reads as "no unit", and listing every unit looks per-unit and gives the D-039
re-map twelve entries meaning one thing. Low stakes, but both readings mislead a designer filtering
by unit. **Decided (a):** `units` is a list of units or the word `all`; `[]` keeps meaning "no
particular unit". Rejected: (b) a separate `scope` field — two fields that can contradict; (c) a
convention on `[]` + `kind: textbook` — fails for a course-wide item that is not a book. Cost: a
two-shaped field every consumer must handle.

**Added to D-040 — the coverage report is persisted, and planning works on partial material (F-19,
Avin).** F-19: the coverage report existed only in chat, though `/plan-units` needs it. Decided:
`/ingest` writes it to `materials/coverage.md` after the teacher has read it (write path; a later run
replaces it only on confirmation; a dated snapshot, input not truth). Avin then raised the normal
case the spec ignored: material for only some units, and wanting to start on the syllabus and the
first unit. Decided:

- The report **states its scope**: which units the material reaches; "no material yet", never
  "thin", for the rest.
- **The course level is always whole but needs evidence** (Avin): goal, outcomes and the **unit
  map** come from something ingested that spans the course — an old syllabus, a book's table of
  contents — plus the teacher; with none, `/plan-units` asks rather than drafting from memory. **The
  unit level is incremental**: objectives come later, from each unit's own slides or the book's
  chapters read in depth; `/plan-units 4 5` plans more units as material arrives.
- **Where an unplanned unit lives — (ii), the syllabus.** A `unit_map` (number, title, summary,
  evidence) in the syllabus front matter, authoritative for which units exist; a `units/NN-slug/`
  directory only once a unit is planned. Rejected (i), a `unit.md` with no objectives: it reverses
  D-038's deliberate "objectives required", and eleven unplanned units would each fire session and
  in-class warnings unless those rules learned "unplanned". Cost of (ii): a unit's title lives in the
  map and in `unit.md` (and the count in `course.yaml`) — `unit_map_mismatch` (warn) catches drift;
  D-032's "overview derived from the units" becomes "from the map and the units".

**Added to D-040 — one resource-kind vocabulary (F-21).** A study path could not be of kind `slide`;
there were three overlapping lists (material kinds, path kinds, D-019's planned answer kinds, with
`slide` vs `slides`). And when `ref` is a material locator, the manifest already knows the kind, so a
`kind` there can only repeat or contradict it. **Decided:** now (2c) add `slides` and `notes` to
path kinds; in step 4, one vocabulary (material kinds + `gem`, `web`) for paths and answers, and
`kind` optional when `ref` is a locator. Cost: an agent reading a path must look up the manifest to
know its kind. (F-21's side note — schema violations print as `warn` — did not reproduce: they are
`error`.)

**Added to D-040 — a refusal shows what replacing would change (F-24).** The hand-edit refusal
previewed the file's first lines (its front matter), not the edit. The old extraction is not kept
(only its hash), so the teacher's edit alone cannot be shown. **Decided (a):** show the diff between
the current file and a fresh extraction of the new source, grouped by anchor — exactly what
`--overwrite` would change. Cost: it cannot attribute differences to the teacher or the source.
Rejected for now: (b) per-anchor hashes to label sections (extra state; 1312 hashes for one book);
(c) keeping full copies of every extraction. (b) can be added later if this confuses.

**Added to D-040 — locators in prose are checked (F-26).** `material_locator_resolves` reads only
front matter, but locators also appear in prose — 65 in the hand test's coverage report, now a
permanent file — and the agent once wrote shorthand (`#page-39`) that resolves against the wrong
material. **Decided:** agents always write locators fully qualified (instruction only: `#section` is
also an ordinary Markdown link, so code cannot catch the shorthand); and a new
`material_locator_in_text` (**warn**) checks `M<NNNN>#anchor` in the bodies of the course's own files
and `coverage.md`, not `LOG.md` or `ingested/`. A deliberate departure from D-037's mechanical line —
front matter is data tools act on, prose is read by people and may be a dated snapshot that
legitimately goes stale. Cost: a non-locator string like "M2024" warns (acceptable, and acceptable
per file).

**Added to D-040 — invariant 5's scope, and `classkit write --diff` (P-2).** In the hand test the
agent edited `course.yaml` at the teacher's request with its own Edit tool and `sed`, outside the
write path, because `classkit write` replaces whole files. Claude's analysis: invariant 5 protects
against *silent loss of the teacher's work* by the framework's own writes; a targeted edit the
teacher asked for, made with a tool that shows its diff, is not that. **Decided:** (1) invariant 5's
scope is stated — the framework's commands and agents; a direct teacher-requested edit is the
teacher's. (2a) `classkit write --diff` prints exactly what `--overwrite` would change; a command
changing part of a file shows it, then writes on approval. Rejected (2b), a key-level YAML editor:
keeping a commented `course.yaml`'s comments needs a new dependency and a path syntax. Cost: the
invariant now openly says what it never covered.

## D-041 — Step 2c-1 outcomes: the local full text certifies itself; several machines; one more guard
**Date:** 2026-10-01 · **Status:** locked (design) · sources: `reviews/impl-gaps-step-2c-1.md`

Step 2c-1 (privacy and `doctor`, D-040) was implemented in a fresh session (233 tests). Its gap
report found that D-040's spec reasoned about one machine plus a clone without the file, not about
several machines with the file. It also caught an error of Claude's: the spec claimed extraction "is
the same on every machine", true only for one library version. The review is deferred to after 2c-2
(Avin: two implementation rounds, one review). Avin decided:

- **G-1/G-3 (b) — the local full text certifies itself.** Its front matter carries `body_hash`; a
  body that matches is ingest's output and is replaced freely, including a stale one (refreshed, no
  longer refused); one that does not is an edit, protected. `private_text_hash` retires from the
  committed manifest. Why: it follows D-040's own principle — what differs per machine stays on the
  machine. Cost: one front-matter field; an edit to that front matter counts as an edit.
- **G-2 (c) — last machine wins, plus a `doctor` note** when this machine's copy differs from the
  one the index was built from. Accepted while one person usually ingests; an explicit
  `ingest --reindex ID` (b) is on record if several people do.
- **G-4 — `course_gitignore_missing` (warn).** "Is `course/.gitignore` there and does it cover
  `private/`" is committed state, so `validate` checks it too; `doctor` (asking git) still catches
  "present but never committed". Found: Avin's `~/.gitignore_global` ignored `.gitignore` itself, so
  no course created on his machine would have shipped its ignore rules. Avin deleted the file.
  Follow-ups: `.DS_Store` into the framework's and the course's `.gitignore` (it surfaced at once);
  `classkit mode developer`'s safety check must verify `.gitignore` is tracked.
- **G-5 — accepted as built**, now stated in the spec: an identical copy across the `private/`
  boundary leaves the material public; `doctor` says delete the public copy.
- **G-6 (a) — `material remove` does not log itself**, like the other `material` verbs; `/ingest`
  logs it. Claude leaned (b) for a simpler rule; Avin kept the smaller surface.
- **Plain fixes:** G-16 — a guarded `write.remove()` so the one deletion goes through the write
  path; G-22 — replacing a file keeps its permissions (the write path was leaving `0600`).
- Ratified as built: G-7 … G-15, G-17 (recorded in the spec by the implementer).

**Added to D-041 — step 2c-2's ⚑ items, accepted as built** (`reviews/impl-gaps-step-2c-2.md`):
G-1 — links harvested by an earlier version are marked removed on the next ingest unless
`links.md` lists them; `add-url` restores one under its old id (cost: eleven materials disappear
from the test course; the Gem must be re-added). G-2 — a changed private source is a `doctor`
**note**, not an ACTION (follows from D-041; cost: a teacher who really updated the book gets exit
0). G-3 — re-ingest never replaces a title, including ingest's own bad ones (cost: the re-test uses a
fresh course). Also recorded: the spec's claim that hyperlinks were readable in the ingested text was
false — Claude's error, the second unverified claim about the code in two rounds (after "extraction
is the same on every machine"); the implementer fixed the extraction. Claude now verifies a claim
about the code before writing it into the spec.

## D-042 — Agents never copy private text into course files; `doctor` checks for it
**Date:** 2026-10-01 · **Status:** locked (design + implemented) · sources:
`reviews/impl-review-step-2c.md` (Gemini review of 2c-1 + 2c-2) and Claude's own check of it

The independent review of 2c-1 and 2c-2 found nothing blocking or should-fix (two nits, both
already resolved or known). Claude's assessment: thin — it did not say how it searched committed
files for the book's text, and it missed the one real gap although the review prompt named the place.
**The gap:** D-040's guarantee ("no body text of a private material reaches a committed file") is
enforced in code only for what *code* writes. Agents read the full text and write committed files —
the coverage report (now saved, `materials/coverage.md`), and from steps 4–6 sessions, answers'
notes, activities — and nothing told them not to quote. Neither implementer nor the reviewer caught
it. **Decided (Avin):** both layers —
1. **the rule**, in the root `CLAUDE.md`, the classifier and §8.7: cite by locator, own words, at
   most a short quoted phrase;
2. **the check**, in `classkit doctor` (only a machine with the full text can make it): any
   committed course Markdown file sharing **12+ consecutive words** with a private full text is an
   ACTION naming the file, material and anchor; the course log is included; skipped, and said so,
   where no full text is present.
Cost: catches verbatim copying only; 12 is a first guess; a few seconds and ~150 MB on a book-sized
text. 294 tests (+5). Review nits: (1) the deletion is already through `write.remove()`; (2) a
globally-ignored `.gitignore` is caught only by `doctor` — the stated cost of D-041.

