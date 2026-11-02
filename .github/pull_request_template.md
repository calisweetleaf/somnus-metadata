---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a67-77ff-730e-b9d6-b30eff562aeb"
  revision: 1
  title: "Description"
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
      - target_ref: "urn:somnus:artifact:01a19a67-77ff-730e-b9d6-b30eff562aeb"
        aspects: ["content"]
  time: {}
  names:
    slug: "description"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19a67-77ff-730e-b9d6-b30eff562aeb"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
## Description

<!-- What changes and why. Link the issue it resolves (Fixes #NNN). -->

## Testing Done

<!-- Exact commands run and their results. Mark anything not run as NOT RUN. -->

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
python -m mypy
```

- [ ] Unit and conformance tests pass
- [ ] Semantic check of `SPEC.md` and `DECISIONS.md` passes
- [ ] `mypy` passes
- [ ] New behavior is covered by a test (or the reason it is not is stated above)

## SPEC / DECISIONS impact

- [ ] No impact: behavior stays within the existing `SPEC.md` contract and `DECISIONS.md` D1-D17
- [ ] `SPEC.md` clarified without changing behavior
- [ ] Normative contract changed: new ratified decision added to `DECISIONS.md`, `SPEC.md` version updated under section 23, and `tests/test_conformance.py` adjusted
- [ ] If implementation and `SPEC.md` disagreed, the implementation was fixed, not the contract

## Checklist

- [ ] Runtime dependencies in `pyproject.toml` remain empty (stdlib only)
- [ ] `src/` does not import from `archive/`
- [ ] Writes to host files preserve bytes outside the metadata envelope (`E_HOST` otherwise)
- [ ] Registry and tool output remains text/TSV; JSON only for MCP JSON-RPC framing (D4, D17)
- [ ] No IDs, dates, actors, licenses, or evidence were invented in Somnus-managed files
- [ ] No secrets or private document content are included
