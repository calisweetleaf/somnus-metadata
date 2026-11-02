# Getting started

This page takes you from installation to a validated, indexed document. It assumes Python 3.11 or later and pip in a virtual environment.

## Prerequisites

- Python 3.11+ (the config loader uses `tomllib`, added in 3.11).
- No third-party packages. `pyproject.toml` declares `dependencies = []`.
- Python's `venv` module and pip for the installation below. `uv` and `pipx` are alternatives, not runtime dependencies.

## Install

```sh
python3 -m venv ~/.venvs/global
~/.venvs/global/bin/python -m pip install -U somnus-metadata
export PATH="$HOME/.venvs/global/bin:$PATH"
somnus --version                  # somnus 2.1.1
somnus-metadata --version          # Same CLI, also prints somnus 2.1.1
```

`README.md` and `docs/USAGE_GUIDE.md` use pip in a virtual environment as the primary install route. Make the `PATH` change persistent in your shell configuration. Non-interactive agent hosts and desktop launchers may not read `~/.bashrc`; the guide also documents linking both commands into a login-visible `~/.local/bin`. Inspect existing entries before replacing them:

```sh
mkdir -p ~/.local/bin
# If these paths are unused, create links to the same installation:
ln -s ~/.venvs/global/bin/somnus ~/.local/bin/somnus
ln -s ~/.venvs/global/bin/somnus-metadata ~/.local/bin/somnus-metadata
```

Ensure `~/.local/bin` is on the host's inherited `PATH`. Alternatively, use `uv tool install somnus-metadata` or `pipx install somnus-metadata`. Choose one installation method; two paths that resolve to the same executable are not two installs (`docs/USAGE_GUIDE.md`).

The distribution is `somnus-metadata`; the primary command and Python import are `somnus`. Starting with 2.1.0, `pyproject.toml` also installs the command alias `somnus-metadata`, targeting the same `somnus.cli:main` function in `src/somnus/cli.py`. Do not install the unrelated PyPI distribution named `somnus` into that environment.

The latest sections of `PLAN.md`, `docs/USAGE_GUIDE.md`, and `runbooks/package-release.md` record public release 2.1.1, exact-wheel acceptance, matching uploaded artifact digests, and a no-cache pip install. This is recorded operator evidence, not an installation repeated by this wiki refresh. Toolkit 2.1.1 implements core `somnus://metadata/core/2.0.0` and registry schema 2 (`src/somnus/__init__.py`); package, registry, and core metadata versions are separate concepts.

If an older command shadows the intended installation, inspect `which -a somnus somnus-metadata`, `readlink -f` on each reported path, and `somnus --version` before changing the environment. Upgrade or remove the stale copy in its owning environment and run `hash -r`. Version 2.0.0 cannot open a schema-2 registry. Use the matching toolkit; do not downgrade the database schema (`README.md`, `docs/USAGE_GUIDE.md`, `src/somnus/db/store.py`).

For an editable development environment with mypy, follow `CONTRIBUTING.md`:

```sh
python3 -m venv .venv       # or: uv venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

On PEP 668 Linux hosts, system pip refuses installs with `externally-managed-environment`. Use the activated virtual environment, `uv tool install`, or `pipx`; do not bypass the system guard (`README.md`, `CONTRIBUTING.md`).

Registry schema 2 adds search; older schema-1 writers refuse it (`src/somnus/db/store.py`, D19 in `DECISIONS.md`). Preserve a database backup before upgrading and use the matching toolkit rather than changing `PRAGMA user_version` manually.

Without installing, run the CLI from the repository root:

```sh
PYTHONPATH=src python -m somnus.cli --help
```

Or in PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m somnus.cli --help
```

The commands below use the installed `somnus` entry point. From a source checkout, replace it with `PYTHONPATH=src python -m somnus.cli` on POSIX, or set `$env:PYTHONPATH = "src"` once and use `python -m somnus.cli` in PowerShell. `AGENTS.md` and `PLAN.md` distinguish checkout verification from testing a separate installation.

## Create the registry

```
somnus init --root .
```

