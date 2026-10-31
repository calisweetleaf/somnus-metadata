"""``somnus index``: reconcile roots into the registry."""

from __future__ import annotations

from pathlib import Path

from somnus.commands._common import Ctx, note
from somnus.output import EXIT_INVALID, EXIT_OK, EXIT_USAGE, SomnusError

UNMANAGED_SHOWN = 10


def run(args, ctx: Ctx) -> int:
    """Scan the named roots, or every registered root (falling back to configured roots)."""
    with ctx.store() as st:
        if args.roots:
            roots = [Path(r).resolve() for r in args.roots]
        else:
            roots = [r for _, r in st.roots()]
            if not roots:
                roots = ctx.cfg.roots
                broad = [r for r in roots if r == Path.home().resolve() or r == Path(r.anchor)]
                if broad:
                    raise SomnusError(f"no roots are registered and the fallback {broad[0]} is too broad to scan;"
                                      " register a project with 'somnus init --root DIR' or name one:"
                                      " 'somnus index DIR'", EXIT_USAGE)
        report = st.scan(roots, exclude=ctx.cfg.exclude, full=args.full)
    ctx.diagnostics(report.diagnostics)
    note(report.summary())
    if report.unmanaged_paths:
        shown = report.unmanaged_paths[:UNMANAGED_SHOWN]
        more = len(report.unmanaged_paths) - len(shown)
        note("unmanaged (no Somnus header, so not searchable): " + ", ".join(shown)
             + (f", and {more} more" if more else ""))
        note("adopt one with 'somnus stamp PATH' (preview) then 'somnus stamp PATH --write'")
    failed = any(d.is_error for d in report.diagnostics) or report.conflicts_opened > 0
    return EXIT_INVALID if failed else EXIT_OK
