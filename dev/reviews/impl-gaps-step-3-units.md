# Implementation gaps — the units increment (D-046), Session 40

Only where the spec did not say and the build decided. ⚑ = needs the author, with its cost.

**G-1 ⚑ The default stage of `approve unit N`.** §8.9 says "defaults to the next one". Built:
*planned* for a unit never approved **or whose approved plan was edited since** (an edit to the plan
is re-approved as a plan); *designed* once the plan is approved and unchanged, or already designed.
The commands always pass `--stage` explicitly. **Cost:** a teacher who says "approve unit 3" twice
in a row, with no edit between, records it as *designed* while its sessions are still placeholders.
The alternative — no default, `--stage` required — costs one word in the chat and removes the trap.
I would take it; it contradicts §8.9's wording, so it is yours.

**G-2 ⚑ `objective_coverage` alerts on every planned unit with more than two objectives.** The
scaffolded placeholder sessions name only `-O1` and `-O2`, so a plan with `-O3`/`-O4` alerts until
`/design-unit` — a finding that always fires in the *planned* state, which D-033 warns trains
teachers to ignore alerts. Built: `/plan-units` and `MANUAL-TESTING.md` name it as expected noise.
**Cost of leaving it:** routine alerts on every planned unit. Fix options: skip the rule for a unit
whose `approved.stage` is `planned` (one condition, but a new state-dependency in a rule), or
scaffold no placeholder goals. Decide with the design increment.

**G-3 ⚑ Who set a material's unit hint is not recorded.** `/plan-syllabus` step 5 must keep "hints
the teacher set by hand", but the manifest has no provenance and `/ingest`'s log entry does not
itemise the teacher's corrections. Built: the command reads the log and, where it does not say,
**asks the teacher** before proposing. **Cost:** rests on the teacher's memory. Recording it (a
`units_set_by: teacher` field written by `classkit material set`) is a schema and tooling change —
not built, per "no new mechanisms".

**G-4 The scaffolded unit's placeholders name `CO1` and `CO2`.** Followed the plan recorded in the
D-021 ledger block (the syllabus template scaffolds two outcomes "to match a scaffolded unit's two
objectives, so the step-3 coverage rules land on a clean skeleton"). So a fresh scaffold raises no
`objective_maps_to_outcome`. Cost: in a real course whose syllabus has no `CO2`, `scaffold unit`
alone gives an `outcome_reference` error until `/plan-units` writes the plan — which it does next.

**G-5 A fifth unit state, *drafted*.** A directory with no `approved` record (scaffolded, or being
planned). §8.9 names *not started / planned / designed*; the overview needed a word for this.

**G-6 The *designed* hash, precisely.** Files: `unit.md`, `sessions/*.md` by name, `in-class.md`,
then items `U<NN>-I*.md` **with `usage: in-class-quiz`** (homework items would otherwise make a
designed unit "edited since"; an unparseable item is counted). Each file is named relative to the
unit, so renaming the directory's slug is not an edit (D-031f); a file whose front matter does not
parse is hashed as raw text rather than stopping `status`. Spec §8.9 updated.

**G-7 `unit_map_mismatch` details.** Skipped when the syllabus has no map (nothing to disagree with;
otherwise every unit of an undrafted syllabus warns). Titles compared ignoring case and spacing.
Unit findings against the unit's `unit.md` (acceptable there), the length finding against the
syllabus. Spec §8.4 updated.

**G-8 Proposed difficulties travel outside the file.** The architect puts only teacher-given
difficulties in `unit.md` and lists proposals as YAML in its report; the command adds the accepted
ones (`origin: proposed`) before writing. That is how "recorded only if the teacher accepts" holds
without an extra write.

**G-9 No material, no plan — but a labelled sketch on request.** The architect does not draft
objectives for a unit with no evidence; it may offer a sketch from general knowledge, labelled as
such, which the command asks the teacher about. Consistent with §5.1 ("not … from memory as though
it were fact"), but a judgement.

**G-10 `/review-unit` on a planned unit reviews the plan.** The critic row needed a route:
`review-unit.md` gained a paragraph (check status; planned → review the plan, log the review). Not a
[units] row by name.

**G-11 Smaller choices.** The skill suggests a `## Plan notes` body section (locators the plan rests
on, what was cut, open questions — checked by `material_locator_in_text`). The approval record no
longer adds its own comment when the template's `# APPROVAL` comment is there (it duplicated; the
syllabus benefits too). A designed approval's log entry lists the unit directory and its quiz items.
Fixed in passing: `/plan-syllabus` and `GETTING-STARTED.md` still said `approved: {on, hash}`
(D-044 renamed it).

**Not relitigated, noted:** none of D-043…D-046 looks wrong from the build. G-1 is the nearest — a
default that is right most of the time and silently wrong in one easy case.
