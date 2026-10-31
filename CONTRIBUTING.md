# Contributing to `somnus-metadata`

`somnus-metadata` is the normative specification (`SPEC.md`) and stdlib-only Python reference implementation (`src/somnus/`) for `somnus://metadata/core/2.0.0`. Every contribution must preserve contract fidelity, host-byte safety, and zero runtime dependencies.

## Table of Contents

1. [Authority and Normative Boundaries](#1-authority-and-normative-boundaries)
2. [Environment Setup from a Fresh Clone](#2-environment-setup-from-a-fresh-clone)
3. [Verification Gate](#3-verification-gate)
4. [Naming and Structural Conventions](#4-naming-and-structural-conventions)
5. [Architecture and Layer Invariants](#5-architecture-and-layer-invariants)
6. [Rules for Somnus-Managed Files](#6-rules-for-somnus-managed-files)
7. [Pull Request and Review Workflow](#7-pull-request-and-review-workflow)
8. [Dependency and Minimum Release Age Policy](#8-dependency-and-minimum-release-age-policy)

---

## 1. Authority and Normative Boundaries

- **`SPEC.md` is normative.** If implementation and `SPEC.md` disagree, treat the discrepancy as an implementation defect. Do not alter the normative contract without an explicit ratified decision and a version update under `SPEC.md` §23.
- **`DECISIONS.md` records ratified rationale D1–D19.** Never silently revise an existing decision; material changes require adding a new ratified decision record and bumping the document revision (`somnus bump`).
- **`tests/test_conformance.py` is the executable 21-fixture acceptance suite** corresponding to `SPEC.md` §21.
- **`Somnus Markdown Metadata Standard Research.md` is frozen historical evidence** and must never be modified or overwritten.
- **`archive/` is historical and non-normative (D15).** Code under `src/` must never import from `archive/`.

---

## 2. Environment Setup from a Fresh Clone

Requires **Python 3.11 or newer** (`pyproject.toml` `requires-python = ">=3.11"`). Runtime dependencies are strictly empty (Python standard library only).

```sh
git clone https://github.com/calisweetleaf/somnus-metadata.git
cd somnus-metadata

# Create and activate a virtual environment (required on PEP 668 Linux hosts
# where system pip refuses installs with externally-managed-environment),
# then install in editable mode with dev tooling (mypy):
python3 -m venv .venv          # or: uv venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"   # or: uv pip install -e ".[dev]"

# Verify CLI execution directly from the source tree
PYTHONPATH=src python -m somnus.cli --version
```

If you use `uv`, you can also install the editable CLI tool via:

```sh
uv tool install --editable .
somnus --version
```

---

## 3. Verification Gate

Every change must pass all three checks before opening or merging a pull request.

From the repository root on POSIX (exact commands from `AGENTS.md`):

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
python -m mypy   # dev tool; install with: pip install "mypy>=1.9"
```

On PEP 668 Linux hosts (`EXTERNALLY-MANAGED`), run `pip install "mypy>=1.9"` (or `pip install -e ".[dev]"`) inside an activated virtual environment (`.venv`), or install `mypy` as an isolated tool (`uv tool install mypy` / `pipx install mypy`).

PowerShell equivalent for source checkout execution:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
```

### Exit Code Contract (`SPEC.md` §19.3, `src/somnus/output.py:9-11`)

- `0` (`EXIT_OK`): Success with no errors.
- `1` (`EXIT_INVALID`): Validation errors, refused operations, or open registry conflicts.
- `2` (`EXIT_USAGE`): CLI usage, configuration, I/O, or environment errors.

### Installed-package acceptance (required before a release)

Source-checkout tests prove the implementation; they do not prove the distribution.
Before any release, run the installed-package acceptance harness from the repository
root:

```sh
python tests/acceptance/installed_package_acceptance.py
python tests/acceptance/installed_package_acceptance.py --keep   # keep the temp tree
```

It builds the wheel from a temporary copy of `pyproject.toml`, `README.md`, and
`src/somnus` (so the checkout is never written to), installs it into an isolated
virtual environment, and drives the installed `somnus` entry point against a fresh
`$SOMNUS_HOME`, real files, a real SQLite registry, a real stdio MCP client, and a
real POSIX PTY. It never imports `somnus` from the source tree and never puts the
checkout on `sys.path`.

- **Prerequisites:** Python 3.11 or newer; a wheel builder (`uv build`, `python -m build`, or `python -m pip wheel`, tried in that order); a venv creator (`uv venv` or `python -m venv`); POSIX with `pty`/`termios` for the terminal checks.
- **Isolation:** everything lives under one `tempfile.mkdtemp()` tree. An inherited `SOMNUS_HOME` is removed and replaced, so the operator's real registry is never touched.
- **Cleanup:** the harness owns the tree and deletes it on exit unless `--keep` is passed, which prints its path.
- **Artifacts:** `result.json`, `result.md`, and `result.log` under `<tmp>/runs/<UTC timestamp>/`.
- **Exit codes:** `0` all checks passed; `1` at least one check failed; `2` harness error (missing prerequisite, build/install failure, or a required check that could not run on this platform). It is not collected by `python -m unittest discover -s tests`, and explicit invocation never silently skips.

The Windows `msvcrt`/`ctypes` terminal paths and the hosted CI workflows are not
exercised by this harness and must be reported as NOT RUN unless a Windows host or
an authorized landing actually ran them.

---

## 4. Naming and Structural Conventions

All new or modified Python code under `src/somnus/` and `tests/` must follow the observed codebase conventions:

### 4.1 Modules and Files

- **Package & Module Names:** Single lowercase words, unseparated or underscored only when required for clarity: `yamlsub.py`, `sidecar.py`, `linecomment.py`, `blockcomment.py`, `ids.py`, `infer.py`, `regions.py`, `document.py`, `config.py`, `output.py`, `cli.py`, `mcp.py`.
- **Private Modules:** Leading underscore for internal shared modules: `src/somnus/commands/_common.py`.
- **Command Modules (`src/somnus/commands/`):** One module per CLI subcommand, named after the CLI verb (`init.py`, `new.py`, `stamp.py`, `check.py`, `index.py`, `ls.py`, `status.py`, `bump.py`, `fork.py`, `regions.py`, `migrate.py`, `stale.py`, `schema.py`, `brief.py`, `edit.py`, `mcp.py`). Two commands map via `_MODULES = {"q": "query", "set": "set_fields"}` in `src/somnus/cli.py:135` so `set_fields.py` (D16) avoids shadowing Python's built-in `set` and `query.py` backs `somnus q`.
- **Test Modules (`tests/`):** Named `test_<module>.py` and executed with the standard library `unittest` runner (`python -m unittest discover -s tests`). No `pytest` dependency is used.

### 4.2 Classes

- **General Classes:** `PascalCase` nouns.
  - **Exceptions:** End in `Error` with a base class matching semantics: `SomnusError(Exception)` (`output.py:34`), `CarrierError(ValueError)` (`carriers/__init__.py:84`), `ConfigError(ValueError)` (`config.py:63`), `YAMLError(ValueError)` (`yamlsub.py:31`), `TerminalError(OSError)` (`tui/term.py:46`), `MigrationError(Exception)` (`commands/migrate.py:34`), `ToolError(Exception)` and `ParamsError(Exception)` (`mcp.py:41,45`).
  - **Dataclasses and Value Types:** Plain `PascalCase` nouns: `Diagnostic`, `Envelope`, `Issue`, `Extraction`, `Splice`, `Inference`, `Config`, `Document`, `RegionRange`, `MarkerScan`, `ArtifactFacts`, `ScanReport`, `Store`, `Ctx`.
  - **Schema Descriptor Nodes (`src/somnus/model/schema.py`):** Concise `PascalCase` nouns (`Str`, `Int`, `Num`, `Bool`, `AnyValue`, `Arr`, `Field`, `Obj`, `MapOf`, `Tagged`, and `Union_` with a trailing underscore to avoid colliding with `typing.Union`).
  - **Private / Internal Classes:** Leading underscore `PascalCase`: `_Line`, `_Flow`, `_Parser`, `_Dumper` (`yamlsub.py`), `_Run` (`model/validate.py`), `_Exporter` (`model/jsonschema_export.py`), `_WindowsConsole`, `_PosixTty` (`tui/term.py`).
  - **Protocols:** `Carrier(Protocol)` (`carriers/__init__.py:67`).
  - **Test Classes (`tests/`):** Suite classes use `Test<Subject>(unittest.TestCase)` (`TestUUID7`, `TestPairing`, `TestConformance`, `TestRoundTrip`); shared test harnesses end in `TestCase` or `Case` (`DocTestCase`, `ConfigTestCase`, `StoreTestCase`, `CliCase`, `RegistryCase`); test doubles use `Fake<Subject>` (`FakeScreen`, `FakeCtx`, `FakeRunner`).

### 4.3 Functions and Methods

- **Public Functions/Methods:** `snake_case` verbs or clear noun phrases (`validate`, `render`, `extract`, `apply_transition`, `check_transition`, `bump_revision`, `scan_markers`, `sync_registry`, `markdown_code_mask`, `atomic_write`, `canonical_yaml`, `connect_readonly`, `run_query`, `somnus_home`, `find_local_config`, `build_parser`).
- **Command Entry Contract:** Every command module in `src/somnus/commands/` must expose `run(args, ctx: Ctx) -> int` returning an exit code (`EXIT_OK`, `EXIT_INVALID`, or `EXIT_USAGE`).
- **Predicates and Lookups:** Prefix with `is_`, `for_`, `sidecar_`, or `host_` (`is_local_id`, `is_example_urn`, `is_sidecar`, `is_sidecar_path`, `sidecar_for`, `host_for`, `for_path`).
- **Private Helpers:** Prefix with a single leading underscore (`_split`, `_apply`, `_verify_preserved`, `_read`, `_decode`, `_parse_into`, `_registry`, `_open_conflict`, `_resolve_rows`, `_check`).

### 4.4 Constants

- **Constants:** `UPPER_SNAKE_CASE`.
  - **Exit Codes (`src/somnus/output.py`):** `EXIT_OK = 0`, `EXIT_INVALID = 1`, `EXIT_USAGE = 2`.
  - **Package Schema & Version Constants (`src/somnus/__init__.py`):** `CORE_SCHEMA`, `SPEC_PROFILE`, `BENCHMARK_PROFILE`, `MIGRATION_EXTENSION`, `DB_USER_VERSION`.
  - **Controlled Vocabularies (`src/somnus/model/vocab.py`):** Plural `UPPER_SNAKE_CASE` tuples/dicts (`CATEGORIES`, `TYPES`, `ROLES`, `SCOPES`, `STATUSES`, `STANDINGS`, `VISIBILITIES`, `RELATION_PREDICATES`, `LEVELS`).
  - **Regular Expressions (Module-Scoped Conventions):**
    - In `src/somnus/ids.py`: compiled regex constants end in `_RE` (`ARTIFACT_URN_RE`, `SOMNUS_URN_RE`, `LEGACY_DOC_RE`, `LOCAL_ID_RE`, `SLUG_RE`, `EXT_REF_RE`).
    - In `src/somnus/model/schema.py`: regex pattern strings end in `_PATTERN` (`TIMESTAMP_PATTERN`, `DATE_PATTERN`, `LOCAL_PATTERN`, `KEBAB_PATTERN`, `ID_PATTERN`, `SOMNUS_URN_PATTERN`, `REF_PATTERN`, `LANGUAGE_PATTERN`, `MEDIA_TYPE_PATTERN`, `OWNER_PATTERN`, `PROFILE_KEY_PATTERN`).
  - **Module Singletons:** Uppercase constants (`SIDECAR` in `carriers/sidecar.py`, `CSS` and `XML` in `carriers/blockcomment.py`, `BRIEF` in `commands/brief.py`, `FIELDS` and `READONLY` in `tui/form.py`).

### 4.5 Diagnostic Codes (`SPEC.md` §19.2, D14)

- **Errors:** Prefix with `E_` followed by an uppercase domain identifier:
  `E_ENVELOPE`, `E_HOST`, `E_YAML`, `E_SCHEMA`, `E_REFERENCE`, `E_REGION`, `E_REVISION`, `E_AUTHORITY`, `E_TEMPORAL`, `E_GRAPH`, `E_EXTRACTION`, `E_POLICY`, `E_LIFECYCLE`, `E_IO`.
- **Warnings:** Prefix with `W_` followed by an uppercase domain/sub-code identifier:
  `W_PREDICATE`, `W_REGION_SPACING`, `W_REGION_UNREGISTERED`, `W_UNMANAGED`. The
  warning registry is closed; near-duplicate titles are a `somnus stale` advisory
  row, not a warning code (D18).
- **Separation of Severity:** Severity (`"error"` or `"warning"`) is stored on `Diagnostic.severity` and never parsed out of the string code at render time.

---

## 5. Architecture and Layer Invariants

- **Stdlib-Only Leaves:** `output.py`, `ids.py`, `yamlsub.py`, `infer.py`, `model/vocab.py`, `model/lifecycle.py`, `carriers/__init__.py`, and `tui/widgets.py` have zero top-level imports from other `somnus` modules.
- **Carrier Isolation:** `src/somnus/carriers/` never imports `model/`, `db/`, `commands/`, `tui/`, or `document.py`.
- **Model Isolation:** `src/somnus/model/` never imports `db/`, `commands/`, `tui/`, `cli.py`, `mcp.py`, or `config.py`.
- **Registry Isolation:** `src/somnus/db/` never imports `commands/`, `tui/`, `cli.py`, or `mcp.py`.
- **MCP Adapter Isolation (D17):** `src/somnus/mcp.py` generates tool schemas from `somnus.cli.build_parser` and invokes CLI commands in child processes; it never imports `db/` or `tui/`.
- **Archive Isolation (D15):** Nothing under `src/` may import from `archive/` (enforced in CI and `.importlinter`).

---

## 6. Rules for Somnus-Managed Files

When editing or adding Somnus-managed artifacts in this repository (`SPEC.md`, `DECISIONS.md`, or fixtures):

1. **Never invent metadata:** Do not fabricate UUIDs, dates (`created_at`, `updated_at`, `reviewed_at`), actors, licenses, measurements, evidence, or acceptance records (`DECISIONS.md` D6, D10).
2. **Never hand-edit `id`:** Content changes to indexed artifacts require a revision increment via `somnus bump` (or `somnus set` / `somnus status`). Lifecycle changes must go through `somnus status`.
3. **Use `somnus set` for header fields (D16):** Editable header fields (`title`, `summary`, `purpose`, `classification.category|type|role|scope|tags`, `access.visibility`, `ingestion.disposition`) should be modified via `somnus set PATH FIELD=VALUE...`. Tool-specific experimental data belongs under `extensions.<owner>`.
4. **Preserve host bytes (`E_HOST`):** Any write to a host file must preserve all bytes outside the metadata envelope (`src/somnus/document.py:156-169`).
5. **No JSON in registry or CLI output (D4, D17):** Registry tables and CLI/MCP tool outputs use aligned plain text or TSV. JSON is permitted only for MCP JSON-RPC transport framing (`somnus mcp`), `somnus schema --json-schema`, and JSON-pointer selectors into JSON host files.

---

## 7. Pull Request and Review Workflow

1. **Branching and Git Policy:**
   - The repository uses `pull.ff=only` for local pulls. Inspect `git status` and fetch before rebasing or fast-forwarding.
   - Pre-commit hooks are configured in `.pre-commit-config.yaml` (`ruff` and `mypy`, plus file hygiene hooks that intentionally skip `.md`, `archive/`, `archives/`, and `tests/` to preserve byte-exact fixtures). Run `pre-commit run --all-files` if `pre-commit` is installed.
2. **OneDrive / Surgeon Workspace Note:**
   - When working in a OneDrive-synced checkout with Surgeon, multi-file transactions (`multi_edit`, `prepare`/`commit`) fail with `WinError 5`. Perform one atomic single-file edit (`op=edit` or `op=create`) per call.
3. **Pull Request Requirements (`.github/pull_request_template.md`):**
   - Include the exact output of the three verification commands in the PR description.
   - Explicitly declare whether the change affects `SPEC.md` or `DECISIONS.md`.
   - Add unit or conformance tests in `tests/test_*.py` covering any new behavior or bug fix.

---

## 8. Dependency and Minimum Release Age Policy

### 8.1 Zero Runtime Dependencies (Normative Rule)

`pyproject.toml` `[project] dependencies = []` **must remain empty**. The `somnus` package relies exclusively on the Python 3.11+ standard library. This invariant is enforced automatically on every push and pull request by the `policy` job in `.github/workflows/ci.yml`. Any pull request that adds a runtime package dependency will be rejected.

### 8.2 Minimum Release Age Policy (7-Day Cooling-Off Rule)

To protect against supply-chain compromise, malicious package publication, and regressions in newly published upstream versions:

- **7-Day Minimum Release Age:** All development/build dependency updates (`pyproject.toml` `[build-system]` `setuptools`, `[project.optional-dependencies] dev` `mypy`, `.pre-commit-config.yaml` hook revisions) and GitHub Actions workflow dependency updates (`.github/workflows/*.yml`, `.github/dependabot.yml` PRs) **must wait at least 7 calendar days (168 hours) after the upstream version's official release timestamp before being merged**.
- **Exception for Critical Security Patches:** An upstream release younger than 7 days may be merged only if it patches a disclosed vulnerability affecting this repository's CI/dev surface, and only after manual diff inspection and explicit maintainer sign-off recorded in the pull request.
