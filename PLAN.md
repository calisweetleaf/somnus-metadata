# Somnus Metadata — Completion and Operator Integration Plan

Updated 2026-10-31 (America/Chicago). Operational handoff, not normative source.
SPEC.md owns the contract; DECISIONS.md records ratified rationale. Source and
execution establish implementation and exercised behavior respectively.

## Colony foray — failing components (2026-10-31)

### Failure ledger (`scout-1`, `~/.colony/larder/somnus-metadata-failure-ledger-20261031.md`)

- **Doctor scan (`somnus-debug 0.1.0`, `m000378`, `m000379`):** `somnus-debug doctor scan src -c .somnus-debug/python_doctor.src.yaml -o .somnus-debug/runs/colony-baseline-20261031.md` (run ID `20261031T232112Z`) scanned **49 files** and reported **374 issues** (**0 critical / 71 serious / 303 minor**, exit `1` under `severity_exit_level = serious`). Row-level comparison against baseline `20261024T030635Z` (70 serious) found **1 true delta**: `silent_failures` at `src/somnus/db/store.py:43` (`searchable_body` catching `UnicodeDecodeError` and returning `""`), verified as a **false positive** (documented sentinel for non-UTF-8 sidecar hosts under D19, covered by `tests/test_store.py::TestSearchIndex.test_sidecar_host_text`). All prior 70 serious findings were re-verified in source (`stubs` 2, `broad_exceptions` 4, `security_risks` 2, `dependency_cycles` 1, `silent_failures` 48, `suspicious_short_classes` 13): **0 real defects**.
- **Ruff residual debt (`m000380`, `m000381`):** `uvx ruff check src tests --select E,F,W,B,C4,T10,ICN,PLE --ignore E501` exited `0` (`All checks passed!`; `0` `F841`, `0` `B904`, `0` `B905`, `0` `E741`; `src/somnus/model/validate.py:327` `claims = _dicts(...)` is now consumed). Prior mark `m000160` was retired as `ROT`.
- **Unit coverage baseline (`m000382`, `m000390`–`m000394`):** `PYTHONPATH=src uvx coverage run -m unittest discover -s tests` over 486 tests measured **86.80%** total branch + statement coverage (`fail_under = 85`), identifying uncovered error/fallback branches in `src/somnus/db/store.py:135-136` (FTS5-unavailable fallback `self.search = False`), `src/somnus/commands/stale.py` (52.5%), `src/somnus/commands/fork.py` (64.0%), `src/somnus/tui/app.py` (68.1%), `src/somnus/infer.py` (69.2%), and `src/somnus/commands/_common.py` (72.8%).
- **Installed-package acceptance gaps (`m000396`):** 4 recent 2.1.0 behaviors were absent from `tests/acceptance/installed_package_acceptance.py`: `q --text` full-text search, `index` unmanaged hints (`UNMANAGED_SHOWN = 10` + `stamp` hint), `index` refusal of home-directory/broad fallback (`too broad to scan`, exit `2`), and MCP relative-path server-directory note.
- **Plugin repository gaps (`m000398`, `m000399`):** In `/home/daeron/Repositories/somnus-metadata-plugin`, `host.drift()` was dead code (`driftReport` implemented in `lib/hosts.mjs` but never called by `lib/cli.mjs` `doctor`), Windows `.cmd`/`.bat` tool wrappers spawned without `shell: true` risked `EINVAL` on Node >= 18.20, and error paths (`parseJsonObject` invalid JSON, `doctor` failed handshake, corrupted Codex managed block) lacked unit tests.

### Fixes landed and verification evidence

