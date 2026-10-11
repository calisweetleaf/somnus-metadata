# Implementation Plan — Somnus Metadata System (`somnus` CLI & Merged Standard)

## Goal Description

The current workspace contains a split baseline:
1. `DECISIONS.md` adopted an early v0.1 research draft proposing loose JSON-based provenance logs (`provenance/*.json`), a hybrid frontmatter root, and visible `:::submatter` container directives.
2. `docs/SOMNUS_FRONTMATTER_SPEC_v2.md` designed a significantly more advanced semantic system with a unified `somnus:` namespace, hidden comment region markers, revision/representation separation, and rich knowledge graphs, but was left unintegrated.
3. The operator explicitly rejected JSON event ledgers and fragmented documentation ("THIS SHOULD BE A GLOBAL .DB WITH A COMPLEX DETAILED YET HUMAN READABLE SCHEMA... JSON IS FORBIDDEN, IT IS SLOW ON INFERENCE").
4. Autonomous agents frequently produce mounds of unmanaged, duplicate, or unvalidated files without shared identity, lifecycle status, or search capability.

**The Solution:**
Unify the system into a single authoritative standard and a production-grade, globally installable tool (`somnus`):
- **Normative Specification (`SPEC.md`)**: A consolidated specification synthesizing v2's semantic model and v0.1's concrete profiles under schema `somnus://metadata/core/2.0.0`.
- **Ratified Decisions (`DECISIONS.md`)**: Formally ratifying decisions D1–D15, overriding the prior draft.
- **Archive Legacy Code (`archive/`)**: Move superseded v0.1 files and intermediate proposals into `archive/` with strict warnings against treating dead code as canon.
- **Zero-Dependency Python Package (`somnus`)**: A lightweight CLI and interactive terminal UI built strictly on the Python 3.11+ standard library (`tomllib`, `sqlite3`, `argparse`, `dataclasses`, `typing`, `pathlib`, `difflib`, `ctypes`/`msvcrt` for Windows VT). Installed globally via `uv tool install --editable .`.
- **Global SQLite Registry & Ledger (`~/.somnus/somnus.db`)**: Plain-English tables, views, and an append-only event ledger with zero JSON storage and zero JSON agent output.
- **Restricted YAML Engine (`yamlsub.py`)**: A dedicated stdlib parser and canonical serializer for the v2 §13 YAML subset, ensuring byte-stable round-tripping and format integrity without external dependencies.
- **Complete Suite of Operations**: `new`, `stamp` (dry-run first), `check`, `index`, `q`, `ls`, `status`, `bump`, `fork`, `regions`, `migrate`, `stale`, `edit` (TUI), `schema`, and `brief`.

---

## User Review Required

> [!IMPORTANT]
> **Key Architecture Commitments (Ratified Decisions D1–D15):**
> 1. **D1 Unified Namespace**: Every standardized field resides exclusively under `somnus:`. No flat or hybrid root leakage.
> 2. **D2 In-Body Regions**: Paired comment markers `<!-- somnus:region:begin <id> -->` and `<!-- somnus:region:end <id> -->`, tracked in the header registry. `:::submatter` directives are deprecated and supported solely via migration.
> 3. **D3 Identity**: `urn:somnus:artifact:<uuidv7>` for new documents; legacy UUIDv4 identities are preserved without reminting. UUID timestamp is never equated to authored creation date.
> 4. **D4 Single Global SQLite Database**: Located at `$SOMNUS_HOME/somnus.db` (default `~/.somnus/somnus.db`). Human-readable relational tables and views. **Strict zero-JSON policy** in database storage and agent CLI outputs.
> 5. **D5 Zero Tolerance**: Strict schema evaluation (`unevaluatedProperties: false` equivalent). Unknown fields trigger errors. Experimental attributes are strictly confined to `extensions.<owner>`.
> 6. **D6 Rich Headers via Tool Automation**: Full v2 core schema in every document; CLI automatically populates standard defaults (visibility, allowed uses, standing, disposition) from configuration.
> 7. **D7 Canonical YAML Serialization**: Stdlib-only restricted parser/serializer enforcing deterministic field ordering and safe string quoting.
> 8. **D14 Compiler-Grade Diagnostic Output**: Output formatted as `path:line:col: severity CODE field: message` plus `--tsv` support for low token consumption and instant greppability.
> 9. **D15 Dead Code Isolation**: Devolved artifacts moved to `archive/` with prominent non-truth warnings. `src/` modules never import from `archive/`.

