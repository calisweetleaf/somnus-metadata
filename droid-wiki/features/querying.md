# Querying the registry

Active contributors: calisweetleaf, Christian

`somnus index` reconciles files on disk into the global SQLite registry at `$SOMNUS_HOME/somnus.db`, and `somnus q`, `ls`, and `stale` read it back as aligned text or TSV. `somnus q --text` searches indexed metadata and host content with ranked excerpts. `somnus regions` audits one file's region markers, and `somnus check --all` validates every configured root.

## Purpose

The registry answers questions a single file cannot: which artifacts exist across all roots, where they live now, which revisions were observed, which conflicts are open, and what the tool has done (the append-only `events` ledger). Decision D4 keeps it free of JSON: headers are stored as canonical restricted YAML text and every column is a plain value, so output is text or TSV only.

Toolkit 2.1.1 uses registry schema 2 with a derived FTS5 index; the normative metadata core remains 2.0.0. The patch repairs unmanaged-file discovery, not carriers, the database schema, or FTS behavior. The runtime stays stdlib-only, with FTS5 availability determined by the Python installation's SQLite build. See [Registry](../systems/registry.md) for schema migration and connection ownership.

## How it works

```mermaid
sequenceDiagram
    participant User
    participant index as somnus index
    participant Store
    participant DB as somnus.db
    participant Reader as somnus q / ls / stale
    User->>index: somnus index [ROOT...] [--full]
    index->>Store: ctx.store() (registry must exist)
    Store->>DB: scan(roots): visit files, mark missing, reconcile conflicts
    Store->>DB: log("index", summary)
    index-->>User: diagnostics + one-line summary
    User->>Reader: somnus q --docs
    Reader->>DB: connect_readonly (mode=ro, query_only)
    DB-->>Reader: rows
    Reader-->>User: aligned table or TSV
```

### `somnus index`

```powershell
somnus init --root C:\work\docs
somnus index                 # every registered root
somnus index docs --full     # one root, re-read every file
```

`src/somnus/commands/index.py` opens the registry for writing (it never creates it; run `somnus init` first). With `ROOT` arguments it scans those directories and registers them as roots through `Store.add_root()`. With no arguments it scans every registered root, falling back to the configured `index.roots` only when none are registered. In that fallback branch, any root equal to `Path.home().resolve()` or its filesystem anchor is refused with exit 2; the message suggests `somnus init --root DIR` or `somnus index DIR`. Explicit and already registered broad roots are not subject to this fallback-only guard. `Store.scan()` in `src/somnus/db/store.py`:

- walks each root with the configured `exclude` globs, pruning VCS directories and preferring a sidecar when a host has one;
- counts hosts with neither an embedded carrier nor a sidecar as scanned/unmanaged and records their paths without reading their payloads;
- skips a location whose `(file_mtime, file_size)` is unchanged unless `--full` is given or the available FTS5 index lacks its row;
- records revisions, locations, tags, regions, relations, entities, and claims, and opens or resolves `revision`, `duplicate-id`, `identity`, and `authority` conflicts (SPEC §18.3);
- refreshes the FTS5 search row for each indexed observation when FTS5 is available, including conflicting revisions;
- marks files that disappeared as `present = 0` and removes only their derived search rows, retaining registry history;
- appends an `index` event with the summary.

It prints diagnostics followed by a summary line such as `scanned 42, indexed 3, unchanged 39, new revisions 1, unmanaged 5, examples 0, invalid 0, missing 0, conflicts opened 0, resolved 1`. The exit code is 1 when any error diagnostic appeared or any conflict was opened.

When a visited document has no envelope and no loading issues, `ScanReport.unmanaged_paths` records its absolute host path with forward slashes. After the summary, `index` prints at most 10 such paths, adds `and N more` if necessary, and explains that these files are not searchable. It suggests `somnus stamp PATH` for a preview, then `somnus stamp PATH --write` to adopt. These stderr notes are informational, not warning/error diagnostics; unmanaged files alone do not cause exit 1.

