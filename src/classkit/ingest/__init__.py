"""Ingest (D-035, spec §8.7): turn whatever a teacher already has into something every later
agent can read and cite precisely.

    materials/source/      the teacher's — any files, any structure; never modified here
      links.md             the course's links, one per line
    materials/ingested/    derived — one .md per material, flat, named by a stable id
    materials/manifest.yaml

`extract` converts one file (a registry keyed by extension); `links` reads and appends to
`links.md`; `manifest` reads and writes the manifest; `core` scans, reconciles, runs, and
records the classifying agent's decisions.
"""

from .core import (
    MaterialError,
    Plan,
    Preflight,
    RunReport,
    merge,
    preflight,
    reconcile,
    run,
    scan,
    set_fields,
    suspected_duplicates,
)
from .extract import anchors
from .manifest import INGESTED_DIR, MANIFEST, SOURCE_DIR, ManifestError, ingested_file, load

__all__ = [
    "INGESTED_DIR", "MANIFEST", "SOURCE_DIR", "ManifestError", "MaterialError", "Plan",
    "Preflight", "RunReport", "anchors", "ingested_file", "load", "merge", "preflight",
    "reconcile", "run", "scan", "set_fields", "suspected_duplicates",
]
