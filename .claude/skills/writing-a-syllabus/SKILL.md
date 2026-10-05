---
name: writing-a-syllabus
description: The standard for a course syllabus (syllabus/syllabus.md) — what makes a real Course Outcome rather than a topic label, a unit map ordered for home study, an honest workload and grading, a body that mirrors the institution's form, an AI-use policy, and how to revise a syllabus without undoing the teacher's edits. Use when drafting, revising or reviewing the syllabus — by syllabus-designer, by the chat during /plan-syllabus revision rounds, and by course-critic under /review-syllabus.
---

# Writing a syllabus

The syllabus is the course's top layer. A teacher establishes it before any unit — and often uploads
it to the university. Unit objectives roll up to its Course Outcomes, and `/plan-units` plans units
from its unit map. This skill is the one standard for it: the agent that drafts it, the chat that
revises it with the teacher, and the critic that reviews it all work to what is written here, so the
teacher never gets contradictory advice.

**Best effort, not a form to complete** (D-043). Draft as well as the evidence allows; the teacher
revises it in conversation or by hand, and approves it. Only `goal` and `outcomes` are required.
What the evidence does not support you **ask about, or leave out — never invent**.

The shape of the front matter is `schemas/syllabus.schema.json`. The methodology's numbers (minutes
per unit, sessions, the class meeting) come from `methodologies/<name>.yaml` — never assume them.

## Front matter — what tools and agents use

- **`goal`** — one paragraph: what the course is for and who it is for. From the old syllabus's aim
  where there is one, sharpened; not a list of subjects. A goal that would fit any course in the
  department says nothing.
- **`outcomes`** — `CO1`, `CO2`, …: what a student who passes can **do**, each one assessable.
  "Analyse the running time of a recursive algorithm", not "Recursion". The test: could an exam tell
  whether a student has it? As many as the course genuinely delivers — usually a handful, each
  spanning several units. An outcome per unit is a unit objective in the wrong layer; one so broad
  it covers the whole course says nothing. `bloom` where it is clear. If the old syllabus lists
  outcomes, start from them and say which you rewrote and why. **Once units reference the outcomes
  (`course/units/*/unit.md`), keep their ids**: renumbering breaks those references.
- **`unit_map`** — every unit, in order: `number`, `title`, a one-line `summary`, and `evidence` —
  the locators the plan for that unit rests on (`M0007#slide-1`, `M0003#page-12`). Write a locator
  only after you have seen its anchor in the ingested file (`## Slide 1`, `## Page 12`); one wrong
  locator sends `/plan-units` to the wrong place (`classkit validate` warns about one that does not
  resolve). A unit the evidence does not reach still goes on the map if the teacher named it, with
  no `evidence`. The number of units is `units` in `course.yaml`; if the evidence implies another
  number, that is a question for the teacher. **Order for home study, not for lectures**: a lecture
  can defer motivation ("we'll see why in three weeks"); a student alone with an unmotivated
  definition stops. Watch the load: three heavy units in a row with no consolidation is a real
  problem. **Every outcome should be built by some units, and every unit should serve some
  outcome** — name any that are not.
- **`workload`** — `credits` and `credit_system` only from the old syllabus or the teacher.
  `total_hours` likewise. What the methodology implies (minutes per unit × units) may be shown next
  to it, clearly as arithmetic, not as the institution's figure.
- **`prerequisites`** — course names or codes, from the old syllabus or the teacher.
- **`reading`** — `required` and `recommended`; a `textbooks` key from `course.yaml` where the book
  is listed there, else free text. Never an `audience: instructor` material (a solutions manual).
- **`assessment`** — the grading scheme, `[{type, weight, description}]`, from the old syllabus or
  the teacher, in their convention (percentages, usually). **Never invent weights.** If the old
  scheme pulls against a flipped course (no credit for the entry quizzes that make the class hour
  work; one final exam worth everything), carry it over as it was and say so — changing the grading
  is the teacher's decision.
- **`approved`** — never written or changed by you. Only `classkit approve syllabus` (or the
  teacher, by hand) writes it; keep it exactly as it is.

