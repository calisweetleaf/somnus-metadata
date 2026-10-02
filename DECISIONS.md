# SOMNUS METADATA — OPEN DECISIONS RECORD

```text
DOCUMENT TITLE:  Somnus Metadata Open Decisions with Recommendations
Classification:  INTERNAL
Version:         0.1.0
Date:            2026-09-22
Author/Origin:   defense-grade-doc-engine (derived from Somnus Markdown Metadata
                 Standard Research.md, Section "Remaining Design Choices")
Status:          PROPOSED (no decision below is ACCEPTED until signed by owner)
```

> Each decision carries an explicit RECOMMENDED choice, trade-off analysis, and
> evidence citation. Status is PROPOSED throughout. Ratification flips individual
> decisions to ACCEPTED; partial acceptance is permitted. Items awaiting a human
> are marked `TODO(needs-owner)`.

## Executive Summary

Five architectural choices were left explicitly open by the research phase: the in-body submatter mechanism, frontmatter root namespacing, primary identifier format, history ledger location, and strictness on unknown fields. This record recommends container directives, Hybrid Semi-Flat roots, UUIDv7 identity, the two-tier ledger model, and zero-tolerance validation with an extensions escape hatch. Each recommendation preserves third-party compatibility, machine verifiability, and token economy for AI agents while deferring only implementation and hosting details to the operator.

## Table of Contents

1. Decision Status Convention
2. Decision 1 — Primary Submatter Mechanism
3. Decision 2 — Frontmatter Root Namespacing
4. Decision 3 — Identifier Format
5. Decision 4 — History Ledger Location
6. Decision 5 — Strictness on Unknown Fields
7. Cross-Decision Consistency Check
8. Ratification Tracker

---

## 1. Decision Status Convention

| Status | Meaning |
|---|---|
| PROPOSED | Recommended choice recorded; no operator sign-off. All five decisions are at this status. |
| ACCEPTED | Operator has ratified the recommendation; `SOMNUS-METADATA-SPEC-v0.1.md` governs. |
| AMENDED | Operator has chosen the non-recommended option or a hybrid; specification REQUIRES update before C2 claims. |
| DEFERRED | Decision explicitly postponed; affected specification sections MUST be treated as informative. |

---

## 2. Decision 1 — Primary Submatter Mechanism

- Status: PROPOSED
- Options: (A) Generic Container Directives (`:::submatter:<type>{...}`) / (B) HTML Comments (`<!-- somnus:submatter ... -->`)

### 2.1 Trade-off analysis

| Criterion (14-point research matrix) | (A) Container Directives | (B) HTML Comments |
|---|---|---|
| Inner Markdown AST parsing | YES — first-class `containerDirective` parent node; headings, lists, emphasis parse normally | YES — body Markdown unaffected (comment is invisible) |
| Nesting | Excellent — arbitrary depth via fence-length increment (`::::` wraps `:::`) | Poor — comments cannot nest; overlapping regions REQUIRE regex bookkeeping |
| Rendered output (GitHub/plain) | Visible literal-text fences on engines without directive support | Hidden — omitted from display |
| Programmatic editing | High — AST node transforms (mdast; Python via mdit-equivalent ports) | High — regex/string splice, but fragile at boundaries |
| Standard stability | De facto standard (mdast RFC; CommonMark Directives Proposal) | Standard CommonMark (comments are HTML Block Types 1–5) |
| Disqualifier check | None | Nesting incapacity disqualifies (B) for documents with stacked invariants/decisions/evidence |

### 2.2 Evidence

- CommonMark Section 4.6 Types 6–7: custom HTML container elements suppress inner
  Markdown parsing and GitHub sanitization strips custom tags — Directives avoid
  this entire failure class (research Sections "CommonMark HTML Block Hazard",
  "Why Directives Outperform").
- 14-criterion evaluation matrix: Directives lead on nesting, AST integration, and
  delimiter balancing; Comments lead only on render invisibility
  (research "Detailed Comparison of Candidate Submatter Mechanisms").
