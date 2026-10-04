# Implementation gap report — step 2c-1 (private and instructor-only material; `classkit doctor`)

**Date:** 2026-10-01
**Implementer:** Claude Opus 5.5, working from `FRAMEWORK-SPEC.md` (§2.2, §7, §8.4, §8.6–§8.8),
`VISION.md`, both `CLAUDE.md` files, `ROADMAP.md`, `_devlog/04-handoff.md` and
`reviews/manual-test-step-0-2b.md`. From the decision log I read D-040 only.
**Scope built:** the ten D-040 ledger rows tagged **[2c-1]**:

- the scaffolded `course/.gitignore`;
- private material in ingest: the committed index, the local full text, moves, "not on this
  machine", `material remove`;
- `private`, `private_text_hash` and `audience` in the manifest, with `apply` and `set --audience`;
- the rules `instructor_material_cited` and `private_material_committed`, and
  `materials_not_ingested` ignoring `private/`;
- `classkit doctor`;
- the classifier and `/ingest`;
- the docs and tests.

**233 tests, green** (+60).

Every entry below is a point where the spec did not settle the answer and I decided. **⚑ = needs a
decision from the author**, with its cost. The rest are recorded, and where marked, already written
into the spec.

**Verdict on the self-containment claim.** §8.7's D-040 section is the most precise part of the spec
I have built from. The *what* was never in doubt. It ran out in two places:

- **Several machines.** The spec reasons about one teacher's machine and one TA's clone that never
  had the file. It does not reason about two machines that both have the file in *different
  versions*, or with *different libraries* (G-1, G-2).
- **Collisions with older rules.** It does not say how "a private material" meets older rules: the
  PDF title fallback, link harvesting, the canonical choice among identical copies, the log
  (G-5, G-6, G-9, G-11).

The most consequential finding came from running the CLI, not from the spec (G-4).

---

## ⚑ Needs a decision

### G-1. `private_text_hash` is committed, but the full text is not — and extraction is not identical across machines (§8.7) — ⚑

**What the spec says.** It records `private_text_hash` in the (committed) manifest, "extraction is
deterministic, so it is the same on every machine".

**Where that fails.** Extraction is deterministic for one library version. A TA with a different
`pypdf` gets a different full text, so their ingest writes a different `private_text_hash` into the
committed manifest. Pulled back to the teacher's machine, the teacher's own unedited full text then
no longer matches, and looks hand-edited. Their next ingest after a source change refuses (exit 3).

**Decided:** implemented as specified.

**Options:**
- **(a)** Keep as is. Cost: churn in the manifest and spurious refusals whenever machines differ in
  library versions. Nothing is lost, because refusing is the safe direction.
- **(b)** Make the full text self-certifying: its own front matter carries the hash of its body as
  written. A body that still matches it is ingest's output; one that does not is an edit. This is
  machine-local, so nothing per-machine reaches the manifest. Cost: one front-matter field;
  `private_text_hash` leaves the manifest schema. It also resolves G-3.
- **(c)** A gitignored sidecar of local hashes. Cost: one more file to explain.

**Recommendation:** (b).

### G-2. Two machines with different copies of the same private source (§8.7) — ⚑

**What the spec doesn't say.** Suppose the teacher updates the book's PDF and a TA still has the old
one. The spec says a private source is "matched by hash like any file". Read literally, the TA's
copy is *changed*. The TA's ingest would then re-index the committed index from the old copy, and
the last machine to run ingest wins.

**Decided:** spec-literal, as for any changed file. Two consequences:

- In practice, G-3's refusal of the TA's stale full text often blocks the re-index, by accident
  rather than design. Both files are checked before either is written.
- Different folder names inside `private/` on two machines produce "moved" back and forth, which
  churns the manifest and the index's `canonical`.

**Options:**
- **(a)** As is.
- **(b)** A private source whose hash differs from the manifest's is "a different copy here".
  `doctor` reports it, and only an explicit `classkit ingest --reindex ID` re-indexes from it.
  Cost: a new flag. The teacher replacing their own book must use it too: from inside a checkout,
  "I updated the book" and "my copy is older" look the same, exactly as with removal (D-040 §3).

