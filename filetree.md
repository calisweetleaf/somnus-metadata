# filetree.md — somnus-metadata

Spatial/dependency map for the current checkout. For task routing and authority,
start with [`AGENTS.md`](AGENTS.md); this file is not normative.

```text
.
├── AGENTS.md                         # project entry packet, validation, constraints
├── SPEC.md                           # normative core 2.0.0 contract; §§20–23 CLI/MCP/conformance/versioning
├── DECISIONS.md                      # ratified rationale D1–D17
├── PLAN.md                           # current delivery state and maintenance priorities
├── README.md                         # install and quick start
├── filetree.md                       # this navigation map
├── pyproject.toml                    # stdlib-only package, `somnus` entry point
├── Somnus Markdown Metadata Standard Research.md # original research artifact; read-only
├── somnus-metadata-v2.zip             # retained historical bundle
├── somnus-metadata.zip                # retained historical bundle
├── .somnus-debug/
│   ├── python_doctor.yaml            # root diagnostics configuration
│   └── python_doctor.src.yaml        # src import-aware diagnostics configuration
├── src/somnus/
│   ├── cli.py                        # argparse command surface / dispatch
│   ├── mcp.py                        # stdio JSON-RPC adapter, D17
│   ├── yamlsub.py                    # restricted YAML parser / canonical serializer
│   ├── document.py                   # envelope IO / byte preservation
│   ├── regions.py                    # in-document metadata regions
│   ├── ids.py, config.py, infer.py   # identity, config, header inference
│   ├── model/
│   │   ├── schema.py, vocab.py       # schema definitions / controlled values
│   │   ├── validate.py               # validation pipeline
│   │   └── lifecycle.py              # lifecycle transition rules
│   ├── carriers/                     # Markdown, comments, sidecar placement
│   ├── db/                           # SQLite schema and registry store
│   ├── commands/                     # one command module per CLI operation
│   │   └── set_fields.py             # `somnus set` implementation (D16)
│   └── tui/                          # terminal UI implementation
├── tests/
│   ├── test_conformance.py           # 21 SPEC acceptance fixtures
│   ├── test_mcp.py                   # adapter protocol, schema, and call behavior
│   └── test_*.py                     # module and CLI behavior suites
├── droid-wiki/                       # explanatory wiki; secondary to SPEC/DECISIONS
│   ├── background/, features/
│   ├── how-to-contribute/, overview/
│   ├── reference/, systems/
│   └── .wiki-meta.json
└── archive/                          # historical and non-normative
    ├── README.md                     # archive boundary warning
    ├── v0.1/                         # prior spec, schemas, examples, tools
    ├── v2-proposal/                  # intermediate proposal
```

## Runtime state outside source

- `$SOMNUS_HOME` (default `~/.somnus/`): `config.toml` and `somnus.db`.
- `.python_doctor/`, `.python_doctor-src/`, `.somnus-debug/runs/`, and
  `.surgeon/` are generated/ignored tooling state; not authoritative source.

## Dependency / authority spine

```text
SPEC.md + DECISIONS.md
        ↓ contract
src/somnus/model + yamlsub + carriers + document + regions + db
        ↓ composed by
commands → cli.py → optional mcp.py / TUI
        ↓ consumed and checked by
tests/test_conformance.py + module/CLI/MCP suites
```

`archive/` is excluded from the runtime spine. `droid-wiki/` explains behavior
but does not override the normative specification.
