# Debugging

Most problems surface as a diagnostic line with a stable code, so debugging usually starts by reading the code and the dotted field path. This page lists the codes the toolkit actually emits, how to get a traceback for internal errors, and how to inspect the registry without changing it.

## Reading a diagnostic

Every diagnostic follows SPEC section 19.2 and DECISIONS.md D14:

```
path:line:col: severity CODE field: message
```

`field` is a dotted payload path such as `somnus.classification.type` or `somnus.knowledge.claims[0].region_ref`, or `-` when no field applies. Line and column are 1-based file positions; `0:0` means the problem is not tied to a position (missing file, missing registry). Add `--tsv` for tab-separated output with no header.

Exit codes: `0` clean, `1` validation errors, refusals, or conflicts, `2` usage, I/O, or environment errors (`src/somnus/output.py`).

## Diagnostic codes

The counts are the number of literal occurrences of each code in `src/somnus/`, which gives a rough sense of how many distinct conditions raise it.

| Code | Sites | What it usually means |
| --- | --- | --- |
| `E_SCHEMA` | 36 | Unknown field (objects are closed, D5), wrong type, value outside a vocabulary, missing required field, or a `schema` other than `somnus://metadata/core/2.0.0` |
| `E_REGION` | 27 | Crossing, unclosed, or duplicate region markers, or a selector that does not resolve (`src/somnus/regions.py`) |
| `E_ENVELOPE` | 17 | No envelope, two envelopes, envelope plus sidecar, unclosed frontmatter or comment block, a forbidden `--` or `*/` inside a comment envelope, or an empty sidecar (`src/somnus/carriers/`) |
| `E_IO` | 15 | File missing or not UTF-8, output file already exists, registry missing, root not a directory, SQL query failed |
| `E_REFERENCE` | 12 | A reference that must resolve does not (semantic level and above) |
| `E_AUTHORITY` | 8 | `accepted` without `valid_time` or `acceptance_ref`, or overlapping accepted authorities |
| `E_TEMPORAL` | 8 | Bad timestamp or date, or an invalid interval |
| `E_HOST` | 6 | A write would change bytes outside the envelope, or a preamble cannot be preserved (multi-line XML declaration or DOCTYPE, misplaced `@charset`, payload containing the carrier's forbidden sequence) |
| `E_EXTRACTION` | 3 | A required resource is unavailable |
| `E_GRAPH` | 3 | A cycle in `supersedes`, `derived_from`, or `part_of`, or a self-edge |
| `E_POLICY` | 3 | Usage or capability policy violation (for example `training` not in `allowed_uses`) |
| `E_YAML` | 2 | Restricted-YAML violation: `null`, anchors, tags, duplicate keys, unquoted strings (`src/somnus/yamlsub.py` raises most of these through `YAMLError`) |
| `E_LIFECYCLE` | 1 | Forbidden transition or a missing reason (`src/somnus/model/lifecycle.py`) |
| `E_REVISION` | 1 | Same artifact and revision observed with different content |
| `W_PREDICATE` | 1 | Relation predicate not in the known predicate table |
| `W_REGION_SPACING` | 1 | Region marker without the expected blank-line spacing |
| `W_REGION_UNREGISTERED` | 1 | Marker in the body with no matching `knowledge.regions` record; `somnus regions PATH --sync --write` registers it |
| `W_UNMANAGED` | 1 | File has no Somnus header |

SPEC section 19.2 also lists `W_DUPLICATE_TITLE`, but no code in `src/somnus/` emits it; `somnus stale` reports near-duplicate titles as table rows instead.

## Common errors

**`E_IO registry ... does not exist; run 'somnus init'`.** Commands that need the registry (`index`, `q`, `ls`, `stale`, `edit`) fail with exit 2 until `$SOMNUS_HOME/somnus.db` exists. Run `somnus init --root DIR`, then `somnus index`. The message comes from `src/somnus/db/store.py` (lines 152 and 657); the TUI raises a similar one from `src/somnus/tui/app.py`.

**`E_HOST refusing to write: content outside the envelope would change`.** Raised by `src/somnus/document.py` after a write is re-extracted and the host bytes differ. The file is not modified. Typical causes are a host with an unusual preamble or a payload containing the carrier's forbidden sequence; a sidecar (`<file>.somnus.yaml`) is the fallback.

**`E_ENVELOPE both an embedded envelope and sidecar ... exist`.** A file has its own header and a sidecar. Remove one; exactly one authoritative envelope is allowed (SPEC section 4).

**`E_IO file is not valid UTF-8 (byte N); use a sidecar`.** Embedded carriers require UTF-8 text. Binary or other-encoded files need a sidecar.

**Revision conflict after editing.** Editing a managed file without `somnus bump` and re-indexing opens a `revision` conflict. Run `somnus bump PATH`.

## Internal errors and `--debug`

`src/somnus/cli.py` catches `SomnusError` and prints its diagnostics. Any other exception is caught at the top level and printed as one line:

```
somnus: internal error: KeyError: 'x' (rerun with --debug for a traceback)
```

with exit code 2. Rerun the same command with `--debug` to get the full Python traceback. Ctrl+C prints `interrupted` and exits 1.

## Inspecting the registry

`somnus q` opens the database read-only (`mode=ro`, `query_only`), so it is safe to use while debugging. Shortcuts are defined in `src/somnus/commands/query.py`:

| Flag | Query |
| --- | --- |
| `--docs` (default) | Present artifacts with path, from the `docs` view |
| `--conflicts` | The `open_conflicts` view |
| `--history` | The `history` view (events, newest first) |
| `--tables` | Every table and view name in the database |

Any other read-only SQL can be passed directly, for example `somnus q "SELECT rel_path, present FROM locations WHERE present = 0"`. `--limit N` caps rows and `--tsv` switches to tab-separated output. Table definitions are on [data models](../reference/data-models.md).

## Stderr notes during writes

When a mutating command records an event and re-observes the file, registry errors are written to stderr as `registry: CODE message` (`Ctx.record` in `src/somnus/commands/_common.py`). These do not change the exit code of the command that triggered them, so scan stderr after writes.

## Python diagnostics

For static problems in the toolkit itself, run somnus-debug doctor with the configs described on [tooling](tooling.md). Scan `src` with `.somnus-debug/python_doctor.src.yaml`; scanning from the repository root reports false `missing_imports` for every `somnus.*` import.
