# Configuration

Configuration is TOML, read with the stdlib `tomllib`, and resolved in layers by `src/somnus/config.py`. It supplies the actor name recorded in registry events, the default header values that `somnus new`, `stamp`, `fork`, and `migrate` write, and the roots and exclusions used by indexing.

## Precedence

From highest to lowest (SPEC section 20, DECISIONS.md D6):

1. CLI flag (`--actor NAME`)
2. The nearest `.somnus.toml` at or above the starting directory
3. `$SOMNUS_HOME/config.toml`
4. Built-in defaults (`BUILTIN` in `src/somnus/config.py`)

`config.load(start, actor)` applies the global file first and the local file second, so local values override global ones. Commands call it with the current working directory (`Ctx.cfg` in `src/somnus/commands/_common.py`), which means the `.somnus.toml` that applies depends on where `somnus` is run, not on which file is being processed.

## `SOMNUS_HOME`

`somnus_home()` returns `$SOMNUS_HOME` (with `~` expanded and the path resolved) or `~/.somnus` when the variable is unset. Two files live there:

| File | Purpose |
| --- | --- |
| `config.toml` | Global configuration, written from `CONFIG_TEMPLATE` by `somnus init` if it does not exist |
| `somnus.db` | The registry (`Config.db_path`) |

Tests set `SOMNUS_HOME` to a temp directory so they never touch the real registry; see [testing](../how-to-contribute/testing.md).

## `.somnus.toml` discovery

`find_local_config(start)` resolves `start`, moves to its parent if it is a file, then checks that directory and each ancestor for a file named `.somnus.toml`. The first match wins; there is no merging between multiple local files.

## Keys

Only three top-level keys are allowed: `actor`, `[defaults]`, and `[index]`. Anything else is an error.

### Top level

| Key | Type | Built-in default | Rule |
| --- | --- | --- | --- |
| `actor` | string | `"operator"` | Must be a nonempty string; recorded in `events.actor` |

### `[defaults]`

These become the corresponding header fields of new and stamped documents.

| Key | Type | Built-in default | Allowed values (`src/somnus/model/vocab.py`) |
| --- | --- | --- | --- |
| `category` | string | `"engineering"` | `research`, `engineering`, `operations`, `governance`, `context`, `archive` |
| `role` | string | `"normative"` | `normative`, `informative`, `working`, `exploratory`, `historical` |
| `scope` | string | `"component"` | `ecosystem`, `fleet`, `repository`, `subsystem`, `module`, `component`, `artifact` |
| `visibility` | string | `"internal"` | `operator-only`, `internal`, `public` |
| `allowed_uses` | array of strings | `["archive", "search", "reason"]` | Each of `archive`, `search`, `reason`, `quote`, `export`, `training`, `execute` |
| `standing` | string | `"candidate"` | `unasserted`, `candidate`, `accepted`, `retired`, `rejected` |
| `disposition` | string | `"candidate"` | `candidate`, `archive-only`, `excluded`, `canonical-candidate` |
| `body_role` | string | `"specification"` | `narrative`, `specification`, `instruction`, `configuration`, `source`, `conversation`, `dataset`, `mixed` |

`standing = "accepted"` passes config validation but is refused when a header is built (`new_payload` in `src/somnus/commands/_common.py`), because a default cannot supply the acceptance record that `accepted` requires (D6, D9).

Layers merge per key: a local file that sets only `role` keeps every other default from the global file or the built-ins.

### `[index]`

| Key | Type | Built-in default | Merge behavior |
| --- | --- | --- | --- |
| `roots` | array of strings | `["."]` in `BUILTIN`, but see below | A nonempty list replaces the roots; each entry is resolved relative to the directory containing the config file that set it. An empty list is ignored. |
| `exclude` | array of strings | `["archive/**", ".git/**", "node_modules/**", "**/__pycache__/**"]` | Replaces the whole list; patterns are not appended |

Roots start as the starting directory (or its parent if `start` is a file), not as the `"."` in `BUILTIN`. A config file with `roots = []`, which is what `CONFIG_TEMPLATE` writes, leaves that default in place. Roots registered with `somnus init --root DIR` are stored in the registry's `roots` table separately from this setting.

Exclude patterns are POSIX-style globs matched against paths relative to a root by `glob_regex` in `src/somnus/db/store.py`: `**/` matches zero or more directories, `**` matches anything, `*` and `?` do not cross `/`. `.git`, `.hg`, and `.svn` directories are always pruned during walks regardless of configuration.

### Rollout safeguards

