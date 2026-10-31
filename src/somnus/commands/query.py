"""``somnus q``: read-only registry queries and full-text search."""

from __future__ import annotations

from somnus.commands._common import Ctx
from somnus.db import run_query
from somnus.db.store import fts_query
from somnus.output import EXIT_OK, EXIT_USAGE, SomnusError

SHORTCUTS = {
    "docs": "SELECT id, title, type, status, standing, revision, path FROM docs ORDER BY path",
    "conflicts": "SELECT id, kind, artifact_id, revision, path, detail, opened_at FROM open_conflicts ORDER BY id",
    "history": "SELECT id, at, actor, action, artifact_id, revision, path, detail FROM history",
    "tables": "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')"
              " AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'search!_%' ESCAPE '!' ORDER BY type, name",
}

# Column weights follow search.sql order: path, title, summary, tags, body.
SEARCH = ("SELECT a.id, a.title, a.type, a.status, search.path,"
          " snippet(search, -1, '[', ']', '...', 12) AS excerpt"
          " FROM search JOIN locations l ON l.id = search.rowid AND l.present = 1"
          " JOIN artifacts a ON a.id = l.artifact_id"
          " WHERE search MATCH ? ORDER BY bm25(search, 2.0, 10.0, 5.0, 5.0, 1.0), search.path")


def run(args, ctx: Ctx) -> int:
    """Run SQL, a shortcut (default ``--docs``), or a ``--text`` full-text search on a read-only connection."""
    params: tuple = ()
    if args.text is not None:
        if args.sql:
            raise SomnusError("give either SQL or --text, not both", EXIT_USAGE)
        match = fts_query(args.text)
        if not match:
            raise SomnusError("--text needs at least one search word", EXIT_USAGE)
        sql, params = SEARCH, (match,)
    else:
        chosen = next((k for k in SHORTCUTS if getattr(args, k)), None)
        sql = SHORTCUTS[chosen] if chosen else (args.sql or SHORTCUTS["docs"])
    conn = ctx.readonly()
    try:
        if params and conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'search'").fetchone() is None:
            raise SomnusError("the registry has no full-text index yet; run 'somnus index'"
                              " (needs SQLite with FTS5)", EXIT_USAGE)
        headers, rows = run_query(conn, sql, params, limit=args.limit)
    finally:
        conn.close()
    ctx.table(headers, rows)
    return EXIT_OK
