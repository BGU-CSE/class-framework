---
id: {{unit_id}}-IC
unit: {{unit_id}}
title: "{{unit_title}} — in class"
duration_minutes: {{in_class_minutes}}

# The weekly meeting. Every activity MUST reference at least one Guiding Question from
# this unit's study sessions — that requirement is what stops the hour turning back into
# a lecture. If an activity has nothing to reference, it does not belong here.
#
# Durations must sum to duration_minutes (within the methodology's tolerance).
activities:
  - id: {{unit_id}}-A1
    type: quiz
    title: "Entry quiz"
    duration_minutes: 8
    guiding_questions: [{{unit_id}}-S01-G1]
    items: []
    grouping: individual
    notes: "Short. Its purpose is to surface misconceptions for the next activity."

  - id: {{unit_id}}-A2
    type: discussion
    title: "Misconception debrief"
    duration_minutes: 12
    guiding_questions: [{{unit_id}}-S01-G1]
    grouping: plenary
    notes: "Driven by what the entry quiz just revealed."

  - id: {{unit_id}}-A3
    type: worked-example
    title: "TODO"
    duration_minutes: 12
    guiding_questions: [{{unit_id}}-S02-G1]
    grouping: plenary

  - id: {{unit_id}}-A4
    type: group-work
    title: "TODO"
    duration_minutes: 13
    guiding_questions: [{{unit_id}}-S03-G1]
    grouping: small-group

  - id: {{unit_id}}-A5
    type: synthesis
    title: "Wrap-up"
    duration_minutes: 5
    guiding_questions: [{{unit_id}}-S04-G1]
    grouping: plenary
---

# {{unit_title}} — lesson plan

Teacher-facing notes: what to watch for, common misconceptions, fallbacks if the entry
quiz shows the prework did not land.
