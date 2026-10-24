# Cleanup opportunities

This page lists concrete, verified places where the codebase could be tidied or where code and documentation have drifted. None of them is a known correctness bug in tested behavior; they are candidates for future work, ordered roughly by how much they matter.

## Spec and code drift

### `W_DUPLICATE_TITLE` was specified but never emitted — resolved (D18)

SPEC section 19.2 listed `W_DUPLICATE_TITLE` among the warning codes, and no module in `src/somnus/` emitted it. Near-duplicate titles are reported only by `somnus stale` as rows of kind `near-duplicate-title` (`src/somnus/commands/stale.py` line 51), and `somnus new` refuses title collisions with `E_IO` (`src/somnus/commands/new.py` line 34).

Resolved 2026-10-23 by D18: the operator chose to drop the undefined code rather than invent a trigger, because the specification stated no condition, threshold, emitting command, or level for it. SPEC section 19.2 no longer lists it and now states that the warning registry is closed and that near-duplicate titles are a registry advisory. The two existing similarity thresholds (`new` at 0.9, `stale` at 0.85) are deliberately left un-unified. This was a non-breaking documentation correction inside core 2.0.0, so the core schema URI is unchanged.

## TODO and FIXME markers

A search of `src/` and `tests/` for `TODO`, `FIXME`, `XXX`, and `HACK` finds no markers. The only hit is the inference rule `(r"task|todo", "task")` in `src/somnus/infer.py` line 15, which maps file names to the `task` type and is not a note. The `TODO(needs-owner)` notes in `archive/v0.1/SOMNUS-METADATA-SPEC-v0.1.md` are historical and not actionable.

## Large modules and long functions

The four largest modules hold 2,865 of the 7,898 lines in `src/somnus/` (about 36%):

| File | Lines | Notes |
| --- | --- | --- |
| `src/somnus/model/validate.py` | 832 | Contains `consistency` (148 lines), `walk` (86), `selectors` (54), and `references` (53) |
| `src/somnus/yamlsub.py` | 757 | Restricted YAML parser and serializer; longest function `block_scalar` (48) |
| `src/somnus/db/store.py` | 675 | Registry store; `_index_document` is 81 lines |
| `src/somnus/model/schema.py` | 601 | Mostly declarative schema nodes, so its size is less of a concern |

The longest functions in the package, measured with `ast`:

| Function | Lines |
| --- | --- |
| `build_payload` in `src/somnus/commands/migrate.py` | 188 |
| `consistency` in `src/somnus/model/validate.py` | 148 |
| `build_parser` in `src/somnus/cli.py` | 104 |
| `walk` in `src/somnus/model/validate.py` | 86 |
| `_index_document` in `src/somnus/db/store.py` | 81 |
| `scan_markers` in `src/somnus/regions.py` | 60 |

`build_payload` maps each v0.1 field family (identity, names, time, classification, relations, locations, leftovers) in one function; splitting it per SPEC section 22 step would match the spec's structure. `consistency` runs many unrelated intra-document checks in sequence and could be split by concern (lifecycle, authority, regions, claims). `build_parser` is long because it declares every subcommand, and `src/somnus/mcp.py` reads those declarations to build its tool schemas, so keeping them in one place is deliberate. It is not a refactoring priority.

## Terminal UI gaps

- **Real-terminal coverage — addressed.** `tests/test_tui.py` covers widgets, key decoding, frame diffing, and the form model with fake screens and contexts. The raw-mode paths in `src/somnus/tui/term.py` are now also exercised on a real POSIX PTY: `PosixTerminalTest` asserts raw-mode entry, exact `termios` restoration, `suspended()` restore/re-enter, differential repaint, decoded key sequences, `EOFError` on closed input, and the `TerminalError` failure path on a non-tty stdin. The Windows `msvcrt`/`ctypes` paths remain untested (no Windows host); only the platform guard is asserted.
- **Registry notes over the TUI — fixed.** `Ctx.record` in `src/somnus/commands/_common.py` writes `registry: CODE message` lines to stderr after a save. `_common.note` now writes to a process-wide sink when `capture_notes` is active, and `somnus edit` installs a `NoteBuffer` sink for the whole alternate-screen session so both screens render the note in their status line. Ordinary CLI commands install no sink and still use stderr. `tests/test_tui.py::TuiSaveChainPtyTest` drives a real save under a PTY and asserts the note reaches the frame and never stderr.

## Documents without Somnus headers

The repository's own working documents are not Somnus-managed: `README.md`, `PLAN.md`, `AGENTS.md`, and `filetree.md` start with a plain `#` heading and no envelope. `SPEC.md`, `DECISIONS.md`, and the files in `archive/v2-proposal/` do carry headers. Stamping the four files with `somnus stamp PATH --write` would let `somnus check --all` cover the whole repository. `AGENTS.md` is a governance file, so stamping it is a deliberate decision rather than routine cleanup.

## Local housekeeping

These are git-ignored and affect only the local working copy:

- `.surgeon/journal/txn/` holds 8 transaction directories (plus `.locks` and `.path-locks`) left by earlier multi-file Surgeon transactions, the kind that fail with WinError 5 in this folder. Some of their mirrors contain pre-`dc3c981` mojibake. Surgeon's `op=recover` lists them so they can be aborted.
- `.somnus-debug/runs/` and older reports under `.python_doctor/reports/` and `.python_doctor-src/reports/` also contain cp1252 mojibake from before the encoding fix. They are historical run output and can be pruned.

## Related pages

- [Pitfalls](background/pitfalls.md)
- [Testing](how-to-contribute/testing.md)
- [Debugging](how-to-contribute/debugging.md)
