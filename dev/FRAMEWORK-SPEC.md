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
| Exports | The class Gem builder, PPTX, **the rendered syllabus** (one human-readable document — e.g. PDF — combining `syllabus.md`, the identity fields from `course.yaml`, and a unit overview derived from the units) | Deferred |
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
proposes duplicates, reports coverage — §8.7), `course-critic` (review). Commands: `/ingest`,
`/plan-units`, `/design-unit N`, `/review-unit N`, and **`/write-items N` scoped to entry-quiz
items** — `/design-unit` already writes the unit's entry quiz, so `/write-items` in Core is for
adding to or reworking it. Deferred: `gem-builder` and `/build-gem` (Exports); the homework and exam
roles of `assessment-writer` and `/write-items` (Assessment).

**Tooling commands used across Core:** `classkit ingest` (the deterministic half of `/ingest`,
§8.7), `classkit add-url` (add a link to the course's materials, §8.7), `classkit material` (record
a material's kind, units or title; merge a confirmed duplicate, §8.7), and `classkit log` (append
to the course log, §8.8).

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
/ingest            (§8.7) 1. pre-flight scan: count files by format, slides/pages, duplicates,
                      links, unsupported files, a rough time estimate — then WAIT for approval
                   2. classkit ingest converts each new or changed source into
                      materials/ingested/M<NNNN>-slug.md with addressable anchors, and
                      updates materials/manifest.yaml (incremental, resumable)
                   3. material-classifier sets each material's kind and likely units
                      (through `classkit material set`) and proposes same-material
                      duplicates; the command asks the teacher to confirm each, and merges
                      only what is confirmed (`classkit material merge`)
                   4. report what the course actually covers and where it is thin
                   Every approved step appends to course/LOG.md (§8.8).
/plan-units        ONE flow, two agents, sequential and file-based (D-029, D-031i):
                   1. syllabus-designer writes syllabus/syllabus.md — goal, Course
                      Outcomes (CO1…), workload, prerequisites. Written to disk first.
                   2. curriculum-architect READS that syllabus and writes units/NN-slug/
                      unit.md, each objective referencing the outcome ids it just read.
                   The handoff is the file, not shared memory: the architect must never
                   invent an outcome id, and either agent can be re-run alone.

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
| `materials/manifest.yaml` | `classkit ingest` (+ `classkit material`, called by material-classifier and the teacher) | every agent that cites material, validator | Core |
| `materials/ingested/*.md` | `classkit ingest`; the teacher may hand-edit | curriculum-architect, designer, assessment-writer, critic | Core |
| `LOG.md` | `classkit log`, called by every command at each approved step | every agent (recent entries), the teacher | Core |
| `unit.md` | curriculum-architect | designer, validator | Core |
| `sessions/NN.md` | study-session-designer | planner, assessment-writer, validator | Core |
| `in-class.md` | lesson-planner | critic, validator | Core |
| `assessments/items/*.md` | assessment-writer | validator, (later) exporters | Core (entry quiz); Assessment (rest) |
| `exports/gems/**` | gem-builder | students, via Gemini | Exports (deferred) |

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
| `materials/ingested/MNNNN-slug.md` | the material's id plus a slug of its title; flat, one per material |
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

`bloom` enum, everywhere it appears: `remember | understand | apply | analyze | evaluate | create`.

**Completeness (D-032).** The syllabus front matter is intended to carry **everything a Bologna-style
course descriptor needs**, so that a teacher never has to keep syllabus information somewhere else.
Only `goal` and `outcomes` are required; everything else may be filled in stages, or deliberately
skipped. Two categories are deliberately *not* fields here:

- **Identity and configuration** — title, code, institution, instructors, language, textbook list —
  live in `course.yaml`, the single source of truth. Repeating them here would create drift.
- **The unit overview / course contents** — derived from the `unit.md` files, which are authoritative.

Both are pulled in when the syllabus is rendered for people to read (deferred — see §1.1). The rule:
**authored content is a field here; derived content is assembled at render time.**

Body: prose aim and narrative. Identity fields (title, code, textbooks) are **not** repeated here —
they live in `course.yaml`. A future rendered syllabus (Exports) pulls them in, along with a unit
overview assembled from the units.

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
| `paths` | array\<obj\> | | **(target, session-level; D-020)** open optional resource pool; each `{ kind (enum), ref (string), note (opt) }`; `kind ∈ gem \| video \| textbook \| article \| exercise \| other`; **not** time-summed |