The latest top sections of `PLAN.md` and `HANDOFF.md` record the release/install commission complete and mark the bulk-adoption frontier superseded (operator correction, 2026-11-01). Five roots are registered; the last recorded scan in `docs/USAGE_GUIDE.md` section 9 reports 2,659 managed hosts, 21,554 unmanaged hosts, and no invalid/missing hosts or conflicts, superseding the earlier 1,064 / 23,148 checkpoint and older `CONTEXT.md` snapshots. This is recorded operator state, not a fresh inspection of this runner. Earlier nested-registration consolidation is complete; do not create duplicate observations by registering nested repositories again.

Configured roots and registered roots are different: `src/somnus/commands/init.py` registers directories in SQLite, and `src/somnus/commands/index.py` prefers those registrations when no explicit roots are passed. The template's `roots = []` is not evidence that the registry has no roots. Inspect both surfaces before changes; do not re-register already completed parents or nested repositories without checking overlap and reconciliation ownership. Back up the registry before authorized consolidation.

Before an authorized bulk adoption, configure excludes for generated/dependency directories and deliberate file exclusions. An `exclude` override replaces the list, so retain required defaults and use root-relative globs that cover nested directories. The handoff also preserves frozen research and `archive/`. Configuration does not adopt a file: `somnus stamp` takes explicit file paths, and `somnus index` reconciles managed files. See [Adopting files](../features/adopting-files.md) and [Querying](../features/querying.md).

Toolkit 2.1.1 repairs the earlier embedded-carrier-only count: `Store.scan` in `src/somnus/db/store.py` reports hosts requiring a new sidecar without reading their payloads. Exclusions still apply before discovery. Its complete `ScanReport.unmanaged_paths` list includes all discovered unmanaged host types; the CLI prints only ten examples. The 23,148 unmanaged checkpoint replaced earlier inventories and is in turn superseded by the last recorded 21,554. Generated dependencies, including the operator's pnpm store, credentials, archives, frozen research, and live Somnus-MCP data remain deliberately excluded (`PLAN.md`). Historical `mash_merge_archive` and `old-non-applicable` trees remain untouched. The preservation pass also excludes generated hosting state, private account-derived exports, runtime objects, test-run output, and machine-owned run records. The 4,054-host reduction from 27,202 did not establish adoption: the managed count remained 1,064 at that checkpoint. Bulk adoption was later stopped by the operator (2026-11-01); the remaining unmanaged hosts are preserved, not unfinished work.

`PLAN.md` records an isolated protected-source fixture whose native-generated standard sidecar passed semantic validation, registry observation, and literal host-byte preservation. It does not record completed bulk protected-host adoption or a new configuration option. Keep that fixture proof separate from corpus completion. Prior known-topic Droid/Codex hits did not establish complete adoption; skill/plugin alignment and both installed-skill reads are recorded complete for Codex and Factory Droid after the clean reinstall, and expanded-corpus searches apply only if the operator resumes adoption.

## Validation errors

`_check` in `src/somnus/config.py` raises `ConfigError` (a `ValueError`) with the file path prefixed. The CLI reports it as an `E_IO` diagnostic with exit code 2.

| Message | Cause |
| --- | --- |
| `unknown keys [...]` | A top-level key other than `actor`, `defaults`, `index` |
| `actor must be a nonempty string` | `actor` is empty, whitespace, or not a string |
| `[defaults] must be a table` / `[index] must be a table` | The section is not a TOML table |
| `defaults.allowed_uses must list values from (...)` | Not a list, or a value outside the vocabulary |
| `defaults.KEY = 'VALUE' is not one of (...)` | Enum value outside the vocabulary |
| `unknown key defaults.KEY` | A defaults key not in the table above |
| `unknown key index.KEY` | An index key other than `roots` or `exclude` |
| `index.KEY must be an array of strings` | `roots` or `exclude` is not a list of strings |
| TOML parse error text | The file is not valid TOML |
| OS error text | The file cannot be opened |

## `CONFIG_TEMPLATE`

`somnus init` writes this to `$SOMNUS_HOME/config.toml` when the file is missing:

```toml
# Somnus global configuration (precedence: CLI flag > .somnus.toml > this file > built-ins)
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
roots = []
exclude = ["archive/**", ".git/**", "node_modules/**", "**/__pycache__/**"]
```

## The resolved `Config`

`config.load` returns a `Config` dataclass with `actor`, `defaults` (merged dict), `roots` (list of resolved `Path`), `exclude` (list of glob strings), `home` (the `SOMNUS_HOME` path), `sources` (the config files that contributed, in application order), and the derived property `db_path` (`home / "somnus.db"`).