Since 2.1.1, the count includes unknown-carrier hosts without sidecars: JSON, text, extensionless files, and binaries now enter both `unmanaged` and `unmanaged_paths` before `_visit()`, without a payload read. Exclusions apply before discovery; a host with a sidecar is skipped and its sidecar observed once. The native report retains the full list, unlike the CLI's ten examples. Discovery does not create metadata or search rows. Zero unmanaged only describes the roots and exclusions actually scanned; inspect invalid/missing/conflict results as well.

The current top sections of `PLAN.md` and `HANDOFF.md` record the release/install commission as complete and mark the bulk-adoption frontier superseded (operator correction, 2026-11-01); they supersede the five-artifact starting snapshot and the earlier 160-path checkpoint. Five roots (Repositories, LAB, Somnus-MCP, Documents, Projects) are configured and registered. The latest recorded scan, cited in `docs/USAGE_GUIDE.md` section 9, reports **2,659 managed / 21,554 unmanaged hosts** across five roots, with **0 invalid / 0 missing / 0 conflicts**. The earlier 1,064 / 23,148 checkpoint with its per-root breakdown is prior history. Adoption is now optional usage, not an open gate: the operator stopped bulk adoption and remaining unmanaged hosts are preserved, not unfinished work. The previous 21,174 embedded-only count is obsolete; the earlier reductions from 27,202 reflected preservation exclusions, not new adoption or a changed scan mechanism. Reconcile existing roots rather than adding nested registrations again. See [Adopting files](adopting-files.md) for counts and preservation safeguards and [Configuration](../reference/configuration.md) for roots versus excludes.

`PLAN.md` retains real Droid and Codex MCP searches from the preceding corpus for `host byte preservation`, `lifecycle`, and `carrier`: **3 hits each** in both hosts, specification listing **1**, stale **7 near-title advisories**, and conflicts **0**. Complete TSV paths were proven in both hosts. After the 1.2.0 native plugin installation (pushed as 4deee50, 25 tests, hosted CI 41399524229), duplicate direct user MCP entries were removed through Surgeon and fresh Codex and Factory sessions successfully called native-plugin MCP `q(text="lifecycle", limit=1, tsv=true)`: Factory session `52dcef09-320e-4d43-851c-e60b1025cf83` returned the lifecycle.py source path, and Codex returned the identical path through `mcp__somnus_metadata__q`. Both native cached skill trees and the requested custom skill copies match the canonical shared skill; the custom copies are compatibility projections, not evidence of native installation on their own. Plugin 1.2.1 (commit 35c228a, 26 tests, hosted CI 41402125903) succeeded 1.2.0 as a clean production payload: both catalogs select the checked-in reproducible 8-file native export rather than the development checkout, and both installed caches were inspected after a clean native remove/install with 0 .somnus.yaml files; the correction is packaging-only and does not change the MCP surface. Dated direct-adapter history: after the plugin 1.1.1 skill update, Droid read its installed skill and called `q(text="host agnostic", limit=3, tsv=true)`, returning three full paths; Codex independently made the same successful MCP query, and a clean reinstall then recorded the fresh installed skill read at both requested paths (`/home/daeron/.codex/skills/custom/somnus-metadata/SKILL.md` and `/home/daeron/.factory/skills/somnus-metadata/SKILL.md`). These are recorded operator results, not new calls by this wiki runner. See [Agent integration](agent-integration.md).

### `somnus q`

```powershell
somnus q                                  # same as --docs
somnus q --conflicts
somnus q --history --limit 20
somnus q --tables
somnus q --text "host bytes" --limit 10
somnus q --text naming conventions         # both words must match
somnus q --text "validat*" --tsv
somnus q "SELECT type, count(*) AS n FROM docs GROUP BY type" --tsv
```

`src/somnus/commands/query.py` runs a shortcut, a full-text search, or a raw SQL statement:

