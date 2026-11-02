# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7e78-76aa-947c-08e81fb976f7"
#   revision: 1
#   title: "somnus mcp: serve the non-interactive commands as Model Context Protocol tools over stdio"
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
#       - target_ref: "urn:somnus:artifact:01a19a67-7e78-76aa-947c-08e81fb976f7"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-mcp-serve-the-non-interactive-commands-as-model-context-protocol-tools-ov"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7e78-76aa-947c-08e81fb976f7"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""``somnus mcp``: serve the non-interactive commands as Model Context Protocol tools over stdio."""

from __future__ import annotations

from somnus.commands._common import Ctx


def run(args, ctx: Ctx) -> int:
    """Serve until the client closes stdin; ``--actor`` is passed to every tool call."""
    from somnus.mcp import serve

    return serve(actor=ctx.actor_override)