- AI ergonomics: `id`-anchored fences give deterministic edit anchors for
  partial-document updates (research "Partial Document Editing and Block Stability").

### 2.3 RECOMMENDED choice

**(A) Generic Container Directives** as the primary and only normative submatter
mechanism in v0.1, per `SOMNUS-METADATA-SPEC-v0.1.md` Section 13.

The visible-fence cost on unextended renderers is accepted because correctness
(nesting, AST fidelity, no sanitizer stripping) dominates invisibility for
normative content. HTML comments MAY be used for purely presentational
annotations but MUST NOT carry normative submatter semantics and MUST NOT be
validated as submatter.

### 2.4 Implications of acceptance

- Editor/validator work centers on directive parsing (mdast-compatible AST),
  not comment-regex extraction.
- Authors accept `:::` fence lines in raw source and in plain-GitHub rendering.

`TODO(needs-owner): ratify Decision 1 (A). If (B) is preferred, Sections 13 and 16
of the specification REQUIRE rewrite and the nesting requirement MUST be restated.`

---

## 3. Decision 2 — Frontmatter Root Namespacing

- Status: PROPOSED
- Options: (A) Hybrid Semi-Flat (core identity fields at root; operational namespaces grouped) / (B) Strict Namespacing (every field under a single `somnus:` key)

### 3.1 Trade-off analysis

| Dimension | (A) Hybrid Semi-Flat | (B) Strict Namespacing |
|---|---|---|
| Third-party indexing (Obsidian, Hugo, static generators reading `title`/`tags` natively) | Preserved — `title`, `tags` visible at expected locations | Degraded — tools see one opaque `somnus` blob |
| Collision risk with third-party keys | Non-zero; mitigated by profile scoping + closed validation | Zero by construction |
| Schema enforcement | Achievable — `unevaluatedProperties: false` at composition root still rejects strays | Achievable — identical guarantees |
| AI ergonomics (flat roots, Section 16) | Aligned — minimal nesting depth | Opposed — every access adds one nesting level |
| Migration cost from existing Markdown estates | Low — `title`/`tags` carry over | High — every file rewritten |

### 3.2 Evidence

- Research candidate architecture adopts Hybrid Semi-Flat explicitly to balance
  compatibility with collision resistance ("Frontmatter Grammar: Hybrid
  Semi-Flat Root Structure").
- Docs-as-code precedent: Jekyll/Hugo/Obsidian ecosystems assume root-level
  `title` and tag-like keys; Strict namespacing breaks that contract silently.
- Collision residual under (A) is bounded: profile payloads are single-key scoped
  (Section 12.2) and unknown root keys fail C2, so collisions surface as errors
  rather than silent merges.

### 3.3 RECOMMENDED choice

**(A) Hybrid Semi-Flat**, per specification Section 5. Property-name casing is
additionally fixed (`snake_case` names; kebab-case values) to close the
research inconsistency.

### 3.4 Implications of acceptance

- `title`, `id`, `slug`, temporal markers remain root-level; validators enforce
  closure rather than relying on namespacing for safety.
- Any future root-key addition REQUIRES a MINOR or MAJOR revision, never ad hoc growth.

`TODO(needs-owner): ratify Decision 2 (A). If (B) is preferred, Section 5 and
Appendix A REQUIRE full rewrite and third-party compatibility claims MUST be struck.`

---

## 4. Decision 3 — Identifier Format

- Status: PROPOSED
- Options: (A) UUIDv7 hex string (`0195e364-bb40-…`, 36 chars) / (B) ULID Base32 string (`01ARZ3NDEKTSV4RRFFQ69G5FAV`, 26 chars)

### 4.1 Trade-off analysis

| Dimension | (A) UUIDv7 (RFC 9562) | (B) ULID |
|---|---|---|
| Standardization | Formal IETF standard (RFC 9562) | Specification, not RFC; no formal standards-track status |
| Time-sortability | Yes — 48-bit big-endian millisecond timestamp prefix | Yes — 48-bit millisecond prefix |
| Collision resistance (decentralized minting) | High — 74 bits entropy + timestamp; zero coordination | High — 80 bits entropy + timestamp; zero coordination |
| Database/parser support | Native UUID type and parser recognition across standard databases and schema engines | Requires custom codec or string handling in UUID-typed stores |
| Human compactness | Moderate — 36 chars with dashes | Higher — 26 Base32 chars |
| Index behavior | Chronologically sortable without frontmatter parsing | Chronologically sortable without frontmatter parsing |

### 4.2 Evidence

- Research identifier evaluation table rates UUIDv7 as "Optimal Standard" and ULID
  as a strong but non-standard candidate lacking native UUID parser recognition.
- UUIDv7's timestamp prefix delivers the required "sortable without parsing"
  property with zero additional infrastructure; ULID's only advantage (8 fewer
  characters) does not offset standards-track and database-type costs.