| Shortcut | Query |
| --- | --- |
| `--docs` (default) | `id, title, type, status, standing, revision, path` from the `docs` view, ordered by path |
| `--conflicts` | `id, kind, artifact_id, revision, path, detail, opened_at` from `open_conflicts` |
| `--history` | `id, at, actor, action, artifact_id, revision, path, detail` from `history` (newest first) |
| `--tables` | Names and types of tables and views, excluding `sqlite_*` and FTS5 `search_*` shadow tables; `search` itself remains visible |
| `--text WORDS` | Ranked `id, title, type, status, path, excerpt` rows from present indexed locations |

The shortcuts and `--text` are mutually exclusive in `src/somnus/cli.py`. A non-search shortcut takes precedence over a SQL argument. With `--text`, however, `src/somnus/commands/query.py` joins the text value and optional positional `[SQL]` value with a space and passes both to `fts_query()` as search words; the positional value is not executed as SQL. This supports the two-word unquoted example above, not arbitrary unquoted word counts: argparse still accepts only one optional positional slot, so quote longer strings. `--limit N` applies `fetchmany(N)` to whatever query runs.

Raw SQL is read-only by construction. `connect_readonly()` opens the database with a `mode=ro` URI and sets `PRAGMA query_only = ON`, so `INSERT`, `UPDATE`, `DELETE`, or DDL fails. `run_query()` turns any `sqlite3.Error` into an `E_IO` diagnostic `query failed: ...` with exit 2. A missing registry is also exit 2 with the message `run 'somnus init'`.

### Full-text search

`fts_query()` in `src/somnus/db/store.py` splits `--text` on whitespace and quotes each term as an FTS5 literal, escaping embedded quotes. Every term must match somewhere in the indexed row; `word*` preserves a trailing prefix operator. Quoting the shell argument does not turn it into a phrase, and `OR`, column filters, and other raw FTS5 operators are not interpreted as operators on this surface. Tokenization uses Porter stemming over `unicode61` with diacritic removal, as defined in `src/somnus/db/search.sql`.

`SEARCH` in `src/somnus/commands/query.py` ranks matches by BM25, with weights path 2, title 10, summary 5, tags 5, and body 1; ties sort by path. Excerpts use FTS5 `snippet()` with automatic column selection, a 12-token budget, `[` and `]` around matches, and `...` for omissions. They may come from metadata rather than the body.

Search scope is the last successfully indexed observation of each managed location, not every file under the current directory and not every historical revision. `searchable_body()` in `src/somnus/db/store.py` excludes embedded envelopes or decodes the sidecar host as UTF-8 with optional BOM. Non-UTF-8 sidecar hosts have no indexed body; metadata remains searchable. The body is capped at 1,000,000 characters, not the combined column size. Unmanaged, invalid, and example-URN documents are not newly indexed.

Results join artifact-level title/type/status to location-level search text. A conflicting observation is searchable without replacing the stored revision, so its excerpt can differ from the artifact title displayed. Mirrors may yield multiple paths for one ID. See [Registry](../systems/registry.md) for reconciliation and retention details.

After a schema-1 upgrade, run `somnus index` to create and backfill the index; missing search rows defeat the ordinary unchanged-file skip. Use `somnus index --full` to re-read eligible files even when mtime and size match. The database remains usable without SQLite FTS5, but full-text search requires it.

| Input or condition | Outcome in `src/somnus/commands/query.py` |
| --- | --- |
| Empty/whitespace-only or wildcard-only `--text` | Exit 2: at least one search word is required |
| Positional `[SQL]` argument plus `--text` | Both values become literal search words, not SQL |
| Missing `search` table | Exit 2: run `somnus index` with SQLite FTS5 |
| `--text` plus another shortcut | Parser usage error, exit 2 |
| No text-search matches | Exit 0; normal empty table plus an informational adoption/reindex hint |

For zero matches, aligned text prints `no rows` to stderr; TSV retains its column header on stdout. Both formats also receive the stderr note `no matches; only files with a Somnus header are indexed`, followed by guidance to use `somnus stamp PATH --write`, then `somnus index`. This does not mean unmanaged files were searched, and the note is not an error.

For raw phrases, Boolean operators, or column filters, use SQL `MATCH` directly:

```powershell
somnus q "SELECT path FROM search WHERE search MATCH 'title:metadata OR body:envelope'" --tsv
```

