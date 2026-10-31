# somnus-metadata

The Somnus metadata standard (core `somnus://metadata/core/2.0.0`) and its stdlib-only toolkit.

Every managed file carries exactly one `somnus:` header. Markdown files use frontmatter or a hidden
comment envelope. Code and config files use a comment envelope. All other files use a
`<file>.somnus.yaml` sidecar. A global SQLite registry (`~/.somnus/somnus.db`) indexes identity,
revisions, relations, claims, conflicts, and a full-text index of managed file content. It contains
no JSON.

- Normative specification: [SPEC.md](SPEC.md)
- Ratified decisions: [DECISIONS.md](DECISIONS.md)
- Historical material (not normative): [archive/](archive/README.md)

## Install

Requires Python 3.11+ and has no third-party dependencies.

```sh
uv tool install somnus-metadata
somnus --version
```

Alternatively, use `pipx install somnus-metadata`. For a Python virtual
 environment, use `python -m pip install somnus-metadata`.

The distribution is **somnus-metadata**; the command and Python import remain
**somnus**. Do not install the unrelated PyPI distribution named `somnus` into
this same environment: it owns the same command/import names.

For development from a source checkout, use `uv tool install --editable .`.
The installed tool works outside this repository; register the project roots you
want to manage with `somnus init --root /path/to/project`.

Somnus Metadata **2.1.0** implements metadata core **2.0.0**.
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
