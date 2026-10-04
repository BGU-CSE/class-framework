# Independent Review: Syllabus & Units Increments (Step 3)

## 1. Verdict

**Needs fixes first.** While the code and logic are robust, there is a **BLOCKING** workflow issue in the prompt sequences for `/plan-syllabus` and `/plan-units` that violates the command interaction protocol and will confuse the agent during execution. 

## 2. Findings by Severity

### BLOCKING (Prompt Findings)

**Write Path Gates in Step 2 of `plan-syllabus.md` & `plan-units.md`**
* **Where:** `plan-syllabus.md` (Step 2) and `plan-units.md` (Step 2).
* **What:** The prompts instruct the agent to run `classkit write`, tell the teacher it failed (exit 3), ask the teacher for `--overwrite` go-ahead, run `classkit validate` and fix errors, and *then* "Wait" at the end of the step.
* **Why it matters:** An agent cannot execute a command, wait for the teacher's approval, run a validation command, fix the errors, and *then* wait again all within one step of a prompt. If the agent pauses to ask for `--overwrite`, it terminates its turn. When the teacher says "yes", the agent might skip the validation because it's no longer in the context of Step 2, or it might try to validate *before* the teacher approves (which would validate the old placeholder files). 
* **Fix direction:** Separate the "Show diff and ask for overwrite" from the "Execute overwrite and validate". Explicitly define the turn boundary. For example, Step 2 should end at "Wait for their go-ahead to overwrite." Then, a new sub-step should state: "Once approved, run `classkit write --overwrite`, then run `classkit validate`, fix any errors, and show the result."

### SHOULD-FIX (Code / Tooling Findings)

* **Gap G-1: Default stage in `approve unit N` jumps state dangerously**
  * **Where:** `src/classkit/approve.py` (`next_stage`).
  * **What:** Approving twice in a row without edits advances the unit to `designed` even if the sessions are still placeholders. 
  * **Why it matters:** A teacher who re-runs the approve command might accidentally flag a placeholder unit as completely designed, breaking the downstream pipeline.
  * **Fix direction:** Remove the default stage inference. Require the `--stage` flag explicitly as the implementer suggested.
* **Gap G-2 & G-4: Scaffolded placeholders cause validation noise**
  * **Where:** `scaffold` templates for unit.md and sessions.
  * **What:** Placeholders include `CO2` (which throws a hard error `outcome_reference` if the syllabus doesn't have it) and only name `-O1`/`-O2` in sessions (which throws an alert `objective_coverage` if the plan has more objectives).
  * **Why it matters:** A teacher scaffolding a unit gets immediate errors and alerts before they've even planned anything, violating the principle that rules shouldn't nag about unfinished states.
  * **Fix direction:** Do not hardcode `CO2` in scaffold templates, or add a condition to `validate.py` that skips these rules if the unit's stage is `planned` or not yet approved.
* **Gap G-3: Provenance of material unit hints is lost**
  * **Where:** `materials/manifest.yaml` and `plan-syllabus.md` (Step 5).
  * **What:** Step 5 relies on the teacher remembering if they set hints manually because the manifest doesn't record who set them.
  * **Why it matters:** Relies on human memory instead of the framework tracking its own state.
  * **Fix direction:** Introduce a `units_set_by: teacher` (or `origin: teacher`) field to the material schema and manifest.

### NITS (Code Findings)

* **Gap G-2 (Syllabus): `unit_map[].evidence` locators are unchecked**
  * **Where:** `src/classkit/validate.py`.
  * **What:** The locators are not validated.
  * **Fix direction:** Add them to the `material_locator_resolves` check (as a warn). This is a low-effort addition that prevents agents from hallucinating map evidence.

## 3. The Implementers' Spec Edits

The implementers did a good job documenting their decisions:
* **Gap G-1 (`approve unit N` default stage):** *Author decision*. The implementer built the spec's "defaults to the next one" but flagged it as a trap. The spec should be updated to make `--stage` mandatory.
* **Gap G-3 (Hash definition):** *Faithful clarification*. The decision to hash the canonical JSON of the front matter excluding the `approved` key is a solid technical design to ensure YAML comments and formatting aren't treated as edits.
* **Gap G-4 (`approve` writes directly):** *Faithful clarification*. The decision to run `--diff` to show changes and `--overwrite` to commit them fits the workflow perfectly.
* **Gap G-6 (Designed hash):** *Faithful clarification*. Hashing relative paths and handling unparseable files gracefully prevents broken files from breaking `classkit status`.

## 4. What is Solid

* **Agent Prompts (`curriculum-architect`, `syllabus-designer`, `course-critic`):** The prompt instructions are meticulously crafted to avoid hallucination. The strict instruction to leave unknowns as `**TBD:**` and to use evidence rather than memory is excellent.
* **Write Path and Hash Logic:** The implementation in `classkit approve` and `classkit write` is extremely robust. The append-mode edits to front matter that preserve teacher comments are well implemented.
* **Spec Adherence:** The separation of concerns between code verification (tooling) and adversarial judgment (course-critic) is well respected in the implementation.

## 5. What was Checked, and What was Not

* **Checked:** 
  * The prompt logic and sequence in `.claude/commands/` and `.claude/agents/`.
  * The `classkit approve` logic, state transitions, and hash generation (`src/classkit/approve.py`).
  * The `classkit validate` rules for syllabus and units.
  * Ran end-to-end scaffolding, syllabus planning, unit planning, and manual edits in a temporary directory to verify `status`, `approve`, and validation warnings.
* **Not Checked:**
  * Materials ingestion and classifier pipeline (`/ingest`) with real PDF files and documents. This relies on external binaries and document structures that were not mocked for this review.
