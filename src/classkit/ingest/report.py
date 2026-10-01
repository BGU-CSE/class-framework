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
    if p.private:
        lines.append(f"Private:      {p.private} file(s) under private/ — an index is committed, the full "
                     "text stays on this machine")
    lines.append(f"Links:        {p.links_listed} in links.md (a link becomes a material only "
                 "when it is listed there)")
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
    if not (r.converted or r.refused or r.kept or r.plan.outstanding()):
        return "Nothing to do: every source is already ingested."

    plan = r.plan
    for mid, old, new in plan.moved:
        lines.append(f"  moved      {mid}  {old} → {new} (same id)")
    for mid, path in plan.duplicates:
        lines.append(f"  duplicate  {mid}  + {path} (identical; merged)")
    for mid, path in plan.gone:
        lines.append(f"  gone       {mid}  - {path} (a copy; the material remains)")
    for mid in plan.removed:
        if mid in plan.unharvested:
            lines.append(f"  removed    {mid}  a link found inside a material, not in links.md — links "
                         "come only from links.md now; `classkit add-url` brings it back under this id")
        else:
            lines.append(f"  removed    {mid}  source deleted — marked removed, not forgotten")
    for mid, path in plan.restored:
        lines.append(f"  restored   {mid}  {path}")
    for c in r.converted:
        if c.local:
            lines.append(f"  full text  {c.id}  → {c.full_text} (this machine only; nothing committed changed)")
            continue
        label = "new" if c.new else "updated"
        where = f" → {c.ingested}" if c.ingested else ""
        if c.full_text:
            where += f" (index) + {c.full_text} (full text, this machine only)"
        reason = f"  ({c.reason})" if c.reason else ""
        lines.append(f"  {label:<10} {c.id}  [{c.status}] {c.path}{where}{reason}")
    for mid in r.kept:
        lines.append(f"  kept       {mid}  your edit kept; the changed source is marked as seen")

    if r.refused:
        lines += ["", "REFUSED — replacing these files could lose edits made by hand:"]
        for refusal in r.refused:
            lines.append(f"  {refusal.id}  {refusal.ingested} — {refusal.reason}")
            lines += [f"      | {line}" for line in refusal.preview.splitlines()]
        lines += [
            "Ask the teacher, then re-run with either",
            "  --overwrite ID   replace the edit with a fresh extraction, or",
            "  --keep ID        keep the edit and mark the changed source as seen.",
        ]

    created = sum(1 for c in r.converted if c.new)
    updated = sum(1 for c in r.converted if not c.new and not c.local)
    local = sum(1 for c in r.converted if c.local)
    lines += ["", f"{created} new materials, {updated} updated, {len(r.refused)} refused."
              + (f" {local} private full text(s) written on this machine only." if local else "")]
    return "\n".join(lines)


def _ids(label: str, ids: list[str], limit: int = 12) -> str:
    ids = sorted(dict.fromkeys(ids))
    shown = ", ".join(ids[:limit]) + (f" (+{len(ids) - limit} more)" if len(ids) > limit else "")
    return f"{label} {shown}"


def log_summary(r: RunReport) -> str | None:
    """What a run changed in the course, by material id — the `changed` line of its course-log
    entry (§8.8). None when it changed nothing: a run that only reports, or only refuses, is not
    an entry."""
    plan = r.plan
    parts = []
    new = [c.id for c in r.converted if c.new]
    if new:
        parts.append(_ids("new", new))
    # A private material's full text written on this machine alone changed nothing committed —
    # it is not a change to the course, so it is not logged.
    updated = [c.id for c in r.converted if not c.new and not c.local]
    if updated:
        parts.append(_ids("updated", updated))
    if r.kept:
        parts.append(_ids("hand edit kept", r.kept))
    if plan.moved:
        parts.append(_ids("moved", [mid for mid, _, _ in plan.moved]))
    if plan.duplicates:
        parts.append(_ids("identical copy merged into", [mid for mid, _ in plan.duplicates]))
    if plan.detached:
        parts.append(_ids("copy split off from", [mid for mid, _ in plan.detached]))
    if plan.gone:
        parts.append(_ids("copy removed from", [mid for mid, _ in plan.gone]))
    if plan.removed:
        parts.append(_ids("removed", plan.removed))
    if plan.restored:
        parts.append(_ids("restored", [mid for mid, _ in plan.restored]))
    return "materials: " + "; ".join(parts) if parts else None