---

## Open Questions

All major architectural questions were resolved during the initial clarification round:
- **Language & Runtime**: Pure Python (stdlib-only), Python ≥ 3.11, globally installed with `uv tool install`.
- **Header Structure**: Full v2 core schema with automated default population.
- **Tool Scope**: Complete command suite including interactive TUI and multi-format carriers.
- **Legacy Files**: Clean relocation to `archive/`.

---

## Proposed Changes

```
somnus-metadata/
├── AGENTS.md                          # [MODIFY] Project router updated for new SPEC and tool usage
├── SPEC.md                            # [NEW] Normative unified specification (v2 + v0.1 profiles)
├── DECISIONS.md                       # [MODIFY] Formally ratified decisions D1–D15
├── PLAN.md                            # [NEW] Execution plan mirrored in repo
├── filetree.md                        # [MODIFY] Updated spatial map reflecting clean layout
├── pyproject.toml                     # [NEW] Pure-Python package configuration (setuptools backend)
├── src/somnus/
│   ├── __init__.py                    # [NEW] Package metadata and schema constants
│   ├── __main__.py                    # [NEW] Module entrypoint (python -m somnus)
│   ├── cli.py                         # [NEW] Subcommand dispatcher and global argument parser
│   ├── output.py                      # [NEW] Diagnostic objects, compiler formatter, exit codes
│   ├── yamlsub.py                     # [NEW] Restricted YAML 1.2.2 parser and canonical serializer
│   ├── ids.py                         # [NEW] UUIDv7 generation (RFC 9562), URN parsing, slugifier
│   ├── config.py                      # [NEW] Hierarchical configuration engine via tomllib
│   ├── document.py                    # [NEW] Atomic document loader/saver with newline preservation
│   ├── regions.py                     # [NEW] Comment marker scanner and header registry synchronizer
│   ├── infer.py                       # [NEW] Heuristic classification and title inference for stamp
│   ├── carriers/
│   │   ├── __init__.py                # [NEW] Carrier protocol, registry, and auto-detection
│   │   ├── markdown.py                # [NEW] Markdown frontmatter & HTML comment carriers
│   │   ├── linecomment.py             # [NEW] Comment-prefixed carriers (#, %, //, --)
│   │   ├── blockcomment.py            # [NEW] Block-comment carriers (/* */, <!-- -->)
│   │   └── sidecar.py                 # [NEW] Detached sidecar bindings (<file>.somnus.yaml)
│   ├── model/
│   │   ├── vocab.py                   # [NEW] Canonical controlled vocabularies and enums
│   │   ├── schema.py                  # [NEW] Declarative schema tree for core and profiles
│   │   ├── lifecycle.py               # [NEW] Formal lifecycle status transition state machine
│   │   ├── validate.py                # [NEW] Multi-stage validator (envelope, syntax, schema, semantic)
│   │   └── jsonschema_export.py       # [NEW] Export converter for JSON Schema Draft 2020-12
│   ├── db/
│   │   ├── schema.sql                 # [NEW] Relational DDL, views, and migration pragmas
│   │   └── store.py                   # [NEW] SQLite persistence engine, ledger, and query runner
│   ├── commands/                      # [NEW] Independent command modules
│   │   ├── init.py                    # Initialize database and user configuration
│   │   ├── new.py                     # Scaffold new document with UUIDv7 and defaults
│   │   ├── stamp.py                   # Safely inject headers into legacy/headerless documents
│   │   ├── check.py                   # Validate documents with structured diagnostics
│   │   ├── index.py                   # Reconcile filesystem roots into the SQLite database
│   │   ├── query.py                   # Execute read-only SQL queries or view shortcuts
│   │   ├── ls.py                      # List indexed artifacts with filters
│   │   ├── status.py                  # Advance document lifecycle with transition validation
│   │   ├── bump.py                    # Increment authored revision and resolve drift
│   │   ├── fork.py                    # Branch document with reminted UUID and lineage link
│   │   ├── regions.py                 # Audit and synchronize in-body region markers
│   │   ├── migrate.py                 # Upgrade legacy v0.1 documents to v2 specification
│   │   ├── stale.py                   # Identify orphan drafts, duplicates, and missing replacements
│   │   ├── schema.py                  # Inspect schema definitions and export JSON Schema
│   │   └── brief.py                   # Generate concise instruction cards for agent integration
│   └── tui/
│       ├── term.py                    # [NEW] Windows VT console initialization and raw key reader
│       ├── widgets.py                 # [NEW] Minimalist terminal widgets (lists, pickers, inputs)
│       └── app.py                     # [NEW] Full-screen document browser and header form editor
├── tests/
│   ├── fixtures/                      # [NEW] Golden fixtures across all carrier formats and edge cases
│   ├── test_yamlsub.py                # [NEW] Restricted YAML parser and round-trip verification
│   ├── test_ids.py                    # [NEW] UUIDv7 and URN verification
│   ├── test_config.py                 # [NEW] Configuration resolution tests
│   ├── test_document.py               # [NEW] Document loading, atomic saving, and byte preservation
│   ├── test_regions.py                # [NEW] Region marker extraction and fence isolation tests
│   ├── test_validate.py               # [NEW] Multi-stage validation rule verification
│   ├── test_lifecycle.py              # [NEW] State transition validation tests
│   ├── test_store.py                  # [NEW] Database indexing, views, and event ledger tests
│   ├── test_carriers.py               # [NEW] Carrier preservation tests across language syntaxes
│   ├── test_commands.py               # [NEW] End-to-end CLI workflow tests
│   └── test_conformance.py            # [NEW] Verification of all 21 acceptance criteria from SPEC §20.2
└── archive/
    ├── README.md                      # [NEW] Disclaimer marking archived assets as non-authoritative
    ├── v0.1/                          # [MOVE] Legacy specs, research-derived schemas, and v0.1 tools
    └── v2-proposal/                   # [MOVE] Intermediate proposal and diff documents
```

