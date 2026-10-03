---
id: {{unit_id}}
number: {{unit_number}}
# The title is also in the syllabus's unit map — keep the two the same
# (`classkit validate` warns when they differ: unit_map_mismatch).
title: "{{unit_title}}"
summary: ""
prerequisites: []
objectives:
  # {{objectives_min}}-{{objectives_max}} Unit Objectives. Teacher-facing and abstract —
  # the working layer is the Guiding Questions in sessions/. Each names the Course
  # Outcome(s) of the syllabus it serves — /plan-units fills these in.
  - id: {{unit_id}}-O1
    statement: "TODO"
    bloom: understand
    outcomes: [CO1]
  - id: {{unit_id}}-O2
    statement: "TODO"
    bloom: apply
    outcomes: [CO2]

# DIFFICULTIES — optional: what students find hard in this unit. Add them whenever you
# know them (after teaching the unit once is fine). `origin: proposed` marks one an agent
# suggested and you accepted — still a guess about your students.
# difficulties:
#   - text: "Students read O(n) as an exact running time rather than an upper bound."
#     origin: teacher

# APPROVAL — written by `classkit approve unit {{unit_number}}` (date, stage, hash), or by you
# by hand (`approved: {date: 2026-10-05, stage: planned}`). `planned` once the objectives
# are approved; `designed` once the whole unit is. Editing afterwards is normal.
---

# {{unit_number}}. {{unit_title}}

Teacher notes for this unit. Not student-facing.

## Home study ({{home_minutes}} min)

See `sessions/` — {{sessions_per_unit}} study sessions of ~{{session_minutes}} min.

## In class ({{in_class_minutes}} min)

See `in-class.md`.
