# Background

This section explains why the Somnus standard and toolkit look the way they do, where they came from, and which mistakes are easy to make while working on them. It draws on `DECISIONS.md`, `archive/`, `SPEC.md` section 22, and the git history.

## Pages

| Page | Read it when |
| --- | --- |
| [Design decisions](design-decisions.md) | You want the reasoning behind a rule in `SPEC.md`, or you are thinking of changing one. Summarizes ratified decisions D1 to D19. |
| [Pitfalls](pitfalls.md) | Before editing anything. Lists the ways a change can corrupt a file, a digest, or the registry, plus environment traps on Windows and OneDrive. |
| [Migration context](migration-context.md) | You meet a v0.1 document, an `archive/` file, or `extensions.somnus-migration` data and need to know what changed between v0.1 and core 2.0.0. |

## Short history

1. **v0.1.** A Markdown-only standard with flat root keys (`id`, `title`, `slug` at the frontmatter root), `:::submatter` container directives for regions, and a two-tier provenance model with external JSON ledgers. It is preserved in `archive/v0.1/`.
2. **v2 proposal.** An intermediate frontmatter proposal by the operator (now `archive/v2-proposal/`). The first commit, `5f1df5d`, brought in the v0.1 spec, schemas, examples, research document, and this proposal together, with the note that the work needed to "re-anchor" around what already existed.
3. **Core 2.0.0.** The current standard. `SPEC.md` was written fresh (`db1fd5a`), the old material was moved behind the archive warning (`91a7195`), and the toolkit was built in layers: foundation, model and carriers, registry, CLI, conformance suite, TUI, and finally per-module unit suites (443 tests, `8f0db0d`). The decisions were ratified in `df72af4`, with D4 written to match the operator's override.

See [lore](../lore.md) for a fuller account of the project's history.

The current managed documents are `SPEC.md` revision 6 and `DECISIONS.md` revision 5. D18 removes the undefined `W_DUPLICATE_TITLE` listing as a non-breaking documentation correction; core stays `somnus://metadata/core/2.0.0`. The closed warning registry contains `W_PREDICATE`, `W_REGION_SPACING`, `W_REGION_UNREGISTERED`, and `W_UNMANAGED`. Near-duplicate titles remain registry advisories, not validation warning codes.

D19, ratified 2026-10-31 in `DECISIONS.md`, adds [full-text search](../features/querying.md) as derived registry state. `src/somnus/__init__.py` advances the package to 2.1.0 and registry schema to 2 without changing core metadata 2.0.0. `PLAN.md` records that package version as unpublished.