---

### Component 1: Governance, Specification & Clean Layout

#### [NEW] `SPEC.md`
The single normative specification for the Somnus Metadata System.
- Standardizes schema URI `somnus://metadata/core/2.0.0`.
- Includes full core field definitions (identity, classification, lifecycle, authority, time, knowledge, access, ingestion).
- Includes concrete profile schemas for `specification` and `benchmark` under `somnus.profile_data`.
- Codifies the lifecycle transition state machine.
- Defines comment region syntax: `<!-- somnus:region:begin <id> -->` ... `<!-- somnus:region:end <id> -->`.
- Formalizes the relational schema of `$SOMNUS_HOME/somnus.db`.
- Standardizes the 21 conformance fixture criteria.

#### [MODIFY] `DECISIONS.md`
Overwrites the prior unratified draft with the ratified decisions D1–D15. Each record documents context, alternatives, decision rationale, and operational consequences.

#### [NEW] `archive/README.md`
```markdown
# ARCHIVE — HISTORICAL AND DEVOLVED ASSETS

> [!WARNING]
> The contents of this directory are preserved strictly for historical lineage.
> **THEY ARE NOT TRUTH, NOT NORMATIVE, AND MUST NOT BE IMPORTED OR CITED AS ACTIVE SPECIFICATIONS.**
> The active normative standard is defined exclusively in `SPEC.md`.
```

