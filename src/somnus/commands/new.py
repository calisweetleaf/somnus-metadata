"""``somnus new``: scaffold a conformant Markdown artifact."""

from __future__ import annotations

from pathlib import Path

from somnus import document as D
from somnus import ids
from somnus.commands._common import Ctx, check_text, inferred_payload, note, refuse
from somnus.db import Store
from somnus.model.lifecycle import now_utc
from somnus.output import EXIT_OK, EXIT_USAGE, SomnusError, emit


def run(args, ctx: Ctx) -> int:
    """Create ``<slug>.md`` with a fresh UUIDv7 at revision 1."""
    title = args.title.strip()
    if not title:
        raise SomnusError("title must not be empty", EXIT_USAGE)
    directory = Path(args.dir).resolve()
    if not directory.is_dir():
        raise SomnusError(f"directory {directory} does not exist", EXIT_USAGE)
    target = directory / f"{ids.slugify(title)}.md"
    if target.exists():
        raise refuse(target, "E_IO", "file already exists; choose another title or --dir")
    if ctx.registry_exists() and not args.force:
        conn = ctx.readonly()
        try:
            similar = Store(conn, ctx.cfg.db_path, ctx.actor).similar_titles(title, threshold=0.9)
        finally:
            conn.close()
        if similar:
            listing = "; ".join(f"{t!r} ({aid})" for aid, t, _ in similar[:3])
            raise refuse(target, "E_IO", f"title collides with registered artifacts: {listing}; use --force")
    payload = inferred_payload(ctx.cfg, target, [], type_=args.type, title=title, status=args.status,
                               created_at=now_utc())
    doc = D.from_text(target, f"# {title}\n")
    text = doc.render(payload, args.carrier)
    check_text(target, text)
    D.atomic_write(target, text)
    ctx.record("new", target, payload["id"], 1, f"{args.type}: {title}")
    emit(str(target))
    note(f"created {payload['id']} revision 1")
    return EXIT_OK
