---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a1aff0-60c9-76b6-95b0-38b2a057b562"
  revision: 1
  title: "Where somnus-metadata stands"
  classification:
    category: "engineering"
    type: "report"
    role: "informative"
    scope: "component"
    tags: []
  lifecycle:
    status: "draft"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a1aff0-60c9-76b6-95b0-38b2a057b562"
        aspects: ["content"]
  time: {}
  names:
    slug: "where-somnus-metadata-stands"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a1aff0-60c9-76b6-95b0-38b2a057b562"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Where somnus-metadata stands

> A plain account of what the system is, which parts are finished, and the remaining publication steps for toolkit 2.2.1. Read this first if you are coming back to the project, or handing it to someone else.

**Source toolkit:** 2.2.1 (`pyproject.toml`) · **Metadata core:** 2.0.0 · **Latest verified on PyPI:** 2.2.0

## The system in one picture

This section gives the mental model; everything else in the repository is detail under it.

Somnus Metadata puts one `somnus:` header inside every file that can hold one, keeps every header in one global SQLite registry, and lets people and agents search and reason over that collection. One backend does the work. Four front ends reach it, and a separate plugin hands it to coding agents.

| Front end | Role | Shared implementation |
| --- | --- | --- |
| `somnus edit` | Interactive browser and header editor | Core validation, document IO and registry |
| `somnus ...` | Commands for people, scripts and skills | The same core backend |
| `somnus watch` | Poll roots and keep metadata and registry current | Carriers, document IO and registry |
| `somnus mcp` | Expose noninteractive CLI commands over stdio | The same commands, launched by the agent host |

The backend lives in `src/somnus/`: `carriers/` chooses header placement,
`document.py` preserves host bytes, `model/` validates the contract, and `db/`
owns SQLite storage and search. The separate `somnus-metadata-plugin` repository
registers the shared skill and MCP adapter in agent hosts.

The watcher and the MCP server are different things. The watcher runs all the time and keeps files and the registry current. The MCP server only starts when an agent host launches it, and it exists so agents can run the same commands the CLI runs.

## Where each part lives on a machine

This section answers "what did installing it actually create".

| Path | What it is | Created by |
| --- | --- | --- |
| `~/.venvs/global/bin/somnus` | The installed command (alias `somnus-metadata`) | `pip install somnus-metadata` in that virtual environment |
| `~/.somnus/somnus.db` | The global registry (SQLite) | `somnus init --root DIR` |
| `~/.somnus/config.toml` | Global settings: defaults, excludes, `[carriers]`, `[watch]` | `somnus init` |
| `~/.somnus/watch.json` | The watcher's heartbeat, read by `somnus daemon status` and the TUI | the running watcher |
| `~/.config/systemd/user/somnus-watch.service` | The Linux user service that keeps the watcher running | `somnus daemon install` |
| `.somnus.toml` in a project | Per-project overrides of the global settings | you, by hand |

`SOMNUS_HOME` moves the whole `~/.somnus` directory elsewhere. On macOS the service is a launchd agent, and on Windows a logon task; `somnus daemon install --dry-run` prints exactly what it would write.

## What changed in 2.2.0

