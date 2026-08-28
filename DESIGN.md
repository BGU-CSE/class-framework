# Design

How the framework works and why it is shaped this way. Written for developers joining the project.

This document describes **structure and flow**. It deliberately does not carry status (see
`ROADMAP.md`) or the chronological record of how decisions were reached (see `_devlog/`, which is
temporary and will be deleted before release). Where a choice needs justifying, it is stated here in
one or two sentences and cross-referenced as `D-nnn`; when `_devlog/` goes, this file is what
survives it.

> **This describes the target design, and parts of it are not built yet.** The draft is being
> finished before the code is changed to match, so the document deliberately runs ahead of the
> repository. The **implementation ledger in `ROADMAP.md` is authoritative for what actually
> exists** — check it before assuming a field, rule or agent behaviour described here is real.

## Where documentation belongs

| Document | Audience | Answers |
|---|---|---|
| `README.md` | Anyone | What is this and how do I use it? |
| `GETTING-STARTED.md` | Teachers | How do I turn my course into a flipped one? |
| **`DESIGN.md`** | **Developers** | **How does it work, and why is it built this way?** |
| `CLAUDE.md` | Agents editing the framework | What must I not break? |
| `ROADMAP.md` | Everyone | What is done, what is next, why? |
| `_devlog/` | Developers (temporary) | How did we get here? What is still undecided? |

---

## 1. The problem

A conventional course is three lecture hours a week for thirteen weeks. Flipping it means moving
acquisition to independent home study and spending the contact hour on application. Two things
reliably go wrong when people do this:

1. **The class hour quietly becomes a lecture again.** The teacher re-explains the prework "so
   everyone is on the same page", and students learn that skipping it costs nothing.
2. **The home-study budget turns out to be fiction.** "Two hours" is really four, students stop
   doing it, and the contact hour collapses because it assumed they had.

Both are *structural* failures, not motivational ones. The framework's central bet is that both can
be made **mechanically detectable**, so they fail loudly at design time rather than silently in
week three.

## 2. The one idea everything rests on

**The Guiding Question is the atomic addressable unit.**

A study goal is phrased as a question a student should be able to answer — *"Why is appending to a
dynamic array O(1) amortized when some appends cost O(n)?"* rather than *"Amortized analysis"*. It
has a stable ID (`U01-S02-G1`), and **everything else in the system references it**: in-class
activities, assessment items, the class Gem.

That single choice (D-010, refining D-007) is what makes the two failure modes checkable:

- An activity must reference ≥1 guiding question from that unit → the hour cannot be about nothing
  the students studied.
- Each guiding question carries a teacher-approved study time (`est_minutes`) and an authoritative
  answer source → the session's home budget is the *sum* of those times, arithmetic, not an
  assertion (D-020).

A guiding question carries, about itself: the `prompt` (the question), an `est_minutes` (the
teacher-approved approximate time to study it), and an `answer` — a set of *precise references to
where the correct answer lives* (a textbook subsection, a slide, a video timestamp), never the
answer in prose (that would put course content in the repo and invite fabrication). The answer is
the *authoritative location* of the correct answer: it grounds the Gem's tutoring, the assessment
writer's correct-answer key, and the critic's check (D-019).

**Study Paths are separate, and live on the Study Session, not the question** (D-020). They are an
*open, optional pool* of alternative resources for studying the session — the class Gem, a video, a
chapter — none mandatory, not exhaustive; a student may use their own (another AI, another video)
instead. They are teacher-facing for now (an inventory of what students can reach) and are **not**
time-summed — the 25-minute guarantee rides on the per-question `est_minutes`, not on the paths.

Everything else in this document is consequence.

## 3. The content model

```
Course = Syllabus + 12–13 Units                     course.yaml (config) · syllabus/syllabus.md
├── Syllabus — Bologna-style top layer              syllabus/syllabus.md
│     goal · Course Outcomes (CO1…) · workload/credits · assessment scheme ·
│     prerequisites. Its rendered view stitches in a unit overview from the units
│     below, so it can't drift. (D-021)
└── each of 12–13 Units — one week's subject, 150 min   units/NN-slug/unit.md
    ├── Unit Objectives (2–4)                       U01-O1  → outcomes: [CO1…]
    │     each rolls up to ≥1 Course Outcome (D-021); teacher-facing, not the
    │     working layer.
    ├── HOME STUDY 100 min = 2 × 50
    │   └── 4 × Study Session (~25 min)             units/NN-slug/sessions/NN.md
    │       ├── 3–5 Guiding Questions               U01-S02-G1  ← the spine
    │       │     ├── est_minutes                   teacher-approved study time; the session
    │       │     │                                 budget is the sum of these (D-020)
    │       │     └── answer                        precise refs to where the correct answer is
    │       │           textbook | slide | video | article | web. Not prose. (D-019)
    │       └── Study Paths (per session)           gem | video | textbook | article | exercise
    │             an open, optional pool of alternative resources for the session.
    │             Not enforced, not exhaustive; students may add their own. Not time-summed. (D-020)
    └── IN-CLASS SESSION 50 min (= Lesson Plan)     units/NN-slug/in-class.md
        └── Activities                              U01-A1
              each references ≥1 Guiding Question of this unit.

Assessment Items                                    assessments/items/U01-I01.md
      each references ≥1 Guiding Question.
```

