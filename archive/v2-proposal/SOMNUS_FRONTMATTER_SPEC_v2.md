---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a0f85e-42ab-74d5-b9e9-1ff49cbd1ca4"
  revision: 1
  title: "Somnus Dawn: Universal Metadata and Frontmatter Specification"
  summary: "A proposed semantic contract for portable artifacts and their absorption into Adab-Nebulae."
  classification:
    category: "engineering"
    type: "specification"
    role: "normative"
    scope: "ecosystem"
    tags: ["somnus-dawn", "metadata", "adab-nebulae", "pulsar"]
  lifecycle:
    status: "proposed"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:concept:metadata-standard"
        aspects: ["semantic-model", "embedding", "ingestion"]
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
    body_role: "specification"
---

# Somnus Dawn

> **UNIVERSAL METADATA & FRONTMATTER · VERSION 2.0.0 PROPOSAL**  
> **Dust and gas become a navigable constellation.**  
> One semantic model. Many file surfaces. Explicit knowledge boundaries.

**Document:** proposed specification · **Date:** 1 October 2026  
**Authority:** candidate for Daeron's adoption · **Companion:** [differences.md](differences.md)

A Somnus artifact should carry enough meaning to survive a rename, a format conversion, an agent handoff, and eventual absorption into Adab-Nebulae. Its header must tell the archive what the artifact is, what it describes, which statements it makes, where those statements apply, and how they may be used. A document's polish, filename, or most recent edit must never substitute for these distinctions.

This proposal advances the uploaded *Somnus Markdown Metadata Standard Research* from a candidate Markdown convention into a universal semantic contract. The upload calls its candidate v0.1 and mixes several version labels. Here, **v1** means that supplied research baseline; **v2** means this proposed specification. It does not imply that a released v1 package exists.

The following clauses are normative **within the proposal**. Adoption is separate. The document does not declare itself accepted canon, does not claim a validator exists, and does not specify hashing, signatures, forensic provenance, or a replacement for Daeron's external tooling. That integration can be defined after the PowerShell tool is supplied.

## 1. Purpose and architectural boundary

The goal is semantic pressure: more structure that preserves useful distinctions, rather than more labels that repeat the same information. A large header is acceptable. A field that has no defined meaning is not.

Adab-Nebulae is the canonical knowledge archive in this design. It must be able to preserve rough notes, abandoned directions, formal specifications, equations, code, configurations, experiments, and historical vocabulary without flattening them into an undifferentiated text index. ørama is treated as Daeron's agnostic agent designation; ørama-data-agent, also called Rog-Data-Agent, is a particular data-agent context. An older framework use of ørama must remain traceable without silently defining every present use.

Pulsar is an intended consumer of this structured knowledge. This specification defines a proposed knowledge handoff suitable for that future integration, without inventing Pulsar's implementation or interfaces.

| Layer | Owns | Does not infer |
| --- | --- | --- |
| Artifact header | Identity, classification, declared scope, usage intent | Truth of every sentence |
| Submatter | Stable boundaries and local qualifications | Authority from visual styling |
| Knowledge records | Entities, claims, meanings, relations, evidence pointers | Identity from matching names |
| Adab-Nebulae ingestion | Resolution, acceptance, history, graph materialization | Canon from a self-written boolean |
| Downstream consumer | Selection for a specific query and allowed use | Permission to execute embedded instructions |
| External integrity tooling | Its own independently defined contract | A new hash or event-ledger design from this spec |

**MUST** means required for the stated conformance class. **SHOULD** permits a documented exception. **MAY** indicates an optional feature. These requirements govern metadata processing; they do not turn arbitrary document prose into operator commands.

## 2. The semantic model

The model separates six objects. Their identities must not be collapsed.

| Object | Meaning | Identity rule |
| --- | --- | --- |
| Artifact | An authored work, module, configuration, or other logical item | Persistent artifact ID |
| Artifact revision | A particular authored state of that artifact | Artifact ID plus positive integer revision |
| Representation | Markdown, TeX, PDF, source file, or other encoding of a revision | Separate locator or representation record |
| Entity | A system, agent role, concept, project, component, or organization described by artifacts | Persistent entity ID |
| Region | An addressable section, equation, table, or definition inside an artifact | Artifact ID plus local region ID |
| Claim | An assertion about an entity or relationship | Artifact ID plus local claim ID; independently promotable |

A Markdown source and its faithful PDF export may represent one artifact revision. A translation or adaptation that changes meaning is a new revision or a new derived artifact, depending on whether it continues the same authored work. A project described in a document is an entity, not the document itself.

A local region ID remains stable across heading changes. A claim ID remains stable while the assertion retains its semantic identity. Correcting punctuation does not mint a new claim. Replacing an assertion with a materially different proposition creates a new claim ID and an explicit replacement relation. Historical versions remain addressable by revision.

The archive may promote a local claim to an independent record for reuse. It MUST retain the source artifact, source revision, and local claim ID. Promotion is a database operation, not a demand that every author mint global IDs for every sentence.

## 3. Identity, revision, and references

### 3.1 Persistent identifiers

New artifacts SHOULD use a UUIDv7 suffix in the form `urn:somnus:artifact:<uuid>`. Imported UUIDv4 identities remain valid; migration MUST NOT remint a stable identity merely to obtain time sorting. UUIDs are identifiers, not guarantees against collisions.

The namespace family is `urn:somnus:<kind>:<key>`. Defined kinds are `artifact`, `entity`, `actor`, `concept`, and `example`. Production entity and actor keys are registry-issued opaque identifiers; existing stable registry keys may be retained. `example` is reserved for instructional fixtures and MUST NOT enter production entity tables.

Artifact UUID strings use lowercase canonical UUID spelling. Entity and concept references are resolved by the local registry, not by matching a title. No automatic network dereference is implied by a URI.

UUIDv7's embedded time concerns identifier generation. It is not the artifact's creation date, an idea's origin date, or the time an assertion became true. Retrospective imports may mint an ID today for material authored years ago.

### 3.2 Revision and representation

`revision` is a positive integer increased for each committed authored state that changes the body or semantic metadata. A transport-only conversion that preserves both may share a revision. Generated locators and archive ingestion receipts belong outside the authored payload and do not force revision increments.

`edition`, when supplied, is a human release label such as `"2.0-draft"`. It does not replace `revision` or the metadata schema version. Concurrent branches that assign the same revision to different states are conflicts; the archive MUST preserve both candidates and require reconciliation, never overwrite one by arrival order.

A faithful export retains artifact ID and revision and lists its representation relationship. A copy with a new purpose, independently edited fork, or semantic adaptation gets a new artifact ID and a `derived_from` edge. A byte-for-byte mirror does not become a new intellectual artifact.

### 3.3 Reference object

A reference is an object with required `ref` and optional `revision`, `region`, `claim`, and `locator_hint`. `revision` is a positive integer. Region and claim addresses use their local IDs. References to an artifact's region or claim SHOULD pin a revision when used as evidence.

```yaml
ref: "urn:somnus:artifact:01a0f85e-42ab-74d5-b9e9-1ff49cbd1ca4"
revision: 1
region: "embedding-contract"
```

