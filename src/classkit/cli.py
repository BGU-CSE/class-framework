"""Command-line entry point: `classkit`."""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

import yaml

from . import approve, doctor, ingest, log, status
from .frontmatter import FrontMatterError
from .ingest import links as linkfile
from .ingest.manifest import AUDIENCES, KINDS, SOURCE_DIR, ManifestError
from .ingest.report import log_summary, plural, preflight_text, run_text
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
from .write import append, diff, write


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
        "--append",
        action="store_true",
        help="add the content to the end of the file; existing content is never rewritten",
    )
    put.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would happen without writing anything",
    )
    put.add_argument(
        "--diff",
        action="store_true",
        help="print a unified diff of exactly what --overwrite would change, writing nothing",
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

    # Ingest (D-035): turn materials/source/ into materials/ingested/ + manifest.yaml.
    ingest_cmd = subcommands.add_parser(
        "ingest",
        help="convert new or changed course materials into citable Markdown (never touches source/)",
    )
    ingest_cmd.add_argument(
        "--preflight",
        action="store_true",
        help="report what is there and what would be converted, without converting or writing",
    )
    ingest_cmd.add_argument(
        "--overwrite",
        action="append",
        default=[],
        metavar="ID",
        help="the teacher confirmed: replace this material's hand-edited ingested file (repeatable)",
    )
    ingest_cmd.add_argument(
        "--keep",
        action="append",
        default=[],
        metavar="ID",
        help="the teacher confirmed: keep this material's hand edit despite a changed source (repeatable)",
    )
    ingest_cmd.add_argument(
        "--no-fetch",
        action="store_true",
        help="do not fetch link titles from the network",
    )
    ingest_cmd.add_argument(
        "--why",
        help="why you ran it, for the course log (default: 'run by hand')",
    )
    ingest_cmd.add_argument(
        "--no-log",
        action="store_true",
        help="do not write a course-log entry — /ingest passes this and writes its own",
    )
    ingest_cmd.add_argument("--course", help="course directory (default: search upward)")

    add_url = subcommands.add_parser(
        "add-url", help="add a link to materials/source/links.md"
    )
    add_url.add_argument("url")
    add_url.add_argument("--note", default="", help="what it is, e.g. 'heaps explained, 12 min'")
    add_url.add_argument("--course", help="course directory (default: search upward)")

    # How the classifying agent and the teacher record decisions about materials, without
    # editing the manifest by hand.
    material = subcommands.add_parser(
        "material",
        help="record a material's kind, units, title or audience; merge; remove a private one",
    )
    actions = material.add_subparsers(dest="action", required=True)
    set_cmd = actions.add_parser("set", help="set kind, units, title or audience of a material")
    set_cmd.add_argument("id", help="material id, e.g. M0007")
    set_cmd.add_argument("--kind", choices=KINDS)
    set_cmd.add_argument(
        "--unit", dest="units", action="append", metavar="UNN",
        help="a unit this material supports, e.g. U03 (repeatable; replaces the list), or `all` "
             "for a course-wide material",
    )
    set_cmd.add_argument("--no-units", action="store_true", help="clear the units list")
    set_cmd.add_argument("--title")
    set_cmd.add_argument(
        "--audience", choices=AUDIENCES,
        help="who may be pointed at it: student (the default) or instructor (never cited to students)",
    )
    set_cmd.add_argument("--course", help="course directory (default: search upward)")
    merge_cmd = actions.add_parser(
        "merge", help="optional: merge one material into another the teacher says is the same "
                      "(never prompted; exact copies are merged by ingest already)"
    )
    merge_cmd.add_argument("id", help="the duplicate, e.g. the PDF export")
    merge_cmd.add_argument("--into", required=True, help="the material to keep, e.g. the deck")
    merge_cmd.add_argument("--course", help="course directory (default: search upward)")
    apply_cmd = actions.add_parser(
        "apply",
        help="record a batch of classifications (YAML list of {id, kind, units, title, audience}); "
             "all or nothing",
    )
    apply_cmd.add_argument(
        "--from", dest="source", help="read the YAML from this file (default: standard input)"
    )
    apply_cmd.add_argument("--course", help="course directory (default: search upward)")
    remove_cmd = actions.add_parser(
        "remove",
        help="mark a private material removed — ingest never does (a missing private source may "
             "just not be on this machine)",
    )
    remove_cmd.add_argument("id", help="material id, e.g. M0005")
    remove_cmd.add_argument("--course", help="course directory (default: search upward)")

    # This machine's copy of the course (D-040): `validate` judges the course, `doctor` the
    # machine — private files present or stale, the .gitignore, dependencies, converters, mode.
    doctor_cmd = subcommands.add_parser(
        "doctor",
        help="check this machine's copy of the course: private files, .gitignore, dependencies "
             "(read-only; exit 1 if something needs action)",
    )
    doctor_cmd.add_argument("--course", help="course directory (default: search upward)")

    # The teacher's approval, recorded in the approved file itself (D-043, spec §8.9).
    approve_cmd = subcommands.add_parser(
        "approve",
        help="record the teacher's approval in the file itself (date, a unit's stage, hash), and log it",
    )
    approve_cmd.add_argument("what", choices=["syllabus", "unit"], help="what is approved")
    approve_cmd.add_argument("number", nargs="?", type=int,
                             help="the unit's number, for `approve unit N`")
    approve_cmd.add_argument(
        "--stage", choices=list(approve.STAGES),
        help="a unit's milestone, required for a unit: planned (its objectives — /plan-units) or "
             "designed (the whole unit — /design-unit). No default (D-047)",
    )
    approve_cmd.add_argument(
        "--diff", action="store_true",
        help="show the change to the file without writing or logging anything",
    )
    approve_cmd.add_argument("--why", help="for the course log (default: 'the teacher approved it')")
    approve_cmd.add_argument("--date", help="YYYY-MM-DD (default: today)")
    approve_cmd.add_argument("--course", help="course directory (default: search upward)")

    # Where the course stands (D-043, spec §8.9) — every command shows it first.
    status_cmd = subcommands.add_parser(
        "status",
        help="where the course stands: the syllabus (approved / edited since / draft), the unit "
             "map, the materials (read-only)",
    )
    status_cmd.add_argument("--course", help="course directory (default: search upward)")

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
        f"{course.config.get('title', 'course')} — {plural(units, 'unit')}, "
        f"{plural(goals, 'guiding question')}, {plural(len(course.items), 'assessment item')}"
    )
    print(f"{plural(len(alerts), 'alert')}, {plural(len(errors), 'error')}, "
          f"{plural(len(warnings), 'warning')}")

    # Accepted exceptions stop nagging, but are never invisible (spec §8.4).
    acceptances = validator.acceptances
    if acceptances:
        files = {a.path for a in acceptances}
        unused = sum(1 for a in acceptances if not a.suppressed)
        line = (
            f"{plural(len(validator.suppressed), 'finding')} suppressed by "
            f"{plural(len(acceptances), 'accepted exception')} in {plural(len(files), 'file')}"
        )
        if unused:
            line += f" ({unused} no longer {'matches' if unused == 1 else 'match'} anything)"
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

    if args.append and args.overwrite:
        print("error: --append and --overwrite are mutually exclusive", file=sys.stderr)
        return 2
    if args.diff:
        # Show the teacher a partial change before it is made (spec §8.6): nothing is written.
        changes = diff(Path(args.path), content)
        if changes:
            sys.stdout.write(changes if changes.endswith("\n") else changes + "\n")
        else:
            print(f"unchanged  {args.path}  (already holds exactly this content)")
        return 0
    if args.append:
        outcome = append(Path(args.path), content, dry_run=args.dry_run)
    else:
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


