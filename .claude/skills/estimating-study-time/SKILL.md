---
name: estimating-study-time
description: How to estimate honestly how long a study path takes, so a 25-minute session really is 25 minutes. Use when setting est_minutes on study paths, checking whether a session fits its budget, or auditing whether a home-study workload is realistic.
---

# Estimating study time

The framework checks that every study session has at least one complete path inside its time
budget. That check is only as honest as the estimates it runs on — and optimistic estimates are
the single most damaging thing you can put in this repo, because they launder an unrealistic
course as a verified one.

The consequence is not abstract. A "2-hour" week that really takes 4 is a week students stop doing
the prework, which collapses the class hour, which is the whole design.

## Where the numbers come from

`defaults/time-constants.yaml`, overridden per course in `course.yaml` under `time_constants`. Read
them; don't invent your own. The shipped values are placeholders and should be tuned to real
students.

## Estimating by kind

**Textbook.** Technical prose is not novel-reading. Notation, proofs and worked examples slow a
student to a fraction of ordinary reading speed, and a page with three equations can take longer
than five pages of exposition. Use the page rate, then look at the actual pages: if it's dense,
say so and raise the estimate.

**Video.** Multiply real duration by the rewatch factor. Students pause, rewind, and re-run the
part that went too fast. A 10-minute video is not 10 minutes of study. And use the *actual*
duration — check it rather than guessing from the title.

**Class Gem.** A tutoring exchange that gets a student to a real answer is several turns, not one.
Budget per guiding question, not per session.

**Exercise.** The time to *attempt* it, including being stuck. Solution-reading time is not
exercise time.

**Overhead.** Add the per-session constant. Opening the material, remembering where you were, and
closing down are real minutes.

## The arithmetic

For a session, the feasibility figure is: session overhead, plus — for each guiding question — the
**fastest** path available for it. Fastest, because the student only has to take one route per
question, and the check asks whether *some* complete route fits.

If that total exceeds the budget, the design is wrong. Fix the design:

- cut a guiding question (usually the right answer — 3 good ones beat 5 rushed)
- move a question to another session
- add a genuinely shorter path for the worst offender

**Do not shave the estimates to make the number fit.** That is the one move that turns this whole
mechanism into theatre.

## Sanity checks that a validator can't run

- Does "CLRS ch.3 pp.45-52 — 8 min" survive contact with eight pages of proofs? Open the estimate
  and ask whether you believe it.
- Is every path for a question suspiciously the same length? That usually means they were filled
  in by pattern rather than considered.
- Does the fast path exist only on paper — a 4-minute video that covers a third of the question?
  A path that doesn't actually answer the question isn't a path.
- Sum the whole unit. Four sessions each "just fitting" 25 minutes is a unit with no slack at all,
  and no student is average on every question.

## When you don't know

Say so. An estimate flagged as a guess is useful; a guess presented as a measurement is not. If a
resource's length can't be checked, leave `est_minutes` off and note what needs confirming — the
validator will warn that feasibility couldn't be fully verified, which is the honest state.
