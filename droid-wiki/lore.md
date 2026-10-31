# Lore

This page tells the history of somnus-metadata through `22117e9` on 2026-10-31 UTC, using dates recorded in git and inside the documents. Where a commit or document does not say why something happened, the reasons given here are inferences and are marked as such. For the decisions themselves, see [design decisions](background/design-decisions.md). For how old material maps to new, see [migration context](background/migration-context.md). The current system is described in [the overview](overview/index.md) and [architecture](overview/architecture.md); workflow operation belongs in [Automation](deployment.md).

## Timeline

Git times below retain the recorded UTC-05:00 offset unless explicitly marked UTC. Dates inside documents are separate evidence, not inferred commit dates. The UTC activity buckets on [By the numbers](by-the-numbers.md) therefore place late October 11 local-time commits on October 12.

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
| 2026-10-11 22:19 | This wiki (36 pages) committed, with blank-line formatting fixes in `PLAN.md` | `f2b1b96` |
| 2026-10-11 23:42 | `somnus set` and the `somnus mcp` stdio server; D16 and D17 ratified; `SPEC.md` and `DECISIONS.md` move to revision 2 | `43ab360` |
| 2026-10-11 23:55 | Wiki updated for `somnus set`, MCP, and D16 to D17 | `8f3e094` |
| 2026-10-12 00:25 | `raw-tree.md` and two historical ZIP bundles added | `7a471c3` |
| 2026-10-20 00:40:48 | Governance guidance and navigation rewritten, `PLAN.md` becomes a maintenance handoff, and revision 3 of `SPEC.md` and `DECISIONS.md` clarifies existing D17 transport behavior | `cddea6a`; five documentation files changed, no runtime or test changes |
| 2026-10-20 00:54:40 | CI and incremental wiki-refresh workflows added | `56c2e44`; `.github/workflows/ci.yml` and `.github/workflows/droid-wiki-refresh.yml` |
| 2026-10-23 (document date) | D18 operator approval closes the warning registry without changing core 2.0.0 | `DECISIONS.md` ratification tracker; committed in `13bb888` |
| 2026-10-24 UTC (release record) | Initial 0.1.0 publication corrected to toolkit 2.0.0 under distribution name `somnus-metadata` | `runbooks/package-release.md`; prior recorded acceptance and installation evidence, not a fresh wiki-run result |
| 2026-10-24 01:14:16 (06:14:16 UTC) | Runtime hardening, TUI diagnostic capture, PTY tests, installed-package harness, D18, and release identity committed | `13bb888`; 57 files, 4,966 insertions and 188 deletions |
| 2026-10-31 (document date) | D19 accepts content search as a derived registry index | `DECISIONS.md` ratification tracker; `SPEC.md` §18.4 |
| 2026-10-31 17:07:29 (22:07:29 UTC) | Full-text search, registry schema 2, and toolkit version 2.1.0 committed; core stays 2.0.0 | `27408fa`; 21 files, 320 insertions and 43 deletions; `PLAN.md` says 2.1.0 is not yet published |
| 2026-10-31 17:41:31 (22:41:31 UTC) | Mission-first entry policy promoted; CLI adoption/search hints and MCP relative-path diagnostics added | `22117e9`; 12 files, 166 insertions and 92 deletions; `AGENTS.md`, `AGENTS.v1.md`, `SPEC.md` revision 7 |

## Eras

### Research era (before 2026-10-02, not in git)

The research document surveys existing standards (Schema.org, W3C PROV, Hugo, Obsidian, JSON Schema) and argues that Somnus needs schema enforcement on top of Markdown. The v0.1 specification, dated 2026-09-22, was derived from it. Its header credits "defense-grade-doc-engine"; the document does not establish whether that label identifies a tool, agent, or person. The v0.1 draft `DECISIONS.md` left five choices open and marked each with `TODO(needs-owner)`: the submatter mechanism, root namespacing, the identifier format, the history ledger location, and strictness on unknown fields.

### The v2 proposal (2026-10-01 to 2026-10-02)

The v2.0.0 proposal is dated 1 October 2026 and calls itself a "candidate for Daeron's adoption". It treats the research document as the v1 baseline. It was committed on 2026-10-02 together with the research, the v0.1 spec, schemas, examples, and tools, all in one commit (`5f1df5d`). The commit message reads: "added v2 personal ideas, forgot this was already being developed so we will need to re-anchor around this." That wording suggests the v2 ideas were written without the v0.1 work in view, and that the two lines then had to be reconciled.

### The 2.0.0 build (2026-10-11)