| Component / Path | Worker & Marks | Change & Exercised Evidence |
| --- | --- | --- |
| `src/somnus/db/store.py`, `tests/test_store.py` | `forager-1` (`m000417`) | **Real defect fixed:** `Store.open` leaked the SQLite connection when `_migrate` refused a newer-schema registry (`SomnusError` bypassed the `sqlite3.Error` handler) or when the file was not a database; `connect_readonly` leaked if `PRAGMA query_only` failed (found via `ResourceWarning: unclosed database` traced with `tracemalloc`). Both now close on failure in `finally` with ownership handoff to `Store`. Added `TestOpenFailures` (`test_refused_open_releases_its_connection`, `test_readonly_connect_failure_releases_its_connection`, `test_sqlite_without_fts5_degrades_to_no_text_search`, `test_other_search_ddl_failures_are_not_swallowed`) and `TestScanFailures`. |
| `src/somnus/document.py`, `src/somnus/commands/{migrate,regions,stamp,_common}.py`, `src/somnus/model/validate.py`, `src/somnus/tui/app.py`, `tests/test_document.py`, `tests/test_tui.py` | `forager-1` (`m000416`, `m000423`) | Cleared Ruff `B904`/`B905`/`E741`/`F841` debt across `src/somnus/`: chained `from exc` on 3 `B904` sites in `document.py` (carrier refusal, invalid UTF-8, unreadable file), applied `zip(strict=True)` on `lines`/`endings` in `document.py`, `commands/migrate.py`, `commands/regions.py`, `commands/stamp.py`, and `tui/app.py` (`detail_lines` 7-column row shape, `LEAP` `m000423`), renamed `E741` bindings in `document.py` and `commands/_common.py`, and removed unused `regions` (`F841`) in `model/validate.py`. Verified by `test_document` and `test_tui` additions; `uvx ruff check src tests --select E,F,W,B,C4,T10,ICN,PLE --ignore E501` exits `0`. |
| `src/somnus/tui/term.py`, `tests/test_term_windows.py` (new) | `forager-1` (`m000418`, `m000421`, `m000424`) | Added `tests/test_term_windows.py` (12 unit tests using `sys.platform = "win32"` and `FakeKernel32`/`FakeMsvcrt`) covering mode save/enable/restore, piped stdin, non-console stdout, missing VT support restore, `Terminal` enter-failure `LEAVE_SCREEN` + stdin restore, `suspended()` round-trip, and `getwch` prefixed keys. `term.py` coverage reached **96%** (`python3 -m unittest tests.test_term_windows` 12 OK; `SALT` `m000421` confirmed no defect in `term.py`). |
| `src/somnus/commands/stale.py`, `src/somnus/commands/fork.py`, `src/somnus/cli.py`, `tests/test_commands.py` | `forager-1` (`m000419`, `m000422`) | Added behavioral tests for `cli.main` last-resort boundary (`internal error` exit `2`, `--debug` traceback, `KeyboardInterrupt` exit `1`, `SomnusError` diagnostics), every `somnus stale` finding kind (`TestStaleReport` 7 OK; `SALT` `m000422` confirmed unreadable-header handler emits a row rather than losing errors), and `fork` sidecar/carrier/collision refusals; fixed `CliCase.db()` leaking SQLite connections. |
| `src/somnus/mcp.py`, `tests/test_mcp.py` | `forager-1` (`m000420`) | Added `TestRunCli`, `TestRunnerFailures`, and `test_argument_validation` exercising `run_cli` child-process execution (real child `brief`, `actor`/`PYTHONPATH`/`timeout`/`stdin` forwarding, lenient decode, CRLF normalization, `TimeoutExpired`/`OSError` -> exit `2`) and `Server.handle` internal-error containment (`RuntimeError` -> `ERR_INTERNAL` with exception type only; session survives). Full unit suite: **534 tests OK, 0 `ResourceWarning`**, `somnus check SPEC.md DECISIONS.md --level semantic` **0/0**, `mypy` **49 files clean**, total coverage **88.76%** (`fail_under = 85`). |
| `tests/acceptance/installed_package_acceptance.py` | `digger-1` (`m000408`, `m000412`) | Added `phase_agent_hints` and `phase_mcp` check 9 covering `q --text` unquoted multi-word search, empty-search adoption hint, `index` unmanaged file hint + `stamp` adoption hint, `index` home/broad-root refusal (exit `2` with fresh home and `HOME` pinned), and MCP relative-path server-directory note. Executed `python3 tests/acceptance/installed_package_acceptance.py`: **65/65 passed, 0 failed, 0 not run** (exit `0`). |
| `/home/daeron/Repositories/somnus-metadata-plugin` (`lib/util.mjs`, `lib/hosts.mjs`, `lib/cli.mjs`, `lib/backend.mjs`, `test/plugin.test.mjs`) | `digger-1` (`m000395`, `m000407`, `m000410`, `m000411`) | Added `util.hashTree` (SHA-256 over sorted slash-normalized relative paths, excluding `.somnus-plugin.json`); stored `skillHash` in `.somnus-plugin.json`; wired `host.drift()` into `cli.mjs` `doctor` (reporting `matches the packaged skill` or `FAIL` with rerun-install hint); preserved CRLF and no-trailing-newline byte-exactness in Codex `config.toml` managed blocks; added `spawnForm()` in `lib/backend.mjs` routing `.cmd`/`.bat` on `win32` through `shell: true` with whitespace-quoted arguments (`backendVersion`, `installBackend`, `mcpHandshake`); expanded unit tests for Windows path round-trip, `win32` `spawnForm` mock, invalid-JSON `PluginError`, `doctor` `FAIL` on dead MCP command, and corrupted Codex block repair. Executed `npm test` (`node --test`): **18/18 passed, 0 failed**. |
| `README.md`, `CONTRIBUTING.md`, `filetree.md`, `runbooks/registry-recovery.md`, `runbooks/package-release.md`, `../somnus-metadata-plugin/README.md` | `chronicler-1` (`m000400`–`m000428`) | Verified PEP 668 Linux `externally-managed-environment` refusal (`python3 -m pip install --dry-run .` against `/usr/lib/python3.14/EXTERNALLY-MANAGED`); updated `README.md` r2 and `CONTRIBUTING.md` r5 (`python3 -m venv .venv` / `uv venv .venv` required before `pip install`); kept public `README.md` plugin sentence unchanged (`LEAP` `m000402`) to avoid disclosing private repository existence on PyPI; updated `runbooks/registry-recovery.md` r1 and `runbooks/package-release.md` r1 for `DB_USER_VERSION = 2` and `src/somnus/db/search.sql`; synchronized `filetree.md` r8 (including `tests/test_term_windows.py`) and plugin `README.md` r2. |

