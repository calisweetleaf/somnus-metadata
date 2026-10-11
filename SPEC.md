---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a"
  revision: 1
  title: "Somnus Metadata System: Normative Specification"
  summary: "The single normative contract for Somnus artifact metadata, carriers, regions, validation, and the global registry."
  classification:
    category: "engineering"
    type: "specification"
    role: "normative"
    scope: "ecosystem"
    tags: ["somnus", "metadata", "specification", "registry"]
  lifecycle:
    status: "active"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a"
        aspects: ["content", "semantic-model", "ingestion"]
  time:
    created_at: "2026-10-11T10:48:59+00:00"
    authored_on: "2026-10-11"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:concept:metadata-standard"]
    entities:
      - ref: "urn:somnus:concept:metadata-standard"
        label: "Somnus Metadata Standard"
        kind: "concept"
        description: "The semantic metadata contract for portable Somnus artifacts."
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason", "quote"]
  ingestion:
    disposition: "canonical-candidate"
    body_role: "specification"
---

# Somnus Metadata System — Normative Specification

**Schema release:** `somnus://metadata/core/2.0.0`
**Reference implementation:** the `somnus` Python package in `src/somnus/`
**Decisions:** [DECISIONS.md](DECISIONS.md) (D1–D15)

This document is the only normative statement of the Somnus metadata standard.
It merges the semantic model of the v2 proposal
(`archive/v2-proposal/SOMNUS_FRONTMATTER_SPEC_v2.md`) with the concrete
profiles of the v0.1 draft (`archive/v0.1/`). Archived documents are lineage
only and MUST NOT be cited as active requirements.

**MUST**, **SHOULD**, and **MAY** carry their RFC 2119 meanings. A requirement
that the reference implementation enforces is marked with its diagnostic code
in brackets, for example `[E_SCHEMA]`.

## 1. Scope and boundary

The standard gives every artifact (a document, source file, configuration,
dataset, or binary) a stable identity, a classification, a lifecycle, scoped
authority, explicit usage permissions, and optional structured knowledge
(entities, terms, regions, claims, relations).

| Layer | Owns | Does not infer |
| --- | --- | --- |
| Artifact header | Identity, classification, declared scope, usage intent | Truth of the body |
| Regions | Stable addressable boundaries inside a body | Authority from styling |
| Knowledge records | Entities, terms, claims, relations, evidence pointers | Identity from matching names |
| Registry (`somnus.db`) | Observation, revision history, conflicts, events | Canon from a self-written field |
| Consumers | Selection for a query and an allowed use | Permission to execute content |

Out of scope: content hashing as an integrity guarantee, signatures, forensic
provenance, and network resolution. Digests stored in the registry
(Section 18) are an equivalence method, not a tamper-evidence mechanism.

## 2. Semantic model

| Object | Identity |
| --- | --- |
| Artifact | Persistent artifact URN (`somnus.id`) |
| Artifact revision | Artifact URN plus positive integer `somnus.revision` |
| Representation | Locator recorded in `representations` or the registry `locations` table |
| Entity | Persistent entity reference (`urn:somnus:entity:…`, `urn:somnus:concept:…`, …) |
| Region | Artifact URN plus local region ID |
| Claim | Artifact URN plus revision plus local claim ID |

A faithful export (Markdown to PDF) shares artifact ID and revision. An
independent edit, fork, or semantic adaptation gets a new artifact ID and a
`derived_from` relation. A byte-identical mirror is the same artifact at a
second location.

## 3. Identity, revision, and references

### 3.1 Identifiers

| Form | Pattern |
| --- | --- |
| Artifact URN | `^urn:somnus:artifact:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` |
| Example URN (fixtures only) | `^urn:somnus:example:[a-z0-9][a-z0-9-]*$` |
| Somnus URN (any kind) | `^urn:somnus:(artifact\|entity\|actor\|concept\|example):[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| External reference | `doi:10.…`, `https://…`, `http://…`, or another `urn:<nid>:…` |
| Local ID | `^[a-z][a-z0-9_]*(?:-[a-z0-9_]+)*$` |

- `somnus.id` MUST be an artifact URN or an example URN `[E_SCHEMA]`. UUID
  hex digits MUST be lowercase.
- New artifacts MUST be minted with UUIDv7 (RFC 9562). Imported identities
  of any UUID version (notably UUIDv4) are valid and MUST NOT be reminted.
- The UUIDv7 timestamp is the moment of ID generation. It MUST NOT be
  compared with, copied into, or used as a substitute for `time.created_at`
  or any other authored date (D3).
- `urn:somnus:example:*` identities are fixtures. The registry refuses to
  index them and never stores example entities.
- A bare legacy UUID resolves to `urn:somnus:artifact:<uuid>`; v0.1
  `urn:somnus:doc:<uuid>` references normalize to the same artifact URN.

### 3.2 Revision

`revision` is a positive integer `[E_SCHEMA]` that increases by one for every
committed authored state that changes the body or semantic metadata. The
`somnus` tool increments it automatically on `status`, `bump`, `regions
--sync --write`, `edit` saves, and `migrate --write`. Two different authored
states with the same artifact ID and revision are a revision conflict
`[E_REVISION]`; the registry preserves both and never resolves by arrival
order.

`edition` is an optional human release label and never replaces `revision`.

### 3.3 Reference object

A reference object has required `ref` and optional `revision` (positive
integer), `region` (local ID), `claim` (local ID), and `locator_hint` (string).
A path is a hint, never identity. References used as evidence SHOULD pin a
revision.

