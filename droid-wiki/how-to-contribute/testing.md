# Testing

The discovered suite is 14 stdlib `unittest` modules under `tests/` with 534 test methods. `tests/test_conformance.py` implements the 21 SPEC section 21 fixtures. A separate, explicitly invoked 66-check installed-package harness is not collected by discovery.

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

These are the three required gates in `CONTRIBUTING.md`. Install mypy through `python -m pip install -e ".[dev]"` inside an activated virtual environment, or as an isolated tool. PEP 668 Linux hosts refuse system pip installs with `externally-managed-environment`; use `python3 -m venv .venv` (or `uv venv .venv`) and activate it first.

This incremental refresh at `803f1e2` on 2026-11-02 UTC ran the existing checkout suite: all 534 tests passed. Semantic validation of `SPEC.md` and `DECISIONS.md` reported 0 errors and 0 warnings. No product tests were added or changed. Runtime source and tests are unchanged from wiki base `61412d8`; the delta adds `HANDOFF.md` and its routing note in `AGENTS.md`.

System Python initially failed `python -m mypy` because mypy was not installed. A temporary isolated mypy 1.18.2 environment then passed all 49 source files using the repository configuration. The temporary environment was removed; no dependency declaration changed. The installed-package harness, coverage, Doctor, hosted CI, and external agent hosts were not rerun for this documentation-only delta.

The earlier refresh at `da82a7a` on 2026-11-01 UTC recorded 534 passing tests, clean semantic validation, and all 66 installed-package checks passing on Linux/Python 3.12.3. `HANDOFF.md` separately records 534/534 and 66/66 on the operator's machine. Its new completion criteria require full-root adoption/indexing and fresh search calls through Droid and Codex MCP; neither prior acceptance nor this checkout suite establishes that rollout.

The previous wiki refresh recorded two errors with mypy 1.9.0 at `src/somnus/tui/term.py:201-202` (conditional console adapter inferred as `object`). That older version was not rerun here, and the declared `mypy>=1.9` range was not changed or fully validated.

## CI checks

`.github/workflows/ci.yml` defines eight test jobs: Python 3.11 and 3.14 on Ubuntu, Windows, and macOS, plus Python 3.12 and 3.13 on Ubuntu. Each runs the full unittest suite and semantic validation of `SPEC.md` and `DECISIONS.md`. The matrix uses `fail-fast: false`, so one failure does not stop the other entries.

Separate Ubuntu jobs reject third-party runtime dependencies and imports from `archive`, then build the package and install its wheel. The installation smoke test changes to `$RUNNER_TEMP`, asserts that `somnus` was imported from `site-packages`, and invokes the installed `somnus check` against the two managed documents. Since `3dcde8b`, the same Ubuntu/Python 3.11 install job also explicitly runs `python tests/acceptance/installed_package_acceptance.py`. The harness builds its own wheel in a temporary source copy, installs it into a separate venv, and exercises CLI, registry, stdio MCP, and POSIX PTY consumers with an isolated `SOMNUS_HOME`. These checks test packaging separately from source-checkout imports. See [Automation](../deployment.md) for triggers and workflow permissions.

The policy job also runs mypy. The `secrets` job runs Gitleaks; `tooling` runs configured pre-commit hooks, six `.importlinter` contracts, and branch coverage with `.coveragerc`'s `fail_under = 85`. Import layering declares three distinct sanctioned cross-links, not a blanket exemption. CodeQL is configured separately in `.github/workflows/codeql.yml`. The latest entry in `PLAN.md` records 88.76% coverage; coverage, hooks, import contracts, Gitleaks, and CodeQL were not rerun for this wiki refresh. The current 66-check installed-package harness runs in the install job, not across the OS/Python test matrix.

These are configured checks. Inspect an actual workflow run before claiming that its platforms or installed-wheel path passed.

## Suites

Counts are AST `test_` methods and physical lines in the current files.