### Remaining NOT RUN and scope boundaries

- **Windows live OS console (`kernel32`/`msvcrt` on a real Windows host) and live Windows `.cmd` execution (`m000424`):** **NOT RUN** locally (no Windows host; Linux `7.0.0-38-generic`). All Windows console mode/input branches in `src/somnus/tui/term.py` (96% coverage via `tests/test_term_windows.py` fakes) and `win32` `spawnForm()` in `somnus-metadata-plugin` are now unit-tested on Linux.
- **Installed-package acceptance harness in CI & plugin CI (`m000397`, `m000411`):** **RUN.** The `installed CLI smoke test` job in `.github/workflows/ci.yml` now runs `tests/acceptance/installed_package_acceptance.py` (green at `3dcde8b`). The private plugin repo has `.github/workflows/ci.yml` running `npm test` on ubuntu and macos for Node 20, 22 and 24 (6/6 green at `4668d32`); Windows is covered there only by `spawnForm` unit tests with a mocked platform.
- **Codex and Antigravity in-host MCP invocation:** **RUN** (2026-10-31, digger-1, re-tasted by parent-1). `codex exec --sandbox read-only` called `somnus-metadata/q`; its session log `~/.codex/sessions/2026/10/31/rollout-2026-10-31T18-25-38-*.jsonl` records `"server":"somnus-metadata"` with the SPEC.md/DECISIONS.md result rows and lists the installed `somnus-metadata` skill. `agy --sandbox --print` returned the same rows; conversation DB `~/.gemini/antigravity-cli/conversations/9b2ca119-*.db` holds 18 `somnus-metadata .../q` tool-call entries and the returned text. Write tools were not exercised in those hosts.
- **Public PyPI 2.1.0 upload:** **NOT RUN** (PyPI continues to serve `2.0.0` until an authorized release upload).

## Agent experience pass and private plugin (2026-10-31)

Core fixes (commit `22117e9`), each from driving the CLI and MCP adapter cold:
unquoted extra `q --text` words are searched; an empty search and `index`
explain adoption (`index` lists up to 10 unmanaged files); `index` refuses an
implicit home-directory or filesystem-root fallback; failed MCP calls with
relative paths name the server directory. SPEC r7. AGENTS.somnus.v2.md is now
`AGENTS.md`; the old entry file is `AGENTS.v1.md` (operator decision).

Private adapter: `calisweetleaf/somnus-metadata-plugin` (GitHub, private, commit
`71a6b5b`), Node 18+, zero dependencies, 10 `node --test` tests. It installs the
`somnus-metadata` skill and MCP server (`somnus --actor <host> mcp`) for Droid,
Codex, and Antigravity; `npx github:calisweetleaf/somnus-metadata-plugin doctor`.

Installed on this laptop (Linux) on 2026-10-31:
- backend `uv tool install --force <this checkout>` -> `~/.local/bin/somnus` 2.1.0;
  registry `~/.somnus/somnus.db` with root `~/Repositories/somnus-metadata` only.
- plugin into all three hosts; backups `~/.factory/mcp.json.bak-somnus-plugin-20261031T224721Z`
  and `~/.codex/config.toml.bak-somnus-plugin-20261031T224721Z`.
- Evidence: `tomllib` parses Codex config; doctor: all checks passed (live handshake,
  16 tools per host); Droid called `q --text` through its own MCP connection.
  Codex and Antigravity in-host calls were exercised later the same day (see the colony foray section).

Open: PyPI still serves 2.0.0 (2.1.0 not uploaded); 236 files under the root are
unmanaged until stamped; ChatGPT via OpenAI Secure MCP Tunnel is not set up.
## Full-text search — D19, package 2.1.0 (2026-10-31)

Registry schema 2 adds the derived FTS5 `search` index (SPEC §18.4, D19);
`somnus q --text WORDS` searches managed file content, including UTF-8 sidecar
hosts. Core schema stays 2.0.0. The package becomes 2.1.0 because tools that
know only registry schema 1 refuse a schema-2 registry. Not yet built for or
uploaded to PyPI; PyPI still serves 2.0.0.

