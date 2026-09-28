---
name: writing-code-items
description: How to write a Coding-class assessment item. Loaded by homework-item-writer (and item-critic) when the plan slot's item_class is `Coding`. Governs items where the student writes code (usually with AI assistance) and submits code plus reasoning about it. Covers stem specifications, starter code, rubric criteria for code quality, and the AI-use stance the class implies.
status: ratified
---

# Writing code items

A Coding item asks the student to write code — usually with an AI
assistant available. Two shapes are common:

- **Autograded** — `format: code`, `item_class: Coding`. The item has `tests`
  the grader runs. Common for entry-quiz Coding items or short homework
  exercises where a runnable check exists.
- **Human-graded** — `format: open`, `item_class: Coding`. No autograder;
  the student submits code and a written analysis, and the teacher (or TA)
  reads and grades against the rubric. Common for larger Coding homework
  where the point is approach and reasoning, not just correctness.

This skill covers both. Load it whenever an item's `item_class` is `Coding`,
regardless of format. The stem-and-rubric guidance below is largely
format-independent; the "Reference solution and test cases" section
applies specifically when tests exist (autograded).

## The one rule that matters

**Grade the code the student submits AND their reasoning about it.**
Working code with no explanation is half an answer. A confident
explanation of code that doesn't run is also half an answer. Both parts
of the submission are graded, and the rubric must make that visible.

The failure mode to watch for: writing a stem where the deliverable is
just code, and a rubric that grades only correctness. A student who
prompted an AI to write the code, ran it once, and submitted it can
satisfy that item without engaging. Fix by requiring reasoning as part
of the deliverable — complexity analysis, edge-case discussion, one
design choice they'd challenge — and grading that reasoning explicitly.

## Stem structure

A well-formed Coding stem specifies:

- **The problem.** What computes what. Inputs, outputs, constraints.
- **The interface.** What the student is writing — a function with a
  named signature, a class, a full program. Naming the interface
  prevents students from turning in a beautifully architected
  never-callable framework.
- **The complexity target, if any.** "Your solution should run in
  O(n log n)" belongs in the stem. Rubric points for meeting it belong
  in the rubric. Both are required if complexity matters.
- **Whether AI is allowed and how it should be documented.** Coding
  class default is AI-allowed; make it explicit in the stem anyway.
  Students see the stem; the class label is metadata.
- **What to submit.** Code, yes. Also: a short analysis (complexity,
  edge cases handled, one design choice you'd challenge), and — if AI
  was used — the prompts you used and one thing you changed from the
  AI's output.

## Starter code

Optional. When present, the rule is: **establish the interface, leave
the algorithm empty.** For a `solve(nums)` item, the starter is the
function signature and a `pass`. Not the algorithm structure, not
comments hinting at steps, not partial implementations. Anything more
turns the item into fill-in-the-blank.

Exception: when the concept being tested lives inside a larger program
(the student is editing one function in a codebase), provide the
surrounding scaffolding and mark clearly which function is theirs.
"Edit only `solve()`; the rest is provided" is a clean contract.

For a from-scratch item, omit starter entirely. The interface is in the
stem.

## Rubric criteria

Weight the rubric across three axes:

- **Correctness** — does the code produce the right output. For autograded
  items (`format: code`), tests cover this mechanically and the rubric may
  weight it lightly. For human-graded items (`format: open`), the rubric
  criterion names what the reviewer checks: "Correct on the general
  non-empty case" is a criterion. "Handles the empty input case" is another.
  Enumerate specific cases rather than a single "works" bullet.
- **Approach and complexity** — did the student meet the complexity
  target from the stem? Did they choose a reasonable data structure?
  A "meets the stated O(n log n) bound; student's analysis confirms
  this" criterion catches the O(n²) solution that passes small
  hand-checks.
- **Reasoning and AI use (if allowed)** — did the student explain
  their choices? If they used AI, did they submit prompts and identify
  something they changed or challenged in the output?

Divide labor cleanly: never grade the same thing twice. If the rubric
awards points for "correct on general case" and another criterion
awards points for "runs without errors," you're double-counting.

## AI-use guidance

The Coding class defaults to AI-allowed. Two things the stem must do:

1. **Say explicitly that AI is allowed and expected.** Students who
   don't know may waste time avoiding it.
2. **Require documentation of AI use** as part of the submission — the
   prompts used, one thing the student changed or challenged from the
   AI's output. Without this, there's no signal on whether the student
   engaged or just pasted.

For items where AI should NOT be allowed (rare in Coding class; more
common if the item is really Practicing-that-happens-to-involve-code),
say so in the stem AND consider whether the item's class should be
`Practicing` instead. Class and stem should agree.

## Reference solution and test cases (for the teacher's file)

Even without an autograder, the item file should carry an
`expected_solution` and a small set of test cases in the item's
metadata. These aren't shown to students; they're the reviewer's cheat
sheet during grading, and `item-solver` runs them to catch broken
model answers.

Test cases the teacher writes for themselves should still be
**deterministic** — no wall-clock, no randomness, no network — because
a reviewer running them to check a student's submission wants
reproducible results.

Reasonable minimum: typical case, empty case, one edge case that
reveals a specific misconception you expect students to have. Three is
usually enough; ten teaches the reviewer nothing new after the third.

## Common failure modes

- **Missing complexity criterion.** The stem says "O(n log n)" and the
  rubric grades only correctness. Small test cases pass on an O(n²)
  solution. The complexity target is dead weight in the stem. Fix by
  adding a rubric criterion for it, naming what the reviewer checks
  (usually: the student's own written analysis).
- **Vague reasoning requirement.** "Explain your solution" invites a
  paragraph the reviewer can't grade. "Explain in one sentence why
  your solution is O(n log n) rather than O(n²)" is graded easily.
- **AI stance mismatch between stem and class.** Coding class says AI
  allowed; stem says "no AI." Either the class is wrong or the stem is.
  Reconcile before finalizing.
- **Ungradeable submission format.** "Submit code and analysis" without
  saying where — Moodle text box? PDF? Repo link? Reviewer wastes time
  chasing formats. Name the format in the stem.
- **Interface not specified.** Student writes `def compute(...)` when
  the reviewer expected `def solve(...)`. Name the function signature
  in the stem when the reviewer expects to test-call anything.

## Phrasing

**Name the interface up front.** "Write a Python function
`solve(nums)` that returns …" — not "write code that computes …".

**When language matters, name it.** "Write a Python 3 function …"
prevents a student from turning in APL. When language is open, name
the constraints of the reviewer's environment (usually: "the reviewer
will run your code in Python 3.11" or equivalent).

**When complexity matters, put the bound in the stem.** Not "efficient"
— "O(n log n) time, O(n) space." Efficient means nothing to a first-year
student.

**When AI use is required to be documented, say what to include.**
"Attach the prompts you used and note one thing you changed from the
AI's response." Not "reflect on your AI use."
