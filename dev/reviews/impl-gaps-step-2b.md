# Implementation gap report — step 2b (ingest)

**Date:** 2026-10-01
**Implementer:** Claude Opus 5.5, working from `FRAMEWORK-SPEC.md` (plus `VISION.md`, both
`CLAUDE.md` files, `ROADMAP.md`, `_devlog/04-handoff.md`). From the decision log I read only D-035.
D-037 and D-038 I knew through the spec, which states them fully enough.
**Scope built:** D-035. That means the scan and pre-flight report; the extractor registry (md, txt, pptx, pdf,
docx built in; pandoc and LibreOffice when installed); `materials/manifest.yaml` and its schema;
`classkit ingest [--preflight]`, `classkit add-url`; `material_locator_resolves` and
`materials_not_ingested`; scaffolded `links.md` and `ingested/`; the `/ingest` command rewritten;
the `material-classifier` agent; dependencies; teacher docs. **163 tests, green** (+64).

Every entry below is a point where the spec did not settle the answer and I decided. Nothing was
guessed silently. **⚑ = needs a decision from the author**, with its cost. The rest are recorded,
and where marked, already written into the spec.

**Verdict on the self-containment claim.** It held for the *what*. §8.7 says clearly what ingest
must do and why, and I never needed the decision log to know what to build. It ran out on
**mechanics**: how matching handles every combination of rename, copy, edit and delete; how the
classifying agent records anything without a write tool; what an anchor's slug is; and which fields
a locator may appear in. Those gaps are below. The biggest one is the agent mechanism (G-1). The
spec says outright that it is undecided.

---

## ⚑ Needs a decision

### G-1. How the classifying agent records without Write/Edit (§8.7 step 3) — ⚑

The spec says an agent "sets `kind` and `units`" and asks the teacher to confirm duplicates. It did
not say how an agent with no write tool sets anything. The brief named this explicitly as mine to
decide.

**Decided:**

- A new CLI surface: `classkit material set ID [--kind] [--unit UNN]... [--no-units] [--title]`,
  `classkit material merge ID --into ID`, and `classkit material duplicates`. Each loads the
  manifest, changes one record, and saves through the write path.
- The agent, `material-classifier`, has tools `Read, Grep, Glob, Bash`. It runs `material set`
  itself, because kind and units are hints the teacher corrects later, and the spec says the agent
  sets them. It **never** runs `material merge`. It *returns* proposed merges with evidence. The
  **command** shows them to the teacher and merges only what is confirmed. That follows §5.2: the
  gate lives in the command, since a subagent cannot ask anything.
- The agent also writes the coverage report (step 4). It has already read every material, and a
  second agent would re-read them all.

**Cost:** three new teacher-facing CLI verbs to maintain and document. The bigger cost: **"no
Write/Edit" is not airtight**, because `Bash` can write a file. The prompt forbids it, and the
structural guarantee stops at the tool list. That is the same for every agent that runs `classkit`.
I added it to spec §9. **Alternative:** the agent returns everything, the command runs every `set`,
and the agent has no Bash at all. That is more airtight, but the command then has to transcribe
dozens of classifications. That is error-prone and wastes the teacher's attention at a gate meant
for duplicates.

### G-2. Manifest fields beyond the spec's table (§8.7) — ⚑ ratify

The spec's table could not support three of its own requirements:

| Added | Why the spec's fields were not enough |
|---|---|
| `source_hashes` (path → hash) | "a renamed file is re-matched by hash", but only the *canonical* source's hash was stored. A confirmed duplicate that is not canonical (the PDF beside its deck) could never be re-matched after a rename. It would reappear as a new material. |
| `removed_at` (date) | "a removed source is marked", but `status` has no `removed` value and nothing else could carry the mark. |
| `merged_into` (`M<NNNN>`) | a confirmed merge must retire an id without deleting its record, or the id could be reused and a locator to it would vanish rather than fail. |
| `note`, `duration` | "only the link and fetchable metadata (title, duration) are recorded", but there was no field for duration, and none for the note the teacher wrote in `links.md`. |

