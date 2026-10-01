# Source materials

**Put your existing course materials in this directory.**

This is the input to `/ingest`. It reads what's here and works out what your course actually
covers — so that the flipped version is a redesign of *your* course rather than a generic one
assembled from the subject's name.

## What to put here

Anything you already have, in any state. It does not need to be organized — one folder of
everything is fine, and so is a tidy tree. Duplicates (a deck and its PDF export) are detected.

- The current syllabus
- Lecture slides (PPTX, PDF)
- Lecture notes, handouts, worked examples
- Reading lists
- Past homework and exams — useful for calibrating level and seeing what you actually assess
- Anything that records which subjects students reliably struggle with

**Videos and web pages** go in `links.md`, one per line with an optional note — or run
`classkit add-url URL --note "…"`.

## Which formats are read

| Format | How |
|---|---|
| `.pptx`, `.pdf` (with a text layer), `.docx`, `.md`, `.txt` | built in |
| `.odt`, `.rtf`, `.html`, `.epub` | if [pandoc](https://pandoc.org) is installed |
| `.ppt`, `.doc`, `.odp` | if LibreOffice is installed |
| anything else | recorded as *unsupported*, listed in the report — export it to PDF and re-run |

A scanned PDF with no text layer is recorded as *no-text* (it would need OCR), and audio and video
files as *media*: recorded, not read. Nothing is silently dropped.

## What `/ingest` does with it

**It never modifies, moves or deletes anything in this directory.** It writes a readable copy
of each file to `../ingested/`, one Markdown file per material, named by a stable id —
`M0007-heaps.md` — with every slide and page marked (`## Slide 18`, `## Page 34`). An answer
reference can then point at **`M0007#slide-18`**, and `classkit validate` checks that slide
exists. Its list of everything ingested is `../manifest.yaml`.

- **Reorganize freely.** A renamed or moved file keeps its id — it is matched by content — so
  references to it do not break.
- **Fix a bad extraction by hand** in `../ingested/`. A later ingest notices the edit and asks
  before replacing it.
- **Add material any time** and run `/ingest` again; only what is new or changed is processed.
- **A deleted file** is marked as removed in the manifest, not forgotten, so any reference to it
  is reported instead of quietly pointing at nothing.

Before converting anything, `/ingest` shows you a pre-flight report — how many files of each
format, slides and pages, duplicates, links, what it cannot read, and roughly how long it will
take — and waits for your go-ahead.

## If this directory is empty

`/ingest` will stop and ask you to add something rather than inventing a course. That's
deliberate: a course designed from nothing but a title looks plausible and is wrong in ways that
are expensive to find later.

## A note on the textbook

If your textbook isn't a file you can drop here, record it in `course.yaml` under `textbooks:`
instead. References cite it by key, e.g. `ref: "CLRS ch.3 pp.45-52"` — allowed, but the
validator cannot check it the way it checks `M0007#page-34`.

## Confidentiality — `private/`

Everything here is committed to your course repo — the file and its full ingested text — and stays
in its git history even if deleted later. If the repo is shared with anyone, a TA or a co-teacher,
treat what you add here as visible to them.

**What must not be committed goes in `private/`** (create the folder): a published textbook's PDF,
a publisher's slides, a solutions manual. `course/.gitignore` keeps it out of git. For each file
there, `/ingest` commits only an *index* — its pages or slides with their labels and sections, no
text — so citations to it are still checked; the full text stays on your machine, in
`../private-text/`. A clone without the file can cite the book but not read it. `classkit doctor`
says what this machine has.

Who may *see* a material is separate from where it is: mark a solutions manual or a past exam
`audience: instructor` (the `/ingest` agent proposes it, you confirm), and a study path that points
students at it is flagged.
