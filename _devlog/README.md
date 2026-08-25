# _devlog — temporary build log

**This folder is scaffolding, not part of the framework. Delete it before the first public release.**

Its job is continuity: if this session is lost, or another coding agent (or another
teacher on the project) picks the work up, everything needed to continue is here.

## Files

| File | Purpose |
|---|---|
| `00-brief.md` | The project brief. What we're building and why. Read this first. |
| `01-decisions.md` | Decision log (ADR-style). Every locked choice + its rationale. |
| `02-progress.md` | Running session log, newest last. What happened, what's next. |
| `03-open-questions.md` | Unresolved questions blocking or shaping future work. |
| `04-handoff.md` | Cold-start instructions for a new agent session. |

The phases themselves live in `../ROADMAP.md`, not here — collaborators need them, and this folder
gets deleted before release.

## Rules for whoever writes here

- Append to `02-progress.md` at the end of every working session.
- A decision only counts once it's in `01-decisions.md`. If it's only in chat, it isn't decided.
- When a question in `03-open-questions.md` gets answered, move it to `01-decisions.md`.
- **Structure and flow belong in `../DESIGN.md`, not here.** This folder records *how we got here*;
  DESIGN.md records *how it works now*. Only DESIGN.md survives this folder's deletion, so any
  rationale worth keeping must be reflected there too.
- Keep course-specific content **out** of this folder — see the separation rule in `01-decisions.md` (D-002).
