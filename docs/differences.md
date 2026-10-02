---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a0f85e-42ab-7265-bfa7-10f4a29a1873"
  revision: 1
  title: "Somnus Metadata v1 to v2: Differences and Migration"
  classification:
    category: "engineering"
    type: "report"
    role: "informative"
    scope: "ecosystem"
    tags: ["somnus-dawn", "metadata", "migration"]
  lifecycle:
    status: "proposed"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:concept:metadata-standard"
        aspects: ["migration"]
  time:
    authored_on: "2026-10-01"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:concept:metadata-standard"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---

# Somnus Dawn: v1 → v2

> **DIFFERENCES & MIGRATION · THE SEMANTIC DELTA**  
> From a candidate Markdown header to a portable knowledge contract.

**Baseline:** uploaded *Somnus Markdown Metadata Standard Research.md*  
**Proposal:** [SOMNUS_FRONTMATTER_SPEC_v2.md](SOMNUS_FRONTMATTER_SPEC_v2.md)  
**Status:** proposed, not accepted canon · **Date:** 1 October 2026

The source is a research investigation, not a released schema. Its candidate is called v0.1; examples also use `0.1.0`, `1.0.0`, and `/v1` identifiers. For this comparison, **v1** denotes that supplied baseline and **v2** denotes the new proposal. The distinction prevents a migration tool from inventing a historical package release.

The principal change is architectural: v1 identifies and classifies documents; v2 also represents the entities, assertions, temporal meanings, and scoped authority needed to absorb them into Adab-Nebulae. Metadata remains authored state. The archive's receipts, inferred views, and acceptance decisions remain distinct.

## 1. Retained foundations

| v1 foundation | v2 treatment |
| --- | --- |
| Location-independent artifact identity | Retained and separated from revisions and representations |
| Classification separate from lifecycle | Retained; genre still does not determine truth |
| Lifecycle separate from authority | Retained; authority becomes scoped and independently resolved |
| Localized submatter | Retained with hidden markers and explicit selector records |
| Core plus profiles | Retained with exact releases and namespaced profile payloads |
| Controlled routing vocabulary | Retained; open tags remain discovery labels |
| JSON Schema Draft 2020-12 | Retained for structural validation, bounded by semantic checks |
| Source-preserving migrations | Retained; host semantics, comments, and mathematical source matter |
| Closed standard fields with extensions | Retained with explicit extension ownership and opaque handling |

## 2. Added in v2

| Addition | What it enables |
| --- | --- |
| Artifact / revision / representation separation | Faithful Markdown, TeX, and PDF surfaces can share a logical work without confusing export and authorship |
| Entity identities separate from artifact IDs | Descriptions of a system do not become the system itself |
| Claim records with kind and assessment | Requirements, observations, hypotheses, inferences, predictions, and measurements remain distinct |
| Region registry with stable local IDs | Sections, equations, tables, and source symbols survive heading changes |
| Revision-qualified evidence references | Evidence points to the source state actually examined |
| Applicability intervals separate from authorship and import time | A historical assertion remains queryable without appearing current |
| Contextual terms and aliases | ørama's changing meaning can be traced without name-based identity collapse |
| Explicit distinctions and registry adjudication | `distinct_from` and unresolved equivalence prevent accidental merges |
| Qualified graph edges | Relations carry assessment, time, context, and evidence rather than bare ID buckets |
| Scoped authority plus acceptance references | Canon is resolved for a target and aspect, rather than self-declared globally |
| Authority conflict records | Overlapping accepted sources are preserved for reconciliation |
| Native comment carriers | YAML payloads embed in TeX, YAML, TOML, source code, SQL, and markup |
| Explicit sidecars | JSON, binaries, and unsupported hosts carry metadata without grammar corruption |
| Host preamble rules | Shebangs, encoding cookies, editor directives, and declarations retain their required placement |
| Mathematical resource declarations | Macros, editable equations, raster limitations, and required attachments remain visible to ingestion |
| Access and allowed-use declarations | Archive, reasoning, export, training, and execution are independently described |
| Candidate / archive-only / excluded / canonical-candidate dispositions | Import intent does not masquerade as accepted canon |
| Logical archive collections and transactions | Ingestion can atomically reconcile revisions, claims, terms, and conflicts |
| Idempotence and tombstone rules | Repeated imports do not duplicate records; disappearing files do not imply deletion |
| Qualified downstream knowledge handoff | A future Pulsar integration can consume assertions with their limitations attached |
| Four conformance classes | Safe transport, valid core, resolved semantics, and canon are distinguishable |
| Error taxonomy and fixture outcomes | Future package behavior can be verified against explicit acceptance criteria |

These are proposed contracts. They are not claims that the archive, adapters, profile schemas, or Pulsar integration already implement them.

## 3. Tightened or corrected

### 3.1 Root structure