```yaml
ref: "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a"
revision: 1
region: "r-lifecycle"
```

Resolution failures remain explicit; a consumer MUST NOT substitute a title
match.

## 4. Namespace and payload (D1)

All standardized metadata resides under one top-level `somnus` mapping. In
Markdown frontmatter, other host keys MAY coexist beside `somnus`. They belong
to the host, are preserved byte-for-byte, and are never validated or used to
override Somnus values.

Each representation carries exactly one authoritative envelope, or one
sidecar binding (Section 17.6). Two envelopes, or an envelope plus a sidecar,
are an error `[E_ENVELOPE]`.

### 4.1 Core fields

Fields appear in this canonical order. Required fields are marked **R**.

| # | Field | Type | R | Contract |
| --- | --- | --- | --- | --- |
| 1 | `schema` | string | R | Exactly `somnus://metadata/core/2.0.0` |
| 2 | `id` | string | R | Artifact or example URN |
| 3 | `revision` | integer | R | ≥ 1 |
| 4 | `title` | string | R | Nonempty |
| 5 | `summary` | string | | Nonempty |
| 6 | `purpose` | string | | Nonempty |
| 7 | `language` | string | | BCP 47 tag, `^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$` |
| 8 | `edition` | string | | Human release label |
| 9 | `classification` | object | R | Section 5 |
| 10 | `lifecycle` | object | R | Section 7 |
| 11 | `authority` | object | R | Section 8 |
| 12 | `time` | object | R | Section 9; may be `{}` |
| 13 | `names` | object | | Section 10.1 |
| 14 | `context` | object | | Section 5.3 |
| 15 | `ownership` | object | | Section 15.2 |
| 16 | `locations` | array | | Section 15.3 |
| 17 | `representations` | array | | Section 15.3 |
| 18 | `content` | object | | Section 14 |
| 19 | `knowledge` | object | R | Sections 10–13 |
| 20 | `access` | object | R | Section 15.1 |
| 21 | `ingestion` | object | R | Section 15.4 |
| 22 | `profiles` | array | | Section 6 |
| 23 | `profile_data` | object | | Section 6 |
| 24 | `bindings` | array | | Section 17.6 (sidecars) |
| 25 | `extensions` | object | | Section 4.3 |

### 4.2 Presence semantics (D5)

- An omitted field means unspecified. An empty array means no entries are
  declared. `{}` means an object with no declared members.
- `null` is forbidden everywhere `[E_YAML]`.
- Unknown fields at any depth of the standardized payload are errors
  `[E_SCHEMA]`. Objects are closed. The only open locations are
  `extensions.<owner>.data`, claim `object.value`, and profile payloads
  validated by their own profile schema.
- Templates and tools MUST NOT invent dates, actors, licenses, repository
  addresses, measurements, acceptance records, or evidence.

### 4.3 Extensions

`extensions` maps an owner namespace
(`^[a-z][a-z0-9]*(?:[-.][a-z0-9]+)*$`) to `{schema, data}`. `schema` is a
nonempty URI string; `data` is any JSON-compatible value. Extensions are
preserved losslessly by every tool, are stored in the registry only as part
of the revision's header text, and never feed trusted semantic tables.

## 5. Classification and context

### 5.1 Controlled vocabularies

| Field | Values |
| --- | --- |
| `category` | `research`, `engineering`, `operations`, `governance`, `context`, `archive` |
| `type` | `whitepaper`, `specification`, `architecture-record`, `report`, `task`, `plan`, `notepad`, `benchmark`, `test-result`, `decision-record`, `runbook`, `index`, `state`, `memory`, `source-code`, `configuration`, `dataset`, `equation-set`, `conversation`, `asset` |
| `role` | `normative`, `informative`, `working`, `exploratory`, `historical` |
| `scope` | `ecosystem`, `fleet`, `repository`, `subsystem`, `module`, `component`, `artifact` |

`classification` fields: `category` R, `type` R, `subtype` (kebab-case
`^[a-z0-9]+(?:-[a-z0-9]+)*$`), `role` R, `scope` R, `tags` R (array of unique
nonempty strings; Unicode allowed; no routing semantics).

### 5.2 Registered auxiliary vocabularies

| Registry | Values |
| --- | --- |
| Authority aspects | `content`, `semantic-model`, `terminology`, `interface`, `behavior`, `configuration`, `performance`, `embedding`, `ingestion`, `migration`, `governance`, `process`, `security` |
| Constraint languages | `semver-range@1`, `pep440-specifier@1`, `path-glob@1`, `platform-tag@1` |
| Ingestion capabilities | `somnus-adapter-markdown@1`, `somnus-adapter-html-comment@1`, `somnus-adapter-hash-comment@1`, `somnus-adapter-tex@1`, `somnus-adapter-slash-comment@1`, `somnus-adapter-sql-comment@1`, `somnus-adapter-block-comment@1`, `somnus-adapter-sidecar@1` |

Adding a value to any vocabulary is a schema release, not free text.

### 5.3 Context

`context` has optional arrays `project_refs`, `system_refs`, `division_refs`,
`repository_refs` (reference objects), and `release_constraints`,
`platform_constraints` (constraint objects).

A **constraint object** is `{target_ref, language, expression}`, all
required nonempty strings. A language outside Section 5.2 is preserved but
unresolved. At semantic level it is `[E_REFERENCE]`. Consumers MUST NOT guess
a language.

## 6. Profiles