**Recommendation:** (b) if TAs will really copy books in. Otherwise (a), revisited after the next
hand test.

### G-3. A stale full text is refused, not overwritten (§8.7) — ⚑

**What the spec says.** Two sentences conflict:

- "if its full text is missing or stale here, ingest writes it";
- a teacher's fix there "is protected like any hand edit".

**Why they conflict.** A stale full text (made from another version) does not match
`private_text_hash`, and only the latest hash is kept. So ingest cannot tell an old extraction from
an edited one.

**Decided:** refuse, which is the safe direction. The refusal says why: "made from another version
of the source; it may hold your edits, and ingest cannot tell". `--overwrite ID` replaces it.
`--keep ID` cannot settle it: the file stays stale and `doctor` keeps listing it.

**Cost:** a TA whose copy predates the teacher's latest gets exit 3 and must answer. G-1 (b) would
resolve this: a self-certified unedited stale file can simply be replaced. The spec now says what is
built.

### G-4. Avin's machine: a global excludes file ignores `.gitignore` itself — ⚑ (action for Avin)

**Found** by running the real CLI on this machine: `~/.gitignore_global` line 3 is `.gitignore`.

**Consequences:**
- `course/.gitignore` is never committed. On this machine everything works and `doctor` said "ok".
- A clone of the course has no ignore rules at all. A TA's first `git add -A` would commit
  `private/`.
- The same applies to any course repo created on this machine.

**Decided:** `doctor` now asks git whether `course/.gitignore` is itself ignored (ACTION:
`git add -f course/.gitignore`). It notes when the file is merely not committed yet. Tested with a
throwaway `core.excludesFile`.

**For Avin:** remove `.gitignore` from `~/.gitignore_global`, or force-add it in every course repo.

**Open:**
- **Should `validate` also report a missing `course/.gitignore`?** It is committed state, the same on
  every clone. The spec puts the `.gitignore` under `doctor` alone. Cost of adding it: one
  advisory rule.
- **`classkit mode developer`'s safety check has the same blind spot**
  (`mode.py: is_ignored` checks the marker, not that `.gitignore` is tracked). Its message says
  "make sure .gitignore itself is tracked" but does not check it.

### G-5. A private copy of a public file leaves the material public (§8.7 matching) — ⚑

**What happens.** Matching merges identical copies into one material, and the canonical copy is "the
shallowest, then shortest". A book at `source/clrs.pdf` and its copy at `source/private/clrs.pdf`
are one material with a public canonical. The material is not private, and its source is committed
anyway. The teacher's act (*copying* rather than moving into `private/`) silently does nothing.

**Decided:**
- No change to matching. The public copy is itself committed, so the fix is to delete it, and that
  is the teacher's call.
- `doctor` reports it as an ACTION with that fix. After the delete, the private twin becomes
  canonical and the next ingest makes the material private (tested).

**Alternative:** prefer a private path as canonical. Cost: the index replaces the committed full
text while the PDF itself stays committed — a false sense of privacy.

**Spec should say** what an identical copy across the boundary means.

### G-6. `material remove` is not logged (§8.7, §8.8) — ⚑ (minor)

**What the spec doesn't say.** Whether `classkit material remove`, run by hand, writes a course-log
entry. `classkit ingest` logs itself when run by hand (D-039). `material set`, `apply` and `merge`
do not: `/ingest` logs them.

**Decided:** `remove` behaves like the other `material` verbs, so it does not log. `/ingest` logs it
on the teacher's confirmation, and the command text includes the `classkit log` call.

**Cost:** a removal done by hand leaves no *why*. The alternative, logging it with `--no-log` for
`/ingest`, costs two flags.

---

## Decided and written into the spec

### G-7. `private/` matched in any case (§8.7)

**What the spec says.** "Anything under `source/private/`".

