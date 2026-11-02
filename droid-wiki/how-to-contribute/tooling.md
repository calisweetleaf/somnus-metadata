# Tooling

The runtime needs Python 3.11 or later and no third-party packages (`pyproject.toml`). Installation is pip-first in a virtual environment, with uv and pipx alternatives (`README.md`, `docs/USAGE_GUIDE.md`). Development tooling includes the somnus-debug configs and GitHub Actions for testing and wiki refresh. `AGENTS.md` also records a OneDrive-specific constraint on multi-file Surgeon edits.

## Packaging (`pyproject.toml`)

| Setting | Value |
| --- | --- |
| Build backend | `setuptools.build_meta`, requires `setuptools>=68.0.0` |
| Project name and version | Published and checkout distribution `somnus-metadata` `2.1.0`; import `somnus`; commands `somnus` and `somnus-metadata`; standard core 2.0.0 |
| `requires-python` | `>=3.11` (needed for `tomllib`) |
| `dependencies` | `[]`, and it must stay empty |
| Console scripts | Both `somnus` and `somnus-metadata` target `somnus.cli:main` in `src/somnus/cli.py` |
| Package discovery | `[tool.setuptools.packages.find] where = ["src"]` |
| Package data | `"somnus.db" = ["schema.sql", "search.sql"]`, so both `src/somnus/db/schema.sql` and `src/somnus/db/search.sql` ship with the wheel and are loaded through `importlib.resources` in `src/somnus/db/store.py` |

`src/somnus/__init__.py` carries `__version__ = "2.1.0"` alongside the schema constants (`CORE_SCHEMA`, `SPEC_PROFILE`, `BENCHMARK_PROFILE`, `MIGRATION_EXTENSION`, `DB_USER_VERSION = 2`). `docs/USAGE_GUIDE.md` section 9 records public PyPI 2.1.0 and supersedes the older unpublished state in `PLAN.md` and `runbooks/package-release.md`; those remain historical release evidence. Do not co-install the unrelated PyPI distribution `somnus`: it shares the import/command names.

The optional `dev` extra installs `mypy>=1.9`; it does not add runtime dependencies. `python -m mypy` checks `src/somnus` using `pyproject.toml`, not strict mode or the tests. This refresh at `da82a7a` passed all 49 source files with a temporary isolated mypy 1.18.2 installation after finding mypy absent. An earlier refresh found two errors with 1.9.0 in `src/somnus/tui/term.py`; that older version and the entire declared version range were not rerun here. See [Testing](testing.md).

`CONTRIBUTING.md` requires creating and activating a virtual environment before editable pip installs on PEP 668 Linux systems. System pip's `externally-managed-environment` refusal is an environment guard, not a toolkit defect; do not bypass it. The install routes below follow `README.md` and `docs/USAGE_GUIDE.md` section 2.

## Development controls

- `.pre-commit-config.yaml` configures hygiene checks, Ruff lint (selected `E,F,W,B,C4,T10,ICN,PLE` rules), and mypy. There is no formatter hook. Only `trailing-whitespace` and `end-of-file-fixer` exclude Markdown, `archive/`, `archives/`, and `tests/`; other hooks have their own scopes. The 500 KB large-file gate separately excludes `archives/`. Configuration does not prove hooks are installed; `pre-commit install` enables them locally.
- `.importlinter` defines six layer/isolation contracts with three distinct sanctioned cross-links. Run with the package importable: `PYTHONPATH=src lint-imports --config .importlinter --no-cache`.
- `.coveragerc` measures statement and branch coverage over `src/somnus` and fails below 85%. The latest 88.76% recorded in `PLAN.md` is not a fresh coverage measurement.
- `.devcontainer/devcontainer.json` selects Python 3.11, source-checkout `PYTHONPATH`, editable `.[dev]` installation, unittest discovery, and VS Code Python/Pylance/mypy extensions. It is configuration, not proof a container was exercised.
- `.github/dependabot.yml` proposes weekly grouped Actions and pip dev/build updates. `CONTRIBUTING.md` requires seven days of release age before merge (critical-security exception requires inspection and sign-off); Dependabot does not enforce that cooling period here.

## Installing with pip (uv/pipx alternatives)

For global use on Linux, install the public release into a venv and expose its commands:

