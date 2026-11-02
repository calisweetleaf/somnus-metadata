# Design decisions

`DECISIONS.md` records nineteen ratified decisions, D1 to D19, that shape `SPEC.md` and the toolkit. The operator ratified D1 to D15 on 2026-10-11 by approving the implementation plan in `PLAN.md`; they replace five PROPOSED recommendations from an earlier draft, which survives in commit `5f1df5d`. D16 and D17 were ratified the same day during the agent-usability review that followed the build. They add `somnus set` and `somnus mcp` without changing the metadata schema, so the release stays `somnus://metadata/core/2.0.0` and `SPEC.md` moved to revision 2.

On 2026-10-20, `SPEC.md` and `DECISIONS.md` moved to revision 3 to describe the existing D17 adapter behavior more explicitly: closed tool schemas, text content, separate protocol and tool errors, stateless calls, and working-directory path resolution. This clarified the transport contract without changing the core schema URI. D18 was ratified on 2026-10-23 and D19 on 2026-10-31; the current document revisions are SPEC 6 and DECISIONS 5. `PLAN.md` is now a maintenance handoff; its current text is not the original ratification record.

## Summary

| # | Decision | Relation to the earlier draft | Enforced in SPEC |
| --- | --- | --- | --- |
| D1 | Single `somnus:` namespace | Reverses draft 2 (Hybrid Semi-Flat roots) | 4 |
| D2 | Comment-marker regions with a header registry | Reverses draft 1 (container directives) | 13 |
| D3 | URN-wrapped UUIDv7 identity; legacy UUIDs kept | Amends draft 3 | 3 |
| D4 | One global SQLite registry, zero JSON | Replaces draft 4 by operator override | 18 |
| D5 | Zero tolerance for unknown fields | Accepts draft 5 | 4.2 |
| D6 | Rich headers populated by tools | New | 20 |
| D7 | Restricted YAML subset and canonical serializer | New | 16 |
| D8 | Carrier matrix with host-preserving placement | New | 17 |
| D9 | Scoped authority, separate from role | New | 8 |
| D10 | Three separate clocks; no invented dates | New | 9 |
| D11 | Qualified relations and typed claims | New | 11, 12 |
| D12 | Tool-enforced lifecycle state machine | New | 7 |
| D13 | Exact release resolution and versioned profiles | New | 6, 23 |
| D14 | Compiler-grade diagnostics | New | 19.2 |
| D15 | Dead-code isolation in `archive/` | New | 1 |
| D16 | Non-interactive header edits with `somnus set` | New (after the build) | 20 |
| D17 | MCP server as a thin CLI adapter | New (after the build; applies D4) | 20 |
| D18 | Closed warning registry; duplicate titles remain advisory | Documentation correction, no new fuzzy-title rule | 19.2 |
| D19 | Full-text search as a derived registry index | Applies D4; package 2.1.0 and registry schema 2, core unchanged | 18.4, 20 |

## The most consequential decisions

### D1: one `somnus:` namespace

v0.1 put `id`, `title`, `slug`, and similar keys at the frontmatter root so that Hugo, Jekyll, and Obsidian could read them. In practice those root keys collide with host keys that mean something different, and a root-level payload cannot be carried unchanged into a TeX, TOML, or code comment. D1 puts every standardized field under one `somnus:` mapping. Other frontmatter keys belong to the host, are preserved byte-for-byte, and are never read as Somnus values. A tool that needs `title` keeps its own root key, and the two titles are never reconciled automatically. This is why the same payload validates in every carrier (fixture 1) and why v0.1 roots are converted only by `somnus migrate`.

### D2: comment-marker regions

