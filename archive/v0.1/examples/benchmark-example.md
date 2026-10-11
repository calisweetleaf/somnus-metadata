---
# ============================================================================
# SOMNUS METADATA CORE (v0.1)
# ============================================================================
somnus:
  version: "0.1.0"
  schema: "somnus://core/v1"
# --- Identity ---
id: "019d3f1f-7b28-7609-a265-9324df0f6233"
slug: "memory-tier-benchmark"
title: "Working Memory Tier Retrieval Benchmark"
aliases:
  - "memory-bench"
  - "tier-retrieval-bench"
description: "Benchmark report for working memory tier retrieval latency."
created_at: "2026-03-30T14:22:01Z"
updated_at: "2026-03-30T15:00:00Z"
# --- Classification ---
classification:
  category: engineering
  type: benchmark
  subtype: memory-performance
  profile: "somnus://profiles/engineering/benchmark/v1"
  role: informative
  scope: subsystem
  tags:
    - benchmarking
    - memory
    - latency
# --- Lifecycle ---
lifecycle:
  status: active
  is_canonical: false
  reviewed_at: "2026-03-30T15:00:00Z"
# --- Lineage & Relations ---
relations:
  supersedes: []
  superseded_by: []
  derived_from:
    - "urn:somnus:doc:019d3e2f-9900-7fac-ad6e-4a50a7a72b34"
  cites:
    - "doi:10.1145/3318464.3389700"
  complements:
    - "urn:somnus:doc:0195e200-1111-7a3b-bf20-998877665544"
# --- Location & Provenance ---
location:
  repository: "git@github.com:somnus-org/somnus-core.git"
  repository_root: "docs/benchmarks"
  path: "examples/benchmark-example.md"
  historical_paths:
    - "drafts/bench/memory-tier-draft.md"
origin:
  repository: "git@github.com:somnus-org/somnus-core.git"
  path: "drafts/bench/memory-tier-draft.md"
  initial_commit: "a1b2c3d4e5f6071829"
provenance:
  authors:
    - name: "Dr. Eleanor Vance"
      id: "user:vance@somnus.org"
      role: author
  operators:
    - name: "Somnus Agent Worker"
      id: "agent:somnus-autodoc-04"
      role: editor
      model: "anthropic/claude-3-7-sonnet"
      operator: "user:vance@somnus.org"
      interaction_at: "2026-03-30T15:00:00Z"
      actions:
        - generated
        - tested
  verification:
    verified_by: "system:somnus-core-ci"
    verified_at: "2026-03-30T15:00:00Z"
    status: passed
  history_ledger: "provenance/ledger/2026-03-30-bench-0195e34b.json"
# ============================================================================
# PROFILE EXTENSION (Profile: Benchmark)
# ============================================================================
benchmark:
  workload: "working-memory-retrieval-64k"
  environment:
    cpu: "AMD Ryzen 5 5625U"
    memory_gb: 16
    os: "Ubuntu 24.04"
  metrics:
    - name: "p50-latency"
      value: 1.42
      unit: "ms"
    - name: "p99-latency"
      value: 4.87
      unit: "ms"
    - name: "throughput"
      value: 12400
      unit: "ops"
---

# Working Memory Tier Retrieval Benchmark

This benchmark measures retrieval latency for the 64KB working memory tier.

:::submatter:invariant{id="019d3f22-3660-7a65-b12c-c038eabef75c" status="active" authority="canonical"}
### Invariant: Measurement Stability

Benchmark runs must pin CPU frequency and disable background consolidation
before sampling latency distributions.
:::

:::submatter:hypothesis{id="0195e366-0210-7a01-bcae-223344556677" test_ref="tests/bench_mem.py"}
64KB working tier caching reduces p99 latency by at least 20 percent
relative to the 16KB baseline without increasing thrash rate.
:::

Nested evidence block for audit trail:

::::submatter:decision{id="0195e361-77aa-7d02-9abc-445566778899" status="accepted"}
### Decision: Accept 64KB Tier

The 64KB tier is accepted after three consecutive passing runs.

:::submatter:evidence{id="0195e367-0311-7b11-affe-778899001122" source="bench/run-2026-03-30.json"}
Run 0195e34b: p50 1.42 ms, p99 4.87 ms, throughput 12400 ops.
:::
::::