def run_ingest(args) -> int:
    course_root = find_course_root(Path(args.course) if args.course else None)
    if args.preflight:
        print(preflight_text(ingest.preflight(course_root, fetch=not args.no_fetch)))
        return 0
    report = ingest.run(
        course_root,
        overwrite=[i.upper() for i in args.overwrite],
        keep=[i.upper() for i in args.keep],
        fetch=not args.no_fetch,
    )
    print(run_text(report))
    # Every run that changes the course is a log entry (§8.8, D-039). /ingest passes --no-log
    # and writes its own entry, which knows the why.
    summary = log_summary(report)
    if summary and not args.no_log:
        path = log.append(course_root, log.Entry(
            title="classkit ingest",
            changed=summary,
            why=args.why or "run by hand",
            files=["materials/manifest.yaml"],
        ))
        print(f"logged  {path}")
    # 3, like `classkit write`: "ask the teacher first", not "something broke".
    return 3 if report.refused else 0


def run_add_url(args) -> int:
    course_root = find_course_root(Path(args.course) if args.course else None)
    try:
        path = linkfile.add_url(course_root / SOURCE_DIR, args.url, args.note)
    except linkfile.BadURL as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"added  {args.url.strip()}  → {path.relative_to(course_root.parent)}")
    print("  Run /ingest (or `classkit ingest`) to record it as a material.")
    return 0


