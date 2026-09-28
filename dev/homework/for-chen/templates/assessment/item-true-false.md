---
id: {{item_id}}
unit: {{unit_id}}
format: true-false
guiding_questions: [{{unit_id}}-S01-G1]
usage: [in-class-quiz]
difficulty: easy
bloom: understand
est_minutes: 1
stem: "TODO — a specific claim that is either true or false, not a general statement."
choices:
  - label: T
    text: "True"
    correct: true
    rationale: "Why the claim is true. This rationale is the whole learning payload for a T-F item — write it carefully."
  - label: F
    text: "False"
    correct: false
    rationale: "The misconception a student holds if they mark it false."
---

Notes: true-false is the weakest format for diagnosis — a coin flip earns 50%.
Use only when the claim itself is worth interrogating: a canonical
misstatement students often accept. The rationale carries all the value, not
the choice. If the claim is false, flip which option has `correct: true` and
keep the same rationale structure.