| File | Change |
| --- | --- |
| `src/somnus/db/search.sql` (new), `schema.sql`, `store.py` | FTS5 DDL; rows written on index, deleted on disappearance, backfilled when missing; FTS5-less SQLite degrades to no `search` table |
| `src/somnus/commands/query.py`, `cli.py`, `brief.py` | `q --text` (plain words, `word*` prefix, BM25 ranking, excerpt column) |
| `SPEC.md` r6, `DECISIONS.md` r5 | §18.1/§18.2/§18.4/§20; D19 plus the missing D18 summary row (revisions via `somnus bump`, temporary `SOMNUS_HOME`) |
| `tests/test_store.py`, `tests/test_commands.py` | +8 tests: indexing, refresh, removal, backfill, v1 migration, sidecar text, query quoting, CLI errors |

Evidence: 484 tests OK; semantic check 0/0; mypy clean (49 files); built 2.1.0
wheel contains `search.sql`; installed acceptance 60/60
(`/tmp/somnus-acceptance-prdh_nh1/runs/20261031T220214Z`). Doctor rescan NOT RUN.
`DECISIONS.md` working copy is CRLF (index LF via `.gitattributes`); left as found.
Only files with a Somnus envelope or sidecar are indexed; adopt others with `somnus stamp`.

Next: HTTP transport is not required for ChatGPT. OpenAI Secure MCP Tunnel
(`tunnel-client --mcp-command "somnus mcp"`) reaches a local stdio server
outbound-only; plan eligibility for ChatGPT custom MCP on Plus is unverified.
Then the npm installer (Droid, Codex, Antigravity).
## Version correction — Somnus Metadata 2.0.0

The operator corrected the release identity: this completed system is version 2.
The earlier 0.1.0 upload inherited stale package metadata and was an operator-agent
error, not a new v1 lineage or the active contract. Runtime __version__,
pyproject.toml, README and the installed version assertion now agree on 2.0.0.
Mode: EDIT, limited to release identity; no algorithm/schema change.
archive/v2-proposal remains historical; SPEC core 2.0.0 remains normative.

The exact 2.0.0 wheel passed 60/60 real installed acceptance checks; 476 checkout
tests, semantic 0/0, mypy and strict package checks passed. Source diagnostic scan
remains 371 findings/70 serious, no new findings, exit 1.
Twine successfully uploaded wheel and source archive to
https://pypi.org/project/somnus-metadata/2.0.0/
Acceptance artifacts: /tmp/somnus-v2-release-ednql0pq/runs/20261024T045338Z/.
After initial propagation delay, fresh no-cache public PyPI tool installation
succeeded and printed somnus 2.0.0. The project API reports 2.0.0 as current;
both uploaded v2 artifact hashes match the exact tested local files.

The erroneous 0.1.0 release is retained as publication history, not overwritten.
Yanking was not performed: no browser is connected for PyPI release management;
existing upload credentials do not establish an authenticated management session.
No deletion was attempted. The new 2.0.0 release supersedes it.

### Historical mistaken 0.1.0 publication

## Published release — 2026-10-24 UTC

**somnus-metadata 0.1.0 is published on PyPI:**
https://pypi.org/project/somnus-metadata/0.1.0/

This current release account supersedes older landing/decision-pending statements
below. The operator authorized finishing distribution in the current turn.
The distribution was renamed from somnus (already owned on PyPI by an unrelated
project) to somnus-metadata; command/import stay somnus and core stays 2.0.0.
MANIFEST.in excludes private research, operator instructions and session artifacts.
No license grant or GitHub visibility change was invented.

Independent rerun: 476 tests OK, semantic 0/0, mypy 49 files clean, Ruff passed.
Strict twine validation and archive inventory passed. The EXACT release wheel
passed all 60 installed CLI/SQLite/file/MCP/PTY checks outside the checkout.
Both uploaded PyPI digests match local artifacts. Fresh installation from public
PyPI succeeded and verified version, import location and zero runtime deps.
Doctor remains nonzero: 49 files, 371 findings, 70 serious, zero critical.
Windows/hosted CI remain unrun; this is not universal platform certification.

Install: `uv tool install somnus-metadata` or `pipx install somnus-metadata`.
Full evidence, artifact hashes and repeatable procedure:
`runbooks/package-release.md`. No source commit/tag/push was performed.

## Commission

Finish the integrated, globally usable Somnus Metadata system under the existing
core 2.0.0 contract, preserve its distinctive mechanisms, and establish completion
through real consumed-boundary use. Do not shrink the objective to five issues or
expand it into unrelated readiness-score infrastructure.

Status of this pass: **native and installed checks passed with reviewed static
findings.** Issue #3 was reproduced at a real PTY, repaired at its owning
mechanism, and covered by falsifying tests. Issue #4's real-terminal paths,
including failure and restoration, are now exercised on a POSIX PTY. Issue #2 was
resolved by operator decision (D18) and the change was carried through SPEC,
DECISIONS, CONTRIBUTING, the navigation and agent-instruction surfaces, and the
explanatory wiki. The installed-package acceptance harness was adopted into the
repository and passes 60/60 outside the checkout. The configured pre-commit
framework was run and passed. The Doctor severity gate remains nonzero and is
reported as such, with every serious finding dispositioned.

## Changes made in this pass

