# **Somnus Markdown Metadata Standard: Architectural Investigation for Frontmatter, Submatter, and Document Profiles**

## **Existing Relevant Standards and Architectural Precedents**

Establishing a resilient metadata foundation for Markdown artifacts within an AI-integrated, local-first engineering and research ecosystem requires analyzing the mechanisms of established data-modeling specifications, static-site generators, and schema formalisms. Rather than constructing ad hoc frontmatter conventions, the Somnus project can extract proven structural patterns from standards that have addressed multi-agent attribution, fine-grained citation graphs, and format interoperability.

### **Dublin Core and Schema.org**

The Dublin Core Metadata Element Set (ISO 15836\) established fifteen elemental properties for resource description: Title, Creator, Subject, Description, Publisher, Contributor, Date, Type, Format, Identifier, Source, Language, Relation, Coverage, and Rights. Dublin Core demonstrated that resource metadata must enforce orthogonality: descriptive properties remain decoupled from physical storage formats, and elements remain repeatable and optional. However, Simple Dublin Core lacked typed relationships, which prompted the emergence of Qualified Dublin Core to introduce structural refinements such as isVersionOf, replaces, and isReplacedBy.

Schema.org adapted these primitives to web-scale discovery by framing metadata in hierarchical class lattices (such as Thing \\rightarrow CreativeWork \\rightarrow Article \\rightarrow TechArticle). Schema.org demonstrates that document classes share fundamental properties—such as name, dateCreated, and author—while sub-classes append domain-specific fields. For Somnus, this hierarchy indicates that document classification cannot remain a passive reporting label; declaring a document type must instantiate a verifiable contract of properties and constraints.

### **W3C PROV and PROV-O**

The W3C Provenance Incubator Group codified a domain-agnostic provenance framework in the PROV Data Model (PROV-DM) and its Web Ontology Language mapping (PROV-O). PROV structures provenance around three foundational concepts:

> * **Entity**: Any physical, digital, or conceptual artifact (such as a specification, code module, or benchmark run).  
> * **Activity**: Dynamic processes or transformations that generate, alter, or consume entities.  
> * **Agent**: Autonomous actors—people, organizations, or software runtimes—bearing responsibility for an activity.

PROV-O models the causal relationships between these nodes using precise relational predicates:

> * wasGeneratedBy: Connects an Entity to the originating Activity.  
> * wasDerivedFrom: Establishes lineage between an Entity and an antecedent Entity.  
> * wasAttributedTo: Associates an Entity directly with an Agent.  
> * wasAssociatedWith: Identifies the Agent executing an Activity.  
> * actedOnBehalfOf: Models delegation chains, tracking human operators commanding synthetic agents.

When applied to an ecosystem where frontier artificial intelligence models synthesize, revise, and verify documentation, PROV demonstrates that collapsing human writers, LLM runtimes, and local toolchains into an undifferentiated author string strips away operational accountability. Somnus requires structural separation between intellectual authorship, runtime execution, and validating tooling.

### **DataCite Metadata Schema**

The DataCite Metadata Schema (versions 4.4 and 4.5) was engineered to ensure persistent identifiability and lineage tracking for scientific datasets, technical reports, and research software. A central innovation of DataCite is the relationType vocabulary within the RelatedIdentifier property group, which formalizes bidirectional dependency tracking using strictly paired inverse verbs:

> * IsVersionOf and HasVersion  
> * IsNewVersionOf and IsPreviousVersionOf  
> * IsSupplementTo and IsSupplementedBy  
> * Continues and IsContinuedBy  
> * Describes and IsDescribedBy  
> * HasMetadata and IsMetadataFor  
> * IsDerivedFrom (lineage synthesis)  
> * Collects and IsCollectedBy

DataCite demonstrates that relational integrity degrades if relationship types remain open-ended text strings. Enforcing an explicit enum of bidirectional relations ensures that repository indexers can construct global directed acyclic graphs (DAGs) across decentralized files without semantic drift.

### **SPDX 3.0**

The System Package Data Exchange (SPDX) 3.0 specification extends Software Bill of Materials (SBOM) standards to encompass artificial intelligence pipelines, training datasets, and build artifacts. SPDX 3.0 decouples an artifact from its metadata envelope through the CreationInfo construct. Within CreationInfo, SPDX isolates three independent variables:

> * createdBy: The primary Agent (individual or corporate entity) responsible for the element.  
> * createdUsing: The software tools, automated compilers, or AI model runtimes leveraged during construction.  
> * created: The canonical timestamp of serialization.

This separation directly resolves an ongoing challenge in multi-agent authoring: an engineer can act as the initiating operator while an LLM agent executes generation through an orchestration harness. Recording these as distinct properties preserves both intellectual direction and technical provenance.

### **Architecture Decision Records and Docs-as-Code**

Architecture Decision Records (ADRs) establish lightweight, text-based conventions for tracking system evolution. ADRs enforce strict, immutable lifecycle states (Proposed, Accepted, Superseded, Deprecated, Rejected) coupled with explicit supersession pointers (Supersedes ADR-0004, Superseded by ADR-0012). Docs-as-code implementations incorporate these patterns into Git-managed Markdown repositories. Static-site generators (such as Jekyll, Hugo, and Astro) manage metadata through YAML frontmatter blocks, while personal knowledge graphs (such as Obsidian) popularize wikilinks (\[\[target\]\]) and block-level references (^block-id).

However, tools like Hugo and Obsidian leave frontmatter schemas largely unconstrained. Keys are added arbitrarily, and schema enforcement is delegated to custom display templates. Somnus requires the fluidity of Markdown combined with the schema enforcement found in compiler-driven software engineering.

## **Core Metadata Dimensions for Somnus**

A universal metadata foundation must define the minimum orthogonal dimensions required to identify, evaluate, position, and govern any artifact across the Somnus repository, regardless of whether it represents an informal notepad, an architectural specification, or an automated benchmark run.

| Dimension | Primary Objective | Key Semantic Fields | Cardinality & Mutability |
| :---- | :---- | :---- | :---- |
| **Schema & Validation** | Declares schema profile and version for machine validation | schema, profile, version | Exactly 1; Immutable per schema version |
| **Stable Identity** | Provides location-independent persistent identification | id, slug, aliases | Exactly 1 id (Immutable); aliases optional |
| **Human Identity** | Provides human-readable titles and summaries | title, description, purpose | Exactly 1 title; description and purpose recommended |
| **Classification** | Situates artifact in taxonomy and sets profile rules | category, type, subtype, tags, role, scope | Structured mapping; category and type mandatory |
| **Lifecycle & State** | Tracks semantic status and temporal validity | status, is\_canonical, stage | Exactly 1 status; state transitions controlled |
| **Temporal Record** | Tracks wall-clock creation and semantic modification | created\_at, updated\_at, verified\_at | Timestamps strictly formatted in ISO 8601 UTC |
| **Spatial & Location** | Captures spatial lineage across repositories and paths | origin (path, repo), location (path, repo) | Mandatory tracking of original vs. current path |
| **Lineage & Graph** | Encodes directional dependency and supersession links | relations (supersedes, derived\_from, cites) | Optional array of qualified identifier references |
| **Actors & Provenance** | Distinguishes creators, editors, models, and tools | authors, operators, attributions | Mandatory authors; incremental operator logging |

### **Analysis of Semantic Necessity**

These nine dimensions represent mutually exclusive, non-overlapping projections of an artifact's operational lifecycle:

