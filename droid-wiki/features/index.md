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
