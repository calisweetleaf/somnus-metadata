# Testing

The discovered suite is 13 stdlib `unittest` modules under `tests/` with 486 test methods. `tests/test_conformance.py` implements the 21 SPEC section 21 fixtures. A separate, explicitly invoked installed-package harness is not collected by discovery.

## Running

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
python -m mypy
```

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
python -m mypy
```

Check the exit status and the final `OK` or `FAILED` summary. `tests/` is not a package, so run one suite with `python -m unittest discover -s tests -p test_yamlsub.py` after setting the same `PYTHONPATH`.

These are the three required gates in `CONTRIBUTING.md`. Install mypy through `python -m pip install -e ".[dev]"` or separately. A prior 2026-10-31 wiki refresh at commit `22117e9` on Python 3.12.3 passed discovery's 486 tests and semantic validation with 0 errors and 0 warnings. The initial `python -m mypy` could not run because mypy was absent; an isolated temporary installation of mypy 1.18.2 then passed all 49 source files with the repository configuration and no persistent dependency changes.

At `b0cc64e`, this incremental refresh ran `PYTHONPATH=src python -m unittest discover -s tests -p test_tui.py` on Linux with Python 3.12.3: all 59 existing TUI tests passed. Semantic validation again reported 0 errors and 0 warnings. Full discovery, mypy, installed-package acceptance, and native macOS/Windows execution were not rerun; no source or test code was changed here.

The previous wiki refresh recorded two errors with mypy 1.9.0 at `src/somnus/tui/term.py:201-202` (conditional console adapter inferred as `object`). That older version was not rerun here, and the declared `mypy>=1.9` range was not changed or fully validated.

## CI checks

`.github/workflows/ci.yml` defines eight test jobs: Python 3.11 and 3.14 on Ubuntu, Windows, and macOS, plus Python 3.12 and 3.13 on Ubuntu. Each runs the full unittest suite and semantic validation of `SPEC.md` and `DECISIONS.md`. The matrix uses `fail-fast: false`, so one failure does not stop the other entries.

Separate Ubuntu jobs reject third-party runtime dependencies and imports from `archive`, then build the package and install its wheel. The installation smoke test changes to `$RUNNER_TEMP`, asserts that `somnus` was imported from `site-packages`, and invokes the installed `somnus check` against the two managed documents. This tests packaging separately from source-checkout imports. See [Automation](../deployment.md) for triggers and workflow permissions.

The policy job also runs mypy. The `secrets` job runs Gitleaks; `tooling` runs configured pre-commit hooks, six `.importlinter` contracts, and branch coverage with `.coveragerc`'s `fail_under = 85`. Import layering declares three distinct sanctioned cross-links, not a blanket exemption. CodeQL is configured separately in `.github/workflows/codeql.yml`. `PLAN.md` records prior coverage of 86.61%; coverage and these tooling gates were not rerun for this wiki refresh.

These are configured checks. Inspect an actual workflow run before claiming that its platforms or installed-wheel path passed.

## Suites

Counts are AST `test_` methods and physical lines in the current files.

| File | Tests | Lines | Covers |
| --- | --- | --- | --- |
| `tests/test_validate.py` | 80 | 693 | Validation pipeline: levels, diagnostic codes, field paths, usage policy (SPEC 19) |
| `tests/test_yamlsub.py` | 75 | 449 | Restricted YAML subset: strict parser, lenient mode, spans, canonical serializer (SPEC 16) |
| `tests/test_tui.py` | 59 | 866 | Widgets, forms, note routing, real POSIX PTY modes/keys/restoration and save chain; off-Windows console guard |
| `tests/test_regions.py` | 41 | 295 | Region markers: pairing, inert contexts, spacing, headings, TeX labels, registry sync (SPEC 13) |
| `tests/test_carriers.py` | 40 | 404 | Envelope extraction, insertion, preambles, host preservation (SPEC 17) |
| `tests/test_document.py` | 35 | 335 | Document loading, byte-preserving atomic saves, digests, positions (SPEC 16.3, 17, 18.3) |
| `tests/test_config.py` | 28 | 198 | Configuration precedence and validation (SPEC 18.1, 20) |
| `tests/test_ids.py` | 24 | 181 | UUIDv7 minting, Somnus URNs, legacy references, slugs (SPEC 3.1) |
| `tests/test_commands.py` | 30 | 437 | End-to-end CLI workflows, `somnus set`, full-text search, adoption hints, and refusal of an implicit home-directory scan |
| `tests/test_conformance.py` | 21 | 365 | One test per SPEC section 21 fixture |
| `tests/test_lifecycle.py` | 21 | 193 | Lifecycle state machine against a transcription of the SPEC 7.1 table |
| `tests/test_store.py` | 21 | 254 | Registry reconciliation, FTS5 refresh/removal/backfill, schema-1 upgrade, sidecar text limits and safe query quoting (SPEC 18.3–18.4) |
| `tests/test_mcp.py` | 11 | 203 | MCP protocol handling, generated schemas, argv round trips, failed-call relative-path hints, and a live stdio session |
| **Discovered total** | **486** | **4,873** | |

Including `tests/acceptance/installed_package_acceptance.py` (925 lines), `tests/` contains 14 Python files and 5,798 physical lines. Its installed checks are not additional unittest methods.

## Installed-package acceptance

Before a release, `CONTRIBUTING.md` requires explicit invocation:

