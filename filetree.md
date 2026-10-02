# filetree.md — somnus-metadata (spatial map only)

> This file is a location map, not a router. For workflow entry points see `AGENTS.md`.

```
.
├── Somnus Markdown Metadata Standard Research.md  # evidence, read-only (685 lines)
├── AGENTS.md                                      # bootstrap (router)
├── filetree.md                                    # this map
├── schemas/
│   └── v1/
│       ├── core.json                              # Somnus Core (somnus://core/v1)
│       └── profiles/
│           ├── engineering-specification-v1.json  # somnus://profiles/engineering/specification/v1
│           └── engineering-benchmark-v1.json      # somnus://profiles/engineering/benchmark/v1
├── examples/
│   ├── specification-example.md                   # usage truth (specification profile)
│   ├── benchmark-example.md                       # usage truth (benchmark profile)
│   └── submatter-example.md                       # usage truth (directive nesting)
└── tools/
    ├── validate.py                                # 3-stage validator (stdlib-only)
    └── operator_docs_audit.py                     # presence audit (report-only)
```

## Ownership

- Research: source of truth for requirements; owned by research pass, frozen.
- Schemas: owned by standard; `core.json` is base, profiles compose via `allOf`.
- Examples: owned by docs; must stay valid under `tools/validate.py`.
- Tools: owned by implementation; stdlib-only, no new dependencies.

## Doc locations

- Evidence: `Somnus Markdown Metadata Standard Research.md`
- Normative: TODO (`SPEC.md` missing; do not treat Research as normative).
- Continuity set: TODO (`CONTEXT.md`, `MEMORY.md`, `NOTEPAD.md`, `TASK.md`, `PLAN.md` missing).
- Validation truth: `schemas/v1/`
- Usage truth: `examples/`