I also **sharpened** one meaning. `source_hash` is now the hash of the canonical source *as last
converted*, and `source_hashes[canonical]` is its current hash. The spec's step 2 ("whose
`source_hash` changed") already implies this. It is also what makes a refused hand edit stay
outstanding until the teacher answers. And `found_in` may carry an anchor (`M0007#slide-3`), because
the spec says to record "where it was found".

**Cost:** five optional fields of schema surface. Written into §8.7 provisionally. Revert there if
rejected. **Recommendation:** ratify. Each one closes a hole the spec's own text opens.

### G-3. PDF page anchors are physical pages, not printed page numbers (§8.7) — ⚑

`## Page 34` could mean the 34th page of the file or the page printed "34". For a textbook PDF the
two differ by the front matter: printed p. 45 might be physical page 63.

**Decided:** physical, 1-based. It always exists, never repeats, and is what a PDF viewer's page box
shows. Where the PDF declares a different printed label, it is noted under the heading:
`*(printed page 45)*`.

**Cost:** a teacher or agent citing "p. 45" from the book must translate it to `page-63`. If they do
not, the locator still validates, because page 45 exists, and it points at the wrong page. The
validator cannot catch that. **Alternative:** anchor by printed label. Labels can repeat (two
"page 1"s), can be roman numerals, and are often missing, so the anchor would not be stable.

### G-4. What a merge does to the retired material (§8.7 step 3) — ⚑

**Decided:** `material merge M0012 --into M0007` moves M0012's sources and their hashes into M0007.
M0007 **keeps its canonical source, and so its anchors**. M0012 is marked `merged_into: M0007` and
kept, and its `.md` is left in `ingested/`. The command tells the agent to merge *into* the material
whose anchors to keep, meaning the deck, not its PDF.

**Cost:** a stale `M0012-….md` stays in `ingested/`, where an agent browsing the directory could read
it as a live material. Deleting it would delete a file the teacher may have edited, and the spec
never authorizes a delete. A locator to `M0012` fails with a message naming M0007. **Alternative:**
pick the canonical automatically by format preference. If the target were the PDF, that would
silently change its anchors from pages to slides and break any locator already citing it.

### G-5. A merged copy that changes, or a canonical source that disappears (§8.7) — ⚑

The spec covers rename, exact duplicate and removal, but not their combinations.

**Decided:**

- A non-canonical copy whose content changes is **detached**: removed from the material and treated
  as new. A re-exported PDF may no longer match its deck, so the teacher is asked again.
- When the canonical source disappears, an **identical** copy takes its place. That changes no
  anchor. If only *non-identical* copies remain (a confirmed PDF), the material is marked removed
  and the copies stand alone as new materials.

**Cost:** after re-exporting a PDF the teacher re-confirms a merge they already approved. A
deleted deck does not quietly hand its id to its PDF, so locators citing its slides fail visibly.
I think that is the right direction (§8.7: "fail validation visibly rather than disappear"), but it
is a judgement.

### G-6. `units` before units exist (§8.7, step 3) — ⚑

`/ingest` runs before `/plan-units`, so at classification time no `unit.md` exists and `U03` names
nothing.

**Decided:** `units` is a hint, per the spec. The agent bases it on the material's own order and
numbering ("Lecture 3"), counted against `course.yaml` `units`, and says in its report that it is
provisional. The validator does **not** check manifest `units` against unit directories. A finding
would fire on every course between `/ingest` and `/plan-units`, which is exactly the always-firing
warning D-033 warns against.

**Cost:** a hint that may be wrong and nothing will ever say so. **Question for the author:**
should `/plan-units` (step 3) re-run classification of `units` once the map exists?

### G-7. `classkit ingest` does not write the course log (§8.8) — ⚑

§8.8 says "Every approved step of every command is an entry … So is each ingest run."

