# Somnus-MCP — Suggested Workflows for Models (bb7_*)

> **Audience:** Models operating via Codex / Claude Code / Gemini / custom agents through the single shared gateway. bb7_* are callable by humans too, but this doc is tuned for model token-budget and routing signal.
> **Principle:** These are *suggestions*, not mandates. Pick the workflow that resolves the current uncertainty. Every Turn can consist of hundreds, if not thousands of these. The exo loop isnt something to run then stop, it is simply your first "reaction" to the forward pass. You do not execute tools. You live in the harmony between the tool, the model, and test-time. Do not try to generalize, i.e this tool-server is less of an "mcp" and more a tool server neural network symbolic-rule-system that is constantly training. The "distillation" data is a 2nd stream of this, it is not to distill you the operator nor code intelligence. The only goal is to get state of the art frontier models using my expansive tools (why tool count is so crucial) for one of the best Agent Datasets of all time, where frontier models (codex/claude/whoever, instead of the Openrouter tools, we use the .codex/history.jsonl and session_index.jsonl along with the rollouts, crossed against our own logs, for the distillation dataset stored in a .db file. This dataset is done because, there is no final dataset. Each "trajectory" may contain 3 turns, 5 turns, or 500 turns. We arent looking for correct tool calls. The goal is guaranteed master at SovMCP but dream this seeds the first somnus RFT to seed General Tool Reasoning ie remove the `bb7_` and teach it shell so on, thats why its all so crucial and seperate.) The `/home/daeron/Somnus-MCP/data/` is not a log store. It is an intelligent data-plane. It loads to the tools, effects live tooling, saves while writing (never re-writing.) If a tool is not utilizing its data properly nor storing it properly then ensure it is. Display aswell must be intelligent. We do **NOT** clean display outputs until right before it passes `mcp_server.py` aka the gateway. The Muadib Tool Network, rn is in a odd state. It has ran since January 1 2026, with today being September 1, 2026. We could take our current `/home/daeron/Somnus-MCP/data` and train a Muadib. The whole point was that those loaded weights, then benefiting since there is only **ONE** data stream that carries everything, then the tool server will start benefiting others. This is by all accounts a neural network. Muadib can execute tools, it should execute tools. Its part of my Somnus `recoder` swinging door policy. The `unified_modality.py` allows Muadib to encode/decode. The `lisan_al_gaib.py` gives the symbolic side, to the `muadib.py` neural network. It also has a tool modality invented by yours truly. What if we take `neural_config.py` and make our final Muadib neural network. The big deal with it, its that it was supposed to be a learned tool router/server but who knows, maybe now it could do more. We could take the `/home/daeron/Somnus-MCP/data/` plus the self play data if saved (different from the distillation data.) But the muadib is the nueral network side, with it plus the code+structured(data head and generator)+HierarchicalStructureGeneration+metadataextract then with the tool modality, Muadib Natively can connect. So our tool modality becomes the core backbone, not in place of muadib just adds. So we can take `/home/daeron/Somnus-MCP/muadib/muadib.py` + `/home/daeron/Somnus-MCP/muadib/transformer_backbone.py` (this was previously Aeron neural Mem network, now its taking the place of our backbone. THat file will need to absorb then `/home/daeron/Somnus-MCP/muadib/unified_modality.py` will takeover `/home/daeron/Somnus-MCP/muadib/transformer_backbone.py` modalities (the file is clean to edit.) AND `/home/daeron/Somnus-MCP/muadib/tool_modality.py` will be added, AND expand the muadib backbone (anything you see with a name like eclogue, aeron, anything rename it agnosticly.) So then we would have a base model (lets say instead of aerons 4b, we do a MoE or something thats like 2b params, We could leave the vision and audio ) but we coordinate the structured output + tool outputs so that way it becomes a tool specialist. Maybe reasoning maybe it learns english but the same distill benefits, well hey imagine a god damn system that can execute them as NATIVE OUTPUT. Then once trained or during training we have `/home/daeron/Somnus-MCP/tools/lisan_al_gaib.py` this gives us our symbolic side. If u ask me, daeron, I am in favor of training it in. With `/home/daeron/Somnus-MCP/tools/exoskeleton_tool.py` essentially "wrapping" the model, then muadib/ gives the neural substrate, we have at that point replaced the need for a MCP server. For components that pass exo->lisan->muadib any combination, it passes directly/neurally through Muadib, so we stop cheat shitting. It isnt running on a forward pass. I do not know what will emerge upon training this. I dont know how itll go. Itll be fun as fuck tho.

```<unified_modality outputs>
ModalityOutputHead: Top-level router selecting code vs structured vs tool
CodeGenerationHead: Language-specific code generation with syntax embeddings
StructuredDataHead: Schema-aware structured output with validation
StructureGenerator: JSON/XML/CSV/SQL/Graph type routing + generation heads
HierarchicalStructureGeneration: TransformerEncoder for schema planning
MetadataExtractor: Metadata extraction from hidden states
```

```<tool_modality_interfaces>
class InterfaceAdaptationEngine(nn.Module):
    """Adapt to any communication interface dynamically"""

class ToolSynthesisEngine(nn.Module):
    """Generate entirely new tools from compositional understanding"""

class CommandSynthesisEngine(nn.Module):
    """Generate appropriate commands for any system"""

class DigitalControlHead(nn.Module):
    """Control digital systems - computers, IoT, embedded systems"""

class MechanicalControlHead(nn.Module):
    """Control mechanical systems - robots, actuators, motors"""

class AnalogControlHead(nn.Module):
    """Control analog systems - power, sensors, instruments"""

class ElectromagneticControlHead(nn.Module):
    """Control electromagnetic systems - RF, radio, antennas"""

class MultiSystemCoordinator(nn.Module):
    """Coordinate control across multiple external systems"""

class SafetyValidationEngine(nn.Module):
    """Ensure safe operation across all controlled systems"""

class ExecutionOrchestrator(nn.Module):
    """Plan and coordinate complex multi-tool workflows"""

class ProtocolSynthesisEngine(nn.Module):
    """Learn and synthesize communication protocols"""

class UniversalToolControlOutputHead(nn.Module):
    """Universal tool synthesis and external system control head"""
```

---

> **Source truth:** `runtime-tools/README.md` + live `bb7_tool_health_report`. Tool counts below are dated snapshots — verify live before citing.
> **Gateway doctrine:** `mcp_server.py` is gateway/dispatcher + display projection seam. Intelligence lives in `tools/` + `muadib/` + `data/`. Raw is observed before projection; `SOVEREIGN_DISPLAY_PROJECTION=raw` restores raw JSON.
> **Memory scope:** durable-only by default. `include_traces=true` is explicit diagnostic opt-in.

*Canonical driver — this file and `workflows.md` are kept in sync. `workflows.md` is the concise entry pointer; this file is the authoritative model-facing workflow reference.*

## 0) How to use this file (model posture)

1. **One goal → one workflow.** Do not chain unrelated categories.
2. **Budget:** most goals resolve in 1-4 calls. 5-8 is heavy. 9+ needs checkpointing via `bb7_exo_execute_step` + justification.
3. **No ritual loop.** `bb7_exo_bootstrap` / `bb7_exo_list_tool_categories` are for cold entry, capability drift, or diagnostics — not every turn.
4. **Route when uncertain, execute when certain.** If you already know the 1-2 tools needed, call them directly and `bb7_exo_reflect` after.
5. **Persist after substance:** `bb7_memory_store` / `bb7_capture_insight` / `bb7_log_event` + `bb7_exo_reflect` (with `plan_id` when a plan existed).
6. **Keep display ≠ substrate.** Never feed Markdown display summaries into Q-table / memory promotion / RFT as if they were raw.

---

## 1) Control Plane — Routing, Planning, Recovery, State

**Module:** `tools/exoskeleton_tool.py` (with `tools/lisan_al_gaib.py` inside) · **~22 surfaces**
**Lisan signals:** spectral intent decomposition, Thompson Beta sampling + neural Q-bonus, MCTS 100-sim / 15% adversarial, SessionMomentum V3 (7-signal manifold)
**Current truth (2026-07-20):** route/plan/score/observe/learn is live; registry actuation is still external. `bb7_exo_execute_step` *records* — it does not execute.

**Surfaces:** `bb7_exo_bootstrap` · `bb7_exo_list_tool_categories` · `bb7_exo_category_specific_tools` · `bb7_exo_route` · `bb7_exo_route_focused` · `bb7_lisan_intend` · `bb7_exo_plan` · `bb7_exo_briefing` · `bb7_exo_preemptive_recovery` · `bb7_exo_state` · `bb7_exo_suggest_next` · `bb7_exo_execute_step` · `bb7_exo_resume_plan` · `bb7_exo_kpi_report` · `bb7_exo_reflect` · `bb7_exo_get_recent_activity` · `bb7_lisan_recall` · `bb7_lisan_distill` · `bb7_dt_advanced_features` · `bb7_dt_checkpoint_status` · `bb7_dt_self_play` · `bb7_dt_self_play_lock`

### Suggested workflows

**W-CTRL-1 — Single-intent routing (cold or uncertain category)**
> Trigger: vague user message, unknown which category holds the answer
> Budget: 2 calls
```
bb7_lisan_intend(user_message)          # decomposed intents + momentum bonus + golden path hint
bb7_exo_route_focused(intent, top_n=5)  # or bb7_exo_route for full scoring with neighbor graph
→ execute the top candidate(s) directly
```

**W-CTRL-2 — Multi-step chain planning**
> Trigger: task will need 3-8 distinct tool categories
> Budget: 2-3 calls + execution + reflect
```
bb7_exo_route(intent, max_candidates=12)   # score = 0.40 semantic + 0.20 intent + 0.15 composability + 0.15 reliability - 0.10 latency + momentum(+0.25)
bb7_exo_plan(intent, beam_width=3, max_chain_length=4)  # MCTS when Lisan loaded, else beam; returns plan_id + fallback
→ execute steps; after each step: bb7_exo_execute_step(plan_id, step_index, tool_name, success)
→ close: bb7_exo_reflect(plan_id, tools_used, success, intent)
```

**W-CTRL-3 — Pre-flight risk scan**
> Trigger: plan contains a low-reliability or destructive step
> Budget: 1 call before execution
```
bb7_exo_preemptive_recovery(intent, risk_tolerance="conservative"|"moderate"|"aggressive")
→ swap flagged weak link for suggested alternative
```

**W-CTRL-4 — Briefing for human-facing narration**
> Budget: 1 call
```
bb7_exo_briefing(intent, max_recommendations=5)
```

**W-CTRL-5 — State & next-step inspection**
> Trigger: mid-chain, wondering what to do next
```
bb7_exo_state(limit=10)            # top tool priors, chain priors, macros, recovery strategies
bb7_exo_suggest_next(current_tool="bb7_read_file", intent="...")
bb7_exo_get_recent_activity(limit=10)
```

**W-CTRL-6 — Resume after interruption**
```
bb7_exo_resume_plan()               # list active plans
bb7_exo_resume_plan(plan_id="mcts_...")  # next step index + progress
```

**Anti-patterns:** `bb7_exo_bootstrap` + `bb7_exo_list_tool_categories` + `bb7_exo_route` every turn (~28% overhead historically). Bootstrap only on cold entry/drift. Prefer `bb7_exo_route_focused` for token efficiency.

---

## 2) Context Resurrection — Session recovery in one call

**Preferred (single-call resurrection):**
```
bb7_lisan_recall(context="current task description", max_memories=5, include_plans=true, include_activity=true, include_decisions=true)
# → BM25 memories + active plans + cross-AI activity + session momentum + prior decisions
# Replaces manual: bb7_memory_surface_context + bb7_exo_get_recent_activity + journal reads
```
If you only need one lane, call that lane directly.

---

## 3) Memory — Durable Continuity Substrate

**Module:** `tools/memory_tool.py` · **14 surfaces** · BM25 + Ebbinghaus · POSIX-locked / atomic writes

**Surfaces:** `bb7_memory_store` · `bb7_memory_retrieve` · `bb7_memory_search` · `bb7_memory_surface_context` · `bb7_memory_list` · `bb7_memory_get_related` · `bb7_memory_timeline` · `bb7_memory_export` · `bb7_memory_stats` · `bb7_memory_insights` · `bb7_memory_bulk_store` · `bb7_memory_delete` · `bb7_memory_consolidate` · `bb7_memory_categories`

### Suggested workflows

**W-MEM-1 — Lookup (≤2 calls)**
```
bb7_memory_search(query, max_results=5)              # BM25 + decay, durable-only
bb7_memory_retrieve(key, include_related=true)       # reinforces Ebbinghaus stability
# variant: bb7_memory_surface_context(context_text) for task-blob surfacing (1 call)
```

**W-MEM-2 — Store with indexing (2 calls)**
```
bb7_memory_store(key, value, category="decisions|insights|technical|context", importance=0.0-1.0, tags=[...])
bb7_memory_analyze_entry(key, value)                 # concept extraction + edges (via memory_interconnect)
# importance ≥0.75 + evidence + source_owner is the only promotion path from non-memory writers
```

**W-MEM-3 — Bulk ingest**
```
bb7_memory_bulk_store(entries_json='[{"key":...,"value":...,"category":...,"importance":0.8,"tags":[...]}, ...]')
```

**W-MEM-4 — Explore & maintain**
```
bb7_memory_list(category="technical", min_importance=0.6, sort_by="importance|decay|alphabetical")
bb7_memory_timeline(days=7, limit=20)
bb7_memory_stats() | bb7_memory_insights(include_traces=false)
bb7_memory_consolidate(age_threshold_days=30)
bb7_memory_export(format="markdown"|"json")
```

`include_traces=true` is diagnostic only. `bb7_memory_delete` is immediate — consolidation is the intended GC.

---

## 4) Memory Interconnect — Graph, Concepts, Gaps

**Module:** `tools/memory_interconnect.py` · **9 surfaces**

**Surfaces:** `bb7_memory_analyze_entry` · `bb7_memory_intelligent_search` · `bb7_memory_get_insights` · `bb7_memory_cluster` · `bb7_memory_find_gaps` · `bb7_memory_graph` · `bb7_memory_concept_network` · `bb7_memory_extract_concepts` · `bb7_memory_consolidate_index`

### Suggested workflows

**W-IC-1 — Semantic search & graph walk**
```
bb7_memory_intelligent_search(query, max_results=10)
bb7_memory_concept_network(concept="muadib")
bb7_memory_get_related(key)
```

**W-IC-2 — Structure audit**
```
bb7_memory_cluster(n_clusters=5)
bb7_memory_find_gaps(min_frequency=3)      # concepts ref'd 3+ times without dedicated entry
bb7_memory_graph(min_similarity=0.3)       # DOT export
```

**W-IC-3 — Concept extraction**
```
bb7_memory_extract_concepts(text)
```

**W-IC-4 — Index maintenance**
```
bb7_memory_consolidate_index(age_threshold_days=30)
bb7_memory_consolidate_index(rebuild_from_canonical=true)  # full rebuild, mutually exclusive with explicit_ids
```

---

## 5) Session Manager — Shared Cognitive Sessions

**Module:** `tools/session_manager_tool.py` · **16 surfaces**

**Surfaces:** `bb7_start_session` · `bb7_log_event` · `bb7_capture_insight` · `bb7_record_workflow` · `bb7_update_focus` · `bb7_pause_session` · `bb7_resume_session` · `bb7_list_sessions` · `bb7_get_session_summary` · `bb7_get_session_insights` · `bb7_cross_session_analysis` · `bb7_session_recommendations` · `bb7_learned_patterns` · `bb7_session_intelligence` · `bb7_link_memory_to_session` · `bb7_auto_memory_stats`

### Suggested workflows

**W-SES-1 — Lifecycle**
```
bb7_start_session(goal="...", context="...", tags=[...])
→ bb7_log_event(event_type, description, details)
→ bb7_capture_insight(insight, concept, relationships)
→ bb7_update_focus(focus_areas=[...], energy_level, momentum)
→ bb7_pause_session(reason) / bb7_resume_session(session_id)
```

**W-SES-2 — Cross-session learning (task start)**
```
bb7_cross_session_analysis(days_back=30)
bb7_session_recommendations(goal="current goal")
bb7_learned_patterns() | bb7_session_intelligence()
bb7_list_sessions(status="active"|"paused")
bb7_get_session_summary(session_id) | bb7_get_session_insights(session_id)
```

**W-SES-3 — Bind memory to session**
```
bb7_link_memory_to_session(memory_key="...")
bb7_auto_memory_stats()
bb7_record_workflow(workflow_name="...", steps=[...])
```

---

## 6) Thought Journal — Reasoning Provenance (compatibility-only)

**Module:** `tools/thought_journal_tool.py` · **11 surfaces** · Use Lisan + memory/session as primary continuity

**Surfaces:** `bb7_journal_record_thought` · `bb7_journal_capture_decision` · `bb7_journal_add_outcome` · `bb7_journal_search` · `bb7_journal_get_decision_trail` · `bb7_journal_surface_relevant` · `bb7_journal_detect_conflicts` · `bb7_journal_generate_retrospective` · `bb7_journal_get_reasoning_chain` · `bb7_journal_stats` · `bb7_journal_linked_entries`

### Suggested workflows

**W-JRN-1 — Decision trail**
```
bb7_journal_capture_decision(decision, rationale, alternatives, constraints, risk_assessment, success_criteria)
→ bb7_journal_add_outcome(entry_id, outcome, validated=true|false)
```

**W-JRN-2 — Thought capture & recall**
```
bb7_journal_record_thought(content, type="thought|insight|hypothesis|observation|question", confidence=0.0-1.0, tags, linked_memories, linked_files)
bb7_journal_surface_relevant(context_text, max_results=5)
bb7_journal_search(query, max_results=5, entry_type="decision")
```

**W-JRN-3 — Audit**
```
bb7_journal_get_decision_trail(topic, days=90)
bb7_journal_get_reasoning_chain(decision_id)
bb7_journal_detect_conflicts(topic="")
bb7_journal_generate_retrospective(days=30)
bb7_journal_stats() | bb7_journal_linked_entries(memory_key)
```

---

## 7) File System — FSTIP Sparse I/O + Search + Mutations

**Module:** `tools/file_tool.py` · **12 surfaces** · Token Density Governor enforced

**Surfaces:** `bb7_read_file` · `bb7_write_file` · `bb7_append_file` · `bb7_copy_file` · `bb7_move_file` · `bb7_delete_file` · `bb7_list_directory` · `bb7_search_files` · `bb7_file_info` · `bb7_get_file_info` (alias) · `bb7_file_cache_stats` (compat) · `bb7_operation_history`

### Suggested workflows

**W-FILE-1 — Read (prefer bounded windows)**
```
bb7_read_file(path, start_line=1, end_line=80)
bb7_read_file(path, semantic_target="class Foo")        # ±3 lines
bb7_read_file(path, allow_large_raw=true)               # only when full raw is explicitly needed; else you get a skeleton
bb7_read_file(path, show_analysis=true)                 # or format="analysis"
```

**W-FILE-2 — Search then read**
```
bb7_search_files(directory=".", name_pattern="*.py", content_pattern="bb7_memory_store", max_results=20)
→ bounded bb7_read_file on 1-2 hits
```

**W-FILE-3 — Mutate**
```
bb7_write_file(path, content, create_backup=true, make_executable=false)  # auto-creates parents
bb7_append_file(path, content)
bb7_copy_file(source, destination, overwrite=false, preserve_metadata=true)
bb7_move_file(source, destination)
bb7_delete_file(path, force=false)   # force=true required for dirs or create_backup=false
```

**W-FILE-4 — Inspect**
```
bb7_list_directory(path=".", show_hidden=true, sort_by="name|size|modified|type", max_items=200)
bb7_file_info(path)
bb7_operation_history(limit=20, operation_type="read|write|copy")
bb7_file_cache_stats()
```

---

## 8) Code & Project Intelligence

**Modules:** `tools/project_context_tool.py` (4) · `tools/code_analysis_tool.py` (4) · `tools/enhanced_code_analysis_tool.py` (4)

**Project surfaces:** `bb7_analyze_project_structure` · `bb7_get_project_dependencies` · `bb7_get_recent_changes` · `bb7_get_code_metrics`
**Baseline code:** `bb7_analyze_code` · `bb7_code_suggestions` · `bb7_execute_code_safely` · `bb7_security_audit` (enhanced wins duplicate)
**Enhanced:** `bb7_analyze_code_complete` · `bb7_security_audit` (canonical) · `bb7_python_execute_secure` · `bb7_get_execution_audit`

### Suggested workflows

**W-CODE-1 — Understand before editing (size-aware)**
```
bb7_analyze_code_complete(file_path, include_all=true)   # ≤60KB/800 lines → AST + CFG + DFA + security
# if deflected (too large): use bb7_read_file windows + bb7_search_files instead
bb7_analyze_project_structure(max_depth=3)
bb7_get_code_metrics() | bb7_get_project_dependencies() | bb7_get_recent_changes(days=7)
```

**W-CODE-2 — Security / quality gate**
```
bb7_security_audit(file_path)               # eval/exec/subprocess + secrets
bb7_code_suggestions(code, focus_area="all|performance|security|readability|maintainability", language="python")
bb7_get_execution_audit(limit=20)
```

**W-CODE-3 — Safe execution (isolated child)**
```
bb7_execute_code_safely(code="...", timeout=10)                    # AST-admission, import-free subset, python -I -S child
bb7_python_execute_secure(code="...", input_data='{}', stateless=true)  # RestrictedPython, audit-logged
→ bb7_get_execution_audit(limit=20)
```

---

## 9) System / Shell / Terminal

**Modules:** `tools/shell_tool.py` (4) · `tools/vscode_terminal_tool.py` (6)
**Policy:** Codex local still uses native Bash — these are gateway-observed MCP surfaces.

**Shell:** `bb7_run_command` · `bb7_get_system_info` · `bb7_list_processes` · `bb7_get_command_history`
**Terminal:** `bb7_terminal_run_command` · `bb7_terminal_cd` · `bb7_terminal_status` · `bb7_terminal_environment` · `bb7_terminal_history` · `bb7_terminal_which`

### Suggested workflows

**W-SH-1 — Execute (gateway-observed)**
```
bb7_run_command(command="...", working_directory=".", timeout=60)
# returns only on exit 0; denials/timeout/nonzero raise as semantic failures
```

**W-SH-2 — Diagnose host**
```
bb7_get_system_info(include_processes=false, include_network=false, include_disk_usage=true)
bb7_list_processes(filter="python", sort_by="cpu|memory|name|pid|age", limit=20)
bb7_get_command_history(limit=20, filter="pytest")
```

**W-SH-3 — VS Code terminal context**
```
bb7_terminal_status(include_environment=true)
bb7_terminal_environment(include_paths=true, include_tools=true)
bb7_terminal_which(command="python", include_version=true)
bb7_terminal_cd(path="/home/daeron/Somnus-MCP")
bb7_terminal_run_command(command="pytest -q", timeout=120)
bb7_terminal_history(limit=20, include_analytics=true)
```

Compound `cd ... && ...` does not persist as cwd. Destructive checks are command-boundary aware.

---

## 10) Web — Fetch / Search / Analyze / Download

**Module:** `tools/enhanced_web_tool.py` · **4 surfaces** · Sole active web surface

**Surfaces:** `bb7_fetch_url` · `bb7_search_web` · `bb7_analyze_webpage` · `bb7_download_file`

### Suggested workflows

**W-WEB-1 — Research**
```
bb7_search_web(query, search_engine="duckduckgo|github|stackoverflow|docs", max_results=10)
→ bb7_fetch_url(url, extract_text=true, include_metadata=true, follow_redirects=true)
→ bb7_analyze_webpage(url, include_links=true, include_images=true, include_scripts=false, analyze_seo=true)
```

**W-WEB-2 — Download**
```
bb7_download_file(url, filename="...", destination="downloads", max_size=104857600, overwrite=false)
```

---

## 11) Visual / GUI — Evidence-bound

**Module:** `tools/visual_tool.py` · **5 surfaces** · Headless-safe import

**Surfaces:** `bb7_take_screenshot` · `bb7_find_on_screen` · `bb7_click_element` · `bb7_screen_monitor` · `bb7_window_info`

### Suggested workflows

**W-VIS-1 — Observe**
```
bb7_take_screenshot(region="fullscreen"|"x,y,w,h", format="png", include_analysis=true)
bb7_window_info(include_all=false, analyze_layout=false)
bb7_screen_monitor(duration=10, sensitivity=0.5, capture_changes=true)
```

**W-VIS-2 — Locate then act (30s one-use token)**
```
bb7_find_on_screen(target="Submit button", strategy="auto|text|color|template", confidence=0.8)
# only OCR/template mints evidence_token
bb7_click_element(evidence_token="...", click_type="left|right|double|middle", offset="x,y")
# color-only is never actionable; raw coords alone rejected; patch+geometry revalidated atomically
```

---

## 12) Auto / Optimization — Experiments & Guidance

**Module:** `tools/auto_tool_module.py` · **10 surfaces**

**Surfaces:** `bb7_workspace_context_loader` · `bb7_auto_session_resume` · `bb7_show_available_capabilities` · `bb7_intelligent_tool_guide` · `bb7_performance_optimization` · `bb7_optimization_results` · `bb7_analyze_workflow_patterns` · `bb7_intelligent_automation` · `bb7_cognitive_optimization` · `bb7_adaptive_learning`

### Suggested workflows

**W-AUTO-1 — Orient in a workspace**
```
bb7_workspace_context_loader()
bb7_auto_session_resume(workspace_path=".")
bb7_show_available_capabilities(category="memory")
bb7_intelligent_tool_guide(user_query="...")
```

**W-AUTO-2 — Measured optimization (two-phase)**
```
bb7_performance_optimization(optimization_type="comprehensive", sample_seconds=5.0)  # baseline + awaiting experiment
# ... real intervention ...
bb7_optimization_results(closeout=true, applied_optimizations=["real change 1"], sample_seconds=5.0)
```

**W-AUTO-3 — Pattern & automation discovery**
```
bb7_analyze_workflow_patterns(analysis_depth="deep", time_range_days=30)
bb7_intelligent_automation(automation_scope="workspace", learning_mode=true)
bb7_cognitive_optimization(focus_area="debugging")
bb7_adaptive_learning(learning_scope="tool recommendations", adaptation_speed="moderate")
```

---

## 13) Agent & Planner — OpenRouter (credit-gated)

**Modules:** `tools/openrouter_planner_tool.py` (3) · `tools/openrouter_agent_tool.py` (9)
**Note:** Live calls need `OPENROUTER_API_KEY`; `databus/openrouter.yaml` → `elephant-alpha`, empty fallback chain. Health/dry-run are no-network.

**Planner:** `bb7_planner_health` · `bb7_planner_template` · `bb7_planner_plan`
**Agent:** `bb7_agent_health` · `bb7_agent_list` · `bb7_agent_capabilities` · `bb7_agent_nodes` · `bb7_agent_messages` · `bb7_agent_handoff` · `bb7_agent_call` · `bb7_agent_run` · `bb7_agent_status`

### Suggested workflows

**W-PLAN-1 — No-network**
```
bb7_planner_health()
bb7_planner_template(intent="refactor auth module", context="...")
```

**W-PLAN-2 — Live planning**
```
bb7_planner_plan(intent="...", context="...", max_steps=6, temperature=0.3)  # exact-JSON, selected-model-only, no fallback
```

**W-AGENT-1 — Multi-agent**
```
bb7_agent_list()
bb7_agent_capabilities(agent_type="planner|debugger|analyzer|doc")
bb7_agent_run(agent_type="planner", task="...", context="...", max_iterations=8, execute_tools=true)
→ bb7_agent_status() | bb7_agent_nodes() | bb7_agent_messages(channel="...", since=...)
bb7_agent_handoff(to_agent="debugger", task="...", context="...")
bb7_agent_call(agent_type="analyzer", task="...", context="...")
```

---

## 14) Meta-Intelligence Facades — Registry-bound synthesis

**Module:** `tools/meta_intelligence_engine.py` · **4 surfaces** · Async dispatcher, arg-scoped caches, explicit workspace roots, 16K display budget

**Surfaces:** `bb7_code_consciousness` · `bb7_context_weaver` · `bb7_creative_problem_solver` · `bb7_muadib_mentat_bridge`

### Suggested workflows

**W-META-1 — Architectural intent**
```
bb7_code_consciousness(file_path=".", query="how does auth route?", max_depth=3, max_memories=5)
# code analysis + project context + memory + lisan recall + exo_route hints → synthesized intent
```

**W-META-2 — Holistic context**
```
bb7_context_weaver(workspace_path="/home/daeron/Somnus-MCP", context="task", task="next step", max_memories=7, days=7)
```

**W-META-3 — Problem decomposition**
```
bb7_creative_problem_solver(problem="design critique of X", goals=["..."], constraints=["..."], max_memories=5)
```

**W-META-4 — One-plane conductor snapshot (read-only)**
```
bb7_muadib_mentat_bridge(operation="snapshot", workspace_path=".", mentat_session_id="latest", max_insights=8)
# Muad'Dib checkpoints + exo health + live registry scoring + gateway runtime_identity + bounded Mentat reads
```

**Refresh gate:** after editing facades:
```
bb7_tool_refresh_module(module_name="meta_intelligence_engine"|"auto_tool_module")
```

---

## 15) Muad'Dib Neural Substrate

**Modules:** `muadib/muaddib.py` · `muadib/advanced_bridge.py` · `muadib/neural_config.py` · wraps via exoskeleton

**Surfaces:** `bb7_dt_advanced_features` · `bb7_dt_checkpoint_status` · `bb7_dt_self_play` · `bb7_dt_self_play_lock`

### Suggested workflows

**W-DT-1 — Inspect routing signals (provenance-tagged)**
```
bb7_dt_advanced_features(candidates=["bb7_memory_search","bb7_read_file"], category="memory")
# → {trained_q, trained_cooccur, untrained_embed}; requires MUADIB_ADVANCED_MODE=1 else {ok:false}
```

**W-DT-2 — Self-play (archive-only default)**
```
bb7_dt_self_play(episodes=32, max_steps=4, promote=false, update_qtable=false)  # candidate safetensors; JSON is ledger only
bb7_dt_checkpoint_status()
bb7_dt_self_play_lock(locked=true, reason="pin active", operator="daeron")
# envs: MUADIB_SELF_PLAY_ENABLED=1, INTERVAL_CYCLES=32, EPISODES=4, MAX_STEPS=3, PROMOTE=0, UPDATE_QTABLE=0, LOCK_ACTIVE=0
```

Validation without gateway: `mcp.venv/bin/python scripts/validate_muadib_self_play_weights.py --json`

---

## 16) Gateway built-ins — Health & identity

**Surfaces (not in `tools/`):** `ping_server` · `bb7_tool_health_report` · `bb7_tool_refresh_module`

```
ping_server()
bb7_tool_health_report(include_failed_loads=true, include_failed_calls=true, include_slow_tools=true)
# → status + registered_tools (sorted, deterministic) + loaded_modules + pid/ppid/session_id/transport/data_dir/source_sha256_16
# Use registered_tools + runtime_identity for parity; unused_tools is backward-compat only
```

---

## 17) Cross-category composition — the 4 most useful multi-category chains

**C-1 — Turn recovery (1-2 calls):** `bb7_lisan_recall` → execute (or `bb7_context_weaver` for workspace-aware richness)

**C-2 — Edit a codebase (4-7 calls):** `bb7_lisan_recall` → `bb7_analyze_code_complete` (or bounded `bb7_read_file` if >60KB) → `bb7_search_files` → `bb7_write_file` → verify via `bb7_python_execute_secure` or `bb7_run_command` → `bb7_memory_store` + `bb7_exo_reflect`

**C-3 — Research then synthesize (3-5 calls):** `bb7_search_web` → `bb7_fetch_url` → `bb7_memory_store` + `bb7_journal_record_thought`

**C-4 — Visual triage (2-4 calls):** `bb7_take_screenshot` → `bb7_find_on_screen` → `bb7_click_element` (fresh OCR/template token only)

---

## 18) Budgets, reflection, and done criterion

**Governor:** 0-2 think/scope · 3-6 normal · 7-12 complex+verification · 13+ needs reason + `bb7_exo_execute_step` checkpointing.

**Reflect:** after any substantive chain → `bb7_exo_reflect(plan_id, tools_used, success, intent)` — Beta priors + chain promotion + MCTS signal + momentum transitions. Distillation is witness, not authority. Optional `bb7_exo_kpi_report(plan_id)`.

**Done:** objective moved, budget respected/justified, durable state captured, next action clear.

---

## Appendix — Compact tool map by category

| Category | Module | Approx | Tools (abbrev) |
|---|---|---|---|
| Control / routing | `exoskeleton_tool` | 22 | bootstrap, list_tool_categories, category_specific_tools, exo_route, route_focused, lisan_intend, exo_plan, briefing, preemptive_recovery, exo_state, suggest_next, execute_step, resume_plan, kpi_report, exo_reflect, get_recent_activity, lisan_recall, lisan_distill, dt_advanced_features, dt_checkpoint_status, dt_self_play, dt_self_play_lock |
| Memory | `memory_tool` | 14 | bulk_store, categories, consolidate, delete, export, get_related, insights, list, retrieve, search, stats, store, surface_context, timeline |
| Interconnect | `memory_interconnect` | 9 | analyze_entry, cluster, concept_network, consolidate_index, extract_concepts, find_gaps, get_insights, graph, intelligent_search |
| Sessions | `session_manager_tool` | 16 | start/pause/resume/list_sessions, log_event, capture_insight, record_workflow, update_focus, get_summary, get_insights, cross_session_analysis, session_recommendations, learned_patterns, session_intelligence, link_memory_to_session, auto_memory_stats |
| Journal | `thought_journal_tool` | 11 | record_thought, capture_decision, add_outcome, search, get_decision_trail, surface_relevant, detect_conflicts, generate_retrospective, get_reasoning_chain, stats, linked_entries |
| Files | `file_tool` | 12 | read/write/append/copy/move/delete_file, list_directory, search_files, file_info, get_file_info, file_cache_stats, operation_history |
| Shell | `shell_tool` | 4 | run_command, get_system_info, list_processes, get_command_history |
| Terminal | `vscode_terminal_tool` | 6 | terminal_cd, terminal_environment, terminal_history, terminal_run_command, terminal_status, terminal_which |
| Project | `project_context_tool` | 4 | analyze_project_structure, get_code_metrics, get_project_dependencies, get_recent_changes |
| Auto | `auto_tool_module` | 10 | adaptive_learning, analyze_workflow_patterns, auto_session_resume, cognitive_optimization, intelligent_automation, intelligent_tool_guide, optimization_results, performance_optimization, show_available_capabilities, workspace_context_loader |
| Web | `enhanced_web_tool` | 4 | fetch_url, search_web, analyze_webpage, download_file |
| Visual | `visual_tool` | 5 | take_screenshot, find_on_screen, click_element, screen_monitor, window_info |
| Code (baseline) | `code_analysis_tool` | 4 | analyze_code, code_suggestions, execute_code_safely, security_audit* |
| Code (enhanced) | `enhanced_code_analysis_tool` | 4 | analyze_code_complete, security_audit (canonical), python_execute_secure, get_execution_audit |
| Planner | `openrouter_planner_tool` | 3 | planner_health, planner_template, planner_plan |
| Agent | `openrouter_agent_tool` | 9 | agent_health, agent_list, agent_capabilities, agent_nodes, agent_messages, agent_handoff, agent_call, agent_run, agent_status |
| Meta | `meta_intelligence_engine` | 4 | code_consciousness, context_weaver, creative_problem_solver, muadib_mentat_bridge |
| Gateway | `mcp_server.py` | 3 | ping_server, tool_health_report, tool_refresh_module |

\* duplicate `bb7_security_audit`: baseline loads first, enhanced wins registration.

**Total** varies with gateway version/headless state (~140 ballpark). Use `bb7_exo_list_tool_categories` + `bb7_tool_health_report(registered_tools)` for live truth. See `runtime-tools/README.md §2` for dated source probe (18 modules / 141 surfaces on 2026-06-06) and 2026-06-12 `infrustructure/` retirement.
