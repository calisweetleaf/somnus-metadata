# AGENTS.md — somnus-metadata

## What this workspace is

The Somnus metadata standard, core `somnus://metadata/core/2.0.0`, with a stdlib-only Python
toolkit (`somnus` CLI, global SQLite registry, terminal UI). Every managed file carries exactly
one `somnus:` header in frontmatter, a comment envelope, or a `<file>.somnus.yaml` sidecar.

## Authority map

- `SPEC.md` = normative. If code and SPEC disagree, SPEC wins and the code is a bug.
- `DECISIONS.md` = ratified decisions D1–D15 explaining why SPEC is shaped as it is.
- `tests/test_conformance.py` = executable acceptance criteria (one test per SPEC §21 fixture).
- `src/somnus/` = runnable truth for validation, carriers, and the registry.
- `Somnus Markdown Metadata Standard Research.md` = evidence only (read-only; never overwrite).
- `archive/` = historical, NOT normative. Never import from it or cite it as active.
- `PLAN.md` = implementation plan; `filetree.md` = location map only.

## Entry points

- Read `SPEC.md` §3–§13 for field contracts, §16–§17 for carriers, §18 for the registry.
- Use `somnus schema FIELD` for per-field documentation; `somnus brief` for the agent cheat sheet.
- Create documents with `somnus new`, never by copying another header (that duplicates its `id`).

## Rules for agents working on Somnus-managed files

- Never hand-invent IDs, dates, actors, licenses, evidence, or acceptance records.
- Never edit `id`. Indexed changes are new revisions (`somnus bump`).
- Lifecycle changes go through `somnus status`, not hand edits.
- Unknown fields are errors; tool-specific data goes under `extensions.<owner>`.
- `normative` role is intent, not acceptance.
- Registry output is text/TSV; JSON is forbidden in the registry (D4).

## Validate

Run from the workspace root:

```
python -m unittest discover -s tests
somnus check SPEC.md DECISIONS.md --level semantic
```

Without an installed tool, use `$env:PYTHONPATH="src"; python -m somnus.cli ...` (PowerShell).
Exit codes: `0` ok, `1` validation errors/refusals/conflicts, `2` usage or I/O errors.

Python diagnostics use somnus-debug with two configs: `.somnus-debug/python_doctor.yaml`
(repo root, for tests) and `.somnus-debug/python_doctor.src.yaml` (scan root `src`, so
`somnus.*` imports resolve).

## Constraints

- Stdlib only. `pyproject.toml` declares `dependencies = []`; keep it that way.
- Never overwrite `Somnus Markdown Metadata Standard Research.md`.
- Nothing under `src/` may import from `archive/`.
- Writes to a host file must leave bytes outside the envelope unchanged (`E_HOST` otherwise).
- This folder is OneDrive-synced: multi-file Surgeon transactions (`multi_edit`, `prepare/commit`)
  fail with WinError 5. Edit one file per call.