**Decided:** `/ingest` logs each approved step with `classkit log`, three entries per run. The
`classkit ingest` *tool* does not log itself. D-038 made the same call for `validate`, and the tool's
caller is the one who knows the *why* the log exists to record.

**Cost:** a teacher who runs `classkit ingest` by hand leaves no log entry. **Alternative:** the tool
appends a terse "N materials ingested" entry with a generic why. That is consistent but low-value,
and on a `/ingest` run it would duplicate the command's own entry.

### G-8. The extraction libraries are not literally "pure Python" (`pyproject.toml`) — ⚑

The brief said "pure-Python libraries, no system packages required". `pypdf` is pure Python.
`python-pptx` and `python-docx` depend on **lxml** (a C extension), and python-pptx also on
**Pillow**. Both install as pre-built wheels on every mainstream platform. **No system package is
needed**, which I take to be the intent.

**Cost:** on an unusual platform without wheels, `pip install` would need a compiler.
**Alternative:** readers written on stdlib `zipfile` + `xml.etree`. That is feasible, but you would
own the OOXML parsing, which is a poor trade against two of the most-used Python packages for these
formats.

---

## Recorded — decided, and where marked, written into the spec

**G-9. Which fields a locator is read from (§8.4, §8.2).** The brief said "study path `resource`".
The field is actually `ref`, on each goal's `paths` today. I check `goals[].paths[].ref` and **also**
`activities[].materials[]` in `in-class.md`. That field exists now, and a fabricated slide there fails
a teacher mid-class. Both are declared in one table, `LOCATOR_FIELDS` in `validate.py`. **Step 4 adds
the goal's `answer[].ref`, and the session-level `paths[].ref`, as one line each**, with no change to
the rule. That has its own ledger row now. *Spec:* §8.7 "What `material_locator_resolves` reads".

**G-10. What a locator is.** `M` + four digits, not inside a longer word or a URL path, optionally
`#anchor`. It is found anywhere in the string, so `"M0007#slide-3 and M0007#slide-4"` checks both.
The rule fails when:

- the id is not in the manifest, or there is no manifest;
- the id was merged or removed;
- the anchor is not a heading in the `.md` *as it is now*, hand edits included;
- or the locator names any anchor on a link, media or unsupported material.

The integrity line is mechanical: each case names something that does not exist. *Spec:* §8.7.

**G-11. The anchor slug.** The spec said only "slugified". I take ATX headings outside fenced code
blocks, lowercase them, and replace every run of non-word characters with `-`. Unicode letters are
kept, so a heading in another script still gets an anchor; the unit-directory `slugify` would erase
it. Repeated headings get `-1`, `-2`, as GitHub numbers them, so a preview shows the same anchor.
Body text starting with `#` is escaped, so extraction never invents an anchor. *Spec:* §8.7.

**G-12. TXT has no anchors.** The anchor table does not list TXT. Plain text has no structure, so it
is cited by id alone. *Spec:* §8.7 table.

**G-13. A `no-text` PDF still gets a `.md`** with its page headings and empty text. Then a locator to
a page that exists resolves, and the teacher can type the text in, preserved as a hand edit. The
threshold is under 10 non-blank characters per page on average, since a scan often carries a stray
page number. *Spec:* §8.7.

**G-14. Slides.** Numbered by position, hidden slides included and marked. Otherwise "slide 12" in
the ingested copy would differ from slide 12 in PowerPoint. The title goes in bold under the
heading, then text (group shapes descended), tables, and speaker notes. Images are ignored.

**G-15. What in `source/` is not material.** The top-level `README.md` (scaffolded framework prose)
and `links.md` (read separately), dot-paths, Office lock files `~$…`, `Thumbs.db`, `desktop.ini`. A
README.md in a *subdirectory* is the teacher's and is ingested. *Spec:* §8.7 layout.

**G-16. `links.md` parsing and URL identity.** The spec writes `—`. I also accept `–`, `--` and `-`,
a leading list bullet, and `[text](url)`, and skip headings, HTML comments and blank lines. A
non-link line is **reported in pre-flight, never guessed at**. Identity: scheme and host lowercased,
fragment and trailing slash dropped, query kept. `kind` is `video` for known video hosts or a video
file extension, else `link`. The scaffolded `links.md` is a heading plus an HTML comment of
instructions, so it parses to no links and no complaints. *Spec:* §8.7.