- Git blob hashes and slugs were evaluated and rejected as primary keys
  (content-instability and collision/rename fragility respectively); that
  rejection is adopted without revisit.

### 4.3 RECOMMENDED choice

**(A) UUIDv7 hex string** as the mandatory primary `id` for all artifacts, per
specification Section 11. ULID MUST NOT be emitted as primary identity in v0.1.
Bare-UUID and `urn:somnus:doc:<uuid>` target forms are both accepted with
normalization (Section 10.1).

### 4.4 Implications of acceptance

- Generators mint RFC 9562 v7 UUIDs; validators check version/variant nibbles and
  timestamp/`created_at` coherence.
- Any future identifier migration (e.g., to a successor RFC) is a MAJOR revision.

`TODO(needs-owner): ratify Decision 3 (A). If (B) is preferred, Sections 7, 10, 11,
and 17 REQUIRE rewrite and database-compatibility claims MUST be re-evidenced.`

---

## 5. Decision 4 — History Ledger Location

- Status: PROPOSED
- Options: (A) Two-Tier Model (frontmatter summary + external `provenance/*.json` ledger) / (B) In-Document Event Log (append every edit to an inline `events:` list)

### 5.1 Trade-off analysis

| Dimension | (A) Two-Tier | (B) In-Document Log |
|---|---|---|
| Frontmatter size over long lifecycles | Bounded — summary only; granular events offloaded | Unbounded growth — every edit appends YAML |
| Git merge behavior | Clean — small stable header; history edits land in separate ledger files | Conflict-prone — concurrent edits to the same `events:` list collide |
| AI token economy | Lean — context windows carry origin + latest state, not full history | Bloated — full history inflates every ingestion |
| Self-containment (single-file portability) | Weaker — file plus ledger reference travel together | Stronger — one file carries everything |
| Verification surface | Ledger is an explicit tamper-evidence boundary (version-controlled, append-only policy) | History is as mutable as the file itself; no separation |
| Duplication with version control | Minimal — ledger stores semantic events, Git stores bytes | High — event log restates what Git already records |

### 5.2 Evidence

- Research "Balanced Provenance Header Design" infers Two-Tier from merge-conflict,
  token-overhead, and Git-duplication analysis; the candidate frontmatter carries
  only `history_ledger` as a pointer.
- Transient pre-commit `transient_events` with hook-driven flush is the documented
  bridge for multi-agent handoffs, preserving (B)'s capture fidelity without (B)'s
  committed bloat.

### 5.3 RECOMMENDED choice

**(A) Two-Tier Model**, per specification Section 9. Committed documents MUST NOT
contain inline unbounded event arrays; working-tree `transient_events` MUST be
flushed to the ledger before commit.

### 5.4 Implications of acceptance

- Repositories adopt a ledger convention and event schema (currently
  `TODO(needs-owner)` — illustrative research form is
  `provenance/ledger/<date>-<id>.json`; no path contract is created in v0.1).
- Validators check Tier 1 presence and ledger-reference resolvability at C3 where
  corpus access exists.

`TODO(needs-owner): ratify Decision 4 (A) AND define the ledger location convention
and event schema (specification Section 9.4, TODO D-5). If (B) is preferred,
Section 9 REQUIRES rewrite and token/merge disciplines MUST be re-specified.`

