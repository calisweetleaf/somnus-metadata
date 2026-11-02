---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a67-7b81-755d-a758-5fd29a9aff88"
  revision: 1
  title: "Reference"
  classification:
    category: "context"
    type: "index"
    role: "informative"
    scope: "component"
    tags: []
  lifecycle:
    status: "draft"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a19a67-7b81-755d-a758-5fd29a9aff88"
        aspects: ["content"]
  time: {}
  names:
    slug: "reference"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19a67-7b81-755d-a758-5fd29a9aff88"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Reference

Lookup pages for configuration keys, header fields, registry tables, and dependencies. Each page is derived from the source file named in it, so when the code changes, that file is the one to re-read.

| Page | Contents | Source of truth |
| --- | --- | --- |
| [Configuration](configuration.md) | Every config key, its type and default, validation errors, `SOMNUS_HOME`, and `.somnus.toml` discovery | `src/somnus/config.py` |
| [Data models](data-models.md) | Top-level `somnus:` header fields and their sub-objects; registry tables, views, and derived search index | `src/somnus/model/schema.py`, `src/somnus/db/schema.sql`, `src/somnus/db/search.sql`, `SPEC.md` sections 4 and 18 |
| [Dependencies](dependencies.md) | Runtime dependencies (none), stdlib modules in use, development tools | `pyproject.toml`, imports in `src/somnus/` |

For CLI flags and subcommands, see [CLI commands](../features/cli-commands.md). For per-field documentation at the terminal, run `somnus schema FIELD`; for a JSON Schema export, `somnus schema --json-schema --out FILE`.
