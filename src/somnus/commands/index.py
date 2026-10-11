"""``somnus index``: reconcile roots into the registry."""

from __future__ import annotations

from pathlib import Path

from somnus.commands._common import Ctx, note
from somnus.output import EXIT_INVALID, EXIT_OK


def run(args, ctx: Ctx) -> int:
    """Scan the named roots, or every registered root (falling back to configured roots)."""
    with ctx.store() as st:
        if args.roots:
            roots = [Path(r).resolve() for r in args.roots]
        else:
            roots = [r for _, r in st.roots()] or ctx.cfg.roots
        report = st.scan(roots, exclude=ctx.cfg.exclude, full=args.full)
    ctx.diagnostics(report.diagnostics)
    note(report.summary())
    failed = any(d.is_error for d in report.diagnostics) or report.conflicts_opened > 0
    return EXIT_INVALID if failed else EXIT_OK
