---
# Homework manifest. Validated against schemas/homework.schema.json.
# Most homeworks should be created via /create-homework rather than hand-written —
# the pipeline plans coverage, runs critic and solver review, and updates defaults.
# This template exists for teachers who need to hand-write a manifest (e.g. for
# a legacy homework being migrated, or a special case the pipeline doesn't handle).

id: {{homework_id}}                  # e.g. HW01, HW02

# What this homework covers.
units: [{{unit_id}}]                 # unit ids; array of one or more
purpose: practice                    # practice | graded | diagnostic
total_minutes: 90                    # time budget for the whole homework

# Where this homework came from.
source:
  kind: material                     # material | quiz_report — 'material' = grounded in course materials, no specific quiz
  # ref: EQ-U03                      # required if kind is quiz_report (id of the source quiz)

# Items in this homework. References only — items live in course/assessments/items/.
# Every referenced item file must have `homework` in its `usage` array.
items:
  - {{unit_id}}-I01                  # e.g. U03-I01
  # - U03-I02
  # - U03-I05

# Tool policy for the whole homework. Must be declared in course.yaml's tools map.
allowed_tools: [pen_and_paper]

# Collaboration policy.
# forbidden       — students work alone
# discussion_only — students may discuss but each submits their own work
# allowed         — students may collaborate fully
collaboration: discussion_only

open_book: true                      # true | false

# When solutions and rubrics are released to students.
# with_homework  — released alongside the assignment (practice only!)
# after_deadline — released after the submission deadline
# never          — not released; students see grades but not the model
# Graded homework may NOT use with_homework (enforced by graded_answer_release_safe).
answer_release: after_deadline

# Prerequisites — earlier units the student needs to have completed.
# Every prerequisite must be a unit id from earlier in the course sequence.
prerequisites: []
  # - U01
  # - U02

# Versions — optional. Only used when this homework has grouped variants
# (e.g. take-home exam with different problem sets per group).
# Each version needs a label and the items specific to that version.
# The `items` array above contains the shared/common items.
# versions:
#   - label: A
#     items: [U03-I06, U03-I07]     # Version A gets its own regular item ids
#   - label: B
#     items: [U03-I08, U03-I09]     # Version B gets different ids — item ids match ^U\d{2}-I\d{2}$

# Status of this manifest. Draft currently marks work-in-progress for teachers
# and tooling, but the Python validator still treats draft and shipped files
# identically. Draft-aware validation is target behavior, not implemented yet.
# /create-homework writes files as draft and strips this field on Gate 2 approval.
# Remove this line (or set to shipped) when the homework is finalized.
# status: draft
---

# Homework body (optional prose)

Any teacher-facing notes about this homework — the rationale, the
pedagogical target, notes for a future revision. Not shown to students;
the student view is generated from the referenced items and metadata.
