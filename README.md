# somnus-metadata

The Somnus metadata standard (core `somnus://metadata/core/2.0.0`) and its stdlib-only toolkit.

Every managed file carries exactly one `somnus:` header. Markdown files use frontmatter or a hidden
comment envelope. Code and config files use a comment envelope. All other files use a
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

Somnus Metadata **2.1.0** implements metadata core **2.0.0** and registry schema **2** (adding `somnus q --text` full-text search and the `somnus-metadata` command alias).
The material under `archive/v2-proposal/` is historical, not the active release.
The CLI, terminal UI and stdio MCP adapter share one backend. A distributable
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

## MCP server

`somnus mcp` serves non-interactive commands (excluding `edit` and `mcp` itself)
as Model Context Protocol tools over stdio.
Each tool returns the command's text output. Register it with any MCP client by command:

```
somnus mcp                           # optional: somnus --actor NAME mcp
```

Exit codes: `0` ok, `1` validation errors, refusals, or conflicts, `2` usage or I/O errors.

## Tests

```
PYTHONPATH=src python -m unittest discover -s tests
```
