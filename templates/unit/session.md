---
id: {{session_id}}
unit: {{unit_id}}
number: {{session_number}}
title: "{{session_title}}"
duration_minutes: {{session_minutes}}

# {{goals_min}}-{{goals_max}} goals. Under question-driven-25 each `prompt` is a QUESTION
# the student should be able to answer after this session. Not a topic label —
# "Why is amortized append O(1) when some appends cost O(n)?" rather than "Amortized analysis".
#
# `paths` are CANDIDATE routes. The student picks one; none is mandatory. At least one
# complete path through all goals should fit inside duration_minutes, or the validator warns.
goals:
  - id: {{session_id}}-G1
    type: question
    prompt: "TODO — phrase as a question the student should be able to answer"
    objectives: [{{unit_id}}-O1]
    paths:
      - kind: gem
        ref: "{{unit_id}}"
        est_minutes: 6
      - kind: textbook
        ref: "TODO — e.g. 'CLRS ch.3 pp.45-52'"
        est_minutes: 8
  - id: {{session_id}}-G2
    type: question
    prompt: "TODO"
    objectives: [{{unit_id}}-O1]
    paths:
      - kind: gem
        ref: "{{unit_id}}"
        est_minutes: 6
  - id: {{session_id}}-G3
    type: question
    prompt: "TODO"
    objectives: [{{unit_id}}-O2]
    paths:
      - kind: gem
        ref: "{{unit_id}}"
        est_minutes: 6
---

# {{session_title}}

Optional framing for the student — why this session matters and how it connects to the
previous one. Keep it short; the goals above carry the work.
