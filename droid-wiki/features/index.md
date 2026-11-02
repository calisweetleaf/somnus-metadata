---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a67-79f7-720f-b44d-3a507a8d3970"
  revision: 1
  title: "Features"
  classification:
    category: "context"
    type: "index"
    role: "informative"
    scope: "component"
    tags: []
  lifecycle:
    status: "draft"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a19a67-79f7-720f-b44d-3a507a8d3970"
        aspects: ["content"]
  time: {}
  names:
    slug: "features"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19a67-79f7-720f-b44d-3a507a8d3970"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Features

These pages describe what the `somnus` CLI does for a user or an agent, one workflow per page. Each page explains the behavior, the commands involved, and the source files to change. For the subsystems underneath (carriers, validation, the registry), see the systems pages linked from each feature page.

| Page | What it covers |
| --- | --- |
| [CLI commands](cli-commands.md) | All 18 subcommands, global flags, the lazy dispatcher, and the shared `Ctx` command context. |
| [Adopting files](adopting-files.md) | `somnus new` and `somnus stamp`: scaffolding new artifacts and inferring headers for existing files. |
| [Lifecycle and revisions](lifecycle-and-revisions.md) | `somnus status`, `somnus bump`, and `somnus fork`: the lifecycle state machine, revision increments, and derived artifacts. |
| [Migration from v0.1](migration.md) | `somnus migrate`: upgrading v0.1 hybrid frontmatter and `:::submatter` directives to core 2.0.0. |
| [Querying the registry](querying.md) | `somnus index`, `q --text`, SQL queries, `ls`, `stale`, `regions`, and `check --all`: full-text search and registry reconciliation (`src/somnus/commands/query.py`). |
| [Agent integration](agent-integration.md) | `somnus brief`, `somnus schema`, `somnus set`, and `somnus mcp`: the agent cheat sheet, per-field documentation, non-interactive header edits, and the MCP server. |

Related: [Architecture](../overview/architecture.md), [Getting started](../overview/getting-started.md), [Glossary](../overview/glossary.md).
