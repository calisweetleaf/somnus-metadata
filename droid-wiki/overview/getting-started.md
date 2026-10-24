# Getting started

This page takes you from a fresh clone to a validated, indexed document. It assumes Python 3.11 or later and, for the global install, `uv`.

## Prerequisites

- Python 3.11+ (the config loader uses `tomllib`, added in 3.11).
- No third-party packages. `pyproject.toml` declares `dependencies = []`.
- Optional: `uv` for installing the `somnus` command globally.

## Install

```
uv tool install somnus-metadata
somnus --version        # somnus 2.0.0
```

Alternatively use `pipx install somnus-metadata`, or `python -m pip install somnus-metadata` inside a virtual environment. For development, run `uv tool install --editable .` from the checkout (`README.md`).

The distribution is `somnus-metadata`; the command and Python import are `somnus`. Do not install the unrelated PyPI distribution named `somnus` into that environment. `pyproject.toml` and `src/somnus/__init__.py` identify toolkit version 2.0.0, implementing `somnus://metadata/core/2.0.0`. Package and schema releases remain separate concepts.

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

The suite has 476 tests, including the 21 conformance fixtures in `tests/test_conformance.py` and real POSIX PTY checks in `tests/test_tui.py`. Check both the exit status and the final `OK` or `FAILED` summary. `.github/workflows/ci.yml` configures checks across Linux, Windows, and macOS and includes an installed-wheel smoke test; configuration alone does not prove those hosted runs passed.

Before a release, explicitly run `python tests/acceptance/installed_package_acceptance.py`. It builds and installs an isolated wheel and exercises real files, SQLite, stdio MCP, and POSIX terminals outside the checkout. It is not collected by unittest discovery. `CONTRIBUTING.md` documents its prerequisites and exit codes. Windows console paths and external MCP hosts need separate verification. See [Testing](../how-to-contribute/testing.md).

## Where to go next

- [Architecture](architecture.md) for how the layers connect.
- [CLI commands](../features/cli-commands.md) for every subcommand.
- [Configuration](../reference/configuration.md) for `config.toml` and `.somnus.toml` keys.
