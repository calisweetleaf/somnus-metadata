# Testing

The discovered suite is 14 stdlib `unittest` modules under `tests/` with 537 test methods. `tests/test_conformance.py` implements the 21 SPEC section 21 fixtures. A separate, explicitly invoked 67-check installed-package harness is not collected by discovery.

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

This refresh to `0881ad7` on 2026-11-02 UTC passed all **537 existing checkout tests** and semantic validation (**0 errors, 0 warnings**). System Python lacked mypy; a temporary isolated **mypy 2.4.1 passed all 49 source files**, and its environment/cache were removed. No product tests or source files were changed. This commit changes only `PLAN.md` and `HANDOFF.md`; installed acceptance and the symlink-root probe were not repeated. Their earlier results below remain historical evidence, not fresh runs. Hosted CI, coverage, Doctor, public installation, and external clients were not exercised.

The preceding `07a6039` refresh also passed the checkout, semantic, and isolated mypy 2.4.1 checks, plus the three existing `TestUnmanagedSidecarHosts` tests under a real symlinked temporary root. It did not repeat installed acceptance.

The preceding wiki refresh from `e82e8bc` to `6cfc132` on 2026-11-02 UTC ran the existing checkout suite: all **537 tests passed**. Semantic validation of `SPEC.md` and `DECISIONS.md` reported **0 errors and 0 warnings**. The existing installed-package harness also passed **67/67**, with 0 failed and 0 not run, on Linux/Python 3.12.3. No product tests were added or changed by this documentation refresh. Unlike the preceding metadata-only adoption commit, `6cfc132` changes `Store.scan` in `src/somnus/db/store.py`, adds three regressions in `tests/test_store.py`, and adds one installed acceptance check.

System Python initially failed `python -m mypy` because mypy was not installed. A temporary isolated installation of **mypy 2.4.1 passed all 49 source files**, exit 0, and was removed afterward. The preceding refresh recorded mypy 1.18.2 rejecting the metadata line `#     type: "source-code"` at `src/somnus/__init__.py:9` as a Python type comment. That older-version failure was not rerun or fixed here; compatibility across the declared `mypy>=1.9` range remains unresolved. No dependency declaration or product code changed. Coverage, Doctor, hosted CI, external agent hosts, and public-index installation were not rerun.

The earlier refresh at `da82a7a` on 2026-11-01 UTC recorded 534 passing tests and 66/66 installed checks. The latest operator records in `PLAN.md` and `HANDOFF.md` now separately record 537/537 and 67/67 for both fresh and exact-release wheels. Prior Droid/Codex known-topic search proof remains valid for that earlier corpus, not final adoption acceptance. Three roots still have unmanaged hosts; neither package acceptance nor this checkout suite establishes full corpus coverage.

An earlier wiki refresh recorded two errors with mypy 1.9.0 at the then-current `src/somnus/tui/term.py:201-202` (conditional console adapter inferred as `object`; now lines 233-234 after the envelope). That version was not rerun here. A prior 1.18.2 pass predates the envelopes and does not supersede the current 1.18.2 failure.

## CI checks

`.github/workflows/ci.yml` defines eight test jobs: Python 3.11 and 3.14 on Ubuntu, Windows, and macOS, plus Python 3.12 and 3.13 on Ubuntu. Each runs the full unittest suite and semantic validation of `SPEC.md` and `DECISIONS.md`. The matrix uses `fail-fast: false`, so one failure does not stop the other entries.

Separate Ubuntu jobs reject third-party runtime dependencies and imports from `archive`, then build the package and install its wheel. The installation smoke test changes to `$RUNNER_TEMP`, asserts that `somnus` was imported from `site-packages`, and invokes the installed `somnus check` against the two managed documents. Since `3dcde8b`, the same Ubuntu/Python 3.11 install job also explicitly runs `python tests/acceptance/installed_package_acceptance.py`. The harness builds its own wheel in a temporary source copy, installs it into a separate venv, and exercises CLI, registry, stdio MCP, and POSIX PTY consumers with an isolated `SOMNUS_HOME`. These checks test packaging separately from source-checkout imports. See [Automation](../deployment.md) for triggers and workflow permissions.

The policy job also runs mypy. The `secrets` job runs Gitleaks; `tooling` runs configured pre-commit hooks, six `.importlinter` contracts, and branch coverage with `.coveragerc`'s `fail_under = 85`. Import layering declares three distinct sanctioned cross-links, not a blanket exemption. CodeQL is configured separately in `.github/workflows/codeql.yml`. Historical evidence in `PLAN.md` records 88.76% coverage; coverage, hooks, import contracts, Gitleaks, and CodeQL were not rerun for this wiki refresh. The current 67-check installed-package harness runs in the install job, not across the OS/Python test matrix.

These are configured checks. Inspect an actual workflow run before claiming that its platforms or installed-wheel path passed.

## Suites

Counts are AST `test_` methods and physical lines in the current files.

