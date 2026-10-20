---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a12ac7-1fd7-7079-a78f-7426391f187d"
  revision: 3
  title: "Somnus Metadata Ratified Decisions D1-D17"
  summary: "Ratified architecture decisions governing SPEC.md and the somnus toolkit."
  classification:
    category: "governance"
    type: "decision-record"
    role: "normative"
    scope: "repository"
    tags: ["decisions", "governance"]
  lifecycle:
    status: "active"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a12ac7-1fd7-7079-a78f-7426391f187d"
        aspects: ["content", "governance"]
  time:
    created_at: "2026-10-11T11:44:15+00:00"
    updated_at: "2026-10-20T04:38:57+00:00"
  names:
    slug: "somnus-metadata-decisions"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a12ac7-1fd7-7079-a78f-7426391f187d"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason", "quote"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---

# Somnus Metadata — Ratified Decisions D1–D17

These decisions govern [SPEC.md](SPEC.md) and the `somnus` toolkit in `src/somnus/`.
The operator ratified D1–D15 by approving the implementation plan ([PLAN.md](PLAN.md)),
and D16–D17 during the agent-usability review that followed the 2.0.0 build.
They supersede the five PROPOSED recommendations in the previous draft of this file.
That draft is preserved in git history (commit `5f1df5d`).

Each record gives its context, the alternatives considered, the decision, and its
consequences. SPEC section numbers are cited where the decision is enforced.

| # | Decision | Supersedes draft | SPEC |
| --- | --- | --- | --- |
| D1 | Single `somnus:` namespace | Draft 2 (Hybrid Semi-Flat), reversed | §4 |
| D2 | Comment-marker regions with a header registry | Draft 1 (container directives), reversed | §13 |
| D3 | URN-wrapped UUIDv7 identity; legacy UUIDs kept | Draft 3, amended | §3 |
| D4 | One global SQLite registry, zero JSON | Draft 4 (two-tier JSON ledger), replaced by operator | §18 |
| D5 | Zero tolerance for unknown fields | Draft 5, accepted | §4.2 |
| D6 | Rich headers populated by tools | new | §20 |
| D7 | Restricted YAML subset and canonical serializer | new | §16 |
| D8 | Carrier matrix with host-preserving placement | new | §17 |
| D9 | Scoped authority, separate from role | new | §8 |
| D10 | Three separate clocks; no invented dates | new | §9 |
| D11 | Qualified relations and typed claims | new | §11, §12 |
| D12 | Tool-enforced lifecycle state machine | new | §7 |
| D13 | Exact release resolution and versioned profiles | new | §6, §23 |
| D14 | Compiler-grade diagnostics | new | §19.2 |
| D15 | Dead-code isolation in `archive/` | new | §1 |
| D16 | Non-interactive header edits with `somnus set` | new | §20 |
| D17 | MCP server as a thin CLI adapter | new | §20 |

---

## D1 — Single `somnus:` namespace

- **Status:** ACCEPTED
- **Context:** The draft recommended Hybrid Semi-Flat roots (`title`, `id`, `tags`
  at the frontmatter root) for third-party tool compatibility. In practice, root
  keys collide with Hugo, Jekyll, and Obsidian keys whose meaning differs, and
  one payload could not travel unchanged into comment carriers (TeX, TOML, code).
- **Alternatives:** (A) Hybrid Semi-Flat roots. (B) Every standardized field under
  one `somnus:` mapping.
- **Decision:** (B). All standardized metadata lives under `somnus:`. Other
  frontmatter keys belong to the host, are preserved byte-for-byte, and are
  never read as Somnus values.
- **Consequences:** The same payload is valid in every carrier (SPEC §21
  fixture 1). Third-party tools that need `title` keep their own root key, and
  the two are never reconciled automatically. v0.1 roots are converted only by
  `somnus migrate`.

## D2 — Comment-marker regions with a header registry

