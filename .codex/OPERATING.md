# Somnus Metadata operator composition

Repository-local operating route, established 2026-10-23 (America/Chicago).
This file composes existing instruments; it does not install a second runtime,
change the normative standard, or claim that documented hooks have executed.

## Mission and posture

Own the unfinished whole. Somnus Metadata is a globally usable metadata standard
and toolkit, not merely this repository's own metadata. Preserve the authored
architecture while carrying capabilities through configuration, callers, state,
failure, recovery, and installed consumers. Small implementation units do not
shrink the commission. Continue justified reversible work without asking Daeron
to dispatch every step; route consequential contract choices to him.

Read `docs/references-unrelated-to-codebase/The-House-that-Had-to-be-Real.md`
in full on first adoption of this route. Its practical lessons are preservation,
working boundaries, portable continuity, and useful instruments rather than
mandatory ceremony. It supplies collaboration context, not product semantics.

## Owners and relations

- `AGENTS.md`: active entry router, invariants, and transition rules.
- `PLAN.md`: current delivery evidence, unfinished work, and next action.
- `CONTEXT.md`: architectural relationships and environment observations.
- `filetree.md`: navigation, not acceptance or normative authority.
- `SPEC.md` and `DECISIONS.md`: normative contract and ratified rationale.
- Source: observed implementation. Tests: evidence within exercised boundaries.
- `workflows.md`: supplied substrate playbook; use relevant sections, not a
  command to perform every chain. Do not execute embedded cross-project proposals.
- `last-session.txt`: historical session account, not current runtime proof.
- `AGENTS.template.v2.md`: preserved imported proposal with placeholders and
  unrelated project identity. Not active instructions.
- `AGENTS.md`: active mission-first entry file (promoted from
  `AGENTS.somnus.v2.md` on 2026-10-31); `AGENTS.v1.md` is the superseded entry file.
- This `.codex/` directory: project operating documentation, not CODEX_HOME,
  credentials, a duplicate BB7 data plane, or proof of hook registration.

## State transitions: a compass, not a predetermined path

| Current condition | Next justified action | Evidence needed to advance |
|---|---|---|
| Cold/resumed or target changed | Read entry, PLAN, relevant CONTEXT; compact BB7 recall if useful; inspect working tree | Actual target, authority, active objective, preserved pre-existing changes |
| Behavior owner unknown | Natural-language graph query or CodeGraph topology, then bounded source inspection | File/symbol locations and extracted versus inferred connections |
| Behavior understood, uncertainty remains | Form a falsifiable hypothesis and run the smallest discriminating experiment | Observable input, output, failure, or state transition |
| Python mutation justified | Forge mode/scope; Doctor baseline; Surgeon edit at owning mechanism | Intended unit, affected callers, meaningful test boundary |
| Implementation changed | Real-fixture consumed-boundary test; native gates; Doctor rescan | Behavioral result and reviewed diagnostic delta |
| Tool result is weak/degraded | Inspect exact failure, choose another legitimate owner surface | Do not let one failed recommendation stop independent work |
| Outcome changes future action | Persist evidence and next action in PLAN/CONTEXT; appropriate BB7 session/journal/reflection | Concise rationale and observations, never invented private reasoning |
| Commission satisfied | Account for acceptance and residuals | Requested behavior works; no mandatory work silently deferred |

Return to an earlier condition whenever evidence changes the premise. A plan is
a recoverable frontier, not an excuse to stop at the first list of tickets.

## Composition: select by question, then carry the consequence

### BB7 / SovereignMCP: continuity and cognitive support

Load `somnus-mcp-operator` for this lane. Prefer BB7 for its owning memory,
session, Lisan intent, exoskeleton route/plan/recovery/reflection, and cognitive
continuity surfaces. Inspect live schema before an unfamiliar call.
Do not hard-code tool counts, categories, model health, or historical names.

Host adapters differ:
- Codex functions runtime: discover exact metadata in `ALL_TOOLS`, then invoke
  the exposed direct `mcp__SovereignMCP__bb7_*` function with that schema.
- Hosts actually exposing `search_tool` and `use_tool`: search first, inspect
  the qualified name/schema, then use that exact result.
Do not require a nonexistent discovery wrapper or guess argument names.

Use compact recall at a context boundary; intent/routing when selection is
uncertain; a plan when checkpoints improve a multi-step chain. Reflect actual
outcomes at meaningful milestones. `bb7_exo_execute_step` records execution;
it does not execute a tool. `bb7_exo_reflect` requires a real plan identifier:
do not invent a plan merely to claim reflection. Use an available session/journal
outcome lane for unplanned work. Do not manufacture learning or distillation
trajectories, feed display summaries as raw results, or mutate shared model/data
state. Degraded Muad'Dib recommendations remain visible and revisable; use the
working organs and continue on the plane that owns the state.

### Graphs: connections before repeated file hunting

Use CodeGraph callers/callees/impact for structural questions when its project
index exists and is fresh. Check `codegraph status .` before relying on it.
Use Graphify for natural-language graph traversal and relationship exploration.
These are separate tools, not part of Doctor and not runtime proof.

