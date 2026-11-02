---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a67-789d-75a7-a213-997b444b6530"
  revision: 2
  title: "Somnus Metadata — Architectural and Operator Context"
  classification:
    category: "context"
    type: "state"
    role: "informative"
    scope: "component"
    tags: []
  lifecycle:
    status: "draft"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a19a67-789d-75a7-a213-997b444b6530"
        aspects: ["content"]
  time:
    updated_at: "2026-11-02T04:08:11+00:00"
  names:
    slug: "somnus-metadata-architectural-and-operator-context"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19a67-789d-75a7-a213-997b444b6530"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Somnus Metadata — Architectural and Operator Context

Established 2026-10-23 (America/Chicago). This is relational context, not a new
normative authority. Read PLAN.md for current evidence, work and acceptance gaps.

## Current distribution and rollout state (2026-11-01)

The toolkit release is **somnus-metadata 2.1.0**; core schema remains **2.0.0**.
The plain-pip installation in `~/.venvs/global` and its `~/.local/bin` links
were checked against the current package index. A fresh installed-wheel acceptance
run passed 66/66; the source suite passed 534/534 and mypy checked 49 files clean.

The separate private plugin is **1.1.0**, installed for Droid, Codex, Antigravity
and OpenCode. Its 21 tests and all four live 16-tool doctor handshakes pass.
Actual Droid/Codex MCP searches are proven, including full TSV paths; the packaged
skill now explicitly requests TSV for agent path consumption. OpenCode in-session
invocation and live Windows console execution remain NOT RUN.

The global rollout is **not complete**. All five requested roots are registered.
Native stamping adopted 141 core-repository and 14 plugin files; the registry has
160 unique present paths after redundant nested registrations were consolidated
with a verified online backup. At the last reconciliation, 21,174 other
embedded-carrier candidates remained, plus unknown-carrier files absent from that
scanner's unmanaged count. PLAN.md's top section and HANDOFF.md own the exact
frontier, exclusions and host-session evidence.

No new backend behavior, public release, remote tunnel, or shared Somnus-MCP
data/model mutation was introduced by this adoption pass. Older environmental
observations below are historical, not current capability claims.

## The system and its boundaries

Somnus Metadata core 2.0.0 is a standard; the somnus Python distribution is its
stdlib-only toolkit. Its current package version is 2.1.0. This repository
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
