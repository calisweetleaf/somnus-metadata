"""``somnus bump``: new revision; resolves revision conflicts."""

from __future__ import annotations

from pathlib import Path

from somnus.commands._common import Ctx, commit, display, load_valid, note
from somnus.model.lifecycle import bump_revision
from somnus.output import EXIT_OK


def run(args, ctx: Ctx) -> int:
    """Increment the revision, stamp ``time.updated_at``, and re-index."""
    path = Path(args.path).resolve()
    doc = load_valid(path)
    payload = doc.copy_payload()
    old = payload["revision"]
    bump_revision(payload)
    commit(doc, payload)
    detail = f"{old} -> {payload['revision']}" + (f": {args.reason.strip()}" if args.reason else "")
    ctx.record("bump", doc.path, payload["id"], payload["revision"], detail, resolve=("revision", "identity"))
    note(f"{display(doc.meta_path)}: revision {old} -> {payload['revision']}")
    return EXIT_OK
