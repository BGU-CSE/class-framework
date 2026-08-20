# Source materials

**Put your existing course materials in this directory.**

This is the main input to `/ingest` and to the curriculum-architect agent. They read what's here
to work out what your course actually covers — so that the flipped version is a redesign of *your*
course rather than a generic one assembled from the topic name.

## What to put here

Anything you already have. Format doesn't matter.

- The current syllabus
- Lecture slides (PPTX, PDF)
- Lecture notes, handouts, worked examples
- Reading lists
- Past homework and exams — useful for calibrating level and seeing what you actually assess
- Anything that records which topics students reliably struggle with

Subdirectories are fine. Organize it however you like.

## What agents do with it

They read it. They don't modify it. Nothing here is published to students, and nothing is copied
into the course automatically — designed content is written to `units/` and `assessments/`, and
you review it there.

## If this directory is empty

`/ingest` will stop and ask you to add something rather than inventing a course. That's
deliberate: a course designed from nothing but a title looks plausible and is wrong in ways that
are expensive to find later.

## A note on the textbook

If your textbook isn't a file you can drop here, record it in `course.yaml` under `textbooks:`
instead. Study paths cite it by key, e.g. `ref: "CLRS ch.3 pp.45-52"`.

## Confidentiality

Past exams here live in your course repo's git history permanently. If that repo is shared with
anyone — a TA, a co-teacher — treat anything you add here as visible to them.
