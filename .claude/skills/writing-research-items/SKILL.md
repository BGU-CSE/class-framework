---
name: writing-research-items
description: How to write a Research-class assessment item. Loaded by homework-item-writer (and item-critic) when the plan slot's item_class is `Research`. Governs mini-research tasks where students use an AI assistant to investigate a research question, then critique, synthesize, or extend. Covers stem framing, rubric criteria for AI-assisted work, and the failure modes specific to this class.
status: ratified
---

# Writing research items

A Research item asks the student to investigate a research question with the help
of an AI assistant, then produce something the AI couldn't have produced
alone: a critique, a synthesis across sources, an extension into new
territory, or a judgment call the AI wouldn't make.

## The one rule that matters

**Grade the student's engagement with the AI's output, not the AI's
output itself.** A student who pastes an AI's answer verbatim and calls
it done should not pass, no matter how correct the AI was. A student
who noticed a subtle error in an otherwise-good AI answer and articulated
it clearly should pass, even if the rest of their answer leans on the
AI.

The failure mode to watch for: writing an item whose rubric can be
satisfied by a competent AI alone. If a strong AI, given the stem and
no student in the loop, could earn a passing score, the item is not a
Research item — it's an AI benchmark, and the student has no reason to
engage. Fix by adding rubric criteria the AI genuinely cannot satisfy:
disagree with a specific claim, connect the subject to material from a
prior unit, identify a case the AI didn't consider.

## Stem structure

A well-formed Research stem has three parts:

1. **The research question to investigate.** Specific enough that a
   good investigation has a shape ("evaluate whether LSM-trees are a
   good fit for a write-heavy time-series database"), not vague
   ("research databases").

2. **The AI-use expectation.** "Use an AI assistant to..." — makes
   explicit that AI is a tool, not an adversary to avoid. Optionally
   name which AI (the class Gem is a common choice, since it can be
   tuned for course context).

3. **The deliverable beyond the AI's output.** What the student
   produces that the AI didn't. "Submit the AI's response, your
   critique of it, and one alternative the AI didn't consider" is
   concrete. "Reflect on what the AI said" is not.

## Rubric criteria

Weight the rubric toward what the student did, not what the AI produced:

- **Investigation quality** — did the student ask specific enough
  questions? Iterate when the AI gave a shallow answer? Get to the
  substance of the subject, or stop at surface?
- **Critique specificity** — did the student point at something
  concrete the AI said and evaluate it, or wave vaguely at "the AI's
  response"? Criteria should reward a student who names the AI's
  paragraph 3 sentence 2 and disagrees with it.
- **Synthesis or extension** — did the student produce something not
  in the AI's output? A comparison to a prior unit's material, an
  application to a new case, a judgment the AI hedged on.
- **AI's output quality (optional, low weight)** — sometimes worth a
  criterion, because a student who couldn't get a good AI answer out
  of any prompt has an investigation-quality problem. But keep the
  weight low; the grade is about the student.

Never award points just for "used AI." AI use is the medium, not the
demonstration.

## Common failure modes

- **Unfalsifiable prompts.** "Research the history of hash tables and
  write what you learned." A student pasting the AI's answer verbatim
  meets this brief. Fix: name what the AI-alone answer would look
  like ("the AI will produce a chronological summary; your submission
  should identify one factual claim you verified independently and
  one you couldn't").
- **Grading the AI, not the student.** If the rubric's top-scored
  submission is one where the AI happened to give a great answer,
  the item measures AI quality, not student learning. Rework criteria
  to reward student judgment even on weaker AI outputs.
- **No submission of the AI interaction.** If the deliverable is only
  the student's final answer, there's no way to check whether the
  student actually engaged or just pasted. Require the prompts and the
  AI's responses in the submission.
- **AI-use forbidden by class conflict.** A stem that says "don't use
  AI" in a Research-class item contradicts the class definition. If
  the teacher wants a no-AI investigation, the class is `Practicing`,
  not `Research`.
- **Answers the AI can't actually help with.** A Research task about
  a subject the AI has no training data on (a specific paper published
  last week, a specific dataset the teacher owns) will produce
  frustrated students. Sanity-check by attempting the item with an AI
  yourself before finalizing.

## AI-use guidance in the stem

Make the AI's role explicit in the stem, not implicit in the class label.
Students see the stem; they may not know what "Research class" implies.

- Name which AI is expected or allowed. "Use the class Gem" or "any AI
  assistant is fine" — both work, name one.
- Name what to submit from the interaction. "Include your prompts and
  the AI's full response as an appendix" is the cleanest.
- Name what NOT to do. "Do not submit the AI's response as your answer"
  saves the awkward conversation where the teacher explains this
  after grading.

## Phrasing

**Use imperative verbs the AI can't satisfy.** Investigate, evaluate,
critique, extend, disagree, judge, choose, defend. Avoid summarize,
describe, list — those the AI does better than the student and
grading either becomes vacuous.

**Bound the investigation.** "Investigate X" is unbounded. "Investigate
X using two sources beyond what the AI cites, and identify one point of
disagreement between them" is bounded. Students finish; graders can
grade.

**When the item is time-budgeted, name the time the investigation
should take, not the reading.** A Research item's `est_minutes` should
count the investigation-plus-writing time, not any reading the student
does before starting. Read the class's `typical_minutes` in
`item-classes.yaml` as the anchor; per-item overrides are fine.
