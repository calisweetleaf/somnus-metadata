# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7ee7-71dd-8f51-ad6fde32ae72"
#   revision: 1
#   title: "somnus regions: audit body markers against knowledge.regions; optionally register them"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a19a67-7ee7-71dd-8f51-ad6fde32ae72"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-regions-audit-body-markers-against-knowledge-regions-optionally-register"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7ee7-71dd-8f51-ad6fde32ae72"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""``somnus regions``: audit body markers against ``knowledge.regions``; optionally register them."""

from __future__ import annotations

from pathlib import Path

from somnus.commands._common import Ctx, commit, display, load_valid, note, unified
from somnus.model.lifecycle import bump_revision
from somnus.output import EXIT_INVALID, EXIT_OK, Diagnostic, emit
from somnus.regions import scan_markers, sync_registry


def run(args, ctx: Ctx) -> int:
    """Print the marker table; with ``--sync`` register unregistered markers (diff unless ``--write``)."""
    path = Path(args.path).resolve()
    doc = load_valid(path)
    payload = doc.copy_payload()
    scan = scan_markers(doc.lines, doc.carrier.region_style, doc.ignore_span, host=doc.carrier.name)
    regions = payload.get("knowledge", {}).get("regions", [])
    by_marker = {r["selector"]["name"]: r for r in regions if r["selector"]["kind"] == "marker"}
    rows = []
    for rid, rng in sorted(scan.ranges.items(), key=lambda kv: kv[1].begin_line):
        reg = by_marker.get(rid)
        rows.append([rid, rng.begin_line, rng.end_line, rng.depth, rng.parent or "-",
                     reg["kind"] if reg else "-", "yes" if reg else "no"])
    for name, reg in sorted(by_marker.items()):
        if name not in scan.ranges:
            rows.append([name, "-", "-", "-", "-", reg["kind"], "missing markers"])
    ctx.table(["marker", "begin", "end", "depth", "parent", "kind", "registered"], rows)
    shown = display(doc.meta_path)
    issues = [Diagnostic(shown, line, col, "warning" if code.startswith("W_") else "error", code, "-", msg)
              for line, col, code, msg in scan.issues]
    ctx.diagnostics(issues)
    if not args.sync:
        unregistered = [r for r in scan.ranges if r not in by_marker]
        if unregistered:
            note(f"{len(unregistered)} unregistered marker(s); run with --sync to register")
        return EXIT_INVALID if any(d.is_error for d in issues) else EXIT_OK
    if any(d.is_error for d in issues):
        note("refusing to sync while marker errors remain")
        return EXIT_INVALID
    added, missing = sync_registry(payload, scan)
    for name in missing:
        note(f"registered region {name!r} has no body markers (left in place)")
    if not added:
        note("registry already lists every marker")
        return EXIT_OK
    bump_revision(payload)
    old = "".join(line + end for line, end in zip(doc.lines, doc.endings, strict=True))
    text = commit(doc, payload, write=args.write)
    if not args.write:
        emit(unified(old, text, shown))
        return EXIT_OK
    ctx.record("regions.sync", doc.path, payload["id"], payload["revision"], "registered " + ", ".join(added),
               resolve=("revision",))
    note(f"{shown}: registered {', '.join(added)} (revision {payload['revision']})")
    return EXIT_OK
