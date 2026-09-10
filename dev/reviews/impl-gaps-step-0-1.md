# Implementation gap report — steps 0 and 1

**Date:** 2026-09-10
**Implementer:** Claude Opus 5, working from `FRAMEWORK-SPEC.md` alone (plus `VISION.md`,
`CLAUDE.md`, `ROADMAP.md`, `_devlog/04-handoff.md`). The decision log was not read.
**Scope built:** step 0 — the overwrite-safe write path (D-031b); step 1 — `classkit scaffold
course` including `syllabus/syllabus.md` (D-021, D-031d).

The spec claims to be self-contained: that an agent with no memory of the design conversations
can implement a phase from it alone. This is what that attempt actually ran into. Every item is a
point where the spec did not determine the answer and I decided for myself. Nothing here was
guessed silently.

Recommendations are marked **CHANGE THE SPEC** or **no change needed**. Three are worth acting on
before step 3: G-9, G-12 and G-15.

---

## Step 0 — the write path

### G-1. No agent-facing surface is specified (§5.2 rule 2, D-031b) — **CHANGE THE SPEC** (done)

The spec says `classkit` "provides the write path agents use". It never says how an agent *invokes*
it. An agent is a prompt with a tool list; a Python function is unreachable from one. Without a
command-line surface the mechanism is real code that nothing can call, and the guarantee stays
prompt-only in practice.

**Decided:** added `classkit write PATH [--from FILE] [--overwrite] [--dry-run]`; content from
stdin by default; exit code **3** for a refusal, distinct from the generic failure code 2 so a
caller can tell *"ask the teacher first"* from *"something broke"*. `--dry-run` is what a command
uses to answer "may I write here?" before it generates anything, which is what §5.2's "checks
whether the target already has content" needs.

**Spec:** written up as the new **§8.6 The write path**.

### G-2. "Already has content" is undefined (§5.2 rule 2) — **CHANGE THE SPEC** (done)

§5.2 says a command "checks whether the target already has content"; §7 invariant 5 says
`write_new()` is the model, and that checks `path.exists()`. Those are different tests, and three
cases fall between them: an empty file, a whitespace-only file, and a rewrite whose bytes are
identical to what is already there.

**Decided:**

| Case | Treatment | Why |
|---|---|---|
| missing, or whitespace only | write | nothing can be lost |
| byte-identical content | `unchanged`, a no-op | re-running a command must stay safe; refusing here would block a command from re-emitting its own approved output |
| anything unreadable as text | refuse | refusing is the safe direction |

**Spec:** the outcome table in §8.6.

### G-3. What "explicit confirmation" is, mechanically (§5.2 rule 2) — **CHANGE THE SPEC** (done)

"Explicit confirmation" could mean a teacher's typed reply, a flag, or a second call. It matters,
because §5.2 also says a subagent cannot ask the teacher anything (D-031h) — so whatever reaches
`classkit` cannot itself be the teacher's answer.

**Decided:** the split is *code refuses, the command asks*. `classkit` enforces that no overwrite
happens without a deliberate second act (`overwrite=True` / `--overwrite`); obtaining the teacher's
yes before performing that act stays the orchestrating command's job, where the conversational gate
already lives. Code cannot verify a human said yes; it can guarantee that nothing is destroyed by
an agent that simply forgot to check.

### G-4. The guarantee is not structural yet, and the spec does not say what would make it so — **CHANGE THE SPEC**

Every writing agent's front matter still declares `tools: Read, Write, Edit, …`. An agent with the
`Write` tool can bypass `classkit` entirely, so today the code path is *available*, not *mandatory*.
The D-031b ledger row says all writers "must write through that path" but never says the enforcement
is **removing `Write` and `Edit` from their tool lists** — which is the only thing that makes it
structural. Without that, D-031b delivers a better prompt, which is exactly what it was raised to
replace.

**Decided:** built the mechanism; added a warning note to §8.6. **The per-agent ledger rows should
be amended** to read "writes through `classkit write`, *and drops `Write`/`Edit` from its tools*",
so the later steps cannot land a half-measure.

### G-5. Whether a refusal raises or returns (§5.2) — no change needed

Unspecified. **Decided:** `write()` returns a `refused` outcome and never raises, so a caller that
ignores the return value still writes nothing. Failing safe beats failing loudly here: an exception
protects only callers who catch it, whereas the returned-refusal design protects even a careless
one. Stated in §8.6.

### G-6. Where write-path tests belong — **CHANGE THE SPEC** (minor)