**G-17. Fetching metadata.** On by default, `--no-fetch` to skip. Timeout 5 s, HTML only, first
512 KB, `og:title` or `<title>`, and a duration where the page declares `itemprop="duration"`. On any
failure the link is recorded titled by its note, else its URL. Tests replace `urlopen` for the whole
module, so failure is the default case there. *Spec:* §8.7.

**G-18. Link lifecycle.** A link listed only in `links.md` is marked removed when its line goes. A
link found inside a document stays, even if a later version of that document drops it. Detecting that
would mean diffing link sets per conversion, which I judged not worth it in Core. Recorded, not in
the spec.

**G-19. Canonical among identical copies.** Shallowest path, then shortest, then alphabetical. It is
deterministic, so a re-run never flips it. In the smoke test this picked `copy.md` over `notes.md`,
which is correct and unlovely. *Spec:* §8.7 "Matching".

**G-20. Title.** First slide title or heading, else the metadata title unless it is tool boilerplate
("PowerPoint Presentation", "Microsoft Word - …"), else the file name. Set once and never
overwritten by re-ingest, because the spec calls it "editable". *Spec:* §8.7 table.

**G-21. Default `kind` before classification.** `kind` is schema-required but set by an agent that
has not run yet, so ingest guesses: `slides` for decks, `video` for media and video links, `link`,
else `other`. *Spec:* §8.7.

**G-22. Suspected duplicates.** "Suspected" was undefined. Pre-flight can only compare names: the
same stem across formats, ignoring `copy`, `final`, `export`, `(1)`, `v2`. After conversion it also
compares content: ≥ 80% of the shorter material's distinct words (≥ 20) appear in the other.
Containment rather than Jaccard, because a deck's speaker notes are absent from its PDF export. A run
reports only pairs involving what it converted, so a pair the teacher declined is not re-asked every
run. Declines are **not stored**, so `classkit material duplicates` lists them forever. *Spec:* §8.7.

**G-23. Resumability.** The spec says "the manifest records per-material state". In practice the
manifest is saved after every material, with bookkeeping (moves, duplicates, removals) applied first.
A run killed between writing a `.md` and saving the manifest leaves an orphan, and the next run
**adopts** it (same canonical path, same source hash) rather than minting a second id. Ids are one
past the highest in the manifest *or* among `ingested/` file names, so a record deleted by hand never
frees its id. *Spec:* §8.7.

**G-24. The teacher's answer to a refused hand edit.** The spec says the command "shows the teacher
the edit and asks", but not what the answers are. I gave two: `--overwrite ID` (fresh extraction) and
`--keep ID` (keep the edit; the changed source is marked seen, so the warning stops). The run exits
**3**, like `classkit write`, meaning "ask the teacher". A material whose source did *not* change is
never re-converted, so its hand edit is left alone without any question. *Spec:* §8.7.

**G-25. Ingest replaces its own output with `overwrite=True`.** Under invariant 5 this needs saying.
`write()` without overwrite would refuse every re-conversion. So ingest passes `overwrite` only when
the file's hash equals `ingested_hash`, which proves nothing a teacher wrote is there. Otherwise it
calls `write()` without it, and the write path refuses. *Spec:* §8.7.

**G-26. The manifest is tool-owned.** It is a bare YAML list, as the spec says "a list". Every save
rewrites it from what was loaded, so a teacher's corrected value survives, but a **YAML comment they
add is lost**. It is saved with `overwrite=True` for the same reason as G-25. The file header says
all this. *Spec:* §8.7.

