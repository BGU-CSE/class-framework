# Working in this repo

## Which hat are you wearing? — decide this first, and say so

**Default: TEACHER.** You are helping build and maintain a **course**. That is what this repo is
for once it has been cloned, and it is what the rest of this file describes.

You are in **FRAMEWORK-DEVELOPER** mode only if either:

- a **`dev/.developer`** file exists — it is gitignored, so it exists only in a developer's checkout
  and never in a teacher's clone; or
- you have been asked to change the framework itself: `schemas/`, `src/classkit/`, `templates/`,
  `methodologies/`, `.claude/`, or `dev/`.

In that case **stop and read `dev/CLAUDE.md` before doing anything** — it carries the invariants you
must not break. A developer switches hats with **`classkit mode developer`** (and back with
`classkit mode teacher`); `classkit mode` alone reports the current one.

**State your mode in your first reply, and again whenever it changes** (it should change rarely —
essentially only when a developer sets up a checkout). A `SessionStart` hook
(`.claude/hooks/report-mode.sh`) announces it as well, but say it yourself: the hook may not have run.

A `course/` directory present is positive confirmation you are in a teacher's repo — the framework
repo never contains one.

---

# Teacher mode — building a course

This repository is your working environment. Your course lives in `course/`, created by
`classkit scaffold`; everything else is the framework that helps you build it.

**`GETTING-STARTED.md` has the full workflow.** `README.md` explains what the project is.

## Vocabulary — use these words, no synonyms

Two words are **banned** because each used to mean two things: **"topic"**, and bare
**"question"** (say *Guiding Question* or *Assessment Item*).

| Term | Meaning |
|---|---|
| **Syllabus** | The course-level top layer, `syllabus/syllabus.md`. Course goal, Course Outcomes, workload, prerequisites. One per course. |
| **Course Outcome** | What a student who passes the course can do. `CO1`, `CO2`, … The roof of the coverage chain: every Unit Objective rolls up to ≥1 outcome. |
| **Unit** | One week's subject. 12–13 per semester. |
| **Unit Objective** | Abstract, teacher-facing goal. 2–4 per unit. Not the working layer. |
| **Study Session** | The ~25-min at-home unit. 4 per Unit. |
| **Guiding Question** | A session goal phrased as a question the student should be able to answer. 3–5 per session. **The atomic addressable unit.** |
| **Study Path** | An optional, non-exhaustive pool of alternative resources for studying a Study Session. Per session, not per question; not time-summed. |
| **In-Class Session** | The weekly 50-min meeting. Synonym: **Lesson Plan**. One per Unit. |
| **Activity** | A component of an In-Class Session. Has a duration; normally references ≥1 Guiding Question. |
| **Assessment Item** | A single quiz/homework/exam question. |

## ID conventions

Mechanically checked by the schemas and the validator.

```
CO1              Course Outcome (in the syllabus)
U01              Unit
U01-O1           Unit Objective
U01-S02          Study Session
U01-S02-G1       Guiding Question   ← referenced by everything else
U01-IC           In-Class Session
U01-A1           Activity
U01-I01          Assessment Item
```

## The commands

| Command | What it does |
|---|---|
| `/ingest` | Read your existing materials and report what the course actually covers |
| `/plan-units` | The syllabus: course goal, Course Outcomes, the unit map, unit objectives |
| `/design-unit N` | One unit end to end — study sessions, the in-class hour, the entry quiz |
| `/review-unit N` | An independent agent reviews what it did not write |

`classkit scaffold` creates files; `classkit validate` checks that the course holds together.
Scaffolding **never overwrites**, so it is safe to re-run at any time.

## How the commands should behave

Hold them to this — it is specified behaviour, not a nicety:

- **Stepwise, with your approval.** A command announces a step, produces it, shows you the result,
  and waits before starting the next. It does not design a whole unit and present it finished.
- **Never overwrite without asking.** Anything already written is shown to you first. This one is
  enforced by the tooling, not merely by instruction.
- **Revise rather than regenerate.** Where output already exists, the default is to change what you
  asked about and leave the rest alone.

## The teacher is the authority

The validator **informs you; it doesn't overrule you.** Only *broken data* — a reference to
something that doesn't exist, a file that can't be read — is an error. Everything else is advice
about good practice: warnings, and **alerts** (high-priority advice, shown first) for coverage —
whether the units deliver the course outcomes. You may depart from any of it.

To make a deliberate exception stop nagging, add to that file's front matter:

```yaml
accepted:
  - rule: session_budget_feasibility
    reason: "long session on purpose — exam week"
```

or change a rule for the whole course in `course.yaml` under `rules:`. **Agents never do either on
their own** — only when you ask — and they never "fix" something you decided.

## Rules the agents follow

- **No invented resources.** No made-up URLs, page numbers, slide numbers or video titles. A
  fabricated reference validates cleanly and fails a student mid-session.
- **Fix what you caused; never overrule the teacher.** Resolve or report any finding your own output
  produced. Never add `accepted:`, change `rules:`, or raise a threshold unless the teacher asks.
- **Every activity in the class hour builds on the home study.** An activity that references no
  Guiding Question is allowed — exam logistics, a current-events hook — and the total time on such
  activities is flagged past a limit, because an hour made of them is a lecture again.
- **The methodology's numbers come from `methodologies/*.yaml`**, never hardcoded — 4 sessions, 25
  minutes, 3–5 questions, a 50-minute hour. To change them, change that file, not the agents.

## Editing framework files

You may — it is your repository. The cost is that `git merge framework/main` will then conflict on
exactly those files. If you want painless updates, add new files rather than editing existing ones.

---

*Developing the framework itself? Everything you need is in **`dev/CLAUDE.md`**.*
