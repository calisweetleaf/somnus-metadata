# Data models

There are two data models: the `somnus:` header carried in each file, declared as a schema tree in `src/somnus/model/schema.py`, and the registry database, declared in `src/somnus/db/schema.sql` and `src/somnus/db/search.sql`. Both follow `SPEC.md`: the header contract is in sections 4 to 17, and the registry in section 18.

## Header payload

The envelope payload has one root key, `somnus`. Its fields appear in this canonical order, which the serializer also uses (the order is derived from the `Obj` declarations in `src/somnus/model/schema.py`). **R** marks required fields.

| # | Field | Type | R | Contract | SPEC |
| --- | --- | --- | --- | --- | --- |
| 1 | `schema` | string | R | Exactly `somnus://metadata/core/2.0.0` | 4.1, 23 |
| 2 | `id` | string | R | `urn:somnus:artifact:<uuid>` or `urn:somnus:example:<slug>` | 3 |
| 3 | `revision` | integer | R | 1 or greater | 3 |
| 4 | `title` | string | R | Nonempty | 4.1 |
| 5 | `summary` | string | | Nonempty | 4.1 |
| 6 | `purpose` | string | | Nonempty | 4.1 |
| 7 | `language` | string | | BCP 47 tag, `[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*` | 4.1 |
| 8 | `edition` | string | | Human release label | 4.1 |
| 9 | `classification` | object | R | Category, type, role, scope, tags | 5 |
| 10 | `lifecycle` | object | R | Status and transition data | 7 |
| 11 | `authority` | object | R | Scoped standing | 8 |
| 12 | `time` | object | R | Authorship clock; may be `{}` | 9 |
| 13 | `names` | object | | Slug and aliases | 10.1 |
| 14 | `context` | object | | Project, system, division, repository refs; constraints | 5.3 |
| 15 | `ownership` | object | | Owner, maintainers, rights | 15.2 |
| 16 | `locations` | array | | Where the artifact lives | 15.3 |
| 17 | `representations` | array | | Other renderings (for example a PDF) | 15.3 |
| 18 | `content` | object | | Math, resources, extraction state | 14 |
| 19 | `knowledge` | object | R | Coverage, subjects, entities, terms, regions, claims, relations | 10 to 13 |
| 20 | `access` | object | R | Visibility and allowed uses | 15.1 |
| 21 | `ingestion` | object | R | Disposition and body role | 15.4 |
| 22 | `profiles` | array | | Versioned profile declarations | 6 |
| 23 | `profile_data` | object | | Profile payloads keyed by profile key | 6 |
| 24 | `bindings` | array | | Sidecar targets | 17.6 |
| 25 | `extensions` | object | | `owner -> {schema, data}` | 4.3 |

Every object is closed: an unknown field at any depth is `E_SCHEMA`, and `null` is never allowed (D5). The only open values are `extensions.<owner>.data`, a claim's `object.value`, and `profile_data` payloads, which their profile schema validates.

### Required members of the required objects

| Object | Required | Optional |
| --- | --- | --- |
| `classification` | `category`, `type`, `role`, `scope`, `tags` | `subtype` (kebab-case) |
| `lifecycle` | `status` | `reason`, `replacement_refs` |
| `authority` | `standing`, `scopes` (each `{target_ref, aspects}`) | `valid_time`, `acceptance_ref`, `owner_ref` |
| `time` | none | `created_at`, `updated_at`, `reviewed_at` (RFC 3339 with offset), `authored_on` (date), `note` |
| `knowledge` | `coverage`, `subjects` | `entities`, `terms`, `regions`, `claims`, `relations` |
| `access` | `visibility`, `allowed_uses` | none |
| `ingestion` | `disposition`, `body_role` | `include_regions`, `exclude_regions`, `atomic_regions`, `requires` |

### Records inside `knowledge`

| Record | Required members | SPEC |
| --- | --- | --- |
| Entity | `ref` (Somnus URN), `label`, `kind` | 10.2 |
| Term | `id`, `label`, `definition`, `entity_refs`, `valid_time` | 10.3 |
| Region | `id`, `kind`, `selector` | 13.1 |
| Claim | `id`, `subject_ref`, `predicate`, `object`, `statement`, `kind`, `assessment`, `valid_time`, `region_ref` | 11 |
| Relation | `id`, `subject`, `predicate`, `object`, `assessment`, `valid_time` | 12 |

Region selectors are tagged by `kind`: `marker`, `tex-label`, `symbol`, `json-pointer`, `heading`, or `line-range` (SPEC 13.2).

### Formats

Patterns are defined at the top of `src/somnus/model/schema.py`. Timestamps are `YYYY-MM-DDTHH:MM:SS[.fff](Z|+HH:MM)`; dates are `YYYY-MM-DD`; local IDs match `[a-z][a-z0-9_]*(-[a-z0-9_]+)*`; references may be Somnus URNs (`artifact`, `entity`, `actor`, `concept`, `example`), `doi:10.*`, `http(s)://` URLs, or foreign URNs. Vocabularies live in `src/somnus/model/vocab.py`; `somnus schema FIELD` prints them for any field.