Goal object (the Guiding Question):

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `U<NN>-S<NN>-G<N>` | ✓ | must be prefixed by its session id |
| `type` | enum | ✓ | `question \| task \| reading \| exercise`; question-driven-25 allows only `question` |
| `prompt` | string | ✓ | the guiding question, phrased so a student can answer and check it |
| `objectives` | array\<`U<NN>-O<N>`\> | ✓ (≥1) | unit objectives this goal rolls up to |
| `est_minutes` | number ≥0 | | **(target, D-020, D-038)** teacher-approved study time; the session budget sums these. **Not schema-required** — a missing estimate is pedagogy (the teacher has not estimated yet), not shape: the budget rule reports the session as *unverifiable* (warn) instead |
| `answer` | array\<obj\> | advisory: ≥1 **unless** `defer_to_class` — not schema-required (D-037) | **(target, D-019)** precise locators of the correct answer; each `{ kind (enum), ref (string), note (opt) }`; `kind ∈ textbook \| slide \| video \| article \| web \| other`; never the answer in prose. **Prefer a material locator** — `ref: "M0007#slide-18"` — which the validator can check (D-035); a textbook key with a locator (`"CLRS §2.3.1"`) remains allowed for sources that are cited but not ingested |
| `defer_to_class` | boolean | | **(target, D-023)** default `false`. If `true`: no `answer`; a pre-class thinking prompt that **must** be referenced by ≥1 in-class activity |

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
| `materials_not_ingested` | a source (file or `links.md` line) is new, changed, moved or gone since the last ingest — one finding, reported against `materials/manifest.yaml` (D-035) | advisory | warn |
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
classkit write PATH [--from FILE] [--overwrite | --append] [--dry-run]
```

Content comes from standard input unless `--from` names a file. Exit codes: `0` written or already
identical, `3` refused — distinct from the generic failure code `2`, so a caller can tell *"ask the
teacher first"* apart from *"something broke"*. `--dry-run` answers "may I write here?" without
writing, which is what a command uses to check a target before it generates anything.

**Appending** — `classkit.write.append()`, `classkit write --append` — adds to the end of a file and
never rewrites existing bytes, so it needs no confirmation; a missing file is created through
`write()`. It exists so that *every* write, including the course log's, goes through this one path
(D-038). `--append` and `--overwrite` are mutually exclusive.

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
course/materials/
  source/                  the teacher's: any files, any structure. Agents never modify it.
    links.md               the course's links, one per line
  ingested/                derived: one .md per material, flat, named by id
    M0007-heaps.md
    M0012-2024-final.md
  manifest.yaml            every material: id, kind, format, paths, hashes, status
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
`/ingest` also collects every URL it finds *inside* slides and documents, recording where it was
found (`found_in: M0007#slide-3`). Each link becomes a material of kind `video` (a known video host
or a video file extension) or `link`. **In Core only the link and safely fetchable metadata (title,
duration) are recorded — not its content.** Fetching is best-effort — 5-second timeout, HTML only,
the first 512 KB — and a link whose metadata cannot be fetched is recorded all the same, titled by
its note or its URL (`--no-fetch` skips it). A link listed only in `links.md` is marked removed when
its line goes; one found inside a document stays.

#### The manifest

`materials/manifest.yaml` — a list; each material:

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `M<NNNN>` | ✓ | assigned once, never reused |
| `title` | string | ✓ | the first slide title or heading, else the file's metadata title (unless it is tool boilerplate such as "PowerPoint Presentation"), else the file name; a link's fetched title, else its note, else its URL. Editable; re-ingest keeps it |
| `format` | string | ✓ | `pptx`, `pdf`, `docx`, `md`, `odt`, `url`, … |
| `kind` | enum | ✓ | `slides \| textbook \| notes \| exam \| exercise \| syllabus \| reading \| link \| video \| other` — set by the classifying agent, correctable by the teacher |
| `sources` | array\<string\> | ✓ | paths under `source/` (or the URL); **more than one when duplicates were merged** |
| `canonical` | string | ✓ | which of `sources` the anchors refer to (a PPTX over its PDF export, since "slide 18" beats "page 18") |
| `source_hash` | string | ✓ | hash (`sha256:…`) of the canonical source **as last converted**; for a link, of its normalized URL |
| `source_hashes` | map path→hash | | the *current* hash of every path in `sources` — how a renamed or moved file is re-matched, including a merged copy that is not canonical. `source_hashes[canonical] ≠ source_hash` means the source changed and is not yet converted |
| `ingested_hash` | string | | hash of the `.md` ingest last wrote — lets a hand edit be detected |
| `status` | enum | ✓ | `ingested \| unsupported \| no-text \| media \| link` |
| `status_reason` | string | | e.g. "install LibreOffice, or export to PDF" |
| `units` | array\<`U<NN>`\> | | units this material appears to support — a hint, set by the agent |
| `found_in` | `M<NNNN>` or `M<NNNN>#anchor` | | for a link discovered inside another material: where |
| `note` | string | | for a link: the note after it in `links.md` |
| `duration` | string | | for a video link, when its page declares one: `12:03`, `1:02:45` |
| `ingested_at` | date | | `YYYY-MM-DD`, stored as a string |
| `removed_at` | date | | the source disappeared. The record and its `.md` are kept, so locators to it fail visibly |
| `merged_into` | `M<NNNN>` | | the teacher confirmed this is the same material as another; its sources moved there and this id is retired |

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
  heading, `*(printed page 45)*`, so a teacher citing "p. 45" can find `page-63`.
