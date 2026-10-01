"""The teacher / framework-developer hat (D-034).

The marker's whole design rests on it being gitignored — a committed marker would put
every teacher's clone into framework-developer mode — so the test that matters most is
the one asserting we refuse to create it in a repo that would track it.
"""

from __future__ import annotations

import subprocess

import pytest

from classkit.mode import (
    DEVELOPER,
    MARKER,
    TEACHER,
    UnsafeMarker,
    current_mode,
    is_ignored,
    set_mode,
)


def git(*args: str, cwd) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    """A git repo shaped like the framework: a dev/ directory and a tracked .gitignore."""
    git("init", "-q", cwd=tmp_path)
    (tmp_path / "dev").mkdir()
    (tmp_path / ".gitignore").write_text("dev/.developer\n", encoding="utf-8")
    git("add", ".gitignore", cwd=tmp_path)
    return tmp_path


def test_default_is_teacher(repo):
    assert current_mode(repo) == TEACHER


def test_switch_to_developer_and_back(repo):
    change = set_mode(repo, DEVELOPER)
    assert change.changed and change.mode == DEVELOPER
    assert (repo / MARKER).exists()
    assert current_mode(repo) == DEVELOPER

    change = set_mode(repo, TEACHER)
    assert change.changed and change.mode == TEACHER
    assert not (repo / MARKER).exists()
    assert current_mode(repo) == TEACHER


def test_switching_is_idempotent(repo):
    set_mode(repo, DEVELOPER)
    again = set_mode(repo, DEVELOPER)
    assert not again.changed
    assert current_mode(repo) == DEVELOPER

    set_mode(repo, TEACHER)
    again = set_mode(repo, TEACHER)
    assert not again.changed


def test_refuses_when_the_marker_would_not_be_ignored(repo):
    """The guard that matters: without the ignore rule the marker could be committed,
    and a committed marker flips every teacher's clone into developer mode."""
    (repo / ".gitignore").write_text("# nothing ignored here\n", encoding="utf-8")

    with pytest.raises(UnsafeMarker):
        set_mode(repo, DEVELOPER)

    # and nothing was left behind
    assert not (repo / MARKER).exists()
    assert current_mode(repo) == TEACHER


def test_refuses_when_gitignore_itself_is_not_tracked(tmp_path):
    """D-041: the ignore rule protects other checkouts only if .gitignore is committed. A global
    excludes file that ignores `.gitignore` leaves the rule on this machine alone."""
    git("init", "-q", cwd=tmp_path)
    (tmp_path / "dev").mkdir()
    (tmp_path / ".gitignore").write_text("dev/.developer\n", encoding="utf-8")  # never added

    with pytest.raises(UnsafeMarker, match="not tracked"):
        set_mode(tmp_path, DEVELOPER)
    assert not (tmp_path / MARKER).exists()

    git("add", ".gitignore", cwd=tmp_path)
    assert set_mode(tmp_path, DEVELOPER).mode == DEVELOPER


def test_the_framework_gitignore_ignores_finder_litter():
    from classkit.model import find_framework_root

    root = find_framework_root()
    assert ".DS_Store" in (root / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_ignore_check_reports_unknown_outside_a_git_repo(tmp_path):
    (tmp_path / "dev").mkdir()
    assert is_ignored(tmp_path, MARKER) is None
    # ...and switching still works, since there is no commit to protect against
    assert set_mode(tmp_path, DEVELOPER).mode == DEVELOPER


def test_the_marker_really_is_ignored_in_this_repository():
    """Guards the actual framework checkout, not a fixture: if the rule is ever dropped
    (or .gitignore stops being tracked, as it once was), this fails."""
    from classkit.model import find_framework_root

    root = find_framework_root()
    assert is_ignored(root, MARKER) is True