- **Status:** ACCEPTED
- **Context:** The draft recommended `:::submatter` container directives. Directives
  render as visible fence text on GitHub and most viewers. They also put
  attributes in the body, where agents edit them without validation.
- **Alternatives:** (A) Container directives. (B) Paired comment markers that carry
  identity only, with attributes held in `knowledge.regions`.
- **Decision:** (B). Markers are `<!-- somnus:region:begin <id> -->` …
  `<!-- somnus:region:end <id> -->`, or the host's comment prefix. Pairing is
  stack-based: nesting is allowed; crossing, unclosed, and duplicate markers are
  errors. Markers in code fences, indented code, or the envelope are inert.
- **Consequences:** Rendered output is clean, and region attributes are
  schema-validated. `:::submatter` survives only as a migration input;
  `somnus migrate` converts directives to marker pairs and keeps their attributes
  under `extensions.somnus-migration`.

## D3 — URN-wrapped UUIDv7 identity; legacy UUIDs kept

- **Status:** ACCEPTED (amends draft 3)
- **Context:** UUIDv7 was already the draft's choice. Two problems remained.
  Bare UUIDs cannot be distinguished from other identifiers in references, and
  the draft required UUID timestamps to be coherent with `created_at`, which
  breaks for imported historical documents.
- **Decision:** New artifacts get `urn:somnus:artifact:<uuidv7>`. Imported UUIDv4
  and v0.1 identities are wrapped, never reminted. The UUID timestamp is never
  treated as an authored date. `urn:somnus:example:*` IDs are reserved for
  examples and are never indexed.
- **Consequences:** Fixtures 9 and 10 hold. Validators check URN shape, not
  timestamp/creation coherence. A slug never resolves identity.

## D4 — One global SQLite registry, zero JSON

- **Status:** ACCEPTED (operator replacement of draft 4)
- **Context:** The draft recommended a two-tier model with external
  `provenance/*.json` ledgers. The operator overrode this in the draft itself:

  > THIS SHOULD BE A GLOBAL .DB WITH A COMPLEX DETAILED YET HUMAN READABLE SCHEMA,
  > WHILE ALSO REMAINING AVAILABLE TO THE MODEL. JSON IS FORBIDDEN, IT IS SLOW ON
  > INFERENCE. ITS TOO MUCH
- **Decision:** One SQLite database at `$SOMNUS_HOME/somnus.db` (default
  `~/.somnus/somnus.db`) with plain-English tables and views (`docs`,
  `open_conflicts`, `history`). No column stores JSON. Revision headers are stored
  as canonical restricted-YAML text. The `events` ledger is append-only and
  enforced by triggers. `somnus q` opens the database read-only.
- **Consequences:** Documents carry no history arrays; history lives in
  `revisions` and `events`. Agents query it with SQL or shortcut flags, and output
  is aligned text or TSV, never JSON. JSON appears only where a format requires
  it: the JSON Schema export (`somnus schema --json-schema`) and json-pointer
  selectors into JSON hosts.

## D5 — Zero tolerance for unknown fields

- **Status:** ACCEPTED (draft 5 as recommended)
- **Decision:** Every standardized object is closed. Unknown fields at any depth
  are `E_SCHEMA`. `null` is forbidden. The only open locations are
  `extensions.<owner>.data`, claim `object.value`, and profile payloads, which are
  validated by their own profile schema.
- **Consequences:** Typos and invented keys fail at core level. Experiments go
  under `extensions.<owner>`, which tools preserve losslessly but never feed into
  trusted registry tables (fixture 11).

## D6 — Rich headers populated by tools

- **Context:** Headers carry classification, authority, access, and ingestion.
  Hand-writing them invites invented values.
- **Decision:** `somnus new`, `stamp`, `fork`, and `migrate` populate the full
  core header from configuration defaults (CLI flag > `.somnus.toml` >
  `$SOMNUS_HOME/config.toml` > built-ins). Tools never invent dates, actors,
  licenses, measurements, evidence, or acceptance records. `stamp` therefore
  writes `time: {}`, while `new` records the real creation instant.
