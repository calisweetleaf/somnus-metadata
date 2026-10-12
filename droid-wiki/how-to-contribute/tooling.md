# Tooling

The toolkit needs nothing beyond Python 3.11, but the development setup uses three external tools: uv for installing the `somnus` command, somnus-debug for static Python diagnostics, and Surgeon for making source edits. This page also covers the packaging metadata and the git attribute and ignore rules.

## Packaging (`pyproject.toml`)

| Setting | Value |
| --- | --- |
| Build backend | `setuptools.build_meta`, requires `setuptools>=68.0.0` |
| Project name and version | `somnus` `0.1.0` (the package version; the standard it implements is core 2.0.0) |
| `requires-python` | `>=3.11` (needed for `tomllib`) |
| `dependencies` | `[]`, and it must stay empty |
| Console script | `somnus = "somnus.cli:main"` |
| Package discovery | `[tool.setuptools.packages.find] where = ["src"]` |
| Package data | `"somnus.db" = ["schema.sql"]`, so the registry DDL ships with the wheel and is loaded through `importlib.resources` in `src/somnus/db/store.py` |

`src/somnus/__init__.py` carries `__version__ = "0.1.0"` alongside the schema constants (`CORE_SCHEMA`, `SPEC_PROFILE`, `BENCHMARK_PROFILE`, `MIGRATION_EXTENSION`, `DB_USER_VERSION = 1`).

## Installing with uv

```powershell
uv tool install --editable .
```

An editable install puts `somnus` on `PATH` and picks up source changes without reinstalling. Without it, run the CLI from the repository root with:

```powershell
$env:PYTHONPATH="src"; python -m somnus.cli check SPEC.md
```

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

The serious findings that remain are reviewed false positives: intentional last-resort reporting handlers (for example the `except Exception` boundary in `src/somnus/cli.py`, marked `noqa: BLE001`), protocol stubs, and short dataclasses. A new serious finding should be fixed or added to that reviewed set deliberately.

Run output goes to `.somnus-debug/runs/`, `.somnus-debug/reports/`, `.python_doctor/`, and `.python_doctor-src/`, all of which are git-ignored.

## Surgeon

All source edits go through the Surgeon MCP tool (`surgeon___surgeon` in Droid), which gives outline, view, and search reads plus atomic, verified edits with per-file undo history kept under `.surgeon/`. In this repository two constraints apply:

- **One file per call.** The folder is synced by OneDrive, and Surgeon's multi-file transactions (`multi_edit`, `prepare`/`commit`) fail with WinError 5 (access denied). Edit or create each file in its own call.
- **UTF-8 mode.** The Surgeon server now runs with `PYTHONUTF8=1`. An earlier session decoded input as cp1252 and double-encoded non-ASCII characters (`§`, en dashes, arrows) in 26 files; commit `dc3c981` repaired them. See [pitfalls](../background/pitfalls.md).

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
