# somnus-metadata

The Somnus metadata standard (core `somnus://metadata/core/2.0.0`) and its stdlib-only toolkit.

Every managed file carries exactly one `somnus:` header. Markdown files use frontmatter or a hidden
comment envelope. Code and config files use a comment envelope. All other files use a
`<file>.somnus.yaml` sidecar. A global SQLite registry (`~/.somnus/somnus.db`) indexes identity,
revisions, relations, claims, and conflicts. It contains no JSON.

- Normative specification: [SPEC.md](SPEC.md)
- Ratified decisions: [DECISIONS.md](DECISIONS.md)
- Historical material (not normative): [archive/](archive/README.md)

## Install

Requires Python 3.11+ and has no third-party dependencies.

```
uv tool install --editable .
somnus --version
```

## Quick start

```
somnus init --root .                 # create ~/.somnus, config.toml, registry; register this root
somnus new specification "My Spec"   # scaffold a conformant Markdown artifact
somnus check my-spec.md --level semantic
somnus stamp notes.py                # dry-run diff; add --write to apply
somnus index                         # reconcile roots into the registry
somnus ls
somnus q --conflicts
somnus set my-spec.md "classification.tags=memory, design"   # header edit, new revision
somnus edit                          # terminal UI
```

`somnus brief` prints an agent cheat sheet suitable for pasting into a repository's `AGENTS.md`.

## MCP server

`somnus mcp` serves every command except `edit` as Model Context Protocol tools over stdio.
Each tool returns the command's text output. Register it with any MCP client by command:

```
somnus mcp                           # optional: somnus --actor NAME mcp
```

Exit codes: `0` ok, `1` validation errors, refusals, or conflicts, `2` usage or I/O errors.

## Tests

```
python -m unittest discover -s tests
```
