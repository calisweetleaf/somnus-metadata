---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a67-789d-75a7-a213-997b444b6530"
  revision: 4
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
    updated_at: "2026-11-02T04:53:05+00:00"
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

The toolkit release is **somnus-metadata 2.1.1** on PyPI and installed with plain
pip in `~/.venvs/global`; core schema stays **2.0.0**, registry schema **2**.
The patch repairs unmanaged-host discovery for files needing a new sidecar,
without loading their contents. Previously, a zero-unmanaged scan could omit
JSON/PDF/image/text hosts. Actual native discovery now covers those file types.

The source suite passed **537/537**, mypy checked **49 files**, and installed-wheel
acceptance passed **67/67**. The released wheel's 51 runtime files matched the
accepted wheel. Doctor deltas and the single intentional-subprocess disposition
are recorded in PLAN.md; static scores are not runtime proof.

The separate private plugin remains **1.1.0**. Its preceding 21-test result is
unchanged; fresh doctor handshakes in Droid, Codex, Antigravity and OpenCode now
serve 16 tools from backend 2.1.1. Real Droid/Codex searches and complete TSV paths
were proven in the previous segment. OpenCode in-session and physical Windows
console invocation remain NOT RUN; no tunnel or shared-data mutation was added.

All five roots are registered. Current checkpoint: **1,064 managed hosts** and
**27,202 unmanaged** across all carrier types. **Documents (899) and Projects (4)
are adopted**, with their nested Git commits local only. Repositories, LAB and
Somnus-MCP adoption remains open; PLAN.md/HANDOFF.md own the exact next action.
Generated dependencies/state, archives, credentials, frozen research and the
running Somnus-MCP data plane remain excluded. Source host content is preserved
under SPEC's explicit encoding/body rules, including its accepted-but-never-
emitted BOM policy. Older observations below are historical, not current claims.

## The system and its boundaries

Somnus Metadata core 2.0.0 is a standard; the somnus Python distribution is its
stdlib-only toolkit. Its current package version is 2.1.1. This repository
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
