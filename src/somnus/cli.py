"""Argument parsing and lazy command dispatch for the ``somnus`` CLI (SPEC Â§20)."""

from __future__ import annotations

import argparse
import importlib
import sys
import traceback
from typing import Optional, Sequence

from somnus import __version__
from somnus.model import vocab
from somnus.output import EXIT_INVALID, EXIT_USAGE, SomnusError

STATUSES = vocab.STATUSES


def _globals(parser: argparse.ArgumentParser, suppress: bool) -> None:
    default = argparse.SUPPRESS if suppress else None
    parser.add_argument("--actor", metavar="NAME", default=default, help="actor recorded in the event ledger")
    parser.add_argument("--tsv", action="store_true", default=argparse.SUPPRESS if suppress else False,
                        help="tab-separated output")
    parser.add_argument("--no-color", dest="no_color", action="store_true",
                        default=argparse.SUPPRESS if suppress else False, help="disable ANSI color")
    parser.add_argument("--debug", action="store_true", default=argparse.SUPPRESS if suppress else False,
                        help="show tracebacks for internal errors")


def build_parser() -> argparse.ArgumentParser:
    """Construct the full argument parser."""
    common = argparse.ArgumentParser(add_help=False)
    _globals(common, suppress=True)
    parser = argparse.ArgumentParser(prog="somnus", description="Somnus metadata toolkit (core 2.0.0).")
    parser.add_argument("--version", action="version", version=f"somnus {__version__}")
    _globals(parser, suppress=False)
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    def cmd(name: str, help_text: str) -> argparse.ArgumentParser:
        return sub.add_parser(name, help=help_text, description=help_text, parents=[common])

    p = cmd("init", "create $SOMNUS_HOME, config.toml, and the registry; register roots")
    p.add_argument("--root", action="append", default=[], metavar="DIR", help="root directory to register")

    p = cmd("new", "scaffold a conformant Markdown artifact")
    p.add_argument("type", choices=vocab.TYPES, metavar="TYPE", help="artifact type")
    p.add_argument("title", metavar="TITLE")
    p.add_argument("--dir", default=".", help="target directory (default: current)")
    p.add_argument("--carrier", choices=("frontmatter", "html-comment"), default="frontmatter")
    p.add_argument("--status", choices=STATUSES, default="draft")
    p.add_argument("--force", action="store_true", help="create despite a similar registered title")

    p = cmd("stamp", "infer and inject a header into unmanaged files (dry-run diff unless --write)")
    p.add_argument("paths", nargs="+", metavar="PATH")
    p.add_argument("--write", action="store_true")
    p.add_argument("--type", choices=vocab.TYPES)
    p.add_argument("--title")

    p = cmd("check", "validate documents and print diagnostics")
    p.add_argument("paths", nargs="*", metavar="PATH")
    p.add_argument("--all", action="store_true", help="check every configured root")
    p.add_argument("--level", choices=vocab.LEVELS, default="core")

    p = cmd("index", "reconcile roots into the registry")
    p.add_argument("roots", nargs="*", metavar="ROOT")
    p.add_argument("--full", action="store_true", help="re-read files even when mtime and size are unchanged")

    p = cmd("q", "read-only registry queries")
    p.add_argument("sql", nargs="?", metavar="SQL")
    shortcut = p.add_mutually_exclusive_group()
    shortcut.add_argument("--docs", action="store_true")
    shortcut.add_argument("--conflicts", action="store_true")
    shortcut.add_argument("--history", action="store_true")
    shortcut.add_argument("--tables", action="store_true")
    p.add_argument("--limit", type=int, metavar="N")

    p = cmd("ls", "list present artifacts")
    p.add_argument("--type", choices=vocab.TYPES)
    p.add_argument("--status", choices=STATUSES)
    p.add_argument("--standing", choices=vocab.STANDINGS)
    p.add_argument("--tag")
    p.add_argument("--path-contains", dest="path_contains")

    p = cmd("status", "validated lifecycle transition (new revision)")
    p.add_argument("path", metavar="PATH")
    p.add_argument("new_status", choices=STATUSES, metavar="NEW_STATUS")
    p.add_argument("--reason")
    p.add_argument("--replacement", action="append", default=[], metavar="REF")

    p = cmd("bump", "new revision; resolves revision conflicts")
    p.add_argument("path", metavar="PATH")
    p.add_argument("--reason")

    p = cmd("fork", "new artifact derived from an existing revision")
    p.add_argument("path", metavar="PATH")
    p.add_argument("--out")
    p.add_argument("--title")

    p = cmd("regions", "audit region markers against the registry")
    p.add_argument("path", metavar="PATH")
    p.add_argument("--sync", action="store_true", help="register unregistered markers")
    p.add_argument("--write", action="store_true")

    p = cmd("migrate", "upgrade v0.1 documents (dry-run diff unless --write)")
    p.add_argument("paths", nargs="+", metavar="PATH")
    p.add_argument("--write", action="store_true")

    p = cmd("stale", "report stale drafts, missing files, near-duplicates, and conflicts")
    p.add_argument("--days", type=int, default=30, metavar="N")

    p = cmd("schema", "field documentation or JSON Schema export")
    p.add_argument("field", nargs="?", metavar="FIELD")
    p.add_argument("--json-schema", dest="json_schema", action="store_true")
    p.add_argument("--out")

    cmd("brief", "print a Markdown agent cheat sheet")

    p = cmd("edit", "terminal UI: document browser, or header editor")
    p.add_argument("path", nargs="?", metavar="PATH")
    return parser


_MODULES = {"q": "query"}


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point; returns the process exit code."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else EXIT_USAGE
    if not args.command:
        parser.print_help()
        return EXIT_USAGE
    from somnus.commands._common import Ctx, note

    ctx = Ctx(actor_override=args.actor, tsv=args.tsv, no_color=args.no_color, debug=args.debug)
    module = importlib.import_module(f"somnus.commands.{_MODULES.get(args.command, args.command)}")
    try:
        return int(module.run(args, ctx))
    except SomnusError as exc:
        ctx.diagnostics(exc.diagnostics)
        return exc.exit_code
    except KeyboardInterrupt:
        note("interrupted")
        return EXIT_INVALID
    except Exception as exc:  # noqa: BLE001 - last-resort boundary: report, never hide
        if args.debug:
            traceback.print_exc()
        else:
            note(f"somnus: internal error: {type(exc).__name__}: {exc} (rerun with --debug for a traceback)")
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
