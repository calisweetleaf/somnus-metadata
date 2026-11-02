# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7e68-738e-97bd-223ea237089a"
#   revision: 1
#   title: "somnus ls: list present artifacts"
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
#       - target_ref: "urn:somnus:artifact:01a19a67-7e68-738e-97bd-223ea237089a"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-ls-list-present-artifacts"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7e68-738e-97bd-223ea237089a"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""``somnus ls``: list present artifacts."""

from __future__ import annotations

from somnus.commands._common import Ctx
from somnus.db import Store
from somnus.output import EXIT_OK


def run(args, ctx: Ctx) -> int:
    """Filter the ``docs`` view."""
    conn = ctx.readonly()
    try:
        rows = Store(conn, ctx.cfg.db_path, ctx.actor).list_docs(
            type=args.type, status=args.status, standing=args.standing, tag=args.tag,
            path_contains=args.path_contains)
    finally:
        conn.close()
    ctx.table(["id", "title", "type", "status", "standing", "revision", "path"], rows)
    return EXIT_OK
