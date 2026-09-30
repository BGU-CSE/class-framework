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
# due_date: 2026-11-15               # optional; printed on the student document (HW-D30)

# Where this homework came from.
source:
  kind: material                     # material | quiz_report — 'material' = grounded in course materials, no specific quiz
  # ref: EQ-U03                      # required if kind is quiz_report (id of the source quiz)
                                     # the report is given in the session, never stored here (HW-D33)

# Items in this homework. References only — items live in course/assessments/items/.
# Every referenced item file must have `homework` in its `usage` array.
items:
  - {{unit_id}}-I01                  # e.g. U03-I01
  # - U03-I02
  # - U03-I05

# Tool policy for the whole homework. Must be declared in course.yaml's tools map.
allowed_tools: [pen_and_paper]

# Tools a specific item needs — optional (HW-D28). Several per item are fine;
# a programming language counts as a tool. Each tool must be declared in
# course.yaml's tools map; each key must be an item of this homework.
# item_tools:
#   U03-I05: [wireshark, gns3]
#   U03-I07: [python]

# Collaboration policy.
# forbidden       — students work alone
# discussion_only — students may discuss but each submits their own work
# allowed         — students may collaborate fully
collaboration: discussion_only

open_book: true                      # true | false

# Versions — optional, targeted (HW-D26). Used when a quiz report shows that
# groups of students struggled with different Guiding Questions. Requires
# source.kind: quiz_report with a ref. Every student gets the shared `items`
# above plus the items of their version.
# - label: unique; never a student name or identifier
# - targets: the Guiding Questions this version remediates (declared units only)
# - items: each must test at least one of the targets and nothing outside them;
#   every target needs at least one item; an item may appear in several versions
# Which student gets which version is kept outside this repository.
# versions:
#   - label: A
#     targets: [U03-S01-G1, U03-S01-G2]
#     items: [U03-I06, U03-I07]
#   - label: B
#     targets: [U03-S02-G1]
#     items: [U03-I08]

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
