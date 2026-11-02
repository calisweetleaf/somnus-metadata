# Cleanup opportunities

This page separates resolved drift from remaining verification boundaries and optional maintenance candidates. Size and diagnostic counts are not evidence of a correctness defect.

## Spec and code drift

### Closed warning registry

D18 resolved the undefined `W_DUPLICATE_TITLE` listing by removing it from SPEC section 19.2 rather than inventing a trigger. The four warnings are `W_PREDICATE`, `W_REGION_SPACING`, `W_REGION_UNREGISTERED`, and `W_UNMANAGED`. Existing title behavior remains: `somnus stale` reports advisory rows at similarity 0.85 and `somnus new` refuses registered-title collisions at 0.9 with `E_IO` unless `--force` is used (`src/somnus/commands/stale.py`, `src/somnus/commands/new.py`). This is not an outstanding implementation task.

## TODO and FIXME markers

A whole-word search of Python files under `src/` and `tests/` finds no uppercase `TODO`, `FIXME`, `XXX`, or `HACK` markers. The lowercase inference rule `(r"task|todo", "task")` in `src/somnus/infer.py` maps file names to the `task` type and is not a note. This search is not a dead-code analysis. Historical archive notes are not active tasks.

## Large modules and long functions

The four largest Python modules hold 3,104 of 9,732 physical Python lines in `src/somnus/` (31.89%; 49 modules, excluding 251 SQL lines). Counts include metadata envelopes. Excluding complete envelopes gives 2,975 of 8,162 Python lines (36.45%) and 187 SQL lines. The adoption commit was metadata-only, but `6cfc132` changes discovery logic and documentation in `src/somnus/db/store.py`:

| File | Lines | Notes |
| --- | --- | --- |
| `src/somnus/model/validate.py` | 875 | Contains `consistency` (147 lines), `walk` (86), `selectors` (54), and `references` (54) |
| `src/somnus/yamlsub.py` | 791 | Restricted YAML parser and serializer; `block_scalar` is 48 lines |
| `src/somnus/db/store.py` | 805 | Registry reconciliation, all-file unmanaged discovery, and derived full-text search maintenance |
| `src/somnus/model/schema.py` | 633 | Mostly declarative schema nodes, so its size is less of a concern |

The longest functions listed below retain their spans; the separate `Store.scan` method in `src/somnus/db/store.py` grows by six lines in the discovery repair:

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
- **Acceptance CI gap is resolved.** Since `3dcde8b`, `.github/workflows/ci.yml` explicitly runs `tests/acceptance/installed_package_acceptance.py` in the Ubuntu/Python 3.11 install job. That historical run covered 65 checks; the current harness has 67, including alias and unmanaged sidecar-host discovery. The preceding refresh passed 67/67 locally, with 0 failures or required checks unrun. Installed acceptance and hosted CI were not repeated for this test/docs-only delta. See [Testing](how-to-contribute/testing.md).
- **Remaining boundaries.** `PLAN.md` records native plugin 1.2.1's fresh 26-test result, green hosted CI 41402125903 (source commit 35c228a), and installation in both Codex and Factory from the clean 8-file production export (both caches inspected with 0 .somnus.yaml files) against backend 2.1.1; the 1.2.0 record (commit 4deee50, 25 tests, CI 41399524229) established the native installed/enabled records in both hosts; both native cached skill trees and custom skill copies match the canonical shared skill, and fresh Codex and Factory sessions returned the lifecycle.py source path from native-plugin MCP lifecycle queries. The 1.1.1 clean-reinstall episode was a superseded direct-adapter report corrected by the operator on 2026-11-02. This refresh repeated the 537 existing tests and semantic validation; mypy, the symlink-root probe, and the 67-check installed run were not repeated for the docs-only delta. Native Windows, OpenCode in-session calls, and external-host writes remain unexercised; skill/plugin alignment is recorded complete for Codex and Factory Droid, and expanded-corpus searches apply only if the operator resumes adoption.
- **Mypy metadata compatibility remains unresolved.** On 2026-11-02, system Python lacked mypy. Isolated mypy 1.18.2 then failed at `src/somnus/__init__.py:9` with `Invalid syntax [syntax]`, interpreting `#     type: "source-code"` in the envelope as a Python type comment. Isolated mypy 2.4.1 passed all 49 source files and a minimal metadata fixture; the fixture was not run with 1.18.2. Temporary environments were removed. Earlier 1.18.2 passes predate adoption; historical 1.9.0 console-adapter errors were not rerun (their former lines 201-202 in `src/somnus/tui/term.py` are now 233-234). The declared `mypy>=1.9` range remains incompletely validated, with no dependency bump or product fix in this documentation request. See [Testing](how-to-contribute/testing.md).

