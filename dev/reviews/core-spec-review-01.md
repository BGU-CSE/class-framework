# Core Specification Design Review

**Date:** 2026-09-10
**Reviewer:** Antigravity (Gemini 3.1 Pro (High))

## 1. VERDICT

**YES WITH CHANGES**. The Core specification successfully defines a structurally checkable, pedagogy-agnostic framework that treats a course as a verifiable system. The content model is remarkably tight, and the mechanisms (like the `defer_to_class` constraint and the unmapped time cap) elegantly tie home-study shortcuts to in-class costs. However, it is not quite ready for implementation due to a circular dependency in the design flow (Lesson Planner vs. Assessment Writer) and the lack of mechanical enforcement for the non-overwrite command protocol. Resolving the data flow ordering and strictly enforcing file protections will change this to a YES.

## 2. IMPLEMENTABILITY SPOT-CHECK

I attempted items (a) JSON Schema for study session, (c) `syllabus.schema.json`, and (d) `/plan-units` command flow.

Points where I had to guess:
- **(a) Study Session conditional:** I had to guess if `answer` is strictly forbidden when `defer_to_class: true` or just optional. The spec says "no `answer`", which implies it should fail validation if both exist, but JSON schema conditionally forbidding a field requires specific `not` constructs. I also had to guess the exact regex for IDs like `U<NN>-S<NN>-G<N>` (e.g., `^U\d{2}-S\d{2}-G\d+$`).
- **(c) Syllabus Schema:** For the `assessment` array, I had to guess if the schema should leave the object shape entirely unconstrained for the Core phase, or enforce the `e.g. { type, weight }` shape mentioned in §8.2. I also had to guess if `prerequisites` allows empty strings or just an empty array.
- **(d) `/plan-units` flow:** I had to guess the technical handoff mechanism between `syllabus-designer` and `curriculum-architect`. The spec says they "share the outcome list", but doesn't say if the syllabus agent writes to disk first and the architect reads it, or if they share an in-memory draft. I also had to guess how the architect determines the `NN-slug` for the unit directory names, as the format is never explicitly defined.

## 3. FINDINGS

### BLOCKING

- **Circular dependency between Lesson Planner and Assessment Writer**
  - **Where:** §5.1 (The design flow) and §8.2 (`in-class.md` / `assessments/items/*.md`)
  - **Issue:** Step 3 runs `lesson-planner` (which writes `in-class.md` containing an `items: [U03-I01]` array for the quiz activity). Step 4 runs `assessment-writer` (which writes those actual items). The lesson planner must invent IDs for items that do not exist yet.
  - **Why it matters:** The workflow will fail validation at step 3 because the `item_reference` rule requires referenced items to exist, or the assessment writer will have to retroactively match hallucinated IDs.
  - **Suggested direction:** Swap the order. Run `assessment-writer` for the entry quiz first (Step 3). Then run `lesson-planner` (Step 4), allowing it to read the generated quiz items and incorporate their exact IDs into the `in-class.md` quiz activity.

- **"Never overwrite" protocol lacks mechanical enforcement**
  - **Where:** §5.2 (Command interaction protocol) and §7 (Invariant 5)
  - **Issue:** The rule "Before writing anything, a command checks whether the target already has content... and asks" relies entirely on prompt adherence. 
  - **Why it matters:** Silent loss of teacher-authored work is stated as "the one failure the framework must never have". Agents are notoriously poor at consistently obeying negative constraints (e.g., "do not overwrite") across long autonomous runs. 
  - **Suggested direction:** Enforce this in the tooling, not just the prompt. Provide a Python wrapper (e.g., a `classkit update-file` command) that structurally blocks overwrites unless a `--force` flag or interactive confirmation is provided, ensuring agents physically cannot overwrite files by accident.

### SHOULD-FIX

- **`guiding_question_assessed` will be guaranteed noise in Core**
  - **Where:** §8.4 (Validation rules) and §3.1 (What Core covers)
  - **Issue:** The rule warns if any guiding question lacks an assessment item. But in Core, only the entry-quiz items exist. A 10-minute quiz cannot possibly test all 15-20 guiding questions from the week's study sessions.
  - **Why it matters:** A warning that fires on every valid unit trains teachers to ignore validation output completely.
  - **Suggested direction:** Defer this rule entirely to the Assessment phase, or change the Core rule to `entry_quiz_covers_sample` (ensuring at least *some* guiding questions are tested), only expecting 100% coverage once homework and exams exist.

- **Syllabus `workload` block is overly strict**
  - **Where:** §8.2 (`syllabus/syllabus.md`)
  - **Issue:** The `workload` object and its `credits` / `credit_system` sub-fields are marked required.
  - **Why it matters:** A teacher drafting a new course might not have institutional approval or credit weighting settled yet. A strict requirement blocks them from validating the rest of their syllabus.
  - **Suggested direction:** Make the `workload` block or its sub-fields optional in the schema. The validator can issue a warning if they are absent, allowing iterative drafting.

- **Shared state mechanism in `/plan-units` is underspecified**
  - **Where:** §5.1 (`/plan-units` flow)
  - **Issue:** The spec demands that `syllabus-designer` and `curriculum-architect` "share the outcome list". It is unclear how two agents share state before files are written. 
  - **Why it matters:** If left to the agent's interpretation, they may diverge, causing the `objective_maps_to_outcome` rule to fail immediately.
  - **Suggested direction:** Explicitly define the handoff as sequential and file-based: the `syllabus-designer` writes `syllabus.md` first, then the `curriculum-architect` reads it to guarantee alignment.

### NITS

- **`max_unmapped_minutes` default is very generous**
  - **Where:** §8.2 (methodologies) and §8.4 (`in_class_unmapped_time_cap`)
  - **Issue:** The default is 15 minutes. In a 50-minute class, that is 30% of the time allowed for unmapped "logistics" or "current events".
  - **Why it matters:** It leaves a large window for a teacher to slip back into lecturing without triggering the guardrail.
  - **Suggested direction:** Reduce the default to 10 minutes. If a teacher genuinely needs more administrative overhead, they can explicitly override it in their `course.yaml`.

- **Name collision on the `answer` key**
  - **Where:** §8.2 (Artifact field specifications)
  - **Issue:** As noted in the spec, `answer` means locators for Guiding Questions, but a model-answer string for Assessment Items.
  - **Why it matters:** Confusing for developers and agents.
  - **Suggested direction:** Rename the assessment item's key to `model_answer` or `solution`.

## 4. WHAT IS GOOD

- **The `defer_to_class` constraint.** Tying a home-study shortcut (deferring an answer) to an in-class cost (must be picked up by an activity) is exceptionally elegant. It structurally prevents the abuse of thinking prompts.
- **Code verifies, agents judge.** The division of labor is cleanly articulated. Relying on deterministic code for reference checking and sums, while restricting agents to semantic and qualitative sanity checks, is highly scalable.
- **The syllabus coverage roof.** Capping the chain at Course Outcomes fixes a major structural gap. The validation rules ensuring no orphans in either direction guarantee alignment from the top down.

## 5. QUESTIONS FOR THE AUTHORS

- How should the `NN-slug` for unit directories be generated? Is it the architect's responsibility to format this (e.g., `01-introduction-to-arrays`), and if so, what are the constraints?
- Regarding the step-wise approval gates in the CLI: Since Claude Code doesn't natively suspend execution mid-prompt, do you envision these "gates" as conversational prompts ("I have drafted X. Shall I proceed to Y?"), or will there be custom tooling to enforce the pause?
