# Lore

This page tells the history of somnus-metadata using the dates recorded in git and inside the documents. Where a commit or document does not say why something happened, the reasons given here are inferences and are marked as such. For the decisions themselves, see [design decisions](background/design-decisions.md). For how old material maps to new, see [migration context](background/migration-context.md). The current system is described in [the overview](overview/index.md) and [the architecture page](overview/architecture.md).

## Timeline

| Date | Event | Evidence |
| --- | --- | --- |
| Before 2026-09-22 | `Somnus Markdown Metadata Standard Research.md` is written | The v0.1 spec names it as its "read-only source of truth" (685 lines) |
| 2026-09-22 | Somnus Markdown Metadata Standard v0.1 drafted, status PROPOSED | Header of `archive/v0.1/SOMNUS-METADATA-SPEC-v0.1.md` |
| 2026-10-01 | Universal metadata v2.0.0 proposal written | "Date: 1 October 2026" in `archive/v2-proposal/SOMNUS_FRONTMATTER_SPEC_v2.md` |
| 2026-10-02 00:27 | First commit `5f1df5d`: 16 files, 5,637 lines | `git log` |
| 2026-10-11 06:26 | Archive move, `SPEC.md`, package foundation, model and carriers, SQLite layer | `91a7195`, `db1fd5a`, `416834a`, `45c0554`, `ea93437` |
| 2026-10-11 06:40 | CLI dispatcher and all commands | `47bac02` |
| 2026-10-11 06:43 | SPEC §21 conformance suite (21 fixtures) | `570eac0` |
| 2026-10-11 06:46 | Decisions D1 to D15 ratified, `PLAN.md` added | `df72af4` |
| 2026-10-11 06:48 | README, archive notice, LF line endings pinned | `cc01549`, `3f835bc` |
| 2026-10-11 06:50 | Terminal UI for `somnus edit` | `b9b8c12` |
| 2026-10-11 07:05 | 443 unit tests and four bug fixes | `8f0db0d` |
| 2026-10-11 08:38 | Double-encoded UTF-8 repaired in 26 files | `dc3c981` |

## Eras

### Research era (before 2026-10-02, not in git)

The research document surveys existing standards (Schema.org, W3C PROV, Hugo, Obsidian, JSON Schema) and argues that Somnus needs schema enforcement on top of Markdown. The v0.1 specification, dated 2026-09-22, was derived from it. Its header credits "defense-grade-doc-engine", which appears to be a document-generation tool or agent rather than a person. The v0.1 draft `DECISIONS.md` left five choices open and marked each with `TODO(needs-owner)`: the submatter mechanism, root namespacing, the identifier format, the history ledger location, and strictness on unknown fields.

### The v2 proposal (2026-10-01 to 2026-10-02)

The v2.0.0 proposal is dated 1 October 2026 and calls itself a "candidate for Daeron's adoption". It treats the research document as the v1 baseline. It was committed on 2026-10-02 together with the research, the v0.1 spec, schemas, examples, and tools, all in one commit (`5f1df5d`). The commit message reads: "added v2 personal ideas, forgot this was already being developed so we will need to re-anchor around this." That wording suggests the v2 ideas were written without the v0.1 work in view, and that the two lines then had to be reconciled.

### The 2.0.0 build (2026-10-11)

Thirteen commits in about two hours and twelve minutes produced the normative `SPEC.md`, the `somnus` package, the SQLite registry, the CLI, the TUI, and the test suites. The commit order (spec first, then foundation, model, database, commands, conformance tests, ratified decisions) suggests the work followed a plan. `PLAN.md` was committed in `df72af4`, and the ratification tracker in `DECISIONS.md` records D1 to D15 as accepted by "Operator approval of PLAN.md implementation plan (2026-10-11)".

## Longest-standing pieces

| File | First commit | Later changes |
| --- | --- | --- |
| `Somnus Markdown Metadata Standard Research.md` | `5f1df5d` (2026-10-02) | None. `AGENTS.md` forbids overwriting it |
| `archive/v0.1/` contents | `5f1df5d` | Moved in `91a7195` with zero content changes |
| `archive/v2-proposal/` contents | `5f1df5d` (under `docs/`) | Moved in `91a7195` with zero content changes |
| `AGENTS.md`, `filetree.md` | `5f1df5d` | Rewritten for 2.0.0 in `cc01549`, encoding fix in `dc3c981` |
| `DECISIONS.md` | `5f1df5d` | Rewritten in `df72af4` (830 lines added, 284 removed) |

