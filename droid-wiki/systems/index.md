# Systems

The internal building blocks of `src/somnus/`, from the text layer up. Each page covers one layer from the [architecture](../overview/architecture.md).

| Page | Covers | Main files |
| --- | --- | --- |
| [YAML subset](yaml-subset.md) | Restricted YAML parser and canonical serializer | `src/somnus/yamlsub.py` |
| [Carriers](carriers.md) | Finding and writing envelopes per file type | `src/somnus/carriers/` |
| [Document model](document-model.md) | Loading files, regions, host-byte preservation, digests | `src/somnus/document.py`, `src/somnus/regions.py` |
| [Validation](validation.md) | Schema, vocabularies, lifecycle, four-level validator | `src/somnus/model/` |
| [Registry](registry.md) | Global SQLite registry, scanning, conflicts, derived FTS5 search | `src/somnus/db/` |
| [Terminal UI](tui.md) | `somnus edit` browser and header editor | `src/somnus/tui/` |

Small support modules:

- `src/somnus/ids.py` mints UUIDv7 artifact URNs, parses references, normalizes v0.1 IDs, and builds slugs.
- `src/somnus/config.py` loads layered configuration; see [Configuration](../reference/configuration.md).
- `src/somnus/infer.py` guesses type, title, and carrier for `stamp` and `new`; see [Adopting files](../features/adopting-files.md).
- `src/somnus/output.py` defines `Diagnostic`, `SomnusError`, exit codes, and table rendering; see [Patterns and conventions](../how-to-contribute/patterns-and-conventions.md).