The example describes the reference shape; the named region is illustrative. A path is a hint, never the identity. DOI and HTTPS references are valid external references. Resolution failures are explicit unresolved records; an importer MUST NOT replace them with a plausible title match.

### 3.4 Local names

Local region, claim, relation, alias, and term IDs match `^[a-z][a-z0-9_]*(?:-[a-z0-9_]+)*$` and are unique within their corresponding artifact namespace. Examples: `r-agent-role`, `c-role-expansion`, `e-alias-current`.

Machine field names use lowercase `snake_case`. Human labels and prose support Unicode. Preserve original labels; search views may normalize them, but normalized spellings do not become identity or authorize merges. Do not transliterate ørama or Übermensch into identity by silently replacing characters.

## 4. One namespace and one authoritative payload

All standardized metadata resides under a single top-level `somnus` mapping. The enclosing host may have other frontmatter keys, but only `somnus` is the standard's authoritative payload.

Markdown tooling MAY require projections such as `title`, `tags`, or `aliases` beside `somnus`. Such projections are generated views. If supplied, they MUST agree with their source metadata and MUST NOT be used to repair or override a conflicting Somnus value. An adapter identifies each projection explicitly in its configuration. This spec does not require duplicating fields for every editor.

A source representation contains exactly one authoritative metadata envelope, or an explicitly declared sidecar binding. Multiple envelopes, or both an envelope and authoritative sidecar, are an error. Rendered banner text is not a second envelope.

`somnus.schema` identifies an exact immutable schema release: `somnus://metadata/core/2.0.0`. This is a proposed offline registry address, not an available web endpoint. The schema release MUST be present in the consumer's registry before strict acceptance. No unpinned `latest` schema is allowed.

### 4.1 Core fields and optional modules

The following fields are required for **core conformance**. The payload may be large; the requirement is semantic completeness, not brevity.

| Field | Type | Contract |
| --- | --- | --- |
| `schema` | String | Exact core schema URI |
| `id` | String | Stable artifact URN |
| `revision` | Integer | Positive authored revision |
| `title` | String | Nonempty human title |
| `classification` | Object | Category, type, role, scope, tags |
| `lifecycle` | Object | Required workflow status |
| `authority` | Object | Required standing and scopes |
| `time` | Object | Known authorship times; may be empty |
| `knowledge` | Object | Coverage and subject references |
| `access` | Object | Visibility and allowed uses |
| `ingestion` | Object | Disposition and body role |

`classification.tags` and `knowledge.subjects` may be empty arrays. An empty `time` mapping means no authorship dates are supplied. Unknown dates MUST NOT be replaced with the ID time or import time. An empty array means no entries are declared, not that none exist in reality.

Optional standard fields are `summary`, `purpose`, `language`, `edition`, `names`, `context`, `ownership`, `locations`, `representations`, `content`, `profiles`, `profile_data`, `bindings`, and `extensions`. Optional submodules inside `knowledge` are `entities`, `claims`, `relations`, `regions`, and `terms`.

Unknown standard fields are errors. Experimental keys belong exclusively inside `extensions`. Every extension is keyed by an owner namespace and carries `schema` plus `data`. The namespace is a nonempty registry identifier, schema is an exact URI string, and data is a JSON-compatible value. Consumers preserve an unknown extension losslessly and MUST NOT treat it as accepted semantic input.

### 4.2 Presence semantics

Omitted fields mean **unspecified**. Empty arrays mean **no entries declared**. `null` is forbidden in the standardized payload; absence is represented by omission. `false` is a real boolean, not an unknown. Values such as `"unknown"`, `"none"`, or `"n/a"` are forbidden stand-ins unless a field explicitly includes that enum value.

Templates must leave unavailable optional values absent. They must not invent dates, actors, repository addresses, license grants, measurements, acceptance records, or evidence to satisfy a template.

## 5. Classification, profiles, and subject context

Classification describes the artifact's genre and function. It does not identify the system it describes and does not determine whether an assertion is true.

| Field | v2 vocabulary |
| --- | --- |
| `category` | `research`, `engineering`, `operations`, `governance`, `context`, `archive` |
| `type` | `whitepaper`, `specification`, `architecture-record`, `report`, `task`, `plan`, `notepad`, `benchmark`, `test-result`, `decision-record`, `runbook`, `index`, `state`, `memory`, `source-code`, `configuration`, `dataset`, `equation-set`, `conversation`, `asset` |
| `role` | `normative`, `informative`, `working`, `exploratory`, `historical` |
| `scope` | `ecosystem`, `fleet`, `repository`, `subsystem`, `module`, `component`, `artifact` |
| `subtype` | Optional registered specialization, otherwise an open kebab-case discovery label |
| `tags` | Array of nonempty Unicode search labels; no authority or routing semantics |

A registry release pins the vocabulary. New routing enums are a compatibility event, not harmless free text. An importer cannot silently reinterpret an unfamiliar enum.

`context` optionally supplies `project_refs`, `system_refs`, `division_refs`, `repository_refs`, `release_constraints`, and `platform_constraints`, all arrays. References use reference objects; constraints use `{target_ref, language, expression}` with an explicit registry-defined expression language. `language` is its exact registered identifier and `expression` is a nonempty string. An unknown constraint language stays unresolved. Consumers must not guess that an expression is SemVer, a path glob, or a mathematical formula.

Profiles are an optional array of `{schema, key}`. The keys of `profile_data` must exactly match declared profile keys; undeclared profile payloads are errors. Each exact profile URI validates the corresponding object at `profile_data.<key>`. A profile may require fields, but it may not redefine core meanings. Duplicate keys and mutually incompatible requirements are errors.

| Proposed profile | Additional contract |
| --- | --- |
| `specification` | Target references, normative region references, acceptance criteria |
| `architecture` | Component references, boundaries, interfaces, dependencies, invariants |
| `decision` | Decision status, alternatives, rationale, affected scope, decision references |
| `research` | Questions, hypotheses, assumptions, method and evidence references |
| `benchmark` | Workload, environment, measurements, units, repetitions, baseline, conditions |
| `task` | Objective, target references, completion criteria, dependencies, task state |
| `configuration` | Host syntax, configuration target, environment, parsing constraints |
| `source` | Language, module references, exported interfaces, test references |
| `conversation` | Participant references, source turns, correction links, capture boundaries |
| `terminology` | Terms, definitions, entity bindings, exclusions, applicability |

The table specifies profile requirements conceptually. Exact profile schemas must be authored and fixture-tested before profile conformance is claimed. This proposal supplies the core grammar and module contracts, not a released schema package.

## 6. Lifecycle, authority, and currentness

### 6.1 Workflow status

`lifecycle.status` is one of `draft`, `proposed`, `provisional`, `active`, `experimental`, `superseded`, `deprecated`, `historical`, `archived`, or `rejected`.

`draft` means incomplete. `proposed` means submitted for adoption. `provisional` means usable with stated limitations. `active` means maintained and in use. `experimental` identifies exploration. `superseded` requires an explicit replacement edge. `deprecated` discourages use without implying a replacement. `historical` means retained for former applicability. `archived` is a storage/maintenance state. `rejected` preserves a declined proposal.