`profiles` is an array of `{schema, key}`. The keys of `profile_data` MUST
exactly equal the declared profile keys `[E_SCHEMA]`. Duplicate keys or
duplicate schema URIs are errors. An unknown profile schema URI is
`[E_SCHEMA]`: the source is retained, semantic acceptance is refused.

Profile keys match `^[a-z][a-z0-9_]*$`. Profiles may add requirements; they
never redefine core meanings.

### 6.1 `somnus://metadata/profile/specification/1.0.0`

Lineage: v0.1 `somnus://profiles/engineering/specification/v1`.

| Field | Type | R | Contract |
| --- | --- | --- | --- |
| `target_refs` | array of reference objects | R | At least one; what the specification governs |
| `acceptance_criteria` | array of strings | R | At least one nonempty criterion |
| `normative_region_refs` | array of local IDs | | Each MUST name a region in `knowledge.regions` `[E_REGION]` |
| `compliance_level` | string | | `mandatory`, `recommended`, `optional` |
| `verification_refs` | array of reference objects | | Test suites or reports that verify the criteria |

### 6.2 `somnus://metadata/profile/benchmark/1.0.0`

Lineage: v0.1 `somnus://profiles/engineering/benchmark/v1`.

| Field | Type | R | Contract |
| --- | --- | --- | --- |
| `workload` | string | R | Nonempty workload description |
| `environment` | object | R | `cpu` R, `memory_gb` R (number ≥ 0), `os` R, `accelerator`, `runtime` |
| `measurements` | array | R | At least one `{name R, value R (number), unit R, repetitions (integer ≥ 1), uncertainty (number ≥ 0)}` |
| `baseline_ref` | reference object | | Baseline benchmark artifact |
| `conditions` | array of strings | | Explicit measurement conditions |

## 7. Lifecycle (state machine)

`lifecycle.status` is one of `draft`, `proposed`, `provisional`, `active`,
`experimental`, `superseded`, `deprecated`, `historical`, `archived`,
`rejected`. Optional `reason` (nonempty string) and `replacement_refs` (array
of reference objects).

### 7.1 Transitions

| From | Permitted targets |
| --- | --- |
| `draft` | `proposed`, `experimental`, `rejected`, `archived`* |
| `proposed` | `provisional`, `active`, `rejected`, `experimental`, `superseded`, `archived`* |
| `provisional` | `active`, `experimental`, `rejected`, `superseded`, `deprecated`, `archived`* |
| `experimental` | `draft`, `proposed`, `provisional`, `rejected`, `deprecated`, `historical`, `archived`* |
| `active` | `superseded`, `deprecated`, `historical` |
| `superseded` | `historical`, `active`† |
| `deprecated` | `historical`, `archived` |
| `historical` | `archived`, `active`† |
| `rejected` | `archived` |
| `archived` | `active`† |

\* Abandonment. Requires `reason` `[E_LIFECYCLE]`.
† Reactivation. Requires `reason` and renewed authority review. The tool
resets `authority.standing` from `accepted` to `candidate` and drops
`valid_time`/`acceptance_ref` `[E_LIFECYCLE]`.

Any other transition is `[E_LIFECYCLE]`. Every transition creates a new
revision. A transition is not a deployment claim.

### 7.2 Static rules

- `superseded` requires at least one `replacement_refs` entry `[E_SCHEMA]`.
  At semantic level each replacement MUST resolve `[E_REFERENCE]`.
- `archived` does not waive parsing, identity, or structural checks.

## 8. Authority

`authority` fields: `standing` R (`unasserted`, `candidate`, `accepted`,
`retired`, `rejected`), `scopes` R (array), `valid_time`, `acceptance_ref`
(reference object), `owner_ref` (reference object).

A **scope** is `{target_ref R, aspects R, conditions}`. `aspects` is a
nonempty array of unique registered aspects (Section 5.2). `conditions` is an
array of constraint objects.

- `scopes` MAY be empty only when `standing` is `unasserted` `[E_AUTHORITY]`.
- `standing: accepted` requires `valid_time` and `acceptance_ref`
  `[E_AUTHORITY]`.
- At canon level, `acceptance_ref` MUST resolve to an indexed artifact of
  type `decision-record` with status `active` `[E_AUTHORITY]`.
- Two accepted artifacts that share a scope `target_ref` and an aspect, with
  overlapping valid intervals, are an authority conflict `[E_AUTHORITY]`.
  Recency and source order are never tie-breakers.