Raw SQL does not automatically add the shortcut's joins, ranking, or excerpts. The virtual table is defined in `src/somnus/db/search.sql`; join `search.rowid` to `locations.id` and filter `locations.present = 1` when composing location-aware queries.

### `somnus ls`

```powershell
somnus ls --type specification --status active
somnus ls --tag directives --path-contains docs/
```

`src/somnus/commands/ls.py` calls `Store.list_docs()`, which filters the `docs` view by exact `type`, `status`, and `standing`, by tag (an `EXISTS` subquery on `tags`), and by substring of the path (`instr`). Columns match `q --docs`.

### `somnus stale`

```powershell
somnus stale --days 14
```

`src/somnus/commands/stale.py` prints one row per finding with columns `finding, artifact, title, detail`. It is a report: the exit code is always 0.

| Finding | Condition |
| --- | --- |
| `stale-draft`, `stale-proposed` | Status `draft` or `proposed` and the newest present location's mtime is older than `--days` (default 30) |
| `unresolved-replacement` | A `superseded` artifact has a `replacement_refs` artifact URN that has no present location |
| `unreadable-header` | The stored `header_yaml` of a superseded artifact cannot be parsed |
| `missing-file` | The artifact has no present location |
| `near-duplicate-title` | Two present artifacts whose case-folded titles have a difflib ratio of at least 0.85 |
| `conflict-<kind>` | Each open conflict, with the first line of its detail |

### `somnus regions`

```powershell
somnus regions docs/guide.md
somnus regions docs/guide.md --sync           # diff
somnus regions docs/guide.md --sync --write   # apply
```

`src/somnus/commands/regions.py` compares body markers with the file's own `knowledge.regions` list (the in-header region registry of SPEC §13.1); it does not need the SQLite registry. It loads a core-valid document, scans markers with `regions.scan_markers()`, and prints a table of `marker, begin, end, depth, parent, kind, registered`, plus a `missing markers` row for each registered marker region with no markers in the body. Marker problems are printed as diagnostics.

With `--sync`, `regions.sync_registry()` appends a `{kind: section, selector: {kind: marker}}` record for every unregistered marker, bumps the revision, and either prints the diff or (with `--write`) commits and records a `regions.sync` event that also resolves open `revision` conflicts. Sync is refused while marker errors remain. Registered regions whose markers are missing are reported and left in place.

### `somnus check --all`

```powershell
somnus check --all --level semantic
somnus check SPEC.md DECISIONS.md --level semantic
```

`src/somnus/commands/check.py` validates named files or walks directories. With `--all`, or with no paths at all, it also walks every configured root (`index.roots` from configuration, defaulting to the current directory). Unmanaged Markdown files found by walking produce `W_UNMANAGED`; other unmanaged files are skipped silently. At `semantic` and `canon` levels, references resolve against the registry (when it exists) plus every document in the current check set. Exit 1 when any error is reported.

### Output formats

All tables go through `Ctx.table()` in `src/somnus/commands/_common.py`: aligned text by default, or TSV with a header row under `--tsv`. Diagnostics follow `path:line:col: severity CODE field: message`, or seven tab-separated columns with no header under `--tsv`. Registry results never use JSON. `somnus schema --json-schema` is the explicit export exception; MCP uses JSON-RPC framing around text/TSV tool content (see [Agent integration](agent-integration.md)).

`table()` in `src/somnus/output.py` clips aligned human-table cells to **60 characters** by default. Use `--tsv` (MCP `tsv: true`) to retain complete paths and other cell values; TSV still cleans embedded tabs and line breaks. A truncated display is not a truncated registry path.

## Integration points

- Tables, views, and conflict semantics: [Registry](../systems/registry.md) and [Data models](../reference/data-models.md).
- Region markers and selectors: [Document model](../systems/document-model.md).
- Validation levels used by `check`: [Validation](../systems/validation.md).
- Roots and excludes: [Configuration](../reference/configuration.md).
- Rationale for zero JSON: [Design decisions](../background/design-decisions.md).
- `somnus edit` with no path is a browser over the same `docs` data: [Terminal UI](../systems/tui.md).