---

## 6. Decision 5 — Strictness on Unknown Fields

- Status: PROPOSED
- Options: (A) Zero Tolerance (`unevaluatedProperties: false`; unknown fields fail C2) / (B) Permissive Warnings (linter flags without exit failure)

### 6.1 Trade-off analysis

| Dimension | (A) Zero Tolerance | (B) Permissive Warnings |
|---|---|---|
| Typo capture (`authur:` for `author:`) | Immediate failure at C2 | Silent drift until a human notices |
| Schema-drift prevention in agent-authored estates | Strong — hallucinations like `status: review-ready` are rejected | Weak — plausible inventions accumulate |
| Rapid human prototyping friction | Higher — experiments must use `extensions` | Lower — anything goes with a warning |
| Pipeline safety for normative artifacts | Guaranteed — downstream indexers see only known shapes | At risk — unknown shapes propagate |
| Escape hatch availability | Yes — `extensions` mapping is open by design (Section 12.4) | Unnecessary — openness is default |

### 6.2 Evidence

- JSON Schema Draft 2020-12 `unevaluatedProperties` semantics exist precisely to
  close the historic `allOf` + `additionalProperties` gap; the research selects
  this keyword for strict composition ("Schema Composition Mechanics",
  "Handling Unknown Fields").
- Closed Core with Open Extension Escape Hatch is the research's stated synthesis:
  strictness where it prevents corruption, openness where it permits experiment —
  which is option (A) with a designed outlet, not option (B).

### 6.3 RECOMMENDED choice

**(A) Zero Tolerance with the `extensions` escape hatch**, per specification
Sections 2, 12.4, and 17.2. Unknown root or core-namespace properties are C2
errors. Content confined to `extensions` MUST NOT affect the C2 verdict.

### 6.4 Implications of acceptance

- CI gates fail on misspellings and invented keys; contributors route experiments
  through `extensions` and promote via schema revision.
- Prototype-heavy workflows SHOULD provide a documented waiver path (e.g.,
  `notepad` type at C1) rather than relaxing global strictness.

`TODO(needs-owner): ratify Decision 5 (A). If (B) is preferred, Sections 2, 12.4,
and 17.2 REQUIRE rewrite and the conformance-level definitions MUST change.`

---

## 7. Cross-Decision Consistency Check

| Pair | Consistency |
|---|---|
| 1 (Directives) + 2 (Hybrid Semi-Flat) | Consistent — both favor AST fidelity and third-party readability over invisibility/encapsulation. |
| 1 (Directives) + 5 (Zero Tolerance) | Consistent — strictness at the frontmatter layer is paired with structured (not free-text) flexibility in the body layer. |
| 2 (Hybrid) + 5 (Zero Tolerance) | Mutually supporting — Hybrid's collision residual is contained by Zero Tolerance's rejection of unknown keys. |
| 3 (UUIDv7) + 4 (Two-Tier) | Consistent — stable time-sortable identity anchors external ledger references across moves. |
| 4 (Two-Tier) + 5 (Zero Tolerance) | Consistent — bounded Tier 1 keeps the closed schema small; unbounded history lives outside the validated envelope. |

No recommended combination creates a contradiction. Adopting any non-recommended
option in isolation is viable but REQUIRES the section rewrites noted per decision.

---

## 8. Ratification Tracker

| Decision | Recommended | Status | Owner sign-off |
|---|---|---|---|
| 1. Submatter mechanism | (A) Container Directives | PROPOSED | `TODO(needs-owner)` |
| 2. Root namespacing | (A) Hybrid Semi-Flat | PROPOSED | `TODO(needs-owner)` |
| 3. Identifier format | (A) UUIDv7 | PROPOSED | `TODO(needs-owner)` |
| 4. Ledger location | (A) Two-Tier | PROPOSED | `TODO(needs-owner)` |
| 5. Unknown-field strictness | (A) Zero Tolerance + extensions | PROPOSED | `TODO(needs-owner)` |