This creates `$SOMNUS_HOME` (default `~/.somnus/`), writes `config.toml`, creates the SQLite registry `somnus.db`, and registers the current directory as a root. Commands that need the registry fail with `E_IO ... run 'somnus init'` until this runs.

## First document

```
somnus new specification "My Spec"            # writes my-spec.md with a full header
somnus check my-spec.md --level semantic       # 0 errors expected
somnus index                                   # reconcile roots into the registry
somnus ls                                      # list indexed artifacts
```

With toolkit version 2.1.0 or later and SQLite FTS5, search the indexed text:

```sh
somnus q --text "specification"
somnus q --text "spec*" --tsv
```

Every word must match. Only managed files are indexed, and results reflect the last observation, not live filesystem search (`src/somnus/commands/query.py`, `src/somnus/db/store.py`). See [Querying](../features/querying.md).

The two-word form `somnus q --text host bytes` also works: `src/somnus/commands/query.py` treats the extra positional argument as search words, not SQL. Quote longer searches as shown above. If there are no matches, the command exits successfully and prints an adoption hint on stderr. `src/somnus/commands/index.py` names up to ten unmanaged files and suggests previewing `somnus stamp PATH` before applying `--write`. When no roots are registered, it refuses an implicit home-directory or filesystem-root fallback; register the intended project with `somnus init --root DIR`.

To adopt an existing file instead, run `somnus stamp notes.py` to see the proposed header as a diff, then `somnus stamp notes.py --write` to apply it. See [Adopting files](../features/adopting-files.md).

Registering a root does not adopt its files. `src/somnus/commands/init.py` stores roots, `src/somnus/commands/stamp.py` adds metadata to explicit file paths, and `src/somnus/commands/index.py` reconciles managed files into the registry. Since 2.1.1, `Store.scan` in `src/somnus/db/store.py` reports unmanaged hosts needing a new sidecar without reading their payloads; the CLI shows up to ten examples, while `ScanReport.unmanaged_paths` holds the complete list. Before an authorized bulk rollout, set exclusions, test representative carriers, and inspect the resulting files. The newest sections of `HANDOFF.md` and `PLAN.md` record the release/install commission complete and mark bulk adoption superseded (operator correction, 2026-11-01). The last recorded scan in `docs/USAGE_GUIDE.md` section 9 reports five registered roots with 2,659 managed hosts, 21,554 unmanaged, and no invalid/missing hosts or conflicts; the earlier 1,064 / 23,148 checkpoint is prior history, and its lower count reflected preservation exclusions, not new adoption. Do not re-register nested roots or resume bulk adoption without a new operator request.

To change the title or tags later without opening the terminal UI, use `somnus set`. Field names are the dotted header paths, and all the assignments go into one new revision:

```
somnus set my-spec.md "title=My Better Spec" "classification.tags=draft, core" --reason "rename"
```

## Connect an agent over MCP

Agents that cannot run shell commands can use `somnus mcp`, which speaks the Model Context Protocol over stdin and stdout. Register the installed command with the MCP client. For Droid, add this to `~/.factory/mcp.json`:

```json
{
  "mcpServers": {
    "somnus": { "type": "stdio", "command": "somnus", "args": ["mcp"] }
  }
}
```

The server lists one tool per CLI command (16 tools; `edit` and `mcp` are left out) and sends the `somnus brief` text as its instructions. See [Agent integration](../features/agent-integration.md).

To make registry use part of an agent's normal workflow, review [the global-instructions appendix](../../docs/AGENTS.appendix.md) and copy its fenced block into your host's global instructions yourself. It covers searching before creating documents, adoption, semantic checks, and command-owned metadata changes. Generating this wiki does not install that snippet or change host configuration.

### Private host installer

