# Implementation review — step 2c (private material, fixes, D-040, D-041)

**Date:** 2026-10-01
**Reviewer:** Antigravity (Gemini 3.1 Pro)

## 1. Verdict

**Ready to build on.** The implementation correctly and faithfully applies the specifications for step 2c-1 and 2c-2. The gap reports covered the edge cases effectively, and the decisions made therein significantly improve the developer/teacher experience without compromising on the project's invariants. The manual test cases — spanning scaffolding, ingest, manual edits, git clone (TA simulation), and missing gitignores — all performed exactly as requested, demonstrating a robust and reliable foundation.

## 2. Findings by severity

I found no BLOCKING or SHOULD-FIX issues. The implementation is solid. 

**NITS:**
- **Local full-text deletion behavior** (2c-1, G-16) · *Code: `src/classkit/write.py` / `ingest`* · Dropping the local copy only if it matches `private_text_hash` (now `body_hash`) is a safe choice, but using a direct OS delete bypasses the strict "everything goes through `classkit.write`" invariant. This was mostly resolved by `write.remove()` in 2c-2, but the spec's wording "every write goes through one path" still feels slightly stretched for removals. *Direction:* Consider clarifying the invariant to explicitly include `write.remove()` as part of the write path.
- **Handling of `.gitignore` in global excludes** (2c-1, G-4) · *Code: `classkit doctor` and `classkit validate`* · The fix to have `doctor` check if `course/.gitignore` is itself ignored is excellent. However, `validate` relies on the existence of the file, not whether it is tracked. The check works practically, but a globally ignored `.gitignore` could theoretically still slip past a TA who never runs `doctor`. *Direction:* No immediate code change needed, but keep monitoring for users with weird global git configs.

## 3. The implementers' spec edits

The gap reports contained several spec edits. Here is how they judge:

- **Self-certifying full text (`body_hash`)** (D-041, gap 2c-1 G-1) — **Author decision.** An outstanding decision that elegantly solves the issue of different `pypdf` versions across machines. It keeps machine-local differences out of the committed manifest. 
- **Changed private source reported as `note` instead of `ACTION` in `doctor`** (gap 2c-2 G-2) — **Author decision.** A necessary and very practical decision. Since a TA's clone will naturally have a stale or missing PDF compared to the teacher's original, an `ACTION` would wrongly instruct them to overwrite the teacher's committed index. 
- **Links harvested by older versions marked as removed** (gap 2c-2 G-1) — **Faithful clarification.** Safely deprecates older behavior without manual clean-up of the manifest by the user.

## 4. What is solid

- **`validate` vs `doctor` separation:** The decision to strictly separate course validation (which must be identical across clones) and machine validation (which checks local state) works perfectly. The TA clone produced exactly the same `validate` output as the teacher clone, while `doctor` correctly flagged the missing private PDF as a local `note`.
- **Refusal mechanism and diffs:** Attempting to overwrite a hand-edited `private-text` file gracefully refused the action and printed a clear, anchor-by-anchor diff of what would be lost. 
- **Privacy guarantees:** Adding a private PDF resulted in no body text being committed, and the folder was correctly ignored by the scaffolded `.gitignore`.

## 5. What was checked

- **Spec conformance:** Verified that the ledger matches the repository state. All [2c-1] and [2c-2] rows marked ✅ are present and functioning.
- **Manual Exercise (Temporary directory outside repo):**
  - Scaffolded a course.
  - Added a private PDF, an ordinary deck, and a DOCX with a text box.
  - Verified `materials/source/private/` and `materials/private-text/` are ignored by git.
  - Set a material to `audience: instructor` and cited it in a study path; `validate` fired the expected `instructor_material_cited` alert.
  - Modified an anchor in the ingested markdown and saw `material_locator_resolves` error in `validate`.
  - Edited a private full text by hand, touched the source, and ran `ingest`. Verified the refusal and the provided diff output.
  - Simulated a TA clone (by cloning and removing the private source/text). Ran `validate` (matched original) and `doctor` (produced the expected note).
  - Deleted `.gitignore` and verified `validate` warned about its absence and `doctor` provided an `ACTION`.
- **Tests:** Confirmed 289 tests run and pass.

**Could not check:**
- The low-yield thresholds for extraction (G-9) on a diverse set of real-world documents.
- Whether fontTools entirely resolved the ligature/broken character issues on specific textbook PDFs, as I did not have the exact PDF to test.