## Body — what only people read

The body is what the teacher uploads, so it **mirrors the institution's form**: the old syllabus's
sections, in its order, when one is ingested; otherwise the template's default skeleton (course
description, aim, learning outcomes, level/type/when offered, prerequisites, teaching methods,
schedule, workload, grading, reading, policies including AI use, staff and office hours). Write each
section as finished prose a student or a committee reads, in the course's `language`
(`course.yaml`). Keep the body **consistent with the front matter** — outcomes, schedule, workload,
grading and reading restate it in words.

- **Teaching methods** describes the flipped course as it will run, with the methodology's numbers:
  at-home study sessions built around guiding questions, then a class meeting that builds on them.
  Do not carry over "three lecture hours a week" from an old syllabus without saying so.
- **Schedule** is the unit map, week by week. Calendar specifics (holidays, exam dates) only where
  the evidence or the teacher gives them.
- **Identity** — title, code, instructors, textbooks — lives in `course.yaml`. A form's header
  section may restate it; `course.yaml` is the source.
- **An AI-use policy, always**, when the course uses an AI study path (a Gem among the study-path
  kinds, a Gem link in the materials, or the teacher says so) — the framework creates the need.
  Propose a concrete policy for the teacher to adjust: what students may use AI for (studying with
  the course Gem, checking understanding), what they may not (submitting AI-written work as their
  own, in quizzes and exams), how to acknowledge use. Mark it as a proposal; an institutional rule
  nobody gave you stays TBD.
- **The teacher's own old syllabus is their text**: carrying a section over as it was is fine, and
  often what the university expects. Say what was carried over and what was rewritten.

**What nobody knows yet stays visible**, never silently dropped and never filled with a plausible
guess: in the body, `**TBD:** <what is missing, and who decides>` ("**TBD:** office hours — the
teacher"); in the front matter, leave the field out.

## Revising — change what was asked, leave the rest

Most of a syllabus's life is revision: during `/plan-syllabus`, in conversation, all semester.

- **Re-read the file first.** The teacher may have edited it by hand; their edits are theirs — never
  revert them.
- **Change what was asked, and whatever must change with it to stay consistent** (an outcome
  reworded → its prose in the body too). Leave everything else as it was — including YAML comments
  and the `approved` block. Regenerating the whole file is never the default.
- **A request that conflicts with the rest**: make the change and say what now disagrees, rather
  than silently "fixing" the other part.
- **Every new factual sentence must trace to the teacher's words** — in this conversation or the
  course log — **not to last year's syllabus.** An old syllabus is evidence of what *was*; carrying
  one of its facts into a revision ("theoretical, 'dry' assignments") presents it as this year's.
  Read your own diff for such a sentence before you show it; if a fact is worth keeping, ask.
- **Show the change before writing it** (`classkit write … --diff`), then write it on the teacher's
  OK (`--overwrite`). An edit after approval is normal; `classkit status` will say "edited since".

## Rules

- **No invented facts or resources.** No credits, weights, policies, dates, office hours or
  prerequisites the evidence and the teacher did not give; no locator whose anchor you have not
  seen. A plausible syllabus that is wrong is worse than an honest one with TBDs: it may be
  uploaded.
- **Locators in full, always** — `M0005#page-39`, never `#page-39`.
- **Citing a book** — a page locator is the PDF's page (`M0003#page-63`), often not the printed
  one. Also give the book's own coordinates: chapter or section, and the printed page (the ingested
  file notes it under the page heading as *(printed page 45)*).
- **Never copy text from a private material** (D-042) — a published book, a solutions manual. Its
  table of contents gives the order; describe it in your own words and cite it by locator; at most
  a short phrase in quotation marks. `classkit doctor` flags 12 or more consecutive words shared
  with a private text.
- **Never point students at instructor-only material** (`audience: instructor`): not in `reading`,
  not in the body. It may still be evidence.
- **Say what you guessed.** The teacher judges the result on their real course; an honest "I could
  not tell" is what lets them correct it.
