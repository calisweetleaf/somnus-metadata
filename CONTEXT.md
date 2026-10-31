# Somnus Metadata — Architectural and Operator Context

Established 2026-10-23 (America/Chicago). This is relational context, not a new
normative authority. Read PLAN.md for current evidence, work and acceptance gaps.

## Current distribution state (2026-10-24 UTC)

The current toolkit release is **somnus-metadata 2.0.0** on PyPI.
The earlier 0.1.0 publication was a stale-metadata versioning error, not v1 canon. The command and
Python package stay **somnus**; the schema stays core 2.0.0. The unrelated PyPI
distribution somnus already owns that index name and must not share an
environment with this toolkit. Fresh isolated public-index installation was
verified. See runbooks/package-release.md for exact artifacts and acceptance.
GitHub remains private; no open-source license grant, commit/tag/push or plugin
publication was made. The plugin is required but deferred for official materials.
Older environment observations below describe the setup session, not release state.

## The system and its boundaries

Somnus Metadata core 2.0.0 is a standard; the somnus Python distribution is its
stdlib-only toolkit. Its current package version is 2.0.0. This repository
contains the standard and implementation; it is not the universe of files the
tool can manage. Somnus envelopes in arbitrary host files are product data, not
permission to rewrite the reference implementation mechanically.

SPEC and ratified decisions constrain behavior. Source shows the implemented
mechanism; execution shows behavior within a tested boundary. A mismatch with
SPEC is a defect unless a deliberate normative decision changes the contract.
An operational plan cannot silently change that relation.

## Functional spine

- model/schema + vocab describe payload shape; validate and lifecycle constrain
  accepted data and transitions. yamlsub owns restricted parsing/serialization.
- carriers own envelope placement/extraction; document composes those with host
  content and preservation checks. regions tracks in-document selectors/markers.
- db/store observes documents into the global SQLite registry and reconciles
  identities, revisions, locations and conflicts.
- commands compose those owners. cli declares the command surface; mcp projects
  non-interactive commands through stdio JSON-RPC with text/TSV tool content.
- tui is a real terminal consumer of shared document/command machinery, not a
  separate metadata implementation. Its failure/display paths need real-terminal
  evidence in addition to form/widget tests.

The TUI save chain is now a resolved seam. EditorScreen.save bumps the payload
revision, commits through commands/_common.py (render, validate, atomic write),
then calls Ctx.record, which observes through Store and can surface registry
diagnostic errors through note. Because note is the process's informational
channel and many modules bind it at import time, _common.py now holds a
process-wide sink: capture_notes(sink) redirects note for the duration of a block
and restores the previous sink afterwards. tui/app.py installs a NoteBuffer as that
sink for the whole alternate-screen session, and both screens drain it into their
status line before every frame. Ordinary commands never install a sink, so CLI
stderr diagnostics are unchanged. Issue #3 is reproduced and covered at a real PTY
by tests/test_tui.py::TuiSaveChainPtyTest, whose trigger is a registry-wide
part_of cycle surfaced as E_GRAPH by Store.graph_cycles during observe.

Graphify found calls from save to bump_revision/commit, commit to check_text,
Document._apply to _verify_preserved, and Ctx.record to store/note. Some edges are
marked INFERRED. This is a discovery aid, not complete execution-path proof.

## Environment observed in this conversation

- Checkout: /home/daeron/Repositories/somnus-metadata; Linux/bash.
- Python command: 3.14.4. CLI contract supports Python >=3.11.
- Surgeon MCP is working; local periphery output was noisy/incomplete for the
  requested trace. Precise bounded views remain useful.
- somnus-debug 0.1.0 is installed. Existing root and src profiles are configured;
  source-root scan covers 49 Python files and resolves somnus imports.
- Doctor baseline has 70 serious findings despite native tests/mypy passing.
  These are different evidence classes, not a contradiction to conceal.
- Doctor state/report generation triggered a host Surgeon-receipt warning.
  Reports/SQLite are documented generated artifacts; source enforcement stays on.
- CodeGraph and Graphify CLIs are installed. CodeGraph index is not initialized.
- Graphify probe lives under /tmp/somnus-metadata-topology-probe, is disposable,
  and must be regenerated after relevant source changes. No external provider
  was used; SQL grammar was unavailable.
- BB7 live health reported 143 registered tools/17 loaded modules, stdio,
  shared /home/daeron/Somnus-MCP/data. This is not model/routing acceptance.
- BB7 focused route and architectural query were callable but poorly matched to
  the trace question. Do not generalize that to absence of useful continuity.
- Global Codex hooks already have entry/capability/harness/Surgeon owners.
  This repo's new .codex/OPERATING.md is a route, not a registered hook.
- /home/daeron/.codex/workflows.md was missing when inspected. A user-supplied
  repository workflows.md now exists; it is a suggested substrate playbook.

The root AGENTS OneDrive warning is inherited portability guidance, not proof
that this Linux checkout currently runs on OneDrive. Preserve its one-file-per-
Surgeon-call restriction; do not infer a current Windows host from that text.

## Continuity without duplicating authority

AGENTS routes entry; PLAN owns frontier/evidence; this file explains relationships.
Keep imported AGENTS.template.v2.md unchanged for comparison. It contains an
unrelated planetary-system identity, placeholders, and generic authority prose;
do not activate it unadapted. The mission-first AGENTS.md (promoted from
AGENTS.somnus.v2.md on 2026-10-31) is active; AGENTS.v1.md is the superseded entry file.

The House fable explains why portable working surfaces matter. It is not a
replacement for current source evidence or a mandate to run every tool.
The Golden Path selects the next justified move from changed state; it neither
requires an unknowable full plan nor permits planning forever.

## Stable anti-drift constraints

No replacement of authored mechanisms with signature-compatible substitutes.
No tool-count/readiness-score chasing, blanket formatter churn, parallel package
layout, fake hook activation, fabricated metadata, or duplicate cognitive data
plane. No release/push/global mutation by implication. Preserve pre-existing
working-tree changes and user-owned archives. Product completion and operator
instrumentation are related but distinct outcomes.