All source and document edits went through Surgeon, one atomic edit per file (this
is a OneDrive-synced workspace where multi-file transactions fail).

### Issue #3 — registry notes drawn over the TUI (fixed)

| File | Change |
|---|---|
| `src/somnus/commands/_common.py` | `note()` now writes to a process-wide sink when one is installed and to stderr otherwise; added `capture_notes(sink)`, a re-entrant context manager that restores the previous sink. Default behavior is unchanged. |
| `src/somnus/tui/app.py` | Added `NoteBuffer`; both screens drain it into their status line before every frame; `main()` installs the buffer as the note sink for the whole alternate-screen session. |
| `tests/test_tui.py` | `NoteSinkTest`, `NoteBufferTest`, `RegistryNoteRoutingTest`, `PosixTerminalTest`, `WindowsConsoleGuardTest`, `TuiSaveChainPtyTest` (+17 tests). |

The sink lives in `_common.py` because `note` owns the process's informational
channel and many modules bind it by name at import time; a module-level sink read at
call time redirects `Ctx.record`'s registry diagnostics without touching callers.
Ordinary commands install no sink, so CLI stderr diagnostics are unchanged.

Reproduction and falsification. Two artifacts whose `part_of` relations form a
registry-wide cycle make `Store.observe` return an `E_GRAPH` error diagnostic, so
`Ctx.record` wrote `registry: E_GRAPH ...` to stderr while the alternate screen was
active. Observed pre-fix byte stream: the note was appended after the help row with
no cursor positioning (`... [qregistry: E_GRAPH part_of cycle ...`). After the fix
the same run renders it in the message row
(`\x1b[23;1H saved revision N; registry: E_GRAPH ...`) and writes nothing to
stderr. `TuiSaveChainPtyTest` fails on the pre-fix wiring
(`'registry:' unexpectedly found in 'registry: E_GRAPH part_of cycle ...'`) and
passes after it. The full diagnostic text exceeds the status line, so the row
clips it; the complete message remains available through `somnus index`,
`somnus q --conflicts`, and the event ledger.

### Issue #4 — real-terminal paths (now exercised)

`PosixTerminalTest` drives `tui/term.py` through a real PTY: raw-mode entry clears
`ICANON`/`ECHO` and the saved `termios` attributes are restored exactly on exit;
`suspended()` restores the normal screen and modes and re-enters; `draw` repaints
only changed rows; arrow/`CSI` sequences, `\r`, and `\x03` decode through the real
`select`/`os.read` path; a closed input raises `EOFError`; and a non-tty stdin makes
`_enter` write `LEAVE_SCREEN` and raise `TerminalError` without entering the
alternate screen. `WindowsConsoleGuardTest` asserts the Windows console adapter
refuses off Windows. The browser screen is additionally exercised end to end by the
adopted acceptance harness (see below). The Windows `msvcrt`/`ctypes` paths
themselves remain NOT RUN (no Windows host).

### Issue #2 — `W_DUPLICATE_TITLE` (resolved by D18)

SPEC §19.2 named `W_DUPLICATE_TITLE` in its warning registry but never stated a
condition, comparison method, threshold, emitting command, or validation level for
it, and no module emitted it. Every other warning code does have a defined
condition. Implementing it would have invented all five. The operator chose to
remove the undefined code rather than invent a trigger.

| File | Change |
|---|---|
| `SPEC.md` | §19.2 drops `W_DUPLICATE_TITLE` and now states that the warning registry is closed and that near-duplicate titles are a registry advisory reported by `somnus stale`, with `somnus new` refusing a colliding title (`E_IO`) unless `--force`; the decisions pointer reads D1–D18. Revision 3 → 5. |
| `DECISIONS.md` | Added D18 with context, alternatives, decision, and consequences; title and heading read D1–D18; a ratification-tracker row was added. Revision 3 → 4. |
| `CONTRIBUTING.md` | §4.5 warning list updated and states the registry is closed; §1 decision count updated; clone URL corrected. |
| `AGENTS.md`, `filetree.md`, `AGENTS.somnus.v2.md`, `.claude/skills/somnus-metadata-dev/SKILL.md`, `.factory/skills/somnus-metadata-dev/SKILL.md` | Decision count and the `tests/acceptance/` entry updated. |
| `droid-wiki/` | `how-to-contribute/debugging.md`, `cleanup-opportunities.md`, `background/design-decisions.md`, `background/index.md`, `overview/index.md`, `how-to-contribute/development-workflow.md` updated for D18, the closed warning registry, the fixed note routing, the addressed real-terminal coverage, and the current test count. |

