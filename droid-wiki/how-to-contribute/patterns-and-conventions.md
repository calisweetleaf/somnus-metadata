# Patterns and conventions

The code follows a small set of rules that keep writes safe and output predictable. Most of them come straight from `SPEC.md` and `DECISIONS.md`.

## Stdlib only

Nothing outside the Python standard library is imported. SQLite comes from `sqlite3`, TOML from `tomllib`, the terminal UI from `ctypes` (Windows) or `termios` (POSIX). The YAML parser is written in-house (`src/somnus/yamlsub.py`) because a general YAML library would accept constructs the standard forbids. Adding a dependency would contradict the `dependencies = []` declaration in `pyproject.toml`.

## Errors: diagnostics, not exceptions

Validation never raises on bad input. Checks append `Diagnostic` records (`src/somnus/output.py`) with a file position, a stable code, and a dotted field path:

```
SPEC.md:12:3: error E_SCHEMA somnus.classification.type: unknown value 'spec'
```

When an operation must stop, code raises `SomnusError` carrying the diagnostics and an exit code. `src/somnus/cli.py` catches it, prints the diagnostics, and returns the code. Anything else that escapes is an internal error; `--debug` shows its traceback.

| Exit code | Constant | Meaning |
| --- | --- | --- |
| 0 | `EXIT_OK` | Success |
| 1 | `EXIT_INVALID` | Validation errors, refusals, or open conflicts |
| 2 | `EXIT_USAGE` | Usage, I/O, or environment errors |

Codes starting with `E_` are errors and `W_` are warnings. `SPEC.md` section 19.2 defines a closed registry of four warning codes. D18 in `DECISIONS.md` removes the undefined `W_DUPLICATE_TITLE`: near-duplicate titles remain advisory rows from `somnus stale`, not validator warnings. The list is in [Debugging](debugging.md).

Informational notes use `note()` in `src/somnus/commands/_common.py`, normally on stderr. Its re-entrant `capture_notes()` context manager temporarily redirects that channel. The terminal UI installs `NoteBuffer` from `src/somnus/tui/app.py` for its alternate-screen session and drains notes into the status row before rendering. CLI diagnostics keep their normal channel. See [Terminal UI](../systems/tui.md).

## Host-byte preservation

Every write calls `Document.render` in `src/somnus/document.py`, which splices the new envelope in, re-extracts the result, and raises `E_HOST` unless every byte outside the envelope is identical. Line endings are tracked per line, so CRLF files stay CRLF. A leading BOM is accepted and dropped on save (SPEC section 16.3). Files are written through `atomic_write`, which writes a temp file in the same directory and swaps it in with `os.replace`.

## Never invent facts

Tools fill headers from configuration and inference, but never fabricate dates, actors, licenses, evidence, measurements, or acceptance records (D6). `somnus stamp` writes `time: {}` because it does not know when a file was authored. A configured default standing of `accepted` is refused.

## Dry run first

Commands that rewrite files (`stamp`, `migrate`, `regions --sync`) print a unified diff and change nothing unless `--write` is passed.

## Output formats

Tables are aligned plain text, or TSV with `--tsv`. Registry data has no JSON output mode (D4). The external-format exceptions are `somnus schema --json-schema` and JSON-RPC framing in `src/somnus/mcp.py` (D17). MCP wraps the command's output in one text content item; it does not turn registry rows into JSON. See [Agent integration](../features/agent-integration.md).

## Closed schemas

Every standardized object rejects unknown keys (`E_SCHEMA`), and `null` is refused at parse time. Tool-specific data goes under `extensions.<owner>.data`. When adding a field, add it to `src/somnus/model/schema.py` (which also controls serialization order) and to the validator, and cite the SPEC section.

## Code style

- `from __future__ import annotations` at the top of every module; full type hints on public functions.
- One-line docstrings on public functions and classes. Comments only where the reason is not obvious.
- Each CLI command is one module in `src/somnus/commands/` exposing `run(args, ctx: Ctx) -> int`; shared helpers live in `src/somnus/commands/_common.py`.
- Source files stay ASCII where possible; non-ASCII characters in code are written as `\u` escapes (see [Pitfalls](../background/pitfalls.md) for why).

## Paths

Registry paths are stored as POSIX strings (`Path.as_posix()`) so the same root reads the same on every platform.

The MCP adapter runs each command in a child process from the server's working directory (`src/somnus/mcp.py`). Use absolute file paths in MCP calls when the client needs stable path resolution. The adapter keeps no application state between calls; writes persist through the files and registry.

## Policy checks

`.github/workflows/ci.yml` rejects non-empty runtime dependencies in `pyproject.toml` and statically checks imports under `src/` for references to `archive`. These checks supplement the rules in `AGENTS.md`; they do not authorize contract changes. A material change to a ratified decision needs an explicit new decision and the versioning steps in `SPEC.md` section 23.

## Related pages

- [Architecture](../overview/architecture.md)
- [Validation](../systems/validation.md)
- [Testing](testing.md)
