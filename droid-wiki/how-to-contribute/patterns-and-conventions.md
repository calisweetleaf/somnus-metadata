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

Codes starting with `E_` are errors and `W_` are warnings. The list is in [Debugging](debugging.md).

## Host-byte preservation

Every write calls `Document.render` in `src/somnus/document.py`, which splices the new envelope in, re-extracts the result, and raises `E_HOST` unless every byte outside the envelope is identical. Line endings are tracked per line, so CRLF files stay CRLF. A leading BOM is accepted and dropped on save (SPEC section 16.3). Files are written through `atomic_write`, which writes a temp file in the same directory and swaps it in with `os.replace`.

## Never invent facts

Tools fill headers from configuration and inference, but never fabricate dates, actors, licenses, evidence, measurements, or acceptance records (D6). `somnus stamp` writes `time: {}` because it does not know when a file was authored. A configured default standing of `accepted` is refused.

## Dry run first

Commands that rewrite files (`stamp`, `migrate`, `regions --sync`) print a unified diff and change nothing unless `--write` is passed.

## Output formats

Tables are aligned plain text, or TSV with `--tsv`. There is no JSON output mode; the registry and CLI avoid JSON by operator decision (D4). The one exception is `somnus schema --json-schema`, because JSON Schema is itself a JSON format.

## Closed schemas

Every standardized object rejects unknown keys (`E_SCHEMA`), and `null` is refused at parse time. Tool-specific data goes under `extensions.<owner>.data`. When adding a field, add it to `src/somnus/model/schema.py` (which also controls serialization order) and to the validator, and cite the SPEC section.

## Code style

- `from __future__ import annotations` at the top of every module; full type hints on public functions.
- One-line docstrings on public functions and classes. Comments only where the reason is not obvious.
- Each CLI command is one module in `src/somnus/commands/` exposing `run(args, ctx: Ctx) -> int`; shared helpers live in `src/somnus/commands/_common.py`.
- Source files stay ASCII where possible; non-ASCII characters in code are written as `\u` escapes (see [Pitfalls](../background/pitfalls.md) for why).

## Paths

Registry paths are stored as POSIX strings (`Path.as_posix()`) so the same root reads the same on every platform.

## Related pages

- [Architecture](../overview/architecture.md)
- [Validation](../systems/validation.md)
- [Testing](testing.md)