**G-27. `materials_not_ingested` is one finding**, reported against `materials/manifest.yaml`. It
lists the first five changes and counts the rest. Fifty new PDFs would otherwise be fifty warnings.
It counts moves, copies, removals, new links and refusals still awaiting an answer, not only new and
changed files. It shares `reconcile()` with the run, so the two cannot disagree. Cost: it hashes every
source file on every `validate` (spec §9). Consistency rule, always active. A fresh scaffold has no
materials, so it is silent.

**G-28. An unreadable manifest** (bad YAML, not a list) is a `schema` **error**, an unreadable file,
rather than a crash. The manifest is also schema-checked like every other artifact.

**G-29. Retrying `unsupported`.** A file is retried only when an optional converter for its format
has been installed since. My first version retried whenever a cheap probe succeeded, and a corrupt
PDF that probes cleanly would then have been re-converted, and warned about, on every run. Caught on
self-review; there is a test.

**G-30. Hidden scope I did not build.** The ledger row "agents that cite material prefer
`M<NNNN>#anchor`" is out of scope, so `study-session-designer` and the other agents do not yet know
about locators. `curriculum-architect` still says to read `materials/source/` directly. That is wrong
now, since it should read `ingested/`, and it belongs to step 3, which rewrites that agent.

---

## Spec edits made (so the review and the author can see them)

All in `FRAMEWORK-SPEC.md`. **⚑** marks an edit that writes in a decision not yet ratified.

1. §2.5 — new extension point "Adding an ingest format".
2. §3.1 — `material-classifier` added to the Core agents. `classkit material` added to the tooling
   commands. ⚑ G-1.
3. §5.1 — `/ingest` flow step 3 split into classify, confirm and merge, and step 4. ⚑ G-1.
4. §6 — `manifest.yaml` writers include `classkit material`.
5. §8.1 — `(target)` removed from `M<NNNN>`.
6. §8.4 — `(target)` removed from both rules. `materials_not_ingested` reworded: moved and gone count
   too, one finding.
7. §8.7 — `(target)` removed from the heading. Added: what in `source/` is not material; `links.md`
   parsing and identity; fetching; link lifecycle; the extra manifest fields ⚑ G-2; title
   precedence; default kind; the ingested file's path; anchor rules; TXT; slide and page numbering
   ⚑ G-3; `no-text` files; the CLI synopsis ⚑ G-1; pre-flight contents; resumability; matching
   ⚑ G-5; suspected duplicates; merging ⚑ G-4; the hand-edit answers; what the locator rule reads;
   logging ⚑ G-7.
8. §9 — two weaknesses: Bash makes "no Write/Edit" a prompt-level guarantee, and `validate` hashes
   all sources.

Docs outside the spec: `CLAUDE.md` (IDs, a Materials section, the locator rule), `GETTING-STARTED.md`
(step 3 rewritten; "not built yet" removed), `README.md` (agent and commands), `dev/CLAUDE.md`
(layout), `dev/MANUAL-TESTING.md` (a step 2b section for the hand test), the materials README
template.

---

## What I got wrong on the way, and what is untested

- **Three defects caught on self-review.** First, found links were carried on a module-level dict
  keyed by `id(report)`. That is a hack that leaks across runs; they now live on the report. Second,
  the `unsupported` retry loop (G-29). Third, a duplicate test that passed for the wrong reason: its
  generated "words" contained digits, which the word regex splits away, so it was passing on the
  file-name heuristic. A separate test now exercises the content check under different names.
- **Commit order.** I first committed the tooling (with the agent test) before the agent. I
  reordered the unpushed commits and ran the suite at each intermediate commit in a scratch worktree.
  Each is green.
- **Not exercised:**
  - the pandoc and LibreOffice *installed* paths, since neither is on this machine (the missing-tool
    path is tested);
  - `fetch_metadata` against a real site (tests forbid the network);
  - PDFs from real tools: the fixtures are a minimal hand-built PDF;
  - performance on hundreds of files.
- **The classifier prompt has never run.** Like every agent in `.claude/`, its quality is unknown
  until Avin runs `/ingest` on real materials. That hand test is the check this step most needs, and
  it is in `dev/MANUAL-TESTING.md`.
