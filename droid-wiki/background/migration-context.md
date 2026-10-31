# Migration context

Core 2.0.0 replaced the v0.1 "Somnus Markdown Metadata Standard" rather than extending it. This page explains what v0.1 looked like, what changed, where the old material lives, and how `somnus migrate` (SPEC section 22) carries a v0.1 document forward without losing anything.

## Where the old material lives

`archive/README.md` puts everything under `archive/` behind a warning: it is historical, not normative, and must not be imported or cited as active. `src/` never imports from it (D15), and the default index configuration excludes `archive/**`.

| Path | What it was | Superseded by |
| --- | --- | --- |
| `archive/v0.1/SOMNUS-METADATA-SPEC-v0.1.md` | The v0.1 specification (1,287 lines) | `SPEC.md` |
| `archive/v0.1/GLOSSARY.md` | v0.1 vocabulary | `SPEC.md` section 2, `src/somnus/model/vocab.py` |
| `archive/v0.1/schemas/v1/` | v0.1 JSON Schemas (`archive/v0.1/schemas/v1/core.json` plus engineering benchmark and specification profiles) | `somnus schema --json-schema` |
| `archive/v0.1/examples/` | Three v0.1 example documents | `somnus new`; still used as `somnus migrate` test inputs |
| `archive/v0.1/tools/` | `archive/v0.1/tools/validate.py` and `archive/v0.1/tools/operator_docs_audit.py` | `somnus check` |
| `archive/v2-proposal/` | `archive/v2-proposal/SOMNUS_FRONTMATTER_SPEC_v2.md` and `archive/v2-proposal/differences.md` | `SPEC.md`, `DECISIONS.md` |

## What v0.1 looked like

v0.1 was Markdown-only. Its main traits, from `archive/v0.1/SOMNUS-METADATA-SPEC-v0.1.md`:

- **Hybrid Semi-Flat roots (section 5).** `id`, `slug`, `aliases`, `title`, `description`, and timestamps sat at the frontmatter root next to mappings such as `classification`, `lifecycle`, `location`, `origin`, `relations`, and `provenance`. The `somnus:` key held only `version: "0.1.0"` and `schema: "somnus://core/v1"`. Strict full namespacing was explicitly forbidden.
- **Bare UUIDv7 IDs (section 11)** with no URN wrapper.
- **`lifecycle.is_canonical`** as a boolean flag for authority (section 8.5).
- **Two-tier provenance (section 9)** with `authors`, `operators`, `verification`, and a `history_ledger` path pointing at an external JSON file.
- **Relation buckets (section 10)** such as `supersedes`, `superseded_by`, `derived_from`, `cites`, and `complements`, each a list of bare IDs, including authored inverse buckets.
- **Submatter directives (section 13).** Regions were `:::submatter:<type>{id="..." status="..."}` fenced blocks, with attributes in the body. Unknown attributes were preserved and only warned about.
- **JSON Schema Draft 2020-12 profiles (section 12)** for validation.

## What changed in 2.0.0

| v0.1 | Core 2.0.0 | Decision |
| --- | --- | --- |
| Root-level `id`, `title`, and namespaces | Everything under `somnus:`; host keys are left alone | D1 |
| `:::submatter` directives with body attributes | Comment-marker pairs carrying identity only; attributes in `knowledge.regions` | D2 |
| Bare UUIDv7 | `urn:somnus:artifact:<uuid>`; UUIDv4 and v0.1 IDs wrapped, not reminted | D3 |
| External JSON ledger and inline provenance | Global SQLite registry with append-only `events`; no JSON | D4 |
| Unknown submatter attributes tolerated | Every object closed; unknown fields are `E_SCHEMA` | D5 |
| `is_canonical: true` | Scoped `authority.standing` that needs an acceptance record | D9 |
| Root timestamps only | Separate authorship, applicability, and observation clocks | D10 |
| Bare relation buckets with authored inverses | Qualified relation records; inverses are registry views | D11 |
| Markdown only | Carrier matrix: frontmatter, HTML comment, line and block comments, sidecars | D8 |

The `archive/v2-proposal/` documents were an intermediate step. They already carry core 2.0.0 headers (for example `archive/v2-proposal/differences.md` is a `report` with status `proposed`), but the proposal itself is superseded by `SPEC.md` and `DECISIONS.md`.

## How `somnus migrate` bridges the gap

SPEC section 22 defines the conversion, implemented in `src/somnus/commands/migrate.py`. The legacy header is parsed in lenient mode (plain scalars allowed), then:

1. `schema` is pinned to core 2.0.0, the UUID is wrapped as `urn:somnus:artifact:<uuid>` without reminting, and `revision` becomes 1.
2. `title`, `description` (to `summary`), and `purpose` are mapped; `slug` and `aliases` go to `names`; `created_at`, `updated_at`, and `lifecycle.reviewed_at` go to `time` with their precision preserved.
3. Vocabulary-valid classification and lifecycle values are mapped. `is_canonical` never raises standing, which becomes `candidate` with a self-scope.
4. `supersedes`, `derived_from`, and `cites` become qualified relations with `assessment: unassessed` and `valid_time.basis: unknown`, and `urn:somnus:doc:` references are normalized. Authored inverse buckets are dropped as relations.
5. `location` and `origin` paths become `locations` entries with `primary`, `origin`, or `historical` roles.
6. Live `:::submatter:<kind>{id=...}` directives outside code become marker pairs and region records. Valid local IDs are kept; UUID-style IDs become `r-<kind>-<first 8 hex>`.
7. Every unmapped key (`provenance`, `origin.initial_commit`, `history_ledger`, genre profile blocks, unmapped enum values, directive attributes) is kept under `extensions.somnus-migration` with schema `somnus://metadata/extension/migration-v0.1/1.0.0`.
8. `access` and `ingestion` come from the configured operator defaults.

Migration stops with exit 1 and leaves the file untouched when the legacy `id` is missing or not a UUID, or when the frontmatter cannot be parsed. It also refuses to write when the migrated result does not validate. Files that are already core 2.0.0 are skipped.

Run it as a dry run first, review the diff, then rerun with `--write`:

```powershell
somnus migrate path\to\old.md
somnus migrate path\to\old.md --write
```

See [migration](../features/migration.md) for the user-facing walkthrough.