## Entry points for modification

- Add a `q` shortcut: extend `SHORTCUTS` in `src/somnus/commands/query.py` and add the flag to the mutually exclusive group in `src/somnus/cli.py`.
- New `ls` filters: `Store.list_docs()` in `src/somnus/db/store.py` plus the flag in `src/somnus/cli.py`.
- New stale findings or thresholds: `_findings()` in `src/somnus/commands/stale.py`.
- Scan behavior: `Store.scan()` and `ScanReport` in `src/somnus/db/store.py`.
- Search extraction and literal conversion: `searchable_body()` and `fts_query()` in `src/somnus/db/store.py`; ranking and excerpts: `SEARCH` in `src/somnus/commands/query.py`. Search cases are in `tests/test_store.py` and `tests/test_commands.py`; `TestSearch.test_unquoted_words_and_hints` covers two unquoted words, unmanaged-file notes, and a zero-match success, while `TestBasics.test_index_refuses_home_as_implicit_root` covers fallback refusal.

## Evidence and limits

`tests/acceptance/installed_package_acceptance.py` includes `phase_agent_hints`: installed CLI checks for a two-word unquoted FTS search, zero-result adoption guidance, unmanaged-file/stamp hints, discovery of JSON/binary hosts without creating sidecars, and implicit home/broad-root refusal. Its installed version assertions now read `pyproject.toml` instead of hard-coding 2.1.0. `TestUnmanagedSidecarHosts` in `tests/test_store.py` covers exclusions, host-byte preservation, bounded allocation for a 64 MB sparse binary, real CLI adoption, and missing-location reconciliation after sidecar deletion. The MCP phase separately checks that a failed relative path names the server directory. A zero-result search is distinct from an empty search argument: the former succeeds with guidance, while the latter remains a usage error.

The current top of `PLAN.md` records **537 passing source tests**, semantic validation with 0 errors/0 warnings, mypy clean across 49 source files, configured Ruff selection exit 0, and **67/67 installed-package acceptance checks**, also passed by the exact uploaded 2.1.1 release wheel outside the checkout. These cover CLI, files, SQLite, MCP, and POSIX PTYs; they are not 67 MCP-only checks. Older 65/65 and 66/66 runs, 88.76% branch-plus-statement coverage, and import-linter results remain historical. None of these operator checks or external-host calls was rerun by this page update. Earlier Droid/Codex search proof remains separate from Antigravity reads and fresh four-host 16-tool doctor handshakes; host write tools, OpenCode in-session invocation, and native Windows execution remain unexercised. See [Testing](../how-to-contribute/testing.md) and [Agent integration](agent-integration.md).

## Key source files

| File | Role |
| --- | --- |
| `src/somnus/commands/index.py` | `somnus index` |
| `src/somnus/commands/query.py` | `somnus q` and its shortcuts |
| `src/somnus/commands/ls.py` | `somnus ls` |
| `src/somnus/commands/stale.py` | `somnus stale` |
| `src/somnus/commands/regions.py` | `somnus regions` |
| `src/somnus/commands/check.py` | `somnus check` |
| `src/somnus/db/store.py` | `Store.scan()`, `list_docs()`, `similar_titles()`, `connect_readonly()`, `run_query()` |
| `src/somnus/db/schema.sql` | Registry DDL |
| `src/somnus/db/search.sql` | FTS5 columns and tokenizer |
| `src/somnus/cli.py` | Mutually exclusive query modes and search help |
| `src/somnus/output.py` | 60-character human-table clipping and complete cleaned TSV values |
| `PLAN.md`, `HANDOFF.md`, `docs/USAGE_GUIDE.md` | Release/install completion record, superseded adoption history, and operator host-search evidence |
| `tests/test_commands.py` | Root-fallback refusal, search behavior, and informational hints |
| `tests/test_store.py` | Search-index maintenance, migration/fallback, and registry failure paths |
| `tests/acceptance/installed_package_acceptance.py` | Explicit installed CLI search/adoption/root-safety checks and MCP relative-path hint |
