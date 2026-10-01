"""Course validation.

Two layers:

1. **Schema** — does every file's front matter have the shape tools need to read it?
2. **Semantics** — does the course hold together as a flipped course under its
   declared methodology?

**The teacher is the authority** (D-037): validation informs, it never overrules. Every
rule is one of two kinds, split by a mechanical line:

* **Integrity** — a finding that *names something that does not exist* (a dangling id, an
  unreadable file). Default severity ``error``; the only kind that fails ``validate``.
* **Advisory** — something is *absent or unconventional*: a session over budget, an hour
  drifting off the home study, a week with no class meeting. Default ``warn``, or
  ``alert`` (high priority, reported first) for the coverage chain.

Severity is resolved as: the course's ``course.yaml`` ``rules:`` → the methodology's
``rules:`` → ``DEFAULT_SEVERITY``. A teacher may also accept one exception in a file's
own front matter (``accepted: [{rule, reason}]``); that rule's findings for that file are
then suppressed, and counted rather than hidden.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .model import Course, Unit

SEVERITIES = ("error", "alert", "warn", "off")

# Every rule the validator knows, with its default severity (spec §8.4). Used when neither
# the course nor the methodology says otherwise. The table is complete on purpose: a rule
# missing from it is a programming error (``report`` raises), and a rule name a teacher
# types that is not in it is a typo worth telling them about (``unknown_rule``).
DEFAULT_SEVERITY = {
    # -- integrity: names something that does not exist --------------------
    "schema": "error",
    "id_consistency": "error",
    "goal_maps_to_objective": "error",
    "outcome_reference": "error",
    "activity_references_guiding_question": "error",
    "item_reference": "error",
    "material_locator_resolves": "error",
    # -- advisory, high priority: the coverage chain -----------------------
    "objective_coverage": "alert",
    # D-040, consistency: a student-facing place points at instructor-only material. An alert,
    # not an error — nothing reaches a student until it is published, and every exporter
    # refuses instructor material in code (the hard guarantee is there).
    "instructor_material_cited": "alert",
    # -- advisory ----------------------------------------------------------
    "schema_unavailable": "warn",
    "unit_count": "warn",
    "session_count": "warn",
    "goal_count": "warn",
    "goal_type": "warn",
    "min_paths_per_goal": "warn",
    "path_estimate_missing": "warn",
    "session_path_feasibility": "warn",
    "in_class_missing": "warn",
    "in_class_duration_match": "warn",
    "activity_count": "warn",
    "activity_type": "warn",
    "require_opening_quiz": "warn",
    "activity_without_guiding_question": "warn",
    "activity_references_other_unit": "warn",
    "item_no_correct_choice": "warn",
    "syllabus_workload_missing": "warn",
    "guiding_question_assessed": "warn",
    "unknown_rule": "warn",
    "accepted_without_reason": "warn",
    "materials_not_ingested": "warn",
    # D-040, consistency: git tracks private material — it is in the repo's history.
    "private_material_committed": "warn",
    # D-041, consistency: course/.gitignore is absent or does not keep private material out of git.
    "course_gitignore_missing": "warn",
    # D-040, consistency: a `M<NNNN>#anchor` in a Markdown body names something that does not
    # exist. Integrity in substance, advisory in severity: prose is read by people and may be a
    # dated snapshot (materials/coverage.md) that legitimately goes stale.
    "material_locator_in_text": "warn",
}

# The order findings are printed in: alerts first (spec §8.4), then errors, then warnings.
REPORT_ORDER = {"alert": 0, "error": 1, "warn": 2}

SCHEMA_FOR = {
    "course": "course.schema.json",
    "syllabus": "syllabus.schema.json",
    "unit": "unit.schema.json",
    "session": "study-session.schema.json",
    "in-class": "in-class-session.schema.json",
    "item": "assessment-item.schema.json",
    "methodology": "methodology.schema.json",
    "manifest": "manifest.schema.json",
}

# Where a material locator (`M0007`, `M0007#slide-18`, spec §8.1) may appear, per artifact: a
# path into the front matter, `*` meaning every element of a list. `material_locator_resolves`
# checks every string these reach. Step 4 adds the guiding question's `answer` (D-019) — and the
# session-level study-path pool (D-020) — as one line each here; the rule itself does not change.
LOCATOR_FIELDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "session": (
        ("goals", "*", "paths", "*", "ref"),  # a study path's resource
    ),
    "in-class": (
        ("activities", "*", "materials", "*"),  # what an activity uses in the room
    ),
}

# The student-facing subset of LOCATOR_FIELDS (D-040): a material cited here is one a student
# is pointed at, so it must not be `audience: instructor` (`instructor_material_cited`). Step 4
# adds the guiding question's `answer[].ref` and the session-level `paths[].ref`; later phases a
# Gem's knowledge files. `activities[].materials` is deliberately absent: the in-class plan is
# the teacher's, and "discuss the manual's solution on p. 13" is legitimate there.
STUDENT_FACING_FIELDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "session": (
        ("goals", "*", "paths", "*", "ref"),  # a study path's resource
    ),
}

# What `course/.gitignore` must list (D-041, `course_gitignore_missing`) — the same two paths
# `classkit doctor` asks git about.
GITIGNORE_REQUIRED = ("materials/source/private/", "materials/private-text/")

# What `private_material_committed` asks git about (D-040). `:(icase)` because macOS git ignores
# `Private/` too, and ingest treats any case of it as private.
PRIVATE_PATHSPECS = (":(icase)materials/source/private", ":(icase)materials/private-text")

# `M0007` or `M0007#slide-18` inside a string — not part of a longer word, a URL path, or an
# anchor of its own.
LOCATOR = re.compile(r"(?<![\w/.#-])(M\d{4})(?!\w)(?:#([\w-]+))?")

# Course files whose Markdown *body* `material_locator_in_text` reads, besides every front-matter
# document (syllabus, units, sessions, in-class, items). Not LOG.md — history: a locator to a
# since-removed material is a true record — and not ingested/ or private-text/, derived text.
PROSE_FILES = (Path("materials") / "coverage.md",)

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _reach(data, path: tuple[str, ...]):
    """Every value at `path` inside `data`, following `*` into lists."""
    if not path:
        yield data
        return
    head, rest = path[0], path[1:]
    if head == "*":
        if isinstance(data, list):
            for element in data:
                yield from _reach(element, rest)
    elif isinstance(data, dict) and head in data:
        yield from _reach(data[head], rest)


_MARK = {"error": "ERROR", "alert": "ALERT", "warn": "warn "}


@dataclass
class Finding:
    level: str  # "error" | "alert" | "warn"
    code: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{_MARK[self.level]}  {self.where}\n       [{self.code}] {self.message}"


@dataclass
class Acceptance:
    """One `accepted:` entry: a teacher's deliberate exception to one rule, in one file."""

    path: Path
    rule: str
    reason: str
    #: findings this entry suppressed in the last run — 0 means it no longer matches anything
    suppressed: list[Finding] = field(default_factory=list)


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


