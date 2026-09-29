# Implementation Review — Step 2a

## 1. Verdict

**Needs fixes first.** The implementation is largely solid and the test coverage is good, but the decision to make `reason` schema-required inside `accepted:` exceptions (G-6) creates a blocking defect. It causes a schema validation error (a hard failure) if a teacher omits the reason for a pedagogical exception, which directly contradicts D-037's principle that validation informs but does not overrule. Once this schema requirement is relaxed into a semantic warning, step 2b is ready to proceed.

## 2. Findings

### BLOCKING

**`reason` in `accepted` exceptions causes a schema error (G-6)**
* **Where:** `schemas/*.schema.json` and `src/classkit/validate.py`
* **What is wrong:** `reason` is a required property for `accepted:` entries in the JSON schemas. A missing reason fails validation as a hard `error` (exit code 1).
* **Why it matters:** It contradicts D-037's principle that validation informs but does not overrule the teacher. The teacher is making an exception to a pedagogical rule; requiring a reason structurally via schema turns an advisory finding into a fatal build error.
* **Suggested direction:** Make `reason` optional in the schemas, and introduce a `warn`-level semantic rule (e.g., `accepted_without_reason`) in the validator.

### SHOULD-FIX

**`classkit log` violates literal invariant 5 but honors spirit (G-17)**
* **Where:** `src/classkit/log.py`
* **What is wrong:** `classkit log` appends to `LOG.md` directly without using `classkit.write.write()`.
* **Why it matters:** While appending directly is safe from overwriting, bypassing the single centralized write path establishes a precedent that agents/tooling might copy in the future, weakening invariant 5's structural guarantee.
* **Suggested direction:** Consider extending `classkit.write` to explicitly support an `append` mode, or update invariant 5 to explicitly document `classkit log` as the sole permissible exception.

### NITS
None observed.

## 3. The implementer's spec edits

* **G-2. §8.2 contradicted §8.4 on outcomes/answer:** Faithful clarification. §8.4 and D-037 were the recent authoritative decisions, so §8.2 was outdated.
* **G-3. Rules in code not listed in §8.4 take successor's severity:** Faithful clarification. New overrides rely on this, defaulting to error would violate D-037.
* **G-5. A bare `off` in YAML is boolean `false`:** Faithful clarification. It is a bug fix for YAML syntax, and the spec explicitly told teachers to write `off`.
* **G-7. Findings about a unit as a whole accepted in `unit.md`:** Author decision. The spec did not prescribe where directory-level warnings should be placed, so the implementer invented a sensible mapping.
* **G-8. `course.yaml` has no front matter:** Faithful clarification. Derives mechanically from D-017 (config is plain YAML).
* **G-9. What "a one-line count of accepted exceptions" counts:** Author decision. Deciding which metrics to surface (suppressed vs entries vs stale) is a product/UX decision.
* **G-11. `DEFAULT_SEVERITY` is now complete:** Author decision. Changes the framework's internal convention from fail-closed (default `error`) to fail-safe (unregistered raises an exception).
* **G-12. May `accepted:` suppress an integrity rule?:** Faithful clarification. Logically follows from the fact that `rules:` can do it.
* **G-14. The shape of `classkit log` arguments:** Author decision. The spec provided the output format, but the CLI arguments (`--changed`, `--why`) were designed by the implementer.
* **G-15. Where `LOG.md` header lives:** Author decision. An implementation detail that doesn't affect the spec.
* **G-16. First log entry on pre-existing course says what ran/existed:** Author decision. Resolving a missing edge case in the course lifecycle.
* **G-17. `classkit log` appends outside write path:** Author decision. Deviates from the literal reading of invariant 5 to fulfill its spirit (don't lose teacher content).

## 4. The ⚑ items

* **G-1 (The split rules had no codes):** The names `activity_without_guiding_question`, `activity_references_other_unit`, and `item_no_correct_choice` are descriptive and consistent. Keep them.
* **G-6 (Is `reason` required in `accepted:`?):** Make `reason` optional and use an advisory `warn`-level `accepted_without_reason` rule. A schema error for a missing reason on a teacher exception contradicts "only integrity findings may be error".
* **G-10 (`unknown_rule` is new, at warn):** `warn` is correct. Making it an error would break the build because of a typo in the teacher's exception, which oversteps the framework's authority.
* **G-13 (Who logs an accepted exception?):** Clarification is correct. The validator must remain read-only; agents should log when they insert it. Update the spec to clarify "each acceptance an agent adds".
* **G-19 (Item `rubric` is schema-required for `open` items):** This is pedagogical presence. Move it out of the schema `required` block and into an advisory rule in step 5.
* **G-20 (Goal `est_minutes` is `✓` in §8.2):** This is pedagogy. Missing a time estimate means the teacher hasn't completed planning. It should be an advisory warning (e.g., `session_budget_unverifiable`), not a schema error.

## 5. What is solid

* The implementation of the `alert` level, reporting order, and `--strict` flag works perfectly.
* Reclassification of the legacy semantic rules and the introduction of `rules:` and `accepted:` overrides are technically sound and respect the specified inheritance hierarchy.
* The append-only course log mechanism successfully captures the required information while protecting against data loss.
* The ledger honesty check passes: the implementer correctly left agent/command rows marked as ⬜ since they haven't been implemented yet.

## 6. What you checked

* Read `FRAMEWORK-SPEC.md`, `ROADMAP.md`, `_devlog/01-decisions.md` (D-036, D-037), and the implementer's gap report (`impl-gaps-step-2a.md`).
* Executed `pytest` locally and verified 92 tests pass.
* Scaffolded a test course in `/tmp` entirely outside the repository.
* Manually injected a bare `off` in `course.yaml` `rules:` and verified it parsed gracefully without throwing a schema error.
* Tested `accepted:` entries: with a reason (successfully suppressed), without a reason (threw schema error), and with a non-existent rule (triggered `unknown_rule` warning).
* Checked `--strict` functionality and verified exit codes behave as expected.
* Verified `LOG.md` append operations and re-scaffolding logic on a virgin course.
