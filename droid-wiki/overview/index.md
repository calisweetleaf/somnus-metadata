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
| `src/somnus/` | The toolkit (49 Python modules, 9,732 physical lines, plus 251 lines of SQL, including metadata envelopes) |
| `tests/` | 14 discovered unittest modules, 537 tests including 21 conformance fixtures; a separate 67-check installed-package acceptance harness |
| `docs/USAGE_GUIDE.md`, `docs/AGENTS.appendix.md` | Operator walkthrough and a portable global-instructions snippet for agents |
| `.github/workflows/` | Cross-platform checks, CodeQL, tagged releases, and automatic wiki refresh |
| `archive/` | v0.1 spec, schemas, examples, tools and the v2 proposal; historical, not normative |
| `Somnus Markdown Metadata Standard Research.md` | Original research; evidence only, read-only |

`README.md` and `pyproject.toml` identify the toolkit as `somnus-metadata` 2.1.1. Both `somnus` and the `somnus-metadata` command alias call `somnus.cli:main`; the Python import remains `somnus`. Core metadata stays 2.0.0, while the registry uses schema 2 (`src/somnus/__init__.py`). The latest sections of `PLAN.md` and `runbooks/package-release.md` record publication, matching artifact digests, exact-wheel acceptance, and a no-cache pip installation of 2.1.1. These are operator records, not a public installation repeated by this wiki refresh. Older release statements in those files are historical. Install with pip in a virtual environment on `PATH`; do not install the unrelated PyPI distribution named `somnus` in the same environment.

A separate private adapter, [somnus-metadata-plugin](https://github.com/calisweetleaf/somnus-metadata-plugin), installs an agent skill and MCP configuration for Droid, Codex, Antigravity, and OpenCode. It is not part of this Python distribution. The latest `PLAN.md` and `HANDOFF.md` record plugin **1.2.1** at commit `35c228a`, 26 passing plugin tests, and passing hosted CI `41402125903`, superseding the 1.2.0 record at commit `4deee50` (25 tests) and the 1.1.1 record at commit `3000082` (21 tests). Since 1.2.1 both catalogs target `native/somnus-metadata-plugin`, a checked-in reproducible export of exactly 8 runtime files, instead of the development checkout; both installed caches were inspected after a clean native remove/install and contain 0 .somnus.yaml files and no Node development adapter code. The operator corrected an earlier misreport in which direct skill/MCP adapter health had been claimed as native installation: 1.2.0 is recorded as installed and enabled in both Codex's and Factory's native plugin lists (native identity somnus-metadata-plugin@somnus-metadata-plugin), and fresh Codex and Factory sessions successfully called the native-plugin MCP lifecycle query, returning the same source path. The shared consumer skill is host-agnostic; both native cached skill trees and the custom skill copies match its canonical source, and the custom copies are compatibility projections, not native-installation evidence on their own. An OpenCode in-session call and host write tools remain unexercised. These are recorded operator results, not integrations tested on this runner. See [Agent integration](../features/agent-integration.md) for the evidence boundary.

`AGENTS.md` is the active mission-first entry. Its rewritten first move (operator correction, 2026-11-01) defines the completion scope as release and installation, which the top sections of `PLAN.md` and `HANDOFF.md` record as complete; the earlier cross-root adoption instructions are superseded history. Recover supporting evidence from `PLAN.md`, read the relevant relationships in `CONTEXT.md`, and use `.codex/OPERATING.md` as an adaptive tool route. `AGENTS.v1.md` is the preserved, superseded entry, not another active policy. Checkout tests, installed acceptance, and compatibility with an external MCP host are separate boundaries. Workflow configuration is not evidence of a successful hosted run.

The newest sections of `HANDOFF.md` and `PLAN.md` record the release/install commission as complete and mark the earlier cross-root adoption frontier superseded (operator correction, 2026-11-01). All five intended roots are registered. The last recorded scan in `docs/USAGE_GUIDE.md` section 9 has **2,659 managed hosts, 21,554 unmanaged, and 0 invalid, missing, or conflicted hosts**; the earlier 1,064 / 23,148 checkpoint is prior history, and its reduced unmanaged count followed preservation exclusions, not additional adoption. Bulk adoption has stopped: adoption is optional usage, not a completion gate, and the remaining unmanaged files are preserved, not unfinished work. Protected-host sidecar handling has only an isolated fixture proof, not a completed bulk rollout. Native `Store.scan` in `src/somnus/db/store.py` includes hosts requiring a new sidecar without loading their payloads. These are operator-host observations, not this runner's registry state. See [Adopting files](../features/adopting-files.md) and [Agent integration](../features/agent-integration.md).

Commit `e82e8bc` added native envelopes and sidecars without changing the 64 source/test Python ASTs. The next commit, `6cfc132`, changes scan behavior and adds three discovery regressions in `tests/test_store.py`, plus an installed CLI acceptance check in `tests/acceptance/installed_package_acceptance.py`. Commit `07a6039` corrects those tests' expected paths with `resolve().as_posix()`; runtime code and package version are unchanged. Physical line counts include metadata envelopes; see [By the numbers](../by-the-numbers.md).

## Quick links

- [Current completion handoff](../../HANDOFF.md): release/install completion record and superseded adoption history
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