Archival does not waive parsing or identity checks and does not erase historically valid claims. It exempts ongoing maintenance, not structural integrity. A correction to archived material is a new revision or correcting artifact, never a hidden rewrite of stored history.

Supported transitions are draft to proposed/experimental/rejected; proposed to provisional/active/rejected/experimental/superseded; provisional to active/experimental/rejected/superseded/deprecated; experimental to draft/proposed/provisional/rejected/deprecated/historical; active to superseded/deprecated/historical; superseded to historical; deprecated to historical/archived; historical or rejected to archived. `draft`, `proposed`, `provisional`, and `experimental` may also become archived if work is abandoned, with a reason. Reactivation from historical, superseded, or archived creates a new revision and requires a reason plus renewed authority review. A transition is not a claim that software has been deployed.

`lifecycle.reason` and `lifecycle.replacement_refs` are optional. Reasons are required for abandonment and reactivation. A superseded artifact requires at least one resolved replacement before current-canon acceptance; partial replacements specify regions or aspects and cannot retire unrelated portions.

### 6.2 Scoped authority

`authority.standing` is `unasserted`, `candidate`, `accepted`, `retired`, or `rejected`. `authority.scopes` is an array of `{target_ref, aspects}` and may be empty only for unasserted authority. `aspects` contains registered scope labels, not free-form claims of universal authority.

Accepted authority additionally requires `valid_time` using the interval contract in Section 7, and `acceptance_ref`: a reference to a decision or operator acceptance record recognized by the configured authority registry. Optional `owner_ref` identifies the actor responsible for maintaining the authority assignment. The document can declare acceptance; ingestion verifies it independently. No model output, latest timestamp, or `standing: accepted` string can grant itself canon.

Candidate and unasserted authority may omit `valid_time`; the omission grants no time-specific authority. Accepted authority with unknown applicability remains unresolved for time-specific canon selection. A scope may include optional `conditions` using the same constraint object contract as context. Acceptance is valid only where those conditions resolve. A normative role describes intended prescriptive content; it does not grant acceptance.

### 6.3 Current canon is computed

An artifact is eligible as current canon for a query only when its acceptance resolves, its authority covers the query, its lifecycle permits current use, its relevant claim/region is applicable, its allowed uses permit the operation, and no unresolved authority conflict applies. `active` and `provisional` can be eligible; provisional limitations must travel with the result.

Two accepted authorities over the same target, aspect, conditions, and overlapping valid interval create an authority conflict unless an explicit delegation or precedence decision resolves them. Recency and source order are not tie-breakers. Return both with a conflict marker; block automatic singular-canon promotion.

Document authority does not upgrade an unverified hypothesis in its body. An accepted research document may contain a rejected hypothesis and valid observations. Selection occurs at claim or region granularity.

## 7. Time and changing meanings

Three clocks remain separate:

| Clock | Location | Meaning |
| --- | --- | --- |
| Authorship | `time` | When the artifact was authored or revised |
| Applicability | Claim, relation, term, or alias `valid_time` | When a statement or meaning applies |
| Archive observation | Ingestion receipt outside the authored payload | When a revision entered the archive |

`time` permits `created_at`, `updated_at`, `reviewed_at`, and `authored_on`. The first three are quoted RFC 3339 timestamps with an explicit offset; known instants normalize to UTC for indexing. `authored_on` is a quoted calendar date and MUST NOT be converted into a fabricated midnight instant. If both creation and update instants exist, update must not precede creation. Historical authoring uncertainty is preserved by omission and optional `time.note`.

A `valid_time` object has required `basis`: `bounded`, `open`, `timeless`, or `unknown`. `bounded` requires `from` and `until`; `open` requires `from` and forbids `until`; `timeless` and `unknown` forbid both bounds. Bounds are quoted RFC 3339 timestamps. Intervals are half-open: from is included, until is excluded. Timeless is an explicit assertion of time independence, not an importer default. Unknown remains retrievable but cannot independently establish applicability to a time-specific query.

For historical changes with only approximate dates, preserve the source's language in `valid_time.note` and use `basis: unknown` until a supported boundary is available. Do not invent an exact instant to force a clean timeline.

The archive stores these applicability intervals alongside its own observation sequence. A later correction may reveal that an earlier statement was already false when imported. That does not erase the earlier observation, and import time does not become truth time.

## 8. Names, aliases, and entity evolution

`names` describes names for the artifact, not names for its subject entities. It permits `slug` and `aliases`. Each artifact alias is `{id, label, kind, valid_time}`; `kind` is `former-title`, `short-name`, `acronym`, `spelling`, or `translation`. A slug is mutable and never resolves identity alone.

`knowledge.entities` contains entity records with required `ref`, `label`, and `kind`; optional `description`, `aliases`, and `external_refs`. Entity kind is `project`, `system`, `component`, `agent`, `agent-role`, `framework`, `concept`, `organization`, `dataset`, `model`, or `tool`. Entity aliases use `{id, label, kind, valid_time}`, with kind `former-name`, `short-name`, `acronym`, `spelling`, or `translation`.

An entity declaration binds a stable reference to a label and kind for this source. It does not authorize overwriting the registry's canonical definition. Conflicting declarations enter a reconciliation queue with both source revisions retained.

One spelling can denote several entities. One entity can carry several names. A historical usage of a term is not necessarily a former name of a current entity. These cases require different records.

`knowledge.terms` entries contain required `id`, `label`, `definition`, `entity_refs`, and `valid_time`; optional `excluded_refs`, `context_refs`, and `region_ref`. An exclusion explicitly records a distinction: for example, a role term should not be interpreted as naming one specific agent implementation. Unresolved exclusions cannot be silently discarded.

**ørama example:** If historical ørama was a framework and current ørama is an agnostic agent designation, the first question is whether this is one entity with an expanded role or two entities linked by conceptual lineage. Metadata must record the supported relationship; it must not decide identity from the shared spelling. Rog-Data-Agent can be an alias for the specific data-agent entity without turning every ørama into Rog.

## 9. Claims and evidence

`knowledge.coverage` is `artifact`, `selected-claims`, or `structured-claims`. `artifact` supplies document-level descriptions only. `selected-claims` identifies some assertions explicitly while leaving other prose unstructured. `structured-claims` means all claims intended for structured export are enumerated; it does not promise that every sentence is an assertion.

The initial claim predicate registry contains `definition`, `has_role`, `has_property`, `requires`, `predicts`, and `measures`. Each accepts an entity/concept subject and a typed literal or reference object according to its registered signature; profile-specific meanings require a pinned registry extension. A predicate label does not encode a claim's assessment.

A claim record has the following contract:

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | Yes | Stable local claim ID |
| `subject_ref` | Yes | Entity or concept the assertion concerns |
| `predicate` | Yes | Registered predicate label |
| `object` | Yes | Exactly one of `ref` or `value` |
| `statement` | Yes | Human-readable assertion |
| `kind` | Yes | `observation`, `definition`, `requirement`, `hypothesis`, `inference`, `prediction`, or `measurement` |
| `assessment` | Yes | `unassessed`, `supported`, `contested`, `refuted`, or `withdrawn` |
| `valid_time` | Yes | Applicability, including explicit unknown |
| `region_ref` | Yes | Local source region ID |
| `evidence_refs` | No | Array of revision-pinned source references |
| `assumption_refs` | No | Array of claim reference objects |
| `context_refs` | No | Array of reference objects |
| `conditions` | No | Explicit constraint objects |
| `confidence` | No | `{value, method}`; value in [0,1], method nonempty |