#### [MOVE] Relocate Devolved Assets to `archive/`
- Move `SOMNUS-METADATA-SPEC-v0.1.md` → `archive/v0.1/SOMNUS-METADATA-SPEC-v0.1.md`
- Move `GLOSSARY.md` → `archive/v0.1/GLOSSARY.md`
- Move `schemas/` → `archive/v0.1/schemas/`
- Move `examples/` → `archive/v0.1/examples/`
- Move `tools/validate.py` & `tools/operator_docs_audit.py` → `archive/v0.1/tools/`
- Move `docs/SOMNUS_FRONTMATTER_SPEC_v2.md` → `archive/v2-proposal/SOMNUS_FRONTMATTER_SPEC_v2.md`
- Move `docs/differences.md` → `archive/v2-proposal/differences.md`

#### [MODIFY] `AGENTS.md` and `filetree.md`
Update root routers to direct human and agent contributors to `SPEC.md`, `DECISIONS.md`, and the `somnus` CLI commands.

---

### Component 2: Packaging & CLI Framework

#### [NEW] `pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68.0.0"]
build-backend = "setuptools.build_meta"

[project]
name = "somnus"
version = "0.1.0"
description = "Universal semantic metadata standard and engineering toolkit"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
somnus = "somnus.cli:main"
```

#### [NEW] `src/somnus/output.py`
Standardizes diagnostic reporting and process exit codes:
```python
from dataclasses import dataclass
from typing import Literal

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_USAGE = 2

@dataclass(frozen=True)
class Diagnostic:
    path: str
    line: int
    col: int
    severity: Literal["error", "warning"]
    code: str
    field: str
    message: str

def render(diagnostics: list[Diagnostic], fmt: Literal["text", "tsv"] = "text") -> str: ...
```

#### [NEW] `src/somnus/cli.py`
Implements fast, lazy argument parsing and command dispatch. Global flags include `--version`, `--actor`, `--tsv`, `--no-color`, and `--debug`.

---

### Component 3: Core Foundation Modules

#### [NEW] `src/somnus/yamlsub.py`
A zero-dependency parser and canonical serializer for the v2 §13 YAML subset:
- **Parser capabilities**: Supports 2-space indentation, mappings, sequence blocks (`- item`), flow sequences (`["a", "b"]`), double-quoted strings with standard escapes, single-quoted strings, unquoted integers and finite decimals, booleans (`true`/`false`), block scalar literals (`|`), folded scalars (`>`), and `#` comments.
- **Strict safety rejections**: Rejects tabs, `null`/`~`/omitted scalar values, anchors (`&`), aliases (`*`), merge keys (`<<`), custom tags (`!`), directives (`%`), intra-payload delimiters (`---`), duplicate mapping keys at any depth, and non-string mapping keys.
- **Canonical Serializer**:
  - Emits keys in the canonical order mandated by SPEC §13 (schema, id, revision, title, summary, classification, lifecycle, authority, time, names, context, ownership, locations, representations, content, knowledge, access, ingestion, profiles, profile_data, bindings, extensions).
  - Enforces explicit double-quoting on all strings.
  - Automatically formats compact scalar lists using flow syntax when within 88 columns.
  - Guarantees byte-stable round-trips: `dumps(loads(s)) == s`.

#### [NEW] `src/somnus/ids.py`
Identifier minting and parsing:
- `new_artifact_urn() -> str`: Mints `urn:somnus:artifact:<uuidv7>` with millisecond precision and random entropy compliant with RFC 9562.
- `parse_urn(urn: str) -> tuple[str, str]`: Extracts namespace and entity key.
- `slugify(title: str) -> str`: Normalizes titles into filesystem-safe kebab-case identifiers.

