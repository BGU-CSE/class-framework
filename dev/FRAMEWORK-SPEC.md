# Framework specification

What the framework must contain, and the exact fields, rules, and identifiers an implementation must
produce. This is the source from which the framework is built.

**Why the project exists and what it is for is in [`VISION.md`](VISION.md).** This document assumes
that and specifies the *what*. It is written to be **self-contained**: an agent with no memory of the
design conversations should be able to implement or verify a phase from this file alone. Rationale is
stated in a sentence or two and tagged `D-nnn` — those tags are breadcrumbs into
`_devlog/01-decisions.md`, which holds the history. They are traceability, not required reading.

---

## 1. Scope of this specification

### 1.1 Phases

The framework is specified and built in **vertical slices**: a phase is specified, implemented,
tested on a real course, and corrected before the next phase is specified (D-022).

| Phase | Covers | Status |
|---|---|---|
| **Core** | Course initiation, syllabus, course outcomes, units, at-home study sessions, the in-class hour **including the entry quiz** | **Specified below** |
| Assessment | Homework, programming assignments, exams, the grading scheme | Deferred |
| Exports | The class Gem builder, PPTX, **the rendered syllabus** (one human-readable document — e.g. PDF — combining `syllabus.md`, the identity fields from `course.yaml`, and a unit overview derived from the units). Every exporter **refuses, in code, to bundle or publish instructor-only or private material** (§8.7, D-040) | Deferred |
| Metrics | Measures for improving a course or its activities | Deferred |
| Lifecycle | Semester arc, revision, re-offering | Deferred |

**This document currently specifies Core only.** Later phases are named here so their absence is
understood as deliberate, not as a gap. Do not implement beyond Core.

The bar for Core: everything needed to **generate and run the learning part** of a flipped course.

### 1.2 The specification runs ahead of the code

The Core specification was completed before the code was changed to follow it. `schemas/`,
`src/classkit/`, and several files under `.claude/` still implement an **earlier model**.

> **The implementation ledger in [`ROADMAP.md`](ROADMAP.md) is authoritative for what actually
> exists.** Fields and rules marked **(target)** in §8 are specified here but not yet built. A
> mismatch between this document and the current code is expected, tracked, and not a defect.

### 1.3 Where documentation belongs

| Document | Audience | Answers |
|---|---|---|
| `README.md` | Anyone | What is this and how do I use it? |
| `GETTING-STARTED.md` | Teachers | How do I turn my course into a flipped one? |
| `dev/VISION.md` | Developers, agents | Why does this exist, what does it produce? |
| **`dev/FRAMEWORK-SPEC.md`** | **Developers, agents** | **What must the framework contain, exactly?** |
| `dev/ROADMAP.md` | Everyone | What is built, what is next, why? |
| `CLAUDE.md` | Agents editing the framework | What must I not break? |
| `dev/_devlog/` | Developers (temporary) | How did we get here? What is still open? |

---

## 2. Framework architecture

Framework-wide: these apply to every phase, not only Core.

### 2.1 The four layers

```
┌────────────────────────────────────────────────────────────┐
│  COMMANDS      .claude/commands/*.md                       │
│  what the teacher types. Orchestration only —              │
│  which agents, in what order, and why that order.          │
└───────────────┬────────────────────────────────────────────┘
                │ invokes
┌───────────────▼────────────────────────────────────────────┐
│  AGENTS        .claude/agents/*.md                         │
│  judgment. Each has its own context and tool set.          │
│  Write course content; cannot verify their own arithmetic. │
└───────────────┬───────────────────────────┬────────────────┘
                │ loads                     │ runs
┌───────────────▼──────────────┐  ┌─────────▼────────────────┐
│  SKILLS  .claude/skills/     │  │  TOOLING  src/classkit/  │
│  craft shared by >1 agent,   │  │  verification.           │
│  so the designer and the     │  │  Deterministic, tested,  │
│  critic judge by one bar.    │  │  free, agent-independent.│
└──────────────────────────────┘  └──────────┬───────────────┘
                                             │ enforces
                                  ┌──────────▼───────────────┐
                                  │  SCHEMAS  schemas/*.json │
                                  │  the content contract.   │
                                  └──────────────────────────┘
```

### 2.2 Code verifies, agents judge

The division of labour is deliberate (D-018).

**Code does what must be exhaustive, arithmetic, deterministic and cheap.** A 13-unit course is
dozens of files with hundreds of guiding-question references that must all resolve, plus hundreds of
small sums, checked in a fraction of a second for no tokens. Rules are unit-tested, so a rule that
stops firing is caught; you cannot unit-test a prompt, and a silently broken rule manufactures false
confidence. And the agent that wrote a unit must not be the one certifying it — self-review is
systematically generous.

**Validation serves the teacher, it does not overrule them** (D-037). The teacher is the authority
and is responsible for what reaches students. Only *integrity* findings — references to things that
do not exist — are errors; everything pedagogical is advice, which a teacher may accept as a
deliberate exception (§8.4). What the framework enforces without exception is different in kind:
**never overwriting the teacher's work** (invariant 5) protects the teacher; it does not constrain
them.

**`validate` judges the course; `doctor` judges this machine** (D-040). What is committed is the
same on every clone, so `classkit validate` must give the teacher and a TA **the same answer** — it
reads only committed state (and what git tracks). What legitimately differs per machine — private
files present or not, a local full text present or stale, tools installed — is reported by
`classkit doctor`, which is read-only like `validate` and says, per line, what to run to fix it.

**Agents do what code cannot attempt:** is this guiding question a topic label in disguise? Would
this activity still work if nobody did the prework? Is eight minutes honest for eight pages of
proofs? This is why `course-critic` exists, and why it is explicitly told not to repeat the
validator.

### 2.3 Repository model

The framework and any teacher's course live in **separate repositories** (D-002, D-009). A course
repo is created by cloning the framework and repointing `origin`, keeping the framework as a second
remote:

```
BGU-CSE/class-framework  ──clone──▶  teacher/my-course
        ▲                                    │
        └────── git push HEAD:branch ────────┤  contribute an agent fix back
                git merge framework/main ────┘  pull framework improvements
```

Shared git history is the point: a GitHub template repo has no common ancestor, so every framework
update would have to be re-applied by hand, and a fork is limited to one per account, which breaks
on the second course.

**The framework repo contains no `course/` directory at all** (D-015). The course tree is created
entirely by `classkit scaffold`, which makes framework/course file-disjointness structural rather
than policed — and that disjointness is what keeps `git merge framework/main` clean. Framework-only
development files live under `dev/` (this spec, the vision, the roadmap, the build log) so they stay
out of a teacher's way (D-024).

Governance (D-014): the framework repo is permission-controlled; a teacher's course repo is
sovereign. *How updates should work after a teacher edits framework files is open (Q-007) — a
development-process question, out of scope for this specification.*

### 2.4 Authoring format

Markdown with YAML front matter for anything containing prose a teacher edits; plain YAML for
configuration (D-017). **Front matter is the machine-readable contract; the body below it is for
humans.** Field-level definitions are in §8.

### 2.5 Extension points

**Adding a methodology.** `question-driven-25` is one implementation of a contract, not the only
option (D-011). Drop a YAML file in `methodologies/`, name it in `course.yaml`, done. Its numbers are
read, never hardcoded. The contract is the study-session schema (§8.5). *This claim is untested —
see §9.*

**Adding a validation rule.** Add the check to `Validator`, give it a code, register its default
severity in `DEFAULT_SEVERITY` — **every** rule, errors included: the table is complete, reporting an
unregistered code raises, and it is how a mistyped rule name in `rules:` or `accepted:` is caught —
and add a test that breaks a scaffolded course and asserts the code fires **at that severity**. A
rule with no such test is worse than no rule. Only an integrity rule may default to `error` (§8.4).

**Adding an ingest format.** One extractor registered by file extension (§8.7) — the same anchors
every time, or locators rot.

**Adding an agent.** New file in `.claude/agents/`. If its craft overlaps an existing agent's, put
the craft in a skill and have both load it — otherwise the two drift and the teacher gets
contradictory advice.

---

## 3. The Core phase

### 3.1 What Core covers

Core is the basic framework: enough to take a conventional lecture course and produce the *learning
part* of a flipped one, end to end.

