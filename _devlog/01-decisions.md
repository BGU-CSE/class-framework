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