The latest `PLAN.md` and `HANDOFF.md` record the separate private [somnus-metadata-plugin](https://github.com/calisweetleaf/somnus-metadata-plugin) adapter at version 1.2.1, superseding the 1.2.0 record (which superseded the 1.1.1 record and the 1.1.0 snapshot in `docs/USAGE_GUIDE.md`). Since 1.2.1, both host catalogs install the checked-in reproducible 8-file native export rather than the development checkout. Droid, Codex, Antigravity, and OpenCode are peer hosts for one canonical consumer skill, not independent authoring sources. The guide documents Node 18.17+ and access to that repository as prerequisites; installing the Python distribution does not install it. Its recorded diagnostic command is:

```sh
npx github:calisweetleaf/somnus-metadata-plugin doctor
```

This is a recorded command, not an installer or diagnostic exercised during this refresh. `PLAN.md` records backend 2.1.1 installed with pip and fresh doctor handshakes with 16 tools per host. The guide places Codex skills under `~/.codex/skills/custom/somnus-metadata/` and Antigravity skills under `~/.gemini/skills/somnus-metadata/`. OpenCode uses `~/.config/opencode/skills/somnus-metadata/` and its local MCP configuration; restart its background server with `opencode service restart`. Re-run the installer with `--somnus /absolute/path/to/somnus` after moving the backend. See [Agent integration](../features/agent-integration.md) for the full host table and comment-preserving OpenCode setup.

Earlier in-host read queries used plugin 1.0.0 in Droid, Codex, and Antigravity. The latest `PLAN.md` evidence records fresh 26/26 plugin tests and hosted CI `41402125903` after the 1.2.1 update, which ships the clean production payload (the reproducible 8-file native export) installed in Codex and Factory with both caches inspected at 0 .somnus.yaml files. The 1.2.0 update established the native installed/enabled records in both Codex and Factory (identity somnus-metadata-plugin@somnus-metadata-plugin) and hosted CI `41399524229`; the operator corrected an earlier misreport in which direct adapter health had been claimed as native installation. Droid read its installed skill and both Droid and Codex returned three full paths from an MCP search for `host agnostic`. An early Codex skill-read attempt was NOT RUN because that child could not locate Surgeon; after the clean reinstall for Codex and Factory Droid, `HANDOFF.md` records the fresh installed skill read at both requested paths, and fresh Codex and Factory sessions called the native-plugin MCP lifecycle query returning the same source path, closing that gap. Use `tsv: true` in MCP query/list calls (CLI: `--tsv`); human tables shorten long cells. An OpenCode in-session call and host write tools remain unexercised. ChatGPT tunnel integration is not set up. Configuration loading, a doctor handshake, a skill read, and actual in-host use are separate acceptance boundaries.

## Run the tests

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
```

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
```

The suite has 537 tests in 14 modules, including the 21 conformance fixtures in `tests/test_conformance.py`, full-text and scan-safety checks in `tests/test_store.py` and `tests/test_commands.py`, and real POSIX PTY checks in `tests/test_tui.py`. The three `TestUnmanagedSidecarHosts` methods in `tests/test_store.py` cover all-file discovery, memory use, and adoption/removal reconciliation. `tests/test_term_windows.py` exercises Windows console branches with fakes, not a live Windows console. Check both the exit status and the final `OK` or `FAILED` summary. `.github/workflows/ci.yml` configures checks across Linux, Windows, and macOS and includes an installed-wheel smoke test; configuration alone does not prove those hosted runs passed.

Before a release, explicitly run `python tests/acceptance/installed_package_acceptance.py`. It builds and installs an isolated wheel and exercises real files, SQLite, stdio MCP, and POSIX terminals outside the checkout. It is not collected by unittest discovery. `.github/workflows/ci.yml` also runs it in the Ubuntu/Python 3.11 install job, after the installed-wheel smoke checks. `CONTRIBUTING.md` documents its prerequisites and exit codes. Windows console paths and external MCP hosts need separate verification. See [Testing](../how-to-contribute/testing.md).

## Where to go next

- [Architecture](architecture.md) for how the layers connect.
- [CLI commands](../features/cli-commands.md) for every subcommand.
- [Configuration](../reference/configuration.md) for `config.toml` and `.somnus.toml` keys.
- [Operator and agent usage guide](../../docs/USAGE_GUIDE.md) for the longer walkthrough, troubleshooting, and recorded remote-access proposals.
