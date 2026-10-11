# filetree.md â€” somnus-metadata (spatial map only)

> This file is a location map, not a router. For workflow entry points see `AGENTS.md`.

```
.
â”œâ”€â”€ AGENTS.md                                      # bootstrap (router)
â”œâ”€â”€ SPEC.md                                        # normative standard, core 2.0.0
â”œâ”€â”€ DECISIONS.md                                   # ratified decisions D1â€“D15
â”œâ”€â”€ PLAN.md                                        # implementation plan
â”œâ”€â”€ README.md                                      # install and quick start
â”œâ”€â”€ filetree.md                                    # this map
â”œâ”€â”€ pyproject.toml                                 # package `somnus`, stdlib-only, entry point `somnus`
â”œâ”€â”€ Somnus Markdown Metadata Standard Research.md  # evidence, read-only
â”œâ”€â”€ src/somnus/
â”‚   â”œâ”€â”€ cli.py                                     # argparse dispatcher, exit-code mapping
â”‚   â”œâ”€â”€ yamlsub.py                                 # restricted YAML subset parser + canonical serializer
â”‚   â”œâ”€â”€ ids.py                                     # UUIDv7 / URN minting and parsing
â”‚   â”œâ”€â”€ config.py                                  # SOMNUS_HOME, config.toml, .somnus.toml layering
â”‚   â”œâ”€â”€ document.py                                # load / locate envelope / save with host preservation
â”‚   â”œâ”€â”€ regions.py                                 # region-marker scanning and pairing
â”‚   â”œâ”€â”€ infer.py                                   # header inference for stamp/new
â”‚   â”œâ”€â”€ output.py                                  # diagnostics, aligned/TSV tables
â”‚   â”œâ”€â”€ model/                                     # schema, vocab, lifecycle, validate, JSON Schema export
â”‚   â”œâ”€â”€ carriers/                                  # markdown, linecomment, blockcomment, sidecar
â”‚   â”œâ”€â”€ db/                                        # schema.sql + store.py (global SQLite registry)
â”‚   â”œâ”€â”€ commands/                                  # one module per CLI command
â”‚   â””â”€â”€ tui/                                       # stdlib terminal UI (`somnus edit`)
â”œâ”€â”€ tests/                                         # unittest suites incl. test_conformance.py (SPEC Â§21)
â””â”€â”€ archive/                                       # historical, NOT normative (see archive/README.md)
    â”œâ”€â”€ v0.1/                                      # v0.1 spec, glossary, schemas, examples, tools
    â””â”€â”€ v2-proposal/                               # intermediate v2 proposal and diff notes
```

## Ownership

- Research: evidence only; frozen.
- SPEC.md: normative; changes follow SPEC Â§23 and a DECISIONS.md revision.
- src/somnus: implementation of SPEC.md; stdlib-only.
- tests: executable acceptance criteria; `test_conformance.py` mirrors SPEC Â§21 one-to-one.
- archive: read-only history; never imported, never indexed.

## Runtime state (outside the repo)

- `$SOMNUS_HOME` (default `~/.somnus/`): `config.toml`, `somnus.db` registry.

## Tooling state (gitignored)

- `.python_doctor/`, `.python_doctor-src/`: somnus-debug doctor state.
- `.somnus-debug/`: doctor configs (tracked) and run logs (`runs/`, ignored).
- `.surgeon/`: Surgeon edit history.
