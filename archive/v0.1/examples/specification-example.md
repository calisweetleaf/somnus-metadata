---
# ============================================================================
# SOMNUS METADATA CORE (v0.1)
# ============================================================================
somnus:
  version: "0.1.0"
  schema: "somnus://core/v1"
# --- Identity ---
id: "019d3e2f-9900-7fac-ad6e-4a50a7a72b34"
slug: "memory-hierarchy-invariants"
title: "Deterministic Invariants for Hierarchical Agent Memory"
aliases:
  - "memory-invariants"
  - "agent-mem-spec"
description: "Normative memory subsystem specification for Somnus Node."
created_at: "2026-03-30T10:00:00Z"
updated_at: "2026-03-30T10:14:00Z"
# --- Classification ---
classification:
  category: engineering
  type: specification
  subtype: memory-subsystem
  profile: "somnus://profiles/engineering/specification/v1"
  role: normative
  scope: subsystem
  tags:
    - agent-architecture
    - memory
    - invariants
# --- Lifecycle ---
lifecycle:
  status: active
  is_canonical: true
  reviewed_at: "2026-03-30T10:14:00Z"
# --- Lineage & Relations ---
relations:
  supersedes:
    - "urn:somnus:doc:0194a112-9c01-7111-a203-018273645500"
  superseded_by: []
  derived_from:
    - "urn:somnus:doc:0193f440-2a3b-7890-bcde-998877665544"
  cites:
    - "doi:10.1145/3318464.3389700"
  complements:
    - "urn:somnus:doc:0195e200-1111-7a3b-bf20-998877665544"
# --- Location & Provenance ---
location:
  repository: "git@github.com:somnus-org/somnus-core.git"
  repository_root: "docs/specifications"
  path: "examples/specification-example.md"
  historical_paths:
    - "drafts/vance/memory-draft.md"
    - "rfc/rfc-012-invariants.md"
origin:
  repository: "git@github.com:somnus-org/somnus-core.git"
  path: "drafts/vance/memory-draft.md"
  initial_commit: "9f83a1b490f23b7e12"
provenance:
  authors:
    - name: "Dr. Eleanor Vance"
      id: "user:vance@somnus.org"
      role: author
  operators:
    - name: "Somnus Copilot"
      id: "agent:somnus-autodoc-04"
      role: editor
      model: "anthropic/claude-3-7-sonnet"
      operator: "user:vance@somnus.org"
      interaction_at: "2026-03-30T10:14:00Z"
      actions:
        - edited
        - verified
  verification:
    verified_by: "system:somnus-core-ci"
    verified_at: "2026-03-30T10:14:00Z"
    status: passed
  history_ledger: "provenance/ledger/2026-03-30-0195e34a.json"
# ============================================================================
# PROFILE EXTENSION (Profile: Specification)
# ============================================================================
specification:
  system_target: "somnus-node"
  compliance_level: "mandatory"
  verification_suite: "tests/compliance/memory_suite.rs"
---

# System Memory Architecture

The memory subsystem is divided into episodic, working, and canonical tiers.

:::submatter:invariant{id="019d3e34-2ce0-7725-acf2-693399e8f529" status="active" authority="canonical"}
### Invariant 1: Single-Writer Principle

Only the designated core consolidation agent may commit updates to the canonical tier.
Any secondary agent attempting concurrent write operations must be rejected with
a concurrency exception.
:::

The following hypothesis is currently undergoing verification:

:::submatter:hypothesis{id="019d3e35-1740-7dc5-b541-f7456b378196" test_ref="tests/bench_mem.py"}
Increasing working memory tier caching from 16KB to 64KB will decrease retrieval latency
without causing context thrashing.
:::

Nesting is supported by incrementing the fence count:

::::submatter:decision{id="0195e360-12ab-7c01-8def-001122334455" status="accepted"}
### ADR-01: Use UUIDv7 for Identity

UUIDv7 is chosen over ULID due to RFC 9562 formal standardization.

:::submatter:evidence{id="0195e366-0210-7a00-98ff-112233445566" source="bench/uuid-sort-2026-03-29.json"}
Sort benchmark shows UUIDv7 indexes 38 percent faster than UUIDv4 on the canonical tier.
:::
::::
