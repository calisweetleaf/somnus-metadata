# filetree.md — somnus-metadata (spatial map only)

> This file is a location map, not a router. For workflow entry points see `AGENTS.md`.

```
.
├── AGENTS.md                                      # bootstrap (router)
├── SPEC.md                                        # normative standard, core 2.0.0
├── DECISIONS.md                                   # ratified decisions D1–D17
├── PLAN.md                                        # implementation plan
├── README.md                                      # install and quick start
├── filetree.md                                    # this map
├── pyproject.toml                                 # package `somnus`, stdlib-only, entry point `somnus`
├── Somnus Markdown Metadata Standard Research.md  # evidence, read-only
├── src/somnus/
│   ├── cli.py                                     # argparse dispatcher, exit-code mapping
│   ├── yamlsub.py                                 # restricted YAML subset parser + canonical serializer
│   ├── ids.py                                     # UUIDv7 / URN minting and parsing
│   ├── config.py                                  # SOMNUS_HOME, config.toml, .somnus.toml layering
│   ├── document.py                                # load / locate envelope / save with host preservation
│   ├── regions.py                                 # region-marker scanning and pairing
│   ├── infer.py                                   # header inference for stamp/new
│   ├── output.py                                  # diagnostics, aligned/TSV tables
│   ├── mcp.py                                     # `somnus mcp` stdio server; tools generated from cli.py
│   ├── model/                                     # schema, vocab, lifecycle, validate, JSON Schema export
│   ├── carriers/                                  # markdown, linecomment, blockcomment, sidecar
│   ├── db/                                        # schema.sql + store.py (global SQLite registry)
│   ├── commands/                                  # one module per CLI command (`set` -> set_fields.py)
│   └── tui/                                       # stdlib terminal UI (`somnus edit`)
├── tests/                                         # unittest suites incl. test_conformance.py (SPEC §21)
└── archive/                                       # historical, NOT normative (see archive/README.md)
    ├── v0.1/                                      # v0.1 spec, glossary, schemas, examples, tools
    └── v2-proposal/                               # intermediate v2 proposal and diff notes
```

## Ownership

- Research: evidence only; frozen.
- SPEC.md: normative; changes follow SPEC §23 and a DECISIONS.md revision.
- src/somnus: implementation of SPEC.md; stdlib-only.
- tests: executable acceptance criteria; `test_conformance.py` mirrors SPEC §21 one-to-one.
- archive: read-only history; never imported, never indexed.

## Runtime state (outside the repo)

- `$SOMNUS_HOME` (default `~/.somnus/`): `config.toml`, `somnus.db` registry.

## Tooling state (gitignored)

- `.python_doctor/`, `.python_doctor-src/`: somnus-debug doctor state.
- `.somnus-debug/`: doctor configs (tracked) and run logs (`runs/`, ignored).
- `.surgeon/`: Surgeon edit history.
