"""``somnus mcp``: serve the non-interactive commands as Model Context Protocol tools over stdio."""

from __future__ import annotations

from somnus.commands._common import Ctx


def run(args, ctx: Ctx) -> int:
    """Serve until the client closes stdin; ``--actor`` is passed to every tool call."""
    from somnus.mcp import serve

    return serve(actor=ctx.actor_override)