#### [NEW] `src/somnus/config.py`
Hierarchical configuration reader using standard library `tomllib`:
- Precedence: Explicit CLI flag > Nearest parent `.somnus.toml` > Global `~/.somnus/config.toml` > Built-in defaults.
- Default configuration provides:
  ```toml
  actor = "operator"
  [defaults]
  category = "engineering"
  role = "normative"
  scope = "component"
  visibility = "internal"
  allowed_uses = ["archive", "search", "reason"]
  standing = "candidate"
  disposition = "candidate"
  body_role = "specification"

  [index]
  roots = ["."]
  exclude = ["archive/**", ".git/**", "node_modules/**", "**/__pycache__/**"]
  ```

---

### Component 4: Document Modeling, Validation & Regions

#### [NEW] `src/somnus/model/vocab.py`
Comprehensive definition of all standard enums, frozen as immutable tuples:
- `CATEGORIES`: `("research", "engineering", "operations", "governance", "context", "archive")`
- `TYPES`: `("whitepaper", "specification", "architecture-record", "report", "task", "plan", "notepad", "benchmark", "test-result", "decision-record", "runbook", "index", "state", "memory", "source-code", "configuration", "dataset", "equation-set", "conversation", "asset")`
- `ROLES`: `("normative", "informative", "working", "exploratory", "historical")`
- `SCOPES`: `("ecosystem", "fleet", "repository", "subsystem", "module", "component", "artifact")`
- `STATUSES`: `("draft", "proposed", "provisional", "active", "experimental", "superseded", "deprecated", "historical", "archived", "rejected")`
- `STANDINGS`: `("unasserted", "candidate", "accepted", "retired", "rejected")`
- `VISIBILITIES`: `("operator-only", "internal", "public")`
- `ALLOWED_USES`: `("archive", "search", "reason", "quote", "export", "training", "execute")`
- `DISPOSITIONS`: `("candidate", "archive-only", "excluded", "canonical-candidate")`
- `BODY_ROLES`: `("narrative", "specification", "instruction", "configuration", "source", "conversation", "dataset", "mixed")`
- `REGION_KINDS`: `("section", "definition", "invariant", "decision", "hypothesis", "evidence", "equation", "table", "code", "example", "archive")`

#### [NEW] `src/somnus/model/lifecycle.py`
Implements the formal transition state machine defined in SPEC §6.1:
- Validates transitions (e.g., `draft` → `proposed`/`experimental`/`rejected`; `active` → `superseded`/`deprecated`/`historical`).
- Enforces requirement of `reason` on abandonment or reactivation.
- Enforces requirement of `replacement_refs` when transitioning to `superseded`.

#### [NEW] `src/somnus/model/validate.py`
Executes multi-stage document validation:
1. **Stage 1 (Syntax & Parsing)**: Validates restricted YAML syntax, checks duplicate keys, rejects forbidden scalars.
2. **Stage 2 (Structural & Schema)**: Validates required core properties, exact types, controlled vocabulary values, RFC 3339 timestamp offsets, ISO dates, and local identifier regexes. Enforces closed property set (unknown fields outside `extensions` fail with `E_SCHEMA`).
3. **Stage 3 (Semantic & Consistency)**:
   - Evaluates conditional requirements (e.g., `standing: accepted` requires `valid_time` and `acceptance_ref`).
   - Ensures `time.updated_at >= time.created_at`.
   - Confirms `valid_time.basis` matches provided `from`/`until` bounds.
   - Verifies that `claim` records match declared region references.
   - Matches header-registered regions with in-body markers.

#### [NEW] `src/somnus/regions.py`
- Scans document bodies for paired region markers:
  ```markdown
  <!-- somnus:region:begin r-example -->
  ...
  <!-- somnus:region:end r-example -->
  ```
