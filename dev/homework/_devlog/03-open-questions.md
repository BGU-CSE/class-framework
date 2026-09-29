# Homework module open questions

Eight questions raised during the homework module design phase. Each is
open — worth resolving before the corresponding sub-feature is trusted in
production, but not blocking on the design itself. Numbered with the
module's own prefix, `HW-Q`, separate from the framework's `Q-` sequence
(HW-D11).

HW-Q04 and HW-Q05 surfaced during audit rounds; HW-Q01, HW-Q02, HW-Q03 were
raised inline with earlier decisions.

Q-026 in the framework's devlog is marked resolved by HW-D01, and Q-029 carries an
update note (2026-09-28).

## HW-Q01 — Assessment item format extensibility
**Raised 2026-09-22 by Shira, during the homework design phase.**

The `format` field on assessment items is a closed enum:
`multiple-choice | multiple-select | open | numeric | true-false | code`.
Adding a new format (matching, ordering, diagram-labeling, short-answer
with regex checking) currently requires forking the framework schema.

**Proposed mechanism** — methodology-gated open strings, mirroring the
pattern already used by in-class activity types:

1. `format` in `assessment-item.schema.json` becomes `string`, not `enum`.
2. `methodology.schema.json` gains `allowed_item_formats: [string]`,
   defaulting to the six built-ins.
3. New semantic rule `item_format_allowed` checks the value is in the
   methodology's list.
4. Course-local templates for custom formats live in
   `course/assessments/formats/<name>.md`.
5. Built-in formats retain their schema-side conditional requirements
   (`choices` for MCQ, `rubric` for open, `tests` for code). Custom
   formats cannot declare schema-enforced requirements — the template
   carries the shape, the teacher accepts the trade-off in exchange for
   extensibility.

