---
# ============================================================================
# SOMNUS METADATA CORE (v0.1)
# ============================================================================
somnus:
  version: "0.1.0"
  schema: "somnus://core/v1"
# --- Identity ---
id: "019d4845-6280-7c3a-831c-d620618c6232"
slug: "submatter-directive-guide"
title: "Submatter Directives Nesting Guide"
aliases:
  - "submatter-guide"
description: "Minimal guide demonstrating invariant, hypothesis, and nested submatter directives."
created_at: "2026-04-01T09:00:00Z"
updated_at: "2026-04-01T09:30:00Z"
# --- Classification ---
classification:
  category: engineering
  type: specification
  subtype: documentation-guide
  profile: "somnus://profiles/engineering/specification/v1"
  role: informative
  scope: component
  tags:
    - submatter
    - directives
    - authoring
# --- Lifecycle ---
lifecycle:
  status: provisional
  is_canonical: false
  reviewed_at: "2026-04-01T09:30:00Z"
# --- Lineage & Relations ---
relations:
  supersedes: []
  superseded_by: []
  derived_from:
    - "urn:somnus:doc:019d3e2f-9900-7fac-ad6e-4a50a7a72b34"
  cites: []
  complements: []
# --- Location & Provenance ---
location:
  repository: "git@github.com:somnus-org/somnus-core.git"
  repository_root: "docs/guides"
  path: "examples/submatter-example.md"
  historical_paths: []
origin:
  repository: "git@github.com:somnus-org/somnus-core.git"
  path: "drafts/guides/submatter-draft.md"
  initial_commit: "c0ffee1234567890ab"
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
      interaction_at: "2026-04-01T09:30:00Z"
      actions:
        - authored
        - edited
  verification:
    verified_by: "system:somnus-core-ci"
    verified_at: "2026-04-01T09:30:00Z"
    status: passed
  history_ledger: "provenance/ledger/2026-04-01-submatter-019d4845.json"
# ============================================================================
# PROFILE EXTENSION (Profile: Specification)
# ============================================================================
specification:
  system_target: "somnus-docs"
  compliance_level: "optional"
  verification_suite: "tests/compliance/submatter_suite.py"
---

# Submatter Directive Guide

This file demonstrates the Generic Container Directive grammar for submatter.

:::submatter:invariant{id="019d4846-1111-7aaa-8bbb-111122223333" status="active" authority="canonical"}
### Invariant: Inner Markdown Parses

Headers, bold **must strictly increase**, lists, and links inside a directive
parse as normal Markdown AST nodes. Do not wrap regions in custom HTML tags.
:::

:::submatter:hypothesis{id="019d4846-2222-7bbb-9ccc-444455556666" test_ref="tests/compliance/submatter_suite.py"}
Directives degrade gracefully on renderers without plugin support:
the `:::` lines show as plain text without mangling surrounding paragraphs.
:::

Arbitrary nesting uses colon-count stacking (`::::` wraps `:::`):

::::submatter:decision{id="019d4846-3333-7ccc-aa11-777788889999" status="accepted"}
### Decision: Directives Over HTML Comments

Container directives are preferred over HTML comments because comments cannot nest.

:::submatter:evidence{id="019d4846-4444-7ddd-bb22-000011112222" source="research/submatter-matrix.md"}
Evaluation matrix: directives score Excellent on nesting and inner AST parsing;
comments score Poor on nesting.
:::

Additional inner block at the same nesting level:

:::submatter:archive{id="019d4846-5555-7eee-8cc3-333344445555" status="historical"}
Historical note preserved for tracing: Pandoc fenced divs were considered
but rejected for weaker parser portability.
:::
::::
