#!/bin/sh
# Report which hat this Claude Code session is wearing.
#
# Run as a SessionStart hook (see .claude/settings.json). Prints a line for the
# human and injects the same fact into the model's context, so the mode is
# established mechanically rather than left to the model to infer.
#
# TEACHER is the default, and the safe direction: a developer wrongly in teacher
# mode writes a course file; a teacher wrongly in developer mode is told about
# pytest and the implementation ledger at the moment they are most lost.
#
# FRAMEWORK-DEVELOPER requires dev/.developer, which is gitignored — so it exists
# only where a developer created it, and never in a teacher's clone. Anything the
# framework *ships* would clone along with everything else and could not
# discriminate.

root="${CLAUDE_PROJECT_DIR:-.}"

if [ -f "$root/dev/.developer" ]; then
  mode="framework-developer"
  human="🔧 class-framework — FRAMEWORK-DEVELOPER mode (dev/.developer present)"
  context="This session is in FRAMEWORK-DEVELOPER mode: you are working on the framework itself. Read dev/CLAUDE.md before changing anything, and do not break the invariants it lists. State your mode in your first reply."
else
  mode="teacher"
  human="🎓 class-framework — TEACHER mode (working on a course)"
  context="This session is in TEACHER mode: you are helping build and maintain a COURSE, not the framework. Use the commands in .claude/commands/ and follow CLAUDE.md. Do not modify schemas/, src/classkit/, templates/, methodologies/, .claude/ or dev/ unless the user explicitly asks you to work on the framework — if they do, read dev/CLAUDE.md first and say that you are switching to framework-developer mode. State your mode in your first reply."
fi

# Escape nothing: both strings are fixed above, so this is safe to inline.
printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
  "$human" "$context"

# mode is printed for humans debugging the hook by running it directly
[ -t 1 ] && echo "mode=$mode" >&2
exit 0
