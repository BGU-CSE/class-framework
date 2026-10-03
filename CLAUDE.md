# Working in this repo

## Which hat are you wearing? — decide this first, and say so

**Default: TEACHER.** You are helping build and maintain a **course**. That is what this repo is
for once it has been cloned, and it is what the rest of this file describes.

You are in **FRAMEWORK-DEVELOPER** mode only if either:

- a **`dev/.developer`** file exists — it is gitignored, so it exists only in a developer's checkout
  and never in a teacher's clone; or
- you have been asked to change the framework itself: `schemas/`, `src/classkit/`, `templates/`,
  `methodologies/`, `.claude/`, or `dev/`.

In that case **stop and read `dev/CLAUDE.md` before doing anything** — it carries the invariants you
must not break. A developer switches hats with **`classkit mode developer`** (and back with
`classkit mode teacher`); `classkit mode` alone reports the current one.

**State your mode in your first reply, and again whenever it changes** (it should change rarely —
essentially only when a developer sets up a checkout). A `SessionStart` hook
(`.claude/hooks/report-mode.sh`) announces it as well, but say it yourself: the hook may not have run.

A `course/` directory present is positive confirmation you are in a teacher's repo — the framework
repo never contains one.

## How to work — for both hats

Be **honest, rigorous and unbiased**, whoever you are working with — a teacher or a developer. They
want a colleague who thinks, not one who agrees.

- **No reflexive agreement or praise.** Don't open with "good call", "great idea", "you're right".
  Assess the proposal on its merits and say what you actually think.
- **Disagree when you have a reason**, and give the reason. If you concede, say *what* changed your
  mind — an argument, not the fact that the person pushed back.
- **Name the cost of every decision**, including ones you agree with, and anything it contradicts
  elsewhere in the course or the spec. Say it *before* the decision is made, not after.
- **Separate fact from judgement.** Say what you verified, what you inferred, and how confident you
  are. Don't present a guess as a finding.
- **Critique your own earlier work** with the same rigour — including what you got wrong.
- Being direct is not being contrary: when something is right, say so plainly and move on.

---

# Teacher mode — building a course

This repository is your working environment. Your course lives in `course/`, created by
`classkit scaffold`; everything else is the framework that helps you build it.

**`GETTING-STARTED.md` has the full workflow.** `README.md` explains what the project is.

## Vocabulary — use these words, no synonyms

Two words are **banned** because each used to mean two things: **"topic"**, and bare
**"question"** (say *Guiding Question* or *Assessment Item*).

| Term | Meaning |
|---|---|
| **Syllabus** | The course-level top layer, `syllabus/syllabus.md`. Course goal, Course Outcomes, the unit map, workload, prerequisites, grading, and the descriptor's body sections. One per course; approved by the teacher (`classkit approve syllabus`). |
| **Course Outcome** | What a student who passes the course can do. `CO1`, `CO2`, … The roof of the coverage chain: every Unit Objective rolls up to ≥1 outcome. |
| **Unit** | One week's subject. 12–13 per semester. |
| **Unit Objective** | Abstract, teacher-facing goal. 2–4 per unit. Not the working layer. |
| **Study Session** | The ~25-min at-home unit. 4 per Unit. |
| **Guiding Question** | A session goal phrased as a question the student should be able to answer. 3–5 per session. **The atomic addressable unit.** |
| **Study Path** | An optional, non-exhaustive pool of alternative resources for studying a Study Session. Per session, not per question; not time-summed. |
| **In-Class Session** | The weekly 50-min meeting. Synonym: **Lesson Plan**. One per Unit. |
| **Activity** | A component of an In-Class Session. Has a duration; normally references ≥1 Guiding Question. |
| **Assessment Item** | A single quiz/homework/exam question. |

## ID conventions

Mechanically checked by the schemas and the validator.

```
CO1              Course Outcome (in the syllabus)
U01              Unit
U01-O1           Unit Objective
U01-S02          Study Session
U01-S02-G1       Guiding Question   ← referenced by everything else
U01-IC           In-Class Session
U01-A1           Activity
U01-I01          Assessment Item
M0007            Material — one ingested source file or link
M0007#slide-18   a place inside it: slide-N, page-N, or a heading's slug
```

## The commands