class Validator:
    def __init__(self, course: Course, framework_root: Path):
        self.course = course
        self.framework_root = framework_root
        self.findings: list[Finding] = []
        # Who has the last word (spec §8.4): the course's own `rules:` over the
        # methodology's, over the framework defaults.
        self.rules = {
            **_as_dict(course.methodology.get("rules")),
            **_as_dict(course.config.get("rules")),
        }
        self.acceptances: list[Acceptance] = [
            Acceptance(doc.path.resolve(), str(entry["rule"]), str(entry.get("reason") or "").strip())
            for doc in course.documents()
            for entry in doc.accepted
        ]

    # -- reporting ---------------------------------------------------------

    def severity(self, code: str) -> str:
        if code not in DEFAULT_SEVERITY:
            raise KeyError(f"validation rule {code!r} has no entry in DEFAULT_SEVERITY")
        level = self.rules.get(code, DEFAULT_SEVERITY[code])
        return level if level in SEVERITIES else DEFAULT_SEVERITY[code]

    def report(self, code: str, where: str | Path, message: str) -> None:
        level = self.severity(code)
        if level == "off":
            return
        finding_path = Path(where).resolve()
        where_str = str(where)
        try:
            where_str = str(Path(where_str).relative_to(self.course.root.parent))
        except (ValueError, OSError):
            pass
        finding = Finding(level, code, where_str, message)

        # A teacher's accepted exception for this rule in this file suppresses it — but it
        # is recorded against the acceptance, so `validate` can still count it.
        for acceptance in self.acceptances:
            if acceptance.rule == code and acceptance.path == finding_path:
                acceptance.suppressed.append(finding)
                return
        self.findings.append(finding)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def suppressed(self) -> list[Finding]:
        """Findings a teacher's `accepted:` entry silenced — counted, never shown as noise."""
        return [f for a in self.acceptances for f in a.suppressed]

    def ordered(self) -> list[Finding]:
        """Findings in report order: alerts, then errors, then warnings (stable within each)."""
        return sorted(self.findings, key=lambda f: REPORT_ORDER[f.level])

    # -- entry point -------------------------------------------------------

    def run(self) -> list[Finding]:
        self.course_goal_ids = {
            str(goal.get("id"))
            for unit in self.course.units
            for goal in unit.goals()
            if isinstance(goal, dict)
        }
        self.check_schemas()
        self.check_rule_names()
        self.check_syllabus()
        self.check_unit_count()
        for unit in self.course.units:
            self.check_unit(unit)
        self.check_items()
        self.check_assessment_coverage()
        self.check_materials()
        return self.findings

    # -- layer 1: schema ---------------------------------------------------

    def check_schemas(self) -> None:
        try:
            import jsonschema  # noqa: PLC0415
        except ImportError:
            self.report(
                "schema_unavailable",
                self.course.root / "course.yaml",
                "jsonschema is not installed, so front matter was not schema-checked. "
                "Install the tooling with `pip install -e .` in the framework repo.",
            )
            return

        import json  # noqa: PLC0415

        cache: dict[str, dict] = {}

        def check(kind: str, where: Path, data: dict) -> None:
            if kind not in cache:
                cache[kind] = json.loads(
                    (self.framework_root / "schemas" / SCHEMA_FOR[kind]).read_text(encoding="utf-8")
                )
            validator = jsonschema.Draft202012Validator(cache[kind])
            for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
                location = "/".join(str(p) for p in error.path) or "(root)"
                self.report("schema", where, f"{location}: {error.message}")

        check("course", self.course.root / "course.yaml", self.course.config)
        if self.course.syllabus is not None:
            check("syllabus", self.course.syllabus.path, self.course.syllabus.data)
        check(
            "methodology",
            self.framework_root / "methodologies" / f"{self.course.methodology.get('id')}.yaml",
            self.course.methodology,
        )
        for unit in self.course.units:
            check("unit", unit.doc.path, unit.doc.data)
            for session in unit.sessions:
                check("session", session.path, session.data)
            if unit.in_class:
                check("in-class", unit.in_class.path, unit.in_class.data)
        for item in self.course.items:
            check("item", item.path, item.data)
        manifest = self._manifest()
        if manifest is not None:
            check("manifest", self.course.root / "materials" / "manifest.yaml", manifest)

    # -- layer 2: semantics ------------------------------------------------

    def check_rule_names(self) -> None:
        """A rule name nothing recognises is almost certainly a typo — and a mistyped
        override or acceptance silently does nothing, so the teacher believes a rule is
        handled when it is not. Advisory: the unrecognised entry merely has no effect."""
        known = set(DEFAULT_SEVERITY)
        sources = [
            (self.course.root / "course.yaml", "course.yaml `rules:`",
             _as_dict(self.course.config.get("rules"))),
            (
                self.framework_root / "methodologies" / f"{self.course.methodology.get('id')}.yaml",
                "the methodology's `rules:`",
                _as_dict(self.course.methodology.get("rules")),
            ),
        ]
        for where, label, rules in sources:
            for code in sorted(set(rules) - known):
                self.report("unknown_rule", where, f"{label} names {code!r}, which is not a "
                            "validation rule, so the entry has no effect.")
        for acceptance in self.acceptances:
            if acceptance.rule not in known:
                self.report(
                    "unknown_rule",
                    acceptance.path,
                    f"`accepted:` names {acceptance.rule!r}, which is not a validation rule, "
                    "so it suppresses nothing.",
                )
        # A silenced finding nobody can later explain is what a reason prevents — but a
        # missing reason is the teacher's call, so it is advice, not a failure (D-038).
        for acceptance in self.acceptances:
            if not acceptance.reason:
                self.report(
                    "accepted_without_reason",
                    acceptance.path,
                    f"`accepted:` for {acceptance.rule!r} gives no `reason`. It still takes "
                    "effect; a reason is what lets someone understand the exception next year.",
                )

    def check_syllabus(self) -> None:
        """The syllabus's own checks. The coverage chain between Course Outcomes and unit
        objectives is checked separately, once objectives carry `outcomes`.

        `workload` is optional (D-031d) so a teacher can draft and validate a syllabus
        before credits are settled — but a syllabus that never gains one is a syllabus
        nobody can plan against, so its absence is a standing warning rather than silence.
        """
        syllabus = self.course.syllabus
        where = self.course.root / "syllabus" / "syllabus.md"

        if syllabus is None:
            self.report(
                "syllabus_workload_missing",
                where,
                "there is no syllabus/syllabus.md, so the course declares no workload. "
                "Run `classkit scaffold course` to create the skeleton.",
            )
            return

        if not syllabus.data.get("workload"):
            self.report(
                "syllabus_workload_missing",
                syllabus.path,
                "the syllabus declares no workload. Fill in `workload` (credits, "
                "credit_system, and optionally total_hours) once they are settled.",
            )

    def check_unit_count(self) -> None:
        declared = self.course.config.get("units")
        actual = len(self.course.units)
        if not isinstance(declared, int):
            return
        if actual > declared:
            self.report(
                "unit_count",
                self.course.root / "course.yaml",
                f"course.yaml declares {declared} units but {actual} exist on disk.",
            )
        elif actual < declared:
            self.report(
                "unit_count",
                self.course.root / "course.yaml",
                f"{actual} of {declared} units exist so far.",
            )

    def check_unit(self, unit: Unit) -> None:
        methodology = self.course.methodology
        home = methodology.get("home_study", {})
        in_class_cfg = methodology.get("in_class", {})

        objective_ids = {o.get("id") for o in unit.objectives if isinstance(o, dict)}
        goal_ids: set[str] = set()

        # --- objectives roll up to Course Outcomes that exist (D-021, D-037). Whether an
        # objective names any outcome at all is advisory, and lands with the coverage chain.
        outcome_ids = {str(o.get("id")) for o in self.course.outcomes}
        for objective in unit.objectives:
            if not isinstance(objective, dict):
                continue
            for outcome in objective.get("outcomes") or []:
                if outcome not in outcome_ids:
                    self.report(
                        "outcome_reference",
                        unit.doc.path,
                        f"objective {objective.get('id')} rolls up to {outcome!r}, which the "
                        "syllabus does not declare as a Course Outcome.",
                    )

        # --- study sessions
        expected_sessions = home.get("sessions_per_unit")
        if isinstance(expected_sessions, int) and len(unit.sessions) != expected_sessions:
            self.report(
                "session_count",
                unit.doc.path,
                f"{unit.id} has {len(unit.sessions)} study sessions; "
                f"methodology '{methodology.get('id')}' expects {expected_sessions}.",
            )

        goal_range = home.get("goals_per_session") or {}
        allowed_types = home.get("allowed_goal_types") or []
        min_paths = (methodology.get("study_paths") or {}).get("min_paths_per_goal", 1)

        for session in unit.sessions:
            goals = session.data.get("goals") or []

            if goal_range:
                low, high = goal_range.get("min"), goal_range.get("max")
                if isinstance(low, int) and isinstance(high, int) and not low <= len(goals) <= high:
                    self.report(
                        "goal_count",
                        session.path,
                        f"{session.id} has {len(goals)} goals; methodology expects {low}-{high}.",
                    )

            if session.data.get("unit") != unit.id:
                self.report(
                    "id_consistency",
                    session.path,
                    f"{session.id} declares unit {session.data.get('unit')!r}, "
                    f"but sits in {unit.id}.",
                )

            number = session.data.get("number")
            if isinstance(number, int):
                expected_id = f"{unit.id}-S{number:02d}"
                if session.id != expected_id:
                    self.report(
                        "id_consistency",
                        session.path,
                        f"id {session.id!r} does not match unit+number (expected {expected_id!r}).",
                    )

            for goal in goals:
                if not isinstance(goal, dict):
                    continue
                goal_id = str(goal.get("id", ""))
                goal_ids.add(goal_id)

                if goal_id and not goal_id.startswith(f"{session.id}-G"):
                    self.report(
                        "id_consistency",
                        session.path,
                        f"goal {goal_id!r} is not prefixed by its session id {session.id!r}.",
                    )

                if allowed_types and goal.get("type") not in allowed_types:
                    self.report(
                        "goal_type",
                        session.path,
                        f"{goal_id}: type {goal.get('type')!r} is not allowed by methodology "
                        f"'{methodology.get('id')}' (allowed: {', '.join(allowed_types)}).",
                    )

                for objective in goal.get("objectives") or []:
                    if objective not in objective_ids:
                        self.report(
                            "goal_maps_to_objective",
                            session.path,
                            f"{goal_id} references objective {objective!r}, "
                            f"which {unit.id} does not define.",
                        )

                paths = goal.get("paths") or []
                if len(paths) < min_paths:
                    self.report(
                        "min_paths_per_goal",
                        session.path,
                        f"{goal_id} has {len(paths)} study paths; at least {min_paths} required.",
                    )

            self.check_session_feasibility(session, goals)

        # --- objective coverage
        covered = {
            objective
            for session in unit.sessions
            for goal in (session.data.get("goals") or [])
            if isinstance(goal, dict)
            for objective in (goal.get("objectives") or [])
        }
        for objective in sorted(o for o in objective_ids if o):
            if objective not in covered:
                self.report(
                    "objective_coverage",
                    unit.doc.path,
                    f"objective {objective} is not addressed by any guiding question.",
                )

        # --- in-class session
        if unit.in_class is None:
            self.report("in_class_missing", unit.doc.path, f"{unit.id} has no in-class.md.")
            return

        self.check_in_class(unit, goal_ids, in_class_cfg)

    def check_session_feasibility(self, session, goals: list) -> None:
        """At least one complete path through every goal must fit the session budget."""
        constants = self.course.time_constants
        budget = session.data.get("duration_minutes") or (
            self.course.methodology.get("home_study", {}).get("session_minutes")
        )
        if not isinstance(budget, (int, float)):
            return

        total = float(constants.get("session_overhead_minutes", 0) or 0)
        unknown: list[str] = []

        for goal in goals:
            if not isinstance(goal, dict):
                continue
            estimates = [
                est
                for est in (self._estimate_path(p, constants) for p in goal.get("paths") or [])
                if est is not None
            ]
            if estimates:
                total += min(estimates)
            else:
                unknown.append(str(goal.get("id", "?")))

        if unknown:
            self.report(
                "path_estimate_missing",
                session.path,
                f"no time estimate for any path of {', '.join(unknown)}; "
                f"the {budget}-minute budget could not be fully verified.",
            )

        if total > budget:
            self.report(
                "session_path_feasibility",
                session.path,
                f"{session.id}: the fastest complete path takes ~{total:.0f} min "
                f"but the session budget is {budget} min. Trim goals, or add a shorter path.",
            )

    @staticmethod
    def _estimate_path(path: dict, constants: dict) -> float | None:
        if not isinstance(path, dict):
            return None
        explicit = path.get("est_minutes")
        if isinstance(explicit, (int, float)):
            return float(explicit)
        defaults = {
            "gem": constants.get("gem_minutes_per_goal"),
            "exercise": constants.get("exercise_default_minutes"),
        }
        fallback = defaults.get(path.get("kind"))
        return float(fallback) if isinstance(fallback, (int, float)) else None

    def check_in_class(self, unit: Unit, goal_ids: set[str], config: dict) -> None:
        doc = unit.in_class
        activities = doc.data.get("activities") or []

        expected_minutes = config.get("minutes")
        declared = doc.data.get("duration_minutes")
        tolerance = config.get("duration_tolerance_minutes", 5)

        if isinstance(expected_minutes, int) and declared != expected_minutes:
            self.report(
                "in_class_duration_match",
                doc.path,
                f"declares {declared} min; methodology expects {expected_minutes}.",
            )

        total = sum(
            a.get("duration_minutes", 0)
            for a in activities
            if isinstance(a, dict) and isinstance(a.get("duration_minutes"), (int, float))
        )
        if isinstance(declared, (int, float)) and abs(total - declared) > tolerance:
            self.report(
                "in_class_duration_match",
                doc.path,
                f"activities total {total} min but the session is {declared} min "
                f"(tolerance ±{tolerance}).",
            )

        count_range = config.get("activities") or {}
        low, high = count_range.get("min"), count_range.get("max")
        if isinstance(low, int) and isinstance(high, int) and not low <= len(activities) <= high:
            self.report(
                "activity_count",
                doc.path,
                f"{len(activities)} activities; methodology expects {low}-{high}.",
            )

        if config.get("require_opening_quiz"):
            first = activities[0] if activities else None
            if not isinstance(first, dict) or first.get("type") != "quiz":
                self.report(
                    "require_opening_quiz",
                    doc.path,
                    "the first activity must be a quiz — it is what makes the meeting "
                    "depend on the prework rather than restate it.",
                )

        allowed = config.get("allowed_activity_types") or []
        for activity in activities:
            if not isinstance(activity, dict):
                continue
            activity_id = str(activity.get("id", "?"))

            if activity_id and not activity_id.startswith(f"{unit.id}-A"):
                self.report(
                    "id_consistency",
                    doc.path,
                    f"activity {activity_id!r} is not prefixed by its unit id {unit.id!r}.",
                )

            if allowed and activity.get("type") not in allowed:
                self.report(
                    "activity_type",
                    doc.path,
                    f"{activity_id}: type {activity.get('type')!r} is not allowed "
                    f"(allowed: {', '.join(allowed)}).",
                )

            # One concern, three findings (D-028, D-037): naming a guiding question that does
            # not exist is broken data; naming one from another unit, or naming none, is a
            # departure the teacher may have meant.
            referenced = activity.get("guiding_questions") or []
            if not referenced:
                self.report(
                    "activity_without_guiding_question",
                    doc.path,
                    f"{activity_id} references no guiding question. Most activities should "
                    "build on the home study, or the hour drifts back into a lecture.",
                )
            for goal_id in referenced:
                if goal_id in goal_ids:
                    continue
                if goal_id in self.course_goal_ids:
                    self.report(
                        "activity_references_other_unit",
                        doc.path,
                        f"{activity_id} references {goal_id!r}, a guiding question of another "
                        f"unit rather than {unit.id}.",
                    )
                else:
                    self.report(
                        "activity_references_guiding_question",
                        doc.path,
                        f"{activity_id} references {goal_id!r}, which is not a guiding "
                        "question anywhere in this course.",
                    )

    def check_items(self) -> None:
        all_goal_ids = self.course_goal_ids
        unit_ids = {unit.id for unit in self.course.units}

        for item in self.course.items:
            if item.data.get("unit") not in unit_ids:
                self.report(
                    "item_reference",
                    item.path,
                    f"{item.id} belongs to unit {item.data.get('unit')!r}, which does not exist.",
                )
            for goal_id in item.data.get("guiding_questions") or []:
                if goal_id not in all_goal_ids:
                    self.report(
                        "item_reference",
                        item.path,
                        f"{item.id} tests {goal_id!r}, which is not a guiding question "
                        "anywhere in this course.",
                    )
            choices = item.data.get("choices") or []
            if choices and not any(c.get("correct") for c in choices if isinstance(c, dict)):
                self.report(
                    "item_no_correct_choice",
                    item.path,
                    f"{item.id} has no choice marked correct.",
                )

    def check_assessment_coverage(self) -> None:
        assessed = {
            goal_id
            for item in self.course.items
            for goal_id in (item.data.get("guiding_questions") or [])
        }
        for unit in self.course.units:
            for session in unit.sessions:
                for goal in session.data.get("goals") or []:
                    if not isinstance(goal, dict):
                        continue
                    goal_id = str(goal.get("id"))
                    if goal_id not in assessed:
                        self.report(
                            "guiding_question_assessed",
                            session.path,
                            f"{goal_id} is not tested by any assessment item.",
                        )


    # -- materials (D-035) ---------------------------------------------------

    def _manifest(self) -> list | None:
        """The materials manifest, or None if there is none — or if it cannot be read, which
        is reported once, as an integrity error (an unreadable file)."""
        if hasattr(self, "_manifest_cache"):
            return self._manifest_cache
        from .ingest.manifest import ManifestError, load  # noqa: PLC0415

        path = self.course.root / "materials" / "manifest.yaml"
        self._manifest_cache = None
        if path.is_file():
            try:
                self._manifest_cache = load(self.course.root)
            except ManifestError as exc:
                self.report("schema", path, f"cannot be read: {exc}")
        return self._manifest_cache

    def check_materials(self) -> None:
        self.check_course_gitignore()
        self.check_material_locators()
        self.check_locators_in_text()
        self.check_instructor_material()
        self.check_materials_ingested()
        self.check_private_material_committed()

    def _cited(self, table: dict[str, tuple[tuple[str, ...], ...]]) -> list[tuple[object, str, str | None]]:
        """Every material locator in the fields `table` names: (document, material id, anchor)."""
        documents: list[tuple[str, object]] = []
        for unit in self.course.units:
            documents += [("session", s) for s in unit.sessions]
            if unit.in_class is not None:
                documents.append(("in-class", unit.in_class))
        return [
            (doc, match.group(1), match.group(2))
            for kind, doc in documents
            for field_path in table.get(kind, ())
            for value in _reach(doc.data, field_path)
            if isinstance(value, str)
            for match in LOCATOR.finditer(value)
        ]

    def check_material_locators(self) -> None:
        """Every `M<NNNN>` / `M<NNNN>#anchor` names a material that exists and, if it names an
        anchor, a heading that exists in that material's ingested file (D-035). Integrity: a
        fabricated "slide 18" of a 12-slide deck is a reference to something that does not exist.
        It proves the place exists — not that the answer is there; that is the critic's job.

        A private material's committed file is its index (D-040), which has every anchor of the
        full text — so its locators resolve on every clone, with or without the book."""
        for doc, material_id, anchor in self._cited(LOCATOR_FIELDS):
            problem = self._locator_problem(material_id, anchor)
            if problem:
                locator = material_id + (f"#{anchor}" if anchor else "")
                self.report("material_locator_resolves", doc.path, f"cites {locator}, but {problem}")

    def check_locators_in_text(self) -> None:
        """`material_locator_in_text` (D-040): the same check over `M<NNNN>#anchor` in the Markdown
        bodies of the course's own files. A warning, not an error, though it names something that
        does not exist: front matter is data tools act on; prose is read by people, and may be a
        dated snapshot. Only fully qualified locators with an anchor are read — a bare `M0007` in
        prose may be anything, and the shorthand `#page-39` cannot be told from an ordinary
        Markdown link. HTML comments (a template's instructions) are skipped. A consistency rule."""
        bodies: list[tuple[Path, str]] = [(doc.path, doc.body) for doc in self.course.documents()]
        for relative in PROSE_FILES:
            path = self.course.root / relative
            if not path.is_file():
                continue
            try:
                bodies.append((path, _body(path.read_text(encoding="utf-8"))))
            except (OSError, UnicodeDecodeError):
                continue
        for path, body in bodies:
            seen: set[str] = set()
            for match in LOCATOR.finditer(_HTML_COMMENT.sub("", body or "")):
                material_id, anchor = match.group(1), match.group(2)
                if not anchor or match.group(0) in seen:
                    continue
                seen.add(match.group(0))
                problem = self._locator_problem(material_id, anchor)
                if problem:
                    self.report("material_locator_in_text", path,
                                f"the text cites {match.group(0)}, but {problem}")

    def _locator_problem(self, material_id: str, anchor: str | None) -> str | None:
        """Why `material_id` / `material_id#anchor` does not resolve — or None when it does. The
        one definition both locator rules share. It proves the place exists, not that the answer
        is there; that is the critic's job. A private material's committed file is its index
        (D-040), which has every anchor of the full text, so its locators resolve on every clone."""
        from .ingest import extract, ingested_file  # noqa: PLC0415

        manifest = self._manifest()
        if not hasattr(self, "_materials"):
            self._materials = {str(r.get("id")): r for r in (manifest or []) if isinstance(r, dict)}
            self._anchors: dict[str, list[str] | None] = {}
        record = self._materials.get(material_id)
        if manifest is None:
            return "no materials have been ingested (there is no materials/manifest.yaml). Run /ingest."
        if record is None:
            return f"{material_id} is not in materials/manifest.yaml."
        if record.get("merged_into"):
            return (f"{material_id} was merged into {record['merged_into']}; cite "
                    f"{record['merged_into']} instead (its anchors may differ).")
        if record.get("removed_at"):
            return f"the source of {material_id} was removed (marked {record['removed_at']})."
        if not anchor:
            return None
        if record.get("status") not in ("ingested", "no-text"):
            return (f"{material_id} is a {record.get('status')} material, which has no "
                    f"anchors; cite {material_id} alone (a timestamp goes in the note).")
        if material_id not in self._anchors:
            path = ingested_file(self.course.root, material_id)
            try:
                self._anchors[material_id] = extract.anchors(_body(path.read_text(encoding="utf-8"))) if path else None
            except (OSError, UnicodeDecodeError):
                self._anchors[material_id] = None
        known = self._anchors[material_id]
        if known is None:
            return f"the ingested file of {material_id} is missing or unreadable. Run /ingest."
        if anchor.rstrip("-") not in known:
            return f"{material_id} has no anchor {anchor!r} ({_summarize(known)})."
        return None

    def check_instructor_material(self) -> None:
        """A student-facing place (STUDENT_FACING_FIELDS) cites a material whose `audience` is
        `instructor` — a solutions manual in a study path (D-040). Advisory, high priority: the
        teacher may mean it, and nothing reaches a student until it is published; the hard
        guarantee is the exporters' refusal. A consistency rule."""
        cited = self._cited(STUDENT_FACING_FIELDS)
        if not cited:
            return
        materials = {str(r.get("id")): r for r in (self._manifest() or []) if isinstance(r, dict)}
        for doc, material_id, anchor in cited:
            record = materials.get(material_id)
            if record is None or record.get("audience") != "instructor":
                continue
            locator = material_id + (f"#{anchor}" if anchor else "")
            self.report(
                "instructor_material_cited",
                doc.path,
                f"cites {locator} in a study path, but {material_id} ({record.get('title')}) is "
                "for instructors only (audience: instructor) — students would be pointed at it. "
                "Cite it from the in-class plan instead; or, if students may see it, "
                f"`classkit material set {material_id} --audience student`.",
            )

    def check_course_gitignore(self) -> None:
        """`course/.gitignore` is absent, or does not list `materials/source/private/` and
        `materials/private-text/` (D-041). Committed state, the same on every clone — so it
        catches the clone that never received the file. It reads the file, so it cannot see one
        present here but never committed; `classkit doctor`, which asks git, catches that. A
        consistency rule."""
        path = self.course.root / ".gitignore"
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.report(
                "course_gitignore_missing", path,
                "the course has no .gitignore, so nothing keeps private material "
                "(materials/source/private/, materials/private-text/) out of git. Re-run "
                "`classkit scaffold course --code CODE --title TITLE` — it only creates what is missing.",
            )
            return
        except (OSError, UnicodeDecodeError):
            text = ""
        listed = {line.strip().lstrip("/").rstrip("/") for line in text.splitlines()
                  if line.strip() and not line.lstrip().startswith("#")}
        missing = [p for p in GITIGNORE_REQUIRED if p.rstrip("/") not in listed]
        if missing:
            self.report(
                "course_gitignore_missing", path,
                f"course/.gitignore does not list {' or '.join(missing)}, so private material "
                f"there would be committed. Add the line{'s' if len(missing) > 1 else ''} "
                f"{', '.join(f'`{m}`' for m in missing)}.",
            )

    def check_private_material_committed(self) -> None:
        """Git tracks a file under `materials/source/private/` or `materials/private-text/`
        (D-040): it is in the repository's history, and the .gitignore did not stop it — it was
        added before, or forced. Detecting is the framework's; cleaning history is the
        teacher's. Asks git, so every clone gets the same answer; outside a git repository, or
        without git, it is skipped silently (`classkit doctor` says why). A consistency rule."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "-z", "--", *PRIVATE_PATHSPECS],
                cwd=self.course.root, capture_output=True, check=False,
            )
        except OSError:
            return
        if result.returncode != 0:
            return  # not a git repository
        tracked = [p for p in result.stdout.decode("utf-8", "replace").split("\0") if p]
        if not tracked:
            return
        shown = ", ".join(tracked[:5]) + (f", and {len(tracked) - 5} more" if len(tracked) > 5 else "")
        self.report(
            "private_material_committed",
            self.course.root / "materials" / "manifest.yaml",
            f"git tracks {len(tracked)} private file(s): {shown}. They are in the repository's "
            "history, so anyone with the repo has them. `git rm --cached PATH` stops tracking a "
            "file from the next commit; removing it from history (e.g. git filter-repo) is your "
            "decision. Run `classkit doctor` to check that course/.gitignore covers private/.",
        )

    def check_materials_ingested(self) -> None:
        """A source file that is new, changed, moved or gone since the last ingest — the
        manifest, and so every locator check, is out of date. Advisory: the teacher may be
        mid-way through adding material.

        Ignores `source/private/` (D-040): what is there differs per machine, and `validate`
        must give the same answer on every clone. `classkit doctor` reports it."""
        from .ingest import core, links  # noqa: PLC0415
        from .ingest.manifest import ManifestError, load  # noqa: PLC0415

        try:
            records = load(self.course.root)
        except ManifestError:
            return  # already reported as unreadable
        files = core.scan(self.course.root)
        listed = links.read(self.course.root / "materials" / "source")
        _state, plan = core.reconcile(self.course.root, [r for r in records if isinstance(r, dict)],
                                      files, listed, local=False)
        outstanding = plan.outstanding()
        if not outstanding:
            return
        shown = "; ".join(outstanding[:5]) + (f"; and {len(outstanding) - 5} more" if len(outstanding) > 5 else "")
        self.report(
            "materials_not_ingested",
            self.course.root / "materials" / "manifest.yaml",
            f"{len(outstanding)} change(s) in materials/source/ since the last ingest — {shown}. "
            "Run /ingest (or `classkit ingest`).",
        )


def _body(text: str) -> str:
    """An ingested file's body — anchors are its headings, never its front matter."""
    from .frontmatter import FrontMatterError, parse  # noqa: PLC0415

    try:
        return parse(text)[1]
    except FrontMatterError:
        return text  # a hand edit that dropped the front matter still has its headings


def _summarize(anchors: list[str]) -> str:
    """What anchors a material does have, briefly: 'slide-1 … slide-12', or the first few."""
    if not anchors:
        return "it has no anchors"
    for prefix in ("slide", "page"):
        numbered = [a for a in anchors if re.fullmatch(rf"{prefix}-\d+", a)]
        if numbered and len(numbered) == len(anchors):
            return f"it has {numbered[0]} … {numbered[-1]}"
    head = ", ".join(anchors[:6])
    return f"it has {head}" + (f", … ({len(anchors)} in all)" if len(anchors) > 6 else "")


def validate(course: Course, framework_root: Path) -> list[Finding]:
    return Validator(course, framework_root).run()
