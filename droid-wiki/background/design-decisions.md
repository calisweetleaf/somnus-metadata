# Design decisions

`DECISIONS.md` records fifteen ratified decisions, D1 to D15, that shape `SPEC.md` and the toolkit. The operator ratified all of them on 2026-10-11 by approving the implementation plan in `PLAN.md`; they replace five PROPOSED recommendations from an earlier draft, which survives in commit `5f1df5d`.

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

## The most consequential decisions

### D1: one `somnus:` namespace

v0.1 put `id`, `title`, `slug`, and similar keys at the frontmatter root so that Hugo, Jekyll, and Obsidian could read them. In practice those root keys collide with host keys that mean something different, and a root-level payload cannot be carried unchanged into a TeX, TOML, or code comment. D1 puts every standardized field under one `somnus:` mapping. Other frontmatter keys belong to the host, are preserved byte-for-byte, and are never read as Somnus values. A tool that needs `title` keeps its own root key, and the two titles are never reconciled automatically. This is why the same payload validates in every carrier (fixture 1) and why v0.1 roots are converted only by `somnus migrate`.

### D2: comment-marker regions

v0.1 marked regions with `:::submatter` container directives. Those render as visible fence text on GitHub and most viewers, and they put attributes in the body where agents edit them without validation. D2 uses paired comments, `<!-- somnus:region:begin <id> -->` and `<!-- somnus:region:end <id> -->` (or the host's comment prefix), that carry only identity. Attributes live in `knowledge.regions` in the header, where the schema validates them. Pairing is stack-based: nesting is allowed, while crossing, unclosed, and duplicate markers are errors. Markers inside code fences, indented code, or the envelope are inert.

### D4: one global SQLite registry, zero JSON

The earlier draft proposed a two-tier model with external `provenance/*.json` ledgers. The operator overrode it in the draft itself:

> THIS SHOULD BE A GLOBAL .DB WITH A COMPLEX DETAILED YET HUMAN READABLE SCHEMA, WHILE ALSO REMAINING AVAILABLE TO THE MODEL. JSON IS FORBIDDEN, IT IS SLOW ON INFERENCE. ITS TOO MUCH

The result is one database at `$SOMNUS_HOME/somnus.db` (default `~/.somnus/somnus.db`) with plain-English tables and views. No column stores JSON; revision headers are stored as canonical restricted-YAML text. The `events` ledger is append-only, enforced by triggers in `src/somnus/db/schema.sql`. Documents carry no history arrays, because history lives in `revisions` and `events`. Query output is aligned text or TSV. JSON appears only where an external format requires it: the JSON Schema export (`somnus schema --json-schema`) and json-pointer selectors into JSON hosts. This decision is why `AGENTS.md` says "Registry output is text/TSV; JSON is forbidden in the registry."

### D5: zero tolerance for unknown fields

Every standardized object is closed. An unknown field at any depth is `E_SCHEMA`, and `null` is forbidden. The only open locations are `extensions.<owner>.data`, a claim's `object.value`, and profile payloads (validated by their own profile schema). Typos and invented keys therefore fail at core level instead of silently entering the registry. Experimental data goes under `extensions.<owner>`, which tools preserve losslessly but never feed into trusted registry tables (fixture 11).

### D9: scoped authority, separate from role

`authority.standing` (`unasserted`, `candidate`, `accepted`, `retired`, `rejected`) is scoped by `{target_ref, aspects}` and is independent of `classification.role`. A document whose role is `normative` describes intent; it is not thereby accepted. `accepted` requires a `valid_time` and an `acceptance_ref`, and at canon level that reference must resolve to an active `decision-record`. Two overlapping accepted authorities open an `authority` conflict, and neither recency nor source order breaks the tie (fixture 15). New artifacts default to `candidate` with a self-scope, and D6 refuses a configured default standing of `accepted` because that would fabricate acceptance.

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

## Changing a decision

The last paragraph of `DECISIONS.md` sets the rule: a changed decision needs a new revision of `DECISIONS.md` (`somnus bump`) and a matching SPEC release under section 23. See [development workflow](../how-to-contribute/development-workflow.md).
