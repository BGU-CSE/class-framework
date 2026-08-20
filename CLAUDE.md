# Working in this repo

Agent-facing context. Read `README.md` for what the project is; this file is about how to
work on it without breaking its invariants.

## Vocabulary — use these words, no synonyms

Two words are **banned** because each used to mean two things: **"topic"**, and bare
**"question"** (say *Guiding Question* or *Assessment Item*).

| Term | Meaning |
|---|---|
| **Unit** | One week's subject. 12–13 per semester. |
| **Unit Objective** | Abstract, teacher-facing goal. 2–4 per unit. Not the working layer. |
| **Study Session** | The ~25-min at-home unit. 4 per Unit. |
| **Guiding Question** | A session goal phrased as a question the student should be able to answer. 3–5 per session. **The atomic addressable unit.** |
| **Study Path** | A candidate route to answering a Guiding Question (gem / video / textbook / article / exercise), typed and time-estimated. |
| **In-Class Session** | The weekly 50-min meeting. Synonym: **Lesson Plan**. One per Unit. |
| **Activity** | A component of an In-Class Session. Has a duration; references ≥1 Guiding Question. |
| **Assessment Item** | A single quiz/homework/exam question. |

## ID conventions

Mechanically checked by the schemas and the validator.

```
U01              Unit
U01-O1           Unit Objective
U01-S02          Study Session
U01-S02-G1       Guiding Question   ← referenced by everything else
U01-IC           In-Class Session
U01-A1           Activity
U01-I01          Assessment Item
```

## Invariants — do not break these

1. **No course content in this repo.** No `course/` directory, no real units, no example
   course. Course content lives only in course repos, created by `classkit scaffold`. Tests
   build a throwaway course in `tmp_path` instead.
2. **Nothing hardcodes methodology numbers.** "4 sessions", "25 minutes", "3–5 questions",
   "50 minutes" are read from `methodologies/*.yaml`. A second methodology with different
   numbers must work without code changes.
3. **Downstream consumes `goals[]`, never the methodology.** The study-session schema is the
   contract between a methodology and everything else. Code that branches on
   `methodology.id == "question-driven-25"` is a bug.
4. **Every Activity references ≥1 Guiding Question.** This is not decoration — it is the
   structural reason the class hour cannot revert to a lecture. Never relax it to make a
   validation pass.
5. **Scaffolding never overwrites.** `write_new()` is the only way scaffold touches disk.
6. **Templates must validate.** A fresh scaffold has to produce a course with zero errors,
   or `tests/test_course_lifecycle.py` fails. Change a schema → change the template.

## Where things live

```
schemas/*.schema.json     the content contract (JSON Schema draft 2020-12)
methodologies/*.yaml      pluggable study-session designs
defaults/time-constants.yaml   how long a study path is assumed to take
templates/                what scaffold copies into a course repo
src/classkit/
  frontmatter.py          Markdown + YAML front-matter parsing
  model.py                locating and loading a course tree
  scaffold.py             create-only content generation
  validate.py             schema layer + semantic rules
  cli.py                  argparse entry point
tests/                    scaffold → validate round-trip
_devlog/                  build log — decisions, progress, open questions
```

## Before changing anything structural

Read `_devlog/01-decisions.md`. Locked decisions are not to be relitigated; several
constraints that look arbitrary have a recorded reason. `_devlog/03-open-questions.md`
lists what is genuinely undecided.

## Adding a validation rule

Add the check to `Validator`, give it a code, and put its default severity in
`DEFAULT_SEVERITY` if it is not an error. Methodologies override severities in their
`rules:` block. Every rule needs a test in `tests/test_course_lifecycle.py` that breaks a
scaffolded course and asserts the code fires — a rule that never fires is worse than no rule.

## Running things

```bash
pip install -e ".[dev]"
pytest
```

`classkit validate` needs a course, so it does nothing useful in this repo. Test against a
throwaway scaffold in a temp directory.

## Not built yet (Phase 1+)

The agent layer, the flip pipeline (`ingest → plan-flip → author-prework → author-session →
qa-review`), PPTX export, and Gem export. Do not assume any of it exists.
