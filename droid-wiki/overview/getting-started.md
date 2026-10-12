# Getting started

This page takes you from a fresh clone to a validated, indexed document. It assumes Python 3.11 or later and, for the global install, `uv`.

## Prerequisites

- Python 3.11+ (the config loader uses `tomllib`, added in 3.11).
- No third-party packages. `pyproject.toml` declares `dependencies = []`.
- Optional: `uv` for installing the `somnus` command globally.

## Install

```
uv tool install --editable .
somnus --version        # somnus 0.1.0
```

The package version (`0.1.0`, from `src/somnus/__init__.py`) is separate from the standard release it implements (`somnus://metadata/core/2.0.0`).

Without installing, run the CLI from the repository root:

```
$env:PYTHONPATH = "src"          # PowerShell
python -m somnus.cli --help
```

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

## Run the tests

```
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

The suite has 443 tests and runs in about three seconds. In PowerShell 5.1 the command can report exit code 1 even when it passes, because unittest writes its progress to stderr; read the final `OK` or `FAILED` line. See [Testing](../how-to-contribute/testing.md).

## Where to go next

- [Architecture](architecture.md) for how the layers connect.
- [CLI commands](../features/cli-commands.md) for every subcommand.
- [Configuration](../reference/configuration.md) for `config.toml` and `.somnus.toml` keys.