- **Consequences:** A configured default standing of `accepted` is refused, because
  it would fabricate acceptance.

## D7 — Restricted YAML subset and canonical serializer

- **Decision:** Headers use a strict YAML subset, parsed by a stdlib-only parser.
  Strings are double-quoted; anchors, aliases, tags, nulls, duplicate keys, and
  implicit typing are refused. Serialization is canonical: schema field order,
  quoted strings, and deterministic flow or block sequences. A carrier's
  forbidden sequences (`--`, `*/`) are escaped.
- **Consequences:** `"NO"` stays a string (fixture 5), duplicate nested keys fail
  (fixture 4), and `payload_digest` is stable across tools.

## D8 — Carrier matrix with host-preserving placement

- **Decision:**
  - Markdown uses frontmatter or a hidden HTML comment envelope.
  - Code and config hosts use line-comment envelopes (`#`, `%`, `//`, `--`) or
    block-comment envelopes (`/* */`, `<!-- -->`) in the leading comment area,
    after mandatory preambles (shebang, encoding cookie, `#Requires`, `% !TeX`,
    `@charset`, the XML declaration).
  - Everything else uses a `<file>.somnus.yaml` sidecar with one primary binding.
  - Every write re-extracts the result and refuses (`E_HOST`) unless the bytes
    outside the envelope are unchanged.
- **Consequences:** Fixtures 1–3 hold. A leading BOM is accepted and never emitted.

## D9 — Scoped authority, separate from role

- **Decision:** `authority.standing` (`unasserted`, `candidate`, `accepted`,
  `retired`, `rejected`) is scoped by `{target_ref, aspects}`, independent of
  `classification.role`. `accepted` requires `valid_time` and an `acceptance_ref`.
  At canon level, that reference must resolve to an active `decision-record`.
  Overlapping accepted authorities open a registry `authority` conflict. Recency
  and source order never break ties.
- **Consequences:** `normative` describes intent and never grants acceptance.
  Fixture 15 holds. New artifacts default to `candidate` with a self-scope.

## D10 — Three separate clocks; no invented dates

- **Decision:** Authorship time lives in `somnus.time`. Applicability lives in
  `valid_time` (`bounded`, `open`, `timeless`, `unknown`). Observation lives in
  the registry (`observed_at`, `first_seen_at`, `last_seen_at`). Dates are never
  converted to fabricated midnight instants. Intervals are half-open.
- **Consequences:** A missing date stays missing. Disappearance during a scan
  marks `present = 0`; it is never a deletion or tombstone (fixture 20).

## D11 — Qualified relations and typed claims

- **Decision:** Relations are records with an `assessment` and a `valid_time`,
  replacing v0.1's bare reference buckets. The predicate table defines inverse
  views and cycle policy (`supersedes`, `derived_from`, and `part_of` are acyclic,
  both within a document and across the registry). Inverse edges are registry
  views; no tool rewrites another artifact. Claims keep their declared `kind`
  verbatim, so a hypothesis in an accepted artifact remains a hypothesis
  (fixture 17). Entity labels never merge identities (fixture 16).

## D12 — Tool-enforced lifecycle state machine

- **Decision:** `lifecycle.status` follows the transition table in SPEC §7.1.
  Abandonment and reactivation require a reason. `superseded` requires
  replacement references. Reactivation resets `accepted` to `candidate`. Every
  transition creates a new revision, applied with `somnus status` rather than by
  hand.

## D13 — Exact release resolution and versioned profiles

- **Decision:** A 2.0.0 validator accepts only `somnus://metadata/core/2.0.0`.
  Profiles are versioned URIs (`specification/1.0.0`, `benchmark/1.0.0`) declared
  in `profiles` and bound to equal `profile_data` keys. An unknown release or
  profile keeps the source but refuses semantic acceptance (fixture 12). v0.1
  documents migrate under the
  `somnus://metadata/extension/migration-v0.1/1.0.0` extension.

