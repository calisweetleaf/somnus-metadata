# Somnus Metadata 2.0.0 — Delivery State and Maintenance Plan

## Purpose and authority

This is a current operational plan, not the original build specification. The
normative contract is `SPEC.md`; ratified rationale is in `DECISIONS.md`; source
and tests decide what is implemented. If this plan conflicts with any of those,
follow the authority order in `AGENTS.md` and correct this plan.

## Current delivery state

Core `somnus://metadata/core/2.0.0` and the stdlib-only `somnus` toolkit are
implemented in this checkout. The delivered surface includes:

- Core schema, restricted-YAML parser/canonical serializer, validation,
  lifecycle, UUIDv7/URN identity, region handling, and host-preserving carriers.
- Global SQLite registry, configuration, diagnostics, and the CLI command set
  documented in `SPEC.md` §20.
- Interactive `somnus edit` plus `somnus set` for the same bounded header field
  set (D16).
- `somnus mcp`, a stdio JSON-RPC adapter that exposes non-interactive CLI
  commands and returns the CLI's text/TSV output (D17).
- The 21-fixture acceptance suite in `tests/test_conformance.py` and module /
  command / MCP suites under `tests/`.

Current checkout verification (2026-10-19):

```sh
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic
```

The verified result was 459 tests passing and semantic validation of these two
documents with zero errors or warnings. This is a checkout-level result; it is
not evidence that a separate global `somnus` installation or an external MCP
client has been validated on every supported host.

## Maintenance priorities

No new normative feature or schema release is authorized by this plan. Select a
new feature only through an explicit operator decision, then update its decision
record and SPEC release together as required by `SPEC.md` §23.

For maintenance work, use this order:

1. Reproduce a reported defect at its owning code path and add a regression test.
2. Keep parser, serializer, schema, CLI, MCP, and conformance behavior aligned;
   do not broaden accepted syntax or editable fields by documentation alone.
3. Verify host-byte preservation, registry consistency, and zero external runtime
   dependencies where the touched path requires them.
4. Update the relevant docs and `filetree.md` only when the implemented surface
   or navigation actually changes.

## Deferred / separately verified surfaces

- Global installation via `uv tool install --editable .` and invocation outside
  the checkout have not been verified in the current work session.
- MCP behavior is covered by the repository's in-process/stdio tests; a live
  external MCP host integration is a separate compatibility check.
- Cross-platform terminal behavior and file-preservation semantics must be
  verified on the target OS when a platform-specific change is made.

These are verification boundaries, not known defects. Do not turn them into
feature work without a task or observed failure.