```sh
python3 -m venv ~/.venvs/global
~/.venvs/global/bin/pip install -U somnus-metadata
export PATH="$HOME/.venvs/global/bin:$PATH"
mkdir -p ~/.local/bin
ln -sf ~/.venvs/global/bin/somnus ~/.local/bin/somnus
ln -sf ~/.venvs/global/bin/somnus-metadata ~/.local/bin/somnus-metadata
```

Persist the venv `PATH` entry for interactive shells as appropriate. The links cover non-interactive agent hosts that do not read `~/.bashrc`, provided their login environment includes `~/.local/bin`. `uv tool install somnus-metadata` and `pipx install somnus-metadata` are alternatives, not additional copies to layer over pip. See [Getting started](../overview/getting-started.md) for setup and [Debugging](debugging.md) for `which -a`, resolved symlink targets, stale versions, and `hash -r`.

For editable development, run from the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

`uv venv .venv` can create the development environment instead. An alternative tool-managed editable install is `uv tool install --editable .`. Editable installs pick up source changes without reinstalling; reinstall when console-script declarations change so both executable entry points are created. `src/somnus/cli.py` still uses `somnus` in help and version output; there is one parser, not an alias-specific command surface. Without an installation, run the CLI from the repository root with:

```powershell
$env:PYTHONPATH="src"; python -m somnus.cli check SPEC.md
```

Plugin host entries pin an absolute backend executable; rerun `install --somnus /abs/path/to/somnus` after relocation. The private Node.js plugin is not a Python dependency or part of the wheel; its four-host setup and separate evidence are on [Agent integration](../features/agent-integration.md).

## somnus-debug doctor

somnus-debug is the operator's own Python diagnostics tool. Two configs live in `.somnus-debug/`, and both use schema version 3.0 with identical thresholds and severities. They differ in what they scan and where they keep state.

| Config | Scan | Includes | State dir |
| --- | --- | --- | --- |
| `.somnus-debug/python_doctor.yaml` | Repository root | `src/*.py`, `tests/*.py`; ignores `archive/*`, `.venv/*`, `build/*`, and other tool caches | `.python_doctor` |
| `.somnus-debug/python_doctor.src.yaml` | `src` | `*.py` | `../.python_doctor-src` |

The source config exists because the doctor names modules relative to the scan root. Scanned from the repository root, `somnus.*` imports do not resolve and every one is reported as `missing_imports`. Its header comment gives the command:

```powershell
somnus-debug doctor scan src -c .somnus-debug/python_doctor.src.yaml
```

Shared settings: functions shorter than 5 lines and classes shorter than 6 are flagged as suspiciously short, cyclomatic complexity above 12 is reported, docstrings and parameter and return hints are required, and private functions are not checked. `severity_exit_level` is `serious`. The serious categories are `missing_imports`, `dependency_cycles`, `stubs`, `placeholder_returns`, `incomplete_methods`, `suspicious_short_classes`, `silent_failures`, `broad_exceptions`, `security_risks`, and `test_gaps`; syntax, tokenization, and read errors are critical; everything else is minor.

These are diagnostic settings, not a current scan result. Review findings against the code before classifying them; a broad last-resort handler or short dataclass may be intentional, but the configuration alone does not prove a finding is a false positive.

The latest 2026-10-31 baseline in `PLAN.md` records 49 files and 374 findings: 0 critical, 71 serious, 303 minor, exit 1. The new serious finding is the documented empty-body sentinel for non-UTF-8 sidecar hosts in `src/somnus/db/store.py`; the handoff records source/test review of it and the prior 70 serious findings. That disposition does not make the configured severity gate green. Doctor was not rerun in this documentation refresh.

Run output goes to `.somnus-debug/runs/`, `.somnus-debug/reports/`, `.python_doctor/`, and `.python_doctor-src/`, all of which are git-ignored.

## Surgeon

`AGENTS.md` is the mission-first entry, promoted on 2026-10-31; `AGENTS.v1.md` is the preserved superseded entry. It records that multi-file Surgeon transactions fail with WinError 5 in the operator's OneDrive-synced folder. `.codex/OPERATING.md` documents the composed operator route, including Surgeon edits and diagnostics. This does not prove Surgeon, Doctor, BB7, or global hooks are installed in the current runner, nor install a project-local hook. When using Surgeon in that environment:

