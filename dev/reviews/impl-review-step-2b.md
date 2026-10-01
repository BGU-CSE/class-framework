# Implementation review — step 2b (ingest)

## 1. Verdict

**Needs fixes first.** The implementation successfully delivers a robust ingestion pipeline, accurate extraction with stable anchors, and proper duplicate detection. The structural refusal to overwrite hand-edits works exactly as specified. However, giving the `material-classifier` agent the `Bash` tool to bypass the lack of `Write`/`Edit` tools breaks Invariant 5 ("Never overwrite a teacher's work ... enforced in code, not by prompt"). This must be fixed to restore the structural guarantee.

## 2. Findings by severity

### BLOCKING

**The `material-classifier` agent uses Bash to write to disk**
- **Where:** `dev/reviews/impl-gaps-step-2b.md` G-1, `.claude/agents/material-classifier.md`
- **What is wrong:** The agent was given the `Bash` tool to run `classkit material set`. 
- **Why it matters:** Giving an agent arbitrary shell access completely defeats Invariant 5 (never overwriting, enforced in code). The agent could theoretically run `rm -rf` or `echo >` and overwrite teacher work. A negative prompt constraint ("do not use Bash to write files") is exactly what D-030 and D-031b were designed to replace with structural guarantees.
- **Suggested fix direction:** Remove the `Bash` tool from the agent. Either have the agent return its proposed `set` classifications as a structured response which the orchestrating command then applies (similar to how `merge` is handled), or expose `classkit material set` as a strictly constrained, purpose-built tool.

### SHOULD-FIX

**Missing tests for `materials_not_ingested` on moved/removed files**
- **Where:** `tests/test_course_lifecycle.py`
- **What is wrong:** The rule is designed to flag new, changed, moved, and removed files. However, the tests only cover new files, changed files, and new links.
- **Why it matters:** Without tests asserting that the rule warns on moved and removed sources, any future refactor to the `reconcile` logic might silently break this behavior. 
- **Suggested fix direction:** Add tests that move/rename a source file and remove a source file, asserting that the rule fires with a `warn`.

**Missing tests for `material_locator_resolves` against hand-edited anchors**
- **Where:** `tests/test_course_lifecycle.py`
- **What is wrong:** The spec states that locators are checked against the `.md` file "as it is now, hand edits included". There are no tests verifying that hand-edited anchors successfully resolve, or that a previously valid anchor fails if a teacher removes it by hand.
- **Why it matters:** Hand edits are a core feature for fixing bad extractions. We must guarantee that validation accurately reads the live state of the file, not just the extraction output.
- **Suggested fix direction:** Add a test that manually edits an ingested `.md` to add a new heading, then verify a locator to that new heading resolves successfully.

### NITS

**`ROADMAP.md` row for step 4 locator fields is unticked, but `paths` is already being checked**
- **Where:** `dev/ROADMAP.md` (D-035)
- **What is wrong:** The ledger notes that `paths[].ref` will be added in step 4. In reality, the codebase checks `goals[].paths[].ref` because `paths` have not yet been moved to the session level (D-020).
- **Why it matters:** It is slightly confusing but technically correct for the current state.
- **Suggested fix direction:** No code fix needed, but acknowledge this nuance when step 4 lands.

## 3. The implementer's spec edits

- **G-1 (Agent recording without Write/Edit):** Author decision. Unacceptable as it breaks Invariant 5.
- **G-2 (Extra manifest fields):** Faithful clarification. These fields logically fulfill the spec's behavioral requirements.
- **G-3 (PDF physical pages):** Author decision. A practical, reliable choice.
- **G-4 (Merge into target, keep stale):** Author decision. Faithful to the mandate not to delete files.
- **G-5 (Merge edge cases):** Faithful clarification. 
- **G-7 (ingest not logging):** Faithful clarification. It mirrors the decision for `validate` in D-038.

## 4. The ⚑ items

- **G-1:** **Reject.** Giving the agent `Bash` compromises the entire write-path safety model. The command must orchestrate the `set` calls based on the agent's structured output.
- **G-2:** **Accept.** The fields are necessary to implement the specified behavior.
- **G-3:** **Accept.** Physical pages guarantee stable, non-repeating anchors.
- **G-4:** **Accept.** Deleting the stale `.md` could destroy teacher edits; leaving it is the safest option.
- **G-5:** **Accept.** The fallback logic is robust.
- **G-6:** **Accept.** Re-running classification in step 3 is unnecessary churn; the hint is sufficient.
- **G-7:** **Accept.** Consistency with `classkit validate`.
- **G-8:** **Accept.** Standard wheels are perfectly fine and avoid the need for external system packages.

## 5. What is solid

- **Extraction and anchors:** The locators are highly reliable. `material_locator_resolves` properly catches missing anchors and removed materials.
- **Hand-edit preservation:** The `--overwrite` / `--keep` workflow perfectly intercepts changes and protects teacher work.
- **Duplicate detection:** The logic for exact hashes and suspected duplicates successfully catches renames and formats.
- **Testing architecture:** The validation tests explicitly verify that rules fire and properly assert the exact expected severity (`error`, `warn`).

## 6. What I checked

- **Spec conformance:** Evaluated the implementer's edits against §8.7 and the framework's invariants.
- **Ledger honesty:** Checked `ROADMAP.md` ticked items against the codebase and confirmed they align with the current implementation phase.
- **Invariants:** Verified that the framework accurately protects `materials/source/`, enforces ID stability on renames, and flags broken locators.
- **Tests:** Reviewed `tests/test_course_lifecycle.py` to ensure rules are tested for behavioral failure and severity correctness.
- **Manual testing:** Created a temporary course outside the repo and exercised the full ingest pipeline (DOCX, PPTX, PDF, exact copies, unsupported files, Markdown, links). Ran preflight, verified `no-fetch` idempotency, renamed source files (ID remained stable), hand-edited ingested files (triggered refusal correctly), merged duplicates, deleted a source file, and ran `classkit validate` to verify locator checks (missing anchors and removed materials both fired errors as expected).
