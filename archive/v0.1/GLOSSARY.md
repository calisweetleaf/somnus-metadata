# SOMNUS METADATA — GLOSSARY (NORMATIVE DEFINITIONS)

```text
DOCUMENT TITLE:  Somnus Metadata Glossary
Classification:  INTERNAL
Version:         0.1.0
Date:            2026-09-22
Author/Origin:   defense-grade-doc-engine (derived from Somnus Markdown Metadata
                 Standard Research.md)
Status:          PROPOSED
```

> Definitions in this file are normative for `SOMNUS-METADATA-SPEC-v0.1.md`.
> Where a definition conflicts with a specification section, the section governs
> for its scope and the conflict MUST be logged as `TODO(needs-owner)`.

## Authority and Conventions

- Terms are listed alphabetically within groups. Each entry states the term, the
  normative definition, and where applicable the specification section that
  constrains it.
- RFC 2119 keywords apply as in the parent specification.
- Value vocabularies (e.g., the eight lifecycle states) are defined here and
  constrained in the specification; this file does not duplicate constraint tables.

## Core Provenance Terms (W3C PROV-O / SPDX 3.0 Adapted)

**Activity**
A dynamic process or transformation that generates, alters, or consumes an Entity,
executed by an Agent. Examples: authoring, verification runs, migration.
(Spec Section 9.)

**Agent**
An autonomous actor — person, organization, or software runtime — bearing
responsibility for an Activity. Subsumes Author, Operator, Model/Provider, Tool,
and Verifier roles when used generically. (Spec Section 9.2.)

**Author (Creator)**
The intellectual originator responsible for the content of an artifact. Recorded in
`provenance.authors` with `role: "author"`. Distinct from the Operator who executes
a session and the Model that generates text. (Spec Section 9.2.)

**Entity**
Any physical, digital, or conceptual artifact: a specification, code module,
benchmark run, or document version. In Somnus metadata, the Markdown document
identified by `id` is the primary Entity. (Spec Section 9.)

**Model / Provider**
The specific machine-intelligence runtime, including provider namespace and model
release identifier (research illustration: `anthropic/claude-3-7-sonnet`).
Recorded on operator entries to preserve runtime provenance. (Spec Section 9.2.)

**Operator**
The immediate physical or synthetic actor executing a session or modification
(e.g., an engineer directing an IDE, or an autonomous repository agent in a
background container). Recorded in `provenance.operators` with the directing
principal in the `operator` field for delegation chains (`actedOnBehalfOf`
semantics). (Spec Section 9.2.)

**Tool**
The client software, script, or environment mediating a write operation
(research illustration: `Somnus-Author/1.2.0`). Distinct from Model (runtime)
and Operator (director). (Spec Section 9.2.)

**Verifier (Reviewer)**
An independent entity certifying technical correctness, formal safety, or
normative compliance without necessarily mutating text. Recorded in
`provenance.verification`. (Spec Sections 9.2, 9.4.)

**Provenance**
The record of agency over an artifact: who originated, executed, and certified
each state, under which runtime and tooling. Tier 1 (frontmatter summary) is
REQUIRED; Tier 2 (external ledger) carries full history. (Spec Section 9.)

**Ledger (History Ledger)**
The Tier 2 external event store referenced by `provenance.history_ledger`,
carrying the ordered granular edit/verification history offloaded from the
frontmatter. Backing format and location are `TODO(needs-owner)`. (Spec Section 9.)

## Document Model Terms

**Frontmatter**
The `---`-delimited YAML 1.2 block at the head of a Markdown document carrying
the Somnus metadata envelope. Parsed strictly before any schema validation.
(Spec Sections 5, 14, 17.1.)

**Core (Somnus Core)**
The mandatory base schema: identity, classification, lifecycle, temporal markers,
location, origin, base provenance, relations envelope. Referenced as
`somnus://core/v1` (illustrative authority). (Spec Section 12.1.)

**Profile**
A specialized schema extension keyed to `classification.type` that constrains a
single top-level profile block (e.g., `specification`, `benchmark`). Composed over
Core via JSON Schema Draft 2020-12 `allOf` with `unevaluatedProperties: false`.
Named by `classification.profile`. (Spec Section 12.)

**Submatter**
Machine-readable metadata attached to a localized body region (invariant,
decision, hypothesis, evidence, archive). Implemented exclusively as Generic
Container Directives in v0.1. Addressable by `id`-anchored fence search.
(Spec Section 13.)

**Directive (Container Directive)**
The `:::`-fenced block syntax per remark-directive / mdast-util-directive,
form `:::submatter:<type>{attr="value" ...}` … `:::`, with nesting by
fence-length increment. A first-class AST parent node. (Spec Section 13.)

**Extension (`extensions`)**
The OPTIONAL open root mapping confining experimental metadata. Content inside
MUST NOT affect Core/Profile conformance verdicts. Promotion into Core or a
Profile REQUIRES a schema revision. (Spec Section 12.4.)

