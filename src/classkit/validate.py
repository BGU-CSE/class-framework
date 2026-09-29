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
    # -- advisory, high priority: the coverage chain -----------------------
    "objective_coverage": "alert",
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
}


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
            Acceptance(doc.path.resolve(), str(entry["rule"]), str(entry.get("reason", "")))
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


def validate(course: Course, framework_root: Path) -> list[Finding]:
    return Validator(course, framework_root).run()
