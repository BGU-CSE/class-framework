"""Ingest (D-035, spec §8.7): turn whatever a teacher already has into something every later
agent can read and cite precisely.

    materials/source/      the teacher's — any files, any structure; never modified here
      links.md             the course's links, one per line
    materials/ingested/    derived — one .md per material, flat, named by a stable id
    materials/manifest.yaml

Private material (D-040) lives under `source/private/`: gitignored, with only an index committed
in `ingested/` and its full text in the gitignored `materials/private-text/`.

`extract` converts one file (a registry keyed by extension); `links` reads and appends to
`links.md`; `manifest` reads and writes the manifest; `core` scans, reconciles, runs, and
records the classifying agent's decisions.
"""

from .core import (
    MaterialError,
    Plan,
    Preflight,
    RunReport,
    apply,
    merge,
    preflight,
    reconcile,
    remove,
    run,
    scan,
    set_fields,
)
from .extract import anchors
from .manifest import INGESTED_DIR, MANIFEST, SOURCE_DIR, ManifestError, ingested_file, load

__all__ = [
    "INGESTED_DIR", "MANIFEST", "SOURCE_DIR", "ManifestError", "MaterialError", "Plan",
    "Preflight", "RunReport", "anchors", "apply", "ingested_file", "load", "merge", "preflight",
    "reconcile", "remove", "run", "scan", "set_fields",
]