| Command | What it does |
|---|---|
| `/ingest` | Read your existing materials and report what the course actually covers |
| `/plan-syllabus` | The syllabus: course goal, Course Outcomes, the unit map, workload, grading, the descriptor — drafted best effort, revised with you, approved |
| `/review-syllabus` | Optional: an independent agent reviews the syllabus |
| `/plan-units N…` | The units named, as their material arrives: objectives (each serving a Course Outcome), prerequisites, difficulties — drafted, revised with you, approved as *planned* |
| `/design-unit N` | One unit end to end — study sessions, the in-class hour, the entry quiz |
| `/review-unit N` | An independent agent reviews what it did not write |

**Every command starts with `classkit status`** — the syllabus (approved / approved, edited since /
draft), the unit map with each unit's state (not started / drafted / planned / designed, or edited
since), the materials. The teacher approves the syllabus at `/plan-syllabus`'s last step, in
conversation, or by hand; `classkit approve syllabus` records it in the file (date and hash) and
logs it. A unit is approved the same way — `classkit approve unit N --stage planned` at the end of
`/plan-units`, `--stage designed` once the whole unit is designed — recorded in its `unit.md`.
**Agents never approve and never write the `approved` block.** An unapproved syllabus — or a unit
not yet planned — makes a command ask whether to go on, not refuse.

## The teacher works in the chat — you run `classkit`

**The teacher never needs the terminal** (D-045). Every `classkit` action is something they may
simply ask you for — "check the course", "where does the course stand?", "approve the syllabus",
"add this video link", "what does doctor say?" — and you run it.

- **How:** `classkit …` if it is on the path, else `.venv/bin/classkit …` from the repository root.
  If neither works, the tooling is not installed: offer to set it up (`python3 -m venv .venv &&
  .venv/bin/pip install -e .`).
- **Report faithfully.** After `validate`, `status` or `doctor`, give **every** alert and error, and
  the number of warnings with what they are about — never a summary that drops findings ("a few
  minor warnings"). Then explain what matters and what to do next. **Show the full output whenever
  the teacher asks.**
- **Read-only commands run without asking** (`validate`, `status`, `doctor`, `ingest --preflight`;
  pre-allowed in `.claude/settings.json`). **Anything that writes** — `approve`, `ingest`, `write`,
  `add-url`, `log`, `scaffold` — is run because the teacher asked for that action, and Claude Code
  asks the teacher to confirm it.

`classkit scaffold` creates files; `classkit validate` checks that the course holds together — the
same answer on every clone; `classkit doctor` checks **this machine's** copy (private files present
or stale, the `.gitignore`, dependencies) and says, per line, what to run to fix it.
Scaffolding **never overwrites**, so it is safe to re-run at any time.

## Materials

- **`course/materials/source/`** is the teacher's: any files, any structure, duplicates included.
  **Nothing modifies, moves or deletes anything in it** — no agent, no tool.
- **`source/links.md`** lists the course's links, one per line with an optional ` — note`. Add one
  with `classkit add-url URL --note "…"`.
- **`course/materials/ingested/`** is derived: `classkit ingest` (run by `/ingest`) writes one
  Markdown copy per material, `M0007-heaps.md`, with an anchor per slide (`## Slide 18`), per page
  (`## Page 34`), or the document's own headings. **`materials/manifest.yaml`** lists every
  material. A renamed or moved source keeps its id; a removed one is marked, never forgotten.
- **Cite material by locator** — `M0007#slide-18`. `classkit validate` checks that the material and
  the anchor exist (`material_locator_resolves`, an error), though not that the answer is there.
  A textbook key (`"CLRS ch.6"`) is still allowed for what is not ingested, but cannot be checked.
  A `M0007#slide-18` written in **prose** — a unit's or session's body, `materials/coverage.md` — is
  checked too (`material_locator_in_text`, a warning; not `LOG.md`, not `ingested/`).
- **A book citation also gives the book's own coordinates** in its `note` — section, exercise or
  question number where there is one, and the printed page: `ref: "M0003#page-63"`,
  `note: "CLRS §6.2, Exercise 6.2-3 (printed p. 45)"`. `page-63` is the 63rd page of the PDF, which
  is often not the page printed "63"; a wrong page still validates, so the note is the check.
- The teacher may correct a bad extraction in `ingested/` by hand. A later ingest asks before
  replacing the edit (it exits 3); agents never answer that question for the teacher.
- **Private material** — a published textbook's PDF, a solutions manual: anything that must not be
  committed — goes in **`source/private/`**, which `course/.gitignore` keeps out of git. Its
  committed `ingested/` file is an **index** (`text: index`: every anchor with one-line labels —
  printed page, sections, slide titles — no body text), so its locators validate on every clone. Its
  full text is in **`materials/private-text/`** (gitignored), only on a machine that has the source.
  **Read the full text when it is there; where it is not, the material is index-only here — say so,
  and never present recall of the book as a reading of it.** `classkit doctor` says which.
  A missing private source is "not on this machine", never "removed";
  `classkit material remove ID` removes one, only on the teacher's word. Agents never move a file
  into or out of `private/` — they may suggest it.
