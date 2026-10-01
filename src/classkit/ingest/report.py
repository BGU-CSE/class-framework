"""Plain-text reports for `classkit ingest` — what the teacher reads at the approval gate."""

from __future__ import annotations

from .core import Preflight, RunReport


def _size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def _duration(seconds: float) -> str:
    if seconds < 60:
        return "under a minute"
    minutes = round(seconds / 60)
    return f"about {minutes} minute{'s' if minutes != 1 else ''}"


def preflight_text(p: Preflight) -> str:
    lines = ["Pre-flight — nothing has been converted or written.", ""]
    if not p.files and not p.links_listed:
        lines.append("materials/source/ is empty: no files, and no links in links.md.")
        return "\n".join(lines)

    formats = ", ".join(f"{count} {fmt}" for fmt, count in p.by_format.items()) or "none"
    lines.append(f"Files:        {len(p.files)} ({_size(p.size)}) — {formats}")
    lines.append(f"Slides/pages: {p.slides} slides, {p.pages} PDF pages")
    lines.append(f"Links:        {p.links_listed} in links.md, {p.embedded_links} embedded in "
                 "slides and documents (recorded during conversion)")
    for number, text in p.plan.rejected_link_lines:
        lines.append(f"              links.md line {number} is not a link, ignored: {text}")
    lines.append("")

    plan = p.plan
    lines.append(
        f"Since the last ingest: {sum(len(n.paths) for n in plan.new)} new, "
        f"{len(plan.changed)} changed, {len(plan.moved)} moved or renamed, "
        f"{len(plan.removed)} removed, {len(plan.unchanged)} unchanged; "
        f"{len(plan.new_links)} new links."
    )
    if plan.moved:
        lines += [f"  moved    {mid}: {old} → {new}" for mid, old, new in plan.moved]
    if plan.removed:
        lines += [f"  removed  {mid} (kept in the manifest, marked removed)" for mid in plan.removed]
    lines.append("")

    if p.exact_duplicates:
        lines.append("Exact duplicates (identical files — merged automatically):")
        lines += [f"  {' = '.join(group)}" for group in p.exact_duplicates]
        lines.append("")
    if p.suspected_duplicates:
        lines.append("Suspected duplicates (same name, different format — you will be asked to confirm):")
        lines += [f"  {' ~ '.join(group)}" for group in p.suspected_duplicates]
        lines.append("")
    if p.unsupported:
        lines.append("Cannot be read — recorded as unsupported, never dropped:")
        lines += [f"  {path}: {reason}" for path, reason in p.unsupported]
        lines.append("")
    if p.media:
        lines.append("Audio/video — recorded, content not extracted:")
        lines += [f"  {path}" for path in p.media]
        lines.append("")

    lines.append(f"To convert: {p.to_convert} materials. Estimated time: {_duration(p.seconds)}.")
    return "\n".join(lines)


def run_text(r: RunReport) -> str:
    lines = []
    if not (r.converted or r.found_links or r.refused or r.kept or r.plan.outstanding()):
        return "Nothing to do: every source is already ingested."

    plan = r.plan
    for mid, old, new in plan.moved:
        lines.append(f"  moved      {mid}  {old} → {new} (same id)")
    for mid, path in plan.duplicates:
        lines.append(f"  duplicate  {mid}  + {path} (identical; merged)")
    for mid, path in plan.gone:
        lines.append(f"  gone       {mid}  - {path} (a copy; the material remains)")
    for mid in plan.removed:
        lines.append(f"  removed    {mid}  source deleted — marked removed, not forgotten")
    for mid, path in plan.restored:
        lines.append(f"  restored   {mid}  {path}")
    for c in r.converted:
        label = "new" if c.new else "updated"
        where = f" → {c.ingested}" if c.ingested else ""
        reason = f"  ({c.reason})" if c.reason else ""
        lines.append(f"  {label:<10} {c.id}  [{c.status}] {c.path}{where}{reason}")
    for c in r.found_links:
        lines.append(f"  link       {c.id}  {c.path}")
    for mid in r.kept:
        lines.append(f"  kept       {mid}  your edit kept; the changed source is marked as seen")

    if r.refused:
        lines += ["", "REFUSED — these ingested files were edited by hand, and their source has changed:"]
        for refusal in r.refused:
            lines.append(f"  {refusal.id}  {refusal.ingested}")
            lines += [f"      | {line}" for line in refusal.preview.splitlines()]
        lines += [
            "Ask the teacher, then re-run with either",
            "  --overwrite ID   replace the edit with a fresh extraction, or",
            "  --keep ID        keep the edit and mark the changed source as seen.",
        ]

    if r.suspected_duplicates:
        lines += ["", "Suspected duplicates — ask the teacher; merge only on confirmation:"]
        for a, b, why in r.suspected_duplicates:
            lines.append(f"  {a} ~ {b}: {why}")
        lines.append("  classkit material merge ID --into ID   (into the one whose anchors to keep — "
                     "a deck over its PDF)")

    created = sum(1 for c in r.converted if c.new) + len(r.found_links)
    lines += ["", f"{created} new materials, {sum(1 for c in r.converted if not c.new)} updated, "
              f"{len(r.refused)} refused."]
    return "\n".join(lines)
