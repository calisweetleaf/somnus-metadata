# Agent integration

`somnus brief` prints a Markdown cheat sheet meant to be pasted into an agent instruction file such as `AGENTS.md`, and `somnus schema` documents any header field or exports the whole header schema as JSON Schema Draft 2020-12. Both are read-only and need no registry. `somnus set` gives agents the header edits the terminal UI gives people, and `somnus mcp` serves every non-interactive command as a Model Context Protocol tool for clients without a shell.

## Purpose

Agents working in a Somnus-managed repository need the handful of rules that keep headers valid (never invent IDs or dates, never edit `id`, change status only through the tool), a way to look up a field's type and vocabulary without reading all of `SPEC.md`, and a way to change header fields without editing the envelope by hand. `brief` covers the rules, `schema FIELD` the lookup, and `set` the edits. `mcp` puts all of them behind one stdio server. The JSON Schema export exists for editors and external tooling that understand JSON Schema; apart from the MCP protocol framing, it is the only JSON the toolkit produces, by design, because D4 forbids JSON in the registry and the toolkit's own output is text or TSV.

## How it works

### `somnus brief`

```powershell
somnus brief
somnus brief > somnus-brief.md     # then paste the section into AGENTS.md
```

`src/somnus/commands/brief.py` prints the constant `BRIEF` string, a Markdown section headed `## Somnus metadata (core somnus://metadata/core/2.0.0)`. It contains:

- where the normative contract lives (`SPEC.md`) and the three carrier families;
- **Rules for agents**: never hand-invent IDs, dates, actors, licenses, evidence, or acceptance records; never edit `id`; indexed changes are new revisions via `somnus bump`; lifecycle changes go through `somnus status`; unknown fields are errors and tool data goes under `extensions.<owner>`; region markers carry identity only and are registered with `somnus regions PATH --sync --write`; `normative` role is intent, and only `authority.standing: accepted` with an acceptance record is authoritative;
- **Commands**: a table mapping needs (new document, adopt a file, validate, change status, new revision, derive a copy, upgrade v0.1, registry, field docs) to command lines;
- the exit-code meanings `0`, `1`, `2`.

The root `AGENTS.md` of this repository carries the same rules in its "Rules for agents working on Somnus-managed files" section. When a rule changes, update `BRIEF`, `AGENTS.md`, and SPEC together.

### `somnus schema FIELD`

```powershell
somnus schema                          # the payload root
somnus schema classification
somnus schema lifecycle.status
somnus schema knowledge.claims.region_ref
```

`resolve()` in `src/somnus/commands/schema.py` walks the declarative schema tree in `src/somnus/model/schema.py`. The leading `somnus.` is optional, `[]` is ignored, and array items are stepped through automatically, so `knowledge.claims.region_ref` reaches the field inside each claim. Profile payloads are reachable under `profile_data` through their short keys, for example `somnus schema profile_data.specification`. An unknown member is a usage error (exit 2) naming the part that failed.

The output starts with plain lines:

```text
field: somnus.lifecycle.status
type: one of: draft, proposed, provisional, active, experimental, superseded, deprecated, historical, archived, rejected
required: yes
```

followed by `about:` when the field has documentation. For objects and tagged unions, a `member, required, type, about` table follows (tagged variants are listed as `<tag>=<kind>: <field>`). `--tsv` applies to that table.

### `somnus schema --json-schema`

```powershell
somnus schema --json-schema
somnus schema --json-schema --out build/somnus-core-2.0.0.schema.json
```

`export()` in `src/somnus/model/jsonschema_export.py` converts the same schema tree:

- `$schema` is `https://json-schema.org/draft/2020-12/schema` and `$id` is the core schema URI;
- every object is closed with `additionalProperties: false` and lists its `required` members;
- enums, `date-time` and `date` formats with the SPEC patterns, string patterns, `minLength`, numeric bounds, `minItems`, and `uniqueItems` are carried over;
- named objects and tagged unions become `$defs` entries referenced with `$ref`; tagged unions become `oneOf` with a `const` on the tag;
- the specification and benchmark profile payload schemas are added to `$defs` with a `$comment` naming their profile URI.

A top-level `$comment` states the limit: restricted-YAML rules, cross-field consistency, references, regions, and profile key binding are enforced only by the `somnus` validator. A document that passes the JSON Schema can still fail `somnus check`. `--out` writes the file atomically; using `--out` without `--json-schema` is a usage error.

### `somnus set`

```powershell
somnus set notes/plan.md "title=Rollout Plan" "classification.tags=release, ops" --reason "retitle"
somnus set notes/plan.md summary=          # an empty optional field is removed
```

`src/somnus/commands/set_fields.py` is the non-interactive twin of the header editor in [Terminal UI](../systems/tui.md) (decision D16). It accepts exactly the fields in `FIELDS` from `src/somnus/tui/form.py`: `title`, `summary`, `purpose`, `classification.category`, `classification.type`, `classification.role`, `classification.scope`, `classification.tags`, `access.visibility`, and `ingestion.disposition`. A leading `somnus.` is optional, and the value is everything after the first `=`.

