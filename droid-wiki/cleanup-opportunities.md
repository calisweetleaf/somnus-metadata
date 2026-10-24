# Cleanup opportunities

This page separates resolved drift from remaining verification boundaries and optional maintenance candidates. Size and diagnostic counts are not evidence of a correctness defect.

## Spec and code drift

### Closed warning registry

D18 resolved the undefined `W_DUPLICATE_TITLE` listing by removing it from SPEC section 19.2 rather than inventing a trigger. The four warnings are `W_PREDICATE`, `W_REGION_SPACING`, `W_REGION_UNREGISTERED`, and `W_UNMANAGED`. Existing title behavior remains: `somnus stale` reports advisory rows at similarity 0.85 and `somnus new` refuses registered-title collisions at 0.9 with `E_IO` unless `--force` is used (`src/somnus/commands/stale.py`, `src/somnus/commands/new.py`). This is not an outstanding implementation task.

## TODO and FIXME markers

A whole-word search of Python files under `src/` and `tests/` finds no uppercase `TODO`, `FIXME`, `XXX`, or `HACK` markers. The lowercase inference rule `(r"task|todo", "task")` in `src/somnus/infer.py` maps file names to the `task` type and is not a note. This search is not a dead-code analysis. Historical archive notes are not active tasks.

## Large modules and long functions

The four largest Python modules hold 2,886 of 8,016 physical Python lines in `src/somnus/` (about 36%; 49 modules, excluding the separate 175-line SQL schema):

| File | Lines | Notes |
| --- | --- | --- |
| `src/somnus/model/validate.py` | 844 | Contains `consistency` (148 lines), `walk` (86), `selectors` (54), and `references` (54) |
| `src/somnus/yamlsub.py` | 759 | Restricted YAML parser and serializer; `block_scalar` is 48 lines |
| `src/somnus/db/store.py` | 682 | Registry store; `_index_document` is 80 lines |
| `src/somnus/model/schema.py` | 601 | Mostly declarative schema nodes, so its size is less of a concern |

The longest functions in the package, measured with `ast`:

| Function | Lines |
| --- | --- |
| `build_payload` in `src/somnus/commands/migrate.py` | 190 |
| `consistency` in `src/somnus/model/validate.py` | 148 |
| `build_parser` in `src/somnus/cli.py` | 104 |
| `walk` in `src/somnus/model/validate.py` | 86 |
| `_index_document` in `src/somnus/db/store.py` | 80 |
| `scan_markers` in `src/somnus/regions.py` | 60 |

`build_payload` maps each v0.1 field family (identity, names, time, classification, relations, locations, leftovers) in one function; splitting it per SPEC section 22 step would match the spec's structure. `consistency` runs many unrelated intra-document checks in sequence and could be split by concern (lifecycle, authority, regions, claims). `build_parser` is long because it declares every subcommand, and `src/somnus/mcp.py` reads those declarations to build its tool schemas, so keeping them in one place is deliberate. It is not a refactoring priority.

## Terminal UI and verification boundaries

- **POSIX terminal coverage exists.** `tests/test_tui.py` now has 59 tests, including real PTY raw-mode/restoration, key, failure, and save-chain checks. The separate installed-package harness covers browser/editor sessions. The earlier absence of real-terminal tests is resolved.
- **Registry-note overlay is fixed.** `capture_notes` in `src/somnus/commands/_common.py` and `NoteBuffer` in `src/somnus/tui/app.py` route notes to the status row. Long messages are clipped; complete registry diagnosis uses `somnus index`, `somnus q --conflicts`, and history.
- **Remaining boundaries.** Native Windows `msvcrt`/`ctypes` terminal paths, hosted CI, and external MCP applications were not exercised in this wiki refresh. Prior installed acceptance is recorded in `PLAN.md` and `runbooks/package-release.md`, not a fresh universal compatibility claim.
- **Older mypy compatibility remains unresolved.** With the same project config on this runner, mypy 1.9.0 reports two errors in `src/somnus/tui/term.py:201-202`; 1.18.2 passes 49 files. The declared `mypy>=1.9` range was not changed. See [Testing](how-to-contribute/testing.md).

## Documents without Somnus headers

The repository's own working documents are not Somnus-managed: `README.md`, `PLAN.md`, `AGENTS.md`, and `filetree.md` start with a plain `#` heading and no envelope. `SPEC.md`, `DECISIONS.md`, and the files in `archive/v2-proposal/` do carry headers. Stamping the four files with `somnus stamp PATH --write` would let `somnus check --all` cover the whole repository. `AGENTS.md` is a governance file, so stamping it is a deliberate decision rather than routine cleanup.

## Diagnostic housekeeping

Generated Surgeon/Doctor state is git-ignored, not product source. Historical cache counts and encoding observations do not establish this runner's state; do not delete operator-owned history as routine cleanup. `PLAN.md` records a prior Doctor rescan of 371 findings, including 70 serious findings and exit 1, with reviewed dispositions. Passing native gates does not turn that static severity gate green.

## Related pages

- [Pitfalls](background/pitfalls.md)
- [Testing](how-to-contribute/testing.md)
- [Debugging](how-to-contribute/debugging.md)