An object `value` is a JSON-compatible scalar, array, or mapping. It never implicitly becomes an entity reference. A measurement SHOULD carry a profile-defined value, unit, uncertainty, sample count, and conditions. A numerical confidence is an author's assessment, not a calibrated probability unless the declared method establishes that interpretation.

`supported` requires at least one evidence reference. Closed acceptance requires those references to resolve. An operator assertion can be evidence for the operator's naming decision; it is not automatically evidence for measured performance. `requirement` identifies a prescribed rule, not observed behavior. `inference` retains assumptions and evidence. `prediction` must not be returned as an observation.

Claims are not automatically extracted as truth from all prose. A heuristic extractor may propose candidates, but these remain unassessed candidates and carry their source spans until reviewed or accepted by the relevant ingestion policy.

## 10. Relationships and graph constraints

`knowledge.relations` is an array of qualified edges. Each edge has required `id`, `subject`, `predicate`, `object`, `assessment`, and `valid_time`; `subject` and `object` are reference objects. Optional `region_ref`, `evidence_refs`, `conditions`, and `note` preserve qualification. `assessment` uses the claim assessment enum, and `supported` requires evidence.

| Predicate | Inverse view | Specific constraint |
| --- | --- | --- |
| `supersedes` | `superseded_by` | Acyclic; replacement scope must be explicit when partial |
| `derived_from` | `has_derivative` | Does not transfer authority; revision-qualified lineage should be acyclic |
| `describes` | `described_by` | Artifact or region to entity |
| `implements` | `implemented_by` | Does not prove compliance by itself |
| `depends_on` | `required_by` | Cycles allowed unless the dependency profile forbids them |
| `part_of` | `has_part` | Containment subgraph must be acyclic |
| `cites` | `cited_by` | Citation is not endorsement |
| `supports` | `supported_by` | Evidence to claim |
| `contradicts` | `contradicts` | Symmetric; retain both sides |
| `renamed_to` | `renamed_from` | Registered naming succession with a time qualification |
| `role_expanded_to` | `role_expanded_from` | Semantic evolution; not identity equivalence |
| `specializes` | `generalizes` | Specific role or implementation to broader concept |
| `equivalent_to` | `equivalent_to` | Candidate equivalence until registry adjudication |
| `distinct_from` | `distinct_from` | Explicit non-equivalence |

Additional predicates require an exact registry extension and declared endpoint kinds, inverse behavior, cycle policy, and inference permissions. An unknown predicate is preserved but not used to derive edges.

Inverse edges are materialized database views. Consumers MUST NOT rewrite another source artifact merely to insert inverse metadata. If both directions are authored, they must agree; contradictions remain conflicts. The overall knowledge graph is not a DAG. Only specifically constrained subgraphs are checked for cycles.

Entity merging requires a recognized registry decision. An `equivalent_to` edge alone cannot collapse IDs. `distinct_from` blocks automatic alias-based merging. Revisions, region boundaries, and contextual qualifications must remain available after any approved consolidation.

## 11. Submatter: stable regions without display pollution

`knowledge.regions` contains `{id, kind, selector}` records, with optional `title`, `claim_ids`, `authority`, `access`, `valid_time`, and `context_refs`. Region kind is `section`, `definition`, `invariant`, `decision`, `hypothesis`, `evidence`, `equation`, `table`, `code`, `example`, or `archive`.

Selectors have required `kind` plus the fields appropriate to that kind:

| Selector kind | Required fields | Acceptance requirement |
| --- | --- | --- |
| `marker` | `name` | Exactly one paired marker range |
| `tex-label` | `name` | One matching TeX label inside a supported structural environment |
| `symbol` | `name`, `language` | One resolved symbol in the pinned source revision |
| `json-pointer` | `pointer` | One resolved pointer in a parsed JSON-compatible host tree |
| `heading` | `text`, `occurrence` | Explicit 1-based occurrence in the pinned revision |
| `line-range` | `from`, `until`, `revision` | 1-based inclusive from, exclusive until; pinned revision |

Marker selectors are preferred for durable authored regions. Heading and line selectors are import or legacy mechanisms; ambiguity produces an unresolved region. TeX labels require a structural adapter because a section label, equation label, and nested environment do not imply the same region extent. A regex alone cannot establish every TeX region boundary.

For Markdown, use separate, standalone comment blocks around ordinary Markdown:

```markdown
<!-- somnus:region:begin r-agent-role -->

## Agent designation

ørama names an agnostic agent role in this illustrative section.

<!-- somnus:region:end r-agent-role -->
```

The header registers `r-agent-role` with selector `{kind: "marker", name: "r-agent-role"}`. The markers carry identity only; the registry holds semantic attributes. This prevents two authoritative copies of a region's status.

Markers must occupy their own lines with blank lines separating them from body blocks. Pairing is stack-based: regions may nest, but ranges may not cross. Separate comments can form nested region ranges; HTML comments themselves must not be nested. Region IDs are unique. Unmatched or duplicated markers are structural errors.

Markers inside fenced code, indented code, host string literals, or literal examples are not live regions. A Markdown adapter must use parser context and recognize the metadata envelope before scanning the body. Line regex over the entire file is insufficient.

Native comment markers use the same marker text after the host comment prefix, for example `% somnus:region:begin r-equation` or `# somnus:region:begin r-config`. Their interpretation requires the host adapter's lexical context. Generic directives and Pandoc fenced divs MAY be imported by explicit adapters, but are not the default authoring syntax.

Region metadata inherits document context, authority limitations, and access restrictions. It may narrow authority and usage permissions; it may not elevate candidate authority to accepted or broaden access. Historical applicability can differ from the document's current workflow status. A hypothesis region remains a hypothesis inside an accepted specification.

## 12. Content and mathematics preservation

`content` optionally declares `math`, `resources`, and `extraction`. The optional root `language` is a BCP 47 language tag describing the primary natural language of the artifact. `math` is `{source_format, delimiters, macro_refs, equation_region_ids}`; source format is `tex`, `mathml`, `unicode`, `raster`, or `mixed`. The arrays declare the actual authoring conventions and dependencies, not an assumed renderer feature.

Resources are `{ref, media_type, role, required}` records; roles include `macro-source`, `figure`, `table-source`, `attachment`, and `rendered-output`. `required` is boolean. Referenced resources must resolve for a claim whose interpretation depends on them. A rendered image is never an automatic substitute for editable math source.

`extraction` is `{state, limitations}`; state is `complete`, `partial`, or `unverified`, and limitations is an array of strings. The field is an author's declaration, checked independently at ingestion. Missing macros, clipped raster equations, or omitted attachments yield partial extraction, not repaired mathematics.

An equation can be a region with a TeX label selector, an attached canonical source resource, and a human description. The archive preserves original math source plus renderer-dependent projections. An embedding cannot become the source of record for an equation.