The research document is the only file whose bytes are unchanged since the first commit and whose path is also unchanged.

## Deprecated features

| v0.1 feature | Replaced by | Decision | Notes |
| --- | --- | --- | --- |
| Hybrid Semi-Flat roots (`title`, `id`, `tags` at the frontmatter root) | All fields under one `somnus:` mapping | D1 | Root keys collided with Hugo, Jekyll, and Obsidian keys. `somnus migrate` converts old roots |
| `:::submatter:<type>{...}` container directives | `<!-- somnus:region:begin <id> -->` comment-marker pairs, with attributes in `knowledge.regions` | D2 | Directives rendered as visible text on GitHub. `somnus migrate` converts them and keeps attributes under `extensions.somnus-migration` |
| JSON Schema files in `archive/v0.1/schemas/v1/` | Python field model in `src/somnus/model/schema.py`, exported on demand by `somnus schema --json-schema` | D4, D5 | JSON Schema is now generated output, not a source file |
| Two-tier ledger with `provenance/*.json` files | One global SQLite database at `$SOMNUS_HOME/somnus.db` | D4 | Tables `revisions` and `events`, append-only by trigger, no JSON columns |
| Bare UUIDv7 identifiers | `urn:somnus:artifact:<uuidv7>`, with old UUIDs wrapped rather than reminted | D3 | |
| `tools/validate.py` (1,115 lines) and `tools/operator_docs_audit.py` | `somnus check`, backed by `src/somnus/model/validate.py` (832 lines) | D14, D15 | Old tools kept in `archive/v0.1/tools/` |

D4 is the one decision the operator replaced directly instead of picking from the draft's options. Its context section quotes an override written into the draft: "THIS SHOULD BE A GLOBAL .DB WITH A COMPLEX DETAILED YET HUMAN READABLE SCHEMA, WHILE ALSO REMAINING AVAILABLE TO THE MODEL. JSON IS FORBIDDEN, IT IS SLOW ON INFERENCE. ITS TOO MUCH". That override never appears as its own commit. The committed draft in `5f1df5d` does not contain it, and the quote first shows up in `df72af4`. It was probably added to the working copy between those commits and folded into the ratified text.

## Major rewrites

- **Decisions record, 2026-10-11 (`df72af4`).** The five-decision v0.1 draft became fifteen ratified decisions. The file shrank from about 295 lines to 253, mostly because long option tables were replaced by short context, alternatives, decision, and consequences blocks.
- **Specification, 2026-10-11 (`db1fd5a`).** `SPEC.md` (908 lines) replaced the 1,287-line v0.1 spec rather than editing it. The old spec went to `archive/` unchanged.
- **Encoding repair, 2026-10-11 (`dc3c981`).** Every non-ASCII character in 26 files had been double-encoded (cp1252 mojibake, for example `â€”` in place of an em dash). The fix changed 168 lines in and 168 out. See [pitfalls](background/pitfalls.md).

## Growth trajectory

Net tracked lines after each commit (insertions minus deletions, cumulative):

| Commit | Date and time | Net lines |
| --- | --- | ---: |
| `5f1df5d` | 2026-10-02 00:27 | 5,637 |
| `91a7195` | 2026-10-11 06:26 | 5,775 |
| `db1fd5a` | 2026-10-11 06:26 | 6,683 |
| `416834a` | 2026-10-11 06:26 | 7,869 |
| `45c0554` | 2026-10-11 06:26 | 10,730 |
| `ea93437` | 2026-10-11 06:26 | 11,773 |
| `47bac02` | 2026-10-11 06:40 | 13,718 |
| `570eac0` | 2026-10-11 06:43 | 14,083 |
| `df72af4` | 2026-10-11 06:46 | 14,629 |
| `cc01549` | 2026-10-11 06:48 | 14,711 |
| `3f835bc` | 2026-10-11 06:48 | 14,713 |
| `b9b8c12` | 2026-10-11 06:50 | 16,373 |
| `8f0db0d` | 2026-10-11 07:05 | 19,133 |
| `dc3c981` | 2026-10-11 08:38 | 19,133 |

The final figure matches the 19,133 physical lines measured at `HEAD` on [the numbers page](by-the-numbers.md). The repository more than tripled in size on 2026-10-11, and the archived pre-git material now makes up about a quarter of it.