Compatibility classification (explicit, not a silent §23 waiver). This is a
**non-breaking documentation correction inside core 2.0.0**. SPEC §23 makes removing
enum values, tightening patterns, or changing field meaning a major release. None
applies: no schema enum value is removed, no pattern changes, no field changes
meaning. `W_DUPLICATE_TITLE` was never emitted, so no consumer could depend on it.
The core schema URI therefore stays `somnus://metadata/core/2.0.0`, and the managed
documents advanced only their own document revisions through `somnus bump`. D18
records this reasoning; the SPEC revision and the core schema release were
deliberately kept independent. If the operator judges that removing any listed
diagnostic code is itself a §23 event, that is a further decision for D18 rather
than an assumption made here.

The existing near-duplicate behavior was preserved exactly: `somnus new` still
refuses at similarity 0.9, `somnus stale` still reports at 0.85, and the two
thresholds were deliberately not unified.

### Documentation drift corrected

`CONTRIBUTING.md` §2 cloned `https://github.com/daeron/somnus-metadata.git`; the
verified remote is `git@github.com:calisweetleaf/somnus-metadata`, so the HTTPS form
is now `https://github.com/calisweetleaf/somnus-metadata.git`.

## Adopted installed-package acceptance harness

`tests/acceptance/installed_package_acceptance.py` is test infrastructure, not a
product runtime or a second backend. One shared Somnus implementation stays under
`src/somnus/`, consumed by the CLI, TUI, and MCP adapter.

- **Invocation (explicit):** `python tests/acceptance/installed_package_acceptance.py`
  from the repository root; `--repo PATH` to target another checkout; `--keep` to
  retain the temp tree. The module has no `test` prefix and the directory has no
  `__init__.py`, so `python -m unittest discover -s tests` does not collect it
  (verified: discovery still yields exactly 476 tests).
- **Isolation:** one `tempfile.mkdtemp()` tree holds `build-src/`, `dist/`, `venv/`,
  `home/`, `work/`, and `cycle/`. The wheel is built from a temporary copy of
  `pyproject.toml`, `README.md`, and `src/somnus`, so the checkout is never written
  to. Any inherited `SOMNUS_HOME` is removed and replaced, so the operator's real
  registry is never touched. No source path is injected.
- **Prerequisites:** Python 3.11+; a wheel builder (`uv build`, `python -m build`,
  `python -m pip wheel`, tried in that order); a venv creator (`uv venv`,
  `python -m venv`); POSIX with `pty`/`termios` for the terminal checks.
- **Artifacts:** `result.json`, `result.md`, and `result.log` under
  `<tmp>/runs/<UTC timestamp>/`.
- **Cleanup ownership:** the harness owns the tree and deletes it on exit unless
  `--keep` is passed, which prints the path.
- **Exit behavior:** `0` all checks passed; `1` at least one check failed; `2`
  harness error (missing prerequisite, build/install failure, or a required check
  that could not run). Explicit invocation never silently skips: an unrunnable check
  is recorded as `not_run` and forces exit 2.
- **Release gate:** `CONTRIBUTING.md` §3 now requires this harness before a release,
  with its invocation, prerequisites, artifact locations, cleanup, and exit codes
  documented.

## Acceptance evidence — this pass

Source checkout, POSIX, Python 3.14.4:

| Gate | Result |
|---|---|
| `PYTHONPATH=src python -m unittest discover -s tests` | 476 tests, OK (was 459) |
| `PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic` | 0 errors, 0 warnings |
| `python -m mypy` | Success, no issues in 49 source files |
| `ruff check --select=E,F,W,B,C4,T10,ICN,PLE --ignore=E501,E741,F841,B904,B905 src tests` | All checks passed |
| `uvx --from pre-commit pre-commit run --all-files` | **all 11 configured hooks passed** (large files, yaml, toml, merge conflicts, case conflicts, debug statements, trailing whitespace, end-of-file, ruff, mypy); no file was modified |
| `PYTHONPATH=src uvx --from import-linter lint-imports --no-cache` | 6 contracts kept, 0 broken (49 files, 141 dependencies) |
| `PYTHONPATH=src uvx --with coverage coverage run -m unittest discover -s tests` + `coverage report` | 86.61% total (branch), above the configured `fail_under = 85` |
| `somnus-debug doctor scan src -c .somnus-debug/python_doctor.src.yaml` | 371 issues, 0 critical, 70 serious, exit **1** (unchanged gate, not green) |

The pre-commit run was executed on a copy of the working tree with every file
staged, so the hook fixers could not modify the operator's files and so untracked
files were covered by `--all-files`. The hooks reported no change; the working tree
is byte-identical afterwards.

Installed package, exercised outside the checkout (adopted harness):

| Item | Value |
|---|---|
| Wheel | built in the run's temp tree from a temp source copy |
| Isolated environment | a fresh venv in the run's temp tree, CPython 3.13.12 (a different minor from the checkout) |
| Isolated registry | `<tmp>/home/somnus.db` (real SQLite); the operator's registry is never touched |
| Result | **60 checks, 60 passed, 0 failed, 0 not run**, exit 0 |
| Artifacts | `<tmp>/runs/<UTC>/result.json`, `result.md`, `result.log` |

