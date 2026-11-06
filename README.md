---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a67-78f9-7428-ad42-b95c245a14e5"
  revision: 3
  title: "somnus-metadata"
  classification:
    category: "context"
    type: "index"
    role: "informative"
    scope: "component"
    tags: []
  lifecycle:
    status: "draft"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a19a67-78f9-7428-ad42-b95c245a14e5"
        aspects: ["content"]
  time:
    updated_at: "2026-11-06T06:11:45+00:00"
  names:
    slug: "somnus-metadata"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19a67-78f9-7428-ad42-b95c245a14e5"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# somnus-metadata

The Somnus metadata standard (core `somnus://metadata/core/2.0.0`) and its stdlib-only toolkit.

Every managed file carries exactly one `somnus:` header, inside the file wherever the format allows it.
Markdown uses frontmatter or a hidden comment envelope. Code, config, and build files use a comment
envelope, routed by filename (`Dockerfile`, `Makefile`, `CODEOWNERS`, `.gitignore`, `requirements.txt`,
...), extension, or shebang. Notebooks carry it in `metadata.somnus`; JSON-with-comments files
(`.jsonc`, `tsconfig.json`) use `//` lines; plain `.json` can opt in to a leading `"$somnus"` member.
Only formats with no place for it (plain text, CSV, binaries, strict JSON by default) use a
`<file>.somnus.yaml` sidecar. A global SQLite registry (`~/.somnus/somnus.db`) indexes identity,
revisions, relations, claims, conflicts, and a full-text index of managed file content. It contains
no JSON.

- Operator & agent usage guide: [docs/USAGE_GUIDE.md](https://github.com/calisweetleaf/somnus-metadata/blob/main/docs/USAGE_GUIDE.md)
- Global `AGENTS.md` snippet for agents: [docs/AGENTS.appendix.md](https://github.com/calisweetleaf/somnus-metadata/blob/main/docs/AGENTS.appendix.md)
- Normative specification: [SPEC.md](SPEC.md)
- Ratified decisions: [DECISIONS.md](DECISIONS.md)
- Historical material (not normative): [archive/](archive/README.md)

## Install

Requires Python 3.11+ and has no third-party dependencies.

Install from PyPI with `pip` into a virtual environment that is on your `PATH`:

```sh
python3 -m venv ~/.venvs/global
~/.venvs/global/bin/pip install -U somnus-metadata
somnus --version
```

On PEP 668 Linux distributions (Ubuntu 23.04+), the system `pip` refuses installs outside a virtual environment with `externally-managed-environment`, so use a venv. `uv tool install somnus-metadata` and `pipx install somnus-metadata` also work; keep only one install so an older copy cannot shadow the newer one. Check with `which -a somnus` and `somnus --version`. The [usage guide](https://github.com/calisweetleaf/somnus-metadata/blob/main/docs/USAGE_GUIDE.md#2-installation-on-ubuntu--linux) covers `PATH` setup for agent hosts.

The PyPI distribution is **somnus-metadata**; the commands are **somnus** and its alias **somnus-metadata**, and the Python import is `somnus`. Do not install the unrelated PyPI distribution named `somnus` into the same environment: it owns the same command and import names.

For editable development from a source checkout, use `pip install -e .` in a virtual environment.
The installed tool works outside this repository; register the project roots you
want to manage with `somnus init --root /path/to/project`.

Somnus Metadata **2.2.0** implements metadata core **2.0.0** and registry schema **2** (with `somnus q --text` full-text search, the `somnus-metadata` command alias, universal embedded carriers, and the always-on `somnus watch` service).
`somnus index` reports unmanaged hosts of every file type, including files that need a new sidecar, without loading unmanaged binary content.
The material under `archive/v2-proposal/` is historical, not the active release.
The backend, the terminal UI, the CLI, the always-on watcher, and the stdio MCP adapter share one core. A distributable
coding-agent plugin is not included in this release.

## Quick start

```
somnus init --root .                 # create ~/.somnus, config.toml, registry; register this root
somnus new specification "My Spec"   # scaffold a conformant Markdown artifact
somnus check my-spec.md --level semantic
somnus stamp notes.py                # dry-run diff; add --write to apply
somnus index                         # reconcile roots into the registry
somnus ls
somnus q --conflicts
somnus q --text "host bytes"         # full-text search; every word must match
somnus set my-spec.md "classification.tags=memory, design"   # header edit, new revision
somnus edit                          # terminal UI
```

`somnus brief` prints an agent cheat sheet suitable for pasting into a repository's `AGENTS.md`.

## Run it 24/7

```
somnus init --root ~/projects/somnus   # register every root you want managed
somnus daemon install                  # systemd user unit / launchd agent / Windows logon task
somnus daemon status                   # heartbeat: running, roots, stamped, revised, errors
loginctl enable-linger "$USER"         # Linux: keep it running while logged out
```

The watcher polls every registered root, stamps new files that can carry an embedded header once
they have been quiet for `settle` seconds, records in-place edits as new revisions, and keeps the
registry and full-text index current. It never creates sidecars unless `[watch] stamp = "all"`, and
only adopts files that existed before it started with `--adopt`. Run it in a terminal with
`somnus watch`, or one pass with `somnus watch --once`. Settings live under `[watch]` and
`[carriers]` in `config.toml` (SPEC §18.5).

Upgrading from 2.1: headers that older releases put in sidecars for hosts that now have a carrier
move inline with `somnus migrate --inline PATH` (dry run) and `--write`.

## MCP server

`somnus mcp` serves non-interactive commands (excluding `edit`, `watch`, and `mcp` itself)
as Model Context Protocol tools over stdio. It is how agents reach the CLI; it is not the watcher.
Agents read the watcher's state with the `daemon` tool (`action: status`).
Each tool returns the command's text output. Register it with any MCP client by command:

```
somnus mcp                           # optional: somnus --actor NAME mcp
```

Exit codes: `0` ok, `1` validation errors, refusals, or conflicts, `2` usage or I/O errors.

## Tests

```
PYTHONPATH=src python -m unittest discover -s tests
```