## Registry

One SQLite database at `$SOMNUS_HOME/somnus.db`, schema version 2 (`PRAGMA user_version`, `DB_USER_VERSION` in `src/somnus/__init__.py`). No column stores JSON; headers are stored as canonical restricted-YAML text (D4). Package 2.1.0 adds the optional derived FTS5 index without changing core metadata 2.0.0 (D19 in `DECISIONS.md`).

### Tables

| Table | Purpose | Key columns |
| --- | --- | --- |
| `roots` | Registered filesystem roots | `id` PK, `path` unique, `added_at`, `last_scan_at` |
| `artifacts` | One row per artifact ID, reflecting its highest observed revision | `id` PK, `title`, `type`, `category`, `role`, `scope`, `status`, `standing`, `visibility`, `current_revision`, `first_seen_at`, `last_seen_at` |
| `revisions` | Immutable observed revision states | PK `(artifact_id, revision)`, `header_yaml`, `payload_digest`, `body_digest`, `observed_at` |
| `locations` | Where each artifact was observed | `id` PK, unique `(root_id, rel_path)`, `artifact_id`, `revision`, `carrier`, `file_mtime`, `file_size`, digests, `present` (0 or 1) |
| `tags` | Classification tags of the current revision | PK `(artifact_id, tag)` |
| `regions` | Region records per revision | PK `(artifact_id, revision, region_id)`, `kind`, `selector_kind`, `title`, `standing` |
| `relations` | Qualified relations per revision | PK `(artifact_id, revision, relation_id)`, `subject_ref`, `predicate`, `object_ref`, `object_revision`, `assessment`, `time_basis`, `valid_from`, `valid_until`, `known_predicate` |
| `entities` | Declared entities per revision | PK `(artifact_id, revision, ref)`, `label`, `kind` |
| `claims` | Typed claims per revision | PK `(artifact_id, revision, claim_id)`, `subject_ref`, `predicate`, `kind`, `assessment`, `statement`, `region_ref`, `object_ref` |
| `conflicts` | Revision, duplicate-ID, authority, and identity conflicts | `id` PK, `kind` (checked), `conflict_key`, `artifact_id`, `revision`, `path`, `detail`, `state` (`open` or `resolved`), `opened_at`, `resolved_at` |
| `events` | Append-only action ledger | `id` autoincrement PK, `at`, `actor`, `action`, `artifact_id`, `revision`, `path`, `detail` |
| `search` | Derived FTS5 text of present locations; available when SQLite supports FTS5 | `rowid = locations.id`, `path`, `title`, `summary`, space-separated `tags`, `body` |

`src/somnus/db/search.sql` configures Porter stemming over `unicode61` tokens with diacritic removal. `searchable_body()` in `src/somnus/db/store.py` uses text outside the envelope, or a UTF-8 sidecar host, with a 1,000,000-character body limit. These rows reflect the last observation, even when a revision conflict leaves the trusted artifact state unchanged. They never feed validation or authority. An incremental scan fills missing rows; disappearance removes the derived row without deleting the location or revision history.

`regions`, `relations`, `entities`, and `claims` reference `revisions(artifact_id, revision)`, so knowledge records are tied to the exact revision they came from. Indexes: `locations_artifact` on `locations(artifact_id)`, `relations_object` on `relations(object_ref)`, and the partial unique index `conflicts_one_open` on `conflicts(kind, conflict_key) WHERE state = 'open'`, which allows at most one open conflict per key.

The triggers `events_no_update` and `events_no_delete` abort any `UPDATE` or `DELETE` on `events` with `events are append-only`.

### Views

| View | Contents |
| --- | --- |
| `docs` | Present artifacts joined to their locations and roots: `id`, `title`, `type`, `status`, `standing`, `revision` (current), `file_revision`, `carrier`, `path` (root path joined with `rel_path`) |
| `open_conflicts` | Conflicts with `state = 'open'` |
| `history` | All events, newest first |

`somnus q --docs`, `--conflicts`, and `--history` query these views; `somnus q --tables` lists tables and views while hiding SQLite internals and FTS5 shadow tables (`src/somnus/commands/query.py`). `somnus q --text` searches `search`, joining present locations and artifacts for ranked excerpts. See [registry](../systems/registry.md) for indexing semantics and [querying](../features/querying.md) for examples.

### Digests

`payload_digest` is SHA-256 of the canonical YAML of the `somnus` payload. `body_digest` is SHA-256 of the UTF-8 bytes outside the envelope after normalizing line endings to LF (SPEC 18.3). A change to either canonical form changes stored digests; see [pitfalls](../background/pitfalls.md).
