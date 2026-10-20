# AGENTS.md — somnus-metadata

## Project state

Somnus Metadata core `somnus://metadata/core/2.0.0` is the normative standard;
`src/somnus/` is its stdlib-only Python toolkit (`somnus` CLI, global SQLite
registry, terminal UI, and stdio MCP adapter). Implemented capability is covered
by the test suites under `tests/`; do not describe an installed tool or external
MCP host as validated unless separately exercised.

## Authority and ownership

- `SPEC.md` is normative. If implementation and SPEC disagree, treat it as a
  defect; do not change the contract without an explicit decision and version
  update under SPEC §23.
- `DECISIONS.md` records ratified rationale D1–D17. Do not silently revise a
  decision; add a new ratified decision for a material change.
- `PLAN.md` is a current delivery/maintenance handoff, not the normative source.
- `tests/test_conformance.py` is the executable 21-fixture acceptance suite.
- `src/somnus/` is implementation truth; tests are behavioral evidence.
- `filetree.md` is the navigation map. Use it to locate the subsystem before
  deep traversal.
- `Somnus Markdown Metadata Standard Research.md` is evidence-only and frozen;
  never overwrite it.
- `archive/` is historical, not normative. Never import from it or cite it as
  active behavior.

## High-value paths

- `src/somnus/model/`: schema, controlled vocabulary, validation, lifecycle.
- `src/somnus/yamlsub.py`: restricted YAML parser and canonical serializer.
- `src/somnus/document.py`, `src/somnus/carriers/`: envelope IO, carrier
  placement, and host-byte preservation.
- `src/somnus/db/`: SQLite registry.
- `src/somnus/commands/`, `src/somnus/cli.py`: command behavior and CLI surface.
- `src/somnus/tui/`: terminal editor/browser; `set_fields.py` backs `somnus set`.
- `src/somnus/mcp.py`: stdio JSON-RPC adapter; D17 and SPEC §20 are its contract.
- `tests/test_conformance.py`, `tests/test_mcp.py`, and the corresponding
  module-specific tests: consumed behavior checks.

## Rules for Somnus-managed files

- Never invent IDs, dates, actors, licenses, evidence, or acceptance records.
- Never hand-edit `id`; indexed content changes create revisions through
  `somnus bump` or the owning command. Lifecycle transitions go through
  `somnus status`.
- Use `somnus set` for its documented editable fields; unknown fields are
  errors. Tool-specific metadata belongs under `extensions.<owner>`.
- `normative` role expresses intent, not acceptance. Registry output is text/TSV;
  JSON is forbidden there (D4). MCP JSON-RPC framing is the D17 exception; tool
  content remains text/TSV.
- Writes to host files must preserve bytes outside the metadata envelope
  (`E_HOST` otherwise).
- `src/` must not import from `archive/`.
- Keep `pyproject.toml` runtime dependencies empty; stdlib only.

## Verification

From the repository root on POSIX:

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
```

PowerShell equivalent for source checkout execution:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
```

With an installed `somnus`, the semantic check may use `somnus check ...`.
Exit codes: `0` success, `1` validation errors/refusals/conflicts, `2` usage,
I/O, or environment errors. A successful import, parser invocation, or test
count alone does not prove an external install or MCP client integration.

Python diagnostics use `somnus-debug` configs:
`.somnus-debug/python_doctor.yaml` (repository root) and
`.somnus-debug/python_doctor.src.yaml` (source scan root).

## Git and working-tree safety

The repository uses a local `pull.ff=only` policy: ordinary `git pull` may
advance only when it can fast-forward. Before reconciling divergence, inspect
`git status`, fetch the remote, compare ahead/behind commits and trees, and
preserve a named local ref before any re-anchor/reset. Do not force-pull or
discard a local commit merely because the ahead/behind count looks small; verify
what it contains first.

## Environment constraint

This folder is OneDrive-synced. Multi-file Surgeon transactions (`multi_edit`,
`prepare/commit`) fail with WinError 5; edit one file per call. Keep historical
and user-owned research artifacts untouched.
