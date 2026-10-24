# Somnus metadata overview

somnus-metadata defines the Somnus metadata standard (core release `somnus://metadata/core/2.0.0`) and ships `somnus`, a Python toolkit that reads, writes, validates, and indexes that metadata. It is a solo research-to-implementation project; the normative contract is `SPEC.md` and the rationale is `DECISIONS.md`.

## What it does

Every file managed by Somnus carries exactly one `somnus:` header. The header records identity, revision, classification, lifecycle status, authority, time, relations, claims, regions, access policy, and ingestion policy for the file. The toolkit:

- puts that header into the right place for the file type (Markdown frontmatter, a comment block in code or config, or a `<file>.somnus.yaml` sidecar) without touching the bytes around it;
- validates headers at four levels (`carrier`, `core`, `semantic`, `canon`) and prints compiler-style diagnostics;
- indexes every registered root into one global SQLite registry at `~/.somnus/somnus.db`, which tracks revisions, locations, relations, claims, and conflicts and keeps an append-only event ledger;
- offers a terminal UI (`somnus edit`) for browsing the registry and editing headers, and `somnus set` for making the same header edits from a script or an agent;
- exposes every non-interactive command to MCP clients through `somnus mcp`, a stdio server that runs the CLI for each tool call.

The package has no third-party dependencies (`pyproject.toml` declares `dependencies = []`) and needs Python 3.11 or later.

## Who uses it

- People and agents who write Markdown specifications, decision records, benchmarks, and notes and want them to be machine-readable without hand-writing headers.
- Agents that need a cheap, structured way to query "what documents exist, which is authoritative, what supersedes what". The registry answers those questions in SQL or plain text; JSON is deliberately absent (see [design decisions](../background/design-decisions.md)).

## Repository at a glance

| Path | What lives there |
| --- | --- |
| `SPEC.md` | Normative standard, 23 sections |
| `DECISIONS.md` | Ratified decisions D1 to D18 |
| `PLAN.md` | Current delivery state and maintenance priorities, not the original build specification |
| `src/somnus/` | The toolkit (49 Python modules, 8,016 lines, plus 175 lines of SQL) |
| `tests/` | 13 discovered unittest modules, 476 tests including 21 conformance fixtures; a separate installed-package acceptance harness |
| `.github/workflows/` | Cross-platform checks, CodeQL, tagged releases, and automatic wiki refresh |
| `archive/` | v0.1 spec, schemas, examples, tools and the v2 proposal; historical, not normative |
| `Somnus Markdown Metadata Standard Research.md` | Original research; evidence only, read-only |

`README.md` and `pyproject.toml` identify the distribution as `somnus-metadata` 2.0.0; the command and import remain `somnus`. Do not install the unrelated PyPI distribution named `somnus` in the same environment. A distributable coding-agent plugin is not included.

`AGENTS.md` sets the authority order and verification boundaries. `PLAN.md` and `runbooks/package-release.md` record prior installed-package acceptance and publication evidence. Checkout tests, installed acceptance, and compatibility with an external MCP host are separate boundaries. Workflow configuration is not evidence of a successful hosted run.

## Quick links

- [Architecture](architecture.md): how the layers fit together
- [Getting started](getting-started.md): install, first document, tests
- [Glossary](glossary.md): artifact, envelope, carrier, standing, region, and other terms
- [CLI commands](../features/cli-commands.md): every `somnus` subcommand
- [Agent integration](../features/agent-integration.md): `somnus brief`, `somnus set`, and the MCP server
- [Registry](../systems/registry.md): the SQLite schema and reconciliation rules
- [Design decisions](../background/design-decisions.md): why the standard looks the way it does
- [Automation](../deployment.md): CI jobs and the rolling wiki pull request