V1 recommends a hybrid root but describes it inconsistently: much of the core is flat, while `somnus` carries version/schema. V2 places every standardized field under `somnus`. Optional editor projections outside that namespace are derived and must agree with the authoritative payload.

This avoids forcing a TOML application to accept an invented metadata table or a YAML configuration loader to accept an extra runtime key. Comments carry metadata without changing the host data tree.

### 3.2 UUID and time semantics

V1 makes UUIDv7 mandatory, describes collision-free decentralized minting, and proposes checking its timestamp against `created_at`. V2 recommends UUIDv7 for new IDs, preserves imported UUIDv4 IDs, and makes collision handling explicit.

The embedded timestamp concerns ID generation. It cannot establish when historical material was created or when a claim became valid. Known dates remain known dates; missing dates remain missing. No midnight timestamps are fabricated from calendar dates.

### 3.3 Graph behavior

V1 suggests DAG construction and broadly cycle-free bidirectional relations. V2 defines cycle policy by predicate. Containment and supersession cannot cycle; other relations can form legitimate cycles unless a specific profile prohibits them.

Inverse relations are database views. The importer does not mutate another source file just to insert the reverse edge. Authored conflicting inverses become conflicts rather than being silently repaired.

### 3.4 Authority and epistemics

V1 uses `lifecycle.is_canonical` to designate a single source of truth. V2 replaces that boolean with scope, standing, acceptance reference, applicability, and conflict checks.

A normative artifact can still be a proposal. An accepted research artifact can still contain an unverified hypothesis. The archive cannot compile all invariant/decision-looking blocks into ground truth merely because their region type suggests authority.

### 3.5 Lifecycle

V2 retains the existing lifecycle concepts and adds `proposed` and `rejected`. It defines abandonment and reactivation behavior, plus partial replacement semantics. Archived items remain subject to structural integrity checks even when ongoing maintenance stops.

Historical applicability is not identical to archival state. A formerly valid definition may be historically important whether its source is archived or still actively maintained.

### 3.6 YAML and carrier grammar

V1 recommends YAML 1.2 and quoting ambiguous values. V2 defines a restricted JSON-compatible YAML subset and requires quoted strings throughout standardized authoring examples. Duplicate keys fail at every depth. Nulls, aliases, anchors, merge keys, tags, directives, and multi-document payloads are excluded by the Somnus contract.

Each carrier now has exact boundaries, prefix removal behavior, placement rules, and forbidden sequences. HTML-comment payloads cannot contain `--`; block-comment payloads cannot contain `*/`. Safe string escaping or a sidecar is required.

### 3.7 Region parsing

V1 favors generic `:::submatter` directives as the primary route and presents regex/string handling as an easy alternative. V2 defaults to separate hidden native-comment markers plus a header registry.

Nested ranges are stack-paired; crossing ranges fail. Markers inside code examples and host strings are inert. Region extraction requires lexical or parser context. An arbitrary regex scan cannot distinguish live semantics from an example of those semantics.

The v1 paper also overgeneralizes custom HTML behavior: CommonMark raw HTML blocks have termination rules, so behavior cannot be reduced to an absolute statement that every Markdown passage between custom tags remains unparsed. V2 avoids depending on custom wrappers and specifies standalone comment blocks with blank-line separation.

### 3.8 Schema evolution

V1 says old validators can ignore new optional additions, despite strict unknown-field rejection. V2 resolves that contradiction: exact releases are required, and an older strict reader may retain newer material without claiming semantic acceptance.

V1 also allows regex refinements as patches. V2 treats a change that rejects previously contract-valid material as breaking. A version label cannot make a compatibility break harmless.

### 3.9 Classification and profiles

V2 adds artifact types needed outside Markdown, including source-code, configuration, dataset, equation-set, conversation, and asset. Tags support Unicode search labels. Machine routing enums remain controlled.

Profiles move from a single classification-level pointer and arbitrary genre root blocks into `profiles` plus `profile_data`. The category, genre, schema release, and payload key no longer implicitly stand in for one another. Exact profile schemas remain implementation work before conformance can be claimed.

### 3.10 Performance and tooling claims

V1 proposes a Rust CLI and asserts sub-millisecond behavior. V2 defines validation stages and fixtures without promising latency or mandating a language. Parser compliance and retention behavior must be tested rather than inferred from a library name.

A future pip-style package can implement the contract. Creating these proposal documents does not claim that package exists.

## 4. Removed from this specification's responsibility

