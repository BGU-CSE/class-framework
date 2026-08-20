"""Command-line entry point: `classkit`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .frontmatter import FrontMatterError
from .model import LayoutError, find_course_root, find_framework_root, load_course
from .scaffold import (
    Result,
    scaffold_course,
    scaffold_item,
    scaffold_session,
    scaffold_unit,
)
from .validate import validate


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
        "--strict", action="store_true", help="treat warnings as errors"
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
    findings = validate(course, framework_root)

    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warn"]

    for finding in errors + warnings:
        print(finding)
        print()

    units = len(course.units)
    goals = sum(len(session.data.get("goals") or []) for u in course.units for session in u.sessions)
    print(
        f"{course.config.get('title', 'course')} — {units} units, "
        f"{goals} guiding questions, {len(course.items)} assessment items"
    )
    print(f"{len(errors)} errors, {len(warnings)} warnings")

    if errors:
        return 1
    return 1 if (args.strict and warnings) else 0


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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        framework_root = find_framework_root()
        if args.command == "validate":
            return run_validate(args, framework_root)
        return run_scaffold(args, framework_root)
    except (LayoutError, FrontMatterError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