`CLAUDE.md` and the D-031 ledger row put "the overwrite-refusal path" tests in
`tests/test_course_lifecycle.py`, which is specifically the scaffold→validate round-trip. The write
path is not a validation rule and has no course in it.

**Decided:** `tests/test_write_path.py` (13 tests). The ledger row should point there.

### G-7. Atomicity — no change needed

Not mentioned anywhere. An interrupted write that truncates a teacher's file to nothing is the same
unrecoverable loss invariant 5 exists to prevent, so writes go through a temp file in the same
directory plus `os.replace`. An implementation detail; the spec should stay out of it.

---

## Step 1 — the syllabus

### G-8. The step 1 / step 3 boundary is ambiguous (ROADMAP step table vs. §8.4) — **CHANGE THE SPEC** (done)

The step table gives step 1 "D-021 (template + scaffold rows)" and step 3 "syllabus schema and
rules". But a syllabus that is scaffolded and never schema-checked is not "a complete, **valid**
course skeleton", which is what step 1 promises.

**Decided:** step 1 = the syllabus **artifact** end to end — schema, template, model loading,
schema-layer wiring, and `syllabus_workload_missing`. Step 3 = the **coverage chain**
(`outcomes` on unit objectives, `objective_maps_to_outcome`, `outcome_coverage`), because those
rules check a field on the *unit* that step 3 is the step that adds. Cutting it anywhere else
either ships an unchecked file or drags unit work into step 1.

**Spec:** ROADMAP's step-1 row now reads "D-021 (schema, template, model, scaffold rows), D-031d".

### G-9. There is no rule for a **missing** syllabus (§8.4) — **CHANGE THE SPEC** ⚠️

§8.4 has `in_class_missing` for a unit, and nothing equivalent for the syllabus, even though §4
makes `syllabus/syllabus.md` a required artifact ("the course-level top layer", one per course).
So a course whose syllabus is deleted validates in silence.

It gets worse once step 3 lands: a course with no syllabus has **no Course Outcomes**, and
`outcome_coverage` ("every Course Outcome covered by ≥1 unit objective") is then *vacuously
satisfied*. The rule that exists to close the coverage chain passes most loudly exactly when the
roof is missing.

**Decided:** I did **not** invent a rule code — that would edit the normative rule table, which the
brief says to ask about first. Instead `syllabus_workload_missing` fires when the file is absent
("there is no syllabus/syllabus.md, so the course declares no workload"), so the absence is at
least visible.

**Recommendation: add `syllabus_missing` to §8.4.** Error is the honest severity; warn is
defensible while a course is still being drafted. I did not add it — this one needs your call.

### G-10. `workload`'s sub-fields: which are required (§8.2) — **CHANGE THE SPEC** (done)

The row reads `{ credits (number), credit_system (string…), total_hours (number, opt) }`. The
"(opt)" on `total_hours` implies the other two are mandatory *within* `workload`, but the row's own
Req column is blank because D-031d made the whole block optional. Two levels of optionality, one
notation.

**Decided:** `workload` is optional; when present, `credits` and `credit_system` are required and
`total_hours` is not — a half-filled workload is worse than none, because it looks settled.
**Spec:** the §8.2 row now marks them ✓ explicitly.

### G-11. The reserved `assessment` block's item shape (§8.2) — **CHANGE THE SPEC** (minor)

"Reserved… e.g. `{ type, weight }`… specified in the Assessment phase". Every other schema in this
repo closes its objects with `additionalProperties: false`.

**Decided:** left `assessment` items **open**. A course that fills the block early should not be
invalidated by the phase that eventually specifies it, and closing a shape we have not designed is
a promise we cannot keep. This is a deliberate exception to the repo's convention and the spec
should say so in a clause, or the next implementer will "fix" it.

*(The independent review hit this same ambiguity — §2 of `core-spec-review-01.md`. It survived that
review being adopted, which suggests reviews record ambiguities more readily than they close them.)*

### G-12. How many Course Outcomes a scaffolded syllabus has — and the interaction nobody has noticed — **CHANGE THE SPEC** ⚠️

`outcomes` needs ≥1, so the template must pick a number, and the spec offers none. That would be
trivial except for what it collides with two steps later:

**A freshly scaffolded course has Course Outcomes and zero units.** Read literally,
`outcome_coverage` ("every Course Outcome covered by ≥1 unit objective") makes *every* outcome
uncovered on a brand-new course — an **error**, on the output of `scaffold course`, breaking
invariant 6 at the first commit of step 3. The same reading fires through the whole middle of a
semester's work, when 3 of 13 units exist.

