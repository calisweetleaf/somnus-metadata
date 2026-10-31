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
- `DECISIONS.md` records ratified rationale D1–D19. Do not silently revise a
  decision; add a new ratified decision for a material change.
- `PLAN.md` is a current delivery/maintenance handoff, not the normative source.
- `tests/test_conformance.py` is the executable 21-fixture acceptance suite.
- `src/somnus/` is implementation truth; tests are behavioral evidence.
- `filetree.md` is the navigation map. Use it to locate the subsystem before
  deep traversal.
- `CONTRIBUTING.md` documents contributor setup, the observed naming
  conventions, and the dependency release-age policy (dev and CI dependency
  bumps wait at least 7 days after release).
- `runbooks/` holds incident runbooks: registry recovery and reconciliation
  (`runbooks/registry-recovery.md`) and host-write incidents / E_HOST response
  (`runbooks/host-write-incident.md`).
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
python -m mypy   # dev tool; install with: pip install "mypy>=1.9"
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


## Composed operator route (2026-10-23)

- Read `PLAN.md` for current evidence/frontier and `CONTEXT.md` for relationships
  and tool-state boundaries. Do not reconstruct the whole repository each turn.
- Follow `.codex/OPERATING.md` for the Golden Path state transitions and the
  BB7 + topology + Surgeon + Doctor + Code Forge composition. Use the instruments
  proactively; do not replace judgment with compulsory bootstrap ceremonies.
- On first adoption, read
  `docs/references-unrelated-to-codebase/The-House-that-Had-to-be-Real.md` fully.
  Preserve authored mechanisms, carry connections into runtime, and leave a
  working surface. Small construction units do not shrink the system objective.
- BB7 owns cognitive continuity; inspect live schemas before calls. Codex uses
  ALL_TOOLS/direct calls; search_tool/use_tool is conditional on the actual host.
  Degraded recommendations do not authorize abandoning the working substrate or
  stopping independent work. No shared-data/model mutation is implied.
- For code connections, use a fresh graph/caller/impact surface before repeated
  text hunting, then inspect decisive source with Surgeon. Doctor is static
  diagnostics, graphs are structural evidence, and native execution proves only
  the exercised boundary. Do not conflate them.
- For Python work, apply the forge construction/promotion discipline and
  fieldkit baseline/repair/native-test/rescan loop. Preserve src/somnus and tests;
  resolve skill-layout conflicts explicitly before claiming full promotion.
- Record diagnostic failures and dispositions in PLAN; no suppressed findings,
  threshold weakening, or mass reformatting to satisfy a readiness score.
- Existing global hooks remain owned by their installed adapters. The local
  .codex route is documentation, not a claim that a project hook is installed.
- `AGENTS.template.v2.md` remains a preserved imported proposal;
  `AGENTS.somnus.v2.md` is the project-specific comparison candidate. Neither
  silently replaces this active entry file. Do not delete or auto-swap them.
