# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1af7c-0a26-7595-b8b5-ac403bdbdb4f"
#   revision: 1
#   title: "somnus watch: run the always-on watcher in the foreground (D20)"
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
#       - target_ref: "urn:somnus:artifact:01a1af7c-0a26-7595-b8b5-ac403bdbdb4f"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-watch-run-the-always-on-watcher-in-the-foreground-d20"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1af7c-0a26-7595-b8b5-ac403bdbdb4f"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""``somnus watch``: run the always-on watcher in the foreground (D20)."""

from __future__ import annotations

from pathlib import Path

from somnus.commands._common import Ctx, note
from somnus.watch import Settings, Watcher


def run(args, ctx: Ctx) -> int:
    """Poll the registered roots (or the named ones) until stopped; ``--once`` makes one pass."""
    settings = Settings.from_config(ctx.cfg, interval=args.interval, settle=args.settle, stamp=args.stamp,
                                    adopt=True if args.adopt else None, revise=args.revise)
    watcher = Watcher(ctx.cfg.home, settings, roots=[Path(r).resolve() for r in args.roots],
                      log=note if not args.quiet else (lambda message: None))
    return watcher.run(once=args.once)
