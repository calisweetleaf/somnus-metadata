# ARCHIVE — HISTORICAL AND DEVOLVED ASSETS

> [!WARNING]
> The contents of this directory are preserved strictly for historical lineage.
> **THEY ARE NOT TRUTH, NOT NORMATIVE, AND MUST NOT BE IMPORTED OR CITED AS ACTIVE SPECIFICATIONS.**
> The active normative standard is defined exclusively in `SPEC.md`.

## Contents

| Path | What it was | Superseded by |
| --- | --- | --- |
| `v0.1/SOMNUS-METADATA-SPEC-v0.1.md` | v0.1 specification (flat roots, `:::submatter` directives) | `SPEC.md` |
| `v0.1/GLOSSARY.md` | v0.1 vocabulary | `SPEC.md` §2, `src/somnus/model/vocab.py` |
| `v0.1/schemas/` | v0.1 JSON Schemas | `somnus schema --json-schema` |
| `v0.1/examples/` | v0.1 example documents | `somnus new`; still used as `somnus migrate` inputs |
| `v0.1/tools/` | v0.1 validator and docs audit | `somnus check` |
| `v2-proposal/` | Intermediate v2 frontmatter proposal and diff notes | `SPEC.md`, `DECISIONS.md` |

## Rules

- Nothing under `src/` imports from `archive/` (DECISIONS.md D15).
- The default index configuration excludes `archive/**`, so these files never enter the registry.
- To bring a v0.1 document forward, run `somnus migrate PATH` and review the diff, then rerun it with `--write`.