The **Syllabus** (`syllabus/syllabus.md`) is the course-level top layer (D-021): a Bologna-style
document whose front matter carries the course goal, **Course Outcomes** (`CO1…`), workload/credits,
the assessment scheme (grading details deferred, Q-026) and prerequisites, with a prose body for the
aim and narrative. It is authored and edited like any other file — scaffold writes the skeleton once
into the reserved `syllabus/` slot and never overwrites. Course Outcomes are the *roof* of the
coverage chain: every Unit Objective rolls up to ≥1 outcome and every outcome is covered by ≥1
objective, so "do the units together deliver the course's promises?" becomes checkable at course
scope. Identity fields (title, code, textbooks) stay in `course.yaml` to avoid duplication; a
*rendered* syllabus stitches in the unit overview live, so it cannot drift. There is no `course.md`.

Vocabulary is fixed and synonym-free (D-012). Two words are banned because each once meant two
things: **"topic"**, and bare **"question"** — say *Guiding Question* or *Assessment Item*. The full
glossary is in `CLAUDE.md`.

Authoring format is Markdown with YAML front matter for anything containing prose a teacher edits,
and plain YAML for configuration (D-017). Front matter is the machine-readable contract; the body
below it is for humans.

## 4. The four layers

```
┌────────────────────────────────────────────────────────────┐
│  COMMANDS      .claude/commands/*.md            6 files    │
│  what the teacher types. Orchestration only —              │
│  which agents, in what order, and why that order.          │
└───────────────┬────────────────────────────────────────────┘
                │ invokes
┌───────────────▼────────────────────────────────────────────┐
│  AGENTS        .claude/agents/*.md              7 files    │
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

**The division of labour is deliberate (D-018): code verifies, agents judge.**

Code does what must be exhaustive, arithmetic, deterministic and cheap — a 13-unit course is 79
files with 221 guiding-question references that must all resolve, plus hundreds of small sums,
checked in 0.09 s for no tokens. Rules are unit-tested, so one that stops firing is caught; you
cannot unit-test a prompt, and a silently broken rule manufactures false confidence. And the agent
that wrote a unit must not be the one certifying it — self-review is systematically generous.

Agents do what code cannot attempt: is this guiding question a topic label in disguise? Would this
activity still work if nobody did the prework? Is eight minutes honest for eight pages of proofs?
This is why `course-critic` exists and why it is explicitly told not to repeat the validator.

## 5. Control flow

What actually happens when a teacher types `/design-unit 3`:

```
teacher: /design-unit 3
   │
   ├─ 1. read course.yaml → methodology name
   │     read methodologies/<name>.yaml → 4 sessions, 25 min, 3–5 goals, 50-min hour
   │     read unit.md, earlier units, materials/source/
   │     (scaffold the unit first if it does not exist)
   │
   ├─ 2. study-session-designer  ─── loads writing-guiding-questions
   │        writes sessions/01..04.md    estimating-study-time
   │
   ├─ 3. lesson-planner              ← cannot run before step 2:
   │        writes in-class.md           it has no questions to build the hour around
   │
   ├─ 4. assessment-writer  ─── loads writing-guiding-questions
   │        writes assessments/items/U03-I*.md
   │
   ├─ 5. classkit validate  → fix every error
   │
   └─ 6. report to the teacher, including what was guessed