| File | Tests | Lines | Covers |
| --- | --- | --- | --- |
| `tests/test_validate.py` | 80 | 725 | Validation pipeline: levels, diagnostic codes, field paths, usage policy (SPEC 19) |
| `tests/test_yamlsub.py` | 75 | 481 | Restricted YAML subset: strict parser, lenient mode, spans, canonical serializer (SPEC 16) |
| `tests/test_tui.py` | 60 | 908 | Widgets, forms, strict detail-row shape, note routing, real POSIX PTY modes/keys/restoration and save chain; off-Windows console guard |
| `tests/test_regions.py` | 41 | 327 | Region markers: pairing, inert contexts, spacing, headings, TeX labels, registry sync (SPEC 13) |
| `tests/test_carriers.py` | 40 | 436 | Envelope extraction, insertion, preambles, host preservation (SPEC 17) |
| `tests/test_document.py` | 38 | 392 | Document loading, chained I/O/encoding/carrier errors, byte-preserving atomic saves, digests, positions (SPEC 16.3, 17, 18.3) |
| `tests/test_config.py` | 28 | 230 | Configuration precedence and validation (SPEC 18.1, 20) |
| `tests/test_ids.py` | 24 | 213 | UUIDv7 minting, Somnus URNs, legacy references, slugs (SPEC 3.1) |
| `tests/test_commands.py` | 45 | 633 | CLI workflows, last-resort error boundary, stale findings, fork refusals, full-text search, adoption hints, and implicit-home scan refusal |
| `tests/test_conformance.py` | 21 | 397 | One test per SPEC section 21 fixture |
| `tests/test_lifecycle.py` | 21 | 225 | Lifecycle state machine against a transcription of the SPEC 7.1 table |
| `tests/test_store.py` | 35 | 513 | Reconciliation, connection cleanup, scan failures, FTS5, schema-1 upgrade, sidecar text, all-file unmanaged discovery, sparse-binary allocation, and real CLI adoption/sidecar removal |
| `tests/test_mcp.py` | 17 | 300 | Protocol/schema/argument handling, CLI subprocess forwarding and failures, relative-path hints, internal-error containment, live stdio |
| `tests/test_term_windows.py` | 12 | 223 | Windows modes, entry failure cleanup, suspension, and prefixed keys through kernel32/msvcrt fakes |
| **Discovered total** | **537** | **6,003** | |

Including `tests/acceptance/installed_package_acceptance.py` (1,018 lines), `tests/` contains 15 Python files and 7,021 physical lines. These counts include metadata envelopes. Installed checks are not additional unittest methods.

## Installed-package acceptance

Before a release, `CONTRIBUTING.md` requires explicit invocation:

```sh
python tests/acceptance/installed_package_acceptance.py --keep
```

`--repo PATH` selects another checkout. The harness builds a wheel from a temporary source copy, creates an isolated venv and `SOMNUS_HOME`, removes inherited source-path injection, and invokes the installed command outside the checkout. It drives real files and SQLite, lifecycle/revision/conflict recovery, carrier refusals, migration inputs, diagnostics, a real stdio MCP peer (16 closed-schema tools and protocol/tool errors), and browser/editor sessions on real POSIX PTYs.

Prerequisites are Python 3.11+, a wheel builder (`uv build`, `python -m build`, then `python -m pip wheel`), a venv creator (`uv venv` or `python -m venv`), and POSIX `pty`/`termios`. Artifacts are `<tmp>/runs/<UTC timestamp>/result.json`, `result.md`, and `result.log`. The harness deletes its own temporary tree unless `--keep` retains it and prints the path. Exit `0` means all passed, `1` a failed check, and `2` a harness/build/install error or required check that could not run (`not_run`); skips are not silently accepted.

The preceding wiki refresh reran `python tests/acceptance/installed_package_acceptance.py` on Linux/Python 3.12.3: **67/67 passed, 0 failed, 0 not run**, exit `0`. The isolated wheel reported 2.1.1 and resolved imports inside its venv, not the checkout. `phase_install` compares both console-script versions to `[project].version` in `pyproject.toml`, replacing obsolete hard-coded 2.1.0 assertions. `phase_agent_hints` now checks that unmanaged JSON and binary hosts appear in index output without creating sidecars. The harness deleted its temporary tree because `--keep` was not used. This validates the invoked harness, not a public-index install or the hosted Ubuntu/Python 3.11 job.

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

### Canonical temporary paths

Commit `07a6039` changes three expected paths in `TestUnmanagedSidecarHosts` in `tests/test_store.py` to `Path.resolve().as_posix()`. `Store.scan()` in `src/somnus/db/store.py` already resolves roots; merely calling `as_posix()` on the original temporary path leaves aliases intact. `PLAN.md` records failures in the first 2.1.1 hosted run (`41390329231`, commit `6cfc132`) on macOS/Windows, where `/var` symlinks or Windows short-name aliases differed. Runtime code, test counts, and package version are unchanged.

