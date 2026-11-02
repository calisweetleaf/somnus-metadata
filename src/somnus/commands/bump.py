# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7de0-76aa-bc57-104f543a1e7c"
#   revision: 1
#   title: "somnus bump: new revision; resolves revision conflicts"
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
#       - target_ref: "urn:somnus:artifact:01a19a67-7de0-76aa-bc57-104f543a1e7c"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-bump-new-revision-resolves-revision-conflicts"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7de0-76aa-bc57-104f543a1e7c"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
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
