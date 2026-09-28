---
id: {{item_id}}
unit: {{unit_id}}
format: numeric
guiding_questions: [{{unit_id}}-S01-G1]
usage: [homework]
difficulty: medium
bloom: apply
est_minutes: 5
stem: "TODO — state the expected units in the stem."
model_answer: "42"
tolerance: 0.01
measurement_units: "ms"
---

Notes: state the expected unit in the stem AND in the metadata. A student
answering '0.042' when the answer is '42 ms' is right about the number and
confused about the unit — that's a diagnosis, not a wrong answer, and the
grading needs to reflect that.

Use `tolerance` for absolute tolerance around the answer. For answers whose
acceptable range should scale (e.g. "within 5% of the true value"), use
`tolerance_pct: 5` instead. Do not set both.