- A `normative` role describes intent; it never grants acceptance.
- Tools default new artifacts to `standing: candidate` with a self-scope
  (`target_ref` equal to the artifact's own ID, aspects `["content"]`).

### 8.1 Current canon

An artifact is current canon for a query only when it passes canon-level
validation (Section 19), its status is `active` or `provisional`, its
`allowed_uses` permit the operation, and no open registry conflict names it.

## 9. Time

Three clocks stay separate:

| Clock | Location |
| --- | --- |
| Authorship | `somnus.time` |
| Applicability | `valid_time` on authority, claims, relations, terms, aliases, regions |
| Observation | Registry `observed_at` / `first_seen_at` / `last_seen_at` |

`time` fields: `created_at`, `updated_at`, `reviewed_at` (RFC 3339 timestamps
with an explicit offset:
`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$`, and a real
calendar instant), `authored_on` (date `YYYY-MM-DD`), `note` (string). All
are optional; `time: {}` declares nothing.

- `updated_at` MUST NOT precede `created_at` `[E_TEMPORAL]`.
- Dates are never converted to fabricated midnight instants.

A **valid_time** object is `{basis R, from, until, note}`:

| `basis` | `from` | `until` |
| --- | --- | --- |
| `bounded` | required | required, strictly after `from` |
| `open` | required | forbidden |
| `timeless` | forbidden | forbidden |
| `unknown` | forbidden | forbidden |

Violations are `[E_TEMPORAL]`. Intervals are half-open `[from, until)`.

## 10. Names, entities, and terms

### 10.1 Artifact names

`names` fields: `slug` (`^[a-z0-9]+(?:-[a-z0-9]+)*$`), `aliases` (array of
`{id R, label R, kind R, valid_time R}`; kind is `former-title`,
`short-name`, `acronym`, `spelling`, or `translation`). A slug never resolves
identity.

### 10.2 Entities

`knowledge.entities` entries: `ref` R (Somnus URN), `label` R, `kind` R
(`project`, `system`, `component`, `agent`, `agent-role`, `framework`,
`concept`, `organization`, `dataset`, `model`, `tool`), `description`,
`aliases` (array of `{id, label, kind, valid_time}` with kind `former-name`,
`short-name`, `acronym`, `spelling`, `translation`), `external_refs` (array
of strings).

An entity declaration binds a reference to a label for this source only.
Matching labels across artifacts never merge entities. Only an explicit
registry decision merges them, and `distinct_from` blocks automatic merging.

### 10.3 Terms

`knowledge.terms` entries: `id` R, `label` R, `definition` R, `entity_refs` R
(array of strings), `valid_time` R, `excluded_refs` (array of strings),
`context_refs` (array of reference objects), `region_ref` (local ID that
MUST exist `[E_REGION]`).

## 11. Claims

`knowledge.coverage` is `artifact`, `selected-claims`, or
`structured-claims`. `knowledge.subjects` is a required array of reference
strings.

A **claim** has: `id` R, `subject_ref` R, `predicate` R (`definition`,
`has_role`, `has_property`, `requires`, `predicts`, `measures`) `[E_SCHEMA]`,
`object` R, `statement` R, `kind` R (`observation`, `definition`,
`requirement`, `hypothesis`, `inference`, `prediction`, `measurement`),
`assessment` R (`unassessed`, `supported`, `contested`, `refuted`,
`withdrawn`), `valid_time` R, `region_ref` R, and optional `evidence_refs`,
`assumption_refs`, `context_refs` (arrays of reference objects),
`conditions` (constraint objects), `confidence` (`{value R in [0,1], method R}`).

- `object` contains exactly one of `ref` (with optional reference-object
  fields) or `value` (any JSON-compatible value) `[E_SCHEMA]`.
- `supported` requires at least one `evidence_refs` entry `[E_SCHEMA]`.
- `region_ref` MUST name a declared region `[E_REGION]`. If a region lists
  `claim_ids`, each MUST exist, and each listed claim's `region_ref` MUST
  equal that region `[E_REGION]`.
- Claim kinds are preserved verbatim through every export. A hypothesis in
  an accepted artifact is still a hypothesis.

## 12. Relations

`knowledge.relations` entries: `id` R, `subject` R (reference object),
`predicate` R, `object` R (reference object), `assessment` R, `valid_time` R,
and optional `region_ref`, `evidence_refs`, `conditions`, `note`.

| Predicate | Inverse view | Cycle policy |
| --- | --- | --- |
| `supersedes` | `superseded_by` | acyclic `[E_GRAPH]` |
| `derived_from` | `has_derivative` | acyclic `[E_GRAPH]` |
| `describes` | `described_by` | — |
| `implements` | `implemented_by` | — |
| `depends_on` | `required_by` | cycles allowed |
| `part_of` | `has_part` | acyclic `[E_GRAPH]` |
| `cites` | `cited_by` | — |
| `supports` | `supported_by` | — |
| `contradicts` | `contradicts` | symmetric |
| `renamed_to` | `renamed_from` | — |
| `role_expanded_to` | `role_expanded_from` | — |
| `specializes` | `generalizes` | — |
| `equivalent_to` | `equivalent_to` | candidate only |
| `distinct_from` | `distinct_from` | blocks merging |

- An unknown predicate is preserved, is reported as a warning
  (`W_PREDICATE`), and is never used to derive edges.
- `supported` requires evidence `[E_SCHEMA]`.
- A self-edge on an acyclic predicate is `[E_GRAPH]`. Acyclicity is checked
  within the document and, during indexing, across the registry.
- Inverse edges are registry views. No tool rewrites another artifact to add
  an inverse.

## 13. Regions (D2)

### 13.1 Registry

`knowledge.regions` entries: `id` R, `kind` R (`section`, `definition`,
`invariant`, `decision`, `hypothesis`, `evidence`, `equation`, `table`,
`code`, `example`, `archive`), `selector` R, and optional `title`,
`claim_ids`, `authority` (`{standing}`), `access` (`{visibility,
allowed_uses}`), `valid_time`, `context_refs`.

A region may narrow, never widen, its document's authority and access
`[E_AUTHORITY]`/`[E_POLICY]`: a region cannot be `accepted` unless the
document is accepted, its visibility cannot be more open than the
document's (`operator-only` < `internal` < `public`), and its
`allowed_uses` must be a subset of the document's.

### 13.2 Selectors

| `kind` | Fields (all required) | Resolution |
| --- | --- | --- |
| `marker` | `name` | Exactly one paired marker range |
| `tex-label` | `name` | Exactly one `\label{name}` outside TeX comments |
| `symbol` | `name`, `language` | Python: exactly one top-level or nested `def`/`class`; other languages unresolved |
| `json-pointer` | `pointer` | RFC 6901 pointer resolves in the bound JSON target |
| `heading` | `text`, `occurrence` (≥ 1) | The n-th Markdown ATX heading whose text equals `text` |
| `line-range` | `from`, `until`, `revision` (all ≥ 1) | `from < until ≤ line count + 1`, `revision` equals the current revision |

Selector objects are closed per kind `[E_SCHEMA]`. Marker selectors are
resolved at core level; every other kind is resolved at semantic level
`[E_REGION]`.

### 13.3 Marker syntax

Markdown and HTML hosts use standalone comment lines:

```markdown
<!-- somnus:region:begin r-lifecycle -->

## Lifecycle

<!-- somnus:region:end r-lifecycle -->
```

Line-comment hosts use the host prefix: `# somnus:region:begin r-config`,
`% somnus:region:begin r-equation`, `// …`, `-- …`. Block-comment hosts use
`/* somnus:region:begin r-x */`.

- Markers occupy their own line. Markdown markers SHOULD be separated from
  body blocks by blank lines (`W_REGION_SPACING`).
- Pairing is stack-based: nesting is allowed; crossing, unmatched,
  unclosed, or duplicated markers are `[E_REGION]`.
- Markers inside fenced code (backtick or tilde fences of any length ≥ 3),
  indented code blocks, or the metadata envelope are inert.
- A registered marker region with no body markers is `[E_REGION]`. A body
  marker with no registry entry is a warning (`W_REGION_UNREGISTERED`);
  `somnus regions --sync` registers it.
- The markers carry identity only. Attributes live in the registry.

## 14. Content and mathematics

`content` fields (all optional):

- `math`: `{source_format R (tex, mathml, unicode, raster, mixed),
  delimiters R (array of strings), macro_refs R (array of locator strings),
  equation_region_ids R (array of local IDs that MUST exist `[E_REGION]`)}`.
- `resources`: array of `{ref R (locator string), media_type R
  (`^[a-z]+/[A-Za-z0-9.+-]+$`), role R (macro-source, figure, table-source,
  attachment, rendered-output), required R (boolean)}`. At semantic level, a
  `required: true` resource whose `ref` is a relative path that does not exist
  relative to the artifact is `[E_EXTRACTION]`.
- `extraction`: `{state R (complete, partial, unverified), limitations R
  (array of strings)}`. A declared `complete` state with a missing required
  resource is `[E_EXTRACTION]`.

## 15. Access, ownership, locations, ingestion

### 15.1 Access

`access`: `visibility` R (`operator-only`, `internal`, `public`),
`allowed_uses` R (unique values from `archive`, `search`, `reason`, `quote`,
`export`, `training`, `execute`). An omitted use is not authorized. `execute`
classifies content; it never authorizes running it.

### 15.2 Ownership

`ownership`: `owner_ref`, `maintainer_refs`, `rights` (`{status R
(specified, unspecified, restricted), license_expression}`).
`license_expression` is required when status is `specified`, and forbidden
otherwise `[E_SCHEMA]`.

### 15.3 Locations and representations

`locations` entries: `kind` R (`repository-path`, `filesystem-path`,
`library-item`, `uri`), `locator` R, `role` R (`origin`, `primary`,
`mirror`, `historical`), `repository_ref`, `observed_on` (date).

`representations` entries: `locator` R, `media_type` R, `role` R (`source`,
`rendered`, `translation`, `projection`), `source_revision` (≥ 1),
`limitations` (array of strings).

### 15.4 Ingestion

`ingestion`: `disposition` R (`candidate`, `archive-only`, `excluded`,
`canonical-candidate`), `body_role` R (`narrative`, `specification`,
`instruction`, `configuration`, `source`, `conversation`, `dataset`,
`mixed`), and optional `include_regions`, `exclude_regions`, `atomic_regions`
(local IDs that MUST exist `[E_REGION]`) and `requires` (capability names).
An unregistered capability blocks semantic acceptance `[E_POLICY]`.
Exclusion wins over inclusion. `canonical-candidate` requests review; it is
not canon.

## 16. Serialization (D7)

### 16.1 Restricted YAML subset

The payload is a restricted subset of YAML 1.2.2:

- Two-space indentation of nested blocks, string mapping keys, and block or
  flow sequences and mappings.
- Strings MUST be double-quoted or single-quoted. Unquoted plain scalars are
  limited to integers (`-?(0|[1-9][0-9]*)`), finite decimals, and `true` /
  `false` `[E_YAML]`.
- Block scalars `|` and `>` with optional `-`/`+` chomping are accepted on
  input. The canonical serializer never emits them.
- `#` comments and blank lines are accepted and ignored.
- Forbidden `[E_YAML]`: tabs in indentation; `null`, `~`, or an empty value
  where a scalar is expected; anchors (`&`), aliases (`*`), merge keys
  (`<<`), tags (`!`), directives (`%`), document markers (`---`, `...`)
  inside the payload, duplicate keys at any depth, non-string keys,
  integers outside ±(2^53 − 1), and non-finite numbers.

Quoted `"NO"`, `"on"`, `"1.0"`, and `"2026-10-11"` are always strings.

### 16.2 Canonical form

The canonical serializer, which every `somnus` write uses:

1. Emits object members in the schema-declared order (Section 4.1 for the
   root; Section 13 order `coverage, subjects, entities, terms, regions,
   claims, relations` for `knowledge`; field-table order elsewhere). Members
   of open values (extension data, claim values) keep their source order.
2. Double-quotes every string. It escapes `\`, `"`, and control characters
   (`\n`, `\t`, `\r`, other controls as `\uXXXX`) and keeps other Unicode
   literal.
3. Emits a sequence of scalars in flow form (`["a", "b"]`) when the whole
   line fits in 88 columns, and otherwise one `- ` item per line. Sequences
   of mappings are block form. Empty containers are `[]` and `{}`.
4. Indents nested blocks by two spaces and sequence items by two spaces
   beneath their key.
5. Escapes carrier-forbidden sequences inside strings: in HTML/XML comment
   carriers, every `-` that follows `-` becomes `\u002d`. In block-comment
   carriers, every `/` that follows `*` becomes `\u002f`.

For canonical input `s`, `dumps(loads(s)) == s` holds byte-for-byte.

### 16.3 Encoding

UTF-8. A leading BOM is accepted on input and never emitted. The tool
preserves the file's existing line ending (LF or CRLF) and writes new files
with LF. Writes are atomic: write to a temporary file in the same directory,
then `os.replace`. Every header write verifies that the bytes outside the
envelope are unchanged. The only exception is the explicit directive
conversion in `migrate`.

## 17. Carriers

A carrier locates and strips the envelope. The YAML payload is identical in
every carrier.

| Host extensions | Carrier | Envelope |
| --- | --- | --- |
| `.md .markdown .mdx` | `markdown` | Frontmatter `---` … `---` (default) or HTML comment envelope |
| `.py .pyw .sh .bash .zsh .ps1 .psm1 .psd1 .toml .yaml .yml .r .R` | `hash` | `# ` prefixed lines |
| `.tex .sty .cls .ltx` | `tex` | `% ` prefixed lines |
| `.js .mjs .cjs .jsx .ts .tsx .rs .c .h .cc .cpp .hpp .go .java .kt .swift .cs` | `slash` | `// ` prefixed lines |
| `.sql` | `sql` | `-- ` prefixed lines |
| `.css .scss .less` | `css` | `/* … */` block |
| `.html .htm .xhtml .xml .svg` | `xml` | `<!-- … -->` block |
| anything else (`.json`, `.pdf`, `.png`, `.ipynb`, …) | `sidecar` | `<file>.somnus.yaml` |

Files named `*.somnus.yaml` are always sidecars, never hash carriers.

### 17.1 Markdown frontmatter

The first line (after an optional BOM) is exactly `---`. The closing
delimiter is the next line that is exactly `---`. An unclosed opener is
`[E_ENVELOPE]`. The frontmatter is split into top-level keys (column 0).
Only the `somnus:` block is parsed by the restricted parser. Other host keys
are preserved verbatim. A second `somnus:` key is `[E_ENVELOPE]`.

### 17.2 HTML comment envelope

```markdown
<!-- somnus:metadata:v2
somnus:
  schema: "somnus://metadata/core/2.0.0"
somnus:end -->
```

The opener and closer lines are exact. In Markdown, the envelope is
recognized only outside fenced or indented code, and only one is allowed.
The payload MUST NOT contain `--` `[E_ENVELOPE]`.

### 17.3 Line-comment carriers

```toml
# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
# somnus:end
```

Each payload line starts with the exact prefix (`# `, `% `, `// `, `-- `).
A line that equals the prefix without its trailing space is a blank payload
line. Exactly one prefix is stripped; indentation after it is retained. Any
other line inside the envelope is `[E_ENVELOPE]`.

The envelope MUST appear in the leading comment area: after mandatory
preamble lines, among blank lines and comments, and before the first host
code line. Text that looks like an envelope after code begins (string
literals, examples) is inert.

### 17.4 Block-comment carriers

CSS uses `/* somnus:metadata:v2` … `somnus:end */`, and the payload MUST NOT
contain `*/`. XML, HTML, and SVG use `<!-- somnus:metadata:v2` …
`somnus:end -->`, and the payload MUST NOT contain `--` `[E_ENVELOPE]`.

### 17.5 Mandatory preambles

| Host | Preserved before the envelope |
| --- | --- |
| Python | Line-1 shebang; encoding cookie (`coding[:=]`) on line 1, or on line 2 when line 1 is a comment |
| Shell, R, JS/TS | Line-1 shebang (`#!`) |
| PowerShell | Line-1 shebang and leading `#Requires` lines |
| TeX | Leading `% !TeX …` magic comments (case-insensitive) |
| CSS | Leading `@charset "…";` |
| XML/HTML/SVG | Leading `<?xml …?>` declaration and `<!DOCTYPE …>` |

Inserting at byte 0 regardless of host is forbidden. When the tool cannot
place the envelope safely, the operation is refused `[E_HOST]`.

### 17.6 Sidecars

The sidecar for `state.json` is `state.json.somnus.yaml`. It contains the
plain restricted-YAML payload (a top-level `somnus:` mapping, with no
delimiters). The payload MUST include `bindings` with exactly one
`role: "primary"` binding whose `required` is `true` and whose `target`
(a relative locator string or a reference object) resolves relative to the
sidecar's directory `[E_ENVELOPE]`. Binding roles are `primary`,
`attachment`, and `representation`. A host file that has both an embedded
envelope and a sidecar is `[E_ENVELOPE]`.

## 18. Global registry (D4)

### 18.1 Location and policy

The registry is one SQLite database at `$SOMNUS_HOME/somnus.db` (default
`~/.somnus/somnus.db`). Configuration lives at `$SOMNUS_HOME/config.toml`.

- **Zero JSON.** No table stores JSON. Headers are stored as canonical
  restricted YAML text. Every column is a plain value, and all names are
  plain English.
- WAL journaling, foreign keys on, and `PRAGMA user_version` tracking schema
  migrations. Current version: **1**.
- `somnus q` opens the database read-only (`mode=ro`, `query_only`).
- Every mutating tool action appends one row to `events`. Events are never
  updated or deleted by the tool.

### 18.2 Schema

The authoritative DDL ships as `src/somnus/db/schema.sql`. Tables:

| Table | Purpose |
| --- | --- |
| `roots` | Registered filesystem roots |
| `artifacts` | One row per artifact ID; columns reflect the highest observed revision |
| `revisions` | Immutable observed revision states: canonical `header_yaml`, `payload_digest`, `body_digest` |
| `locations` | Where each artifact was observed (`root_id`, `rel_path`, `carrier`, `file_mtime`, `file_size`, `present`) |
| `tags` | Classification tags of the current revision |
| `regions`, `relations`, `entities`, `claims` | Knowledge records per revision |
| `conflicts` | `revision`, `duplicate-id`, `authority`, `identity` conflicts with open/resolved state |
| `events` | Append-only ledger (`at`, `actor`, `action`, `artifact_id`, `revision`, `path`, `detail`) |

Views: `docs` (present artifacts with path), `open_conflicts`, `history`
(events, newest first).

### 18.3 Indexing semantics

- **Equivalence method.** `payload_digest` is SHA-256 of the canonical YAML
  of the `somnus` payload. `body_digest` is SHA-256 of the UTF-8 bytes
  outside the envelope, after normalizing line endings to LF.
- **Incremental.** A location whose `(file_mtime, file_size)` is unchanged
  is skipped unless `--full` is given.
- **Idempotent.** Re-indexing a revision with identical digests creates no
  new records.
- **Revision conflict.** Same artifact and revision with different digests
  keeps the stored revision, opens a `revision` conflict, and writes the
  candidate's header into the conflict detail. `somnus bump` resolves it.
- **Duplicate ID.** One artifact ID present at two paths with different
  digests opens a `duplicate-id` conflict. Byte-identical mirrors are
  allowed. A conflict resolves automatically when re-indexing no longer
  observes the condition.
- **Identity change.** A path whose artifact ID changed opens an `identity`
  conflict.
- **Authority overlap.** Overlapping accepted authorities (Section 8) open
  an `authority` conflict.
- **Disappearance.** A file missing during a scan is marked `present = 0`.
  This is never a tombstone or a deletion.
- `urn:somnus:example:*` artifacts are not indexed.

## 19. Validation pipeline (D5, D14)

### 19.1 Levels

| Level | Checks |
| --- | --- |
| `carrier` | Envelope location, uniqueness, closure, forbidden sequences, sidecar binding shape |
| `core` | Carrier, plus restricted YAML, closed schema, vocabularies, formats, conditional requirements, intra-document consistency, marker regions |
| `semantic` | Core, plus resolved references (registry and the current check set), non-marker selectors, required resources, profile payloads, constraint languages, capabilities |
| `canon` | Semantic, plus accepted standing, resolved acceptance record, `active`/`provisional` status, and no open conflict |

`somnus check` defaults to `core`. Reference resolution at semantic level
uses the registry when it exists, plus every artifact in the current check
set. External references (`doi:`, `http(s)://`, foreign URNs) count as
resolved-external. Example URNs resolve only when declared in the same
document.

### 19.2 Diagnostics

```
path:line:col: severity CODE field: message
```

`--tsv` emits `path<TAB>line<TAB>col<TAB>severity<TAB>code<TAB>field<TAB>message`
with no header. Lines and columns are 1-based file positions. `field` is the
dotted payload path (`somnus.classification.type`, `somnus.knowledge.claims[0].region_ref`)
or `-`.

| Code | Condition |
| --- | --- |
| `E_ENVELOPE` | Missing, duplicate, unclosed, or malformed envelope or sidecar binding |
| `E_HOST` | Placement would alter host semantics |
| `E_YAML` | Restricted-YAML violation |
| `E_SCHEMA` | Unknown field, wrong type, bad vocabulary value, missing required field, unknown release |
| `E_REFERENCE` | Required reference unresolved |
| `E_REGION` | Region marker or selector failure |
| `E_REVISION` | Conflicting state for one artifact revision |
| `E_AUTHORITY` | Authority rule violation or overlap |
| `E_TEMPORAL` | Invalid time or interval |
| `E_GRAPH` | Forbidden cycle or self-edge |
| `E_EXTRACTION` | Required resource unavailable |
| `E_POLICY` | Usage or capability policy violation |
| `E_LIFECYCLE` | Forbidden transition or missing transition reason |
| `E_IO` | File cannot be read or written |
| `W_*` | Warnings (`W_PREDICATE`, `W_REGION_SPACING`, `W_REGION_UNREGISTERED`, `W_UNMANAGED`, `W_DUPLICATE_TITLE`) |

### 19.3 Exit codes

`0` means success with no errors. `1` means validation errors, refused
operations, or conflicts. `2` means usage, I/O, or environment errors.

## 20. CLI contract

`somnus [--version] [--actor NAME] [--tsv] [--no-color] [--debug] <command>`

| Command | Effect |
| --- | --- |
| `init [--root DIR]…` | Create `$SOMNUS_HOME`, `config.toml`, and the database; register roots |
| `new TYPE TITLE [--dir] [--carrier frontmatter\|html-comment] [--status] [--force]` | Scaffold a conformant Markdown artifact with a UUIDv7, revision 1, and config defaults; refuses title collisions |
| `stamp PATH… [--write] [--type] [--title]` | Infer and inject a header into an unmanaged file; dry-run diff unless `--write` |
| `check [PATH…] [--all] [--level L]` | Run the pipeline and print diagnostics |
| `index [ROOT…] [--full]` | Reconcile roots into the registry |
| `q [SQL] [--docs\|--conflicts\|--history\|--tables] [--limit N]` | Read-only queries in aligned text or TSV |
| `ls [--type] [--status] [--standing] [--tag] [--path-contains]` | List present artifacts |
| `status PATH NEW_STATUS [--reason] [--replacement REF]…` | Validated lifecycle transition (new revision) |
| `bump PATH [--reason]` | New revision; resolves revision conflicts |
| `fork PATH [--out] [--title]` | New UUIDv7, revision 1, `derived_from` the parent revision |
| `regions PATH [--sync] [--write]` | Audit markers against the registry; register unregistered markers |
| `migrate PATH… [--write]` | Upgrade v0.1 documents (Section 22) |
| `stale [--days N]` | Report stale drafts, unreplaced supersessions, missing files, near-duplicate titles, open conflicts |
| `schema [FIELD] [--json-schema] [--out FILE]` | Show field docs or export JSON Schema Draft 2020-12 |
| `brief` | Print a Markdown agent cheat sheet |
| `edit [PATH]` | Terminal UI: document browser, or header editor |

Configuration precedence: CLI flag > nearest parent `.somnus.toml` >
`$SOMNUS_HOME/config.toml` > built-in defaults.

## 21. Conformance fixtures

The implementation is acceptable only when every row holds. Each row maps to
a test in `tests/test_conformance.py`.

| # | Fixture | Expected result |
| --- | --- | --- |
| 1 | Same payload in Markdown, TeX, YAML comments, TOML comments, sidecar | Equal normalized model |
| 2 | YAML/TOML host before and after comment insertion | Identical host data tree |
| 3 | Python encoding cookie and shell shebang | Preserved placement |
| 4 | Duplicate nested mapping key | Parse rejection |
| 5 | Quoted `"NO"`, `"on"`, versions, dates | Strings remain strings |
| 6 | Metadata-looking text in a literal code example | No live envelope or region |
| 7 | Properly nested separate region markers | Valid nested ranges |
| 8 | Crossing or missing region marker | Region error |
| 9 | Imported UUIDv4 artifact with unknown creation date | ID retained; no invented creation time |
| 10 | UUIDv7 mint time differs from known historical creation date | Valid; no date equality enforced |
| 11 | Unknown optional extension | Preserved; excluded from trusted semantics |
| 12 | Unknown exact core or required profile release | Source retained; semantic acceptance refused |
| 13 | Renamed file or faithful PDF representation | Artifact identity retained |
| 14 | Same ID and revision with distinct authored states | Conflict preserved |
| 15 | Two overlapping accepted authorities | No automatic singular canon |
| 16 | Historical alias shared with a new entity | No automatic identity merge |
| 17 | Hypothesis inside accepted research | Still a hypothesis |
| 18 | Missing TeX macro or clipped equation | Partial extraction; no reconstructed fact |
| 19 | Reingestion of the same revision | No duplicate records |
| 20 | Source disappears during a scan | No implicit tombstone |
| 21 | Header permits `reason` but omits `training` | Reasoning permitted; training refused |

## 22. Migration from v0.1

`somnus migrate` converts v0.1 hybrid documents (root `id`, `title`,
`classification`, `lifecycle.is_canonical`, `relations` buckets,
`:::submatter` directives) into this standard. It parses the legacy header
in lenient mode (plain scalars allowed) and then:

1. Pins `schema` to core 2.0.0, wraps the UUID as `urn:somnus:artifact:<uuid>`
   without reminting, and sets `revision: 1`.
2. Maps `title`, `description` → `summary`, and `purpose`; `slug` and
   `aliases` → `names`; `created_at`/`updated_at`/`lifecycle.reviewed_at`
   → `time` with precision preserved.
3. Maps vocabulary-valid classification and lifecycle values. `is_canonical`
   never elevates standing, which becomes `candidate` with a self-scope.
4. Converts `supersedes`, `derived_from`, and `cites` into qualified
   relations (`assessment: unassessed`, `valid_time.basis: unknown`), and
   normalizes `urn:somnus:doc:` references. Authored inverse buckets are not
   converted.
5. Converts `location`/`origin` paths into `locations` with
   `primary`/`origin`/`historical` roles.
6. Converts live (non-code) `:::submatter:<kind>{id=…}` directives into
   marker pairs and region records. Region IDs keep valid local IDs, and
   UUID-style IDs become `r-<kind>-<first 8 hex>`.
7. Preserves every unmapped key (`provenance`, `origin.initial_commit`,
   `history_ledger`, genre profile blocks, unmapped enum values, directive
   attributes) under `extensions.somnus-migration` with schema
   `somnus://metadata/extension/migration-v0.1/1.0.0`.
8. Takes `access` and `ingestion` from configured operator defaults.

Migration stops (exit 1, file untouched) when the legacy `id` is missing or
not a UUID, or when the frontmatter cannot be parsed.

## 23. Versioning

Exact release resolution is mandatory: a 2.0.0 validator rejects other
releases at core level `[E_SCHEMA]`. A minor release may add optional
features. Removing enum values, tightening patterns, or changing field
meaning is a major release.