```sh
python tests/acceptance/installed_package_acceptance.py --keep
```

`--repo PATH` selects another checkout. The harness builds a wheel from a temporary source copy, creates an isolated venv and `SOMNUS_HOME`, removes inherited source-path injection, and invokes the installed command outside the checkout. It drives real files and SQLite, lifecycle/revision/conflict recovery, carrier refusals, migration inputs, diagnostics, a real stdio MCP peer (16 closed-schema tools and protocol/tool errors), and browser/editor sessions on real POSIX PTYs.

Prerequisites are Python 3.11+, a wheel builder (`uv build`, `python -m build`, then `python -m pip wheel`), a venv creator (`uv venv` or `python -m venv`), and POSIX `pty`/`termios`. Artifacts are `<tmp>/runs/<UTC timestamp>/result.json`, `result.md`, and `result.log`. The harness deletes its own temporary tree unless `--keep` retains it and prints the path. Exit `0` means all passed, `1` a failed check, and `2` a harness/build/install error or required check that could not run (`not_run`); skips are not silently accepted.

`PLAN.md` records a prior 60/60 installed acceptance run for package 2.1.0; `runbooks/package-release.md` records the earlier published 2.0.0 wheel verification. That harness was not rerun during this wiki refresh, and its stdio peer does not certify an external MCP application. The existing tests were run without adding or changing product tests here.

Commit `22117e9` adds `test_index_refuses_home_as_implicit_root` and `test_unquoted_words_and_hints` in `tests/test_commands.py`. They check the no-registered-root fallback guard, an explicit project-root scan, unmanaged-file adoption hints, two unquoted search words, and a successful zero-match search with a hint. The existing `test_call_maps_exit_codes` in `tests/test_mcp.py` now checks the server-directory note for a failed relative-path call and its absence for an absolute path. See [Querying](../features/querying.md) and [Agent integration](../features/agent-integration.md).

## Patterns worth knowing

### Temporary `SOMNUS_HOME`

No test touches the real `~/.somnus/somnus.db`. `CliCase.setUp` in `tests/test_commands.py` creates a temp directory, saves the current `SOMNUS_HOME`, points `SOMNUS_HOME` at `<tmp>/home`, and changes the working directory into the temp tree. `tearDown` restores the working directory and the environment variable (removing it if it was unset) and deletes the tree. The helper `cli(*argv)` calls `somnus.cli.main` with redirected stdout and stderr and returns `(exit_code, stdout, stderr)`; `ok(*argv)` asserts exit 0. `tests/test_config.py` uses the same save-and-restore pattern for `SOMNUS_HOME`, and `tests/test_store.py` opens a `Store` against a database path inside a temp directory.

### Byte preservation

Host-byte preservation (SPEC section 17, D8) is tested at the byte level:

- `tests/test_document.py` compares `path.read_bytes()` before and after saves, checks that CRLF files stay CRLF (`test_crlf_preserved`), that a JSON host next to a sidecar keeps its exact `b'{"a": 1}\r\n'`, that a leading BOM is accepted and never emitted, and that a final line without a newline survives.
- Tests that simulate a hand edit in `tests/test_commands.py` and `tests/test_store.py` write with `write_text(..., encoding="utf-8", newline="")`. `newline=""` stops Python from translating `\n` to `\r\n` on Windows, so the bytes on disk are exactly what the test intends and digests stay comparable.
- `CliCase.write` uses `write_bytes(text.encode("utf-8"))` for the same reason.

### Independent transcriptions

`tests/test_lifecycle.py` holds `SPEC_TABLE`, a copy of the SPEC 7.1 transition table typed in independently of `src/somnus/model/lifecycle.py`, and checks the implementation against it. This catches drift between spec and code rather than testing the code against itself.

### Conformance fixtures

`tests/test_conformance.py` has two classes. `TestConformance` covers fixtures that need no registry (1 to 12, 18, 21). `TestRegistryConformance` builds a temp registry for fixtures 13 to 17, 19, and 20. Test names carry the fixture number, for example `test_14_same_revision_distinct_states_conflict` and `test_20_disappearance_is_not_a_tombstone`. A `payload()` helper returns a minimal valid core 2.0.0 payload that tests mutate with `copy.deepcopy`.

### Archived inputs

`tests/test_commands.py` reads v0.1 examples from `archive/v0.1/examples/` as migration inputs. This is the one sanctioned use of `archive/` from tests; `src/` never imports from it.

## Evidence boundaries

`tests/test_tui.py` adds 17 tests over the earlier suite: note capture/buffering, real POSIX PTY raw-mode entry and restoration, suspension, drawing, key decoding, EOF/non-TTY failure, the registry-note save chain, and an off-Windows adapter guard. Since `b0cc64e`, `PosixTerminalTest.attrs()` masks only `PENDIN` from local-mode flags before comparing terminal attributes. The source comment identifies it as a macOS kernel-owned status bit set when canonical mode toggles, which `tcsetattr()` cannot restore. All other returned attributes remain part of the comparison; runtime code in `src/somnus/tui/term.py` is unchanged.

Native Windows `msvcrt`/`ctypes` paths remain unexercised. Hosted CI, native macOS, and live external MCP applications were not exercised in this refresh. A passing Linux checkout suite does not validate a separate global installation or establish macOS behavior. See [Terminal UI](../systems/tui.md) and [Cleanup opportunities](../cleanup-opportunities.md).