- Fenced-code awareness: Ignores marker-like text occurring inside Markdown code fences (```` ``` ```` or `~~~` of any length) and indented code blocks.
- Verifies proper nesting and detects crossing, duplicate, or unclosed markers (`E_REGION`).
- Provides `sync_registry()` to reconcile body markers with `somnus.knowledge.regions` in the frontmatter.

#### [NEW] `src/somnus/document.py`
Encapsulates loading and atomic saving:
- Detects and preserves line-ending style (`\n` vs `\r\n`).
- Strips and suppresses UTF-8 BOMs.
- `save(doc, payload)` performs atomic write via temporary file replacement (`os.replace`).
- Guarantees body preservation: asserts that body byte content is strictly unchanged after frontmatter manipulation.

---

### Component 5: Multi-Format Carrier Bindings

#### [NEW] `src/somnus/carriers/`
Implements carrier extraction and injection across document formats per SPEC §14:
- `markdown.py`: Handles standard Markdown frontmatter (`---` ... `---`) and hidden HTML comment envelopes (`<!-- somnus:metadata:v2` ... `somnus:end -->`).
- `linecomment.py`: Handles comment-prefixed formats preserving required preambles:
  - Hash (`# `): Python (preserving shebang and encoding cookies on lines 1–2), Shell, PowerShell, TOML, YAML, R.
  - Percent (`% `): LaTeX (preserving `% !TeX` magic comments).
  - Slash (`// `): JavaScript, TypeScript, Rust, C, C++, Go.
  - SQL (`-- `): SQL scripts.
- `blockcomment.py`: Handles CSS (`/* ... */`) and XML/SVG/HTML (`<!-- ... -->`) with terminator escaping.
- `sidecar.py`: Handles binary, JSON, and unsupported formats by maintaining `<filename>.somnus.yaml` sidecar files containing an explicit primary binding.

---

### Component 6: Relational Database & Persistence

#### [NEW] `src/somnus/db/schema.sql`
Defines the SQLite database schema at `$SOMNUS_HOME/somnus.db`:
```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA user_version = 1;

CREATE TABLE roots (
    root_id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    label TEXT,
    added_at TEXT NOT NULL
);

CREATE TABLE artifacts (
    artifact_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    role TEXT NOT NULL,
    scope TEXT NOT NULL,
    status TEXT NOT NULL,
    standing TEXT NOT NULL,
    visibility TEXT NOT NULL,
    disposition TEXT NOT NULL,
    current_revision INTEGER NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE revisions (
    artifact_id TEXT REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
    revision INTEGER NOT NULL,
    schema_uri TEXT NOT NULL,
    header_yaml TEXT NOT NULL,
    payload_digest TEXT NOT NULL,
    body_digest TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    PRIMARY KEY (artifact_id, revision)
);

CREATE TABLE locations (
    root_id INTEGER REFERENCES roots(root_id) ON DELETE CASCADE,
    rel_path TEXT NOT NULL,
    artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
    carrier TEXT NOT NULL,
    file_mtime TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    present INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (root_id, rel_path)
);

CREATE TABLE tags (
    artifact_id TEXT REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (artifact_id, tag)
);

CREATE TABLE regions (
    artifact_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    region_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT,
    line_from INTEGER,
    line_until INTEGER,
    PRIMARY KEY (artifact_id, revision, region_id),
    FOREIGN KEY (artifact_id, revision) REFERENCES revisions(artifact_id, revision) ON DELETE CASCADE
);

CREATE TABLE relations (
    artifact_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    relation_id TEXT NOT NULL,
    subject_ref TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_ref TEXT NOT NULL,
    assessment TEXT NOT NULL,
    PRIMARY KEY (artifact_id, revision, relation_id),
    FOREIGN KEY (artifact_id, revision) REFERENCES revisions(artifact_id, revision) ON DELETE CASCADE
);

CREATE TABLE entities (
    entity_ref TEXT NOT NULL,
    label TEXT NOT NULL,
    kind TEXT NOT NULL,
    source_artifact TEXT REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
    source_revision INTEGER NOT NULL,
    PRIMARY KEY (entity_ref, source_artifact, source_revision)
);

CREATE TABLE claims (
    artifact_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    claim_id TEXT NOT NULL,
    subject_ref TEXT NOT NULL,
    predicate TEXT NOT NULL,
    statement TEXT NOT NULL,
    kind TEXT NOT NULL,
    assessment TEXT NOT NULL,
    region_ref TEXT,
    PRIMARY KEY (artifact_id, revision, claim_id),
    FOREIGN KEY (artifact_id, revision) REFERENCES revisions(artifact_id, revision) ON DELETE CASCADE
);

CREATE TABLE conflicts (
    conflict_id INTEGER PRIMARY KEY,
    kind TEXT CHECK (kind IN ('revision', 'duplicate-id', 'authority', 'identity')) NOT NULL,
    artifact_id TEXT NOT NULL,
    detail TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT
);

CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    artifact_id TEXT,
    revision INTEGER,
    path TEXT,
    detail TEXT
);

CREATE VIEW docs AS
SELECT
    a.title,
    a.type,
    a.status,
    a.standing,
    a.current_revision AS rev,
    r.path || '/' || l.rel_path AS path,
    a.last_seen_at,
    a.artifact_id
FROM artifacts a
JOIN locations l USING (artifact_id)
JOIN roots r USING (root_id)
WHERE l.present = 1;

CREATE VIEW open_conflicts AS
SELECT * FROM conflicts WHERE resolved_at IS NULL;

CREATE VIEW history AS
SELECT event_id, at, actor, action, path, revision, detail
FROM events
ORDER BY event_id DESC;
```

#### [NEW] `src/somnus/db/store.py`
Provides thread-safe persistence access:
- Read-only queries enforced via SQLite `file:...?mode=ro` URI connections.
- Incremental indexing skipping unchanged `(mtime, size)` tuples.
- Detection of duplicate IDs across files, flagging `duplicate-id` conflicts.
- Detection of modified content with unchanged revisions, flagging `revision` conflicts.
- Near-duplicate title detection using normalized string similarity.
- Audit logging of all mutating operations to the `events` table.

---

### Component 7: CLI Commands

Each subcommand is encapsulated in `src/somnus/commands/<name>.py`:
- `init.py`: Scaffolds `~/.somnus/config.toml` template, initializes database tables, and registers initial workspace roots.
- `new.py`: Generates a conformant artifact with a newly minted UUIDv7, default values, initial revision 1, creation timestamp, and slugified filename. Checks for title collisions before creating.
- `stamp.py`: Analyzes unmanaged files, infers title and classification (via `infer.py`), constructs a valid header, and outputs a unified diff. Injects header only when `--write` is specified.
- `check.py`: Evaluates files or entire roots through the 3-stage validation pipeline, emitting compiler-style diagnostic lines or TSV.
- `index.py`: Traverses roots, indexes revisions and graph records, detects drift, records events, and flags conflicts.
- `query.py`: Runs ad-hoc read-only SQL queries or built-in shortcuts (`--docs`, `--conflicts`, `--history`).
- `ls.py`: Filters and displays active indexed documents from the `docs` view.
- `status.py`: Enforces state transitions via `lifecycle.py`, bumps revision, updates file frontmatter, and logs the transition event.
- `bump.py`: Increments artifact revision in both frontmatter and database, resolving revision drift conflicts.
- `fork.py`: Clones an existing artifact with a new UUIDv7, resets revision to 1, and records a `derived_from` relation pointing to the parent.
- `regions.py`: Audits in-body markers and synchronizes `knowledge.regions`.
- `migrate.py`: Translates legacy v0.1 documents to the v2 core specification.
- `stale.py`: Scans roots for stale drafts, abandoned proposals, unreplaced superseded files, and near-duplicate title clusters.
- `schema.py`: Displays documentation for schema fields and emits JSON Schema Draft 2020-12 on request.
- `brief.py`: Outputs a compact markdown usage cheat sheet suitable for pasting into repo `AGENTS.md` files.

---

### Component 8: Zero-Dependency Interactive Terminal UI (TUI)

#### [NEW] `src/somnus/tui/term.py`
Cross-platform terminal abstraction built without curses:
- **Windows**: Invokes `kernel32.dll` via `ctypes` to enable `ENABLE_VIRTUAL_TERMINAL_PROCESSING` and `ENABLE_PROCESSED_INPUT`. Reads raw keyboard inputs via `msvcrt.getwch()`.
- **POSIX**: Configures raw mode via `termios` and `tty`.
- Implements double-buffered screen rendering with ANSI escape codes and alternate screen buffers (`\x1b[?1049h`).

#### [NEW] `src/somnus/tui/widgets.py`
Reusable terminal components:
- Scrollable list selector with arrow navigation and search filtering.
- Radio list picker for controlled vocabulary enums.
- Text input box with cursor positioning.
- Split-screen layout container.

#### [NEW] `src/somnus/tui/app.py` & `src/somnus/commands/edit.py`
Interactive interface:
- **Doc Browser Mode** (invoked via `somnus edit` without arguments): Filterable live view of all indexed documents in the database.
- **Header Editor Mode** (invoked via `somnus edit <file>`): Interactive form to edit metadata fields with real-time validation feedback. Pressing `e` opens the markdown body in `$EDITOR` or notepad; pressing `s` formats, canonicalizes, auto-bumps revision, and writes changes atomically.

---

### Component 9: Verification Suite

#### [NEW] `tests/`
Comprehensive automated tests running under `python -m unittest`:
- `test_yamlsub.py`: Tests restricted YAML parsing, error handling on forbidden syntax, and serialization round-tripping across 60+ cases.
- `test_ids.py`: Verifies RFC 9562 UUIDv7 structure, version and variant nibbles, and URN parsing.
- `test_config.py`: Verifies precedence resolution across CLI flags, local `.somnus.toml`, and global config.
- `test_document.py`: Verifies atomic write operations, carriage return preservation, BOM handling, and strict body-byte immutability.
- `test_regions.py`: Tests region extraction, code fence isolation, nesting validation, and registry synchronization.
- `test_validate.py`: Tests multi-stage validator across all structural and semantic failure modes.
- `test_lifecycle.py`: Tests lifecycle transition validations and constraint enforcement.
- `test_store.py`: Tests SQLite schema initialization, indexing, conflict flagging, and event logging.
- `test_carriers.py`: Tests envelope extraction and insertion across Python, Shell, LaTeX, TOML, CSS, and sidecar files.
- `test_commands.py`: End-to-end integration tests for `new`, `stamp`, `check`, `status`, `bump`, `fork`, and `index`.
- `test_conformance.py`: Explicitly tests all 21 acceptance fixture criteria from SPEC §20.2.

---

## Verification Plan

### Automated Tests
Run all unit and integration tests from the workspace root:
```powershell
python -m unittest discover -s tests -v
```

Verify zero runtime external dependencies:
```powershell
python -c "import tomllib, sqlite3, argparse, dataclasses, typing, pathlib, difflib, ctypes; print('Stdlib verification passed')"
```

Verify global CLI installation via `uv`:
```powershell
uv tool install --editable .
somnus --version
```

Execute full repo validation:
```powershell
somnus check --all --level semantic
```

### Manual Verification
1. **Document Creation**:
   ```powershell
   somnus new specification "Memory Engine Architecture"
   ```
   Verify file generation, valid UUIDv7, revision 1, default fields, and proper registration in `somnus.db`.
2. **Document Stamping**:
   Create a raw markdown file without frontmatter, run `somnus stamp test.md` to review the dry-run diff, then run `somnus stamp test.md --write` and verify frontmatter insertion with identical body bytes.
3. **Database Inspection**:
   ```powershell
   somnus q --docs
   somnus q --history
   ```
   Verify that documents and recorded events are legibly formatted in tabular output.
4. **Interactive TUI**:
   ```powershell
   somnus edit
   ```
   Launch the TUI in Windows Terminal, navigate through indexed documents, open a document form, test enum field pickers, and exit cleanly.
