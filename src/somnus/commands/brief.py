# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7dd0-7013-8d7c-5fdf050b0118"
#   revision: 1
#   title: "somnus brief: a Markdown cheat sheet for agent instruction files"
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
#       - target_ref: "urn:somnus:artifact:01a19a67-7dd0-7013-8d7c-5fdf050b0118"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-brief-a-markdown-cheat-sheet-for-agent-instruction-files"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7dd0-7013-8d7c-5fdf050b0118"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""``somnus brief``: a Markdown cheat sheet for agent instruction files."""

from __future__ import annotations

from somnus import CORE_SCHEMA
from somnus.commands._common import Ctx
from somnus.output import EXIT_OK, emit

BRIEF = f"""## Somnus metadata (core `{CORE_SCHEMA}`)

Normative contract: `SPEC.md`. Every managed file carries exactly one `somnus:` envelope
(Markdown frontmatter, a comment envelope in code/config files, or a `<file>.somnus.yaml` sidecar).

**Rules for agents**

- Never hand-invent IDs, dates, actors, licenses, evidence, or acceptance records.
- Never edit `id`. Any change to the header or body that should be indexed is a new `revision` (`somnus bump`).
- Lifecycle changes go through `somnus status`, never by editing `lifecycle.status` directly.
- Title, summary, purpose, classification, tags, visibility, and disposition change with `somnus set`,
  not by hand-editing the envelope.
- Unknown fields are errors. Put tool-specific data under `extensions.<owner>`.
- Region markers (`<!-- somnus:region:begin r-id -->` … `end`) carry identity only; register them with
  `somnus regions PATH --sync --write`.
- `normative` role is intent, not acceptance. Only `authority.standing: accepted` with an acceptance
  record is authoritative.

**Commands**

| Need | Command |
| --- | --- |
| New document | `somnus new TYPE "Title" [--dir DIR]` |
| Adopt an existing file | `somnus stamp PATH` (diff) then `--write` |
| Validate | `somnus check PATH… [--level core\\|semantic\\|canon]` |
| Change status | `somnus status PATH NEW_STATUS [--reason …] [--replacement URN]` |
| Edit header fields | `somnus set PATH title="…" "classification.tags=a, b" [--reason …]` |
| New revision | `somnus bump PATH [--reason …]` |
| Derive a copy | `somnus fork PATH [--title …]` |
| Upgrade v0.1 | `somnus migrate PATH` then `--write` |
| Registry | `somnus index`, `somnus ls`, `somnus q --docs\\|--conflicts\\|--history`, `somnus stale` |
| Search content | `somnus q --text "words to find"` (every word must match; `word*` is a prefix) |
| Field docs | `somnus schema classification.type` |
| MCP tools | `somnus mcp` (stdio server; every command above as a tool) |

Exit codes: `0` ok, `1` validation errors/refusals/conflicts, `2` usage or I/O errors.
"""


def run(args, ctx: Ctx) -> int:
    """Print the cheat sheet."""
    emit(BRIEF)
    return EXIT_OK