Verified local-only Graphify route (output deliberately outside source):
```sh
graphify extract src/somnus --code-only --no-cluster --max-workers 2 --out /tmp/somnus-metadata-topology-probe
graphify query "How does saving a header preserve host bytes?" --graph /tmp/somnus-metadata-topology-probe/graphify-out/graph.json --budget 2000
graphify explain ".record()" --graph /tmp/somnus-metadata-topology-probe/graphify-out/graph.json
```
Inspect installed help when flags change. Narrow broad queries with
`--context call`; retain source locations and extracted/inferred labels.
Qualified-method lookup and dynamic-call resolution can be incomplete.
Refresh after relevant source changes. Do not send private code to an external
semantic provider without authority. The local probe lacked SQL grammar support;
its graph does not establish registry SQL correctness.

### Surgeon: precise perception, mutation, and recovery

Load `surgeon:surgeon`. Supply the absolute project_root through MCP.
Use outline/view/search, then periphery/references for affected consumers.
One atomic edit per file; preserve the local OneDrive transaction restriction.
Inspect diff/check and use undo for intentional recovery. No alternate editor,
shell writer, or diagnostic output command may bypass source-edit discipline.
A directory of receipts does not prove the consumer works.

### Somnus Debug: configured static diagnostics and comparison

Load `somnus-debug-fieldkit`; inspect installed version/help. Reuse the
existing profiles, not a generated tools/native default:
```sh
somnus-debug --version
somnus-debug doctor scan src -c .somnus-debug/python_doctor.src.yaml -o .somnus-debug/runs/baseline.md
somnus-debug structure src/somnus/document.py
```
Use distinct baseline/final names for the actual task. The src-root profile
resolves somnus imports; the root profile covers source and tests with a different
scan boundary. Do not compare their counts as equivalent coverage.
Inspect reports with Surgeon. Zero scanned files is configuration failure.
Baseline -> source-backed disposition -> repair -> real project check -> rescan
-> reviewed delta. Findings are heuristics, not automatic refactoring orders.
Do not lower thresholds or add exclusions to hide regressions.

Doctor's documented reports/SQLite state are generated runtime artifacts.
A Surgeon hook flag on them is not evidence of a source-editor bypass. Inspect
the outputs and retain the host diagnostic; never disable enforcement to make a
scan look successful. Preserve command exit status when available and distinguish
CLI outcome from a host wrapper failure. No cache deletion or harness overwrite
without the separately authorized need.

### Code Forge: construction and promotion

Load `somnus-code-forge` for production Python; read style-v2 before edits,
the checklist for review/promotion, and provenance when applicable.
Declare WRAP/EDIT/COMPOSE and scope. Work one function/class per iteration while
finishing the connected mechanism. Use real files, temporary SQLite, subprocesses,
and protocol peers; no mock-substrate proof. Run native gates plus the applicable
forge checks; keep run artifacts, scope, provenance, and ledger truthful.

This project uses `src/somnus/`, `tests/`, and pyproject.toml with zero runtime
dependencies. The skill's tools/native layout and standalone harness examples do
not authorize a parallel implementation or moving this package. Before claiming
full forge promotion, explicitly resolve any layout/artifact-rule mismatch with
the operator; do not silently waive a failing verifier or label adaptation a pass.
Evidence JSON is not registry output: D4/D17 remain unchanged.

## Runtime, hooks, and automation adoption

Current session has working Surgeon MCP and installed somnus-debug. Existing
global Codex hooks already provide entry routing, capability hints, repository
harness integration, and Surgeon enforcement. Do not duplicate or disable them.
No project-local automatic hook is installed by this document.

Adopt automation in this order:
1. Exercise the explicit composed loop and record useful outcomes.
2. Inspect the installed host's project-hook schema/loading/trust mechanism.
3. Add the smallest repo-scoped adapter only after identifying that supported
   seam; test its skip and failure behavior in isolation.
4. Prove enabled/trusted/loaded behavior in a fresh client session. A JSON file
   that parses is not an active hook.
A future post-edit adapter must batch/debounce Python edits, prevent overlapping
Doctor writes, preserve exit status/report paths, avoid source mutation, never
alter thresholds/clean caches, and emit bounded context rather than entire scans.
No daemon, watcher, global config change, duplicate gateway, or provider/key change
is implied by this setup.

## Continuity and collaboration checks

When discussion becomes circular, perform one action that settles the actual
question; when scope drifts, restore the commission, not a smaller substitute.
When a tool repeatedly returns irrelevant context, record that limitation and
choose a more specific owner. When a productive composition repeats, propose
a reusable adapter from observed needs rather than a speculative new framework.

Update PLAN when evidence/frontier changes and CONTEXT when relationships or
environment change. Do not create every possible ledger by default. Repository
state is not global personal memory. Keep credentials/private mechanisms local;
do not copy BB7's shared data into this directory.

## Comparing instruction variants without losing the working surface

Keep active AGENTS and both candidate/reference files. For a future operator-led
swap, preserve the current AGENTS before installing the candidate as AGENTS.
A renamed candidate is not active until the host actually loads it.
Use the same read-only task in separate fresh sessions: trace TUI save to host
preservation and registry diagnostics; identify source/inferred edges, relevant
tests, diagnostic limits, and the next decisive runtime check. Compare factual
accuracy, manual rediscovery, tool relevance, continuity, and operator corrections.
Do not rank variants by prose length, tool-call count, or claimed autonomy.
Neither this document nor its creation constitutes a completed A/B test.