**In Core:** course initiation and configuration; the syllabus (course goal, Course Outcomes,
workload, prerequisites); units and their objectives; the at-home study sessions (guiding questions,
their answers, their study time, the session's study-path pool); the in-class hour and its
activities; and the **entry quiz** — its assessment items and their answer keys.

**Not in Core** (named in §1.1, specified in later phases): homework and programming assignments,
exams, grading weights, the Gem builder, PPTX export, metrics, and course lifecycle.

**Agents and commands active in Core.** Agents: `syllabus-designer` (the syllabus and its Course
Outcomes) **(target, D-029)**, `curriculum-architect` (the unit map and unit objectives),
`study-session-designer` (sessions, guiding questions, answers, `est_minutes`, the study-path pool),
`lesson-planner` (the in-class hour), `assessment-writer` (entry-quiz items only, in Core),
`topic-researcher` (finds real resources), `material-classifier` (classifies ingested materials,
reports coverage; read-only — it returns, the command records, §8.7), `course-critic` (review). Commands: `/ingest`,
`/plan-units`, `/design-unit N`, `/review-unit N`, and **`/write-items N` scoped to entry-quiz
items** — `/design-unit` already writes the unit's entry quiz, so `/write-items` in Core is for
adding to or reworking it. Deferred: `gem-builder` and `/build-gem` (Exports); the homework and exam
roles of `assessment-writer` and `/write-items` (Assessment).

**Tooling commands used across Core:** `classkit ingest` (the deterministic half of `/ingest`,
§8.7), `classkit add-url` (add a link to the course's materials, §8.7), `classkit material` (record
a batch of classifications, or one material's kind, units or title; optionally merge two materials,
§8.7), `classkit log` (append
to the course log, §8.8), and `classkit doctor` (check this machine's copy of the course, §8.7).

### 3.2 The shape of a flipped course

Under Core's default methodology, `question-driven-25`, a course is **12–13 Units**. One unit is one
week's subject and carries **150 minutes** of student time, split in two:

```
UNIT — one week's subject, 150 min
│
├── AT HOME — 100 min (2 × 50-min academic hours)
│   │   GOAL: ACQUISITION. The student meets the material and arrives at class
│   │   able to answer that week's guiding questions.
│   │
│   └── 4 × STUDY SESSION (~25 min each)
│       │   One sitting, self-contained.
│       │
│       ├── 3–5 GUIDING QUESTIONS
│       │     A question the student must be able to answer after the session.
│       │     Each carries an `answer` (where the correct answer is found) and an
│       │     `est_minutes` (how long studying it should take). The session's
│       │     25 minutes is the sum of those times.
│       │
│       └── STUDY PATHS (one pool per session)
│             Alternative resources — a video, a chapter, the class Gem.
│             Optional and non-exhaustive; the student may use their own instead.
│
└── IN CLASS — 50 min, one meeting per unit (the Lesson Plan)
    │   GOAL: APPLICATION. Build on what was studied at home — surface and repair
    │   misconceptions, work examples, practise, synthesise.
    │   Explicitly NOT re-explaining the prework.
    │
    └── 3–6 ACTIVITIES, opening with the ENTRY QUIZ
          The entry quiz is what makes the hour depend on the prework: it shows
          who studied and which misconceptions the next activity must address.
          Activities are built on the week's guiding questions.
```

Above the units sits the **Syllabus** — the course goal, its Course Outcomes, workload and
prerequisites — and each unit's objectives roll up to those outcomes (§4).

**The shape is Core; the numbers are the methodology's.** 150 / 100 / 50, four sessions of 25
minutes, 3–5 questions per session, an hour of 3–6 activities — every one of these is read from
`methodologies/question-driven-25.yaml`, never hardcoded (invariant 2, §8.5). A different methodology
supplies different numbers and the rest of the framework keeps working.

### 3.3 Why flipping fails, and Core's bet

A conventional course is three lecture hours a week for thirteen weeks. Flipping it moves acquisition
to independent home study and spends the contact hour on application. Two things reliably go wrong
when people do this:

1. **The class hour quietly becomes a lecture again.** The teacher re-explains the prework "so
   everyone is on the same page", and students learn that skipping it costs nothing.
2. **The home-study budget turns out to be fiction.** "Two hours" is really four, students stop
   doing it, and the contact hour collapses because it assumed they had.

Both are *structural* failures, not motivational ones. Core's bet is that both can be made
**mechanically visible** at design time, rather than discovered in week three.

*Visible*, not *fatal*: since D-037 both checks are advisory warnings the teacher may accept, because
the teacher is the authority. That is a real weakening of the original bet ("fail loudly"), accepted
knowingly. The residual risk is that a warning is seen and ignored; `alert`, counted exceptions and
the course log reduce that risk but do not remove it (§9).

### 3.4 Core's central mechanism: the Guiding Question

**The Guiding Question is the atomic addressable unit.**

A study goal is phrased as a question a student should be able to answer — *"Why is appending to a
dynamic array O(1) amortized when some appends cost O(n)?"* rather than *"Amortized analysis"*. It
has a stable ID (`U01-S02-G1`), and **everything else references it**: in-class activities, assessment
items, and later the class Gem.

That single choice (D-010, refining D-007) is what makes the two failure modes checkable:

- In-class activities are built on that unit's guiding questions, and the time an hour may spend on
  activities that reference none is capped → the hour cannot drift away from what the students
  studied (invariant 4, D-028).
- Each guiding question carries a teacher-approved study time (`est_minutes`) → the session's home
  budget is the *sum* of those times: arithmetic, not an assertion (D-020).

A guiding question carries, about itself: the `prompt` (the question), an `est_minutes` (the
teacher-approved approximate time to study it), and an `answer` — a set of *precise references to
where the correct answer lives* (a textbook subsection, a slide, a video timestamp), **never the
answer in prose** (that would put course content in the repo and invite fabrication). The answer is
the authoritative location of the correct answer: it grounds the assessment writer's correct-answer
key, the critic's check, and later the Gem's tutoring (D-019).

The one exception is a question deliberately left open: a goal may set `defer_to_class: true` and
carry no answer — a pre-class *thinking prompt* whose resolution is deferred to the in-class meeting
(D-023). The cost of that escape is structural: a deferred question must be picked up by ≥1 in-class
activity, so it consumes contact time rather than becoming a way to skip writing an answer. Most
study-session questions are answerable; deferral is the minority case.

**Study Paths are separate, and live on the Study Session, not the question** (D-020). They are an
*open, optional pool* of alternative resources for studying the session — a video, a chapter, the
class Gem — none mandatory, not exhaustive; a student may use their own (another AI, another video)
instead. They are teacher-facing for now, an inventory of what students can reach, and are **not**
time-summed: the 25-minute guarantee rides on the per-question `est_minutes`, not on the paths.

---

## 4. Core content model

```
Course = Syllabus + 12–13 Units                     course.yaml (config) · syllabus/syllabus.md
├── Syllabus — Bologna-style top layer              syllabus/syllabus.md
│     goal · Course Outcomes (CO1…) · workload/credits · assessment scheme (reserved) ·
│     prerequisites, level, teaching methods, reading. A complete Bologna
│     descriptor; unit contents are derived from the units below. (D-021, D-032)
└── each of 12–13 Units — one week's subject, 150 min   units/NN-slug/unit.md
    ├── Unit Objectives (2–4)                       U01-O1  → outcomes: [CO1…]
    │     each rolls up to ≥1 Course Outcome (D-021); teacher-facing, not the working layer.
    ├── HOME STUDY 100 min = 2 × 50
    │   └── 4 × Study Session (~25 min)             units/NN-slug/sessions/NN.md
    │       ├── 3–5 Guiding Questions               U01-S02-G1  ← the spine
    │       │     ├── est_minutes                   teacher-approved study time; the session
    │       │     │                                 budget is the sum of these (D-020)
    │       │     └── answer                        precise refs to where the answer is
    │       │           textbook|slide|video|article|web. Not prose. (D-019)
    │       │           — OR defer_to_class: true, no answer, resolved in class (D-023)
    │       └── Study Paths (per session)           an open, optional pool of alternative
    │             resources. Not enforced, not exhaustive, not time-summed. (D-020)
    └── IN-CLASS SESSION 50 min (= Lesson Plan)     units/NN-slug/in-class.md
        └── Activities                              U01-A1
              each references ≥1 Guiding Question of this unit.
              The entry quiz (activity of type `quiz`) uses Assessment Items.

Assessment Items                                    assessments/items/U01-I01.md
      each references ≥1 Guiding Question.
      CORE: entry-quiz items only. Homework/exam items are the Assessment phase.
```

**The Syllabus** (`syllabus/syllabus.md`) is the course-level top layer (D-021): a Bologna-style
document whose front matter carries the course goal, **Course Outcomes** (`CO1…`), workload/credits,
a reserved assessment block (grading details are the Assessment phase), and prerequisites, with a
prose body for the aim and narrative. It is authored and edited like any other file — scaffold writes
the skeleton once into the reserved `syllabus/` slot and never overwrites.

Course Outcomes are the **roof of the coverage chain**: every Unit Objective rolls up to ≥1 outcome,
and every outcome is covered by ≥1 objective, so *"do the units together deliver what the course
promised?"* becomes checkable at course scope. Identity fields (title, code, textbooks) stay in
`course.yaml` to avoid duplication, and the unit overview is derived from the `unit.md` files rather
than copied, so neither can drift. Producing a **rendered syllabus** — one human-readable document
(e.g. PDF) combining all three for students or an accreditation committee — is deferred to the
Exports phase (§1.1); the front matter is designed so that renderer has everything it needs. There is
no `course.md`.

**Vocabulary is fixed and synonym-free** (D-012). Two words are banned because each once meant two
things: **"topic"**, and bare **"question"** — say *Guiding Question* or *Assessment Item*. The full
glossary is in `CLAUDE.md`; the identifiers are in §8.1.

---

## 5. Core control flow

### 5.1 The design flow

Course-level setup runs once; then units are designed one at a time.

```
/ingest            (§8.7) 1. pre-flight scan: count files by format, slides/pages, exact copies,
                      links, unsupported files, a rough time estimate — then WAIT for approval
                   2. classkit ingest converts each new or changed source into
                      materials/ingested/M<NNNN>-slug.md with addressable anchors, and
                      updates materials/manifest.yaml (incremental, resumable)
                   3. material-classifier (read-only) returns each material's kind,
                      likely units and audience; the command shows the classification,
                      applies the teacher's corrections, and records it
                      (`classkit material apply`). No duplicate questions (D-040)
                   4. report what the course actually covers and where it is thin —
                      stating its scope (which units the materials reach, and "no material
                      yet" for the rest, never "thin"); after the teacher has read it,
                      written to materials/coverage.md (D-040)
                   Every approved step appends to course/LOG.md (§8.8).
/plan-units        ONE flow, two agents, sequential and file-based (D-029, D-031i):
                   1. syllabus-designer writes syllabus/syllabus.md — goal, Course
                      Outcomes (CO1…), workload, prerequisites, and the UNIT MAP (all
                      units: number, title, order) (target, D-040). Written to disk first.
                   2. curriculum-architect READS that syllabus and writes units/NN-slug/
                      unit.md for the units the teacher chooses to plan NOW — each
                      objective referencing the outcome ids it just read.
                   The handoff is the file, not shared memory: the architect must never
                   invent an outcome id, and either agent can be re-run alone.
/plan-units 4 5    (target, D-040) plan more units later, as their material arrives —
                   step 2 only, against the existing syllabus and map.

                   PARTIAL MATERIAL IS THE NORMAL CASE (D-040). The course level is
                   always whole — you cannot write outcomes for a third of a course — but
                   it needs EVIDENCE: something ingested that spans the course (an old
                   syllabus, a book's table of contents, a deck series), read through
                   materials/coverage.md and the materials themselves, plus the teacher.
                   With no such evidence the command asks the teacher; it does not draft
                   a course from memory as though it were fact. The unit level is
                   incremental: objectives come from that unit's own material (its
                   slides, the book's chapters read in depth), so units without material
                   stay on the map, unplanned, until it arrives. Completeness rules stay
                   skipped until every unit exists (§8.4).

/design-unit 3
   ├─ 1. read course.yaml → methodology name
   │     read methodologies/<name>.yaml → sessions/unit, session minutes, goals/session, in-class
   │     read syllabus, unit.md, earlier units, materials/source/
   │     (scaffold the unit first if it does not exist)
   ├─ 2. study-session-designer  ─── loads writing-guiding-questions, estimating-study-time
   │        writes sessions/01..NN.md (guiding questions, est_minutes, answers or defer_to_class,
   │        and the session's study-path pool)
   ├─ 3. assessment-writer  ─── loads writing-guiding-questions
   │        writes the ENTRY-QUIZ items in assessments/items/U03-I*.md (usage: in-class-quiz)
   ├─ 4. lesson-planner            ← runs after BOTH 2 and 3: it needs the guiding questions to
   │        writes in-class.md        build the hour around, and the real item ids to put in
   │                                  the quiz activity's `items` (D-031a)
   ├─ 5. classkit validate  → fix every error
   └─ 6. report to the teacher, including what was guessed

/review-unit 3     course-critic reviews what it did not write
```

Three orderings are load-bearing rather than stylistic:

- **`/plan-units` precedes `/design-unit`.** Session goals map to unit objectives, which map to
  Course Outcomes; the roof must exist first.
- **The lesson planner runs after the session designer *and* the assessment writer.** The hour is
  built from the week's guiding questions, so it cannot be planned before they exist; and its quiz
  activity lists real item ids in `items`, so those items must exist first. Planning the hour before
  the items forces the planner to invent ids for items nobody has written (D-031a).
- **Review is a separate command and a different agent.** `/review-unit 3` runs `course-critic`,
  which did not write the work it judges.

And one workflow rule: **design one unit at a time.** Agents infer the subject and level from what is
already in the repo, so a reviewed unit 1 improves unit 2, and an unreviewed bad one propagates.

### 5.2 How commands behave

The teacher is a participant in the command, not its audience at the end. Three rules bind **every**
command in every phase (D-030).

**1. Stepwise, with approval gates.** A command does not run start to finish and present a finished
result. For each step it: says what it is about to do → produces that step → shows the result →
**waits for approval or correction** before starting the next. `/design-unit 3` is therefore: study
sessions → *approve* → the in-class hour → *approve* → entry-quiz items → *approve* → validate and
report. A correction at a gate is applied before moving on, not deferred to the end.

Why: an agent that designs a whole unit before the teacher sees anything compounds a wrong
assumption across four sessions, an hour, and a quiz. Gates keep the blast radius one step wide.

**Where the gate lives.** A gate is *conversational* — the command states what it produced and waits
for the teacher's reply. It must therefore sit in the **orchestrating command, between agent
invocations**: a subagent cannot ask the teacher anything, so a gate placed inside an agent silently
does nothing. The command runs one agent, shows the result, waits, then runs the next (D-031h).

**2. Never overwrite without permission — and this is enforced in code, not by prompt.** Before
writing anything, a command checks whether the target already has content; if it does, it **stops and
asks**, showing what exists and what it proposes to replace.

This rule is **mechanically enforced**: `classkit` provides the write path agents use, and that path
*structurally refuses* to overwrite existing content without explicit confirmation — the same
guarantee `write_new()` already gives `scaffold`, generalized to every agent and command (D-031b).
The mechanism and its outcomes are specified in §8.6. A prompt instruction is not sufficient here. "Do not overwrite" is a negative constraint, and agents
violate those on long autonomous runs; the failure it guards against — **silent loss of a teacher's
authored work — is the one failure the framework must never have**, and it is unrecoverable. This is
the one place where the framework does not trust an agent to follow an instruction.

**3. Revision, not regeneration.** When output already exists, the default mode is **update**: change
what the teacher asked to change, leave everything else intact, and report what changed. Regenerating
from scratch is an explicit choice, never the default. This is what makes partial edits possible —
revising one Course Outcome without rewriting the syllabus, or re-doing session 3 without touching
sessions 1, 2 and 4 — and it is how a course is maintained year to year.

---

## 6. Core data flow

| Artifact | Written by | Consumed by | Phase |
|---|---|---|---|
| `course.yaml` | teacher | every agent, all tooling | Core |
| `syllabus/syllabus.md` | syllabus-designer | validator, critic | Core (the rendered syllabus export is Exports) |
| `methodologies/*.yaml` | framework (or a teacher adding one) | designer, planner, validator | Core |
| `defaults/time-constants.yaml` | framework, overridable per course | designer, critic (advisory) | Core |
| `materials/source/*` | teacher (and `classkit add-url` → `links.md`) | `/ingest` only | Core |
| `materials/manifest.yaml` | `classkit ingest` (+ `classkit material`, run by `/ingest` and the teacher — never by an agent) | every agent that cites material, validator | Core |
| `materials/ingested/*.md` | `classkit ingest`; the teacher may hand-edit | curriculum-architect, designer, assessment-writer, critic | Core |
| `materials/private-text/*.md` | `classkit ingest`, on a machine that has the private source; gitignored; the teacher may hand-edit | the same agents, when present here; `classkit doctor` | Core (D-040) |
| `.gitignore` (course) | `classkit scaffold course` (create-only); the teacher may extend | git; `classkit doctor` | Core (D-040) |
| `LOG.md` | `classkit log`, called by every command at each approved step | every agent (recent entries), the teacher | Core |
| `unit.md` | curriculum-architect | designer, validator | Core |
| `sessions/NN.md` | study-session-designer | planner, assessment-writer, validator | Core |
| `in-class.md` | lesson-planner | critic, validator | Core |
| `assessments/items/*.md` | assessment-writer | validator, (later) exporters | Core (entry quiz); Assessment (rest) |
| `exports/gems/**` | gem-builder | students, via Gemini | Exports (deferred); never bundles instructor-only or private material (D-040) |

Nothing downstream reads a methodology's *identity* — only the `goals[]` a session declares (§8.5).

---

## 7. Invariants

Enforced by tests, schemas, or review. `CLAUDE.md` states them for agents working on the framework;
they are repeated here with their reasons.

1. **No course content in the framework repo.** Tests build a throwaway course in `tmp_path`.
2. **Nothing hardcodes methodology numbers.** They are read from `methodologies/*.yaml` (§8.5).
3. **Downstream consumes `goals[]`, never the methodology.** The alternative makes D-011 a lie.
4. **The class hour is built on the home study.** Activities reference that unit's guiding questions.
   An activity referencing none is permitted but flagged, and the **total unmapped time in an hour is
   capped** (§8.4) — the cap is what stops the hour drifting back into a lecture. Legitimate
   exceptions exist (exam logistics, a current-events hook); an hour made of them does not. **An agent never raises the cap, or accepts an exception, on its own**; the teacher may (D-028, D-037).
5. **Nothing overwrites a teacher's work without permission — enforced in code.** Scaffolding is
   create-only (`write_new()` is its only path to disk), and every agent and command writes through a
   `classkit` path that structurally refuses to overwrite existing content without explicit
   confirmation (§5.2, D-030, D-031b). Not a prompt instruction: this failure is unrecoverable.
   **Scope (D-040):** the framework's own commands and agents. An edit the teacher asks for directly
   in conversation is the teacher's edit, made with a tool (Claude Code shows the diff and, per its
   permission mode, asks). The guarantee is the write path's, not a sandbox around everything an AI
   tool can do.
6. **Templates must validate.** A fresh scaffold produces zero errors, or the tests fail.
7. **Agents must not fabricate resources.** A made-up URL or page number validates cleanly and fails a
   student mid-session. Applies to `answer` locators and study paths alike.

---

## 8. Core specification reference (normative)

Everything below is what an implementation must produce for Core. Front-matter keys are YAML.
"Req" = required. Rows tagged **(target)** are not yet in `schemas/` — see the ledger (§1.2).

### 8.1 ID conventions

Mechanically checked. `NN` is two digits; `N` is one or more.

| ID | Meaning | Example |
|---|---|---|
| `CO<N>` | Course Outcome (in the syllabus) | `CO1` |
| `U<NN>` | Unit | `U01` |
| `U<NN>-O<N>` | Unit Objective | `U01-O1` |
| `U<NN>-S<NN>` | Study Session | `U01-S02` |
| `U<NN>-S<NN>-G<N>` | Guiding Question — the addressable spine | `U01-S02-G1` |
| `U<NN>-IC` | In-Class Session (one per unit) | `U01-IC` |
| `U<NN>-A<N>` | Activity | `U01-A1` |
| `U<NN>-I<NN>` | Assessment Item | `U01-I01` |
| `M<NNNN>` | Material — one ingested source (a file or a link) (D-035) | `M0007` |
| `M<NNNN>#<anchor>` | A locator inside a material: `slide-N`, `page-N`, or a heading slug | `M0007#slide-18` |

`M` is used rather than `S` because `S` already means Study Session.

### 8.2 Artifact field specifications

Every artifact below that has front matter — syllabus, unit, study session, in-class session,
assessment item — also takes an optional `accepted: [{rule, reason}]` list: the teacher's deliberate
exceptions to validation rules for that file (§8.4). It is not repeated in each table.

#### File and directory naming

| Path | Rule |
|---|---|
| `units/NN-slug/` | `NN` = the unit number, zero-padded to two digits. `slug` = the unit title lowercased, every run of non-alphanumeric characters replaced by `-`, leading/trailing `-` stripped; empty result becomes `untitled`. E.g. unit 3 "Asymptotic Analysis" → `03-asymptotic-analysis`. The directory is located by its `NN-` prefix, so the slug may be renamed by hand without breaking anything (D-031f). |
| `units/NN-slug/sessions/NN.md` | `NN` = the session number within the unit, zero-padded to two digits |
| `units/NN-slug/in-class.md` | fixed name, one per unit |
| `syllabus/syllabus.md` | fixed name, one per course |
| `assessments/items/UNN-INN.md` | the item's id |
| `materials/source/**` | anything, any structure — the teacher's; never modified by agents (§8.7) |
| `materials/source/links.md` | fixed name; the course's list of links (§8.7) |
| `materials/ingested/MNNNN-slug.md` | the material's id plus a slug of its title; flat, one per material (for a private material: its index) |
| `materials/source/private/**` | the teacher's files that must not be committed; gitignored (§8.7) |
| `materials/private-text/MNNNN-slug.md` | a private material's full text; the same name as its index; gitignored (§8.7) |
| `.gitignore` | fixed name, at the course root; scaffolded (§8.7) |
| `materials/manifest.yaml` | fixed name, one per course |
| `LOG.md` | fixed name, one per course, at the course root (§8.8) |

#### `course.yaml` — course configuration (plain YAML, no body)

| Field | Type | Req | Notes |
|---|---|---|---|
| `code` | string | ✓ | institutional course code, e.g. `"202-1-2051"` |
| `title` | string | ✓ | |
| `institution` | string | ✓ | |
| `instructors` | array\<string\> | | |
| `language` | string | ✓ | BCP-47; English only for now (D-001); default `en` |
| `methodology` | string | ✓ | filename stem under `methodologies/`; default `question-driven-25` |
| `units` | integer 1–20 | ✓ | number of units (weeks); typically 12–13 |
| `textbooks` | array\<obj\> | | each `{ key (✓), citation (✓), url }`; `key` is referenced by study paths and answers |
| `time_constants` | object | | per-course overrides of `defaults/time-constants.yaml` (any subset) |
| `in_class` | object | | **(target, D-031e)** per-course overrides of the methodology's in-class settings. Currently one key: `max_unmapped_minutes` (integer ≥0) — the cap on in-class time spent on activities that reference no guiding question. Overrides the methodology default (10). Setting it to the full hour length disables the guardrail, which is the teacher's right (D-014) |
| `agents` | object | | course-local agent-role → replacement name (Q-007) |
| `rules` | object | | (D-037) rule-code → `error \| alert \| warn \| off`. The teacher's course-wide override of any validation rule; wins over the methodology (§8.4). A bare `off` is read as the severity, although YAML 1.1 parses it as boolean false |

Deferred: a `gem` block (Exports phase).

#### `syllabus/syllabus.md` — the top layer (D-021)

| Field | Type | Req | Notes |
|---|---|---|---|
| `goal` | string | ✓ | one-paragraph aim of the course |
| `outcomes` | array\<obj\> | ✓ (≥1) | each `{ id (`CO<N>`, ✓), statement (✓), bloom (enum, opt) }` — the coverage roof |
| `workload` | object | | `{ credits (✓), credit_system (✓; string — ECTS is one instantiation, never hardcoded), total_hours (number, opt) }`. Optional so a teacher can draft and validate a syllabus before credits are settled; `syllabus_workload_missing` warns while it is absent (D-031d) |
| `prerequisites` | array\<string\> | | course-level prerequisites (free text or course codes) |
| `assessment` | array\<obj\> | | **reserved** grading scheme, e.g. `{ type, weight }` — specified in the Assessment phase; may be empty in Core. Its item shape is **deliberately left open** (`additionalProperties` *not* false), unlike every other object in `schemas/`: closing a shape we have not designed would invalidate a course that fills the block early. Do not "fix" this before the Assessment phase specifies it (G-11) |
| `level` | string | | **(target, D-032)** e.g. `undergraduate`, `graduate`. Free string, not an enum — degree structures differ by institution |
| `course_type` | string | | **(target, D-032)** e.g. `compulsory`, `elective`, `elective in track X` |
| `offered` | object | | **(target, D-032)** `{ year_of_study (number/string), semester (string) }` — when in the programme the course sits |
| `teaching_methods` | array\<string\> | | **(target, D-032)** how the course is taught, e.g. `flipped classroom`, `weekly in-class problem solving`. Bologna expects this, and for a flipped course it is the descriptor that actually distinguishes it |
| `reading` | object | | **(target, D-032)** `{ required: [string], recommended: [string] }`. Entries may be a `textbooks[].key` from `course.yaml` (preferred — no duplication) or free-text for anything not listed there |
| `unit_map` | array\<obj\> | | **(target, D-040, step 3)** the whole semester's plan, written before most units exist: each `{ number (✓), title (✓), summary (opt), evidence (opt, array of material locators — what the plan for this unit rests on) }`. **Authoritative for which units the course has and their order and titles.** A `units/NN-slug/` directory is created only when a unit is *planned* in detail (§5.1); `unit_map_mismatch` warns when a unit's `unit.md` disagrees with its map entry |

`bloom` enum, everywhere it appears: `remember | understand | apply | analyze | evaluate | create`.

**Completeness (D-032).** The syllabus front matter is intended to carry **everything a Bologna-style
course descriptor needs**, so that a teacher never has to keep syllabus information somewhere else.
Only `goal` and `outcomes` are required; everything else may be filled in stages, or deliberately
skipped. Two categories are deliberately *not* fields here:

- **Identity and configuration** — title, code, institution, instructors, language, textbook list —
  live in `course.yaml`, the single source of truth. Repeating them here would create drift.
- **The units' detail** — objectives, sessions, the in-class hour — lives in the `unit.md` files and
  below them. The **unit map** (which units, in what order, their titles) is authored here instead
  (D-040): it is decided before most units exist, so it cannot be derived from them.

Both are pulled in when the syllabus is rendered for people to read (deferred — see §1.1). The rule:
**authored content is a field here; derived content is assembled at render time.**

Body: prose aim and narrative. Identity fields (title, code, textbooks) are **not** repeated here —
they live in `course.yaml`. A future rendered syllabus (Exports) pulls them in, along with a unit
overview assembled from the unit map and, where they exist, the units.

#### `units/NN-slug/unit.md` — a unit

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `U<NN>` | ✓ | |
| `number` | integer 1–20 | ✓ | |
| `title` | string | ✓ | the week's subject |
| `summary` | string | | |
| `prerequisites` | array\<`U<NN>`\> | | units that must precede this one |
| `objectives` | array\<obj\> | ✓ (≥1) | see below. **Kept as shape, deliberately** (D-038): a unit with no objectives has nothing for guiding questions to roll up to, so the coverage chain cannot even be expressed for it — unlike an absent `outcomes` list, which is merely unfinished |

Objective object:

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `U<NN>-O<N>` | ✓ | |
| `statement` | string | ✓ | |
| `bloom` | enum | | optional Bloom level |
| `outcomes` | array\<`CO<N>`\> | | (D-021) Course Outcomes this objective rolls up to. **Not schema-required** (D-037): naming none is advisory (`objective_maps_to_outcome`, **target**); naming one the syllabus does not declare is an integrity error (`outcome_reference`) |

#### `units/NN-slug/sessions/NN.md` — a study session

This is **the methodology contract** (§8.5): downstream consumes `goals[]`, never the methodology.

Session front matter:

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `U<NN>-S<NN>` | ✓ | |
| `unit` | `U<NN>` | ✓ | must match the containing unit |
| `number` | integer ≥1 | ✓ | position in the unit; `id` must equal `unit + S{number:02d}` |
| `title` | string | ✓ | |
| `duration_minutes` | integer ≥1 | ✓ | the session's time budget (≈ methodology `session_minutes`) |
| `goals` | array\<obj\> | ✓ | count within methodology `goals_per_session` (3–5 for question-driven-25) |
| `paths` | array\<obj\> | | **(target, session-level; D-020)** open optional resource pool; each `{ kind (enum), ref (string), note (opt) }`; `kind` from **the resource-kind vocabulary** (below, D-040) — **optional when `ref` is a material locator**, whose kind the manifest already records; required otherwise; **not** time-summed |

Goal object (the Guiding Question):

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `U<NN>-S<NN>-G<N>` | ✓ | must be prefixed by its session id |
| `type` | enum | ✓ | `question \| task \| reading \| exercise`; question-driven-25 allows only `question` |
| `prompt` | string | ✓ | the guiding question, phrased so a student can answer and check it |
| `objectives` | array\<`U<NN>-O<N>`\> | ✓ (≥1) | unit objectives this goal rolls up to |
| `est_minutes` | number ≥0 | | **(target, D-020, D-038)** teacher-approved study time; the session budget sums these. **Not schema-required** — a missing estimate is pedagogy (the teacher has not estimated yet), not shape: the budget rule reports the session as *unverifiable* (warn) instead |
| `answer` | array\<obj\> | advisory: ≥1 **unless** `defer_to_class` — not schema-required (D-037) | **(target, D-019)** precise locators of the correct answer; each `{ kind (enum), ref (string), note (opt) }`; `kind` from **the resource-kind vocabulary** (below, D-040), optional when `ref` is a material locator; never the answer in prose. **Prefer a material locator** — `ref: "M0007#slide-18"` — which the validator can check (D-035); a textbook key with a locator (`"CLRS §2.3.1"`) remains allowed for sources that are cited but not ingested. **A book citation carries the book's own coordinates in `note`** — section, exercise or question number where there is one, and the printed page — because `page-N` is the physical page (§8.7, D-039): `ref: "M0003#page-63"`, `note: "CLRS §6.2, Exercise 6.2-3 (printed p. 45)"`. Applies to study paths too |
| `defer_to_class` | boolean | | **(target, D-023)** default `false`. If `true`: no `answer`; a pre-class thinking prompt that **must** be referenced by ≥1 in-class activity |

> **The resource-kind vocabulary (D-040).** One list for a material's `kind`, a study path's `kind`
> and an `answer` locator's `kind`: `slides | textbook | notes | exam | exercise | syllabus | reading |
> link | video | other`, plus `gem` and `web` for paths and answers. Before D-040 there were three
> overlapping lists (`slide` vs `slides`; a teacher's own deck could only be `other`). Where `ref` is
> a material locator (`M0006#slide-2`), `kind` may be omitted — the manifest knows it, and a second
> copy could only repeat or contradict it. *Today's per-goal path kinds are `gem | video | textbook |
> slides | notes | article | exercise | other` (`slides` and `notes` added in step 2c-2); the full
> vocabulary, and `kind` optional for a locator, land with D-019/D-020 in step 4.*

> A goal's `answer` is a **list of locators** — where the answer can be found. It is not the answer
> itself. The assessment item's model answer is a separate field named `model_answer` (D-031g), so the
> two never collide.

#### `units/NN-slug/in-class.md` — the in-class session (Lesson Plan)

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `U<NN>-IC` | ✓ | |
| `unit` | `U<NN>` | ✓ | |
| `title` | string | | |
| `duration_minutes` | integer ≥1 | ✓ | must equal methodology `in_class.minutes`; activities sum to it within tolerance |
| `activities` | array\<obj\> | ✓ (≥1) | count within methodology `in_class.activities` |

Activity object:

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `U<NN>-A<N>` | ✓ | prefixed by its unit id |
| `type` | enum | ✓ | from methodology `allowed_activity_types`, e.g. `quiz \| discussion \| critical-thinking \| worked-example \| group-work \| synthesis` |
| `title` | string | | |
| `duration_minutes` | integer ≥1 | ✓ | |
| `guiding_questions` | array\<`U<NN>-S<NN>-G<N>`\> | | not required by the schema (D-028, D-037) — the guiding questions of *this unit* the activity builds on. Normally non-empty; an activity with none is flagged, and unmapped time is capped (§8.4) |
| `reason` | string | | **(target, D-028)** why this activity references no guiding question, e.g. `"exam logistics"`, `"current-events hook"`. Only meaningful when `guiding_questions` is absent or empty; the critic judges whether it is legitimate |
| `items` | array\<`U<NN>-I<NN>`\> | | assessment items used (typically the entry quiz). Every id **must resolve to an existing item of this unit** — checked by `activity_item_reference` (D-031a) |
| `grouping` | enum | | `individual \| pairs \| small-group \| plenary` |
| `materials` | array\<string\> | | |
| `notes` | string | | |

#### `assessments/items/UNN-INN.md` — assessment item (Core: entry-quiz items only)

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `U<NN>-I<NN>` | ✓ | |
| `unit` | `U<NN>` | ✓ | |
| `format` | enum | ✓ | `multiple-choice \| multiple-select \| open \| numeric \| true-false \| code` |
| `guiding_questions` | array\<`U<NN>-S<NN>-G<N>`\> | ✓ (≥1) | what the item tests |
| `usage` | array\<enum\> | | `in-class-quiz \| homework \| exam \| self-check \| gem-practice`; **Core writes `in-class-quiz`** |
| `difficulty` | enum | | `easy \| medium \| hard` |
| `bloom` | enum | | |
| `est_minutes` | number ≥0 | | time to *answer* the item (distinct from a goal's study time) |
| `stem` | string | ✓ | the question as presented to the student |
| `choices` | array\<obj\> | ✓ for `multiple-choice`/`multiple-select` | each `{ label (`^[A-Za-z]$`), text, correct (bool), rationale }`; every distractor's `rationale` names the misconception it detects |
| `model_answer` | string | | **(target: renamed from `answer`; D-031g)** the model answer, for `open`/`numeric`/`code`. Renamed because a guiding question's `answer` is a *list of locators* and an item's was a *string* — one key, two meanings |
| `rubric` | array\<obj\> | | each `{ criterion, points, notes }`. **(target, D-038)** Presence is pedagogy, not shape: an `open` item without a rubric is readable, so the schema's current `required` for `open` moves to an advisory rule in step 5. (`choices` stays required for choice formats — an item without choices cannot be read) |

#### `methodologies/*.yaml` — the methodology definition

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | string `^[a-z0-9][a-z0-9-]*$` | ✓ | |
| `name` | string | ✓ | |
| `summary` | string | | |
| `designer_agent` | string | | the agent implementing this methodology's session design |
| `unit` | object | ✓ | `{ total_minutes (✓), objectives: {min,max} (✓) }` |
| `home_study` | object | ✓ | `{ total_minutes, sessions_per_unit, session_minutes, goals_per_session: {min,max}, default_goal_type?, allowed_goal_types?, budget_tolerance_minutes? }` **(target: `budget_tolerance_minutes`; D-020)** |
| `in_class` | object | ✓ | `{ scope (unit\|session), minutes, activities: {min,max}?, duration_tolerance_minutes? (default 5), require_opening_quiz? (default false), max_unmapped_minutes? (default 10), allowed_activity_types }` **(target: `max_unmapped_minutes`; D-028, default lowered by D-031e)**. `max_unmapped_minutes` is overridable per course in `course.yaml` |
| `study_paths` | object | | `{ allowed_kinds?, min_paths_per_session? }` **(target: renamed from `min_paths_per_goal`; D-020)** |
| `rules` | object | | rule-code → `error \| alert \| warn \| off`; overrides the defaults in §8.4 for courses using this methodology. A course's own `course.yaml` `rules:` overrides it in turn |

`question-driven-25` values: `unit.total_minutes 150`, `objectives 2–4`; `home_study.total_minutes
100`, `sessions_per_unit 4`, `session_minutes 25`, `goals_per_session 3–5`, `allowed_goal_types
[question]`; `in_class.scope unit`, `minutes 50`, `activities 3–6`, `require_opening_quiz true`.

### 8.3 Time and feasibility model

- **Session budget — the "25 minutes is real" guarantee.** For each session:
  `sum(goal.est_minutes) + session_overhead_minutes ≤ budget`, where `budget = duration_minutes`
  (falling back to methodology `session_minutes`), checked within
  `home_study.budget_tolerance_minutes`. `session_overhead_minutes` comes from the time constants.
  Deferred (`defer_to_class`) goals still contribute their `est_minutes` — thinking time counts.
- **`est_minutes` is teacher-approved, and its honesty is a human-judgment step.** Code checks the
  sum only. `study-session-designer` *proposes* an `est_minutes`, and `course-critic`
  *sanity-checks* it, both using `defaults/time-constants.yaml` as an **advisory yardstick** — never
  a validator input (D-025). Those constants are placeholders (Q-005); advisory means a bad constant
  misguides rather than fails a build.
- **Study paths are not time-summed** (D-020). A path may carry a rough time to help a student
  choose, but nothing depends on it.

### 8.4 Validation rules

**The teacher is the authority** (D-037). The validator exists to catch what *agents* get wrong and to
*inform* the teacher — never to overrule a teacher's deliberate choice. It reports; it does not
gatekeep. So every rule is one of two kinds:

- **Integrity** — the course is broken *as data*: something is referenced that does not exist, or a
  file cannot be read. Almost never intentional, and agents and tools cannot reason correctly over
  it. Severity **`error`**.
- **Advisory** — something is missing, or departs from the methodology's good practice. A teacher may
  have good reasons for any of these (a holiday week with no class hour, a deliberately long
  session). Severity **`warn`**, or **`alert`** for the checks that matter most.

The dividing line is mechanical: **a finding that names something that does not exist is integrity;
a finding that something is absent or unconventional is advisory.** So one concern can yield both —
an objective naming `CO9` when there is no `CO9` is an integrity error; an objective naming no outcome
at all is an advisory alert.

#### Severities

| Severity | Meaning | `classkit validate` |
|---|---|---|
| `error` | integrity — broken data | reported; exit code 1 |
| `alert` | **high-priority advisory** — look at this soon | reported **first**, marked `ALERT`; does not fail |
| `warn` | advisory | reported; does not fail |
| `off` | not checked | — |

`--strict` counts alerts and warnings as failures too, for a teacher who wants that.

#### Overrides — who has the last word

1. A **methodology's** `rules:` block sets defaults for courses that use it.
2. The course's **`course.yaml` `rules:`** block overrides the methodology — the teacher's last word,
   for any rule. (Switching an *integrity* rule off is allowed, but tools may then misbehave over the
   broken references it would have caught.)
3. **Per instance, a teacher accepts an exception** in the artifact's own front matter:

   ```yaml
   accepted:
     - rule: in_class_missing
       reason: "holiday week — no class meeting"
   ```

   That rule's findings for that file are then suppressed, so a known exception stops nagging — a
   warning that always fires trains the teacher to ignore every warning. `validate` still prints a
   one-line count of accepted exceptions, so they are never invisible — how many findings they
   suppressed, and how many entries no longer match anything. Each acceptance **an agent adds, at
   the teacher's request,** is recorded in the course log (§8.8); `validate` itself is read-only and
   never writes to the log, and a teacher editing by hand may log it or not (D-038).
   `accepted:` is a field on every artifact that has front matter (syllabus, unit, session,
   in-class session, item). **Only `rule` is required** — an entry with no rule cannot be read.
   **`reason` is optional**: a missing or blank reason is reported by the advisory rule
   `accepted_without_reason`, never as a schema error. Likewise `rule` is **not pattern-checked**:
   any mistyped code, whatever its case, is reported by `unknown_rule`. Both follow the same
   principle — a mistake in the teacher's *own exception* is advice, not a failure (D-038).
   Findings about a unit as a whole — `session_count`, `in_class_missing`, `objective_coverage` —
   are reported against its `unit.md`, so that is where they are accepted. Findings reported
   against `course.yaml` (which has no front matter) are adjusted course-wide with `rules:`.

**Agents fix what they caused, and never overrule the teacher.** An agent must fix or surface any
finding its own output produced, and may **never** add an `accepted:` entry, change `rules:`, or
raise a threshold on its own — only on the teacher's explicit instruction, which is then logged. And
an agent never "corrects" something the teacher decided: a teacher's exception or a teacher-made
inconsistency is reported and left alone unless the teacher asks.

**Schemas check shape, not pedagogy.** JSON Schema enforces what tools need to *read* a file — ids,
types, allowed keys. Whether a guiding question *has* an answer, or an objective *has* an outcome, is
advisory, so it is expressed as a rule below, not as a schema `required` — otherwise the schema layer
would turn advice back into errors.

#### The rules

Severity is the default; **(target)** means not built yet. Every rule is also a *consistency* or
*completeness* rule (see below).

| Code | Checks | Kind | Default |
|---|---|---|---|
| `schema` | front matter parses and has the shape tools need (ids, types, allowed keys) | integrity | error |
| `schema_unavailable` | `jsonschema` not installed → schema layer skipped | — | warn |
| `id_consistency` | every id matches its unit/number/session/prefix rules | integrity | error |
| `goal_maps_to_objective` | each objective a goal names is defined by its unit | integrity | error |
| `outcome_reference` | each outcome an objective names exists in the syllabus (D-037) | integrity | error |
| `activity_references_guiding_question` | a guiding question an activity names exists somewhere in the course | integrity | error |
| `activity_item_reference` | every id in an activity's `items` resolves to an existing item | integrity | error **(target, D-031a)** |
| `item_reference` | an item's `unit` and `guiding_questions` exist | integrity | error |
| `material_locator_resolves` | every `M<NNNN>` / `M<NNNN>#anchor` locator names a real material and anchor (D-035; which fields are read: §8.7) | integrity | error |
| `outcome_coverage` | every Course Outcome is covered by ≥1 unit objective. Completeness rule | advisory | **alert** **(target, D-021/D-033/D-037)** |
| `objective_coverage` | every unit objective is addressed by ≥1 guiding question | advisory | **alert** |
| `objective_maps_to_outcome` | every unit objective names ≥1 Course Outcome | advisory | **alert** **(target, D-021/D-037)** |
| `syllabus_missing` | the course has no `syllabus/syllabus.md` | advisory | **alert** **(target, D-033/D-037)** |
| `unit_count` | units on disk vs `course.yaml` `units` | advisory | warn |
| `unit_map_mismatch` | the syllabus `unit_map` and the units disagree: a unit directory whose number is not on the map or whose title differs from its entry, or a map whose length differs from `course.yaml` `units`. Consistency rule | advisory | warn **(target, D-040, step 3)** |
| `session_count` | sessions per unit == methodology `sessions_per_unit` | advisory | warn |
| `goal_count` | goals per session within `goals_per_session` | advisory | warn |
| `goal_type` | `goal.type ∈ allowed_goal_types` | advisory | warn |
| `answer_reference_present` | each goal has ≥1 `answer` unless `defer_to_class` | advisory | warn **(target, D-019/D-023/D-037)** |
| `deferred_question_resolved_in_class` | each `defer_to_class` goal is referenced by ≥1 activity | advisory | warn **(target, D-023/D-037)** |
| `session_budget_feasibility` | `sum(est_minutes) + overhead ≤ budget`, within tolerance | advisory | warn **(target, D-020/D-037)** |
| `min_paths_per_session` | session has ≥ `study_paths.min_paths_per_session` paths | advisory | warn **(target, D-020)** |
| `in_class_missing` | unit has an `in-class.md` | advisory | warn |
| `in_class_duration_match` | declared == methodology `minutes`, activities sum to it within tolerance | advisory | warn |
| `activity_count` | activities within `in_class.activities` | advisory | warn |
| `activity_type` | `activity.type ∈ allowed_activity_types` | advisory | warn |
| `require_opening_quiz` | if set, the first activity is a `quiz` | advisory | warn |
| `activity_without_guiding_question` | an activity names ≥1 guiding question (split from `activity_references_guiding_question`, D-028/D-037) | advisory | warn |
| `activity_references_other_unit` | a guiding question an activity names belongs to *this* unit, not another (split, D-037; the case Q-029's homework-checking quiz needs) | advisory | warn |
| `in_class_unmapped_time_cap` | total time of activities referencing no guiding question ≤ `max_unmapped_minutes` | advisory | warn **(target, D-028/D-031e/D-037)** |
| `item_no_correct_choice` | a choice-format item has ≥1 choice marked `correct` (split from `item_reference`, D-037) | advisory | warn |
| `syllabus_workload_missing` | the syllabus declares no `workload` | advisory | warn |
| `unknown_rule` | a rule code in `course.yaml` `rules:`, a methodology's `rules:`, or an `accepted:` entry names no rule — a typo that would otherwise silently do nothing | advisory | warn |
| `accepted_without_reason` | an `accepted:` entry gives no `reason` (or a blank one). The exception still takes effect (D-038) | advisory | warn |
| `material_locator_in_text` | a `M<NNNN>#anchor` in the Markdown body of a course file (not `LOG.md`, not `ingested/`) names a real material and anchor (§8.7). Consistency rule | integrity, reported as advisory (prose) | warn |
| `materials_not_ingested` | a source (file or `links.md` line) is new, changed, moved or gone since the last ingest — one finding, reported against `materials/manifest.yaml` (D-035). **Ignores `source/private/`** (D-040): its files are not looked at and private materials are not judged — what is there differs per machine, and `classkit doctor` reports it. For a material whose hand-edit refusal awaits the teacher, the message says so and names `classkit ingest --keep ID` / `--overwrite ID`, not "run /ingest" (F-25): its source changed and its ingested file differs from `ingested_hash` | advisory | warn |
| `course_gitignore_missing` | `course/.gitignore` is absent or does not list `materials/source/private/` and `materials/private-text/` (§8.7). Reported against `course/.gitignore`. Consistency rule | advisory | warn |
| `instructor_material_cited` | a student-facing locator (today a study path's `ref`; step 4 adds `answer`, D-019) names a material with `audience: instructor` (D-040). Consistency rule | advisory | **alert** |
| `private_material_committed` | git tracks a file under `materials/source/private/` or `materials/private-text/` (any case) — it is in the repo's history; removing it from history is the teacher's decision. One finding, reported against `materials/manifest.yaml`; skipped silently outside git (D-040). Consistency rule | advisory | warn |
| `unit_has_entry_quiz_items` | the unit has ≥1 item with `usage: in-class-quiz` | advisory | warn **(target, D-031c)** |
| `guiding_question_assessed` | every guiding question is tested by ≥1 assessment item | advisory | **off in Core**; warn from the Assessment phase **(D-031c)** |

Retired by D-020: `path_estimate_missing`, and the per-path `_estimate_path` helper.

**Which course state a rule applies to (D-033).** A course spends almost all of its life *half
built* — steps 1–6 of the implementation plan, and a teacher's whole authoring semester, happen in
that state, and invariant 6 requires a freshly scaffolded course to validate clean. Every rule must
therefore say which state it judges. There are two kinds:

- **Consistency rules — always active, at every state.** They ask whether what *is* present holds
  together: schema conformance, id consistency, dangling references (`goal_maps_to_objective`,
  `objective_maps_to_outcome`, `activity_references_guiding_question`, `item_reference`,
  `activity_item_reference`, `answer_reference_present`, `deferred_question_resolved_in_class`),
  duration sums, and counts against methodology ranges. A course half-written can still be
  internally consistent, so these fire from the first unit onwards.
- **Completeness rules — active only once the course is complete.** They ask whether *everything
  promised* has been delivered, which is unanswerable while material is still being written.
  `outcome_coverage` is the case in point: read against a 3-of-13-unit course, every not-yet-covered
  outcome is an error, so the rule would fail every scaffolded course (breaking invariant 6) and
  shout through an entire authoring semester until the teacher switched it off.

**The course is complete when the number of units on disk equals `course.yaml`'s `units`** — the
condition `unit_count` already computes. While it is incomplete, a completeness rule does not fire,
and `classkit validate` **reports that it was skipped and why** ("outcome_coverage: skipped — course
incomplete, 3 of 13 units"), so a skipped check is visible rather than silent.

Note the asymmetry this produces in the coverage chain, which is deliberate: **objective → outcome is
a consistency rule** (an objective that rolls up to nothing is wrong the moment it is written, and is
caught immediately), while **outcome → objective is a completeness rule** (an outcome nothing covers
yet is simply unfinished work). The chain is checked in both directions, but the two directions
become meaningful at different times.

**Why `syllabus_missing` is a high-priority alert (D-033, softened from error by D-037).** `scaffold course` always creates the
syllabus, so it can only be absent if it was deleted. Worse, a course with no syllabus has **no
Course Outcomes**, which makes `outcome_coverage` *vacuously true* — the rule that closes the
coverage chain would pass most confidently exactly when the roof is gone. An alert is the honest
severity: the teacher may be mid-rewrite, but a silently-empty guarantee must not go unnoticed.

**Why `guiding_question_assessed` is off in Core (D-031c).** In Core the only assessment items are
entry-quiz items, and a short entry quiz cannot test all ~15–20 of a unit's guiding questions. The
rule would therefore fire on every valid unit, and a warning that always fires teaches the teacher to
ignore all warnings. It is switched off in `question-driven-25`'s `rules:` block and turns on in the
Assessment phase, when homework and exams make full coverage a reasonable expectation.
`unit_has_entry_quiz_items` is the Core-appropriate replacement: it checks the quiz exists at all,
not that it covers everything.

### 8.5 The methodology contract

The **study-session schema (§8.2) is the contract** between a methodology and the rest of the
framework. A methodology sets the numbers and the vocabulary of `goal.type`; downstream reads only
the produced `goals[]` and the session structure — never the methodology's identity (invariant 3).

- **Read from the methodology:** sessions per unit, session length and budget tolerance, goals per
  session, allowed goal types, unit total minutes and objective range, the in-class
  scope/minutes/activity range/allowed activity types/opening-quiz flag/unmapped-time cap, allowed
  study-path kinds and the per-session minimum, and rule severities. A course may override selected
  values in `course.yaml` (`time_constants`, `in_class.max_unmapped_minutes`); the methodology
  supplies the default, the course has the last word.
- **Downstream may** specialize on `goal.type` — a methodology emitting `task` or `reading` instead of
  `question` still works. **Downstream must not** branch on `methodology.id`, or assume the
  question-driven numbers. Code that does either is a bug against D-011 and invariant 3.
- **Adding a methodology** is a new YAML file named in `course.yaml`; no code change (§2.5). *This is
  the load-bearing claim of the multi-teacher premise, and it is still unverified — see §9.*

### 8.6 The write path

Invariant 5 and §5.2 rule 2 say a teacher's work is never overwritten without permission, and that
the guarantee is enforced in code. This is the code (D-031b). Every agent and every command puts
content on disk through it — from Python as `classkit.write.write()`, from a shell as
`classkit write`.

**The refusal is structural.** With default arguments the call *cannot* replace a file that already
has content: it returns a `refused` outcome and touches nothing. A caller that ignores the return
value therefore still loses nothing. Replacing content requires a separate, deliberate act —
`overwrite=True`, `--overwrite` — which is the "explicit confirmation" §5.2 requires; the command
shows the teacher what is there (the refusal quotes the opening of the existing file) and asks
before taking it.

| Outcome | When | Wrote? |
|---|---|---|
| `created` | the target did not exist | yes |
| `replaced` | the target existed and either held no content, or `overwrite` was given | yes |
| `unchanged` | the target already holds exactly this content | no (no-op) |
| `refused` | the target has content and `overwrite` was not given | **no** |
| `appended` | `append()` / `--append`: content added to the end; existing bytes untouched | yes |

Two cases are deliberately *not* refusals, because nothing can be lost in either: a file holding
only whitespace, and a file already holding exactly the content being written — so re-running a
command is safe. Anything unreadable as text counts as content; refusing is the safe direction.

```
classkit write PATH [--from FILE] [--overwrite | --append] [--dry-run] [--diff]
```

Content comes from standard input unless `--from` names a file. Exit codes: `0` written or already
identical, `3` refused — distinct from the generic failure code `2`, so a caller can tell *"ask the
teacher first"* apart from *"something broke"*. `--dry-run` answers "may I write here?" without
writing, which is what a command uses to check a target before it generates anything. **`--diff`**
(D-040) prints a unified diff of exactly what `--overwrite` would change, without writing:
a command that must change part of a file (one key in `course.yaml`) shows the teacher that diff,
and writes with `--overwrite` only once it is approved. No key-level editor: preserving the comments
in a teacher's YAML would need a new dependency and a path syntax, for a rare operation.

**Appending** — `classkit.write.append()`, `classkit write --append` — adds to the end of a file and
never rewrites existing bytes, so it needs no confirmation; a missing file is created through
`write()`. It exists so that *every* write, including the course log's, goes through this one path
(D-038). `--append` and `--overwrite` are mutually exclusive.

**Removing (D-041)** — `classkit.write.remove(path, expected_hash)` deletes a file only if
its content still hashes to what the caller says it wrote, and refuses otherwise — the same
argument that lets ingest replace its own unedited output. It exists so that the one deletion
ingest needs (a local full text no longer wanted) also goes through this path. No CLI verb: nothing
a teacher runs deletes files.

**Permissions (D-041).** Replacing a file keeps its permission bits; a new file gets the
usual default (the user's umask), not the temporary file's private `0600`.

`scaffold` is this path's create-only special case: `write_new()` calls it and never passes
`overwrite`, so scaffolding has no way to replace a teacher's file at all.

> **The guarantee is only as structural as the agents' tool sets.** An agent that still has `Write`
> or `Edit` in its front matter can bypass this path entirely. Routing each writing agent through it
> — and removing those tools — is a per-agent change, made in the step where that agent is built.

### 8.7 Materials and ingest (D-035)

Ingest turns whatever a teacher already has — in whatever state it is in — into something every later
agent can read and **cite precisely**. It assumes no organization: one folder of everything, or a
tidy tree, duplicates included.

#### Layout — two layers, never mixed

```
course/
  .gitignore               scaffolded: keeps private material out of git (D-040)
  materials/
    source/                the teacher's: any files, any structure. Agents never modify it.
      links.md             the course's links, one per line
      private/             (D-040) the teacher's files that must not be committed —
                           a published book, a solutions manual. Gitignored.
    ingested/              derived and committed: one .md per material, flat, named by id
      M0007-heaps.md
      M0012-2024-final.md
      M0005-clrs.md        for a private material: the INDEX only — no body text
    private-text/          (D-040) derived, gitignored, this machine only: the full
      M0005-clrs.md        text of each private material, same anchors as its index
    manifest.yaml          every material: id, kind, format, paths, hashes, status
    coverage.md            (D-040) the latest coverage report, written by /ingest
```

`ingested/` is **flat and keyed by a stable id**, not a mirror of `source/`. A file that is renamed or
moved keeps its id (the manifest matches it by content hash), so **locators never break when the
teacher reorganizes `source/`**.

Everything under `source/` is material except: the top-level `README.md` (scaffolded) and
`links.md` (read separately), any path with a component starting with `.`, Office lock files
(`~$…`), and `Thumbs.db` / `desktop.ini`. `scaffold course` creates `source/README.md`,
`source/links.md` and `ingested/`; the manifest is created by the first ingest.

#### `links.md`

One link per line, optionally followed by `—` and a note:

```
https://www.youtube.com/watch?v=… — heaps explained, 12 min, good for U06
https://en.wikipedia.org/wiki/Binary_heap
```

Parsing: blank lines, `#` headings and `<!-- … -->` comments are skipped; a leading list bullet
and Markdown `[text](url)` are accepted; ` — `, ` – `, ` -- ` or ` - ` separate the note. Any other
line is **not a link**: it is listed in the pre-flight report and ignored, never guessed at. A URL
must be `http(s)` with a host. Two URLs are the same link when they match with scheme and host
lowercased, the fragment and a trailing slash dropped — the query is kept (`watch?v=…` is a video's
whole identity).

`classkit add-url URL [--note TEXT]` appends a line through the write path's append mode (§8.6),
rejecting a malformed URL or one already listed (exit 2).
**A link becomes a material only when the teacher lists it** (D-040). Ingest does **not** harvest
URLs from inside slides and documents: in the hand test that recorded a book's whole bibliography as
course materials, broke URLs at line wraps, and buried the one link that mattered. A link inside a
deck is readable in the deck's ingested text (kept as `[text](url)`). The classifying agent *mentions* links it
noticed that look like course resources ("the Unit 1 deck links to the course Gem — add it with
`classkit add-url`?"); the teacher decides. Each listed link becomes a material of kind `video` (a
known video host or a video file extension) or `link`. **In Core only the link and safely fetchable metadata (title,
duration) are recorded — not its content.** Fetching is best-effort — 5-second timeout, HTML only,
the first 512 KB — and a link whose metadata cannot be fetched is recorded all the same, titled by
its note or its URL (`--no-fetch` skips it). A link listed only in `links.md` is marked removed when
its line goes. A link harvested by an
earlier version (it carries `found_in`) is treated the same way: the next ingest marks it removed
unless `links.md` lists it, and listing it restores its old id, so a locator to it keeps working.

#### The manifest

`materials/manifest.yaml` — a list; each material:

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `M<NNNN>` | ✓ | assigned once, never reused |
| `title` | string | ✓ | the first slide title or heading, else the file's metadata title — unless it is tool boilerplate ("PowerPoint Presentation", "Microsoft Word - …") **or looks like a file name or a path** (`manual.dvi`, `*.tex`, `*.pdf`, `C:\…`; D-040/F-12) — else the file name, cleaned of `_` and extension. **Never a PDF's first line of text** (D-040/F-12). A plain-text file, which has nothing else, is still titled by its first line — except a private one (G-9). A link's fetched title, else its note, else its URL. Editable; re-ingest keeps it |
| `format` | string | ✓ | `pptx`, `pdf`, `docx`, `md`, `odt`, `url`, … |
| `kind` | enum | ✓ | `slides \| textbook \| notes \| exam \| exercise \| syllabus \| reading \| link \| video \| other` — set by the classifying agent, correctable by the teacher |
| `sources` | array\<string\> | ✓ | paths under `source/` (or the URL); **more than one when duplicates were merged** |
| `canonical` | string | ✓ | which of `sources` the anchors refer to (a PPTX over its PDF export, since "slide 18" beats "page 18") |
| `source_hash` | string | ✓ | hash (`sha256:…`) of the canonical source **as last converted**; for a link, of its normalized URL |
| `source_hashes` | map path→hash | | the *current* hash of every path in `sources` — how a renamed or moved file is re-matched, including a merged copy that is not canonical. `source_hashes[canonical] ≠ source_hash` means the source changed and is not yet converted |
| `ingested_hash` | string | | hash of the `.md` ingest last wrote — lets a hand edit be detected |
| `status` | enum | ✓ | `ingested \| unsupported \| no-text \| media \| link` |
| `status_reason` | string | | e.g. "install LibreOffice, or export to PDF" |
| `units` | array\<`U<NN>`\> or `all` | | units this material appears to support — a hint, proposed by the agent. **`all`** = course-wide (the textbook, a course Gem); `[]` = no particular unit (D-040). Set by `/ingest` before any unit exists, from the material's own numbering; **re-mapped by `/plan-units` once the unit map is approved (target, D-039, step 3)** |
| `found_in` | `M<NNNN>` or `M<NNNN>#anchor` | | **retired (D-040)** — links are no longer harvested from materials; kept in the schema only so a manifest written before D-040 still validates |
| `note` | string | | for a link: the note after it in `links.md` |
| `duration` | string | | for a video link, when its page declares one: `12:03`, `1:02:45` |
| `ingested_at` | date | | `YYYY-MM-DD`, stored as a string |
| `removed_at` | date | | the source disappeared. The record and its `.md` are kept, so locators to it fail visibly |
| `merged_into` | `M<NNNN>` | | the teacher confirmed this is the same material as another; its sources moved there and this id is retired |
| `private` | boolean | | (D-040) `true` when the canonical source **as last converted** was under `source/private/` (like `source_hash`, it records the last conversion: a file just moved in or out differs from it until the next ingest converts it). Set by ingest from the path, never by hand; written only when `true`; recorded so that a clone without the file still knows |
| `private_text_hash` | string | | **retired (D-041)** — was the hash of the full text in `private-text/`; a committed field cannot describe a machine-local file (extraction differs across library versions). The full text now certifies itself (below). Kept in the schema only so an older manifest validates |
| `audience` | enum | | (D-040) `student \| instructor`; absent means `student`. Who may be *pointed at* this material. Proposed by the classifying agent, confirmed by the teacher at gate 3. Independent of `private` (a published book is private but `student`) |

Schema: `schemas/manifest.schema.json`, checked by `classkit validate` (`schema`; an unreadable
manifest is a `schema` error too). The file is tool-owned: every save rewrites the whole list from
what was loaded, so a value the teacher corrected survives, but a YAML comment they added does not.
Records are never deleted, which is also what keeps ids from being reused; a new id is one past the
highest in the manifest **or** among `ingested/` file names. Before classification, `kind` is
guessed from the format (`slides` for decks, `video` for media and video links, `link`, else
`other`).

#### An ingested file

Front matter carries the id, title, format, canonical source path and `source_hash`. The body is the
extracted text with **explicit anchors**, so a locator names a place that demonstrably exists. The
file lives at `ingested/M<NNNN>-<slug>.md` and is found by its `M<NNNN>-` prefix, so the slug may be
renamed by hand.

| Format | Anchor | Locator |
|---|---|---|
| PPTX, ODP | one heading per slide: `## Slide 18` | `M0007#slide-18` |
| PDF | one heading per page: `## Page 34` | `M0003#page-34` |
| DOCX, ODT, RTF, MD, HTML | the document's own headings, slugified | `M0012#question-3` |
| TXT | none — plain text has no structure; a line starting `#` is escaped | `M0015` |
| link, video | none — the material is the link | `M0020` (a timestamp goes in the locator's `note`) |

- **Anchors are slugs of the body's ATX headings** (`#`…`######`), outside fenced code blocks: lowercased,
  every run of non-word characters replaced by `-`, Unicode letters kept. A repeated heading gets
  `-1`, `-2`, … as GitHub's renderer does. So `## Slide 18` → `slide-18`. Body text that would start
  with `#` is escaped, so extraction never invents an anchor.
- **Slides** are numbered by position in the deck, hidden slides included (marked `*(hidden slide)*`);
  the slide title follows the heading in bold, then the text, tables and speaker notes.
- **Pages** are physical pages, 1-based — they always exist and never repeat. Where the PDF's
  printed page label differs (front matter, a textbook's own numbering) it is noted under the
  heading, `*(printed page 45)*`, so a teacher citing "p. 45" can find `page-63`. Because a wrong
  page still validates (page 45 exists), **every book citation also names the book's own
  coordinates in its `note`** — section, exercise or question number, printed page (§8.2, D-039).
- A **`no-text`** PDF still gets its page headings, with empty text: a locator to a page that exists
  resolves, and the teacher may type the text in by hand.
- `unsupported` and `media` materials have no `.md` and no anchors; they are cited by id alone.

#### Private and instructor-only material (D-040)

Two different properties, with two mechanisms suited to each:

| | Example | Source committed? | Full text committed? | Student-facing material may cite it? |
|---|---|---|---|---|
| ordinary | the teacher's own slides | yes | yes | yes |
| **private** | a published textbook's PDF | **no** | **no** — index only | yes |
| **instructor** | a solutions manual, a past exam | per its folder | per its folder | **no** |

**Private = where the file is.** Anything under `source/private/` is private — the folder name
matched **in any case**, because macOS git ignores `Private/` too, and treating it as ordinary
would commit the full text of a file whose source git keeps out (`doctor` asks for the exact name).
Git ignores by path, not by manifest field, so a folder is the one mechanism a `.gitignore` can
protect. `scaffold course` writes `course/.gitignore` covering `materials/source/private/` and
`materials/private-text/` — in `course/`, so it belongs to the course and never conflicts with a
framework update; create-only, like every scaffolded file, so re-running `scaffold course` adds it
to an older course (and logs that it did). The rules protect a clone only if `course/.gitignore`
is itself committed — a global excludes file that lists `.gitignore` defeats that silently, and
`doctor` reports it.

- **The committed `ingested/M<NNNN>-slug.md` of a private material is an index**, not the text:
  front matter as usual plus `text: index`, and in the body **every anchor heading the full text
  has**, each followed only by its one-line labels — never body text:
  - PDF: per page, the printed page label where it differs from the physical number (as in the full
    text, `*(printed page 45)*`) and the section(s) that start on that page, from the PDF's outline
    (bookmarks), `*(section: 6.2 Maintaining the heap property)*`; without an outline, pages and
    labels only;
  - PPTX/ODP: per slide, the slide title (`**Heaps**`) and `*(hidden slide)*`;
  - DOCX and other heading-structured formats: the headings themselves (they *are* the anchors).

  A label is one line of at most 120 characters, never a heading. The material's `title` — in the
  index's front matter and the manifest, both committed — is never a line of body text either: a
  heading, slide title or metadata title, else the file name (not a PDF's first line). A few KB.
  Locators resolve against the index, so they validate on every clone. The index is ingest's own
  output (`ingested_hash`, hand-edit protection as for any ingested file).
- **The full text is written to `materials/private-text/M<NNNN>-slug.md`** — gitignored, this
  machine only, the same anchors, its front matter carrying the `source_hash` it was made from
  **and `body_hash`, the hash of the file as ingest wrote it, without that line (D-041)**. The full text
  *certifies itself*: a body that still matches `body_hash` is ingest's own output and may be
  replaced freely — including a **stale** one, made from another version of the source, which is
  simply refreshed; a body that does not match is the teacher's edit and is protected like any hand
  edit (refused through the write path, `--keep` / `--overwrite`). Nothing machine-specific reaches
  the committed manifest. (D-041 replaces the committed `private_text_hash`: extraction is
  deterministic only for one library version, so a TA's ingest rewrote it and made the teacher's
  own unedited text look edited — and a stale text could not be told from an edited one.) Editing
  the front matter itself breaks the self-check, and the file then counts as edited — the safe
  direction. A full text written before D-041 has no `body_hash`: it counts as unedited if it
  matches the retired `private_text_hash` its manifest record still carries, else as edited; ingest
  drops that field whenever it next converts the material. Both files are checked before either is written, so a refusal of one leaves both as
  they were — an index and a full text from different versions would disagree about their anchors.
  Agents read the full text when it is there. Where it is not, the material is *index only here*:
  an agent says so and must not present recall as a reading of it.
- **A private source that appears on a machine** (a TA copies the PDF in) is matched by hash like any
  file; if its full text is missing or stale here, ingest writes it, and leaves the committed index
  alone when nothing changed. Such a run changes nothing committed — not the index, not the
  manifest's `ingested_at` — so it is reported as `full text … (this machine only)` and is **not a
  course-log entry**.
- **A private source that is missing is "not on this machine", never "removed".** A teacher's
  machine without the PDF and a TA's clone that never had it are indistinguishable from inside a
  checkout, so ingest does not mark a private material removed, and its locators keep resolving.
  Removing one is explicit: `classkit material remove ID` (run by the teacher, or by `/ingest` on
  the teacher's confirmation). It refuses a material that is not private (delete its source;
  ingest marks it removed) and one whose source is still on this machine (the next ingest would
  restore it). Like every removal it keeps the record and the index, so a locator to it fails
  visibly. Cost, accepted: a book deleted from the teacher's own machine keeps its record until
  removed; `classkit doctor` lists it.
- **Moving a file into or out of `private/`** is a move (same id) that changes `private`: the next
  ingest rewrites the committed `.md` as an index (or as the full text) and adds or drops the local
  copy — dropping it only if it is exactly what ingest wrote (its `body_hash` proves no edit is
  lost), through the write path's guarded `remove()` (D-041); a hand-edited one stays, and `doctor` lists it as a leftover. Moving a file into `private/` **does not remove it from git history**; `validate` reports it
  (`private_material_committed`), and cleaning history stays the teacher's decision.
- **Two machines with different copies of the same private source** (a corrected printing on the
  teacher's machine, the old PDF on a TA's): each sees the other's as *changed*, and **the last
  machine to ingest rebuilds the committed index** from its copy (D-041, accepted while one person
  usually ingests). `doctor` reports, as a note, when this machine's copy differs from the one the
  committed index was built from (D-041) — a note, not an action, because from inside a checkout "I updated the book" and "my copy is older" look the same. If several people ingest one course, revisit:
  an explicit `ingest --reindex ID` was the rejected alternative.
- **An identical copy across the boundary** (`source/clrs.pdf` *and* `source/private/clrs.pdf`) is
  one material whose canonical source is the public path — so it is **not** private, and the
  public copy is committed anyway. Copying into `private/` protects nothing; only deleting the public
  copy does, and that is the teacher's call. `doctor` reports it as an ACTION; once the public copy
  is gone, the private one becomes canonical and the next ingest makes the material private.
  Preferring a private path as canonical was rejected: it would commit an index while the PDF itself
  stayed committed — a false sense of privacy.
- **The framework does not decide what is copyrighted.** The classifying agent may say "this looks
  like a published book — consider moving it to `source/private/`"; the move is the teacher's.
- Without an outline (a scan, some exports) the index has pages and printed labels but no sections.

**Instructor = what the material is.** The manifest's `audience: instructor`, proposed by the
classifying agent with its reason and confirmed by the teacher at gate 3. Default `student`: most
material is student-facing, and gate 3 follows conversion directly.

- **Citing it from a student-facing place is an `alert`** (`instructor_material_cited`): a study
  path's `ref`, a guiding question's `answer` (D-019), and later a Gem's knowledge files. **Not**
  the in-class plan or an assessment item's model answer — those are the teacher's, and "discuss the
  manual's solution on p. 13" is legitimate there.
- An alert, not an error (D-037): a study path in the course repo does not reach a student until it
  is *published*. **The hard guarantee is at publication** — every exporter refuses, in code, to
  bundle or publish `audience: instructor` or private material (Exports phase).
- Which fields count as student-facing is one table in the validator, like `LOCATOR_FIELDS`: today a
  study path's `ref` (`goals[].paths[].ref`); step 4 adds `answer[].ref` and the session-level
  `paths[].ref`. `activities[].materials` is deliberately absent.
- "Instructor" does not mean "agents never read it": the classifier must read a solutions manual to
  classify it. It means "never pointed at, or handed to, a student". What an agent reads also goes to
  the model provider; neither property changes that.

**`classkit doctor`** — this machine's copy of the course, read-only, each line `ok`, `note` or
`ACTION`, the last with the command that fixes it: `course/.gitignore` present and in effect for
`private/` and `private-text/` (asked of git in a repository, read from the file outside one), and
itself committed — not ignored by a global excludes file; a `Private/` in another case; per private
material, whether its source and its full text are here, whether the full text is stale against the
source or hand-edited (a note), whether this machine's copy of the source differs from the one the
committed index was built from (a note), and whether its committed copy is
really an index; new or moved private files; leftover full texts whose material is gone, merged, no
longer private or unknown; the framework's dependencies (classkit's own requirements) importable;
the optional converters available (pandoc, LibreOffice), with how many materials wait for each; the
working mode. A full text is *stale* when the `source_hash` in its front matter differs from the
manifest's. **A private source not on this machine is a `note`, not an action** — a TA's clone
without the book is normal. Exit `0` when nothing needs action, `1` when something does — so a
script can gate on it; `--course DIR` as elsewhere. `/ingest` runs it first, and an agent runs it before relying on a
private material's full text. The pre-flight refers to it rather than repeating it.

**`course_gitignore_missing` (warn, D-041)** — `validate`'s side of the same protection:
the course has no `course/.gitignore`, or it does not list `materials/source/private/` and
`materials/private-text/`. Committed state, the same on every clone, so it catches the clone that
never received the file. It reads the disk, so it cannot see a `.gitignore` present but never
committed (a global excludes file that ignores `.gitignore` — found on the author's machine);
`doctor`, which asks git, catches that. The two complement each other.

`private_material_committed` asks git which files under `materials/source/private/` and
`materials/private-text/` are tracked (`git ls-files`). Outside a git repository, or without git, it
is skipped silently and `doctor` says why.

#### Extractors — proactive for common formats, reactive for the rest

Conversion is **code**, not agent work (D-018): it must produce the *same anchors every time*, or
locators rot.

- **Built in** (Python, installed with the framework): `.md`, `.txt`, `.pptx`, `.pdf` (text layer),
  `.docx`.
- **Through optional external converters**, when installed: pandoc (`.odt`, `.rtf`, `.html`,
  `.epub`) and LibreOffice (`.ppt`, `.doc`, `.odp`, converted first to a built-in format). If they are
  missing, those files are marked `unsupported` with a hint — never silently dropped.
- **Anything else**: recorded as `unsupported`, listed in the pre-flight report, never fatal to the run.
  The teacher can export it to PDF and re-ingest.
- **Flagged, not handled in Core:** scanned PDFs with no text layer (`no-text` — would need OCR) and
  audio/video files (`media` — recorded, content not extracted).
- **Extraction quality (D-040 — the hand test's F-03, F-06–F-10).**
  - **DOCX text boxes** (`w:txbxContent`, including inside `mc:AlternateContent` — read the
    `Choice` or the `Fallback`, never both) are extracted with the body. An official syllabus made of
    text boxes came out as 13 characters.
  - **Equations** in slides and documents (Office Math, `m:oMath`; in a deck, inside
    `mc:AlternateContent`) are extracted as linear text in a code span — `` `(n)/(2)+x^(2)` `` — where
    possible, else as an `[equation]` placeholder, so a reader knows something is there.
  - **PDF text** is normalised: ligatures (`ﬁ`, `ﬂ`, …) expanded; the extractor's optional
    font-parsing dependency (fontTools, for `pypdf`) is installed, which fixes most broken
    characters (verify on a real textbook). Formula layout in PDFs remains unreliable; known.
  - **Low yield is reported, never silent.** Per material, the run summary flags an extraction far
    smaller than its source (e.g. a few characters from a 45 KB document) and counts empty slides
    and pages ("20 of 37 slides have no text"), so thin extraction is not mistaken for thin teaching.
    "Far smaller" is measured for DOCX and PPTX against the document's own XML (its pictures do not
    count): under 0.005 characters per byte, once the XML is over 20 KB. A PDF's measure is its empty
    pages (and `no-text` for a scan). `/ingest` passes these lines to the classifier.
  - **Library noise is captured**: what the readers log or warn (pypdf, python-pptx, python-docx,
    fontTools) is not printed; a file that drew complaints is reported once, by name, with the count
    and the first message — in the pre-flight and in the run summary.
- **Adding a format** is one extractor registered by file extension — an extension point like adding a
  methodology (§2.5). In code: `@register(".ext")` in `src/classkit/ingest/extract.py`, a function
  from a path to the extracted Markdown, its title, and a status (and, for a private material's index,
  its one-line labels). A hyperlink is kept in the Markdown as `[text](url)` — a PDF's link
  annotation as `*(link: url)*` — so it stays readable; it is never recorded as a material (D-040).
- A file an extractor cannot read (corrupt, password-protected) is `unsupported` with the reason;
  one bad file never stops the run. An `unsupported` file is retried only once an optional converter
  for its format has been installed.
- External converters work on a temporary copy; nothing is ever written next to a file in `source/`.

#### How a run works

```
classkit ingest [--preflight] [--overwrite ID]... [--keep ID]... [--no-fetch]
                [--why TEXT] [--no-log] [--course DIR]
classkit add-url URL [--note TEXT] [--course DIR]
classkit material apply [--from FILE] [--course DIR]       # YAML list of {id, kind?, units?, title?}
classkit material set ID [--kind K] [--unit UNN|all]... [--no-units] [--title T] [--course DIR]
classkit material merge ID --into ID [--course DIR]
classkit material remove ID [--course DIR]                 # only a private material, once its source is gone here
classkit doctor [--course DIR]
```

`material apply` and `material set` also accept `audience` (`--audience student|instructor`).

1. **Pre-flight, no processing** — `classkit ingest --preflight` writes nothing. Files found by
   format and total size, total slides and PDF pages, links in `links.md`,
   non-link lines in `links.md`, what changed since the last ingest — **by name and id**, not only counted (F-23; up to 15 per kind) —, files the
   reader complained about (once each), exact copies (merged
   silently), unsupported and media files with their hints, and a rough
   time estimate. Then the command **waits for approval** (§5.2).
2. **Convert** — `classkit ingest` processes only materials that are new or whose source changed
   (plus one whose `.md` is missing). It first applies the bookkeeping — moves, exact duplicates,
   removals — then converts one material at a time, **saving the manifest after each**, so an
   interrupted run resumes where it stopped. If it stopped between writing a `.md` and saving the
   manifest, the next run *adopts* that orphan (same canonical path, same source hash) rather than
   minting a second id.
3. **Classify** — the `material-classifier` agent is **read-only** (`Read`, `Grep`,
   `Glob`; no `Write`, `Edit` or `Bash` — D-039: it reads more untrusted text than any other agent,
   so it can run nothing). It **returns** `kind`, `units` and `audience` for each
   material as a YAML block — flagging any that looks like a published book outside `private/` —
   and may *mention*, as information, that two materials are the same content in two formats
   ("M0012 is the PDF export of M0007 — cite the deck"). The command shows the classification,
   applies the teacher's corrections, and records the block with `classkit material apply` — **all
   or nothing**: every entry is checked (known id, not merged or removed, valid kind and unit ids,
   no unknown keys, no id twice) before any is recorded.
4. **Report** what the course actually covers and where it is thin. **(D-040)** The report
   states its scope — which units the ingested material reaches — and says "no material yet", not
   "thin", for the rest; the volume check and ordering problems apply only to what is covered. After
   the teacher has read it, `/ingest` writes it to **`materials/coverage.md`** through the write
   path, headed by its date and the material ids it covered. A later run replaces it only on the
   teacher's confirmation (the write path refuses and shows what is there), so notes the teacher
   added are never lost silently. It is a dated snapshot: `/plan-units` reads it as input, not as
   truth.

**Matching** — one function (`reconcile`) shared by the pre-flight, the run, and the validator, so
the three never disagree about what is "not ingested". A known path with the same hash is
unchanged; with a new hash it is *changed* (the canonical source) or *detached* (a merged copy no
longer identical — it stands alone again as a new material). An unknown path whose hash a
material knows is *moved* (if that material's path with the hash is gone) or an *exact duplicate*
(added to its `sources`); whose hash a removed material had, is *restored* under the old id; else
*new*. Identical new files arrive as one material; its canonical path is the shallowest, then
shortest, then alphabetical. When a canonical source disappears, an identical copy takes its place;
if only non-identical copies remain, the material is marked removed and they stand alone. **A
private path is never marked removed or gone this way** (D-040): its missing source means "not
on this machine". The validator calls `reconcile` with private files excluded and private materials
not judged, so `materials_not_ingested` is the same on every clone.

**Same material in two formats is not detected, and nobody is asked** (D-040, reversing that part
of D-035). Only *exact* copies (same hash) are merged, silently. A deck and its PDF export stay two
materials: both are valid to cite, nothing breaks, and asking about it at every run cost more than
the problem it prevented — Avin's hand test produced 13 suspected pairs, all false. The one
preference is the agents': **when the same content exists as a deck and as a PDF, cite the deck**
(a slide is more precise, and the deck is what the teacher edits). If deduplication is ever needed —
most likely when an exporter bundles knowledge files — it is solved there, where it bites.

**Merging** is optional, never prompted (`material merge ID --into TARGET`) — the target keeps its canonical source and so its
anchors; the merged material's sources (and their hashes) join it; the merged record is marked
`merged_into` and its `.md` is left in place. A locator to the retired id is then an error that names
the target. Merge into the material whose anchors you want: the deck, not its PDF export.

**Hand edits are preserved.** A teacher may fix a bad extraction in `ingested/`. A material whose
source has not changed is never re-converted, so its edit is simply left alone. If the source *has*
changed and the file's hash no longer matches `ingested_hash`, re-ingest **does not regenerate it
silently** — it writes through the write path (§8.6) without `overwrite`, which refuses; the run
exits `3` (as `classkit write` does) and lists the refusals. **(D-040)** For each one it
shows **what replacing would change**: the differences between the current file and a fresh
extraction of the new source, grouped by anchor ("Slide 9: … → …"). It cannot say which differences
are the teacher's edit and which the source's change — only a hash of the old extraction is kept —
but it shows exactly what `--overwrite` would lose and gain, which is the decision being asked. The front
matter and the opening note are left out (they say where the text came from); at most ten anchors,
fourteen lines each, are shown, with a count of the rest. The
command shows the teacher the edit and asks, then re-runs with the answer: `--overwrite ID` (replace
the edit with a fresh extraction) or `--keep ID` (keep it; the changed source is marked as seen).
Until then the material stays outstanding (`materials_not_ingested`). Replacing ingest's *own*
unedited output passes `overwrite` — the hash proves nothing a teacher wrote is lost.

**What `material_locator_resolves` reads.** Locators are found by pattern (`M` + four digits, not
inside a longer word or URL path, optionally `#anchor`) in the fields listed in the validator's
`LOCATOR_FIELDS`: today a study path's `ref` and an activity's `materials`. A guiding question's
`answer` joins that list when it exists (D-019) — one line, not a new rule. The rule fails a locator
whose id is not in the manifest (or there is no manifest), was merged or removed, or names an
anchor that is not a heading of the material's `.md` — read as it is now, hand edits included —
or names any anchor of a material that has none (link, media, unsupported). A textbook-key
citation (`"CLRS ch.6"`) is not a locator and is not checked.

**Locators in prose (D-040).** `material_locator_in_text` (warn) applies the same check to
`M<NNNN>#anchor` found in the Markdown **bodies** of the course's own files — syllabus, units,
sessions, in-class, items, and `materials/coverage.md` — but not `LOG.md` (history: a locator to a
since-removed material is a true record) or `ingested/` (derived text). A warning, not an error,
though it names something that does not exist: front matter is data that tools act on, prose is read
by people and may be a dated snapshot that legitimately goes stale. Agents always write locators
**fully qualified** (`M0005#page-39`, never `#page-39`); the shorthand cannot be caught by code,
because `#section` is also an ordinary Markdown link. Only locators with an anchor are read in prose — a bare
`M0007` in a sentence may be anything — and text inside HTML comments (a template's instructions)
is skipped.

**Logging** (D-039). Ingest changes the course, so **every run that changes something is a log
entry** (§8.8) — including a run by hand, which nothing else would record. `classkit ingest` appends
one itself: `classkit ingest` as the title, what changed by material id (new, updated, moved,
removed, merged copies, kept edits), and `--why` (default "run by hand"). A run that changes nothing,
or only refuses, writes no entry. `/ingest` passes `--no-log` and logs each approved step itself with
`classkit log`, since it knows the why. (Unlike `validate`, which changes nothing and never logs.)

**A removed source** is marked in the manifest, never deleted: locators pointing at it must fail
validation visibly rather than disappear.

### 8.8 The course log (D-036)

`LOG.md` at the course root records **what changed in the course and why** — the meaning that
git's history of bytes does not carry. It covers the course only: materials, syllabus, units,
sessions, the hour, items. Never framework development.

Append-only. One entry per non-trivial change:

```markdown
## 2026-10-02 — /design-unit 3, step 1 approved
- **Changed:** U03-S01..S04 created (14 guiding questions)
- **Why:** first design of unit 3; teacher asked for fewer proof-heavy questions
- **Files:** units/03-heaps/sessions/01.md … 04.md
```

- **Every approved step of every command is an entry** — the log and the approval gates (§5.2) are
  the same moments. So is each ingest run.
- It is written by **`classkit log`**, not by each agent in its own style, so the format stays
  consistent and parseable:

  ```
  classkit log TITLE --changed TEXT --why TEXT [--file PATH]... [--date YYYY-MM-DD] [--course DIR]
  ```

  `TITLE` is the heading after the date — who or which command, and what happened
  (`"/design-unit 3, step 1 approved"`). `--changed` (what changed, by ID) and `--why` are
  required: an entry without a *why* is what git already records. Each field is one line (runs of
  whitespace, newlines included, collapse to a space); `Files` is comma-separated. The date
  defaults to today.
- **Append-only, structurally, through the write path.** `classkit log` adds entries with the write
  path's append mode (§8.6), which never rewrites existing bytes — so it cannot lose a teacher's
  text, including hand-written entries. If `LOG.md` does not exist it is created (header, then the
  entry) through `write()` (D-038).
- **`classkit scaffold course` starts the log**, create-only like everything scaffold writes, with
  a first entry listing the files that run created. On a course that predates the log, re-running
  scaffold creates it and says that everything else already existed. On a course that has a log, a
  re-run that creates anything (typically `.gitignore` on a course scaffolded before D-040) appends
  an entry naming what it created; one that creates nothing writes nothing.
- Parsing is tolerant: a hand-written heading with no date keeps its whole text as the title, and
  lines that are not a `Changed`/`Why`/`Files` field are kept as notes.
- **Agents read the recent entries before starting work**, so they know what was done last time and
  why — which is what makes year-to-year revision possible without re-deriving intent.
- The teacher may add entries by hand ("taught U03 — students found S02 too long").

---

## 9. Known weaknesses and open risks

Honest list, kept current.

- **Parts of this document are specified, not built.** `schemas/`, `src/classkit/` and several agents
  still implement the earlier model; the ledger says exactly which (§1.2). Deliberate and temporary,
  and the most likely thing to mislead.
- **Nobody but the critic checks that study times are honest.** The 25-minute guarantee rides on one
  teacher-approved `est_minutes` per question. Code verifies the arithmetic; only `course-critic` can
  judge whether a number is plausible. It has the time constants as an advisory yardstick (D-025), so
  it is not pure guesswork — but those constants are placeholders (Q-005), so calibration is rough.
  Fallback on record: drop the yardstick and rely on pure judgment.
- **The lecture-reversion guarantee is now a budget, not an absolute.** It used to be "every activity
  references a guiding question, no exceptions". Real hours contain legitimate unmapped activities, so
  D-028 replaced the absolute with a per-hour cap on unmapped time. That is more honest, but it moves
  the guarantee from a bright line to a number someone chose — and since D-031e that number is
  overridable per course, so a teacher can raise it to the full hour and switch the protection off
  entirely. That is deliberate (a course repo is sovereign, D-014) and it means the guarantee is a
  *default*, not something the framework can insist on.
- **The two headline guarantees are advisory.** Since D-037 a class hour drifting into a lecture, or
  a session over its budget, produces a warning, not a failure. The design relies on the teacher
  reading warnings; one who ignores them gets none of the protection §3.3 promises.
- **Some locators cannot be verified.** `material_locator_resolves` proves a slide or page exists,
  not that the answer is on it; and video timestamps and un-ingested textbook citations cannot be
  checked at all. Invariant 7 becomes *partly* mechanical — the critic still owns the rest.
- **"No Write/Edit" is only as strong as Bash.** An agent with `Bash` but no `Write`/`Edit` can still
  write a file; only its prompt forbids it. `material-classifier` therefore has no `Bash` either
  (D-039) — it returns, and the command records. The agents that still have `Bash` are reviewed as
  each is rewritten (G-4 carry-over). The orchestrating session itself has every tool; invariant 5
  is a guarantee of the write path, not a sandbox.
- **A course with private material is not self-contained** (D-040). Another clone has the index
  but not the book: agents there can cite and validate it, not read it. A new private file is not
  reported by `validate` (which ignores `private/`, to stay the same on every machine) — only by
  `classkit doctor` and the pre-flight. And a file committed before it was moved into `private/`
  stays in git history; the framework detects it, the teacher cleans it.
- **`materials_not_ingested` hashes every source file on every `validate`.** Correct and simple, and
  fast for a typical course; a course with gigabytes of video in `source/` will feel it.
- **Extraction quality varies.** Slides that are mostly images or diagrams extract to little text, and
  scanned PDFs to none. The teacher can fix a bad extraction by hand (it is preserved), but an agent
  reading a poor extraction will under-rate that material.
- **The agent layer has never been run on a real course.** Every prompt in `.claude/` is untested
  against real materials. Expect substantial revision after the first unit.
- **The pluggable-methodology claim is unverified.** D-011 says another methodology works without code
  changes; nobody has written one. Anything that must change in `src/` to accommodate a second
  methodology is a bug against invariant 3.
- **Exam confidentiality is unresolved** — Assessment phase (Q-002, Q-022).
