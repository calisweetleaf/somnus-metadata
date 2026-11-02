# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7e06-70fb-9b2f-6dee4c686644"
#   revision: 1
#   title: "somnus edit: terminal UI (document browser, or header editor for one file)"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a19a67-7e06-70fb-9b2f-6dee4c686644"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-edit-terminal-ui-document-browser-or-header-editor-for-one-file"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7e06-70fb-9b2f-6dee4c686644"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
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
