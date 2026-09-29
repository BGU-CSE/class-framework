"""Command-line entry point: `classkit`."""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from . import log
from .frontmatter import FrontMatterError
from .mode import DEVELOPER, TEACHER, UnsafeMarker, current_mode, set_mode
from .model import LayoutError, find_course_root, find_framework_root, load_course
from .scaffold import (
    Result,
    scaffold_course,
    scaffold_item,
    scaffold_session,
    scaffold_unit,
)
from .validate import Validator
from .write import write


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="classkit",
        description="Tooling for the class-framework. Run inside a course repo.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser(
        "validate", help="check a course against its methodology and schemas"
    )
    check.add_argument("path", nargs="?", help="course directory (default: search upward)")
    check.add_argument(
        "--strict",
        action="store_true",
        help="fail on alerts and warnings too, not only on errors",
    )

    scaffold = subcommands.add_parser(
        "scaffold", help="create content skeletons (never overwrites)"
    )
    kinds = scaffold.add_subparsers(dest="kind", required=True)

    new_course = kinds.add_parser("course", help="create the course tree")
    new_course.add_argument("--code", required=True, help="institutional course code")
    new_course.add_argument("--title", required=True)
    new_course.add_argument("--institution", default="Ben-Gurion University of the Negev")
    new_course.add_argument("--instructor", default="")
    new_course.add_argument("--units", type=int, default=13)
    new_course.add_argument("--methodology", default="question-driven-25")
    new_course.add_argument("--path", help="where to create it (default: ./course)")

    new_unit = kinds.add_parser("unit", help="create a unit with its sessions and lesson plan")
    new_unit.add_argument("number", type=int)
    new_unit.add_argument("--title")

    new_session = kinds.add_parser("session", help="create one extra study session")
    new_session.add_argument("unit", help="unit id, e.g. U05")
    new_session.add_argument("number", type=int)
    new_session.add_argument("--title")

    new_item = kinds.add_parser("item", help="create an assessment item")
    new_item.add_argument("unit", help="unit id, e.g. U05")
    new_item.add_argument(
        "--format", default="multiple-choice", choices=["multiple-choice", "open"]
    )

    # The overwrite-safe write path (D-031b), for agents and commands. Refuses to
    # replace a file that already has content unless --overwrite says so explicitly.
    put = subcommands.add_parser(
        "write",
        help="write a file, refusing to overwrite existing content without --overwrite",
    )
    put.add_argument("path", help="file to write")
    put.add_argument(
        "--from",
        dest="source",
        help="read the content from this file (default: standard input)",
    )
    put.add_argument(
        "--overwrite",
        action="store_true",
        help="explicit confirmation that replacing the existing content is intended",
    )
    put.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would happen without writing anything",
    )

    # The course log (D-036): what changed in the course and why. Append-only.
    log_cmd = subcommands.add_parser(
        "log",
        help="append an entry to the course log, LOG.md (what changed, and why)",
    )
    log_cmd.add_argument(
        "title",
        help="who or which command, and what happened, e.g. '/design-unit 3, step 1 approved'",
    )
    log_cmd.add_argument(
        "--changed", required=True, help="what changed, by ID, e.g. 'U03-S01..S04 created'"
    )
    log_cmd.add_argument("--why", required=True, help="why it changed")
    log_cmd.add_argument(
        "--file",
        dest="files",
        action="append",
        default=[],
        help="a file the change touched, relative to the course (repeatable)",
    )
    log_cmd.add_argument("--date", help="YYYY-MM-DD (default: today)")
    log_cmd.add_argument("--course", help="course directory (default: search upward)")

    # Which hat a session in this repo wears (D-034). Teacher is the default; switching
    # to framework-developer creates a gitignored marker, and refuses if the ignore rule
    # is missing, because a committed marker would flip every teacher's clone.
    mode_cmd = subcommands.add_parser(
        "mode",
        help="show or switch the working mode: teacher (default) or framework-developer",
    )
    mode_cmd.add_argument(
        "mode",
        nargs="?",
        choices=["teacher", "developer", "framework-developer"],
        help="switch to this mode (omit to show the current one)",
    )

    return parser


def report_scaffold(result: Result, root: Path) -> None:
    def display(path: Path) -> str:
        try:
            return str(path.relative_to(root))
        except ValueError:
            return str(path)

    for path in result.created:
        print(f"  created  {display(path)}")
    for path in result.skipped:
        print(f"  exists   {display(path)}  (left untouched)")

    print(f"\n{len(result.created)} created, {len(result.skipped)} left untouched.")


