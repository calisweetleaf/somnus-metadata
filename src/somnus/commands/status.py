"""``somnus status``: validated lifecycle transition (new revision)."""

from __future__ import annotations

from pathlib import Path

from somnus import ids
from somnus.commands._common import Ctx, commit, display, load_valid, note, refuse
from somnus.model.lifecycle import apply_transition, check_transition
from somnus.output import EXIT_OK, EXIT_USAGE, SomnusError


def run(args, ctx: Ctx) -> int:
    """Apply one permitted transition and write the new revision."""
    path = Path(args.path).resolve()
    doc = load_valid(path)
    payload = doc.copy_payload()
    current = payload["lifecycle"]["status"]
    refs = []
    for raw in args.replacement:
        ref = ids.normalize_legacy_ref(raw.strip())
        if not ids.is_reference_string(ref):
            raise SomnusError(f"--replacement {raw!r} is not a Somnus URN or external reference", EXIT_USAGE)
        refs.append({"ref": ref})
    existing = payload["lifecycle"].get("replacement_refs", [])
    problems = check_transition(current, args.new_status, args.reason, [*existing, *refs])
    if problems:
        raise refuse(doc.meta_path, "E_LIFECYCLE", "; ".join(problems), "somnus.lifecycle.status")
    new = apply_transition(payload, args.new_status, args.reason, refs)
    commit(doc, new)
    ctx.record("status", doc.path, new["id"], new["revision"], f"{current} -> {args.new_status}",
               resolve=("revision",))
    note(f"{display(doc.meta_path)}: {current} -> {args.new_status} (revision {new['revision']})")
    if new["authority"].get("standing") != payload["authority"].get("standing"):
        note("reactivation reset authority standing to 'candidate'; renewed review is required")
    return EXIT_OK