## D14 — Compiler-grade diagnostics

- **Decision:** Diagnostics print as `path:line:col: severity CODE field: message`.
  `--tsv` gives the same information tab-separated. Codes are stable (`E_*`
  errors, `W_*` warnings). Exit codes: `0` clean, `1` validation errors, refusals,
  or conflicts, `2` usage, I/O, or environment errors.
- **Consequences:** Output is greppable and cheap for agents to consume, with no
  JSON envelope.

## D15 — Dead-code isolation in `archive/`

- **Decision:** The v0.1 specification, schemas, examples, tools, and the v2
  proposal live under `archive/` behind a non-truth warning
  ([archive/README.md](archive/README.md)). Nothing in `src/` imports from
  `archive/`, and the default index configuration excludes `archive/**`.
  Archived v0.1 examples remain useful as migration test inputs.

## D16 — Non-interactive header edits with `somnus set`

- **Status:** ACCEPTED
- **Context:** The `somnus edit` form changes ten header fields with vocabulary
  checks, a revision bump, a host-preserving write, and a registry event. Agents
  cannot drive a full-screen terminal UI, so they edited the envelope by hand.
  Hand edits skip the revision bump and the event, and comment envelopes and
  sidecars are easy to break.
- **Alternatives:** (A) Hand edits followed by `somnus bump`. (B) A general setter
  for any field path. (C) A command limited to the form's fields that shares the
  form's code.
- **Decision:** (C). `somnus set PATH FIELD=VALUE…` accepts exactly the fields in
  `FIELDS` (`src/somnus/tui/form.py`) and applies them through the same form
  model. All assignments land in one new revision, and a call that changes no
  value writes nothing. Identity, revision, lifecycle, authority, and time stay
  with their dedicated commands.
- **Consequences:** The TUI and the CLI cannot disagree about which fields are
  editable or how values are parsed. Widening the settable set means changing
  `FIELDS`, which changes both surfaces together.

## D17 — MCP server as a thin CLI adapter

- **Status:** ACCEPTED (applies D4)
- **Context:** Agents with a shell already use the CLI. Clients without a shell, or
  that prefer typed tools, need a Model Context Protocol server. The MCP stdio
  transport is JSON-RPC, while D4 keeps JSON out of the registry and out of
  toolkit output.
- **Alternatives:** (A) No server. (B) A server with its own logic and JSON
  results. (C) A stdlib server whose tools are generated from the CLI's argument
  parser and whose calls run the CLI.
- **Decision:** (C). `somnus mcp` serves newline-delimited JSON-RPC 2.0 on stdio.
  Each tool is one CLI command, except the interactive `edit`. Its input schema
  comes from that command's argparse definition, and each call runs the command
  in a child process. The result is the command's text or TSV output, and a
  non-zero exit sets `isError`. The `initialize` response carries the `somnus brief`
  text as server instructions, and `--actor` given to `somnus mcp` is passed to
  every call. Tool argument schemas are closed; tool-call output is one text
  item, while protocol/parameter failures use JSON-RPC errors. The server emits
  no application state across calls; relative paths resolve from its working
  directory. The detailed transport behavior is specified in SPEC §20.
- **Consequences:** JSON appears only as MCP framing, which D4 already allows
  where a format requires it. The registry and every tool result stay JSON-free.
  A new CLI command or flag becomes an MCP tool or parameter with no server
  change, and the server keeps no state between calls.

---

## Ratification tracker

| Decision | Status | Ratified by |
| --- | --- | --- |
| D1–D15 | ACCEPTED | Operator approval of PLAN.md implementation plan (2026-10-11) |
| D16–D17 | ACCEPTED | Operator selection during the agent-usability review (2026-10-11) |

Changing a decision requires a new revision of this document (`somnus bump`) and a
matching SPEC release under §23.
