"""``somnus stale``: stale drafts, unresolved replacements, missing files, near-duplicates, open conflicts."""

from __future__ import annotations

import difflib
import time

from somnus import yamlsub
from somnus.commands._common import Ctx
from somnus.output import EXIT_OK


def _findings(conn, days: int) -> list[list[object]]:
    rows: list[list[object]] = []
    cutoff = time.time() - days * 86400
    present = {aid for (aid,) in conn.execute("SELECT DISTINCT artifact_id FROM locations WHERE present = 1")}
    for aid, title, status, newest in conn.execute(
        "SELECT a.id, a.title, a.status, max(l.file_mtime) FROM artifacts a"
        " JOIN locations l ON l.artifact_id = a.id AND l.present = 1"
        " WHERE a.status IN ('draft', 'proposed') GROUP BY a.id ORDER BY a.id"
    ):
        if newest is not None and newest < cutoff:
            age = int((time.time() - newest) // 86400)
            rows.append([f"stale-{status}", aid, title, f"unchanged for {age} days"])
    for aid, title, header in conn.execute(
        "SELECT a.id, a.title, r.header_yaml FROM artifacts a"
        " JOIN revisions r ON r.artifact_id = a.id AND r.revision = a.current_revision"
        " WHERE a.status = 'superseded' ORDER BY a.id"
    ):
        try:
            refs = yamlsub.parse(header).data["somnus"]["lifecycle"].get("replacement_refs", [])
        except (yamlsub.YAMLError, KeyError, TypeError) as exc:
            rows.append(["unreadable-header", aid, title, str(exc)])
            continue
        unresolved = [r["ref"] for r in refs if r.get("ref", "").startswith("urn:somnus:artifact:")
                      and r["ref"] not in present]
        if unresolved:
            rows.append(["unresolved-replacement", aid, title, ", ".join(unresolved)])
    for aid, title in conn.execute(
        "SELECT id, title FROM artifacts a WHERE NOT EXISTS"
        " (SELECT 1 FROM locations l WHERE l.artifact_id = a.id AND l.present = 1) ORDER BY id"
    ):
        rows.append(["missing-file", aid, title, "no present location"])
    titles = conn.execute(
        "SELECT DISTINCT id, title FROM docs ORDER BY id"
    ).fetchall()
    for i, (a_id, a_title) in enumerate(titles):
        for b_id, b_title in titles[i + 1:]:
            ratio = difflib.SequenceMatcher(None, a_title.casefold(), b_title.casefold()).ratio()
            if ratio >= 0.85:
                rows.append(["near-duplicate-title", a_id, a_title, f"{b_id} {b_title!r} ({ratio:.2f})"])
    for cid, kind, aid, detail in conn.execute(
        "SELECT id, kind, artifact_id, detail FROM open_conflicts ORDER BY id"
    ):
        rows.append([f"conflict-{kind}", aid, "", detail.splitlines()[0] if detail else f"conflict {cid}"])
    return rows


def run(args, ctx: Ctx) -> int:
    """Print one row per finding (report only; exit 0)."""
    conn = ctx.readonly()
    try:
        rows = _findings(conn, max(args.days, 0))
    finally:
        conn.close()
    ctx.table(["finding", "artifact", "title", "detail"], rows)
    return EXIT_OK
