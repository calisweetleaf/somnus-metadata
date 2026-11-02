# Reference

Lookup pages for configuration keys, header fields, registry tables, and dependencies. Each page is derived from the source file named in it, so when the code changes, that file is the one to re-read.

| Page | Contents | Source of truth |
| --- | --- | --- |
| [Configuration](configuration.md) | Every config key, its type and default, validation errors, `SOMNUS_HOME`, and `.somnus.toml` discovery | `src/somnus/config.py` |
| [Data models](data-models.md) | Top-level `somnus:` header fields and their sub-objects; registry tables, views, and derived search index | `src/somnus/model/schema.py`, `src/somnus/db/schema.sql`, `src/somnus/db/search.sql`, `SPEC.md` sections 4 and 18 |
| [Dependencies](dependencies.md) | Runtime dependencies (none), stdlib modules in use, development tools | `pyproject.toml`, imports in `src/somnus/` |

For CLI flags and subcommands, see [CLI commands](../features/cli-commands.md). For per-field documentation at the terminal, run `somnus schema FIELD`; for a JSON Schema export, `somnus schema --json-schema --out FILE`.