For chunking, an equation, its referenced definitions, and critical assumptions form an atomic retrieval unit or an explicitly linked bundle. If too large for a consumer budget, retain the unit and generate a qualified summary; do not split the equation text into unrelated fragments and claim lossless extraction.

## 13. Serialization: one portable YAML payload

All carriers extract the same `somnus` mapping. Comment transport does not switch the metadata language to TOML, Python, TeX, or shell syntax.

Somnus adopts a restricted YAML 1.2.2 authoring subset. Standard fields use two-space indentation, string keys, quoted string values, decimal finite numbers, lowercase `true`/`false`, arrays, and mappings. Integers must be exactly representable by the consumer; implementations claiming interoperability must at least support the signed 53-bit safe-integer range, and reject rather than round larger unsupported values. Block strings are permitted when they obey the carrier's forbidden-sequence rules. Nulls, aliases, anchors, merge keys, custom tags, directives, multiple YAML documents, and non-string mapping keys are forbidden. Duplicate keys are errors at every depth. Tab indentation is forbidden.

This restriction is a Somnus interoperability decision, not a claim that YAML itself forbids every excluded feature. It makes the normalized model JSON-compatible. Carrier delimiters are stripped before parsing; Markdown's closing `---` is not a second YAML document in the extracted payload.

UTF-8 is the standard authoring encoding. LF is preferred; CRLF input is accepted without altering host semantics. A leading UTF-8 BOM may be accepted at extraction but is not emitted. Normalization must not rewrite the source file simply to improve indexing. Field order is for readability and has no semantic effect.

The canonical field order is schema, identity, description, classification, lifecycle, authority, time, names, context, ownership, locations, representations, content, knowledge, access, ingestion, profiles, profile_data, bindings, extensions. Within `knowledge`, use coverage, subjects, entities, terms, regions, claims, relations.

## 14. Carrier bindings across formats

A **carrier** locates and strips the metadata envelope; a **host adapter** understands the surrounding file. They are separate responsibilities. A carrier must never insert application-visible keys into a configuration unless that host explicitly reserves them.

| Host | Default carrier | Placement | Important boundary |
| --- | --- | --- | --- |
| Markdown / MDX | YAML frontmatter | Start of file | Hidden display is renderer-dependent; MDX requires its own adapter |
| Plain CommonMark | HTML comment envelope | Start of body | Comments are hidden by ordinary renderers; do not wrap body text inside one |
| LaTeX | `%` comment lines | Before document body, after required magic comments | TeX source remains unchanged outside the envelope |
| YAML | `#` comment lines | Leading header area | Never add `somnus:` to the host configuration mapping by default |
| TOML | `#` comment lines | Leading header area | YAML payload inside comments; no new TOML table |
| Python / shell / PowerShell | `#` comment lines | After mandatory preamble | Preserve shebang, encoding cookie, help/directive requirements |
| JavaScript / TypeScript / Rust / C / C++ | `//` comment lines | Supported leading comment area | Respect host directives and preprocessor constraints |
| CSS | `/* ... */` block envelope | After any required initial declaration | Serializer must guard the block-comment terminator |
| SQL | `--` comment lines | Leading comment area | Strip exactly one transport prefix; dialect adapter required |
| HTML / XML / SVG | HTML/XML comment envelope | After XML declaration/DOCTYPE where required | Escape forbidden comment sequences |
| JSON | Sidecar | Adjacent or registry-bound | Strict JSON has no comment carrier |
| PDF / DOCX / images / notebooks | Sidecar or explicitly defined adapter | Separate declared binding | No assumed arbitrary comment support |

Comments in a configuration are invisible to its normal data parser. They are still visible to anyone who reads the source, and formatters may discard them. Hidden rendering is not confidentiality. A comment-preserving editor or sidecar route is required where header retention matters.

### 14.1 Markdown frontmatter

```yaml
---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:example:artifact"
  revision: 1
  title: "Carrier shape only"
---
```

This is a **carrier fragment**, not a core-conformant artifact: it deliberately omits required modules and uses an example ID. The first non-BOM line must be `---`. The closing delimiter is an unindented line containing exactly `---`. An unclosed opener is an extraction error. Conventional frontmatter is not universal CommonMark syntax; use the next binding when an ordinary CommonMark display must hide the envelope.

### 14.2 Markdown and HTML hidden envelope

```markdown
<!-- somnus:metadata:v2
somnus:
  schema: "somnus://metadata/core/2.0.0"
  title: "Carrier shape only"
somnus:end -->
```

The opening and closing lines are exact carrier markers. The payload must contain no `--` sequence. When strings contain that sequence, the serializer emits equivalent YAML double-quoted escapes, or selects a sidecar. Literal block values that cannot be safely represented in the carrier must be changed to escaped quoted strings. The entire surrounding document is never wrapped in this comment.

### 14.3 YAML, TOML, and hash-comment hosts

```toml
# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   title: "Configuration carrier shape only"
# somnus:end

[agent]
mode = "local"
```

Strip exactly `# ` from each payload line. A carrier blank line is `# `, not an unprefixed empty line. Retain indentation after stripping. The example's `[agent]` table is ordinary host TOML and not part of the YAML payload. The same envelope works above an ordinary YAML configuration mapping.

LaTeX uses `% `, slash-comment hosts use `// `, and SQL uses `-- ` with the same marker names. The adapter matches the configured prefix exactly and does not repeatedly strip comment characters from payload text.

A TeX carrier can precede the document declaration while keeping its body ordinary TeX. This is a carrier fragment; its metadata is intentionally incomplete.

```tex
% !TeX program = lualatex
% somnus:metadata:v2
% somnus:
%   schema: "somnus://metadata/core/2.0.0"
%   title: "Equation carrier shape only"
% somnus:end
\documentclass{article}
\begin{document}
\begin{equation}\label{eq:state-update}
s_{t+1} = F(s_t, a_t)
\end{equation}
\end{document}
```

A production header would register the equation using the `tex-label` selector and declare any required macros. Neither the TeX engine nor a TOML parser needs to understand Somnus metadata for these carriers to remain comments.

### 14.4 Block-comment hosts

```css
/* somnus:metadata:v2
somnus:
  schema: "somnus://metadata/core/2.0.0"
  title: "Stylesheet carrier shape only"
somnus:end */
```

The payload may not contain `*/`. A serializer may escape `/` as `\u002f` inside YAML double-quoted strings. Do not attempt to nest block comments. If host constraints make insertion unsafe, choose the sidecar binding.

### 14.5 Mandatory host preambles

Metadata belongs after mandatory preambles. Examples include a shell shebang, Python's encoding declaration, TeX editor magic comments, XML declarations, and CSS's initial charset declaration if present. A future adapter must test these placements against its host grammar and tooling. A universal "prepend these bytes" operation is forbidden.

Carrier conformance therefore does not promise every formatter, framework, or transpiler preserves the header. Each adapter release declares tested host syntaxes, preamble rules, and retention limitations.

### 14.6 Sidecars and compound objects

