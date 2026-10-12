# Somnus metadata overview

somnus-metadata defines the Somnus metadata standard (core release `somnus://metadata/core/2.0.0`) and ships `somnus`, a Python toolkit that reads, writes, validates, and indexes that metadata. It is a solo research-to-implementation project; the normative contract is `SPEC.md` and the rationale is `DECISIONS.md`.

## What it does

Every file managed by Somnus carries exactly one `somnus:` header. The header records identity, revision, classification, lifecycle status, authority, time, relations, claims, regions, access policy, and ingestion policy for the file. The toolkit:

- puts that header into the right place for the file type (Markdown frontmatter, a comment block in code or config, or a `<file>.somnus.yaml` sidecar) without touching the bytes around it;
- validates headers at four levels (`carrier`, `core`, `semantic`, `canon`) and prints compiler-style diagnostics;
- indexes every registered root into one global SQLite registry at `~/.somnus/somnus.db`, which tracks revisions, locations, relations, claims, and conflicts and keeps an append-only event ledger;
- offers a terminal UI (`somnus edit`) for browsing the registry and editing headers.

The package has no third-party dependencies (`pyproject.toml` declares `dependencies = []`) and needs Python 3.11 or later.

## Who uses it

- People and agents who write Markdown specifications, decision records, benchmarks, and notes and want them to be machine-readable without hand-writing headers.
- Agents that need a cheap, structured way to query "what documents exist, which is authoritative, what supersedes what". The registry answers those questions in SQL or plain text; JSON is deliberately absent (see [design decisions](../background/design-decisions.md)).

## Repository at a glance

| Path | What lives there |
| --- | --- |
| `SPEC.md` | Normative standard, 23 sections |
| `DECISIONS.md` | Ratified decisions D1 to D15 |
| `src/somnus/` | The toolkit (45 Python modules, 7,514 lines, plus 175 lines of SQL) |
| `tests/` | 12 unittest suites (about 4,100 lines), 443 tests, including one test per SPEC section 21 fixture |
| `archive/` | v0.1 spec, schemas, examples, tools and the v2 proposal; historical, not normative |
| `Somnus Markdown Metadata Standard Research.md` | Original research; evidence only, read-only |

## Quick links

- [Architecture](architecture.md): how the layers fit together
- [Getting started](getting-started.md): install, first document, tests
- [Glossary](glossary.md): artifact, envelope, carrier, standing, region, and other terms
- [CLI commands](../features/cli-commands.md): every `somnus` subcommand
- [Registry](../systems/registry.md): the SQLite schema and reconciliation rules
- [Design decisions](../background/design-decisions.md): why the standard looks the way it does