> * Identity addresses persistence across file renames, movements, and network transfers.  
> * Classification governs schema compilation and validator routing.  
> * Lifecycle dictates whether autonomous agents may trust assertions contained in the file as current system reality.  
> * Spatial semantics record repository topography, preventing synchronization collisions across mirrors and forks.  
> * Lineage tracks the directional evolution of ideas, tracing how proposals transform into implementations.  
> * Provenance tracks agency, establishing accountability across human engineers and synthetic model sessions.

Collapsing these orthogonal dimensions—such as encoding the document lifecycle into a directory path (docs/archived/spec.md) or embedding classification into an identifier (RFC-0012)—creates severe fragility. Renaming the directory or reclassifying the artifact invalidates existing relational links throughout the repository.

## **Recommended Taxonomy Architecture**

A pervasive anti-pattern in metadata engineering is the unconstrained flat taxonomy, where diverse semantic concepts are merged into a single category list (e.g., category: \[whitepaper, draft, security, v1, urgent\]). This conflates document genres, lifecycle states, topical themes, and organizational domains, forcing downstream consumers to apply speculative heuristic filters.

### **Hierarchical Classification Schema**

To prevent classification degradation, Somnus must separate organizational domain, structural artifact class, architectural scope, and open indexing into dedicated structural keys.

`classification:`  
&nbsp;&nbsp;`category: engineering`  
&nbsp;&nbsp;`type: architecture-record`  
&nbsp;&nbsp;`subtype: consensus-protocol`  
&nbsp;&nbsp;`profile: "somnus://profiles/engineering/architecture-record/v1"`  
&nbsp;&nbsp;`role: normative`  
&nbsp;&nbsp;`scope: subsystem`  
&nbsp;&nbsp;`tags:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- distributed-systems`  
&nbsp;&nbsp;&nbsp;&nbsp;`- p2p`  
&nbsp;&nbsp;&nbsp;&nbsp;`- rafter`

*Evidence-Supported Recommendation*: The fields within classification serve distinct operational functions:

> * **category**: Defines the broad institutional domain or operational sphere in which the document exists.  
> * **type**: Identifies the structural genre of the artifact, acting as the deterministic key that binds the document to an enforcing JSON Schema profile.  
> * **subtype**: Provides domain-specific specialization of the parent type without proliferating distinct schema files.  
> * **profile**: An absolute URI pointing directly to the versioned schema that validates the document’s profile-specific block.  
> * **role**: Specifies the authority tier and epistemic intent of the text, distinguishing binding technical rules from speculative thinking.  
> * **scope**: Defines the blast radius or system boundary governed by the artifact.  
> * **tags**: An open-ended array reserved for free-text search indexing, keyword discovery, and cross-cutting conceptual groups.

### **Controlled versus Open Vocabularies**

Fields governing programmatic routing, validation, and security boundaries must be strictly constrained to closed, enumerated vocabularies. Conversely, discovery keywords must remain unconstrained:

| Classification Field | Grammar Rule | Vocabulary Domain / Allowed Values | Validation Enforcement |
| :---- | :---- | :---- | :---- |
| **category** | Closed Enum | research, engineering, operations, governance, context, archive | Rejection on unlisted values |
| **type** | Closed Enum | whitepaper, specification, architecture-record, report, task, plan, notepad, benchmark, test-result, decision-record, runbook, index, state, memory | Rejection on unlisted values |
| **role** | Closed Enum | normative, informative, working, exploratory, historical | Rejection on unlisted values |
| **scope** | Closed Enum | ecosystem, fleet, repository, subsystem, module, component | Rejection on unlisted values |
| **subtype** | Open Regex Pattern | Lowercase kebab-case string (^\[a-z0-9\]+(-\[a-z0-9\]+)\*$) | Validated via regular expression |
| **profile** | URI / URN | Valid URI pattern (^somnus://profiles/\[a-z0-9/-\]+$) | Validated via URI schema resolution |
| **tags** | Open Array | Array of kebab-case strings (^\[a-z0-9\]+(-\[a-z0-9\]+)\*$) | Validated against string formatting rules |

## **Provenance and Operator Modeling**

Technical artifacts in the Somnus ecosystem are generated, edited, refined, and verified by combinations of human engineers, autonomous CI systems, and frontier language models. Capturing this collaborative lifecycle requires a structured provenance grammar.

### **Actor Disambiguation**

Adapting W3C PROV-O and SPDX 3.0 to Markdown metadata requires distinguishing between creative origination, direct system interaction, and runtime tooling:

> * **Author / Creator**: The intellectual originator responsible for the content of the artifact.  
> * **Operator**: The immediate physical or synthetic actor executing a given session or modification (e.g., an engineer directing an IDE, or an autonomous repository agent running in a background container).  
> * **Model / Provider**: The specific machine intelligence runtime, including provider namespace and model release identifier (e.g., anthropic/claude-3-7-sonnet, openai/o3-mini).  
> * **Tool**: The client software, script, or environment mediating the write operation (e.g., Somnus-CLI/0.4.1, Neovim/0.10).  
> * **Verifier / Reviewer**: An independent entity certifying the technical correctness, formal safety, or normative compliance of the artifact.

### **Controlled Vocabulary for Interaction Actions**

Actions recorded within document provenance blocks must be restricted to a normalized vocabulary to allow deterministic filtering:

> * authored: Initial human or primary creative creation of the document content.  
> * generated: Initial synthetic production of content via an automated agent or LLM.  
> * edited: Incremental structural or semantic modification of text and metadata.  
> * reviewed: Formal human or automated inspection without direct text mutation.  
> * verified: Cryptographic, empirical, or deterministic verification of assertions (such as running test suites or checking proofs).  
> * tested: Execution of attached benchmarks or verification suites.  
> * migrated: Translocation, format re-encoding, or relocation across repository boundaries.  
> * reformatted: Non-semantic adjustments, such as whitespace normalization or frontmatter realignment.  
> * canonized: Formal administrative elevation of document status to normative authority.  
> * deprecated: Administrative transition marking the artifact as superseded or obsolete.

### **Balanced Provenance Header Design**

*Architectural Inference*: Recording an unbounded history of every microscopic edit inside a Git-tracked Markdown frontmatter generates merge conflicts, inflates token overhead during AI context window ingestion, and duplicates information natively managed by Git.

Somnus should therefore adopt a **Two-Tier Provenance Model**: frontmatter retains the immutable origin, current operational state, and latest verification signature, while granular edit-by-edit histories are offloaded to an external ledger referenced by path or ID.

`provenance:`  
&nbsp;&nbsp;`created_by:`  
&nbsp;&nbsp;&nbsp;&nbsp;`name: "Dr. Eleanor Vance"`  
&nbsp;&nbsp;&nbsp;&nbsp;`id: "user:vance@somnus.org"`  
&nbsp;&nbsp;&nbsp;&nbsp;`role: author`  
&nbsp;&nbsp;`created_with:`  
&nbsp;&nbsp;&nbsp;&nbsp;`tool: "Somnus-Author/1.2.0"`  
&nbsp;&nbsp;`last_modified_by:`  
&nbsp;&nbsp;&nbsp;&nbsp;`name: "Somnus Agent Worker"`  
&nbsp;&nbsp;&nbsp;&nbsp;`id: "agent:somnus-autodoc-04"`  
&nbsp;&nbsp;&nbsp;&nbsp;`role: editor`  
&nbsp;&nbsp;&nbsp;&nbsp;`model: "anthropic/claude-3-7-sonnet"`  
&nbsp;&nbsp;&nbsp;&nbsp;`operator: "user:vance@somnus.org"`  
&nbsp;&nbsp;`verification:`  
&nbsp;&nbsp;&nbsp;&nbsp;`verified_by: "system:somnus-core-ci"`  
&nbsp;&nbsp;&nbsp;&nbsp;`verified_at: "2026-03-30T14:22:01Z"`  
&nbsp;&nbsp;&nbsp;&nbsp;`status: passed`  
&nbsp;&nbsp;`history_ledger: "provenance/ledger/2026-03-30-0195e34a.json"`

For transient working environments or multi-agent handoffs prior to repository commit, an optional transient\_events array can be populated inline. Repository pre-commit hooks can then automatically flush these entries into the external ledger file, maintaining a lean frontmatter footprint.

## **Lifecycle, Currentness, and Supersession Semantics**

Boolean flags such as is-current: true fail to capture technical document lifecycles. A document may be formally canonical while undergoing an experimental revision; alternatively, an active working draft is not yet canonical, yet it is currently valid and active.

### **Separation of Lifecycle Status and Canonical Authority**

*Evidence-Supported Recommendation*: Somnus must model lifecycle maturity and canonical authority as orthogonal properties:

> * **status (Workflow Maturity)**: The operational phase of the document within the repository.  
  * draft: Incomplete work; internal consistency is not guaranteed.  
  * provisional: Complete and coherent, but awaiting formal verification or review.  
  * active: Formally accepted, operational, and actively maintained.  
  * experimental: Exploring alternative designs; explicitly non-binding.  
  * superseded: Replaced by a newer artifact; retained for historical lineage.  
  * deprecated: Phase-out announced; use is discouraged; no direct replacement.  
  * historical: Former active state; preserved strictly for archival reference.  
  * archived: Cold storage; immutable; exempt from ongoing validation.  
> * **is\_canonical (Authority Level)**: A boolean asserting whether the document represents the binding single source of truth for its designated scope and type.

### **Document State Machine and Transition Rules**

Artifact status transitions follow deterministic rules to ensure document integrity:

> * A draft artifact transitions to provisional upon structural completion, or to experimental if marked as an exploratory prototype.  
> * A provisional artifact transitions to active upon passing formal verification and review, or to superseded if preempted during review.  
> * An active document transitions to superseded when an explicit replacement is approved, or to deprecated if retired without replacement.  
> * A superseded document transitions to historical once active system cutovers are complete.  
> * Both historical and deprecated documents eventually transition to archived for cold storage.

### **Lineage and Directed Graph Relations**

Document relationships must be modeled as a directed graph using qualified DataCite-inspired relational verbs. References must target stable identifiers rather than volatile file paths:

`relations:`  
&nbsp;&nbsp;`supersedes:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "urn:somnus:doc:0195e34a-89a2-7b1c-92e1-45601278abcd"`  
&nbsp;&nbsp;`superseded_by: []`  
&nbsp;&nbsp;`derived_from:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "urn:[span_3](start_span)[span_3](end_span)[span_5](start_span)[span_5](end_span)somnus:doc:0195e11f-22b0-7c2a-88f4-00129845ef01"`  
&nbsp;&nbsp;`cites:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "doi:10.1145/3318464.3389700"`  
&nbsp;&nbsp;`complements:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "urn:somnus:doc:0195e200-1111-7a3b-bf20-998877665544"`

Enforcing strict inverse semantics ensures repository integrity. If Document B asserts supersedes: \[Document A\], repository-level verification passes can either validate or automatically inject superseded\_by: \[Document B\] into Document A, preventing orphaned references.

## **Stable Identity and Location Semantics**

In large, multi-repository systems, Markdown files are frequently moved, renamed, split, or consolidated. Treating the file system path as the primary document key causes broken links, invalidates citations, and disrupts graph traversal.

### **Evaluation of Identifier Paradigms**

| Identifier Scheme | Collision Resistance | Time-Sortable | Human Readability | Decentralized Minting | Verdict for Somnus Identity |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **UUIDv4** | Absolute (2^{122} entropy) | No (Random) | Low (Hex-and-dash) | Yes (Cryptographic RNG) | Acceptable, but non-sortable; produces index fragmentation. |
| **UUIDv7 (RFC 9562\)** | High (2^{74} entropy \+ 48-bit timestamp) | Yes (Millisecond order) | Moderate (Standard 36-char hex) | Yes (Zero coordination) | **Optimal Standard**: Native time ordering, native UUID tool parsing. |
| **ULID** | High (2^{80} entropy \+ 48-bit timestamp) | Yes (Millisecond order) | High (26 Base32 characters) | Yes (Zero coordination) | Strong candidate, but lacks native UUID parser recognition in standard databases. |
| **Git BLOB Hash (SHA-1/256)** | Cryptographic | No | Very Low (40/64 hex characters) | No (Requires content finalization) | Unsuitable for identity: mutating one character changes the ID entirely. |
| **Slug / Path / Filename** | Vulnerable to collision | No | High | No (Prone to renaming collisions) | Unusable as primary key; excellent as secondary human alias. |

*Evidence-Supported Recommendation*: Somnus should standardize on **UUIDv7 (RFC 9562\)** as the mandatory primary identifier for all artifacts. UUIDv7 provides an optimal balance:

> * The first 48 bits encode a big-endian Unix timestamp in milliseconds, providing natural chronological sorting in databases and file listings without requiring frontmatter parsing.  
> * The remaining bits encode standard RFC variant markers and 74 bits of cryptographically secure pseudorandom entropy, ensuring decentralized, collision-free generation across multi-agent fleets without centralized authority coordination.  
> * It formats cleanly into the standard 36-character hexadecimal string, allowing out-of-the-box validation in databases and schema engines without custom codecs.

### **Decoupling Location from Identity**

Location represents an artifact's transient physical placement, whereas identity represents its immutable logical presence. Location metadata must capture both original provenance and current directory placement:

`id: "0195e35b-1729-7d88-b21a-e7c6530a21cf"`  
`slug: "consensus-safety-invariants"`  
`location:`  
&nbsp;&nbsp;`repository: "git@github.com:somnus-org/core-architecture.git"`  
&nbsp;&nbsp;`repository_root: "docs/specifications"`  
&nbsp;&nbsp;`path: "docs/specifications/consensus-safety.md"`  
&nbsp;&nbsp;`historical_paths:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "drafts/vance/consensus-draft.md"`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "rfc/rfc-012-invariants.md"`  
`origin:`  
&nbsp;&nbsp;`repository: "git@github.com:somnus-org/research-sandbox.git"`  
&nbsp;&nbsp;`path: "experiments/2026-02/consensus-notes.md"`  
&nbsp;&nbsp;`initial_commit: "9f83a1b490f23b7e12"`

This structural separation enables static CI tooling to detect file movements and automatically update location.path and location.historical\_paths without altering the document's stable identity.

## **Profile and Extension Architecture**

Somnus documents span diverse genres, ranging from formal mathematical proofs and hardware benchmarks to transient agent notepads and execution plans. Standardizing these artifacts requires choosing between a monolithic mega-schema or a modular core-plus-extension system.

### **Small Universal Core plus Composable Document Profiles**

*Evidence-Supported Recommendation*: Somnus should implement a **Small Universal Core \+ Composable Document Profiles** model.

Monolithic schemas force every document to account for irrelevant attributes (such as requiring task deadlines on a research paper). Conversely, schema-free extensions lead to semantic fragmentation, preventing global operations like scanning all documents for outdated models or identifying superseded artifacts across the repository.

Under this architecture, the standard library defines:

> 1. **Somnus Core**: The mandatory base schema containing identity, classification, basic lifecycle, temporal markers, location, and base provenance.  
> 2. **Somnus Profiles**: Specialized schema extensions keyed to classification.type that introduce constrained property sets.

### **Schema Composition Mechanics**

Evaluating composition mechanisms highlights distinct trade-offs across validation engines:

| Composition Mechanism | Implementation Mechanics | Schema Validation Guarantees | Unknown Field Handling | Tooling Ecosystem & Portability |
| :---- | :---- | :---- | :---- | :---- |
| **JSON Schema Draft 2020-12** (allOf \+ unevaluatedProperties) | Core schema referenced via $ref inside profile; root uses unevaluatedProperties: false. | Strict structural typing; deep semantic validation. | Explicitly disallows unknown properties across all composable subschemas. | Universal support across Rust, Python, Go, Node, C++. |
| **CUE (Configure, Unify, Execute)** | Value lattices; schemas and data are unified identically (\#Core & \#Profile). | Mathematical guarantee of conflict-free unification. | Open by default; closed via strict definition locks. | Requires CUE Go runtime or C-bindings; CLI is lightweight, but language ecosystem is smaller. |
| **YAML Anchors & Merge Keys (\<\<: \*core)** | Textual YAML-level macro substitution. | None; only clones text keys prior to parsing. | Entirely reliant on external parser. | Dangerous: deprecated in YAML 1.2; poor cross-language parity. |
| **JSON-LD Framing / Mixins** | Semantic Web context mapping via @context and framing algorithms. | Weak structural validation; high semantic reasoning. | Tolerates open unknown fields completely. | Extremely heavy; requires graph database and RDF engines. |

JSON Schema Draft 2020-12 provides the most rigorous, portable implementation mechanism. In Draft 2020-12, the unevaluatedProperties keyword resolves the historic limitation of allOf combined with additionalProperties: false\[span\_7\](start\_span)\[span\_7\](end\_span), where sibling schemas were unable to evaluate properties declared across composition boundaries.

### **Profile Implementation Pattern**

A profile schema dereferences the Somnus Core and extends it cleanly:

`{`  
&nbsp;&nbsp;`"$schema": "https://json-schema.org/draft/2020-12/schema",`  
&nbsp;&nbsp;`"$id": "somnus://profiles/engineering/benchmark/v1",`  
&nbsp;&nbsp;`"title": "Somnus Benchmark Profile",`  
&nbsp;&nbsp;`"type": "object",`  
&nbsp;&nbsp;`"allOf": [`  
&nbsp;&nbsp;&nbsp;&nbsp;`{ "$ref": "somnus://core/v1" }`  
&nbsp;&nbsp;`],`  
&nbsp;&nbsp;`"properties": {`  
&nbsp;&nbsp;&nbsp;&nbsp;`"benchmark": {`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"type": "object",`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"required": ["workload", "environment", "metrics"],`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"properties": {`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"workload": { "type": "string" },`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"environment": {`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"type": "object",`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"required": ["cpu", "memory_gb", "os"],`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"properties": {`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"cpu": { "type": "string" },`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"memory_gb": { "type": "number" },`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"os": { "type": "string" }`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`}`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`},`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"metrics": {`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"type": "array",`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"items": {`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"type": "object",`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"required": ["name", "value", "unit"],`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"properties": {`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"name": { "type": "string" },`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"value": { "type": "number" },`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`"unit": { "type": "string" }`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`}`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`}`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`}`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`}`  
&nbsp;&nbsp;&nbsp;&nbsp;`}`  
&nbsp;&nbsp;`},`  
&nbsp;&nbsp;`"unevaluatedProperties": false`  
`}`

By scoping the profile's unique payload under a single key (benchmark:), the extension prevents root-level namespace collisions with future core schema revisions.

## **Detailed Comparison of Candidate Submatter Mechanisms**

Submatter attaches machine-readable metadata to localized regions within a Markdown document (e.g., invariants, architectural decisions, hypotheses, benchmarks, code blocks, or evidence). An AI agent or static analysis engine must be able to address, extract, reason over, and update these regions independently without destroying the document's human readability or breaking standard Markdown parsers.

### **The Candidates**

Six implementation paradigms represent the practical candidate space:

> 1. **XML-Style Custom Elements**: Enclosing regions in explicit HTML-like tags (e.g., \<somnus-region type="decision"\> ... \</somnus-region\>).  
> 2. **HTML Comments**: Embedding structured JSON or YAML within comment blocks (e.g., \<\!-- somnus:region type="decision" ... \--\> ... \<\!-- /somnus:region \--\>).  
> 3. **Generic Markdown Directives**: The container directive syntax formalized in remark-directive and mdast-util-directive (e.g., :::region{type="decision" id="..."} ... :::).  
> 4. **Pandoc-Style Fenced Divs**: Pandoc's bracketed fenced div extension (e.g., ::: {\#id .decision type="decision"} ... :::).  
> 5. **Fenced Code Blocks with Custom Info-Strings**: Using fenced code blocks with custom language identifiers (e.g., yaml:somnus-submatter ... ).  
> 6. **Obsidian-Style Callouts with Appended Block IDs**: Markdown blockquotes formatted as callouts with an Obsidian block identifier anchor (e.g., \> \[\!decision\] ... ^dec-01).

### **Evaluation Matrix**

| Criterion | 1\. XML Custom Tags | 2\. HTML Comments | 3\. Generic Directives | 4\. Pandoc Fenced Divs | 5\. Fenced Code Blocks | 6\. Callouts \+ Block IDs |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **1\. Raw Readability** | Poor (visual clutter) | Excellent (hidden in render) | Excellent (clean delimiters) | Very Good (clean delimiters) | Good (visible code fence) | Excellent (native quote look) |
| **2\. CommonMark Render** | **Broken (strips formatting)** | Hidden (omitted from display) | Literal text if unextended | Literal text if unextended | Renders as code box | Renders as styled callout |
| **3\. GitHub Compatibility** | Unsafe; tags sanitized | Completely safe (ignored) | Renders ::: as plain text | Renders ::: as plain text | Renders as pre/code block | Supported native callouts |
| **4\. Obsidian Compatibility** | HTML parsed; styles vary | Fully ignored | Ignored / plain text | Community plugin required | Renders as syntax block | **Native first-class support** |
| **5\. Parser Availability** | Universal HTML | Universal RegExp/Lexer | Node (mdast), Python (mdit) | Pandoc (Haskell), Python | Universal (standard Markdown) | Native in Obsidian/GFM |
| **6\. Inner AST Parsing** | **NO (treated as raw text)** | **YES (markdown unaffected)** | **YES (first-class AST parent)** | **YES (first-class AST parent)** | **NO (escaped code string)** | **YES (standard blockquote)** |
| **7\. Robustness / Recovery** | Fragile (DOM parsing rules) | High (unmatched comment safe) | High (delimiter balancing) | High (delimiter balancing) | Very High (standard fences) | High (standard blockquote) |
| **8\. Manual Ergonomics** | Moderate (tag pairing) | High (simple comment blocks) | High (minimal punctuation) | High (minimal punctuation) | High (standard fence syntax) | High (fast typing) |
| **9\. AI Authoring Ergonomics** | Moderate (tag hallucinations) | High (standard comment) | High (widely fine-tuned) | High | Very High (native fence generation) | High |
| **10\. Programmatic Editing** | High (XML/DOM parsers) | High (regex / string splice) | High (AST node transformations) | High (AST node transformations) | High (AST or string match) | Moderate (line prefix tracking) |
| **11\. Nesting Capability** | Complex (HTML void/nesting) | Poor (comments cannot nest) | **Excellent (arbitrary depth :::: )** | **Excellent (depth by colon count)** | Extremely Poor (fence collisions) | Moderate (nested \>\> quotes) |
| **12\. Incremental Parsing** | Poor (requires tree context) | Excellent (linear scan) | Good (scan for delimiters) | Good (scan for delimiters) | Excellent (scan for fences) | Good (line-by-line quote scan) |
| **13\. Polyglot Portability** | Universal | Universal | Requires unified or port | Requires Pandoc or custom lex | Universal | Universal |
| **14\. Standard Stability** | W3C Standard | Standard CommonMark | De facto standard (mdast RFC) | Pandoc spec standard | CommonMark Standard | GFM / Obsidian de facto |

## **Markdown and Parser Interoperability Hazards**

Evaluating submatter candidates exposes critical parsing behaviors in CommonMark, GitHub Flavored Markdown (GFM), and YAML parsers that must guide system design.

### **The CommonMark HTML Block Hazard**

A common assumption in document tooling design is that Markdown can be enclosed in arbitrary XML or HTML container tags without affecting formatting:

`<somnus-region type="invariant" id="inv-01">`  
`### Invariant: Sequence Monotonicity`  
`The state sequence numbers **must strictly increase**.`  
`</somnus-region>`

In the CommonMark Specification (Section 4.6), raw HTML blocks are classified into seven discrete types:

> * **Types 1–5**: Defined by specific opening delimiters (\<script\>, \<pre\>, \<\!-- ... \--\>, \<? ... ?\>, \<\!DECLARATION ... \>) and closed by matching literal patterns.  
> * **Type 6**: Matches standard HTML block tags (such as \<div\>, \<p\>, \<table\>) that may interrupt an active paragraph and terminate at the next blank line.  
> * **Type 7**: Matches complete open or closing tags of arbitrary names (e.g., \<somnus-region\>), but which **cannot interrupt an existing paragraph** and must terminate at a blank line.

*Crucial Technical Fact*: Under the CommonMark specification, **the content inside Type 6 and Type 7 HTML blocks is treated as raw, unparsed literal text**. The parser *does not construct Markdown AST nodes for content enclosed within these HTML tags*.

As a consequence, headings (\#\#\# Invariant) are not parsed into heading nodes, bold markers (\*\*must strictly increase\*\*) remain unparsed asterisk characters, inner bulleted lists do not form list items, and embedded links do not resolve in the AST. Unless a downstream compiler integrates an explicit HTML post-processing pass with a custom Markdown-re-injection mechanism, wrapping regions in custom HTML/XML tags breaks Markdown rendering across CommonMark-compliant parsers, including cmark-gfm, GitHub, GitLab, and Obsidian.

Furthermore, GitHub executes server-side HTML sanitization using an allowlist filter. Custom HTML tags like \<somnus-region\> are stripped entirely, causing enclosed elements to collapse into unstyled inline text and discarding custom attributes like type or id.

### **The YAML Interoperability Trap: 1.1 versus 1.2**

YAML frontmatter engines suffer from fragmentation between YAML 1.1 and YAML 1.2 implementations.

`# Examples of fatal YAML 1.1 implicit coercions:`  
`country: NO              # Parsed as boolean false in YAML 1.1[span_147](start_span)[span_147](end_span)[span_149](start_span)[span_149](end_span)`  
`canonical: yes           # Parsed as boolean true in YAML 1.1[span_151](start_span)[span_151](end_span)[span_154](start_span)[span_154](end_span)`  
`flag: on                 # Parsed as boolean true in YAML 1.1[span_152](start_span)[span_152](end_span)[span_155](start_span)[span_155](end_span)`  
`version: 1.20            # Parsed as float 1.2 in both 1.1 and 1.2[span_157](start_span)[span_157](end_span)`  
`timesta[span_77](start_span)[span_77](end_span)[span_79](start_span)[span_79](end_span)[span_81](start_span)[span_81](end_span)mp: 2026-03-30    # Parsed as a native language Date object, not a string[span_159](start_span)[span_159](end_span)`

> 1. **The Norway Problem**: In YAML 1.1, the unquoted scalar strings y, Y, yes, Yes, YES, n, N, no, No, NO, true, false, on, and off are parsed as booleans. An artifact with region: NO or state: off is corrupted silently. In YAML 1.2 Core Schema, booleans are restricted to true and \[span\_148\](start\_span)\[span\_148\](end\_span)\[span\_150\](start\_span)\[span\_150\](end\_span)false. However, foundational parsers such as Python's PyYAML remain pinned to YAML 1.1, while modern JavaScript and Rust loaders implement YAML 1.2.  
> 2. **Unquoted Version Numbers**: A version declared as version: 1.20 is coerced into a floating-point number (1.2), truncating semantically significant trailing zeros.  
> 3. **Implicit Timestamps**: ISO date scalars (e.g., 2026-03-30) are automatically deserialized into runtime date objects in some loaders, but retained as strings in others. When converting to JSON, timezone offsets can drift based on the host system's locale.  
> 4. **Duplicate Key Behavior**: YAML 1.2 explicitly forbids duplicate keys within a single mapping node. However, legacy or lenient parsers fail to throw errors and silently apply "last-key-wins", discarding earlier key-value pairs without warning.  
> 5. **Tab Indentation**: YAML strictly forbids the horizontal tab (\\t) for indentation. Editors that mix tabs and spaces cause parser failures that are difficult to diagnose visually.

To maintain interoperability, Somnus must require that all string scalars containing version numbers, status tokens, or dates be explicitly quoted or parsed using a YAML 1.2 Core parser.

## **Validation Architecture**

To ensure metadata integrity without burdening developers or CI pipelines, the Somnus validation architecture must support local-first verification across diverse programming languages via a lightweight CLI binary.

### **Multi-Stage Validation Pipeline**

Validation is organized as a three-stage sequential pipeline:

> * **Stage 1: Grammar and Structural Parse**: The frontmatter block bounded by the opening and closing \--- delimiters is extracted and fed to a strict YAML 1.2 parser. The parser rejects tab characters, duplicate mapping keys, and unquoted ambiguous scalars. Simultaneously, submatter regions in the Markdown body are extracted via AST traversal or directive delimiter matching.  
> * **Stage 2: Schema Conformance Validation**: The extracted frontmatter data is validated against the base somnus://core/v1 JSON Schema. Next, the URI declared in classification.profile is resolved, and the document payload is validated against the corresponding profile schema (such as somnus://profiles/engineering/whitepaper/v1). Any unmapped root properties trigger an immediate schema violation via unevaluatedProperties: false.  
> * **Stage 3: Semantic and Referential Integrity Check**: The validator verifies contextual invariants that fall outside structural schema checks. This includes verifying that the millisecond timestamp embedded in the document's UUIDv7 matches the created\_at field, confirming that bidirectional relations resolve without cycles, and ensuring that files marked as superseded contain at least one valid target in relations.superseded\_by.

### **Polyglot Schema Engine**

*Evidence-Supported Recommendation*: Somnus schemas should be implemented using **JSON Schema Draft 2020-12**.

JSON Schema provides high-performance validation across major development environments:

> * Standard-compliant libraries are available in Rust (jsonschema, boon), Python (jsonschema, fastjsonschema), TypeScript/Node (ajv), Go (sanitizers/go-jsonschema), and C/C++.  
> * Combining allOf composition with unevaluatedProperties: false ensures strict validation across schema inheritance layers without child fields leaking or triggering false positives.  
> * Schemas reside as static, version-controlled JSON files within the repository (schemas/v1/core.json), avoiding proprietary runtime or language-specific compiler dependencies.

While CUE offers expressive constraint definitions, its dependency on the Go runtime complicates cross-compilation into embedded or multi-language CLI toolchains. JSON Schema Draft 2020-12 provides the broadest portability.

### **Standalone CLI Distribution**

The Somnus validator can be compiled into a standalone native binary (somnus validate \<path\>) using Rust, combining pulldown-cmark for Markdown parsing, serde\_yaml for YAML 1.2 ingestion, and jsonsche\[span\_63\](start\_span)\[span\_63\](end\_span)\[span\_66\](start\_span)\[span\_66\](end\_span)\[span\_69\](start\_span)\[span\_69\](end\_span)ma-rs for validation. This delivers sub-millisecond execution times suitable for local Git pre-commit hooks and real-time IDE language servers without requiring external runtime dependencies.

## **Versioning and Migration Strategy**

As system requirements evolve, the Somnus metadata standard must support schema migrations across thousands of historical files without breaking legacy tools or blocking adoption of newer profiles.

### **Semantic Schema Versioning**

The schema version must be declared explicitly in every document frontmatter through a composite URI:

`somnus:`  
&nbsp;&nbsp;`version: "1.0.0"`  
&nbsp;&nbsp;`schema: "somnus://core/v1"`

*Evidence-Supported Recommendation*: Semantic Versioning (SemVer 2.0.0) governs schema evolution:

> * **PATCH (1.0.0 \\rightarrow 1.0.1)**: Documentation improvements, description updates, or non-breaking regular expression refinements in the schema.  
> * **MINOR (1.0.0 \\rightarrow 1.1.0)**: Addition of new optional metadata fields, new non-normative classification types, or new submatter region types. Older validators continue to parse newer documents by ignoring unvalidated optional additions, provided unevaluatedProperties is scoped correctly.  
> * **MAJOR (1.0.0 \\rightarrow 2.0.0)**: Renaming existing fields, removing fields, altering default enum vocabularies, or changing submatter delimiter grammar. Requires automated batch migration.

### **Handling Unknown Fields: Strict Core versus Extension Namespaces**

A key challenge in strict schema validation is balancing closed validation (preventing spelling mistakes) with extensibility (allowing experimental fields).

*Architectural Inference*: Somnus should enforce a **Closed Core with an Open Extension Escape Hatch**:

> * Standard properties in the Somnus Core and official profiles run under unevaluatedProperties: false. If a contributor writes authur: instead of author:, the validator fails immediately.  
> * To support experimental metadata without breaking CI checks, an explicit, optional namespace is provided: extensions: or x-somnus-\*.  
> * Properties inside extensions are validated against an open schema (type: object, additionalProperties: true). This allows experimental fields to be tested in isolation before being proposed for inclusion in a minor schema revision.

### **Automated Document Migration**

When a MAJOR schema revision is published, the Somnus CLI must provide an automated codemod engine:

`somnus migrate --from core/v1 --to core/v2 docs/`

Because YAML parsers often strip comments and alter whitespace formatting during deserialization and re-serialization, the migration engine must parse frontmatter using a concrete syntax tree (CST) engine (such as ruamel.yaml in Python or a custom CST tokenizer). This ensures that hand-written YAML comments, custom field ordering, and Markdown body formatting remain intact across migrations.

## **AI-Agent Ergonomics**

Frontier AI coding and research agents will serve as primary authors, editors, and consumers of Somnus Markdown files. Metadata structures must be designed to minimize token overhead, eliminate syntactic ambiguity, and prevent AI hallucinations during editing passes.

### **Token Economy and Structural Predictability**

Verbose semantic formats like JSON-LD, RDF XML, and deeply nested dictionaries exhaust context windows and increase generation latency. Conversely, flat key-value pairs reduce nesting errors.

`# Inefficient, high-token nesting:`  
`metadata:`  
&nbsp;&nbsp;`temporal_data:`  
&nbsp;&nbsp;&nbsp;&nbsp;`creation_information:`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`iso_timestamp_utc: "2026-03-30T10:00:00Z"`

`# Somnus streamlined ergonomic pattern:`  
`created_at: "2026-03-30T10:00:00Z"`

> * **2-Space Indentation**: Mandating standard 2-space indentation prevents indentation drift, which frequently causes models to output broken YAML blocks.  
> * **Kebab-Case Lowercase Properties**: AI models can generate inconsistent capitalizations when using CamelCase (e.g., oscillating between createdDate, createDate, and CreatedDate). Standardizing strictly on lowercase kebab-case or snake\_case reduces token confusion. Lowercase kebab-case aligns naturally with standard Markdown URL slugs and command-line interfaces.  
> * **Flat Root Mappings**: Keeping core identity, status, and classification at the root level minimizes the nesting depth required during generation.

### **Preventing Hallucination via Closed Grounding**

When an AI model encounters an open-ended classification system, it often invents plausibly named keys (e.g., status: review-ready, category: deep-learning-research).

To prevent schema drift during synthetic authoring, Somnus system prompts and automated tool definitions should inject the compact JSON Schema definition of the target profile into the model's context window. Restricting core fields to closed enumerated vocabularies with descriptive, distinct names provides clear operational boundaries for generation.

### **Partial Document Editing and Block Stability**

A major ergonomic failure occurs when an agent attempts to edit a single section in a 2,000-line Markdown document. If metadata is only present at the root, the agent must inspect the entire file to determine the status of a specific sub-region.

Furthermore, using diff/patch tools or search-and-replace blocks over large text files is error-prone. Submatter boundaries provide deterministic anchors:

`:::submatter:decision{id="0195e360-12ab-7c01" status="accepted"}`  
`### ADR-01: Use UUIDv7 for Identity`  
`UUIDv7 is chosen over ULID due to RFC 9562 formal standardization.`  
`:::`

When instructed to modify ADR-01, an agent can search directly for :::submatter:decision{id="0195e360-12ab-7c01" and rewrite only that delimited block. This eliminates ambient context tracking and avoids unintentional modifications to neighboring sections.

### **Epistemic Grounding: Distinguishing Fact from Hypothesis**

In complex research and architectural artifacts, AI systems frequently confuse speculative proposals with verified system facts. Submatter provides machine-readable epistemic tagging within the artifact body:

> * :::submatter:hypothesis: Theoretical assertions awaiting empirical validation.  
> * :::submatter:invariant: Non-negotiable structural constraints that must not be broken by agent refactorings.  
> * :::submatter:decision: Accepted architectural choices.  
> * :::submatter:evidence: Empirical observations, benchmark runs, or test outputs supporting a hypothesis.  
> * :::submatter:archive: Deprecated, obsolete context preserved purely for historical tracing.

By traversing the AST, an AI agent can selectively extract only invariant and decision blocks to compile a ground-truth operational prompt, ignoring speculative hypotheses or historical context.

## **Candidate Somnus Architecture Based on the Evidence**

Synthesizing the empirical evidence, standards analysis, and ergonomic requirements produces a candidate architecture for the Somnus Markdown Metadata Standard (v0.1).

### **Frontmatter Grammar: Hybrid Semi-Flat Root Structure**

To balance third-party Markdown tool compatibility (e.g., Obsidian, Hugo, static-site generators) with collision resistance and strict schema enforcement, Somnus adopts a **Hybrid Semi-Flat Root Structure**.

`---`  
`# ==============================================================================`  
`# SOMNUS METADATA CORE (v0.1)`  
`# ==============================================================================`  
`somnus:`  
&nbsp;&nbsp;`version: "0.1.0"`  
&nbsp;&nbsp;`schema: "somnus://core/v1"`

`# --- Identity ---`  
`id: "0195e364-bb40-7f22-9df8-8bc6289b5c30"`  
`slug: "memory-hierarchy-invariants"`  
`title: "Deterministic Invariants for Hierarchical Agent Memory"`  
`aliases:`  
&nbsp;&nbsp;`- "memory-invariants"`  
&nbsp;&nbsp;`- "agent-mem-spec"`

`# --- Classification ---`  
`classification:`  
&nbsp;&nbsp;`category: engineering`  
&nbsp;&nbsp;`type: specification`  
&nbsp;&nbsp;`subtype: memory-subsystem`  
&nbsp;&nbsp;`profile: "somnus://profiles/engineering/specification/v1"`  
&nbsp;&nbsp;`role: normative`  
&nbsp;&nbsp;`scope: subsystem`  
&nbsp;&nbsp;`tags:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- agent-architecture`  
&nbsp;&nbsp;&nbsp;&nbsp;`- memory`  
&nbsp;&nbsp;&nbsp;&nbsp;`- invariants`

`# --- Lifecycle ---`  
`lifecycle:`  
&nbsp;&nbsp;`status: active`  
&nbsp;&nbsp;`is_canonical: true`  
&nbsp;&nbsp;`reviewed_at: "2026-03-30T10:14:00Z"`

`# --- Lineage & Relations ---`  
`relations:`  
&nbsp;&nbsp;`supersedes:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "0194a112-9c01-7111-a203-018273645500"`  
&nbsp;&nbsp;`superseded_by: []`  
&nbsp;&nbsp;`derived_from:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "0193f440-2a3b-7890-bcde-998877665544"`  
&nbsp;&nbsp;`cites:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- "doi:10.1145/3318464.3389700"`

`# --- Location & Provenance ---`  
`location:`  
&nbsp;&nbsp;`repository: "git@github.com:somnus-org/somnus-core.git"`  
&nbsp;&nbsp;`path: "specs/memory/invariants.md"`  
`origin:`  
&nbsp;&nbsp;`repository: "git@github.com:somnus-org/somnus-core.git"`  
&nbsp;&nbsp;`path: "drafts/vance/memory-draft.md"`

`provenance:`  
&nbsp;&nbsp;`authors:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- name: "Dr. Eleanor Vance"`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`id: "user:vance@somnus.org"`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`role: author`  
&nbsp;&nbsp;`operators:`  
&nbsp;&nbsp;&nbsp;&nbsp;`- name: "Somnus Copilot"`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`model: "anthropic/claude-3-7-sonnet"`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`operator: "user:vance@somnus.org"`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`role: editor`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`interaction_at: "2026-03-30T10:14:00Z"`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`actions:`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`- edited`  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`- verified`

`# ==============================================================================`  
`# PROFILE EXTENSION (Profile: Specification)`  
`# ==============================================================================`  
`specification:`  
&nbsp;&nbsp;`system_target: "somnus-node"`  
&nbsp;&nbsp;`compliance_level: "mandatory"`  
&nbsp;&nbsp;`verification_suite: "tests/compliance/memory_suite.rs"`  
`---`

### **Submatter Grammar: Generic Container Directives**

*Evidence-Supported Recommendation*: Submatter should be implemented using **Generic Container Directives** (colons :::), matching the syntax of remark-directive and the CommonMark Directives Proposal:

`# System Memory Architecture`

`The memory subsystem is divided into episodic, working, and canonical tiers.`

`:::submatter:invariant{id="0195e366-0210-7a00-98ff-112233445566" status="active" authority="canonical"}`  
`### Invariant 1: Single-Writer Principle`  
`Only the designated core consolidation agent may commit updates to the canonical tier.`&nbsp;  
`Any secondary agent attempting concurrent write operations must be rejected with`&nbsp;  
`a concurrency exception.`  
`:::`

`The following hypothesis is currently undergoing verification:`

`:::submatter:hypot[span_92](start_span)[span_92](end_span)[span_101](start_span)[span_101](end_span)hesis{id="0195e366-0210-7a01-bcae-223344556677" test_ref="tests/bench_mem.py"}`  
`Increasing working memory tier caching from 16KB to 64KB will decrease retrieval latency`&nbsp;  
`without causing context thrashing.`  
`:::`

#### **Why Directives Outperform Alternative Submatter Syntaxes**

> 1. **Preservation of Markdown Semantics**: Unlike custom HTML elements (\<somnus-region\>), container directives preserve standard parsing for inner Markdown content. Headers, bold text, lists, and code blocks inside the container directive parse cleanly into the AST.  
> 2. **Clean AST Integration**: Directives are natively represented in standard ASTs (such as mdast) as containerDirective nodes, storing attributes cleanly in a dedicated attributes mapping.  
> 3. **Graceful GitHub / Plaintext Degradation**: In systems lacking directive plugins, the container renders as raw text lines without mangling enclosing paragraphs or triggering aggressive HTML sanitizers.  
> 4. **Arbitrary Nesting**: Directives support arbitrary nesting depth simply by incrementing the fence count (:::: wraps :::), avoiding parser ambiguity.

## **Remaining Design Choices Requiring an Explicit Somnus Decision**

The evidence gathered points toward clear architectural paths, but several distinct trade-offs require an explicit engineering choice by the Somnus project team:

| Architectural Decision | Option A | Option B | Core Trade-off |
| :---- | :---- | :---- | :---- |
| **1\. Primary Submatter Mechanism** | **Container Directives (:::submatter)** | **HTML Comments (\<\!-- somnus:submatter \--\>)** | Directives are first-class visible block elements in ASTs, but render as visible text on standard GitHub interfaces. HTML comments are hidden in renderers, but cannot nest cleanly and require regex parsing. |
| **2\. Frontmatter Root Namespacing** | **Hybrid Semi-Flat** (Core fields at root; metadata scoped under somnus:) | **Strict Namespacing** (Every single field under a somnus: root key) | Hybrid Semi-Flat allows standard editors (Obsidian, Hugo) to index title and tags natively, but risks naming collisions with third-party tools. Strict namespacing prevents all key collisions, but degrades third-party tool ergonomics. |
| **3\. Identifier Format** | **UUIDv7 Hex String** (0195e364-bb40-...) | **ULID Base32 String** (01ARZ3NDEKTSV4RRFFQ69G5FAV) | UUIDv7 is an official IETF standard (RFC 9562\) with native database UUID type support. ULID is shorter (26 vs 36 characters) and slightly more compact to read, but lacks formal RFC standardization. |
| **4\. History Ledger Location** | **Two-Tier Model** (Summary in frontmatter; full events in provenance/\*.json) | **In-Document Event Log** (Append every edit directly to an events: YAML list) | The Two-Tier Model keeps document headers lean and token-efficient for AI prompts, but requires an external ledger folder. In-Document Event Logs keep files self-contained, but bloat frontmatter over long editing lifecycles. |
| **5\. Strictness on Unknown Fields** | **Zero Tolerance (unevaluatedProperties: false)** | **Permissive Warnings (Linter flags without exit failure)** | Zero tolerance prevents spelling mistakes and halts schema drift, but can block rapid human prototyping. Permissive warnings allow exploratory drafting, but risk corrupting downstream automated pipelines. |

## **Technical Summary of Findings**

To guide the downstream implementation pass for the Somnus Frontmatter and Submatter Standard (v0.1), the investigation concludes with the following design recommendations:

> 1. **Grammar**: Adopt YAML 1.2 Core Schema for frontmatter, mandating explicit quotes on version numbers, status tokens, and timestamps to eliminate YAML 1.1 type coercion errors.  
> 2. **Identity**: Standardize on RFC 9562 UUIDv7 for all document identifiers, embedding an immutable millisecond creation timestamp directly into a decentralized, time-sortable primary key.  
> 3. *Classification*: Decouple operational taxonomy via a structured classification mapping (category, type, subtype, role, scope, profile, tags), applying closed enumerations to structural genres while keeping tags open-ended.  
> 4. **Schema Composition**: Model profiles through JSON Schema Draft 2020-12, composing profiles over a minimal Somnus Core using allOf combined with unevaluatedProperties: false to enforce closed, modular document types.  
> 5. **Submatter**: Implement section-level metadata using Generic Container Directives (:::submatter:\<type\>{...}). Standard HTML/XML tags must be avoided, as CommonMark Type 6 and Type 7 parsing rules prevent the internal Markdown content from being processed into AST nodes.  
> 6. **Validation**: Build a standalone, multi-stage native validation binary (somnus validate) capable of validating structural syntax, JSON Schema profile conformance, and referential graph integrity locally and in sub-millisecond execution times.

#### **Works cited**

1\. Instruments@DataCite \- Metadata Game Changers, https://metadatagamechangers.com/blog/2024/9/12/instrumentsdatacite 2\. RelationType code list: source and casing \- The PID Forum, https://pidforum.org/t/relationtype-code-list-source-and-casing/2688 3\. relationType — DataCite Metadata Schema 4.5 documentation, https://datacite-metadata-schema.readthedocs.io/en/4.5/appendices/appendix-1/relationType/ 4\. YAML-LD 1.0 \- W3C, https://www.w3.org/TR/yaml-ld-10/ 5\. What's in a name: the release of Metadata Schema 4.4 \- DataCite, https://datacite.org/blog/the-release-of-metadata-schema-4-4/ 6\. 3\. Collecting the metadata \- PIDinst, https://docs.pidinst.org/en/latest/datacite-cookbook/metadata.html 7\. Introducing DataCite Metadata Schema 4.5, https://datacite.org/blog/introducing-datacite-metadata-schema-4-5/ 8\. Release History \- DataCite Metadata Schema, https://schema.datacite.org/versions.html 9\. SPDX© Specification v3.0.1, https://spdx.dev/wp-content/uploads/sites/31/2024/12/SPDX-3.0.1-1.pdf 10\. Relationship \- SPDX Specification 3.0.1, https://spdx.github.io/spdx-spec/v3.0.1/model/Core/Classes/Relationship/ 11\. CreationInfo \- SPDX Specification 3.0.1, https://spdx.github.io/spdx-spec/v3.0.1/model/Core/Classes/CreationInfo/ 12\. using/docs/getting-started.md at main · spdx/using \- GitHub, https://github.com/spdx/using/blob/main/docs/getting-started.md 13\. spdx-3-serialization-prototype-playground/jsonld/examples ... \- GitHub, https://github.com/spdx/spdx-3-serialization-prototype-playground/blob/main/jsonld/examples/package\_sbom.json 14\. SPDX SBOM Specification Practical Guide for Security Teams, https://safeguard.sh/resources/blog/spdx-specification-practical-guide 15\. Feature Log \- Write On\! with Retype, https://retype.com/feature-log/ 16\. Clean Copy \- Obsidian Plugin, https://community.obsidian.md/plugins/clean-copy 17\. obsidian-markdown | Skills Hub \- Mentalok, https://mentalok.io/en/skills-hub/obsidian-markdown 18\. UUID v7 (UUIDv7) Generator & Timestamp Extractor — RFC 9562, https://www.authgear.com/tools/uuidv7-generator/ 19\. RFC 9562: Universally Unique IDentifiers (UUIDs), https://www.rfc-editor.org/info/rfc9562/ 20\. Generate UUIDv7 :: uuidv7.org, https://uuidv7.org/ 21\. UUIDv7 Generator \- Free Online Time-Sortable UUID | Base64.sh, https://www.base64.sh/uuidv7-generator/ 22\. JSON Schema Builder \- Dart API docs \- Pub.dev, https://pub.dev/documentation/json\_schema\_builder/latest/ 23\. Combining unevaluatedProperties and ref: \# · json-schema-org, https://github.com/orgs/json-schema-org/discussions/375 24\. Understanding unevaluatedProperties | by Simon Mikulcik \- Medium, https://medium.com/@smikulcik/bulletproof-your-input-validation-understanding-unevaluatedproperties-c6e7a0eb6ddd 25\. syntax-tree/mdast-util-directive \- GitHub, https://github.com/syntax-tree/mdast-util-directive 26\. remark-directive \- NPM, https://www.npmjs.com/package/remark-directive 27\. 8.18 Divs and Spans \- Pandoc, https://pandoc.org/demo/example33/8.18-divs-and-spans.html 28\. Obsidian Markdown Cheat Sheet: Syntax and Features, https://markdowneditoronline.com/blog/obsidian-markdown-cheat-sheet 29\. Diff: spec.txt, https://spec.commonmark.org/0.29/changes.html 30\. HTML blocks \- CommonMark Spec, https://spec.commonmark.org/0.25/ 31\. 0.30 \- CommonMark Spec, https://spec.commonmark.org/0.30/ 32\. Question: Custom HTML Tags and Safety · Issue \#538 \- GitHub, https://github.com/thephpleague/commonmark/issues/538 33\. spec/fixtures/cmark-gfm/spec.txt \- GitLab, https://gitlab.com/gitlab-org/ruby/gems/gitlab-glfm-markdown/-/blob/59cfe1b1c57f42ceb258276577d9f6cc7f2734d5/spec/fixtures/cmark-gfm/spec.txt 34\. github/cmark-gfm, https://github.com/github/cmark-gfm 35\. Creating an extension to allow custom tags \- html-sanitizer, https://github.com/tgalopin/html-sanitizer/blob/master/docs/2-creating-an-extension-to-allow-custom-tags.md 36\. Which inline HTML styles does GitHub Markdown accept?, https://stackoverflow.com/questions/44831505/which-inline-html-styles-does-github-markdown-accept 37\. GitHub \- mganss/HtmlSanitizer: Cleans HTML to avoid XSS attacks, https://github.com/mganss/htmlsanitizer 38\. HTML module markdown sanitization filter \- GitHub Gist, https://gist.github.com/9da9fc7ce746d3be59c0972373b0b4dd 39\. YAML to JSON Converter Online \- ToolzYard, https://toolzyard.com/tools/yaml-to-json.html 40\. TOML vs YAML vs JSON: Which Config Format to Use, https://jsontotable.io/blog/toml-vs-yaml-vs-json 41\. JSON to YAML Converter: Convert Online With Zero Uploads, https://www.toolsura.com/tools/json-to-yaml-converter/ 42\. TOML vs YAML vs StrictYAML \- python \- Stack Overflow, https://stackoverflow.com/questions/65283208/toml-vs-yaml-vs-strictyaml 43\. YAML Validator Online \- Syntax Checker Tool \- StrateCode DevTools, https://stratecode.tools/tools/yaml-validator/ 44\. A Media Type for Describing JSON Documents \- JSON Schema, https://json-schema.org/draft/2020-12/json-schema-core 45\. Time-Sortable Identifiers Explained: UUIDv7, ULID, and Snowflake, https://www.authgear.com/post/time-sortable-identifiers-uuidv7-ulid-snowflake/ 46\. draft-ietf-jsonschema-json-schema-03 \- IETF Datatracker, https://datatracker.ietf.org/doc/draft-ietf-jsonschema-json-schema/