- A **`no-text`** PDF still gets its page headings, with empty text: a locator to a page that exists
  resolves, and the teacher may type the text in by hand.
- `unsupported` and `media` materials have no `.md` and no anchors; they are cited by id alone.

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
- **Adding a format** is one extractor registered by file extension — an extension point like adding a
  methodology (§2.5). In code: `@register(".ext")` in `src/classkit/ingest/extract.py`, a function
  from a path to the extracted Markdown, its title, the links found, and a status.
- A file an extractor cannot read (corrupt, password-protected) is `unsupported` with the reason;
  one bad file never stops the run. An `unsupported` file is retried only once an optional converter
  for its format has been installed.
- External converters work on a temporary copy; nothing is ever written next to a file in `source/`.

#### How a run works

```
classkit ingest [--preflight] [--overwrite ID]... [--keep ID]... [--no-fetch] [--course DIR]
classkit add-url URL [--note TEXT] [--course DIR]
classkit material set ID [--kind K] [--unit UNN]... [--no-units] [--title T] [--course DIR]
classkit material merge ID --into ID [--course DIR]
classkit material duplicates [--course DIR]
```

1. **Pre-flight, no processing** — `classkit ingest --preflight` writes nothing. Files found by
   format and total size, total slides and PDF pages, links in `links.md` and embedded in documents,
   non-link lines in `links.md`, what changed since the last ingest, exact and suspected duplicates
   (only those this run has to decide), unsupported and media files with their hints, and a rough
   time estimate. Then the command **waits for approval** (§5.2).
2. **Convert** — `classkit ingest` processes only materials that are new or whose source changed
   (plus one whose `.md` is missing). It first applies the bookkeeping — moves, exact duplicates,
   removals — then converts one material at a time, **saving the manifest after each**, so an
   interrupted run resumes where it stopped. If it stopped between writing a `.md` and saving the
   manifest, the next run *adopts* that orphan (same canonical path, same source hash) rather than
   minting a second id.
3. **Classify and confirm** — the `material-classifier` agent sets `kind` and `units` through
   `classkit material set` (it has no `Write`/`Edit`), and proposes suspected same-material
   duplicates with its evidence. **The command asks the teacher to confirm each**, and runs
   `classkit material merge` only on confirmation. Exact duplicates (same hash) merge without asking.
4. **Report** what the course actually covers and where it is thin.

**Matching** — one function (`reconcile`) shared by the pre-flight, the run, and the validator, so
the three never disagree about what is "not ingested". A known path with the same hash is
unchanged; with a new hash it is *changed* (the canonical source) or *detached* (a merged copy no
longer identical — it stands alone again, and is asked about afresh). An unknown path whose hash a
material knows is *moved* (if that material's path with the hash is gone) or an *exact duplicate*
(added to its `sources`); whose hash a removed material had, is *restored* under the old id; else
*new*. Identical new files arrive as one material; its canonical path is the shallowest, then
shortest, then alphabetical. When a canonical source disappears, an identical copy takes its place;
if only non-identical copies remain, the material is marked removed and they stand alone.

**Suspected duplicates** are reported, never merged by code: in pre-flight, files whose names match
across formats (ignoring markers such as `copy`, `final`, `export`, `(1)`); after conversion, also
pairs where ≥80% of the shorter material's distinct words appear in the other (≥20 words). The run
reports only pairs involving what it converted, so a pair the teacher declined is not re-asked on
every run; `classkit material duplicates` lists them all.

**Merging** (`material merge ID --into TARGET`) — the target keeps its canonical source and so its
anchors; the merged material's sources (and their hashes) join it; the merged record is marked
`merged_into` and its `.md` is left in place. A locator to the retired id is then an error that names
the target. Merge into the material whose anchors you want: the deck, not its PDF export.

**Hand edits are preserved.** A teacher may fix a bad extraction in `ingested/`. A material whose
source has not changed is never re-converted, so its edit is simply left alone. If the source *has*
changed and the file's hash no longer matches `ingested_hash`, re-ingest **does not regenerate it
silently** — it writes through the write path (§8.6) without `overwrite`, which refuses; the run
exits `3` (as `classkit write` does) and lists the refusals with the opening of each file. The
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

**Logging.** `classkit ingest` does not write the course log itself — like `validate`, it is a tool
the teacher may also run by hand. `/ingest` logs each approved step with `classkit log` (§8.8).

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
  scaffold creates it and says that everything else already existed.
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
- **"No Write/Edit" is only as strong as Bash.** `material-classifier` records everything through
  `classkit`, and has no `Write`/`Edit` — but it has `Bash`, which could write a file. The prompt
  forbids it; nothing structural does. The same holds for every agent that runs `classkit`.
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