| Removed or replaced | Reason |
| --- | --- |
| Frontmatter provenance session logging | Daeron already has external tooling; this task does not redesign it |
| Hash/signature design and mandatory integrity ledger | Explicitly outside the requested semantic work |
| Inline transient event flushing and mandatory provenance folder | Not a prerequisite for semantic header adoption |
| UUID time equals artifact creation time | Invalid for retrospective imports and delayed identity assignment |
| `is_canonical` as sufficient authority | Cannot express scope, acceptance, historical applicability, or conflicts |
| Primary visible custom directive syntax | Conflicts with the requested hidden, format-spanning embedding surface |
| Source rewrites to add inverse relations | Archive views can supply inverses without changing authored works |
| Implicit whole-graph DAG requirement | Knowledge graphs legitimately contain cycles |
| Token minimization as the overriding header design goal | Deliberate semantic richness is a user requirement |
| Fictional author/provider/repository examples as a production template | Unknown real values must stay absent |
| Archived files exempt from all validation | Retention does not waive identity and parsing integrity |
| Silent old-reader acceptance of unknown new fields | Conflicts with strict schema semantics |
| Unmeasured native-binary latency claims | Performance requires implementation evidence |

Removal here does not delete metadata or history from existing artifacts. Older provenance fields are preserved for Daeron's external tooling or an explicitly labeled legacy extension. This proposal makes no assumptions about that tool's powers or wire format before inspection.

## 5. Field migration map

| v1 field or pattern | v2 destination | Migration rule |
| --- | --- | --- |
| `somnus.version` | `somnus.schema` | Pin the exact schema release; do not confuse it with artifact edition |
| `somnus.schema` | `somnus.schema` | Replace the old candidate address with the adopted exact release |
| Root `id` | `somnus.id` | Preserve UUID suffix; qualify stable identity with artifact URN |
| Root `title`, `description`, `purpose` | `somnus.title`, `summary`, `purpose` | Preserve meaning; do not compress a long description destructively |
| Root `slug` | `somnus.names.slug` | Keep mutable discovery label |
| Root string `aliases` | `somnus.names.aliases` | Add local IDs and kind; time basis unknown unless supported |
| Root `classification` | `somnus.classification` | Map compatible enums; preserve unknown values in migration extension |
| `classification.profile` | `somnus.profiles[]` | Exact schema plus profile payload key |
| Genre block such as `specification` | `somnus.profile_data.specification` | Preserve payload pending an exact profile validator |
| `lifecycle.status` | `somnus.lifecycle.status` | Preserve compatible state; do not elevate maturity |
| `lifecycle.is_canonical` | `somnus.authority` | Candidate authority until scoped acceptance resolves |
| `lifecycle.reviewed_at` | `somnus.time.reviewed_at` | Preserve known instant and offset |
| Root creation/update dates | `somnus.time` | Keep date precision; never use UUID mint time as substitute |
| Root relation buckets | `somnus.knowledge.relations[]` | Qualify endpoints; assessment unassessed until evidence attached |
| `location`, `origin` | `somnus.locations[]` | Explicit primary/origin roles; old paths remain hints |
| `origin.initial_commit` | External tooling or legacy extension | Preserve without building a commit provenance contract |
| `provenance.authors/operators/...` | Existing external tooling or legacy extension | No fabricated replacement session log |
| Directive ID/attributes | `knowledge.regions[]` plus hidden markers | Parse live directives; preserve stable local IDs where valid |
| Inline hypothesis text | Optional `knowledge.claims[]` | Add only supported structure; no automatic truth promotion |
| `extensions` or `x-somnus-*` | `somnus.extensions.<owner>` | Preserve opaque payload and declare its migration schema |
| No revision field | `somnus.revision` | Initialize documented v2 revision; do not invent missing historical revisions |
| No usage intent | `somnus.access`, `somnus.ingestion` | Use explicit operator policy; unknown permission cannot be assumed |

A bare v1 UUID and its new qualified artifact URN refer to the same preserved identity. The migration registry should retain the bare UUID as a legacy resolution key so old citations continue to work.

## 6. Migration stop conditions

Preserve the source and hold affected semantic acceptance when any of these conditions occurs:

- The v1 `id` is missing, duplicated, or ambiguous.
- A canonical boolean has no resolvable target scope or acceptance decision.
- An alias could refer to both a historical framework and a present agent role.
- A directive-like block may be a literal example rather than a live region.
- A date is known only approximately but the target field would require an exact instant.
- A mathematical export is incomplete, clipped, or dependent on missing macros.
- The same identity/revision already exists with different authored content.
- A host grammar would be affected by inserting or relocating the envelope.

These conditions block the affected normalization or promotion, not useful archival retention. Migration reports must name what remains unresolved and preserve the original values.

## 7. What v2 makes possible

A future archive query can distinguish the earlier framework use of ørama, its present agnostic agent designation, and the particular Rog-Data-Agent context. It can return the originating statement, affected entity, applicable interval, linked implementation, and unresolved identity questions. Matching text alone cannot safely do that.

That is the proposal's tenfold expansion: portable headers become structured entry points into a source-preserving archive, while downstream consumers retain the qualifications required to reason over Somnus knowledge. Adoption still requires registry integration and tested adapters; the proposal supplies the contract they must honor.