v0.1 marked regions with `:::submatter` container directives. Those render as visible fence text on GitHub and most viewers, and they put attributes in the body where agents edit them without validation. D2 uses paired comments, `<!-- somnus:region:begin <id> -->` and `<!-- somnus:region:end <id> -->` (or the host's comment prefix), that carry only identity. Attributes live in `knowledge.regions` in the header, where the schema validates them. Pairing is stack-based: nesting is allowed, while crossing, unclosed, and duplicate markers are errors. Markers inside code fences, indented code, or the envelope are inert.

### D4: one global SQLite registry, zero JSON

The earlier draft proposed a two-tier model with external `provenance/*.json` ledgers. The operator overrode it in the draft itself:

> THIS SHOULD BE A GLOBAL .DB WITH A COMPLEX DETAILED YET HUMAN READABLE SCHEMA, WHILE ALSO REMAINING AVAILABLE TO THE MODEL. JSON IS FORBIDDEN, IT IS SLOW ON INFERENCE. ITS TOO MUCH

The result is one database at `$SOMNUS_HOME/somnus.db` (default `~/.somnus/somnus.db`) with plain-English tables and views. No column stores JSON; revision headers are stored as canonical restricted-YAML text. The `events` ledger is append-only, enforced by triggers in `src/somnus/db/schema.sql`. Documents carry no history arrays, because history lives in `revisions` and `events`. Query output is aligned text or TSV. JSON appears only where an external format requires it: the JSON Schema export (`somnus schema --json-schema`), json-pointer selectors into JSON hosts, and MCP JSON-RPC framing under D17. This decision is why `AGENTS.md` says "Registry output is text/TSV; JSON is forbidden there (D4)." MCP tool content remains the command's text output.

### D5: zero tolerance for unknown fields

Every standardized object is closed. An unknown field at any depth is `E_SCHEMA`, and `null` is forbidden. The only open locations are `extensions.<owner>.data`, a claim's `object.value`, and profile payloads (validated by their own profile schema). Typos and invented keys therefore fail at core level instead of silently entering the registry. Experimental data goes under `extensions.<owner>`, which tools preserve losslessly but never feed into trusted registry tables (fixture 11).

### D9: scoped authority, separate from role

`authority.standing` (`unasserted`, `candidate`, `accepted`, `retired`, `rejected`) is scoped by `{target_ref, aspects}` and is independent of `classification.role`. A document whose role is `normative` describes intent; it is not thereby accepted. `accepted` requires a `valid_time` and an `acceptance_ref`, and at canon level that reference must resolve to an active `decision-record`. Two overlapping accepted authorities open an `authority` conflict, and neither recency nor source order breaks the tie (fixture 15). New artifacts default to `candidate` with a self-scope, and D6 refuses a configured default standing of `accepted` because that would fabricate acceptance.

### D19: content search stays derived

D19 chooses an FTS5 table inside the existing database rather than a second search store or external grep. `src/somnus/db/search.sql` defines plain-text `path`, `title`, `summary`, `tags`, and `body` columns. `src/somnus/db/store.py` maintains one row per present location; `src/somnus/commands/query.py` implements `somnus q --text` with required words, prefix matching, BM25 ranking, and text/TSV excerpts.

The index never feeds validation, conflicts, or the event ledger. Missing rows are backfilled by an incremental scan, and `somnus index --full` refreshes content from disk. SQLite builds without FTS5 retain the registry without content search. D19 advances registry schema to 2, which older writers refuse, and package version to 2.1.0. It leaves core metadata at 2.0.0 because no artifact fields change. `docs/USAGE_GUIDE.md` now records publication of 2.1.0, superseding older unpublished-release statements in `PLAN.md`. See [Registry](../systems/registry.md), [Querying](../features/querying.md), and [Getting started](../overview/getting-started.md).

## Notes on the rest

- **D3.** New IDs are `urn:somnus:artifact:<uuidv7>`. Imported UUIDv4 and v0.1 IDs are wrapped, never reminted, and the UUID's embedded timestamp is never treated as an authored date. `urn:somnus:example:*` IDs are reserved for examples and never indexed.
- **D6.** `somnus new`, `stamp`, `fork`, and `migrate` fill in the full header from configuration. They never invent dates, actors, licenses, measurements, evidence, or acceptance, which is why `stamp` writes `time: {}` while `new` records the real creation instant.
- **D7.** A stdlib-only parser for a strict YAML subset: double-quoted strings, no anchors, aliases, tags, nulls, duplicate keys, or implicit typing. The canonical serializer makes `payload_digest` stable across tools.
- **D8.** Markdown uses frontmatter or a hidden HTML comment; code and config use comment envelopes after mandatory preambles; everything else uses a sidecar. Every write is re-extracted and refused with `E_HOST` unless the bytes outside the envelope are unchanged.
- **D10.** Authorship time (`somnus.time`), applicability (`valid_time`), and observation (registry columns) are separate. Missing dates stay missing, and a file that disappears is marked `present = 0`, never deleted.
- **D11.** Relations carry an `assessment` and `valid_time`; `supersedes`, `derived_from`, and `part_of` must be acyclic. Inverse edges are registry views, and a hypothesis stays a hypothesis even inside an accepted artifact.
- **D12.** Status changes follow the SPEC 7.1 table and are applied with `somnus status`, which creates a new revision. Reactivation resets `accepted` to `candidate`.
- **D13.** A 2.0.0 validator accepts only `somnus://metadata/core/2.0.0`. Profiles are versioned URIs bound to `profile_data` keys.
- **D14.** The `path:line:col: severity CODE field: message` format and the 0/1/2 exit codes. See [debugging](../how-to-contribute/debugging.md).
- **D15.** Old material lives in `archive/` behind a non-truth warning, `src/` never imports it, and the default index excludes `archive/**`.
- **D16.** `somnus set` changes exactly the fields the `edit` form exposes, through the same form model, in one new revision. Agents no longer hand-edit envelopes to retitle or retag a document. See [Agent integration](../features/agent-integration.md).
- **D17.** `somnus mcp` generates its tools from the CLI's argparse definitions and runs the CLI for every call. JSON is limited to the MCP framing, which D4 already permits where a format requires it, and every tool result is the command's text output.
- **D18.** Removed the undefined, never-emitted `W_DUPLICATE_TITLE` listing instead of inventing a trigger. The closed warning set is `W_PREDICATE`, `W_REGION_SPACING`, `W_REGION_UNREGISTERED`, and `W_UNMANAGED`. `somnus stale` retains advisory near-duplicate rows at similarity 0.85; `somnus new` retains collision refusal at 0.9 (`E_IO`, bypassable with `--force`). D18 classifies this as a non-breaking documentation correction: no schema enum, pattern, or field meaning changed, so core stays 2.0.0 while document revisions advance.

## Changing a decision

The last paragraph of `DECISIONS.md` sets the rule: a changed decision needs a new revision of `DECISIONS.md` (`somnus bump`) and a matching SPEC release under section 23. `AGENTS.md` also requires a new ratified decision for a material change; do not silently rewrite existing rationale. See [Development workflow](../how-to-contribute/development-workflow.md) and [Agent integration](../features/agent-integration.md).
