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
