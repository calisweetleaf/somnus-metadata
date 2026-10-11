"""``somnus edit``: terminal UI (document browser, or header editor for one file)."""

from __future__ import annotations

import sys
from pathlib import Path

from somnus.commands._common import Ctx
from somnus.output import EXIT_USAGE, SomnusError


def run(args, ctx: Ctx) -> int:
    """Launch the full-screen UI; requires an interactive terminal."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise SomnusError("somnus edit needs an interactive terminal", EXIT_USAGE)
    from somnus.tui.app import main

    return main(ctx, Path(args.path).resolve() if args.path else None)