```

Two orderings are load-bearing rather than stylistic:

- **The lesson planner runs after the session designer.** The hour is built from the week's guiding
  questions, so it cannot be planned before they exist.
- **Review is a separate command and a different agent.** `/review-unit 3` runs `course-critic`,
  which did not write the work it judges.

And one workflow rule: **design one unit at a time.** Agents infer the subject and level from what
is already in the repo, so a reviewed unit 1 improves unit 2, and an unreviewed bad one propagates.

## 6. Data flow

| Reads | Written by | Consumed by |
|---|---|---|
| `course.yaml` | teacher | every agent, all tooling |
| `syllabus/syllabus.md` | curriculum-architect | validator, (rendered) syllabus export |
| `methodologies/*.yaml` | framework (or a teacher adding one) | designer, planner, validator |
| `defaults/time-constants.yaml` | framework, overridable per course | designer, critic, validator |
| `materials/source/*` | teacher | `/ingest`, curriculum-architect, designer |
| `unit.md` | curriculum-architect | designer, validator |
| `sessions/NN.md` | study-session-designer | planner, assessment-writer, gem-builder, validator |
| `in-class.md` | lesson-planner | critic, validator |
| `assessments/items/*.md` | assessment-writer | validator, (later) exporters |
| `exports/gems/**` | gem-builder | students, via Gemini |

Nothing downstream reads a methodology's *identity* — only the `goals[]` a session declares. See §8.

## 7. The two-repo model

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
update would have to be re-applied by hand, and a fork is limited to one per account which breaks on
the second course.

**The framework repo contains no `course/` directory at all** (D-015). The course tree is created
entirely by `classkit scaffold`, which makes framework/course file-disjointness structural rather
than policed — and that disjointness is what keeps `git merge framework/main` clean.

Governance (D-014): the framework repo is permission-controlled; a teacher's course repo is
sovereign — they may do whatever they like in it. The framework cannot enforce anything there, so
merge hygiene is documented guidance, not a rule: editing framework files is allowed and will
conflict on the next pull. How updates *should* work after a teacher has edited things is still open
(Q-007).

## 8. Extension points

**Adding a methodology.** `question-driven-25` is one implementation of a contract, not the only
option (D-011). Drop a YAML file in `methodologies/`, name it in `course.yaml`, done. Its numbers —
sessions per unit, session length, goals per session, allowed goal types, activity types, rule
severities — are read, never hardcoded.

The contract is the **study-session schema**: downstream agents consume `goals[]` and may specialize
on `goal.type`, but must never branch on which methodology produced them. `type` exists precisely so
a methodology emitting tasks or readings instead of questions still works.

*This claim is untested.* See §10.

**Adding a validation rule.** Add the check to `Validator`, give it a code, set a default severity in
`DEFAULT_SEVERITY` if it is not an error, and add a test that breaks a scaffolded course and asserts
the code fires. A rule with no such test is worse than no rule.

**Adding an agent.** New file in `.claude/agents/`. If its craft overlaps an existing agent's, put
the craft in a skill and have both load it — otherwise the two drift and the teacher gets
contradictory advice.

## 9. Invariants

Enforced by tests, schemas, or review. `CLAUDE.md` states them for agents working on the framework;
they are repeated here with their reasons.

1. **No course content in the framework repo.** Tests build a throwaway course in `tmp_path`.
   Without this, framework updates collide with teacher content.
2. **Nothing hardcodes methodology numbers.** Otherwise every teacher gets Avin's pedagogy.
3. **Downstream consumes `goals[]`, never the methodology.** The alternative makes D-011 a lie.
4. **Every Activity references ≥1 Guiding Question.** The structural reason the hour cannot revert
   to a lecture. Never relaxed to make a validation pass.
5. **Scaffolding never overwrites.** `write_new()` is the only path to disk. A teacher re-running
   scaffold months later must not lose work.
6. **Templates must validate.** A fresh scaffold produces zero errors, or the tests fail — which is
   what keeps templates and schemas from drifting apart.
7. **Agents must not fabricate resources.** A made-up URL or page number validates cleanly and fails
   a student mid-session.

## 10. Where this design might be wrong

Honest list, kept current.

- **Parts of this document are designed, not built.** The design draft is being finished before the
  code follows, so `schemas/`, `src/classkit/` and several agents still implement the previous
  model. `ROADMAP.md`'s implementation ledger says exactly which. This gap is deliberate and
  temporary; it is also the most likely thing to mislead a new developer.
- **Nobody but the critic checks that study times are honest.** Since D-020 the 25-minute guarantee
  rides on one teacher-approved `est_minutes` per question. Code can verify the arithmetic; only
  `course-critic` can judge whether a number is plausible against the material it covers. That is a
  real weakening compared with a derived estimate — accepted knowingly, because the derived version
  was never actually wired up (Q-024) — but it means the guarantee has a human-judgment step in it,
  not a mechanical one.
- **The agent layer has never been run on a real course.** Every prompt in `.claude/` is untested
  against real materials. Expect substantial revision after the first unit. (ROADMAP Phase 2)
- **The pluggable-methodology claim is unverified.** D-011 says another methodology works without
  code changes; nobody has written one. Anything that must change in `src/` to accommodate a
  second methodology is a bug against invariant 3. (Phase 3)
- **Time constants are close to dead.** `defaults/time-constants.yaml` holds invented numbers that
  the validator barely uses, and D-020 removed their load-bearing role entirely. Whether they still
  earn a place — proposing an `est_minutes` for a teacher to approve — is open. (Q-005, Q-024)
- **`scaffold` may not need to be code at all.** An agent could read a template and write files;
  257 of 1,097 Python lines are at stake. (Q-021)
- **Exam confidentiality is unresolved.** Course repos are private, but git history is permanent and
  org owners can read it. (Q-002, Q-022)