**The problem.** On macOS, git (with `core.ignorecase`) ignores `Private/` too. Treating `Private/`
as ordinary material would commit the full text of a file whose source git keeps out — the exact
leak D-040 prevents.

**Decided:**
- Ingest treats any case as private.
- `private_material_committed` uses `:(icase)` pathspecs.
- `doctor` asks for the exact name, because on a case-sensitive system `Private/` is *not* ignored.

**Spec updated.**

### G-8. What the index contains, exactly (§8.7)

**What the spec says.** "The printed page label", "one-line labels".

**Decided:**
- A printed label is noted only where it differs from the physical number, exactly as in the full
  text. Otherwise every page of a book without front matter would carry a redundant label.
- Sections are `*(section: …)*` and printed pages `*(printed page …)*`. Slide titles are `**…**`,
  plus `*(hidden slide)*`.
- A label is one line of at most 120 characters, escaped so it can never become a heading.
- Outline entries are flattened in outline order. A broken bookmark is skipped, never fatal.

**Spec updated.**

### G-9. A private material's title must not be body text (§8.7 manifest `title`)

**Found** by the "no body text in the index" test.

**The problem.** A PDF without a metadata title took its **first line of text** as its title. That
title lands in the committed manifest and in the index's front matter. The spec's title rule ("first
slide title or heading, else metadata, else the file name") never mentions a first line. The code
had already departed from the spec there, and for private material that departure leaks.

**Decided:**
- For private material, the title is never body-derived (`Extraction.title_from_body`). It falls
  back to the file name.
- Non-private PDFs are unchanged: their titles are F-12's business in 2c-2, which should also decide
  whether the first-line fallback survives at all.
- A material *moved* into `private/` keeps the title it already had. That title is in git history
  regardless.

**Spec updated.**

### G-10. A machine-local conversion is not a change to the course (§8.7, §8.8)

**What the spec says.** "Leaves the committed index alone when nothing changed".

**What it doesn't say.** A conversion would still have set `ingested_at` in the manifest, recorded
links, and written a log entry. All three are committed changes made by a machine-local act.

**Decided:**
- A conversion that changes nothing committed is *local*. It leaves `ingested_at` alone, records no
  links, is reported as `full text … (this machine only)` and is excluded from the log entry.
- Tested byte-for-byte on a simulated TA clone.

**Spec updated.**

### G-11. Links inside private material (§8.7; overlaps 2c-2)

**The problem.** Link harvesting, which 2c-2 removes altogether, would record URLs found in a private
book's text as link materials in the committed manifest. They are its text.

**Decided:** never harvest from private material, now. One line, removed with the rest of harvesting
in 2c-2.

### G-12. What "`materials_not_ingested` ignores `source/private/`" means mechanically (§8.4, §8.7)

**Decided:** `reconcile(local=False)`. Files under `private/` are not scanned, and private materials
are neither marked removed nor judged for pending conversion.

**Consequences:**
- A file moved *into* `private/` but not yet re-ingested shows in `validate` as "source removed:
  M…". From committed state, its committed path is gone, which is honest but loosely worded.
  `doctor` names the move.
- A missing index of a private material is not reported by this rule. `material_locator_resolves`
  catches any citation of it.

**Spec updated.**

### G-13. Where `private_material_committed` is reported (§8.4)

**What the spec doesn't say.** Which file the finding is reported against. None of the candidates
has front matter.

**Decided:**
- One finding against `materials/manifest.yaml`, like `materials_not_ingested`. It is adjustable
  course-wide with `rules:` only.
- The message names up to five files and the `git rm --cached` step. It leaves history cleaning to
  the teacher.

**Spec updated.**

### G-14. Re-scaffolding writes the `.gitignore`, and logs it (§8.8)

**What the spec says.** The `.gitignore` is "added to existing courses on re-scaffold". It does not
say whether the course log records that, and before this step a re-scaffold of a course with a log
recorded nothing.

**Decided:**
- A re-run that creates anything appends an entry naming it. One that creates nothing writes
  nothing, and the existing test stays green.
- Scaffold writes `.gitignore` first.

**Spec updated** (§8.8).

### G-15. `classkit material remove` preconditions (§8.7)

**Decided:**
- It refuses a non-private material: delete its source and ingest marks it removed, which is the
  existing rule.
- It refuses one whose source is still on this machine. Otherwise the next ingest would *restore* it
  through the removed-material match.
- It keeps the record and the index, like every removal.

**Spec updated.**

### G-16. Dropping the local full text on a move out of `private/` (§8.6, §8.7)

**The problem.** "adds or drops the local copy", but the write path has no delete.

**Decided:**
- Delete it only if its hash equals `private_text_hash`. That is the same argument that lets ingest
  replace its own unedited output.
- A hand-edited copy stays, and `doctor` lists it as a leftover.

**Should the spec change?** Possibly. "Every write goes through one path" is now untrue of this one
deletion. A `write.remove()` with the same hash guard would restore it.

**Spec updated** for the behaviour.

### G-17. `doctor`'s details (§8.7)

**Decided:**
- **Statuses.** `ok`, `note` and `ACTION`; only `ACTION` fails. "A private source not on this
  machine" is a **note**, because a TA's clone without the book is normal and must not exit 1
  forever.
- **What it also checks:**
  - `course/.gitignore` itself committed (G-4) and a case-variant `Private/` (G-7);
  - a committed copy that is not an index, which would leak;
  - a hand-edited full text (a note);
  - new or moved private files;
  - an identical public twin (G-5).
- **The `.gitignore` check.** In a repository it asks git (`check-ignore` on a probe path), so a
  negating rule elsewhere is caught; outside one it reads the file.
- **Dependencies.** Read from classkit's own installed requirements, so the fontTools that 2c-2 adds
  will be checked with no change here.
- **Converters.** A missing one is a note, with the number of materials waiting for it.
- **Mode.** The mode of the framework root found from the course.

**Spec updated.**

---

## Recorded, no spec change needed

- **G-18. No code mechanism for consistency vs completeness.** `dev/CLAUDE.md` asks each new rule to
  be declared one or the other. The code has no such mechanism yet; it arrives with
  `outcome_coverage` in step 3. Both new rules are consistency rules, declared in the spec's table
  and in `DEFAULT_SEVERITY`'s comments.
- **G-19. Scaffold does not create `source/private/`.** A `.gitkeep` inside it would itself be
  ignored and never reach a clone. The scaffolded `source/README.md` tells the teacher to create the
  folder, consistent with the spec's list of what scaffold creates.
- **G-20. "An agent runs `doctor` before relying on a private material's full text."** The classifier
  has no Bash (D-039) and cannot. `/ingest` runs `doctor` and passes on which materials are index
  only. The other agents that read material are rewritten in steps 3 and 4; until then they are
  told through the root `CLAUDE.md`.
- **G-21. Instructor material in a merged record.** `merge` does not combine `audience`. A locator to
  a merged id is already an error, so no student-facing citation can slip through.
- **G-22. Incidental, not 2c-1.** Files written through the write path are mode `0600`, because
  `mkstemp` in `_atomic_write` creates them that way. Git ignores it. On a shared machine other
  users cannot read the course. Worth a look in 2c-2.
- **G-23. A MANUAL-TESTING count I changed.** The `.gitignore` makes a fresh scaffold create 13 files,
  so I corrected Step 1's count, which was F-01's stale "10". F-01's other half, the stale commit
  line, is left for 2c-2.

## Not built (out of scope, untouched)

These are all [2c-2] rows: duplicate detection and its verb, link harvesting (except G-11),
`units: all`, `coverage.md`, `material_locator_in_text`, the refusal diff, `write --diff`, path
kinds, and the plain fixes. Also untouched: [step 3], [step 4] and [Exports]. Exporters do not exist,
so the export-time refusal is still only a ledger row.