Thirteen commits in about two hours and twelve minutes produced the normative `SPEC.md`, the `somnus` package, the SQLite registry, the CLI, the TUI, and the test suites. The commit order (spec first, then foundation, model, database, commands, conformance tests, ratified decisions) suggests the work followed a plan. `PLAN.md` was committed in `df72af4`, and the ratification tracker in `DECISIONS.md` records D1 to D15 as accepted by "Operator approval of PLAN.md implementation plan (2026-10-11)".

### Agent-usability pass (2026-10-11, evening)

After the wiki landed, a review of how agents use the toolkit found two gaps. The terminal UI was the only way to change a title or tags without hand-editing an envelope, and agents without a shell could not reach the CLI at all. Commit `43ab360` closed both. `somnus set` (D16) reuses the TUI form model to apply the same edits in one revision. `somnus mcp` (D17) is a stdlib JSON-RPC server that builds its tools from the CLI's argparse definitions and runs the CLI for each call. The metadata schema did not change, so the release stayed at core 2.0.0, and the tool recorded the governance changes itself: `somnus set` on `DECISIONS.md` and `somnus bump` on `SPEC.md` took both to revision 2. The ratification tracker records D16 and D17 as an "Operator selection during the agent-usability review (2026-10-11)".

### Governance and automation handoff (2026-10-20)

Commit `cddea6a` changes the repository's entry guidance rather than its implementation. `AGENTS.md` spells out authority, host-byte preservation, verification limits, and safe handling of divergent git history. `filetree.md` becomes the current subsystem map. `PLAN.md` is explicitly a delivery and maintenance handoff, not the original build specification or permission for a new feature.

The same commit raises the managed document revisions of `SPEC.md` and `DECISIONS.md` to 3 while leaving core `somnus://metadata/core/2.0.0` and decisions D1 to D17 in place. The clarification describes existing MCP behavior: newline-delimited JSON-RPC, closed argument schemas, separate protocol and tool errors, ignored notifications and stray responses, no application state between calls, and relative paths resolved from the server's working directory. It is not a new D18 or a runtime rewrite.

At 00:54:40, `56c2e44` adds `.github/workflows/ci.yml` and `.github/workflows/droid-wiki-refresh.yml`. CI is configured for unit/conformance and semantic checks, dependency/archive-import policy guards, and an installed-wheel smoke check. Wiki automation is configured to generate with read-only repository permissions and hand pages to a separate publishing job that opens or updates a rolling pull request.

These are configured workflows, not evidence of successful hosted execution. The October 19 checkout verification recorded in `PLAN.md` reports 459 passing tests and clean semantic checks; that historical record is not a fresh run in this wiki survey, a global-install validation, or an external MCP-host compatibility result. See [Automation](deployment.md) for operational details and verification boundaries.

### Hardening and release identity (2026-10-24)

Commit `13bb888` records the next implementation changes after the agent-usability pass. Its author and committer timestamps are both **2026-10-24 01:14:16-05:00**, or **06:14:16 UTC**. The commit message is only `.`, so the mechanisms below come from its diff and the owning files, not an inferred narrative about the author's intent.

- `SPEC.md` §19.2 and `DECISIONS.md` D18 close the warning registry and remove the never-emitted `W_DUPLICATE_TITLE`. The D18 ratification tracker records operator approval on **2026-10-23**, a document date distinct from the commit timestamp. Existing near-title behavior remains: `somnus new` refuses a colliding title unless forced, while `somnus stale` reports an advisory. Core stays `somnus://metadata/core/2.0.0`.
- `src/somnus/commands/_common.py` adds `capture_notes`, while `src/somnus/tui/app.py` adds `NoteBuffer` and uses the capture context so registry diagnostics do not write over the alternate-screen editor. `tests/test_tui.py` adds real PTY cases, and `tests/acceptance/installed_package_acceptance.py` adds a separately invoked 60-check installed-package harness. It is not a discovered unittest suite.
- `pyproject.toml` and `src/somnus/__init__.py` identify toolkit **2.0.0**. The distribution is **somnus-metadata**, distinct from the unrelated PyPI `somnus`; the Python import and console command remain `somnus`. Python requires 3.11 or newer and runtime dependencies remain empty. There is no packaged agent plugin.

`runbooks/package-release.md` dates the actual publication record **2026-10-24 UTC**. It describes an initial 0.1.0 upload with stale version metadata, then the corrected 2.0.0 release, exact-wheel acceptance (60/60), 476 tests, clean semantic/mypy checks, matching artifact hashes, and a fresh public-index installation. Those are prior recorded release results, not checks rerun by this wiki refresh. The runbook explicitly does not establish that 0.1.0 was yanked, that native Windows terminal behavior passed, or that hosted CI ran. A package publication is not evidence of a Git tag or hosted release. See [deployment](deployment.md) and [testing](how-to-contribute/testing.md).

### Content search and registry schema 2 (2026-10-31)