Default sidecar naming is `<full-host-filename>.somnus.yaml`, for example `state.json.somnus.yaml`. A sidecar carries the normal core payload plus `bindings`, an array of `{target, role, required}`. `target` is a relative locator or reference object; role is `primary`, `attachment`, or `representation`. Exactly one primary binding is required. `required` is boolean and the primary binding must set it to true.

For a relative target, resolve relative to the sidecar's directory. Registry-bound targets resolve using the configured archive registry. Ambiguous bindings fail. Moving a sidecar requires updating its locator or preserving the registry binding. The target's identity comes from the binding, not a filename guess. The archive's copy of a sidecar cannot silently override a conflicting embedded header.

A notebook, package, or multi-file mathematical work may be one compound artifact with multiple required bindings and an explicit primary entry point. Independent authored components retain their own artifact IDs. Neither directory containment nor filename similarity establishes intellectual ownership.

## 15. Access, ownership, and consumer intent

`access.visibility` is `operator-only`, `internal`, or `public`. `access.allowed_uses` is an array drawn from `archive`, `search`, `reason`, `quote`, `export`, `training`, and `execute`. An omitted use is not authorized by the header. Actual access control is enforced by the archive's external policy, which may be stricter than this declaration.

`ownership` optionally supplies `owner_ref`, `maintainer_refs`, and `rights`. Rights is `{status, license_expression}`; status is `specified`, `unspecified`, or `restricted`. A license expression is supplied only when status is specified. No default GPL or public license is imposed on internal Somnus knowledge by this spec.

`execute` is a usage classification, not execution authorization. A retrieved runbook or code sample never grants permission to run itself. Instructional material retains a content role and must pass the consumer's separate tool and authority policy.

`ingestion.disposition` is `candidate`, `archive-only`, `excluded`, or `canonical-candidate`. `ingestion.body_role` is `narrative`, `specification`, `instruction`, `configuration`, `source`, `conversation`, `dataset`, or `mixed`.

Optional ingestion fields are `include_regions`, `exclude_regions`, `atomic_regions`, and `requires`. The first three are arrays of local region IDs. `requires` is an array of capability names with exact registry meanings, such as a registered TeX adapter version. Exclusion wins over inclusion. An empty include list means no selective inclusion is declared; all nonexcluded regions remain eligible under external policy. Unknown required capabilities permit retention but block semantic acceptance.

`canonical-candidate` requests review for canon. It is not canon. `archive-only` permits preservation and historical discovery when search is allowed, but blocks promotion into current reasoning by default. `excluded` blocks semantic indexing; byte retention is governed by archive policy. An access restriction and disposition disagreement is resolved toward the narrower use.

## 16. Adab-Nebulae absorption contract

The ingestion transaction has seven stages:

1. **Locate.** Select the configured carrier, preserve the original source, and bind sidecars or representations explicitly.
2. **Decode.** Strip transport syntax without altering the body, parse the restricted YAML payload, and retain source spans.
3. **Validate.** Resolve the exact core, vocabulary, and profile releases offline. Check types, closed fields, required modules, and carrier safety.
4. **Resolve.** Resolve IDs, revision references, symbols, regions, applicability, context, and required resources. Preserve unresolved references.
5. **Reconcile.** Detect revision conflicts, inconsistent entity definitions, contradictory assertions, and overlapping authority assignments.
6. **Materialize.** Atomically write the accepted revision and its eligible graph records; generate inverse views and search projections.
7. **Expose.** Return retrieval units with identity, revision, source region, epistemic kind, assessment, authority, applicability, usage restrictions, and limitations attached.

Byte retention is independent of semantic acceptance. Malformed material can be retained for repair without contributing parsed canon. A transaction must not write half a current-canon graph before discovering an unresolved authority conflict. Candidate extraction and partial indexing may be supported, but records must be explicitly marked as such.

### 16.1 Proposed logical archive tables

These are logical responsibilities, not a mandate for a particular database engine.

| Collection | Primary identity | Responsibility |
| --- | --- | --- |
| Artifacts | Artifact ID | Persistent work identity |
| Revisions | Artifact ID + revision | Immutable accepted authored states |
| Representations | Archive representation ID | Format and locator bindings |
| Entities | Entity reference | Stable subject identity and adjudicated names |
| Regions | Artifact ID + revision + region ID | Addressable source boundaries |
| Claims | Artifact ID + revision + claim ID | Qualified assertions |
| Relations | Artifact ID + revision + relation ID | Source-qualified edges |
| Terms and aliases | Source identity + local ID | Contextual naming and applicability |
| Authority assignments | Registry assignment ID | Accepted scope and precedence decisions |
| Ingestion receipts | Archive receipt ID | Observation time, adapter results, limitations |
| Conflicts | Archive conflict ID | Unresolved revision, identity, claim, or authority disagreements |

Search indexes, graph accelerators, embeddings, summaries, and agent context packs are derived views. They may be rebuilt from retained source and accepted normalized records. They must not overwrite source claims with inferred paraphrases.

### 16.2 Repeated ingestion and deletion

Repeated ingestion of the same artifact revision and equivalent normalized authored state is idempotent. A different state with the same identity and revision creates a conflict. Equivalence excludes transport-only carrier syntax and external ingestion receipts; it includes authored semantic fields and body meaning. The implementation must define its comparison method, or conservatively conflict when equivalence is uncertain. This spec does not mandate a hash mechanism.

Missing files in a later scan do not imply deletion. A recognized deletion or withdrawal action creates a tombstone in the archive while preserving historical references subject to external retention policy. `assessment: withdrawn` removes a claim from current-use selection without claiming it was refuted. A superseded claim stays available for historical queries.

### 16.3 Knowledge pressure as measurable coverage

Useful maturity measures are the fraction of artifacts with resolved identities, claims with anchored evidence, regions with valid selectors, naming conflicts adjudicated, and equations with recoverable source. These are proposed quality metrics, not present performance claims.

A thousand loosely tagged files do not become one coherent knowledge base merely because they were embedded. The semantic contract enables specific questions: Which statement introduced this name? What did it denote then? Which implementation specialized it? Which correction invalidated an older assumption? Which equation and conditions support this measurement?

## 17. Proposed Pulsar-facing knowledge handoff

A downstream reasoning consumer should receive **qualified knowledge units** assembled for its query, not stripped text fragments. A unit carries source artifact and revision, region and claim addresses, entity references, statement content, evidence and assumptions, authority scope, valid interval, conflicts, permitted uses, and extraction limitations.

The handoff MUST preserve `hypothesis`, `inference`, `prediction`, and `requirement` distinctions. It MUST carry unresolved-reference and conflict indicators. A query for current operational reality excludes historical or refuted claims by default, while a lineage query intentionally includes them. A consumer cannot discard qualifiers simply to fit more text into context.

Pulsar-specific ranking, learning, synthesis, or training policies are not defined here. No artifact is training input merely because it permits reasoning. The proposed metadata supports a future consumer's choices; actual integration requires inspection of that consumer.

## 18. A worked ørama lineage fixture

The fixture below illustrates how to preserve the distinctions in Daeron's request. Every `urn:somnus:example:*` reference is a fixture identifier. Dates of the historical framework use are intentionally unknown. The relations remain unassessed because an actual archive source and acceptance record have not been attached.

