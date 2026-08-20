---
description: Build the Google Gem bundle for a unit — instructions plus knowledge files
argument-hint: "<unit number, or 'course'>"
---

Build the Gem bundle for **$1** using the **gem-builder** agent.

The Gem is a study path students actually rely on, not an export afterthought — `kind: gem`
appears on nearly every guiding question, often as the fallback for a student with no textbook to
hand.

Read the unit's study sessions and `course.yaml` (`gem.scope`, `gem.tutoring_stance`) first.

Output goes to `exports/gems/`. Note that `exports/` is gitignored in the framework repo; if the
teacher wants the bundle versioned in their course repo, ask before changing that.

**Before finishing, state explicitly what you excluded and why.** The knowledge files are readable
by any student who has the Gem, so assessment items, teacher-facing misconception notes, and
homework solutions must not be in there. Silence about exclusions is not reassurance.

Remind the teacher the bundle is a draft for review. This is the most student-visible artifact the
framework produces and nobody should publish it unread.
