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
