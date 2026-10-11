"""``somnus q``: read-only registry queries."""

from __future__ import annotations

from somnus.commands._common import Ctx
from somnus.db import run_query
from somnus.output import EXIT_OK

SHORTCUTS = {
    "docs": "SELECT id, title, type, status, standing, revision, path FROM docs ORDER BY path",
    "conflicts": "SELECT id, kind, artifact_id, revision, path, detail, opened_at FROM open_conflicts ORDER BY id",
    "history": "SELECT id, at, actor, action, artifact_id, revision, path, detail FROM history",
    "tables": "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')"
              " AND name NOT LIKE 'sqlite_%' ORDER BY type, name",
}


def run(args, ctx: Ctx) -> int:
    """Run SQL or a shortcut (default ``--docs``) against a read-only connection."""
    chosen = next((k for k in SHORTCUTS if getattr(args, k)), None)
    sql = SHORTCUTS[chosen] if chosen else (args.sql or SHORTCUTS["docs"])
    conn = ctx.readonly()
    try:
        headers, rows = run_query(conn, sql, limit=args.limit)
    finally:
        conn.close()
    ctx.table(headers, rows)
    return EXIT_OK
