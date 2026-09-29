---
id: {{item_id}}
unit: {{unit_id}}
format: code
item_class: Coding
guiding_questions: [{{unit_id}}-S01-G1]
usage: [homework]
difficulty: medium
bloom: apply
# est_minutes is optional for Coding (time_variance: high, HW-D06). When absent, the
# homework budget uses the midpoint of the class's typical_minutes range.
stem: "TODO — problem statement: inputs, outputs, constraints (including complexity)."
starter_code: |
  # Skeleton the student edits. Omit for from-scratch problems.
  def solve(nums):
      pass
expected_solution: |
  # Reference solution. Teacher-only: it goes to the teacher answers document.
  def solve(nums):
      return sum(nums)
tests:
  - input: "[1, 2, 3]"
    expected: "6"
    note: "typical case"
  - input: "[]"
    expected: "0"
    note: "empty case — the tripwire"
  - input: "[-1, 1]"
    expected: "0"
    note: "cancellation"
rubric:
  - criterion: "Handles the empty case."
    points: 3
  - criterion: "Correct for the general non-empty case."
    points: 5
  - criterion: "Meets the complexity constraint stated in the stem."
    points: 2
---

Notes: code items combine a rubric (which grades the student's *approach*)
with tests (which grade correctness mechanically). Both should be present.
The rubric catches "correct logic, one edge case missed"; the tests catch
"looks reasonable but wrong on real input."

Tests must be deterministic — no wall-clock, no randomness, no network. The
grader runs them, and a flaky test in an item bank is worse than no test.

# Notes

- This is the homework module's **Coding-class** template (HW-D10). The format
  `code` belongs to the framework; what this template adds is the Coding fields:
  `starter_code`, `expected_solution` and `tests`.
- `format: code` means autograded — the item's `tests` are run against the student's
  code. Use this template when the item has a runnable check.
- For a Coding-class homework item that will be graded by a human reading the code
  (not autograded), start from `item-open.md` instead, set `item_class: Coding`, and
  structure the rubric per the `writing-code-items` skill.