**Not decided:**
- Whether `assessment-writer` needs a per-format skill loaded to write
  custom formats correctly (probably yes, one skill per custom format,
  authored by the teacher — same pattern as `writing-code-items` under
  Q-026's deferred work).
- How rendering handles custom formats — the student handout needs to
  know how to display a matching item, and the framework's rendering
  step (which doesn't exist yet) has no plug-in point for a per-format
  renderer.
- Whether extension is per-course (custom format lives under `course/`)
  or shareable across courses of the same methodology.

**Sequencing:** not blocking. The six built-in formats cover the pilot
course. Revisit when a course actually needs a seventh — the design here
is a proposal, not a build.

---

## HW-Q02 — Item bank ingest: reference-only vs. fully-materialized items
**Raised 2026-09-22 by Shira, during the homework design phase.**
**Related:** Q-026 (resolved → HW-D01), Q-028 (material extraction), Q-002
(confidential assessment material), HW-Q06 (homework confidentiality), HW-Q08
(identifier capacity and provenance).

Teachers arrive with existing assessment items in heterogeneous formats:
past exams as PDFs, homework as Word docs, Moodle XML exports, MCQs in
spreadsheets. Two things the current design can't do with these:

1. Search across them uniformly. `homework-planner`'s search-and-browse
   requires consistent front matter.
2. Reference them from a homework manifest. `homework.items` expects
   `U0N-I0M` ids that resolve to files under `course/assessments/items/`.

Full conversion — extract each question, generate the missing pedagogical
metadata (Bloom, distractor rationales, class), rewrite as a complete
`.md` — is expensive per item and stalls on the rationale gap: existing
MCQs almost never have per-distractor rationales, and rationales are the
framework's diagnostic payload.

**Proposed mechanism** — two item shapes:

Items in the bank can be one of two shapes, both at
`course/assessments/items/U0N-I0M.md`, both with searchable front matter:

- **Fully-materialized items.** Current design. Front matter includes
  `stem`, `choices` (with rationales), `rubric`, `model_answer` as applicable.
  Written by `assessment-writer` or manually authored. Planner can display
  the full stem in candidate lists.
- **Reference-only items.** New shape. Front matter carries only search
  metadata (`unit`, `format`, `item_class`, `bloom`, `difficulty`,
  `guiding_questions`, `keywords`, `est_minutes`) plus a `source_ref`
  field pointing at the original — filename in `materials/source/`, page
  or slide or row number, optional item identifier within the source. The
  stem, choices, and rationale live in the source document. Planner can
  find these items but shows them as "source: file X, page N" pointers
  rather than full stems.

**Consequences:**
- Ingest is fast. Item-extractor produces one metadata stub per detected
  question — a catalog card, not a rewrite. LLM cost is bounded by
  number of questions, not by their length.
- Nothing is lost at ingest. Source is authoritative. Metadata errors
  are one-line edits; the underlying question stays untouched.
- Upgrade path exists. A reference-only item that gets picked for
  repeated reuse can be "promoted" — expand its `.md` with full stem,
  choices, and rationales (manually or agent-drafted).
- Planner behavior branches. Direct reuse of a reference-only item works
  (the manifest just references its id); adaptation requires promotion
  first, since there is no stem to adapt.

**Schema changes required (deferred):**
- `assessment-item.schema.json`: add optional `source_ref` object
  (`file`, `page` or `slide` or `row`, optional `item_id`). Fields
  currently required (`stem`, `choices`, `rubric`) become
  required-unless-`source_ref`-is-present.
- New validator rule `item_source_resolvable`: for reference-only items,
  `source_ref.file` exists in `materials/source/`. Warn, not error.
- `homework-planner.md`: presentation rules gain a case for
  reference-only candidates.

**Not decided:**
- Whether ingest is one command (`/ingest-items`) or a mode of `/ingest`.
- The `keywords` field's shape — free-text tags, extracted noun phrases,
  or teacher-supplied.
- Whether promotion should be automated (framework prompts after N reuses)
  or fully manual.
- How this interacts with a potential `legacy: true` flag. Overlap is
  large; may be one flag, not two.

**Sequencing:** not blocking the homework pipeline itself, but blocking
the moment a teacher wants to reuse existing questions rather than
authoring everything fresh. The pilot course has ~100+ existing items
across old exams and homework; without ingest, the bank starts empty and
fills at the speed the teacher writes new homework.

### Coordination boundary

Do not design or implement a homework-only importer. The framework has one
shared item bank (HW-D21), and framework Q-028 already owns ingestion from the
same source materials. HW-Q02 stays open until that design is coordinated with
Chen; a second command or a second conversion path would create incompatible
items in the same bank.

The homework module contributes these requirements to the framework ingest
design:

- Read candidate assessments from Word, PDF, Moodle exports, and other source
  formats the framework elects to support.
- Split an assessment into candidate Assessment Items without silently
  treating extraction guesses as approved content.
- Ask the teacher to confirm every mapping to the current course's unit and
  Guiding Questions.
- Keep an item that fits no current Guiding Question in an explicit review
  state; never invent a mapping merely to satisfy the schema.
- Apply the framework's confidentiality decision before importing past exams
  or other restricted material (Q-002 and HW-Q06).
- Write accepted items only to the shared `course/assessments/items/` bank.
- Add provenance only after the framework settles HW-Q08's identifier and
  metadata proposals.

---

## HW-Q03 — Agent-authored files: what status, what discipline?
**Raised 2026-09-22 by Shira, during HW-D04's design.**
**Related:** HW-D04 (interviewer as general-purpose agent), HW-Q01
(item format extensibility — custom formats also risk this).

Until now the framework has assumed all skills, templates, schemas, and
agent prompts are **hand-authored**. Someone sat with the file, thought
about the "one rule that matters," harvested failure modes from real
errors, refined phrasing across many attempts. Files with that treatment
are trusted as load-bearing — when `homework-item-writer` loads
`writing-code-items`, the skill's guidance is authoritative.

HW-D04 breaks that assumption. `/new-hw-type`'s second interviewer call
drafts a whole skill file from a one-paragraph teacher description. The
resulting file *looks* like a skill — same front matter, same section
headings — but it hasn't earned the same trust. The "one rule that
matters" was inferred, not distilled. Failure modes weren't harvested,
they were guessed. Phrasing wasn't refined by writing many items,
because none have been written.

**Proposed convention** — `status` field in front matter:

- `status: draft` — agent-authored or auto-generated. Read for guidance,
  but not load-bearing. If a draft skill says "always X" and a
  hand-authored skill says "sometimes Y," the hand-authored one wins.
- (absent, or `status: ratified`) — the current default; hand-authored,
  trusted.

**Promotion path** — teacher removes the `status: draft` line (or sets
`status: ratified`) once the skill has proven useful. Could be
manual, could be a future `/promote-skill` command, could be
automatic after N successful uses. Not decided.

### The problem this proposal doesn't fully solve

Right now, nothing in the framework acts on a `status: draft` flag.
`/new-hw-type` writes files with the flag; `homework-item-writer` reads
them the same as any other skill. The convention is aspirational —
future-you reading a draft skill wouldn't know it's not trusted, and
neither would a running agent.

Making the convention real requires:

- Every agent that loads skills learns to check `status`
- The "load differently" semantics need concrete definition — does a
  draft skill get lower priority in conflicts? Skipped entirely for
  high-stakes items? Loaded but with a warning surfaced to the teacher?
- The convention should apply to more than skills — agent-authored
  templates, item-class entries, tool declarations have the same
  trust question

### Not decided

- **Should agent-authored files be marked at all,** or should they just
  land as regular files that improve over time? A markerless approach
  is simpler but silent — no distinction between a skill Shira thought
  carefully about and one an agent guessed at.
- **What's the marker** — a `status` front-matter field, a filename
  prefix (`draft-writing-reading-items.md`), a separate directory
  (`.claude/skills/draft/`)? Front-matter loses discoverability in file
  listings; filename/directory forces file renames on promotion, which
  breaks references.
- **What does "load differently" mean concretely** for each kind of
  file? Skills, templates, and item-class entries would each need their
  own answer.
- **How does promotion happen** — manual teacher edit, dedicated
  command, automatic after N uses? Manual is simplest but easily
  forgotten; automatic is prone to promoting things that shouldn't be.
- **Should agents even be authoring these things,** or should the
  auto-draft branch of `/new-hw-type` always defer to a human? The
  interviewer's writing-skill drafts are a real convenience but they're
  also the point where the framework starts trusting its own
  generations. This is a bigger question than mechanics.
- **How does this interact with HW-Q01** (custom item formats)? Custom
  formats also need per-format skills, and those would face the same
  agent-vs-hand-authored question.

### Sequencing

Not blocking. `/new-hw-type` currently writes files with `status: draft`
and nothing checks the flag — the aspirational convention is in place
without teeth. Revisit once agent-authored files have accumulated in
real course use and the trust distinction actually bites. The pilot
course will surface this within a few homeworks if `Coding`,
`Research`, or a teacher-added class gets its skill drafted rather
than hand-authored.

---

## HW-Q04 — Should item-critic and item-solver apply to quiz and exam items?
**Raised 2026-09-22 by Shira, during HW-D05's design.**
**Related:** HW-D01 (homework as first-class content type), HW-D05
(evaluation strategy per class), Q-002 (exam confidentiality — still open).

Currently the multi-agent evaluation pipeline (`item-critic` +
`item-solver` looping with `assessment-writer`) runs only for homework
items. Quiz and exam items still go through the framework's original
flow: `assessment-writer` writes, `classkit validate` runs, teacher
reviews the distractor rationales. No per-item critic pass, no persona
attempts, no autograder pipeline.

**The asymmetry.** A homework MCQ gets three-agent review + teacher
gate. An entry-quiz MCQ gets one-agent + teacher. The same
"giveaway phrasing" or "unobservable rubric criterion" issues that
`item-critic` catches in a homework item go uncaught in a quiz item
that the same teacher will use in the same course.

### Possible extensions

- **`item-critic` for quiz/exam.** Same reviewer, same checks
  (giveaway detection, rubric criterion observability, guiding-question
  alignment). No new agent needed. Would run inside `/write-items`
  after `assessment-writer` produces items, before teacher review.
- **`item-solver` for autograded exam/quiz items.** Real autograder
  behavior, currently absent from the framework entirely. Would need
  the same `evaluation.strategy` handling as homework (HW-D05), applied
  to items regardless of usage.
- **A separate `exam-critic`.** Different concerns from `item-critic`:
  ambiguity is worse in a high-stakes exam, difficulty calibration
  matters more, cheating vectors matter. Could inherit from
  `item-critic` and layer exam-specific checks.

### Design tensions

- **Overkill for entry quiz.** A 2-minute concept-check MCQ getting
  a three-iteration critic loop and persona-attempt solver is
  disproportionate. The teacher can eyeball five entry-quiz items.
- **Not overkill for exams.** Exam items are high-stakes. A giveaway
  MCQ in an exam is a real problem. `item-critic` earns its keep here.
- **Framework's current quiz-writing rule** (`assessment-writer.md`
  line 42) says: "For an entry quiz, aim at diagnosis, not
  difficulty." Adding a solver that measures calibration might
  actively conflict with the diagnosis-first stance.

### Not decided

- Whether `item-critic` should run per-usage: on for exam, on for
  homework, off for entry quiz. Or on for all, with the teacher able
  to skip it per-command.
- Whether `item-solver` should run at all outside homework, or
  whether autograding (HW-D01's `format: code`) should have its own
  agent when the time comes.
- Whether the class-strategy model (HW-D05) should be extended so a
  class can declare "evaluate me in homework, but not in quiz."
- How this interacts with Q-002 (exam confidentiality): if exam
  items live in a separate repo, does the multi-agent pipeline reach
  them at all?

### Sequencing

Not blocking. The homework pipeline works with just its own agents.
Revisit when: (a) a teacher explicitly asks for critic-review of
quiz items, (b) the autograder use case for exams comes up in a
real course, or (c) enough homeworks have shipped that we can tell
whether critic/solver caught things the teacher would have missed.

---

## HW-Q05 — Sandbox and resource policy for code execution
**Raised 2026-09-22 by external reviewer.**
**Related:** HW-D01 (homework pipeline), HW-D05 (evaluation strategy),
HW-D02 (Coding item class).

`item-solver` executes teacher-provided or agent-generated code via
Bash when the class's `evaluation.strategy` is `execute` (typically
Coding-class autograded items). Currently the guidance to code
authors is "no wall-clock, no randomness, no network" — this is a
prompt instruction, not an enforceable policy.

### Real risks

- **Infinite loops** — a buggy `expected_solution` or a fuzz-style
  test can hang the pipeline.
- **File system access** — code can read or write anywhere Bash can
  reach.
- **Network egress** — a call to a package registry, a leaked API
  key, a data-exfiltration path.
- **Resource exhaustion** — memory bombs, disk fills, fork bombs.
- **Non-determinism** — even with "no randomness" as instruction, a
  test's outcome depending on `os.urandom` or system time makes
  autograding unreliable.

### Options

- **Container sandbox** — run `expected_solution` and `tests` inside
  a per-item Docker or Podman container with strict CPU, memory, and
  time limits, and no network. Adds an operational dependency.
- **Restricted subprocess** — Python-level restrictions (resource
  module limits, `subprocess` with timeout, restricted PATH). Less
  strong than a container but no external dependency.
- **External autograder service** — e.g. Codegrade, or a custom
  service. Removes the problem from the pipeline but adds
  integration cost.
- **Skip execution entirely** — force all Coding items through
  `persona_attempt` and remove `execute` as a strategy. Loses
  autograding value.

### Design tensions

- **Local development ergonomics.** Teachers running
  `/create-homework` locally on their laptop should not need a
  container runtime installed. A sandbox that's optional for local
  drafts but required in CI is one middle ground.
- **Autograder value.** The whole point of `execute` is to catch
  reference solutions that fail their own tests, and to give the
  solver a real signal. Weakening this loses evaluation power.
- **Attack surface.** Course repos are shared with collaborators
  and TAs; a malicious PR that adds an item with an evil
  `expected_solution` could reach a teacher who runs the pipeline
  without noticing.

### Not decided

- Whether the framework should ship a sandbox or leave it as a
  build-time integration responsibility.
- Whether local runs and CI runs should have different execution
  guarantees.
- Whether the `execute` strategy should be gated behind an explicit
  `--allow-execution` flag on the command.
- What the minimum acceptable resource policy is (time limit,
  memory limit, filesystem, network).

### Sequencing

Should be resolved before the `execute` strategy is used against
untrusted content — i.e. before any course repository accepts
external contributions to items. For a single-author course being
run by the author, the risk is lower (though infinite loops are
still real). A minimum viable policy: subprocess timeout + network
disabled + read-only filesystem for the running code.

---

## HW-Q06 — Where is homework graded, and what must stay hidden?
**Raised 2026-09-28 by Shira, during the homework design phase.**
**Related:** framework Q-002 (exam confidentiality), Q-029 (the entry quiz
checking homework), D-004 (Moodle sync, not built); HW-Q05 (sandbox).

For a graded homework the correct answers live in the item files —
`model_answer`, `rubric`, `expected_solution`, `tests` — inside the course
repo, which is shared with collaborators and whose git history is permanent.
The framework already stops and asks before writing exam items (Q-002); the
homework pipeline does not control *where the answers are stored*.
(`answer_release`, which controlled when students saw answers, was dropped in
HW-D25; publishing solutions is the teacher's call, outside the pipeline.)

How sensitive that is depends on the **item class** and the **purpose**,
not on "graded or not" alone:

| Case | Where grading happens | What is sensitive |
|---|---|---|
| Coding, graded on Moodle VPL | VPL runs the tests | the hidden test cases and the reference solution (`tests`, `expected_solution`) — students must not see them before the deadline |
| DIY / Practicing, practice | often not graded; answers may be released with the homework | little or nothing |
| DIY / Practicing, graded | teacher or TA, against the model answer | `model_answer`, `rubric` |
| Research | teacher, against the rubric | only the rubric — no answer key by design |
| Not checked; next week's quiz asks from it | the entry quiz | framework Q-029 — out of scope for the module for now |

### Candidate shape (not designed)

A per-class `grading` block in `item-classes.yaml`, for example
`channel: manual | vpl | none`, plus which fields stay hidden and until when.
The planner and Gate 1 could then tell the teacher what a given homework
exposes, instead of one blanket warning.

### Not decided

- Whether graded answers may live in the course repo at all — that is
  Q-002, the framework's decision.
- How `tests` are exported to VPL's format — belongs with the Exports phase
  and Moodle sync (D-004), not with the homework module.
- Whether the "quiz checks homework" model (Q-029) needs anything from the
  homework manifest.

### Sequencing

Revisit when Q-002 is decided or when a course first grades homework on
VPL. (Partly settled by HW-D24: the Word documents, including the teacher
answers document, are never committed. The answers inside the item files
remain the open part.) Until then the module changes no behavior: the leak check on the
student document (HW-D23) is the safeguard.

---

## HW-Q07 — Re-reviewing a finished or old homework
**Raised 2026-09-29, when `/review-homework` was removed (HW-D17).**

The pipeline checks each item (critic, solver) and the teacher approves the
whole at Gate 2. Nothing re-checks a **finished homework as a whole**: item
order and difficulty ramp, redundancy between items, tone consistency,
balance between targeted versions (HW-D26), overlap with earlier homework. Nor is there a way
to re-check an **old** homework before reusing it next semester.

### Not decided

- Whether this is needed at all, or Gate 2 is enough.
- If needed: a module-owned agent (not the framework's `course-critic`), a
  step inside `/create-homework` before Gate 2, or a standalone command.

### Sequencing

Revisit after the first real homework, if teachers ask for it.

---

## HW-Q08 — Bank growth: identifier capacity and provenance
**Raised 2026-09-29, with HW-D21.** **For the framework (Chen):** both touch
the shared item schema.

- **Identifier capacity.** Item ids are `U01-I01`…`U01-I99` — at most 99 items
  per unit. A bank that keeps every homework, quiz and exam item across
  semesters, plus imported past items, will reach that limit.
- **Provenance.** Nothing records whether an item was generated by the
  pipeline or imported, or where an imported item came from (which past
  exam, which semester's homework). Usage history can be derived from
  manifests (HW-D21); provenance cannot.

### Not decided

- A wider id pattern (e.g. three digits) versus another scheme.
- Which provenance fields, if any (for example `origin: generated | imported`
  and a free-text source), and whether they are optional.
- Both are changes to `assessment-item.schema.json` and the framework's id
  conventions, so they are proposals to Chen, not module decisions.
