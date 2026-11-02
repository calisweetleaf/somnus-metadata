# Somnus metadata overview

somnus-metadata defines the Somnus metadata standard (core release `somnus://metadata/core/2.0.0`) and ships `somnus`, a Python toolkit that reads, writes, validates, and indexes that metadata. It is a solo research-to-implementation project; the normative contract is `SPEC.md` and the rationale is `DECISIONS.md`.

## What it does

Every file managed by Somnus carries exactly one `somnus:` header. The header records identity, revision, classification, lifecycle status, authority, time, relations, claims, regions, access policy, and ingestion policy for the file. The toolkit:

- puts that header into the right place for the file type (Markdown frontmatter, a comment block in code or config, or a `<file>.somnus.yaml` sidecar) without touching the bytes around it;
- validates headers at four levels (`carrier`, `core`, `semantic`, `canon`) and prints compiler-style diagnostics;
- indexes every registered root into one global SQLite registry at `~/.somnus/somnus.db`, which tracks revisions, locations, relations, claims, and conflicts and keeps an append-only event ledger (`src/somnus/db/store.py`);
- searches managed file content with `somnus q --text`, using a derived SQLite FTS5 index (`src/somnus/db/search.sql`, `src/somnus/commands/query.py`);
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
| `DECISIONS.md` | Ratified decisions D1 to D19 |
| `HANDOFF.md` | Current operator completion job, verified-state record, and remaining full-index/search acceptance |
| `PLAN.md` | Current delivery state and maintenance priorities, not the original build specification |
| `src/somnus/` | The toolkit (49 Python modules, 8,146 lines, plus 187 lines of SQL) |
| `tests/` | 14 discovered unittest modules, 534 tests including 21 conformance fixtures; a separate 66-check installed-package acceptance harness |
| `docs/USAGE_GUIDE.md`, `docs/AGENTS.appendix.md` | Operator walkthrough and a portable global-instructions snippet for agents |
| `.github/workflows/` | Cross-platform checks, CodeQL, tagged releases, and automatic wiki refresh |
| `archive/` | v0.1 spec, schemas, examples, tools and the v2 proposal; historical, not normative |
| `Somnus Markdown Metadata Standard Research.md` | Original research; evidence only, read-only |

`README.md` and `pyproject.toml` identify the toolkit as `somnus-metadata` 2.1.0. Both `somnus` and the `somnus-metadata` command alias call `somnus.cli:main`; the Python import remains `somnus`. Core metadata stays 2.0.0, while the registry uses schema 2 (`src/somnus/__init__.py`). `docs/USAGE_GUIDE.md` records publication of 2.1.0, and the [public PyPI release metadata](https://pypi.org/pypi/somnus-metadata/2.1.0/json) confirms a wheel and sdist uploaded on 2026-11-01 UTC (October 31 in the operator's local time). Older unpublished-release statements in `PLAN.md` describe the earlier handoff. Install with pip in a virtual environment on `PATH`; do not install the unrelated PyPI distribution named `somnus` in the same environment.

A separate private adapter, [somnus-metadata-plugin](https://github.com/calisweetleaf/somnus-metadata-plugin), installs an agent skill and MCP configuration for Droid, Codex, Antigravity, and OpenCode. It is not part of this Python distribution. `docs/USAGE_GUIDE.md` records plugin 1.1.0, four successful doctor handshakes on the operator's Linux laptop, and the revised skill locations. In-host read queries were previously exercised with plugin 1.0.0 in Droid, Codex, and Antigravity; an OpenCode in-session call and host write tools remain unexercised. These are recorded results, not integrations tested on this runner. See [Agent integration](../features/agent-integration.md) for the evidence boundary.

`AGENTS.md` is the active mission-first entry. Its 2026-11-01 first-move note points to `HANDOFF.md`, which takes precedence over older next actions in `PLAN.md` until its completion criteria are met. Then recover supporting evidence from `PLAN.md`, read the relevant relationships in `CONTEXT.md`, and use `.codex/OPERATING.md` as an adaptive tool route. `AGENTS.v1.md` is the preserved, superseded entry, not another active policy. Checkout tests, installed acceptance, and compatibility with an external MCP host are separate boundaries. Workflow configuration is not evidence of a successful hosted run.

`HANDOFF.md` records a working pip-installed 2.1.0 backend, plugin 1.1.0, 534 passing tests, and 66/66 installed-package checks on the operator's machine. The unfinished job is adoption and indexing across the intended roots, followed by real search calls through both Droid and Codex MCP. Its snapshot records only five indexed artifacts and `roots = []` in global configuration; this is historical operator state, not an inspection of this runner or evidence that bulk indexing is complete. Registration, adoption, and search are separate steps. See [Adopting files](../features/adopting-files.md) and [Agent integration](../features/agent-integration.md).

## Quick links

- [Current completion handoff](../../HANDOFF.md): full-index job and required search evidence, not a completed rollout
- [Operator and agent usage guide](../../docs/USAGE_GUIDE.md): step-by-step local workflows and recorded integration boundaries
- [Global agent-instructions appendix](../../docs/AGENTS.appendix.md): a snippet to review and copy into your host's global instructions
- [Architecture](architecture.md): how the layers fit together
- [Getting started](getting-started.md): install, first document, tests
- [Glossary](glossary.md): artifact, envelope, carrier, standing, region, and other terms
- [CLI commands](../features/cli-commands.md): every `somnus` subcommand
- [Agent integration](../features/agent-integration.md): `somnus brief`, `somnus set`, and the MCP server
- [Registry](../systems/registry.md): the SQLite schema and reconciliation rules
- [Querying](../features/querying.md): structured queries and full-text search
- [Design decisions](../background/design-decisions.md): why the standard looks the way it does
- [Automation](../deployment.md): CI jobs and the rolling wiki pull request