The `07a6039` refresh set Python's temporary root to a real directory symlink and reran all three existing methods. All passed, including real CLI stamping and sparse-file allocation checks. This is a Linux alias regression probe, not native macOS/Windows validation or proof that a corrected hosted run passed. The operator-document-only `0881ad7` refresh did not repeat this separate probe.

### Independent transcriptions

`tests/test_lifecycle.py` holds `SPEC_TABLE`, a copy of the SPEC 7.1 transition table typed in independently of `src/somnus/model/lifecycle.py`, and checks the implementation against it. This catches drift between spec and code rather than testing the code against itself.

### Conformance fixtures

`tests/test_conformance.py` has two classes. `TestConformance` covers fixtures that need no registry (1 to 12, 18, 21). `TestRegistryConformance` builds a temp registry for fixtures 13 to 17, 19, and 20. Test names carry the fixture number, for example `test_14_same_revision_distinct_states_conflict` and `test_20_disappearance_is_not_a_tombstone`. A `payload()` helper returns a minimal valid core 2.0.0 payload that tests mutate with `copy.deepcopy`.

### Archived inputs

`tests/test_commands.py` reads v0.1 examples from `archive/v0.1/examples/` as migration inputs. This is the one sanctioned use of `archive/` from tests; `src/` never imports from it.

## Evidence boundaries

`tests/test_tui.py` adds 17 tests over the earlier suite: note capture/buffering, real POSIX PTY raw-mode entry and restoration, suspension, drawing, key decoding, EOF/non-TTY failure, the registry-note save chain, and an off-Windows adapter guard. Since `b0cc64e`, `PosixTerminalTest.attrs()` masks only `PENDIN` from local-mode flags before comparing terminal attributes. The source comment identifies it as a macOS kernel-owned status bit set when canonical mode toggles, which `tcsetattr()` cannot restore. All other returned attributes remain part of the comparison; runtime code in `src/somnus/tui/term.py` is unchanged.

`tests/test_term_windows.py` now exercises Windows `msvcrt`/`ctypes` branches using fakes on Linux, including mode restoration after failed entry and a suspended-screen round trip. This is unit evidence, not native Windows console execution. `tests/test_commands.py` covers internal CLI errors with and without `--debug`, interrupts, all stale-report finding kinds, and fork refusals; its database helper closes returned connections. `tests/test_store.py` checks failed-open connection ownership and separates unavailable FTS5 from unrelated DDL failures. `tests/test_mcp.py` checks real child CLI execution, subprocess forwarding, timeout/OSError conversion, and per-request exception containment.

Hosted CI, native macOS/Windows consoles, coverage, Doctor, and external MCP applications were not exercised in this refresh. The `6cfc132` refresh passed 537 checkout tests, semantic validation, isolated mypy 2.4.1, and 67 installed-package checks including real POSIX PTYs and a stdio MCP peer. The `07a6039` refresh repeated the checkout/semantic/type checks and added a symlink-root probe. The `0881ad7` refresh repeated only the checkout/semantic/type checks. The `3e09b64` docs-only refresh repeated the 537 checkout tests and the semantic check (0 errors, 0 warnings); mypy was not rerun. The `605c5a8` docs-only refresh did not rerun the gates. The `fe19ce3` docs-only refresh repeated the 537 checkout tests and the semantic check (0 errors, 0 warnings); mypy was not rerun. Historical CI results remain separate from these runner checks.

Current operator records in `PLAN.md` separately show native plugin 1.2.1's fresh 26-test result, green hosted CI 41402125903 (source commit 35c228a), and installation in both Codex and Factory from the clean 8-file production export against backend 2.1.1, with both installed caches inspected after a clean native remove/install (0 .somnus.yaml files, no development adapter code). Plugin 1.2.0 (commit 4deee50) established the native installed/enabled records in both hosts (identity `somnus-metadata-plugin@somnus-metadata-plugin`; Factory at commit 4deee507dc7a). Both native cached skill trees and the requested custom skill copies match the canonical shared skill, and fresh Codex and Factory sessions called native-plugin MCP `q(text="lifecycle", limit=1, tsv=true)`, each returning the lifecycle.py source path. The earlier 1.1.1 clean-reinstall episode was a superseded direct-adapter report the operator corrected on 2026-11-02; direct skill/MCP adapter health is not native plugin registration. Skill/plugin alignment is recorded complete for Codex and Factory Droid; expanded-corpus searches apply only if the operator resumes adoption. OpenCode in-session calls, native Windows, and external-host writes remain unexercised. The last recorded scan is 2,659 managed and 21,554 unmanaged hosts across all carrier types, superseding the 1,064 / 23,148 checkpoint. The reductions followed preservation exclusions, not adoption; an isolated protected-host sidecar fixture does not prove a bulk rollout. Passing local checks does not validate those separate environments or exhaustive coverage. See [Agent integration](../features/agent-integration.md), [Terminal UI](../systems/tui.md), and [Cleanup opportunities](../cleanup-opportunities.md).