**Decided (for now):** the template ships `CO1` and `CO2`, mirroring the two objectives a
scaffolded unit gets, so the skeleton is internally consistent whenever the rule does arrive.

**Recommendation: §8.4 must say when `outcome_coverage` applies.** The plausible answer is that it
is a *course-completeness* check, meaningful only once the unit map is complete — i.e. skipped
while `units on disk < course.yaml units` (the condition `unit_count` already computes). Please
settle this before step 3; it is the difference between a rule that closes the coverage chain and a
rule teachers switch off in week one.

### G-13. Which rules a methodology file should enumerate (§2.5 vs. §8.4) — no change needed

§2.5 says a new rule sets its default in `DEFAULT_SEVERITY`; §8.4 says a methodology's `rules:`
block may override any; the D-019 ledger row additionally says to list its new rule in
`question-driven-25.yaml` "so other methodologies can re-tune its severity" — which is already true
without listing it.

**Decided:** `DEFAULT_SEVERITY` only, following §2.5's recipe. `syllabus_workload_missing` is a
course-level concern, and putting it in a *methodology* file would imply the methodology has an
opinion about credits, which it does not.

### G-14. The syllabus body has no specified structure (§8.2) — no change needed

"Body: prose aim and narrative" is all there is. **Decided:** a section skeleton (Aim / Course
outcomes / Prerequisites / How the course runs / Workload). The body is for humans and the front
matter is the contract, so leaving this unspecified is correct.

### G-15. **The "rendered syllabus" is referenced three times and specified nowhere** — **CHANGE THE SPEC** ⚠️

§4 says "a *rendered* syllabus stitches in the unit overview live, so it cannot drift" and "Its
rendered view stitches in a unit overview from the units below"; §6's data-flow table lists
"(rendered) syllabus export" as a consumer of `syllabus/syllabus.md`. There is no section defining
it: no command, no output path, no format, no phase, and no ledger row. It is load-bearing in the
argument for *why* identity fields are not repeated in the syllabus — the anti-drift guarantee is
the rendering — and it does not exist.

**Decided:** built nothing; the front matter deliberately omits identity fields as §8.2 requires, so
whatever renders it later has everything it needs.

**Recommendation:** either specify it (probably one paragraph in §8 plus a ledger row) or move it to
the deferred list in §1.1 and say so where it is referenced. Right now a reader reasonably concludes
it exists. This is the same failure mode as Q-028 (ingest): a component named in passing, never
specified, and invisible to a document review because there is no section to review.

### G-16. Drift the ledger does not cover: `gem` in `course.yaml` — **CHANGE THE SPEC** (minor)

§8.2 says of `course.yaml`: "Deferred: a `gem` block (Exports phase)." But `schemas/course.schema.json`
defines one, `templates/course/course.yaml` scaffolds one, and `GETTING-STARTED.md` documents it as
a setting teachers should set. So every scaffolded course ships configuration for a phase that does
not exist. No ledger row covers this, so it is drift rather than a tracked gap.

**Decided:** left alone — outside steps 0–1 and it breaks nothing. **Recommendation:** a row under
the Exports slice, or remove it from the template.

---

## What this says about the self-containment claim

The spec held up well on **what to build**: the content model, the ID grammar, the field lists and
the rule table were precise enough to implement without inventing structure. Nothing in §8 turned
out to be wrong.

It was thinner on three things, in rough order of cost:

1. **Interactions between a rule and the states a course passes through.** §8.4 defines each rule
   against a *finished* course. G-12 is the sharp case: a rule that is obviously right for a
   complete course is obviously wrong for a scaffolded one, and the spec has no place where "the
   course is half-built" is a state under consideration — even though invariant 6 says every
   scaffold must validate, and steps 1–6 spend all their time in exactly that state.
2. **Absence.** Rules check that present things are consistent; §8.4 has almost nothing about a
   required artifact that is not there (G-9). The coverage chain is most likely to be broken by
   deletion, and deletion is what it currently cannot see.
3. **Mechanism for things the spec assigns to code.** §5.2 delegates the never-overwrite guarantee
   to `classkit` and then says nothing about how it is reached, what "content" is, or what the
   confirmation looks like (G-1, G-2, G-3) — and the one part that would make it structural rather
   than advisory (G-4) is not stated anywhere. The spec was written from the *content model*
   outward, and this is the seam where it stops.

The pattern in G-15 and in Q-028 is the same one this project already recorded once: **a document
review cannot flag a section that does not exist.** The gaps that cost the most here — the rendered
syllabus, the missing-syllabus rule, the scaffolded-course reading of `outcome_coverage` — were all
invisible to reading and immediate on contact with an implementation.