Commit `27408fa` adds search of managed content without making the index authoritative. Its author and committer timestamps are **2026-10-31 17:07:29-05:00**, or **22:07:29 UTC**. The D19 ratification date in `DECISIONS.md` is also October 31; it records operator direction to add content search.

The new 12-line `src/somnus/db/search.sql` defines an FTS5 table with path, title, summary, tags, and body columns. `src/somnus/db/store.py` maintains one plain-text row per present managed location during scanning, backfills missing rows even when the file's timestamps have not changed, and removes rows for missing locations. `src/somnus/commands/query.py` adds read-only `somnus q --text` queries with BM25 ranking and excerpts. SQLite builds without FTS5 retain the ordinary registry. See [querying](features/querying.md) and [registry](systems/registry.md).

`pyproject.toml` and `src/somnus/__init__.py` advance toolkit identity to **2.1.0** because schema-1 tools refuse the schema-2 registry, as D19 explains in `DECISIONS.md`. `SPEC.md` remains core `somnus://metadata/core/2.0.0`; its managed revision becomes 6 and `DECISIONS.md` becomes revision 5. `PLAN.md` still records **2.0.0 as the published PyPI release** and **2.1.0 as not yet published**. The commit is not evidence of a new public release.

The October 31 entry in `PLAN.md` records 484 passing tests, semantic validation with 0 errors and 0 warnings, mypy clean across 49 source files, and installed acceptance 60/60. It also says no new Doctor scan was run. These are prior recorded results, not executions performed for this wiki refresh.

### Mission-first entry and agent hints (2026-10-31)

Commit `22117e9`, dated **2026-10-31 17:41:31-05:00** (**22:41:31 UTC**), promotes the mission-first `AGENTS.md` by operator decision and preserves the superseded entry in `AGENTS.v1.md`. `AGENTS.md` now starts with the integrated objective in `PLAN.md` and the relevant `CONTEXT.md` boundary; `.codex/OPERATING.md` remains an adaptive transition map, not a mandatory sequence or proof that its tools are installed.

The same commit addresses CLI/MCP friction. `src/somnus/commands/index.py` lists up to ten unmanaged files with preview/apply adoption hints and refuses a home-directory or filesystem-root fallback only when no roots are registered and no explicit roots were supplied. `src/somnus/db/store.py` supplies the unmanaged paths. `src/somnus/commands/query.py` includes the one optional positional word slot in `--text` search and explains empty results. Failed MCP commands with relative path arguments gain the server-working-directory note before the exit suffix in `src/somnus/mcp.py`. See [agent integration](features/agent-integration.md).

`SPEC.md` advances to revision 7 to describe search-word handling and the MCP note. Core remains 2.0.0, toolkit identity remains 2.1.0 in `pyproject.toml`, and no new product-contract decision follows D19 in `DECISIONS.md`. `tests/test_commands.py` adds two test methods; `tests/test_mcp.py` strengthens an existing method. The commit records **486 passing tests** and semantic 0/0 with mypy clean. That is distinct from the earlier 484-test search milestone and is historical commit evidence, not a new installed-package or external-host acceptance result.

## Longest-standing pieces

| File | First commit | Later changes |
| --- | --- | --- |
| `Somnus Markdown Metadata Standard Research.md` | `5f1df5d` (2026-10-02) | None. `AGENTS.md` forbids overwriting it |
| `archive/v0.1/` contents | `5f1df5d` | Moved in `91a7195` with zero content changes |
| `archive/v2-proposal/` contents | `5f1df5d` (under `docs/`) | Moved in `91a7195` with zero content changes |
| `AGENTS.md`, `filetree.md` | `5f1df5d` | Rewritten for 2.0.0 in `cc01549`, encoding fix in `dc3c981`, governance/navigation rewrite in `cddea6a`, mission-first entry/navigation update in `22117e9` |
| `DECISIONS.md` | `5f1df5d` | Rewritten in `df72af4` (242 lines added, 284 removed in this file); revision 2 in `43ab360`, revision 3 in `cddea6a` |

The research document is the only file whose bytes are unchanged since the first commit and whose path is also unchanged.

The implementation was unchanged between the agent-usability pass and the October 20 automation handoff: `git diff 43ab360 56c2e44 -- src tests` is empty. That statement no longer describes current HEAD: `13bb888` changes runtime and test files, including `src/somnus/yamlsub.py`, `src/somnus/model/validate.py`, `src/somnus/db/store.py`, `src/somnus/mcp.py`, and the TUI; `27408fa` then adds content search through the existing registry and query layers, and `22117e9` adds CLI/MCP hints. The layer spine remains the same; see [architecture](overview/architecture.md).

## Deprecated features

