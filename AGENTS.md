# AGENTS.md — somnus-metadata

## What this workspace is

Somnus Markdown Metadata Standard v0.1, research-to-implementation.
Research defines 9 metadata dimensions, classification enums, two-tier
provenance, UUIDv7 identity, JSON Schema Draft 2020-12 core+profiles,
`:::submatter:` directives, and a 3-stage validation pipeline.

## Current state

- Research complete: `Somnus Markdown Metadata Standard Research.md` (685 lines, read-only).
- Implementation newly added: `schemas/v1/core.json`,
  `schemas/v1/profiles/engineering-specification-v1.json`,
  `schemas/v1/profiles/engineering-benchmark-v1.json`,
  `examples/specification-example.md`, `examples/benchmark-example.md`,
  `examples/submatter-example.md`, `tools/validate.py`,
  `tools/operator_docs_audit.py`.
- TODO: SPEC.md normative spec does not exist yet; do not treat Research as normative.
- TODO: CONTEXT.md / MEMORY.md / NOTEPAD.md / TASK.md / PLAN.md continuity set missing.
- TODO: Rust binary, CST migration, full inverse-injection remain future work.

## Authority map

- `Somnus Markdown Metadata Standard Research.md` = evidence (read-only, do not overwrite).
- `SPEC.md` = normative if present; currently missing, so Research is evidence only.
- `schemas/v1/` = validation truth (core + profiles, Draft 2020-12, `unevaluatedProperties: false`).
- `examples/` = usage truth (valid frontmatter + submatter usage).
- `tools/validate.py` = runnable truth for the 3-stage pipeline.

## Entry points

- Read research first, then `schemas/v1/core.json` for field contracts.
- Copy `examples/specification-example.md` or `examples/benchmark-example.md` for new docs.
- See `filetree.md` for spatial locations (map only, not a router).

## Validate

Run from workspace root:

```
python3 tools/validate.py examples/specification-example.md
python3 tools/validate.py examples/benchmark-example.md
python3 tools/validate.py examples/submatter-example.md
python3 tools/operator_docs_audit.py --root .
```

Exit codes for `validate.py`: 0 valid, 1 validation failed, 2 I/O or frontmatter error.
`jsonschema` is optional; the validator falls back to structural checks when missing.

## Constraints

- Never overwrite `Somnus Markdown Metadata Standard Research.md`.
- Stdlib-first; no new dependencies introduced.
- Do not invent package manager, VCS, build, or cloud workflows (none declared here).