| File | Tests | Lines | Covers |
| --- | --- | --- | --- |
| `tests/test_validate.py` | 80 | 693 | Validation pipeline: levels, diagnostic codes, field paths, usage policy (SPEC 19) |
| `tests/test_yamlsub.py` | 75 | 449 | Restricted YAML subset: strict parser, lenient mode, spans, canonical serializer (SPEC 16) |
| `tests/test_tui.py` | 60 | 876 | Widgets, forms, strict detail-row shape, note routing, real POSIX PTY modes/keys/restoration and save chain; off-Windows console guard |
| `tests/test_regions.py` | 41 | 295 | Region markers: pairing, inert contexts, spacing, headings, TeX labels, registry sync (SPEC 13) |
| `tests/test_carriers.py` | 40 | 404 | Envelope extraction, insertion, preambles, host preservation (SPEC 17) |
| `tests/test_document.py` | 38 | 360 | Document loading, chained I/O/encoding/carrier errors, byte-preserving atomic saves, digests, positions (SPEC 16.3, 17, 18.3) |
| `tests/test_config.py` | 28 | 198 | Configuration precedence and validation (SPEC 18.1, 20) |
| `tests/test_ids.py` | 24 | 181 | UUIDv7 minting, Somnus URNs, legacy references, slugs (SPEC 3.1) |
| `tests/test_commands.py` | 45 | 601 | CLI workflows, last-resort error boundary, stale findings, fork refusals, full-text search, adoption hints, and implicit-home scan refusal |
| `tests/test_conformance.py` | 21 | 365 | One test per SPEC section 21 fixture |
| `tests/test_lifecycle.py` | 21 | 193 | Lifecycle state machine against a transcription of the SPEC 7.1 table |
| `tests/test_store.py` | 32 | 413 | Reconciliation, connection cleanup, scan failures, FTS5 fallback/refresh/removal/backfill, schema-1 upgrade, sidecar text and query quoting |
| `tests/test_mcp.py` | 17 | 268 | Protocol/schema/argument handling, CLI subprocess forwarding and failures, relative-path hints, internal-error containment, live stdio |
| `tests/test_term_windows.py` | 12 | 191 | Windows modes, entry failure cleanup, suspension, and prefixed keys through kernel32/msvcrt fakes |
| **Discovered total** | **534** | **5,487** | |

Including `tests/acceptance/installed_package_acceptance.py` (968 lines), `tests/` contains 15 Python files and 6,455 physical lines. Its installed checks are not additional unittest methods.

## Installed-package acceptance

Before a release, `CONTRIBUTING.md` requires explicit invocation:

```sh
python tests/acceptance/installed_package_acceptance.py --keep
```

`--repo PATH` selects another checkout. The harness builds a wheel from a temporary source copy, creates an isolated venv and `SOMNUS_HOME`, removes inherited source-path injection, and invokes the installed command outside the checkout. It drives real files and SQLite, lifecycle/revision/conflict recovery, carrier refusals, migration inputs, diagnostics, a real stdio MCP peer (16 closed-schema tools and protocol/tool errors), and browser/editor sessions on real POSIX PTYs.

Prerequisites are Python 3.11+, a wheel builder (`uv build`, `python -m build`, then `python -m pip wheel`), a venv creator (`uv venv` or `python -m venv`), and POSIX `pty`/`termios`. Artifacts are `<tmp>/runs/<UTC timestamp>/result.json`, `result.md`, and `result.log`. The harness deletes its own temporary tree unless `--keep` retains it and prints the path. Exit `0` means all passed, `1` a failed check, and `2` a harness/build/install error or required check that could not run (`not_run`); skips are not silently accepted.

The earlier `da82a7a` refresh reran `python tests/acceptance/installed_package_acceptance.py` on Linux/Python 3.12.3: **66/66 passed, 0 failed, 0 not run**, exit `0`. The isolated wheel reported 2.1.0 and resolved imports inside its venv, not the checkout. Its `phase_install` check confirmed that the installed `somnus-metadata --version` alias also prints `somnus 2.1.0`. The harness deleted its temporary tree because `--keep` was not used. That local run validates the invoked harness, not the hosted Ubuntu/Python 3.11 job. It was not repeated for this handoff-only update.

`PLAN.md` separately records prior installed acceptance and the green hosted install job at `3dcde8b`; `runbooks/package-release.md` records the earlier published 2.0.0 wheel verification. The harness's stdio peer does not certify an external MCP application.

The expanded harness adds `phase_agent_hints` for multi-word search, zero-match adoption hints, unmanaged-file hints, and implicit broad-root refusal with an isolated home. `phase_mcp` also verifies failed relative-path calls name the server directory (`tests/acceptance/installed_package_acceptance.py`).

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

`tests/test_term_windows.py` now exercises Windows `msvcrt`/`ctypes` branches using fakes on Linux, including mode restoration after failed entry and a suspended-screen round trip. This is unit evidence, not native Windows console execution. `tests/test_commands.py` covers internal CLI errors with and without `--debug`, interrupts, all stale-report finding kinds, and fork refusals; its database helper closes returned connections. `tests/test_store.py` checks failed-open connection ownership and separates unavailable FTS5 from unrelated DDL failures. `tests/test_mcp.py` checks real child CLI execution, subprocess forwarding, timeout/OSError conversion, and per-request exception containment.

Hosted CI, native macOS/Windows consoles, coverage, Doctor, and external MCP applications were not exercised in this refresh. The prior Linux installed-package run exercised real POSIX PTYs and a stdio MCP peer; the current run repeated the 534 checkout tests and isolated mypy check, not installed acceptance. `PLAN.md` records hosted CI/CodeQL success, including installed acceptance at `3dcde8b`, and read calls in Droid, Codex, and Antigravity on the operator's host; writes there remain unexercised. `HANDOFF.md` is now the current completion job, with full-index and Droid/Codex search proof still required. Passing local checks do not validate those separate environments. See [Terminal UI](../systems/tui.md) and [Cleanup opportunities](../cleanup-opportunities.md).
