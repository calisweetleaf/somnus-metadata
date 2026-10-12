# Glossary

Terms used across `SPEC.md`, the code, and this wiki. Controlled vocabularies are defined in `src/somnus/model/vocab.py`.

| Term | Meaning |
| --- | --- |
| Artifact | A managed file's identity. Its ID is `urn:somnus:artifact:<uuid>`, minted as UUIDv7 for new files; imported UUIDs are wrapped, never reminted (SPEC section 3). |
| Revision | Positive integer in the header. Any indexed change to header or body should be a new revision (`somnus bump`). |
| Header / payload | The mapping under the `somnus:` key. "Payload" is the parsed dict; "header" is its serialized text. |
| Envelope | The region of a file that holds the header: frontmatter, an HTML comment, a comment block, or a whole sidecar file. |
| Carrier | The adapter that finds and writes envelopes for one family of file types (`src/somnus/carriers/`). See [Carriers](../systems/carriers.md). |
| Host | The file that carries an envelope. Bytes outside the envelope are host content and must never change on write (`E_HOST`). |
| Sidecar | `<file>.somnus.yaml`, used for files that cannot carry an embedded header (binaries, JSON). |
| Region | A span of the body delimited by paired markers `<!-- somnus:region:begin r-id -->` and `<!-- somnus:region:end r-id -->`. Markers carry identity only; attributes live in `knowledge.regions` (D2). |
| Classification | `category`, `type`, `role`, `scope`, and `tags`. Types include `specification`, `decision-record`, `benchmark`, `source-code`, and 16 others. |
| Role | Intent of the document: `normative`, `informative`, `working`, `exploratory`, `historical`. A normative role does not make a document authoritative. |
| Standing | Authority state: `unasserted`, `candidate`, `accepted`, `retired`, `rejected`. Scoped by `{target_ref, aspects}` (SPEC section 8). |
| Acceptance | `standing: accepted` plus `valid_time` and an `acceptance_ref`. At canon level the reference must resolve to an active `decision-record`. |
| Lifecycle status | `draft`, `proposed`, `provisional`, `active`, `experimental`, `superseded`, `deprecated`, `historical`, `archived`, `rejected`. Changed only through `somnus status` (SPEC section 7). |
| Valid time | When a statement applies: basis `bounded`, `open`, `timeless`, or `unknown`. Separate from authoring time (`somnus.time`) and observation time (registry). |
| Relation | A qualified edge such as `supersedes`, `derived_from`, `part_of`, `depends_on`, with an `assessment` and `valid_time`. `supersedes`, `derived_from`, and `part_of` must be acyclic. |
| Claim | A typed statement (`observation`, `definition`, `requirement`, `hypothesis`, `inference`, `prediction`, `measurement`). Its kind is kept verbatim; a hypothesis in an accepted document stays a hypothesis. |
| Entity | A named thing (project, system, agent, concept, ...) referenced by claims. Shared labels never merge entities. |
| Profile | A versioned extension schema such as `specification/1.0.0` or `benchmark/1.0.0`, declared in `profiles` with data under `profile_data`. |
| Extensions | `extensions.<owner>.data`, the only open location for tool-specific fields. Preserved, never indexed as trusted data. |
| Validation level | `carrier`, `core`, `semantic`, `canon`, each a superset of the previous. See [Validation](../systems/validation.md). |
| Registry | The global SQLite database at `$SOMNUS_HOME/somnus.db`. See [Registry](../systems/registry.md). |
| Root | A directory registered with `somnus init --root` and scanned by `somnus index`. |
| Conflict | A registry row for a problem across files. The `conflicts.kind` column allows `revision`, `duplicate-id`, `authority`, and `identity`. Registry-wide graph cycles are reported as `E_GRAPH` diagnostics during a scan, not stored as conflicts. |
| Event | A row in the append-only `events` ledger recording who changed what and when. |
| Diagnostic | One finding, printed as `path:line:col: severity CODE field: message` (`src/somnus/output.py`). |
| Mojibake | Text corrupted by decoding UTF-8 as cp1252. Hit this repo once; see [Pitfalls](../background/pitfalls.md). |