`run()` loads the document with `load_valid()`, feeds every assignment through `FormModel.apply()` (tags are comma-separated and de-duplicated; an empty `summary` or `purpose` is removed), and compares the result with the loaded payload. If nothing changed it prints `no changes` and writes nothing. Otherwise it calls `bump_revision()`, writes through `commit()` (core validation plus host-byte preservation), and records a `set` event naming the changed fields and the `--reason`.

Refusals leave the file untouched:

| Input | Exit | Diagnostic |
| --- | --- | --- |
| A field outside `FIELDS` (`id`, `lifecycle.status`, ...) | 2 | Lists the settable fields |
| An argument without `=`, or the same field twice | 2 | Usage error |
| A value outside a vocabulary | 1 | `E_SCHEMA` with the allowed values |
| A result that fails core validation (for example an empty title) | 1 | The validator's diagnostics |

### `somnus mcp`

```powershell
somnus mcp                       # stdio server; register this command with an MCP client
somnus --actor my-agent mcp      # actor recorded for every write made through the server
```

`src/somnus/mcp.py` implements a stdlib-only MCP server over newline-delimited JSON-RPC 2.0 on stdin and stdout (decision D17). It handles `initialize`, `ping`, `tools/list`, and `tools/call`, ignores notifications, and answers malformed input with JSON-RPC errors (`-32700` parse, `-32600` invalid request, `-32601` unknown method, `-32602` bad params or unknown tool). Batches are accepted. The `initialize` result carries the `BRIEF` text as server instructions and negotiates the protocol version from `PROTOCOL_VERSIONS`.

```mermaid
sequenceDiagram
    participant Client as MCP client
    participant Server as mcp.Server
    participant CLI as python -m somnus.cli
    Client->>Server: tools/call {name, arguments}
    Server->>Server: command_line(tool, arguments)
    Server->>CLI: child process, --no-color, --actor
    CLI-->>Server: exit code, stdout, stderr
    Server-->>Client: text content, isError when exit != 0
```

`build_tools()` generates one tool per command from the argparse definitions collected by `build_parser(parsers)`, so a new command or flag shows up in MCP without touching the server. `edit` and `mcp` are excluded (`EXCLUDED`), and the global `--actor`, `--debug`, and `--no-color` stay server-side. Positionals become required properties, `store_true` flags become booleans, repeatable and multi-value arguments become string arrays, `type=int` becomes an integer, and `choices` become an `enum`. Tools in `READ_ONLY` (`brief`, `check`, `ls`, `q`, `stale`) carry `readOnlyHint: true`.

`command_line()` checks argument types and turns them into an argv: options as `--flag=value` and positionals after `--`, so a title or SQL string that starts with `-` is never read as an option. `run_cli()` runs that argv with the server's own interpreter, with `PYTHONIOENCODING=utf-8`, no stdin, a 600-second timeout, and no console window on Windows. The tool result is the command's stdout and stderr as text, with Windows line endings normalized. A non-zero exit sets `isError` and appends `[exit N]`, so agents keep the 0/1/2 distinction. No result is JSON; the protocol framing is the only JSON involved, which D4 allows where a format requires it.

Relative paths in tool arguments resolve against the server's working directory, so absolute paths are the safe choice.

## Integration points

- Header editing shared with the TUI: [Terminal UI](../systems/tui.md).
- The schema tree both commands read: [Data models](../reference/data-models.md) and [Validation](../systems/validation.md).
- Why JSON appears only in the schema export and MCP framing: D4 and D17 in [Design decisions](../background/design-decisions.md).
- Getting an agent started in a new repository: [Getting started](../overview/getting-started.md).
- Full command list: [CLI commands](cli-commands.md).

## Entry points for modification

- Cheat sheet text: the `BRIEF` constant in `src/somnus/commands/brief.py`.
- Field documentation strings: the `doc` arguments on fields in `src/somnus/model/schema.py`. Both `schema FIELD` and the JSON Schema `description` values come from them.
- Mapping of schema node types to JSON Schema keywords: `_Exporter.node()` in `src/somnus/model/jsonschema_export.py`. A new node type in `src/somnus/model/schema.py` needs a branch here, or export raises `TypeError`.
- Profile short keys for field lookup: `_PROFILE_KEYS` in `src/somnus/commands/schema.py`.
- Settable fields: `FIELDS` in `src/somnus/tui/form.py`. A change there changes `somnus set` and the TUI together.
- MCP tool generation: `_param()` and `build_tools()` in `src/somnus/mcp.py`. A new argparse action kind needs a branch in `_param()`. Tests are in `tests/test_mcp.py`, including a live stdio session against a child server.

## Key source files

| File | Role |
| --- | --- |
| `src/somnus/commands/brief.py` | `somnus brief` and the `BRIEF` text |
| `src/somnus/commands/schema.py` | `somnus schema`, field resolution, member tables |
| `src/somnus/commands/set_fields.py` | `somnus set`: validated, revisioned header edits |
| `src/somnus/mcp.py` | MCP stdio server, argparse-to-tool generation, child-process runner |
| `src/somnus/commands/mcp.py` | `somnus mcp` entry point |
| `src/somnus/model/jsonschema_export.py` | JSON Schema Draft 2020-12 export |
| `src/somnus/model/schema.py` | Declarative schema tree shared by validation, docs, and export |
| `AGENTS.md` | Repository agent rules that mirror the brief |
