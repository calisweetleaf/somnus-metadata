# Dependencies

The `somnus` package has no runtime dependencies outside the Python standard library, and that is a project rule, not an accident. `pyproject.toml` declares `dependencies = []` and `requires-python = ">=3.11"`; this page lists the stdlib modules the toolkit relies on and the tools used to develop it.

## Runtime

| Requirement | Why |
| --- | --- |
| Python 3.11 or later | `tomllib` (new in 3.11) reads `config.toml` and `.somnus.toml` in `src/somnus/config.py` |
| SQLite FTS5, optional | Enables `somnus q --text` through `src/somnus/db/search.sql`; `src/somnus/db/store.py` keeps the registry usable without it |
| No third-party packages | `AGENTS.md`: "Stdlib only. `pyproject.toml` declares `dependencies = []`; keep it that way." |

The stdlib-only rule is why the project includes its own restricted YAML parser and serializer (`src/somnus/yamlsub.py`, D7) instead of PyYAML, and its own terminal UI (`src/somnus/tui/`) instead of curses wrappers or Textual.

## Distribution and entry points

The distribution is named `somnus-metadata`; its Python import remains `somnus`. Both the checkout and public PyPI release are **2.1.0**, implementing core `somnus://metadata/core/2.0.0` and registry schema **2**; these are distinct version identities. `docs/USAGE_GUIDE.md` sections 2 and 9 supersede the older unpublished-2.1.0 state in `PLAN.md` and `runbooks/package-release.md`.

`pyproject.toml` declares both `somnus = "somnus.cli:main"` and `somnus-metadata = "somnus.cli:main"` under `[project.scripts]`. Both ship in public 2.1.0. The second name is a packaging alias, not a dependency, new Python package, extra subcommand, or extra MCP tool. The counts stay 18 commands and 16 MCP tools, and `src/somnus/cli.py` still labels help/version output `somnus`. The older 2.0.0 package lacks the alias and cannot open a schema-2 registry.

