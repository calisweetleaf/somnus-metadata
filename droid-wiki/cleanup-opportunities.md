# Cleanup opportunities

This page separates resolved drift from remaining verification boundaries and optional maintenance candidates. Size and diagnostic counts are not evidence of a correctness defect.

## Spec and code drift

### Closed warning registry

D18 resolved the undefined `W_DUPLICATE_TITLE` listing by removing it from SPEC section 19.2 rather than inventing a trigger. The four warnings are `W_PREDICATE`, `W_REGION_SPACING`, `W_REGION_UNREGISTERED`, and `W_UNMANAGED`. Existing title behavior remains: `somnus stale` reports advisory rows at similarity 0.85 and `somnus new` refuses registered-title collisions at 0.9 with `E_IO` unless `--force` is used (`src/somnus/commands/stale.py`, `src/somnus/commands/new.py`). This is not an outstanding implementation task.

## TODO and FIXME markers

A whole-word search of Python files under `src/` and `tests/` finds no uppercase `TODO`, `FIXME`, `XXX`, or `HACK` markers. The lowercase inference rule `(r"task|todo", "task")` in `src/somnus/infer.py` maps file names to the `task` type and is not a note. This search is not a dead-code analysis. Historical archive notes are not active tasks.

## Large modules and long functions

The four largest Python modules hold 2,959 of 8,146 physical Python lines in `src/somnus/` (about 36%; 49 modules, excluding 187 lines across the two SQL files):

| File | Lines | Notes |
| --- | --- | --- |
| `src/somnus/model/validate.py` | 843 | Contains `consistency` (147 lines), `walk` (86), `selectors` (54), and `references` (54) |
| `src/somnus/yamlsub.py` | 759 | Restricted YAML parser and serializer; `block_scalar` is 48 lines |
| `src/somnus/db/store.py` | 756 | Registry reconciliation and derived full-text search maintenance |
| `src/somnus/model/schema.py` | 601 | Mostly declarative schema nodes, so its size is less of a concern |

The longest functions in the package, measured with `ast`:

| Function | Lines |
| --- | --- |
| `build_payload` in `src/somnus/commands/migrate.py` | 190 |
| `consistency` in `src/somnus/model/validate.py` | 147 |
| `build_parser` in `src/somnus/cli.py` | 106 |
| `walk` in `src/somnus/model/validate.py` | 86 |
| `_index_document` in `src/somnus/db/store.py` | 84 |
| `scan_markers` in `src/somnus/regions.py` | 60 |

`build_payload` maps each v0.1 field family (identity, names, time, classification, relations, locations, leftovers) in one function; splitting it per SPEC section 22 step would match the spec's structure. `consistency` runs many unrelated intra-document checks in sequence and could be split by concern (lifecycle, authority, regions, claims). `build_parser` is long because it declares every subcommand, and `src/somnus/mcp.py` reads those declarations to build its tool schemas, so keeping them in one place is deliberate. It is not a refactoring priority.

The 90-day history includes initial creation, so churn is not a defect ranking. At `d620172`, `src/somnus/db/store.py` has 796 changed lines across seven commits and `src/somnus/model/validate.py` has 925 across four; both remain useful review targets when their behavior changes. See [By the numbers](by-the-numbers.md) for the measurement method.

## Terminal UI and verification boundaries

- **POSIX terminal coverage exists.** `tests/test_tui.py` now has 60 tests, including real PTY raw-mode/restoration, key, failure, and save-chain checks. The separate installed-package harness covers browser/editor sessions. The earlier absence of real-terminal tests is resolved.
- **Registry-note overlay is fixed.** `capture_notes` in `src/somnus/commands/_common.py` and `NoteBuffer` in `src/somnus/tui/app.py` route notes to the status row. Long messages are clipped; complete registry diagnosis uses `somnus index`, `somnus q --conflicts`, and history.
- **Windows branch tests now exist.** `tests/test_term_windows.py` adds 12 tests with kernel32/msvcrt fakes for mode changes, cleanup, suspension, and key decoding. This does not establish real Windows console behavior.
- **Acceptance CI gap is resolved.** Since `3dcde8b`, `.github/workflows/ci.yml` runs the full 65-check `tests/acceptance/installed_package_acceptance.py` harness in its Ubuntu/Python 3.11 install job. `PLAN.md` records that hosted run as green; this refresh did not inspect or rerun the hosted workflow. See [Testing](how-to-contribute/testing.md) for current runner checks.
- **Remaining boundaries.** Native Windows consoles and external MCP applications were not exercised in this wiki refresh. The latest `PLAN.md` entry records prior 65/65 installed acceptance, green hosted CI/CodeQL, and in-host read queries from Droid, Codex, and Antigravity. Host writes remain unexercised. The CI install job does not expand installed acceptance to Windows/macOS consoles or external hosts.
- **Older mypy compatibility remains unresolved.** A previous wiki refresh recorded two errors with mypy 1.9.0 in `src/somnus/tui/term.py:201-202`. The refresh at `d620172` passed 49 files using an isolated mypy 1.18.2 installation after finding the tool absent; neither version was rerun in this refresh. The declared `mypy>=1.9` range was not changed. See [Testing](how-to-contribute/testing.md).

Commit `d620172` fixes SQLite connection leaks on failed writable/read-only setup in `src/somnus/db/store.py`, with regression coverage in `tests/test_store.py`. It also removes the prior Ruff residual findings through exception chaining, strict pairing, and unused-binding cleanup; `PLAN.md` records the selected Ruff gate passing. These are resolved repairs, not open maintenance tasks.

## Documents without Somnus headers

The repository's own working documents are not Somnus-managed: `README.md`, `PLAN.md`, `AGENTS.md`, and `filetree.md` start with a plain `#` heading and no envelope. `SPEC.md`, `DECISIONS.md`, and the files in `archive/v2-proposal/` do carry headers. Stamping the four files with `somnus stamp PATH --write` would let `somnus check --all` cover the whole repository. `AGENTS.md` is a governance file, so stamping it is a deliberate decision rather than routine cleanup.

## Diagnostic housekeeping

Generated Surgeon/Doctor state is git-ignored, not product source. Historical cache counts and encoding observations do not establish this runner's state; do not delete operator-owned history as routine cleanup. The latest `PLAN.md` baseline records 374 findings (0 critical, 71 serious, 303 minor), exit 1, with reviewed dispositions. Its one new serious finding is the intentional empty-body sentinel for non-UTF-8 sidecar hosts in `src/somnus/db/store.py`. Doctor was not rerun here. Passing native gates does not turn that static severity gate green.

## Related pages

- [Pitfalls](background/pitfalls.md)
- [Testing](how-to-contribute/testing.md)
- [Debugging](how-to-contribute/debugging.md)