def run_material(args) -> int:
    course_root = find_course_root(Path(args.course) if args.course else None)
    try:
        if args.action == "set":
            units = [] if args.no_units else (list(args.units) if args.units else None)
            record = ingest.set_fields(course_root, args.id.upper(), kind=args.kind, units=units,
                                       title=args.title, audience=args.audience)
            shown_units = record.get("units") or []
            shown_units = shown_units if isinstance(shown_units, str) else ",".join(shown_units) or "-"
            print(f"{record['id']}  kind={record.get('kind')}  units={shown_units}"
                  f"  audience={record.get('audience') or 'student'}  title={record.get('title')!r}")
        elif args.action == "merge":
            record = ingest.merge(course_root, args.id.upper(), args.into.upper())
            print(f"merged {args.id.upper()} into {record['id']}: sources {', '.join(record['sources'])}")
            print(f"  {args.id.upper()} is retired; anchors stay those of {record['canonical']}.")
        elif args.action == "remove":
            record = ingest.remove(course_root, args.id.upper())
            print(f"removed {record['id']} ({record.get('title')}): marked removed_at {record['removed_at']}; "
                  "its record and index are kept, so anything citing it is reported.")
        elif args.action == "apply":
            text = (Path(args.source).read_text(encoding="utf-8") if args.source
                    else sys.stdin.read())
            try:
                entries = yaml.safe_load(text)
            except yaml.YAMLError as exc:
                raise ingest.MaterialError(f"not valid YAML: {exc}") from exc
            results = ingest.apply_all(course_root, entries or [])
            # Every field set is echoed, unchanged ones marked, so the teacher sees what was
            # confirmed as well as what changed (teacher test: `kind` was silent when already so).
            for material_id, fields, changed in results:
                shown = "  ".join(
                    f"{k}={','.join(v) if isinstance(v, list) else v}"
                    + ("" if k in changed else " (unchanged)") for k, v in fields.items()
                )
                print(f"{material_id}  {shown}")
            changes = sum(1 for _id, _fields, changed in results if changed)
            print(f"{changes} materials changed, {len(results) - changes} already so.")
    except ingest.MaterialError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def run_doctor(args) -> int:
    course_root = find_course_root(Path(args.course) if args.course else None)
    try:
        framework_root = find_framework_root(course_root)
    except LayoutError:
        framework_root = None
    lines = doctor.diagnose(course_root, framework_root)
    print(doctor.report(lines))
    return 1 if any(line.status == doctor.ACTION for line in lines) else 0


def run_approve(args) -> int:
    if args.date:
        try:
            datetime.date.fromisoformat(args.date)
        except ValueError:
            print(f"error: --date must be YYYY-MM-DD, not {args.date!r}", file=sys.stderr)
            return 2
    if args.what == "unit" and args.number is None:
        print("error: which unit? `classkit approve unit N [--stage planned|designed]`", file=sys.stderr)
        return 2
    if args.what == "syllabus" and (args.number is not None or args.stage):
        print("error: the syllabus has no number and no stage — `classkit approve syllabus`", file=sys.stderr)
        return 2
    course_root = find_course_root(Path(args.course) if args.course else None)
    try:
        if args.what == "unit":
            approval = approve.approve_unit(course_root, args.number, stage=args.stage, on=args.date,
                                            dry_run=args.diff, why=args.why or "")
        else:
            approval = approve.approve_syllabus(course_root, on=args.date, dry_run=args.diff,
                                                why=args.why or "")
    except approve.ApproveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    shown = approval.path.relative_to(course_root).as_posix()
    stage = f" as {approval.stage}" if approval.stage else ""
    if approval.already:
        print(f"unchanged  {shown}  (already approved{stage} {approval.on}; "
              "not edited since — nothing to record)")
        return 0
    sys.stdout.write(approval.changes if approval.changes.endswith("\n") else approval.changes + "\n")
    if args.diff:
        print(f"(nothing written — run without --diff to record the approval{stage})")
        return 0
    print(f"approved   {shown}{stage}  on {approval.on}, {approval.hash[:15]}…")
    print(f"logged     {course_root / log.LOG_FILE}")
    return 0


def run_status(args) -> int:
    course_root = find_course_root(Path(args.course) if args.course else None)
    try:
        framework_root = find_framework_root(course_root)
    except LayoutError:
        framework_root = None
    print(status.report(status.status(course_root, framework_root)))
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
        if args.command == "ingest":
            return run_ingest(args)
        if args.command == "add-url":
            return run_add_url(args)
        if args.command == "material":
            return run_material(args)
        if args.command == "doctor":
            return run_doctor(args)
        if args.command == "approve":
            return run_approve(args)
        if args.command == "status":
            return run_status(args)
        framework_root = find_framework_root()
        if args.command == "mode":
            return run_mode(args, framework_root)
        if args.command == "validate":
            return run_validate(args, framework_root)
        return run_scaffold(args, framework_root)
    except (LayoutError, FrontMatterError, FileNotFoundError, ManifestError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