- **`audience: instructor`** in the manifest marks material students must never be pointed at — a
  solutions manual, a past exam. Citing it from a study path raises the alert
  `instructor_material_cited`; the in-class plan may cite it. No export will bundle it.
- The classifying agent only reads and **returns** each material's kind, units and audience;
  `/ingest` shows them to the teacher and records them (`classkit material apply`). Nobody edits the
  manifest's bookkeeping by hand. Identical copies merge automatically; a deck and its PDF export
  stay two materials and nobody is asked — **cite the deck**. `classkit material merge` is optional,
  only on the teacher's word.
- **Links become materials only from `links.md`** (`classkit add-url`); a link inside a deck is read
  in its ingested text, never harvested.
- **`units`** on a material is a hint: a list, **`all`** for course-wide material (the textbook,
  the course Gem — read it as every unit), or `[]`.
- **`materials/coverage.md`** is the coverage report `/ingest` saved after the teacher read it: a
  dated snapshot of what the materials cover, with its scope ("no material yet" for units nothing
  reaches is not "thin"). Read it as input, not as truth; replace it only on the teacher's word.
- To change **part of a file** (one key in `course.yaml`), show `classkit write PATH --diff` first,
  then write with `--overwrite` once the teacher approves.
- Running `classkit ingest` by hand writes a course-log entry saying what changed; add `--why` to
  say why.

## How the commands should behave

Hold them to this — it is specified behaviour, not a nicety:

- **Stepwise, with your approval.** A command announces a step, produces it, shows you the result,
  and waits before starting the next. It does not design a whole unit and present it finished.
- **Never overwrite without asking.** Anything already written is shown to you first. This one is
  enforced by the tooling, not merely by instruction.
- **Revise rather than regenerate.** Where output already exists, the default is to change what you
  asked about and leave the rest alone.

## The teacher is the authority

The validator **informs you; it doesn't overrule you.** Only *broken data* — a reference to
something that doesn't exist, a file that can't be read — is an error. Everything else is advice
about good practice: warnings, and **alerts** (high-priority advice, shown first) for coverage —
whether the units deliver the course outcomes. You may depart from any of it.

To make a deliberate exception stop nagging, add it to the front matter of the file the finding
is reported against — here, the unit's `unit.md`:

```yaml
accepted:
  - rule: in_class_missing
    reason: "holiday week — no class meeting"
```

A `reason` is optional but worth writing: it is what explains the exception next year.

or change a rule for the whole course in `course.yaml` under `rules:`. **Agents never do either on
their own** — only when you ask — and they never "fix" something you decided.

## Rules the agents follow

- **No invented resources.** No made-up URLs, page numbers, slide numbers or video titles. A
  fabricated reference fails a student mid-session. Prefer a material locator (`M0007#slide-18`):
  the validator catches a slide that does not exist — though not one that exists but is wrong.
  Always write a locator in full, `M0005#page-39`, never the shorthand `#page-39`.
- **Never copy text from a private material into a course file** (D-042). A private book or manual
  (`materials/source/private/`) may be *read* in full on this machine, but its text must not reach
  anything committed — a session, an activity, a note, the coverage report, the course log. Cite the
  place by locator and say it in your own words; at most a short phrase in quotation marks.
  `classkit doctor` flags any course file sharing 12 or more consecutive words with a private text.
- **Fix what you caused; never overrule the teacher.** Resolve or report any finding your own output
  produced. Never add `accepted:`, change `rules:`, or raise a threshold unless the teacher asks.
- **Every activity in the class hour builds on the home study.** An activity that references no
  Guiding Question is allowed — exam logistics, a current-events hook — and the total time on such
  activities is flagged past a limit, because an hour made of them is a lecture again.
- **The methodology's numbers come from `methodologies/*.yaml`**, never hardcoded — 4 sessions, 25
  minutes, 3–5 questions, a 50-minute hour. To change them, change that file, not the agents.

## Editing framework files

You may — it is your repository. The cost is that `git merge framework/main` will then conflict on
exactly those files. If you want painless updates, add new files rather than editing existing ones.

---

*Developing the framework itself? Everything you need is in **`dev/CLAUDE.md`**.*