This section is the release in one place. The design record is decision D20 in [DECISIONS.md](../DECISIONS.md#d20--universal-embedded-carriers-and-the-always-on-watcher).

| Area | Before (2.1.1) | Now (2.2.0) | Where it is specified |
| --- | --- | --- | --- |
| Which files get an inline header | Chosen by extension only, so `CODEOWNERS`, `Dockerfile`, `Makefile`, `.gitignore`, shebang scripts, and notebooks fell back to `<file>.somnus.yaml` sidecars | Chosen by filename, then pattern, then extension, then shebang. Notebooks use `metadata.somnus`. Plain `.json` can opt in to a leading `"$somnus"` member | [SPEC.md section 17](../SPEC.md#17-carriers) |
| Existing sidecars | Stayed sidecars | Still valid; `somnus migrate --inline PATH --write` moves them into their files (same ID, revision + 1) | [SPEC.md section 17.6](../SPEC.md#176-sidecars) |
| Keeping the registry current | Only when someone ran `somnus index` | `somnus watch` runs continuously; `somnus daemon install` makes it a user service | [SPEC.md section 18.5](../SPEC.md#185-the-watcher-d20) |
| Editing a managed file | Left an open revision conflict until someone ran `somnus bump` | The watcher records the edit as a new revision after the file is quiet for 10 seconds (`[watch] revise = "auto"`) | [SPEC.md section 18.5](../SPEC.md#185-the-watcher-d20) |
| New files | Invisible until stamped by hand | The watcher stamps new files that can hold an inline header; it never creates sidecars unless `[watch] stamp = "all"` | [SPEC.md section 18.5](../SPEC.md#185-the-watcher-d20) |
| Agents | 16 MCP tools | 17: adds `daemon`, so an agent can read the watcher's state. `watch` itself is not a tool | [SPEC.md section 20](../SPEC.md#20-cli-contract) |

Sidecars remain only for files with no place for a header: plain text, CSV, binaries, and strict JSON by default. Strict JSON stays a sidecar by default because adding a member changes the data that strict consumers validate; set `[carriers] json = "key"` to change that globally.

## What is verified

This section lists the checks that were run on this tree and what each one proves.

| Check | Command | Result on this tree |
| --- | --- | --- |
| Unit and conformance tests | `PYTHONPATH=src python -m unittest discover -s tests` | 579 tests pass, including `tests/test_routing.py` and `tests/test_watch.py` |
| Type check | `python -m mypy` | No issues in 56 source files |
| Import layering | `lint-imports --config .importlinter` | 6 contracts kept |
| Coverage gate | `coverage run -m unittest discover -s tests` then `coverage report` | 87 percent (gate is 85) |
| Hooks | `pre-commit run --all-files` | All hooks pass |
| Installed wheel, end to end | `python tests/acceptance/installed_package_acceptance.py` | 77 of 77 checks pass, including the new carrier and watcher checks |
| Spec self-check | `python -m somnus.cli check SPEC.md DECISIONS.md --level semantic` | 0 errors, 0 warnings |

Hosted CI passes on Linux, macOS and Windows. Physical service installation on the laptop and a physical Windows console have not been exercised in this cloud session.

## Current release and remaining publication

The D20 backend and plugin 1.3.0 are merged. D20 is ratified in DECISIONS.md.
Toolkit 2.2.0 is published on PyPI. The supplied revision correction targets
2.2.1 because published versions cannot be overwritten. Metadata core stays
2.0.0. The plugin remains a separate private repository.

The correction restores the isolated heartbeat module, missing filename mappings,
inline metadata in five repository configuration files, and this handoff.
The migration payload mapper is split by the SPEC section 22 field families;
unknown legacy values remain in the migration extension.

Finish publication from an environment with the authorized PyPI publisher:

1. Check out current `main` and run the gates in the release runbook.
2. Build and inspect a wheel and source archive for **2.2.1**.
3. Run strict Twine checks and upload those exact artifacts using the existing
   credential store. Never put a token into source, chat or command arguments.
4. Verify public artifact hashes and a fresh installation from PyPI.
5. Tag the accepted commit as `v2.2.1`; the existing tag workflow creates a
   GitHub Release, but does not publish to PyPI.

The cloud workspace has no PyPI publishing credentials, and the connected laptop
is offline. **2.2.1 is not yet published.** The authoritative procedure is
[runbooks/package-release.md](../runbooks/package-release.md).

A source merge or package upload does not install or enable the native plugin,
start a global watcher, or migrate unrelated project roots. Those machine changes
require access to the target machine. Use `somnus daemon install --dry-run` to
inspect a service plan and `somnus migrate --inline PATH` to preview migration.

## Where to go next

This section routes to the detailed documents.

- [README.md](../README.md): install, quick start, and running the watcher.
- [SPEC.md](../SPEC.md): the normative contract; sections 17, 18.5, and 20 cover this release.
- [docs/USAGE_GUIDE.md](USAGE_GUIDE.md): the operator and agent guide, including the carriers table and the watcher.
- [DECISIONS.md](../DECISIONS.md): why each design choice was made.
- [HANDOFF.md](../HANDOFF.md): the running engineering log.
