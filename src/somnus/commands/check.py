"""``somnus check``: run the validation pipeline and print diagnostics."""

from __future__ import annotations

from pathlib import Path

from somnus import document as D
from somnus.commands._common import Ctx, display, note, walk
from somnus.model.validate import validate
from somnus.output import EXIT_INVALID, EXIT_OK, Diagnostic, SomnusError

_MARKDOWN = {".md", ".markdown", ".mdx"}


def run(args, ctx: Ctx) -> int:
    """Validate named files, walked directories, or every configured root."""
    explicit = [Path(p).resolve() for p in args.paths]
    roots = explicit if explicit and not args.all else [*explicit, *ctx.cfg.roots]
    named = {p for p in explicit if p.is_file()}
    diags: list[Diagnostic] = []
    docs: list[D.Document] = []
    for p in explicit:
        if not p.exists():
            diags.append(Diagnostic(display(p), 0, 0, "error", "E_IO", "-", "file not found"))
    for path in walk([r for r in roots if r.exists()], ctx.cfg.exclude):
        try:
            doc = D.load(path)
        except SomnusError as exc:
            diags.extend(exc.diagnostics)
            continue
        unmanaged = doc.envelope is None and not doc.issues
        if unmanaged and path not in named:
            if path.suffix.lower() in _MARKDOWN:
                diags.append(Diagnostic(display(path), 1, 1, "warning", "W_UNMANAGED", "-",
                                        "Markdown file has no Somnus header (see 'somnus stamp')"))
            continue
        docs.append(doc)
    resolver = ctx.resolver() if args.level in ("semantic", "canon") else None
    if resolver is not None:
        for doc in docs:
            if doc.payload is not None:
                resolver.add_payload(doc.payload)
    for doc in docs:
        diags.extend(validate(doc, args.level, resolver))
    ctx.diagnostics(diags)
    errors = sum(1 for d in diags if d.is_error)
    note(f"checked {len(docs)} file(s) at level {args.level}: {errors} error(s), {len(diags) - errors} warning(s)")
    return EXIT_INVALID if errors else EXIT_OK
