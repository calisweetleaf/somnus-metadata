# filetree.md — somnus-metadata

Spatial/dependency map for the current checkout. For task routing and authority,
start with [`AGENTS.md`](AGENTS.md); this file is not normative.

```text
.
├── AGENTS.md                         # project entry packet, validation, constraints
├── SPEC.md                           # normative core 2.0.0 contract; §§20–23 CLI/MCP/conformance/versioning
├── DECISIONS.md                      # ratified rationale D1–D19
├── PLAN.md                           # evidence, completion frontier, operator setup/handoff
├── CONTEXT.md                        # architectural relations and observed tool boundaries
├── AGENTS.somnus.v2.md                # inactive project-specific comparison candidate
├── AGENTS.template.v2.md              # preserved imported proposal; not active instructions
├── .codex/OPERATING.md                # adaptive composed tool/skill route; no local hook installed
├── workflows.md                      # supplied BB7 suggested playbook
├── last-session.txt                  # historical Factory account; not current proof
├── docs/references-unrelated-to-codebase/ # user-owned collaboration context, including House fable
├── README.md                         # install and quick start
├── filetree.md                       # this navigation map
├── pyproject.toml                    # stdlib-only package, `somnus` entry point

├── MANIFEST.in                       # minimal release contents; excludes private operator/research artifacts
├── runbooks/package-release.md        # actual PyPI release and repeatable publishing/verification route
├── Somnus Markdown Metadata Standard Research.md # original research artifact; read-only
├── archives/                         # user-owned historical bundles; root ZIP deletions pre-exist
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
│   ├── db/                           # SQLite schema, FTS5 search index (D19), registry store
│   ├── commands/                     # one command module per CLI operation
│   │   └── set_fields.py             # `somnus set` implementation (D16)
│   └── tui/                          # terminal UI implementation
├── tests/
│   ├── test_conformance.py           # 21 SPEC acceptance fixtures
│   ├── test_mcp.py                   # adapter protocol, schema, and call behavior
│   ├── test_*.py                     # module and CLI behavior suites
│   └── acceptance/
│       └── installed_package_acceptance.py # explicit installed-wheel acceptance (not discovered)
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