def run_validate(args, framework_root: Path) -> int:
    course_root = find_course_root(Path(args.path) if args.path else None)
    course = load_course(course_root, framework_root)
    validator = Validator(course, framework_root)
    validator.run()

    # Alerts are printed first (spec §8.4): they are what the teacher should look at soonest,
    # even though only errors — broken data — fail the run.
    for finding in validator.ordered():
        print(finding)
        print()

    findings = validator.findings
    errors = [f for f in findings if f.level == "error"]
    alerts = [f for f in findings if f.level == "alert"]
    warnings = [f for f in findings if f.level == "warn"]

    units = len(course.units)
    goals = sum(len(session.data.get("goals") or []) for u in course.units for session in u.sessions)
    print(
        f"{course.config.get('title', 'course')} — {units} units, "
        f"{goals} guiding questions, {len(course.items)} assessment items"
    )
    print(f"{len(alerts)} alerts, {len(errors)} errors, {len(warnings)} warnings")

    # Accepted exceptions stop nagging, but are never invisible (spec §8.4).
    acceptances = validator.acceptances
    if acceptances:
        files = {a.path for a in acceptances}
        unused = sum(1 for a in acceptances if not a.suppressed)
        line = (
            f"{len(validator.suppressed)} findings suppressed by {len(acceptances)} accepted "
            f"exceptions in {len(files)} files"
        )
        if unused:
            line += f" ({unused} no longer match anything)"
        print(line)

    if errors:
        return 1
    return 1 if (args.strict and (alerts or warnings)) else 0


def run_scaffold(args, framework_root: Path) -> int:
    if args.kind == "course":
        root = Path(args.path) if args.path else Path.cwd() / "course"
        result = scaffold_course(
            root,
            framework_root,
            code=args.code,
            title=args.title,
            institution=args.institution,
            instructor=args.instructor,
            units=args.units,
            methodology=args.methodology,
        )
        report_scaffold(result, root.parent)
        return 0

    course_root = find_course_root()

    if args.kind == "unit":
        result = scaffold_unit(course_root, framework_root, args.number, args.title)
    elif args.kind == "session":
        result = scaffold_session(
            course_root, framework_root, args.unit.upper(), args.number, args.title
        )
    else:
        result = scaffold_item(course_root, framework_root, args.unit.upper(), args.format)

    report_scaffold(result, course_root.parent)
    return 0


def run_write(args) -> int:
    """`classkit write` — the one way agents and commands put content on disk.

    Exit codes: 0 written (or already identical), 3 refused because the target already
    has content. 3 is distinct from the generic failure code so a caller can tell
    "you must ask the teacher first" apart from "something broke".
    """
    content = (
        Path(args.source).read_text(encoding="utf-8")
        if args.source
        else sys.stdin.read()
    )

    outcome = write(
        Path(args.path), content, overwrite=args.overwrite, dry_run=args.dry_run
    )

    if outcome.refused:
        print(f"refused: {outcome.path}", file=sys.stderr)
        print(f"  {outcome.message}", file=sys.stderr)
        if outcome.preview:
            print("\n  what is there now:", file=sys.stderr)
            for line in outcome.preview.splitlines():
                print(f"    | {line}", file=sys.stderr)
        return 3

    print(f"{outcome.status}  {outcome.path}")
    return 0


def run_log(args) -> int:
    if args.date:
        try:
            datetime.date.fromisoformat(args.date)
        except ValueError:
            print(f"error: --date must be YYYY-MM-DD, not {args.date!r}", file=sys.stderr)
            return 2
    course_root = find_course_root(Path(args.course) if args.course else None)
    entry = log.Entry(
        title=args.title,
        changed=args.changed,
        why=args.why,
        files=args.files,
        date=args.date or "",
    )
    try:
        path = log.append(course_root, entry)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"logged  {path}")
    return 0


def run_mode(args, framework_root: Path) -> int:
    if args.mode is None:
        mode = current_mode(framework_root)
        print(f"mode: {mode}")
        if mode == TEACHER:
            print("  You are working on a COURSE. Switch with `classkit mode developer`.")
        else:
            print("  You are working on the FRAMEWORK. Read dev/CLAUDE.md.")
            print("  Switch back with `classkit mode teacher`.")
        return 0

    target = TEACHER if args.mode == "teacher" else DEVELOPER
    try:
        change = set_mode(framework_root, target)
    except UnsafeMarker as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"mode: {change.mode}")
    print(f"  {change.message}")
    if change.changed:
        # The SessionStart hook reads the marker once, at startup, so a running session
        # still holds the old mode in its context.
        print("  Restart Claude Code for a running session to pick this up.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "write":
            return run_write(args)
        if args.command == "log":
            return run_log(args)
        framework_root = find_framework_root()
        if args.command == "mode":
            return run_mode(args, framework_root)
        if args.command == "validate":
            return run_validate(args, framework_root)
        return run_scaffold(args, framework_root)
    except (LayoutError, FrontMatterError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