Commit `d620172` fixes SQLite connection leaks on failed writable/read-only setup in `src/somnus/db/store.py`, with regression coverage in `tests/test_store.py`. It also removes the prior Ruff residual findings through exception chaining, strict pairing, and unused-binding cleanup; `PLAN.md` records the selected Ruff gate passing. These are resolved repairs, not open maintenance tasks.

### Canonical-path expectations corrected

`PLAN.md` records the first 2.1.1 hosted run (`41390329231`, `6cfc132`) failing three discovery tests on macOS/Windows because temporary-directory aliases differed from resolved scanner paths. Commit `07a6039` fixes only the expected paths in `tests/test_store.py` with `resolve().as_posix()`, not the runtime or release. All three methods passed the preceding refresh's Linux symlink-root probe; corrected hosted macOS/Windows execution remains unverified. See [Testing](how-to-contribute/testing.md#canonical-temporary-paths).

## Adoption coverage

`README.md`, `PLAN.md`, `AGENTS.md`, and `filetree.md` already carry metadata; the former proposal to stamp them is resolved. The latest recorded scan in `docs/USAGE_GUIDE.md` section 9 reports five roots with 2,659 managed hosts, 21,554 unmanaged, and no invalid/missing hosts or conflicts; the earlier 1,064 managed / 23,148 unmanaged checkpoint (Documents and Projects complete under exclusions) is a prior dated record. Earlier core/plugin adoption and nested-registration consolidation are complete. The lower unmanaged counts reflect preservation exclusions, not further adoption.

Bulk adoption is no longer open work: the operator stopped it on 2026-11-01, and `docs/USAGE_GUIDE.md` section 9 now frames adoption as optional usage, not a completion gate. The remaining unmanaged hosts across the five roots are preserved, and existing cross-root changes are kept untouched. Protected-source standard-sidecar handling retains its isolated byte-preservation, semantic-validation, and native-observation proof, with no bulk rollout (`PLAN.md`). The 2.1.1 fix in `src/somnus/db/store.py` replaced the incomplete 21,174 embedded-only count with all-file discovery without reading unmanaged payloads. The canonical host-agnostic skill/plugin alignment is recorded complete for native plugin 1.2.1, installed in Codex and Factory from the clean production payload, with the 1.2.0 record establishing the native installed/enabled records in both hosts and the native MCP lifecycle queries from fresh sessions; the earlier 1.1.1 clean-reinstall record is superseded direct-adapter history. Do not resume adoption without a new operator request. See [Adopting files](features/adopting-files.md) and [Configuration](reference/configuration.md).

## Diagnostic housekeeping

Generated Surgeon/Doctor state is git-ignored, not product source; do not delete operator-owned history as routine cleanup. `PLAN.md` records source Doctor unchanged at 49 files, 373 findings and 71 serious. Root Doctor increases from 1,757/276 findings/serious to 1,758/277 over 64 files; the added fixed-argv, no-shell CLI subprocess in `tests/test_store.py` has an explicit disposition. Both deltas are recorded CLEAN with that disposition, not green severity gates. Doctor was not rerun here.

## Related pages

- [Pitfalls](background/pitfalls.md)
- [Testing](how-to-contribute/testing.md)
- [Debugging](how-to-contribute/debugging.md)