- **One file per call.** The folder is synced by OneDrive, and Surgeon's multi-file transactions (`multi_edit`, `prepare`/`commit`) fail with WinError 5 (access denied). Edit or create each file in its own call.
- **Encoding.** Preserve UTF-8 input and output. An earlier session decoded input as cp1252 and double-encoded non-ASCII characters in 26 files; commit `dc3c981` repaired them. A current server encoding setting is not declared in the repository. See [Pitfalls](../background/pitfalls.md).

## GitHub Actions

| Workflow | Purpose |
| --- | --- |
| `.github/workflows/ci.yml` | Eight OS/Python test combinations, semantic validation, stdlib/archive guards, mypy, Gitleaks, pre-commit, import contracts, coverage, wheel smoke test and installed-package acceptance |
| `.github/workflows/codeql.yml` | Python security analysis on main pushes, pull requests, and weekly Monday schedule |
| `.github/workflows/release.yml` | `v*` tag tests/build/version check and GitHub Release with distribution artifacts; not a PyPI publisher |
| `.github/workflows/droid-wiki-refresh.yml` | Push-triggered incremental wiki generation and a separate publish job that updates the `factory/droid-wiki` pull request |

Commit `954d5b4` updates the workflows to checkout v7, setup-python v7, Gitleaks v3, CodeQL v4, upload-artifact v7, and download-artifact v8. The configured jobs, permissions, and test matrix are unchanged. The wiki pull-request action remains commit-pinned at v8.1.1. See [Dependencies](../reference/dependencies.md#github-actions) for the exact action-to-workflow mapping. These refs describe configuration; this refresh did not execute the hosted workflows or verify upstream release age.

Commit `a5c507c` adds `delete-branch: true` to the pull-request action in `.github/workflows/droid-wiki-refresh.yml`: a publish run with nothing left to review removes `factory/droid-wiki`. If that branch is absent, generation starts from the wiki on the checked-out branch, normally the merged copy on `main`. A missing rolling branch alone does not require full regeneration. This configuration change leaves product code, workflow triggers, and permissions unchanged; hosted cleanup was not exercised here.

Commit `66847b7` adds `paths-ignore: ['droid-wiki/**']` to the main push trigger in `.github/workflows/droid-wiki-refresh.yml`. Merging a wiki-only pull request no longer starts another metadata-only refresh. A push that also changes another path still qualifies. Permissions and the rolling publish flow are unchanged; this refresh did not execute the hosted trigger.

Since commit `3dcde8b`, the Ubuntu/Python 3.11 install job in `.github/workflows/ci.yml` explicitly invokes `tests/acceptance/installed_package_acceptance.py` after the installed-wheel smoke checks. The current 66-check harness builds its own wheel and uses a separate venv and isolated `SOMNUS_HOME`; it exercises both command entry points, SQLite registry, stdio MCP, and real POSIX PTYs. It is not collected by unittest discovery and does not certify native Windows consoles or external MCP applications. `PLAN.md` records a green hosted run of the earlier 65-check harness at `3dcde8b`; that is prior handoff evidence, not a hosted run inspected by this refresh. See [Testing](testing.md).

The CI install job uses `pip`, `build`, and the setuptools backend; those are build tools, not runtime dependencies. Wiki generation uses Factory Droid and the `FACTORY_API_KEY` secret. The publish job optionally uses `FACTORY_WIKI_PR_TOKEN`, otherwise `github.token`. Do not print secret values. See [Automation](../deployment.md) for permissions, artifacts, token caveats, and recovery.

## Git attributes and ignores

`.gitattributes`:

```
* text=auto eol=lf
*.db binary
```

All text files are normalized to LF in the repository and checked out as LF (commit `3f835bc`). SQLite files are treated as binary. The toolkit itself preserves whatever line endings a file already has, so this rule only governs what git stores.

`.gitignore` excludes Python build output (`__pycache__/`, `*.pyc`, `*.egg-info/`, `build/`, `dist/`), doctor state and reports (`.python_doctor/`, `.python_doctor-src/`, `.somnus-debug/runs/`, `.somnus-debug/reports/`, both `production_doctor.log` files), and Surgeon history (`.surgeon/`).

## Related pages

- [Dependencies](../reference/dependencies.md) for the stdlib modules the toolkit uses
- [Debugging](debugging.md) for runtime diagnostics
- [Patterns and conventions](patterns-and-conventions.md)