| v0.1 feature | Replaced by | Decision | Notes |
| --- | --- | --- | --- |
| Hybrid Semi-Flat roots (`title`, `id`, `tags` at the frontmatter root) | All fields under one `somnus:` mapping | D1 | Root keys collided with Hugo, Jekyll, and Obsidian keys. `somnus migrate` converts old roots |
| `:::submatter:<type>{...}` container directives | `<!-- somnus:region:begin <id> -->` comment-marker pairs, with attributes in `knowledge.regions` | D2 | Directives rendered as visible text on GitHub. `somnus migrate` converts them and keeps attributes under `extensions.somnus-migration` |
| JSON Schema files in `archive/v0.1/schemas/v1/` | Python field model in `src/somnus/model/schema.py`, exported on demand by `somnus schema --json-schema` | D4, D5 | JSON Schema is now generated output, not a source file |
| Two-tier ledger with `provenance/*.json` files | One global SQLite database at `$SOMNUS_HOME/somnus.db` | D4 | Tables `revisions` and `events`, append-only by trigger, no JSON columns |
| Bare UUIDv7 identifiers | `urn:somnus:artifact:<uuidv7>`, with old UUIDs wrapped rather than reminted | D3 | |
| `archive/v0.1/tools/validate.py` (1,115 lines) and `archive/v0.1/tools/operator_docs_audit.py` | `somnus check`, backed by `src/somnus/model/validate.py` (844 lines at the current snapshot) | D14, D15 | Historical paths were `tools/validate.py` and `tools/operator_docs_audit.py`; neither is active implementation |

D4 is the one decision the operator replaced directly instead of picking from the draft's options. Its context section quotes an override written into the draft: "THIS SHOULD BE A GLOBAL .DB WITH A COMPLEX DETAILED YET HUMAN READABLE SCHEMA, WHILE ALSO REMAINING AVAILABLE TO THE MODEL. JSON IS FORBIDDEN, IT IS SLOW ON INFERENCE. ITS TOO MUCH". That override never appears as its own commit. The committed draft in `5f1df5d` does not contain it, and the quote first shows up in `df72af4`. It was probably added to the working copy between those commits and folded into the ratified text.

## Major rewrites

- **Decisions record, 2026-10-11 (`df72af4`).** The five-decision v0.1 draft became fifteen ratified decisions. The file shrank from about 295 lines to 253, mostly because long option tables were replaced by short context, alternatives, decision, and consequences blocks.
- **Specification, 2026-10-11 (`db1fd5a`).** `SPEC.md` (908 lines) replaced the 1,287-line v0.1 spec rather than editing it. The old spec went to `archive/` unchanged.
- **Encoding repair, 2026-10-11 (`dc3c981`).** Every non-ASCII character in 26 files had been double-encoded (cp1252 mojibake, for example `â€”` in place of an em dash). The fix changed 168 lines in and 168 out. See [pitfalls](background/pitfalls.md).
- **Maintenance handoff, 2026-10-20 (`cddea6a`).** `PLAN.md` shrinks from 647 to 64 physical lines; `AGENTS.md` and `filetree.md` are rewritten for current authority and navigation. `SPEC.md` §20 and D17 gain transport clarification, not a new schema version. The commit changes five documentation files with 214 insertions and 719 deletions.

## Growth trajectory

Historical snapshot through `43ab360` only, retained from the October 11 survey. These are cumulative net tracked text lines (insertions minus deletions); blank lines count. They are not the current HEAD measurement on [By the numbers](by-the-numbers.md).

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
| `f2b1b96` | 2026-10-11 22:19 | 19,192 |
| `43ab360` | 2026-10-11 23:42 | 19,900 |

The last two rows leave out the 3,177 net lines of wiki pages under `droid-wiki/`. The final 19,900 figure was the non-wiki physical-line count at `43ab360`, not today's total. On that historical basis the repository more than tripled in size on October 11, with archived material making up about a quarter of the snapshot.

At the historical `56c2e44` snapshot, the same non-wiki text scope contained 91 files and 19,781 physical lines, including 4,587 historical lines in `archive/`. The lower total reflects documentation replacement as well as additions, not removal of runtime capability. Its source and test totals were 7,898 Python lines and 4,372 lines respectively. Two binary ZIP bundles are excluded from LOC.

At the `22117e9` snapshot, `src/somnus/` contained 8,138 physical Python lines in 49 files and 187 SQL lines in `src/somnus/db/schema.sql` and `src/somnus/db/search.sql`. `tests/` totaled 5,795 lines in 14 Python files: 4,870 in discovered modules and 925 in `tests/acceptance/installed_package_acceptance.py`. [By the numbers](by-the-numbers.md) uses a narrower runtime/test/configuration scope for its language chart; that snapshot's 14,966-line total is not directly comparable with the historical whole non-wiki totals above.