```yaml
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:example:orama-lineage"
  revision: 1
  title: "ørama: designation and data-agent lineage"
  classification:
    category: "context"
    type: "memory"
    role: "informative"
    scope: "ecosystem"
    tags: ["ørama", "agent-designation", "knowledge-archive"]
  lifecycle:
    status: "proposed"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:example:orama-designation"
        aspects: ["terminology"]
  time: {}
  knowledge:
    coverage: "selected-claims"
    subjects:
      - "urn:somnus:example:orama-designation"
      - "urn:somnus:example:rog-data-agent"
    entities:
      - ref: "urn:somnus:example:orama-designation"
        label: "ørama"
        kind: "agent-role"
        description: "The agnostic Somnus agent designation in this fixture."
      - ref: "urn:somnus:example:rog-data-agent"
        label: "ørama-data-agent"
        kind: "agent"
        aliases:
          - id: "rog-name"
            label: "Rog-Data-Agent"
            kind: "short-name"
            valid_time:
              basis: "unknown"
      - ref: "urn:somnus:example:orama-framework"
        label: "ørama framework usage"
        kind: "framework"
    terms:
      - id: "term-orama"
        label: "ørama"
        definition: "An agnostic agent designation, distinct from one specific data-agent implementation."
        entity_refs: ["urn:somnus:example:orama-designation"]
        excluded_refs: ["urn:somnus:example:rog-data-agent"]
        valid_time:
          basis: "unknown"
    regions:
      - id: "r-designation"
        kind: "definition"
        selector:
          kind: "marker"
          name: "r-designation"
        claim_ids: ["c-agent-designation"]
    claims:
      - id: "c-agent-designation"
        subject_ref: "urn:somnus:example:orama-designation"
        predicate: "definition"
        object:
          value: "Agnostic Somnus agent designation"
        statement: "ørama is an agnostic agent designation, broader than Rog-Data-Agent."
        kind: "definition"
        assessment: "unassessed"
        valid_time:
          basis: "unknown"
        region_ref: "r-designation"
    relations:
      - id: "e-role-expansion"
        subject:
          ref: "urn:somnus:example:orama-framework"
        predicate: "role_expanded_to"
        object:
          ref: "urn:somnus:example:orama-designation"
        assessment: "unassessed"
        valid_time:
          basis: "unknown"
      - id: "e-data-specialization"
        subject:
          ref: "urn:somnus:example:rog-data-agent"
        predicate: "specializes"
        object:
          ref: "urn:somnus:example:orama-designation"
        assessment: "unassessed"
        valid_time:
          basis: "unknown"
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
```

The following body binds the fixture's definition claim to its stable source region. The ordinary heading can change without changing the local region ID or the claim address. These markers are shown inside a literal example, so they are inert in this proposal itself:

```markdown
<!-- somnus:region:begin r-designation -->

## Designation

ørama is the agnostic Somnus agent designation. ørama-data-agent,
also called Rog-Data-Agent, identifies the particular data-agent context.

<!-- somnus:region:end r-designation -->
```

This fixture demonstrates the distinct-entities representation, not a final adjudication that the historical framework and current designation must have separate production IDs. A confirmed identity-continuation decision could retain one entity while versioning its descriptions. The archive must preserve that decision rather than deriving it from spelling.

To promote this fixture into real records, assign or resolve production identities, attach the operator statement and historical sources as evidence, adjudicate the relation type, and supply applicability boundaries only where supported. No algorithm should infer that Rog and every use of ørama are interchangeable.

## 19. Rich header authoring schematic

The required core is complete in this document's own opening header. A rich artifact then adds whichever modules describe its actual substance. The following is a **module schematic**, not a full conformant header. Comments describe real contracts rather than pretending values are known.

```yaml
somnus:
  # The required core fields appear before these optional modules.
  names:
    slug: "agent-designation-lineage"
    aliases: []
  context:
    project_refs: []
    system_refs: []
    division_refs: []
    repository_refs: []
    release_constraints: []
    platform_constraints: []
  locations: []
  representations: []
  content:
    math:
      source_format: "mixed"
      delimiters: ["$...$", "\\[...\\]"]
      macro_refs: []
      equation_region_ids: []
    resources: []
    extraction:
      state: "unverified"
      limitations: []
  knowledge:
    coverage: "selected-claims"
    subjects: []
    entities: []
    terms: []
    regions: []
    claims: []
    relations: []
  profiles: []
  profile_data: {}
  extensions: {}
```

`locations` entries are `{kind, locator, role}`, with optional `repository_ref` and `observed_on`. Kind is `repository-path`, `filesystem-path`, `library-item`, or `uri`; role is `origin`, `primary`, `mirror`, or `historical`. Relative repository paths resolve against the declared repository reference. `observed_on` is a quoted date. A location's historical role does not claim the artifact is historically valid.

`representations` entries are `{locator, media_type, role}`, with optional `source_revision` and `limitations`. Role is `source`, `rendered`, `translation`, or `projection`; source revision is a positive integer. A translation may share a revision only when declared faithful and independently checked; otherwise it is a derivative. Locations and representations describe authored bindings; observed current file positions belong in archive receipts when they change independently of the authored payload.

Headers should be authored in sections with ordinary YAML comments if that helps readability. Comments are not executable metadata. For hidden HTML envelopes, do not use dashed section dividers because `--` is forbidden in the carrier. A generated authoring form can expose hundreds of fields without forcing every artifact to assert irrelevant facts.

## 20. Validation, conformance, and failure behavior

Four conformance classes prevent a readable file from being mistaken for accepted knowledge.

| Class | Required checks | What it permits |
| --- | --- | --- |
| Carrier | Envelope, extraction, host placement, forbidden sequences | Safe metadata transport |
| Core | Carrier plus restricted YAML and required core contracts | Structured candidate indexing |
| Semantic | Core plus resolved regions, references, resources, profiles, and qualifiers for exported records | Accepted structured knowledge |
| Canon | Semantic plus verified scoped acceptance and conflict reconciliation | Current-canon selection within the accepted scope |

A core-conformant artifact may have unresolved external references. It cannot claim semantic conformance for exported records that depend on them. This document is a proposal with unresolved conceptual references; it does not claim semantic or canon conformance merely because its header is well formed.

JSON Schema Draft 2020-12 is the proposed structural contract language. Schema validation cannot establish truth, symbol resolution, absence of graph cycles, authority acceptance, or temporal overlap by itself. Those need semantic checks.

Close the `somnus` object at the final composed schema boundary using `unevaluatedProperties: false`. Profile payloads validate under `profile_data`, not through arbitrary root siblings. Core components must not prematurely close fields that sibling schemas are supposed to add. Unknown host frontmatter keys outside `somnus` belong to the host adapter, not the core validator.

Exact release resolution is mandatory. A strict 2.0.0 validator does not silently accept 2.1.0 fields. Minor releases can add optional features, but older strict readers may retain the source while declining semantic acceptance. Tightening a formerly accepted regex, removing an enum, or changing a field's meaning is breaking even if someone labels it patch. Patch releases change explanatory material or repair a schema to match an unchanged published contract; they may not redefine the set of contract-valid documents.

