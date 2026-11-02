---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a7a-db54-7732-bbce-453ddafc4c56"
  revision: 1
  title: "Scope — complete all-file discovery for registry adoption"
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
      - target_ref: "urn:somnus:artifact:01a19a7a-db54-7732-bbce-453ddafc4c56"
        aspects: ["content"]
  time: {}
  names:
    slug: "scope-complete-all-file-discovery-for-registry-adoption"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19a7a-db54-7732-bbce-453ddafc4c56"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Scope — complete all-file discovery for registry adoption

## Engagement mode

- Mode: EDIT.
- Target: `src/somnus/db/store.py::Store.scan`.
- Operator: Daeron; implementing agent: Codex.
- Date: 2026-11-01 (America/Chicago).
- Baseline: Git `e82e8bca40917c93b4010c8c6fbe547282e991d3`, which retains the
  complete pre-change source and tests.
- Justification: I am repairing the native reconciliation owner. A separate
  generic filesystem crawler would duplicate its root/exclusion policy and let
  "unmanaged 0" omit unknown-carrier hosts.

## Invariants and boundary

Preserve every carrier, identity/revision rule, exclusion, FTS behavior, missing
location transition, and host-write guarantee. The repair lists unstamped
sidecar-only hosts as unmanaged without reading their content or writing hosts.
It does not auto-adopt files, follow extra directories, or mutate shared models.
Package patch release 2.1.1 keeps core schema 2.0.0 and registry schema 2.

The canonical project layout stays `src/somnus/` and `tests/`. The existing
installed-package acceptance harness supplies real CLI/SQLite/file/MCP/PTY checks
and JSON/Markdown/log artifacts; no `tools/native` shadow implementation or
parallel test harness is being installed. Git preserves the source snapshot.
These are the project's native promotion gates, not a claim that the generic
Code Forge layout verifier has passed unchanged.

## Acceptance and evidence

1. Real JSON, extensionless/text and binary fixtures appear in unmanaged paths.
2. Excluded files remain excluded; discovery leaves every host byte untouched.
3. A 64 MB real sparse binary is discovered with less than 8 MB traced Python
   allocation, rather than being read into memory.
4. Real CLI stamping makes a JSON host managed exactly once. Removing its sidecar
   reports it as unmanaged again and marks the old location missing.
5. The installed-wheel harness proves unmanaged sidecar-host hints through the
   consumed CLI.
6. Full unittest, semantic, mypy, and installed acceptance gates stay green.
7. Root/source Doctor baseline and final scans have comparable coverage. Any new
   serious finding is resolved or explicitly dispositioned in PLAN.md.
8. Build/publish/reinstall the patch through the existing release route; then
   continue the full cross-root adoption in HANDOFF.md.