Covered by that run: `--version`; import resolves inside the venv and not the
checkout; packaged `schema.sql` present; `init`/`new`/`check`/`index`/`ls`/
`q --docs`/`q --history`/`q --tables`; `set` to revision 2 with host bytes outside
the envelope compared byte-for-byte; `bump` to revision 3; an illegal
`status draft -> active` refused with `E_LIFECYCLE` and a legal `draft -> proposed`
to revision 4; `fork` with `derived_from`; idempotent re-index; `stale` table;
`regions`; `schema --json-schema` parsed and `$id`-checked; `brief`; `stamp`
dry-run and `--write` with every host line preserved byte-for-byte; an
unpreservable XML preamble refused with `E_HOST` and the file untouched; a
same-revision body drift opening a `revision` conflict that `bump` resolves;
disappearance marked absent (not deleted) and re-observation after restore;
`migrate` on a real `archive/v0.1` example (dry-run diff, then `--write` to a
core-2.0.0 document that validates and indexes); `check --all` reporting
`W_UNMANAGED` as a warning while exiting 0; a compiler-style
`path:line:col: severity CODE field: message` diagnostic on stdout with exit 1;
`--tsv` with seven tab-separated fields and no header; `--no-color` free of ANSI
escapes; a real stdio MCP client covering `initialize`, `tools/list` (exactly the
16 non-interactive commands; `edit` and `mcp` excluded; every schema closed),
text/TSV tool content, tool errors for bad arguments and failing commands, `-32601`
for an unknown method, `-32700` for a parse error, session survival, and an empty
server stderr; the **browser screen** under a real PTY (clean enter/leave, the
document count rendered, and an open-editor round-trip exiting 0); and the editor
screen under a real PTY, asserting the `E_GRAPH` registry note reaches the frame and
never stderr.

## Doctor baseline triage

Baseline `.somnus-debug/runs/operator-baseline-20261023.md` (run ID
`20261024T030635Z`), config `.somnus-debug/python_doctor.src.yaml`, 49 files,
0 critical / 70 serious / 306 minor, exit 1.

Disposition of all 70 serious findings — none is a confirmed defect:

