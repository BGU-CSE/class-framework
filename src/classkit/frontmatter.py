"""Parsing for Markdown files with YAML front matter (D-019)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(?P<fm>.*?)\r?\n---[ \t]*(?:\r?\n(?P<body>.*))?\Z", re.S)


class FrontMatterError(ValueError):
    """The file is missing front matter, or its YAML does not parse."""


def parse(text: str) -> tuple[dict, str]:
    """Split a Markdown document into its front-matter mapping and its body."""
    match = _FRONT_MATTER.match(text)
    if not match:
        raise FrontMatterError("no YAML front matter (file must start with a '---' line)")

    try:
        data = yaml.safe_load(match.group("fm"))
    except yaml.YAMLError as exc:
        raise FrontMatterError(f"front matter is not valid YAML: {exc}") from exc

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise FrontMatterError("front matter must be a mapping, not a list or scalar")

    return data, match.group("body") or ""


def load(path: Path) -> tuple[dict, str]:
    """Parse the file at `path`, raising FrontMatterError with the path attached."""
    try:
        return parse(path.read_text(encoding="utf-8"))
    except FrontMatterError as exc:
        raise FrontMatterError(f"{path}: {exc}") from exc


def load_yaml(path: Path) -> dict:
    """Load a plain YAML file that must contain a mapping."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping at the top level")
    return data
