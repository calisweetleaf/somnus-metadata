---
name: somnus-metadata-dev
description: Develop, validate, and operate inside the somnus-metadata repository (core 2.0.0 normative specification and stdlib-only Python toolkit). Use when editing src/somnus/, running tests or semantic checks, handling E_HOST or registry conflicts, or navigating SPEC.md and DECISIONS.md.
---

# `somnus-metadata-dev` — Repository Operating Skill

Use this skill whenever working inside `/home/daeron/Repositories/somnus-metadata` (`somnus://metadata/core/2.0.0`).

## 1. Authority Spine and Key Files

Consult `filetree.md` before deep directory traversal. Authority flows strictly top-down:

| Path | Role and Constraints |
| --- | --- |
| `AGENTS.md` | Repository operating rules, verification gate, and environment constraints. |
| `SPEC.md` | Single normative contract (`somnus://metadata/core/2.0.0`). Implementation disagreements are code defects; contract changes require an explicit decision and version update under `SPEC.md` §23. |
| `DECISIONS.md` | Ratified architecture decisions D1–D18. Never silently revise a decision; add a new ratified decision and bump revision (`somnus bump`). |
| `PLAN.md` | Current delivery state and maintenance handoff (non-normative). |
| `filetree.md` | Spatial and dependency navigation map for the checkout. |
| `CONTRIBUTING.md` | Observed naming rules (`E_*`/`W_*`, `_RE`/`_PATTERN`, command `run(args, ctx)`), PR checklist, and 7-day minimum release age policy. |
| `runbooks/registry-recovery.md` | Operational runbook for `~/.somnus/somnus.db` backup/restore, `somnus index --full`, and `somnus q --conflicts`. |
| `runbooks/host-write-incident.md` | Operational runbook for `E_HOST` refusals, `somnus stamp --write`, and header recovery from `revisions.header_yaml`. |
| `Somnus Markdown Metadata Standard Research.md` | Frozen historical evidence. **Never overwrite or edit.** |
| `archive/` | Historical v0.1 and v2-proposal material (D15). **Never import from `archive/` or cite as active behavior.** |

## 2. Environment and Surgeon Constraints

- **Python Runtime:** Python `>=3.11`, **stdlib-only runtime** (`pyproject.toml` `dependencies = []` must remain empty).
- **OneDrive + Surgeon Constraint:** This checkout resides on a OneDrive-synced filesystem. Multi-file Surgeon transactions (`multi_edit`, `prepare`/`commit`) fail with `WinError 5`. Always execute **one atomic single-file Surgeon operation (`op=edit` or `op=create`) per call** with `project_root="/home/daeron/Repositories/somnus-metadata"`.
- **Global Registry Location:** `$SOMNUS_HOME/somnus.db` (default `~/.somnus/somnus.db`), configured via `$SOMNUS_HOME/config.toml` and optional local `.somnus.toml` (precedence: CLI flag > `.somnus.toml` > `$SOMNUS_HOME/config.toml` > built-ins).

## 3. Setup and Verification Gate

Run all verification commands from the repository root (`/home/daeron/Repositories/somnus-metadata`):

### POSIX Verification Gate (Mandatory Before Completion)

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
python -m mypy   # dev tool; install with: pip install "mypy>=1.9"
```

### PowerShell Equivalent

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
```

### Exit Codes (`SPEC.md` §19.3, `src/somnus/output.py`)

- `0` (`EXIT_OK`): Clean execution / validation passed.
- `1` (`EXIT_INVALID`): Validation errors, refused operations (`E_HOST`, `E_LIFECYCLE`, `E_SCHEMA`, etc.), or open registry conflicts.
- `2` (`EXIT_USAGE`): Usage, configuration, I/O, or environment errors.

## 4. High-Value Implementation Map (`src/somnus/`)

- `src/somnus/model/`: Declarative schema (`schema.py`), controlled vocabularies (`vocab.py`), 4-level validation pipeline (`validate.py`: `carrier`, `core`, `semantic`, `canon`), lifecycle state machine (`lifecycle.py`), JSON Schema Draft 2020-12 exporter (`jsonschema_export.py`).
- `src/somnus/yamlsub.py`: Restricted YAML parser and canonical serializer (D7). Double-quoted strings; no anchors, aliases, tags, nulls, duplicate keys, or implicit typing.
- `src/somnus/carriers/`: Carrier protocol (`__init__.py`), Markdown frontmatter/HTML comment (`markdown.py`), `#`/`%`/`//`/`--` line comments (`linecomment.py`), CSS/XML block comments (`blockcomment.py`), and `<file>.somnus.yaml` sidecars (`sidecar.py`).
- `src/somnus/document.py`: `Document` loader, `_verify_preserved` (`E_HOST` guard), and `atomic_write` (same-dir tempfile + `fsync` + `os.replace`).
- `src/somnus/db/`: SQLite DDL (`schema.sql`, `DB_USER_VERSION = 1`) and `Store` (`store.py`). Zero JSON stored (D4).
- `src/somnus/commands/` & `src/somnus/cli.py`: CLI surface (`init`, `new`, `stamp`, `check`, `index`, `q`, `ls`, `status`, `bump`, `set`, `fork`, `regions`, `migrate`, `stale`, `schema`, `brief`, `edit`, `mcp`). `_MODULES = {"q": "query", "set": "set_fields"}`.
- `src/somnus/tui/`: Terminal UI (`app.py`, `term.py`, `widgets.py`) and shared editable field model (`form.py`, shared with `commands/set_fields.py` per D16).
- `src/somnus/mcp.py`: Newline-delimited stdio JSON-RPC 2.0 MCP server (D17); exposes all CLI commands except `edit` and `mcp` as closed-schema tools and runs each via subprocess returning text/TSV output.

## 5. Rules for Somnus-Managed Artifacts

1. **No fabricated metadata:** Never invent IDs, timestamps, dates, actors, licenses, evidence, or acceptance records (D6, D10).
2. **Never hand-edit `id` or `revision`:** Use `somnus bump PATH --reason "..."` after body edits to mint a new revision and resolve `revision` conflicts. Use `somnus status PATH NEW_STATUS` for lifecycle transitions (D12).
3. **Use `somnus set` for header fields (D16):** Modify `title`, `summary`, `purpose`, `classification.category|type|role|scope|tags`, `access.visibility`, or `ingestion.disposition` via `somnus set PATH FIELD=VALUE...`. Put tool-specific metadata under `extensions.<owner>`.
4. **Host-byte preservation (`E_HOST`):** Every write re-extracts the envelope and verifies that host lines outside the envelope are unchanged (`src/somnus/document.py:156-169`). If a write is refused with `E_HOST`, consult `runbooks/host-write-incident.md`.
5. **Registry reconciliation:** Run `PYTHONPATH=src python -m somnus.cli index` (or `--full`) to reconcile roots into `~/.somnus/somnus.db`, and `PYTHONPATH=src python -m somnus.cli q --conflicts` to inspect open conflicts (`runbooks/registry-recovery.md`).