| Category | Count | Disposition |
|---|---:|---|
| `stubs` | 2 | `Carrier.extract` / `Carrier.render` are `typing.Protocol` declarations (`carriers/__init__.py:67-81`). Sanctioned architecture. |
| `broad_exceptions` | 4 | `cli.main` last-resort boundary (annotated `noqa`), `document.atomic_write` temp cleanup, `mcp.Server.handle` per-request boundary, `Terminal._enter` cleanup-then-reraise. Each is the narrowest correct boundary. |
| `security_risks` | 2 | `mcp.run_cli` `subprocess.run` (the adapter's only execution seam, D17) and `EditorScreen.edit_body` `subprocess.call` (the documented external-editor feature). |
| `dependency_cycles` | 1 | `carriers/__init__.py` with its three carrier modules; broken by the deliberate function-local imports in `_registry()`. The repository's own `.importlinter` layering contract passes with 3 declared ignored imports, so this is declared architecture. |
| `silent_failures` | 48 | Every handler either appends to a diagnostics list, returns a typed sentinel its caller handles, or returns an exit code / message to the caller. The TUI's 12 are the same pattern with `self.message` as the surface. |
| `suspicious_short_classes` | 13 | `@dataclass(frozen=True)` schema descriptor nodes and small value types; the canonical shape for a declarative schema DSL. |

Minor categories: `unused_imports` (50) are 43 × `from __future__ import annotations`
plus 7 `db/__init__.py` `__all__` re-exports; `missing_docstrings` (66) are the
18-character threshold on short-but-meaningful docstrings plus dunders and nested
closures; `type_hint_gaps` (34) include the 17 `run(args, ctx: Ctx) -> int`
signatures that are the *documented* command entry contract (CONTRIBUTING §4.3);
`complexity` (31) are long cohesive parsing/validation functions.

Repaired: `_Exporter` in `model/jsonschema_export.py` had no docstrings at all
despite backing the public `somnus schema --json-schema` surface. The remaining
minor findings are annotation-only or threshold artifacts with no behavioral
consequence; sweeping them would be cosmetic churn, not defect repair.

Rescan (same config, same 49-file coverage, thresholds untouched):
`.somnus-debug/runs/post-hardening-20261023.md`, run ID `20261024T041847Z`,
371 issues, 0 critical, 70 serious, exit 1. Normalized delta: the 6 `_Exporter`
docstring findings resolved; 3 new *minor* `suspicious_short_functions` on the new
`NoteBuffer` methods; **no new serious finding**. The exit code is unchanged and the
severity gate was not weakened.

## Coding-agent plugin versus MCP adapter

Clarified separately as requested. What exists in this repository is:

- an **MCP adapter**: `somnus mcp` (`src/somnus/mcp.py`), the stdio JSON-RPC server
  specified by D17 and SPEC §20, which projects every non-interactive CLI command as
  a tool. This is exercised for real by the acceptance harness.
- an **agent instruction skill**: `.claude/skills/somnus-metadata-dev/SKILL.md` and
  an identical `.factory/skills/somnus-metadata-dev/SKILL.md`. These are Markdown
  operating instructions for an agent working in this repository. They are not
  executable code and are not exercised by any test.

What does **not** exist in this public repository: no packaged coding-agent plugin
is shipped inside `somnus-metadata` (`README.md` and `MANIFEST.in` keep the public
distribution stdlib-only). A separate private repository
(`calisweetleaf/somnus-metadata-plugin`, `/home/daeron/Repositories/somnus-metadata-plugin`)
now implements the host installer/adapter for Factory Droid, Codex, and Google
Antigravity (18/18 `node --test` tests passing; see top sections).

## Not run / platform-specific

- **Windows terminal paths** (`msvcrt`, `ctypes` console modes): no Windows host.
  Only the platform guard is asserted locally, and the harness records the POSIX-only
  terminal checks as `not_run` on non-POSIX.
- **Hosted CI workflows** (`.github/workflows/*`): **RUN and green** as of 2026-10-31
  (`gh run list --limit 5` shows `CI` and `CodeQL` passing on GitHub Actions, including
  the `tooling` job running `pre-commit`, `import-linter`, and `coverage`). The
  installed-package acceptance harness (`tests/acceptance/installed_package_acceptance.py`)
  is run locally before release (65/65 passed) and runs in CI in the `installed CLI smoke test` job (since `3dcde8b`).
- **`coverage`, `import-linter`, and `pre-commit`**: remain outside runtime
  `[project] dependencies = []` (stdlib-only invariant); executed in CI's `tooling`
  job and locally via `uvx`.
- **Strict-mode mypy, and type checking of `tests/`**: the configured `mypy` run
  covers `src/somnus` only, as the project config intends.

## Working-tree preservation

The prior type-check/hardening work remains modified/untracked. Root ZIP deletions
and `archives/` predate this pass and are user-owned state. No reset, cleanup,
staging, commit, or push was performed. `build/` and `src/somnus.egg-info/` created
by an earlier wheel build were removed; the adopted harness builds from a temp copy
and writes nothing into the checkout (verified). Imported `AGENTS.template.v2.md`,
`workflows.md`, `last-session.txt`, the research document, and the House fable are
untouched.

## Observed line-ending state (reported, not changed)

`DECISIONS.md` is uniformly CRLF (331 of 331 lines) in the working copy while every
other file, including `SPEC.md`, is LF. This is pre-existing working-copy state, not
introduced by this pass:

- `.gitattributes` declares `* text=auto eol=lf`, so git normalizes CRLF to LF when
  comparing. That is why `git status` reported `DECISIONS.md` as unmodified at the
  start of this session despite the CRLF, and why `git diff` now warns that "CRLF
  will be replaced by LF the next time Git touches it".
- A controlled experiment on disposable fixtures showed Surgeon preserves the
  file's existing line endings on write (LF in, LF out; CRLF in, CRLF out).
- `SPEC.md` was edited and bumped twice in this pass and stayed LF, so `somnus bump`
  also preserves the existing endings rather than imposing one.

Given both, `DECISIONS.md` must already have been CRLF before either operation, and
the endings are uniform, so no LF lines were inserted into it. The document still
validates (0 errors at semantic level) and `somnus bump` succeeded on it, which is
further evidence that the envelope write preserved host bytes. It was deliberately
left as-is: converting it to LF would be a mass line-ending change to a user-owned
file with no functional benefit, and the operator excluded mass formatting. The
operator may normalize it on the next landing if desired.

## Workflow conflict resolved explicitly

The Somnus Code Forge layout (`tools/native/<domain>/`, `SCOPE.md`, `SOTA_RUN.md`,
`snapshots/`) does not apply to this repository: `AGENTS.md` names `src/somnus/` as
implementation truth, forbids forking `src/somnus` into `tools/native`, and defines
`tests/` plus the native gates as the evidence class. This pass used the forge's
construction discipline (mode declared per change, one unit at a time, real
fixtures, native gates, Doctor rescan, reviewed deltas) inside the repository's own
layout. No forge promotion is claimed from native tests alone.

## Next executable action

1. Core toolkit release identity is 2.0.0. Preserve immutable release artifacts;
   do not overwrite either published version. See the current correction above.
2. The operator has confirmed the distributable coding-agent plugin is required,
   but explicitly deferred it until official docs/structures are supplied.
   Do not substitute a host-specific wrapper or pretend MCP alone is that plugin.
3. D18's non-breaking documentation classification was reviewed and retained;
   no core schema payload/field change was introduced.
4. Issues #5 and #6 remain optional, not release prerequisites.
5. Future Git commit/push/tag or hosted-CI work must preserve the substantial
   pre-existing working tree and include only deliberately selected material.
   PyPI publication did not silently land that tree or make GitHub public.
