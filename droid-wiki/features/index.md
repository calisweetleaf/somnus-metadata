# Features

Active contributors: Trey

These pages describe what the `somnus` CLI does for a user or an agent, one workflow per page. Each page explains the behavior, the commands involved, and the source files to change. For the subsystems underneath (carriers, validation, the registry), see the systems pages linked from each feature page.

| Page | What it covers |
| --- | --- |
| [CLI commands](cli-commands.md) | All 18 subcommands, global flags, the lazy dispatcher, and the shared `Ctx` command context. |
| [Adopting files](adopting-files.md) | `somnus new` and `somnus stamp`: scaffolding, embedded/sidecar adoption, and the five-root rollout frontier. |
| [Lifecycle and revisions](lifecycle-and-revisions.md) | `somnus status`, `somnus bump`, and `somnus fork`: the lifecycle state machine, revision increments, and derived artifacts. |
| [Migration from v0.1](migration.md) | `somnus migrate`: upgrading v0.1 hybrid frontmatter and `:::submatter` directives to core 2.0.0. |
| [Querying the registry](querying.md) | `somnus index`, `q --text`, SQL queries, `ls`, `stale`, `regions`, and `check --all`: all-carrier discovery, managed-file search, and reconciliation (`src/somnus/db/store.py`, `src/somnus/commands/query.py`). |
| [Agent integration](agent-integration.md) | `somnus brief`, `somnus schema`, `somnus set`, and `somnus mcp`: the agent cheat sheet, per-field documentation, non-interactive header edits, and the MCP server. |

Related: [Architecture](../overview/architecture.md), [Getting started](../overview/getting-started.md), [Glossary](../overview/glossary.md).

The current toolkit is 2.1.1 (`pyproject.toml`), with 18 commands and 16 MCP tools. Its discovery repair reports unmanaged sidecar-only hosts without reading their payloads; discovery still does not adopt or search them. Per the operator correction of 2026-11-01 recorded in `PLAN.md`, `HANDOFF.md`, and `docs/USAGE_GUIDE.md`, cross-root bulk adoption has stopped and is optional usage, not a completion gate; the latest recorded scan is 2,659 managed / 21,554 unmanaged with 0 invalid / 0 missing / 0 conflicts. The separate host-agnostic plugin 1.2.1 is installed in Codex and Factory from its clean production payload (commit 35c228a; 26 tests and hosted CI 41402125903 green): both catalogs select the checked-in reproducible 8-file native export, and both installed caches were inspected after a clean native remove/install with 0 .somnus.yaml files. The 1.2.0 record established the verified native identity `somnus-metadata-plugin@somnus-metadata-plugin` (installed and enabled in both hosts), native cached skill trees matching the canonical shared skill, and fresh host sessions querying through the native plugin MCP. The earlier 1.1.1 clean-reinstall report was a direct skill/MCP adapter record, corrected by the operator on 2026-11-02; direct adapter health is not native plugin registration. The release/install commission is recorded complete in `PLAN.md` and `HANDOFF.md`. See [Adopting files](adopting-files.md), [Agent integration](agent-integration.md), and [Testing](../how-to-contribute/testing.md) for the checkpoint and evidence boundaries.