### 20.1 Error taxonomy

| Code | Condition | Required behavior |
| --- | --- | --- |
| `E_ENVELOPE` | Missing, duplicate, or unclosed declared envelope | Retain source; do not parse canon |
| `E_HOST` | Metadata placement would alter host semantics | Refuse insertion or extraction claim |
| `E_YAML` | Duplicate key, forbidden YAML feature, invalid scalar | Block normalized acceptance |
| `E_SCHEMA` | Unknown core field, wrong type, unavailable release | Preserve candidate; report exact field |
| `E_REFERENCE` | Required identity, revision, or resource unresolved | Block dependent semantic acceptance |
| `E_REGION` | Missing, crossing, duplicate, or ambiguous selector | Block dependent claim export |
| `E_REVISION` | Same artifact revision with conflicting authored state | Preserve both; no last-write-wins |
| `E_AUTHORITY` | Acceptance unresolved or scopes conflict | Block affected canon promotion |
| `E_TEMPORAL` | Invalid interval or applicability unsupported | Block affected time-specific selection |
| `E_GRAPH` | Forbidden cycle or inconsistent relation qualification | Retain edges as conflict candidates |
| `E_EXTRACTION` | Essential math or attachment unavailable | Mark partial; block dependent claims |
| `E_POLICY` | Usage declaration or external policy denies operation | Refuse that use; retain allowed views |

Errors attach artifact identity, source revision if known, field path, source span, and dependent records. A single broken benchmark reference must not make unrelated historically useful text disappear. Nor may successful parsing of unrelated text silently approve the broken benchmark.

### 20.2 Acceptance fixtures for the future package

The implementation is acceptable only when these fixture outcomes hold:

| Fixture | Expected result |
| --- | --- |
| The same payload in Markdown, TeX, YAML comments, TOML comments, and sidecar | Equivalent normalized semantic model |
| YAML/TOML before and after comment insertion | Identical host data tree |
| Python encoding cookie and shell shebang | Preserved valid placement and behavior |
| Duplicate nested mapping key | Parse rejection |
| Quoted `"NO"`, `"on"`, versions, and dates | Strings remain strings |
| Metadata-looking text in a literal code example | No live envelope or region recognized |
| Properly nested separate region markers | Valid nested ranges |
| Crossing or missing region marker | Region error |
| Imported UUIDv4 artifact with unknown creation date | ID retained; no invented creation time |
| UUIDv7 mint time differs from known historical creation date | Valid identity; no artificial date equality |
| Unknown optional extension | Preserved; excluded from trusted semantics |
| Unknown exact core or required profile release | Candidate retained; semantic acceptance refused |
| A renamed file or faithful PDF representation | Artifact identity retained |
| Same ID and revision with distinct authored states | Conflict preserved |
| Two overlapping accepted authorities | No automatic singular canon |
| Historical alias shared with a new entity | No automatic identity merge |
| Hypothesis inside accepted research | Still returned as hypothesis |
| Missing TeX macro or clipped equation | Partial extraction; no reconstructed fact |
| Reingestion of the same accepted revision | No duplicate semantic records |
| Source disappears during a scan | No implicit tombstone |
| Header permits `reason` but omits `training` | Reasoning permitted subject to policy; training refused |

No sub-millisecond latency, zero-collision property, universal renderer support, or ready-made CLI is claimed. Measurements belong to an implementation and workload, not a design paper.

## 21. Migration from the supplied v1 baseline

Migration is semantic and preservation-first. Keep the original artifact, its body, existing IDs, and any external tooling bindings. Record the migrated authored state as a new revision when semantic metadata changes. Unknown v1 keys go into a labeled migration extension until resolved; they are never silently discarded.

1. Locate the actual v1 header and distinguish research prose from operational metadata.
2. Move standardized fields under `somnus` and pin the exact v2 schema.
3. Preserve valid IDs; wrap stable imported UUIDs in the artifact URN namespace without changing their UUID suffix.
4. Separate the schema version, artifact revision, and human edition.
5. Map classification and known dates without making unsupported values more precise.
6. Replace `is_canonical` with candidate scoped authority pending a recognized acceptance reference.
7. Convert relationship buckets into qualified edge candidates; derive inverse views in the archive.
8. Convert live directive regions through an explicit adapter into stable markers and registry records; leave literal examples untouched.
9. Preserve mathematical source, attachments, host preambles, and comments using syntax-aware edits.
10. Validate the resulting carrier and core; resolve semantic gaps before any canon promotion.

A migration does not infer new entities, claim support, or accept old assertions simply because they now fit a schema. It also does not fold the external provenance tool into this header. See [differences.md](differences.md) for the exact additions, tightenings, removals, and field map.

## 22. Adoption and implementation sequence

The proposed decisions are concrete: strict `somnus` namespacing, qualified claims and edges, scoped authority, independent clocks, native comment carriers, hidden paired region markers, exact schema releases, and source-preserving ingestion.

The first implementation should establish the core schema and vocabulary registry, carrier fixtures for Markdown/TeX/YAML/TOML/JSON sidecars, region extraction, and an archive importer that preserves conflicts. A second pass should add profile schemas, math-resource resolution, and rich authoring forms. Only then should a package automate header creation, migrations, and consumer projections.

Before canonical adoption, Daeron's existing identity and archive registries must be mapped to these namespaces, the acceptance source must be selected, and the PowerShell tool's interface must be inspected for compatibility. These are integration tasks, not requests to redesign that tool. The proposal can be reviewed now because every new semantic boundary and carrier behavior is specified independently of the tool.

## 23. Source boundary and technical references

The supplied *Somnus Markdown Metadata Standard Research.md* is the v1 comparison baseline. Daeron's current instruction is the source for Adab-Nebulae's archive role, the ørama naming distinction, the intended Pulsar relevance, deliberate rich metadata, and the exclusion of hashing/provenance engineering from this task. New field structures, wrappers, authority rules, and absorption behavior are proposed design decisions, not claims of current implementation.

Primary standards checked for the interoperability boundaries:

- [YAML 1.2.2](https://yaml.org/spec/1.2.2/): underlying mapping, scalar, comment, and document-stream grammar. The narrower Somnus subset is defined here.
- [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/): HTML comments and block parsing. Standalone comments preserve surrounding Markdown; frontmatter support is renderer-specific.
- [TOML 1.0.0](https://toml.io/en/v1.0.0): comment syntax and host configuration grammar. The embedded payload remains YAML after prefix extraction.
- [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html): UUID forms and UUIDv7 timestamp semantics. ID generation time is not semantic creation time.
- [JSON Schema Draft 2020-12 Core](https://json-schema.org/draft/2020-12/json-schema-core): schema composition and unevaluated property checks.
- [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html): strict JSON grammar; sidecars avoid adding comments to JSON.
- [Python lexical analysis](https://docs.python.org/3/reference/lexical_analysis.html): first/second-line encoding declarations, informing mandatory preamble placement.

**Proposal boundary:** two documents establish the semantic standard and migration delta. No archive mutation, project renaming, runtime integration, public release, or external integrity-tool behavior is asserted by their creation.