**Conformance (C1 / C2 / C3)**
C1 Core-Wellformed (parses); C2 Profile-Conformant (validates against Core plus
named Profile; minimum for conformance claims); C3 Graph-Consistent (referential
and lifecycle guards hold; REQUIRED for canonical claims). (Spec Section 2.)

**DAG (Directed Acyclic Graph)**
The constraint on lineage relation families (`supersedes`, `derived_from`,
`continues`, `has_version` and inverses): edges MUST NOT form cycles. `cites`
and `complements` families are exempt. (Spec Section 10.3.)

**Inverse Semantics**
The pairing discipline requiring each forward relation to have a resolvable
reverse pointer (e.g., `supersedes` ⇔ `superseded_by`), maintained by tooling
or validated at Stage 3. (Spec Section 10.2.)

## Identity and Placement Terms

**Identity (`id`)**
The immutable RFC 9562 UUIDv7 primary key of an artifact, 36-character
hex-and-dash form. Stable across renames, moves, and transfers. (Spec Section 11.1.)

**Slug**
A REQUIRED kebab-case human-readable alias (e.g., `consensus-safety-invariants`).
Convenience only; MUST NOT be used for machine references. (Spec Section 11.2.)

**Alias**
An OPTIONAL kebab-case alternate name listed in `aliases`. Same non-authoritative
standing as `slug`. (Spec Section 11.2.)

**Location**
The transient physical placement of an artifact: `repository`, `repository_root`,
`path`, `historical_paths`. Updated on moves without altering `id`.
(Spec Section 11.3.)

**Origin**
The immutable birth placement: `repository`, `path`, `initial_commit`.
Recorded once at creation. (Spec Section 11.3.)

**Canonical**
The authority claim `lifecycle.is_canonical: true`: the document asserts binding
single-source-of-truth standing for its scope and type. Orthogonal to lifecycle
status; REQUIRES C3. (Spec Sections 8.1, 8.5.)

## Classification Terms

**Category**
Broad institutional domain. Closed enum:
`research`, `engineering`, `operations`, `governance`, `context`, `archive`.
(Spec Section 6.2.)

**Type**
Structural genre binding a document to its enforcing Profile. Closed enum of 14
values (`whitepaper` … `memory`). Completeness is `TODO(needs-owner)`.
(Spec Section 6.2.)

**Subtype**
OPTIONAL kebab-case specialization of `type` that MUST NOT smuggle a new genre.
Pattern `^[a-z0-9]+(-[a-z0-9]+)*$`. (Spec Section 6.4.)

**Role**
Authority tier and epistemic intent. Closed enum: `normative`, `informative`,
`working`, `exploratory`, `historical`. (Spec Section 6.2.)

**Scope**
Governed system boundary, narrow to wide: `component`, `module`, `subsystem`,
`repository`, `fleet`, `ecosystem`. (Spec Section 6.2.)

**Tags**
Open discovery keywords, kebab-case array. MUST NOT encode state, role, or scope.
(Spec Section 6.4.)

## Lifecycle Terms

**Draft**
Incomplete work; consistency not guaranteed. Entry state of the state machine.
(Spec Sections 8.2–8.4.)

**Provisional**
Complete and coherent; awaiting formal verification or review. (Spec Section 8.2.)

**Active**
Formally accepted, operational, actively maintained. (Spec Section 8.2.)

**Experimental**
Exploratory alternative; explicitly non-binding. `is_canonical` MUST be `false`.
(Spec Section 8.2.)

**Superseded**
Replaced by a newer artifact; retained for lineage. REQUIRES non-empty
`relations.superseded_by`. (Spec Section 8.2.)

**Deprecated**
Phase-out announced; use discouraged; no direct replacement asserted.
(Spec Section 8.2.)

**Historical**
Former active state preserved strictly for archival reference. (Spec Section 8.2.)

**Archived**
Cold storage; immutable; exempt from ongoing validation except C1. Terminal state;
re-activation REQUIRES a new-identity successor. (Spec Sections 8.2–8.4.)

## Relation Terms

**Relation**
A typed directed edge from one artifact identifier to another, grouped in named
`relations` lists (`supersedes`, `derived_from`, `cites`, `complements`,
`continues`, `describes`, `has_version` families and inverses). Lineage families
are acyclic; citation/complement families MAY cycle. (Spec Section 10.)

**Supersession**
The replacement edge (`supersedes` / `superseded_by`) with lifecycle coupling:
`superseded` status REQUIRES a target. (Spec Sections 8.4, 10.2.)

## Schema and Syntax Terms

**JSON Schema Draft 2020-12**
The schema language for Core and Profiles. Composition uses `allOf`; closure uses
`unevaluatedProperties: false` at the composition root. (Spec Section 12.2.)

**YAML 1.2 Core Schema**
The required frontmatter parsing discipline. All version, status, and date scalars
MUST be quoted strings; tabs and duplicate keys are errors. (Spec Section 14.)

**SemVer (Semantic Versioning 2.0.0)**
The schema-evolution discipline: PATCH (non-breaking fixes), MINOR (additive
optional), MAJOR (breaking; migration REQUIRED). Declared per document in
`somnus.version`. (Spec Section 15.)
