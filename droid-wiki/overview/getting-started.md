# Getting started

This page takes you from a fresh clone to a validated, indexed document. It assumes Python 3.11 or later and, for the global install, `uv`.

## Prerequisites

- Python 3.11+ (the config loader uses `tomllib`, added in 3.11).
- No third-party packages. `pyproject.toml` declares `dependencies = []`.
- Optional: `uv` for installing the `somnus` command globally.

## Install

```
uv tool install somnus-metadata
somnus --version        # Published release recorded in PLAN.md: somnus 2.0.0
```

Alternatively use `pipx install somnus-metadata`, or `python -m pip install somnus-metadata` inside a virtual environment. For development, run `uv tool install --editable .` from the checkout (`README.md`).

The distribution is `somnus-metadata`; the command and Python import are `somnus`. Do not install the unrelated PyPI distribution named `somnus` into that environment. `pyproject.toml` and `src/somnus/__init__.py` identify this checkout as toolkit 2.1.0, implementing `somnus://metadata/core/2.0.0`. `PLAN.md` records 2.0.0 as the published PyPI release; 2.1.0 and its full-text search feature are not yet published. Use an editable checkout installation to try that feature. Package, registry, and core metadata versions are separate concepts.

```sh
uv tool install --editable .
somnus --version        # somnus 2.1.0 from this checkout
```

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

With checkout version 2.1.0 and SQLite FTS5, search the indexed text:

```sh
somnus q --text "specification"
somnus q --text "spec*" --tsv
```

Every word must match. Only managed files are indexed, and results reflect the last observation, not live filesystem search (`src/somnus/commands/query.py`, `src/somnus/db/store.py`). See [Querying](../features/querying.md).

The two-word form `somnus q --text host bytes` also works: `src/somnus/commands/query.py` treats the extra positional argument as search words, not SQL. Quote longer searches as shown above. If there are no matches, the command exits successfully and prints an adoption hint on stderr. `src/somnus/commands/index.py` names up to ten unmanaged files and suggests previewing `somnus stamp PATH` before applying `--write`. When no roots are registered, it refuses an implicit home-directory or filesystem-root fallback; register the intended project with `somnus init --root DIR`.

To adopt an existing file instead, run `somnus stamp notes.py` to see the proposed header as a diff, then `somnus stamp notes.py --write` to apply it. See [Adopting files](../features/adopting-files.md).

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

### Private host installer

`PLAN.md` records a separate private [somnus-metadata-plugin](https://github.com/calisweetleaf/somnus-metadata-plugin) adapter for Droid, Codex, and Antigravity. It requires Node 18+ and access to that repository; installing the Python distribution does not install it. Its recorded diagnostic command is:

```sh
npx github:calisweetleaf/somnus-metadata-plugin doctor
```

This is a command recorded by the handoff, not an installer or diagnostic exercised during this wiki refresh. The operator's 2026-10-31 Linux setup used backend 2.1.0 installed from a checkout, and doctor reported live handshakes with 16 tools per host. Only Droid has a recorded in-host search call; Codex and Antigravity still need restart/loading and in-host verification. ChatGPT tunnel integration is not set up. See [Agent integration](../features/agent-integration.md) before treating configuration as acceptance.

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

The suite has 486 tests, including the 21 conformance fixtures in `tests/test_conformance.py`, full-text and scan-safety checks in `tests/test_store.py` and `tests/test_commands.py`, and real POSIX PTY checks in `tests/test_tui.py`. Check both the exit status and the final `OK` or `FAILED` summary. `.github/workflows/ci.yml` configures checks across Linux, Windows, and macOS and includes an installed-wheel smoke test; configuration alone does not prove those hosted runs passed.

Before a release, explicitly run `python tests/acceptance/installed_package_acceptance.py`. It builds and installs an isolated wheel and exercises real files, SQLite, stdio MCP, and POSIX terminals outside the checkout. It is not collected by unittest discovery. `CONTRIBUTING.md` documents its prerequisites and exit codes. Windows console paths and external MCP hosts need separate verification. See [Testing](../how-to-contribute/testing.md).

## Where to go next

- [Architecture](architecture.md) for how the layers connect.
- [CLI commands](../features/cli-commands.md) for every subcommand.
- [Configuration](../reference/configuration.md) for `config.toml` and `.somnus.toml` keys.
