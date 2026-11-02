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
somnus --version                  # somnus 2.1.0
somnus-metadata --version          # Same CLI, also prints somnus 2.1.0
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

`docs/USAGE_GUIDE.md` records PyPI release 2.1.0. The [public release metadata](https://pypi.org/pypi/somnus-metadata/2.1.0/json), checked during this refresh, confirms the wheel and sdist were uploaded on 2026-11-01 UTC. This is availability evidence, not a fresh installation test. Older unpublished-release statements in `PLAN.md` predate that release. Toolkit 2.1.0 implements core `somnus://metadata/core/2.0.0` and registry schema 2 (`src/somnus/__init__.py`); package, registry, and core metadata versions are separate concepts.

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

With toolkit version 2.1.0 and SQLite FTS5, search the indexed text:

```sh
somnus q --text "specification"
somnus q --text "spec*" --tsv
```

Every word must match. Only managed files are indexed, and results reflect the last observation, not live filesystem search (`src/somnus/commands/query.py`, `src/somnus/db/store.py`). See [Querying](../features/querying.md).

The two-word form `somnus q --text host bytes` also works: `src/somnus/commands/query.py` treats the extra positional argument as search words, not SQL. Quote longer searches as shown above. If there are no matches, the command exits successfully and prints an adoption hint on stderr. `src/somnus/commands/index.py` names up to ten unmanaged files and suggests previewing `somnus stamp PATH` before applying `--write`. When no roots are registered, it refuses an implicit home-directory or filesystem-root fallback; register the intended project with `somnus init --root DIR`.

To adopt an existing file instead, run `somnus stamp notes.py` to see the proposed header as a diff, then `somnus stamp notes.py --write` to apply it. See [Adopting files](../features/adopting-files.md).

Registering a root does not adopt its files. `src/somnus/commands/init.py` stores roots, `src/somnus/commands/stamp.py` adds metadata to explicit file paths, and `src/somnus/commands/index.py` reconciles managed files into the registry. Before an authorized bulk rollout, set exclusions, test representative carriers, and inspect the resulting files. The current operator job and its still-required Droid/Codex search proof are in `HANDOFF.md`; do not treat its recorded installation and test results as completed indexing.

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

`docs/USAGE_GUIDE.md` records a separate private [somnus-metadata-plugin](https://github.com/calisweetleaf/somnus-metadata-plugin) adapter, version 1.1.0, for Droid, Codex, Antigravity, and OpenCode. It requires Node 18.17+ and access to that repository; installing the Python distribution does not install it. Its recorded diagnostic command is:

```sh
npx github:calisweetleaf/somnus-metadata-plugin doctor
```

This is a recorded command, not an installer or diagnostic exercised during this refresh. The updated guide records backend 2.1.0 installed with pip, doctor handshakes with 16 tools per host, Codex skills under `~/.codex/skills/custom/somnus-metadata/`, and Antigravity skills under `~/.gemini/skills/somnus-metadata/`. OpenCode uses `~/.config/opencode/skills/somnus-metadata/` and its local MCP configuration; restart its background server with `opencode service restart`. Re-run the installer with `--somnus /absolute/path/to/somnus` after moving the backend. See [Agent integration](../features/agent-integration.md) for the full host table and comment-preserving OpenCode setup.

In-host read queries were exercised in Droid, Codex, and Antigravity with plugin 1.0.0. An OpenCode in-session call and host write tools remain unexercised. ChatGPT tunnel integration is not set up. Configuration loading, a doctor handshake, and actual in-host use are separate acceptance boundaries (`docs/USAGE_GUIDE.md`).

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

The suite has 534 tests in 14 modules, including the 21 conformance fixtures in `tests/test_conformance.py`, full-text and scan-safety checks in `tests/test_store.py` and `tests/test_commands.py`, and real POSIX PTY checks in `tests/test_tui.py`. `tests/test_term_windows.py` exercises Windows console branches with fakes, not a live Windows console. Check both the exit status and the final `OK` or `FAILED` summary. `.github/workflows/ci.yml` configures checks across Linux, Windows, and macOS and includes an installed-wheel smoke test; configuration alone does not prove those hosted runs passed.

Before a release, explicitly run `python tests/acceptance/installed_package_acceptance.py`. It builds and installs an isolated wheel and exercises real files, SQLite, stdio MCP, and POSIX terminals outside the checkout. It is not collected by unittest discovery. `.github/workflows/ci.yml` also runs it in the Ubuntu/Python 3.11 install job, after the installed-wheel smoke checks. `CONTRIBUTING.md` documents its prerequisites and exit codes. Windows console paths and external MCP hosts need separate verification. See [Testing](../how-to-contribute/testing.md).

## Where to go next

- [Architecture](architecture.md) for how the layers connect.
- [CLI commands](../features/cli-commands.md) for every subcommand.
- [Configuration](../reference/configuration.md) for `config.toml` and `.somnus.toml` keys.
- [Operator and agent usage guide](../../docs/USAGE_GUIDE.md) for the longer walkthrough, troubleshooting, and recorded remote-access proposals.