The [PyPI 2.1.0 release metadata](https://pypi.org/pypi/somnus-metadata/2.1.0/json) reports wheel upload `2026-11-01T04:10:57.876446Z` and sdist upload `2026-11-01T04:10:59.159213Z` (October 31 in the operator's local time). Artifact availability is not itself installation evidence: separately, `docs/USAGE_GUIDE.md` section 9 records a clean-venv release smoke test covering both command versions, init/stamp/index/`q --text`, and a 16-tool MCP handshake. No public install was performed during this refresh.

`tests/acceptance/installed_package_acceptance.py` includes an alias `--version` assertion in `phase_install`, bringing the installed harness to 66 checks. The latest guide records 66/66 passed; older 65/65 results in `PLAN.md` remain historical. Neither is a fresh run here. See [Testing](../how-to-contribute/testing.md) for acceptance scope and [Automation](../deployment.md) for CI/release boundaries. [`docs/USAGE_GUIDE.md`](../../docs/USAGE_GUIDE.md) covers pip-first venv installation, uv/pipx alternatives, and `PATH` shadowing. Never install the unrelated PyPI distribution named `somnus` into the same environment.

The optional global instructions in [`docs/AGENTS.appendix.md`](../../docs/AGENTS.appendix.md) are manually copied guidance, not an installed dependency or an automatic host configuration change. The separate private plugin 1.1.0 requires Node.js 18.17+ and private-repository access; it configures Droid, Codex, Antigravity, and OpenCode but is not shipped in the Python distribution. See [Agent integration](../features/agent-integration.md) for paths and host-specific evidence limits. Neither it nor the guide's remote-access options are Python runtime requirements or evidence of remote integrations exercised here.

## Standard library modules in use

Grouped by purpose, from the imports in `src/somnus/`:

| Module | Used in | Purpose |
| --- | --- | --- |
| `sqlite3` | `src/somnus/db/store.py` | The global registry |
| `importlib` (`resources`) | `src/somnus/db/store.py`, `src/somnus/cli.py` | Load the packaged `src/somnus/db/schema.sql` and `src/somnus/db/search.sql`; import command modules lazily |
| `tomllib` | `src/somnus/config.py` | Configuration files |
| `hashlib` | `src/somnus/document.py` | SHA-256 payload and body digests |
| `uuid`, `threading`, `time` | `src/somnus/ids.py` | UUIDv7 minting with in-process monotonicity |
| `unicodedata` | `src/somnus/ids.py`, `src/somnus/tui/widgets.py` | Slug transliteration; display width of characters |
| `re` | carriers, `src/somnus/yamlsub.py`, `src/somnus/regions.py`, `src/somnus/model/validate.py`, others | Patterns and envelope scanning |
| `math` | `src/somnus/yamlsub.py` | Finite-number checks |
| `tokenize`, `io` | `src/somnus/regions.py` | Find region markers in real Python comments, not strings |
| `ast` | `src/somnus/infer.py`, `src/somnus/model/validate.py` | Read module docstrings for inference; resolve `symbol` selectors |
| `json` | `src/somnus/commands/schema.py`, `src/somnus/model/validate.py`, `src/somnus/mcp.py` | JSON Schema export, json-pointer selectors into JSON hosts, and MCP JSON-RPC framing (D17); registry rows remain text/TSV |
| `tempfile`, `os` | `src/somnus/document.py` | Atomic writes (temp file plus replace) |
| `difflib` | `src/somnus/commands/_common.py`, `src/somnus/commands/stale.py`, `src/somnus/db/store.py` | Dry-run diffs; near-duplicate title ratios |
| `datetime` | `src/somnus/db/store.py`, `src/somnus/model/validate.py`, `src/somnus/model/lifecycle.py`, `src/somnus/commands/migrate.py`, `src/somnus/ids.py` | Timestamps and interval checks |
| `argparse` | `src/somnus/cli.py` | Command-line parsing |
| `termios`, `tty`, `select` | `src/somnus/tui/term.py` | Raw terminal input on POSIX |
| `msvcrt`, `ctypes` | `src/somnus/tui/term.py`, `src/somnus/commands/_common.py` | Raw console input and VT mode on Windows |
| `codecs`, `contextlib`, `shutil` | `src/somnus/tui/term.py` | Incremental key decoding, terminal mode restore, terminal size |
| `subprocess`, `shlex`, `textwrap` | `src/somnus/tui/app.py` | Launch `$EDITOR` for body edits; wrap text |
| `copy`, `dataclasses`, `typing`, `pathlib`, `sys` | Throughout | General use |

## Build

| Tool | Version | Role |
| --- | --- | --- |
| setuptools | `>=68.0.0` | Build backend (`setuptools.build_meta`); packages `src/somnus` and ships `src/somnus/db/schema.sql` and `src/somnus/db/search.sql` as package data |

## Development tools

None of these are imported by the package or needed to run it.

`pyproject.toml` declares zero runtime dependencies, one build requirement (`setuptools>=68.0.0`), and one optional `dev` requirement (`mypy>=1.9`). Install the latter with `python -m pip install -e ".[dev]"` inside an activated development venv. Other tools below have separate configuration or are optional operator tools.

| Tool | Role | More |
| --- | --- | --- |
| pip and venv | Primary public install: `~/.venvs/global/bin/pip install -U somnus-metadata`; editable checkout development: `python -m pip install -e ".[dev]"` in a venv | [Tooling](../how-to-contribute/tooling.md) |
| uv or pipx | Optional isolated public installs (`uv tool install somnus-metadata` / `pipx install somnus-metadata`); uv also supports `uv tool install --editable .` | [Tooling](../how-to-contribute/tooling.md) |
| somnus-debug | Static Python diagnostics with `.somnus-debug/python_doctor.yaml` and `.somnus-debug/python_doctor.src.yaml` | [Tooling](../how-to-contribute/tooling.md) |
| Surgeon | MCP tool used for all source edits, one file per call in this folder | [Tooling](../how-to-contribute/tooling.md) |
| `unittest` (stdlib) | The test runner; no pytest | [Testing](../how-to-contribute/testing.md) |
| mypy | Configured source type check and the optional `dev` extra in `pyproject.toml` | [Testing](../how-to-contribute/testing.md) |
| pre-commit and Ruff | File hygiene, linting, and type-check hooks in `.pre-commit-config.yaml`; no formatter hook | [Tooling](../how-to-contribute/tooling.md) |
| coverage and import-linter | Optional branch-coverage and architecture checks using `.coveragerc` and `.importlinter`; not project dependencies | [Testing](../how-to-contribute/testing.md) |

`.github/dependabot.yml` schedules weekly GitHub Actions and Python build/dev update proposals. It does not enforce dependency age: `CONTRIBUTING.md` requires at least seven days after upstream release before merging a dependency update, except an explicitly reviewed security exception.

## GitHub Actions

Commit `954d5b4` updates six action families across the four workflows below. These are automation dependencies, not Python runtime requirements. The table records configured refs, not a claim that the upstream releases or hosted runs were verified during this refresh.

| Action | Configured ref | Workflow sources |
| --- | --- | --- |
| `actions/checkout` | `v7` | `.github/workflows/ci.yml`, `.github/workflows/codeql.yml`, `.github/workflows/droid-wiki-refresh.yml`, `.github/workflows/release.yml` |
| `actions/setup-python` | `v7` | `.github/workflows/ci.yml`, `.github/workflows/release.yml` |
| `gitleaks/gitleaks-action` | `v3` | `.github/workflows/ci.yml` |
| `github/codeql-action/init`, `github/codeql-action/analyze` | `v4` | `.github/workflows/codeql.yml` |
| `actions/upload-artifact` | `v7` | `.github/workflows/droid-wiki-refresh.yml` |
| `actions/download-artifact` | `v8` | `.github/workflows/droid-wiki-refresh.yml` |

The wiki publisher remains pinned to `peter-evans/create-pull-request@5f6978faf089d4d20b00c7766989d076bb2fc7f1` (v8.1.1) in `.github/workflows/droid-wiki-refresh.yml`. See [Automation](../deployment.md) for permissions, the artifact handoff, and release boundaries.

## Adding a dependency

Do not. If a feature seems to need a third-party package, the expected path is a small stdlib implementation or a change to the feature. A real exception would be a change to the project's constraints in `AGENTS.md` and would need the operator's explicit decision.

## Key source files

| File | Role |
| --- | --- |
| `pyproject.toml` | Distribution version, empty runtime dependencies, build/dev requirements, both console scripts, and SQL package data |
| `src/somnus/cli.py` | Shared parser and `somnus` help/version identity |
| `tests/acceptance/installed_package_acceptance.py` | Isolated installation and alias version assertion |
| `PLAN.md`, `runbooks/package-release.md` | Historical publication and acceptance evidence; older unpublished state is superseded by the usage guide |
| `README.md`, `docs/USAGE_GUIDE.md`, `docs/AGENTS.appendix.md` | Current public release/install guidance, four-host setup boundaries, and optional manual agent instructions |
