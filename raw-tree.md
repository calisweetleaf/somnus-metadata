---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a67-7c79-720a-969f-6e86da54abc9"
  revision: 1
  title: "File Tree: somnus-metadata"
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
      - target_ref: "urn:somnus:artifact:01a19a67-7c79-720a-969f-6e86da54abc9"
        aspects: ["content"]
  time: {}
  names:
    slug: "file-tree-somnus-metadata"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19a67-7c79-720a-969f-6e86da54abc9"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# File Tree: somnus-metadata

**Generated:** 10/11/2026, 10:20:26 PM
**Root Path:** `c:\Users\trent\OneDrive\Desktop\Treys-Workspace\somnus-metadata`

```
├── .somnus-debug
│   ├── python_doctor.src.yaml
│   └── python_doctor.yaml
├── archive
│   ├── v0.1
│   │   ├── examples
│   │   │   ├── benchmark-example.md
│   │   │   ├── specification-example.md
│   │   │   └── submatter-example.md
│   │   ├── schemas
│   │   │   └── v1
│   │   │       ├── profiles
│   │   │       │   ├── engineering-benchmark-v1.json
│   │   │       │   └── engineering-specification-v1.json
│   │   │       └── core.json
│   │   ├── tools
│   │   │   ├── operator_docs_audit.py
│   │   │   └── validate.py
│   │   ├── GLOSSARY.md
│   │   └── SOMNUS-METADATA-SPEC-v0.1.md
│   ├── v2-proposal
│   │   ├── SOMNUS_FRONTMATTER_SPEC_v2.md
│   │   └── differences.md
│   └── README.md
├── droid-wiki
│   ├── background
│   │   ├── design-decisions.md
│   │   ├── index.md
│   │   ├── migration-context.md
│   │   └── pitfalls.md
│   ├── features
│   │   ├── adopting-files.md
│   │   ├── agent-integration.md
│   │   ├── cli-commands.md
│   │   ├── index.md
│   │   ├── lifecycle-and-revisions.md
│   │   ├── migration.md
│   │   └── querying.md
│   ├── how-to-contribute
│   │   ├── debugging.md
│   │   ├── development-workflow.md
│   │   ├── index.md
│   │   ├── patterns-and-conventions.md
│   │   ├── testing.md
│   │   └── tooling.md
│   ├── overview
│   │   ├── architecture.md
│   │   ├── getting-started.md
│   │   ├── glossary.md
│   │   └── index.md
│   ├── reference
│   │   ├── configuration.md
│   │   ├── data-models.md
│   │   ├── dependencies.md
│   │   └── index.md
│   ├── systems
│   │   ├── carriers.md
│   │   ├── document-model.md
│   │   ├── index.md
│   │   ├── registry.md
│   │   ├── tui.md
│   │   ├── validation.md
│   │   └── yaml-subset.md
│   ├── by-the-numbers.md
│   ├── cleanup-opportunities.md
│   ├── fun-facts.md
│   └── lore.md
├── src
│   └── somnus
│       ├── carriers
│       │   ├── __init__.py
│       │   ├── blockcomment.py
│       │   ├── linecomment.py
│       │   ├── markdown.py
│       │   └── sidecar.py
│       ├── commands
│       │   ├── __init__.py
│       │   ├── _common.py
│       │   ├── brief.py
│       │   ├── bump.py
│       │   ├── check.py
│       │   ├── edit.py
│       │   ├── fork.py
│       │   ├── index.py
│       │   ├── init.py
│       │   ├── ls.py
│       │   ├── migrate.py
│       │   ├── new.py
│       │   ├── query.py
│       │   ├── regions.py
│       │   ├── schema.py
│       │   ├── stale.py
│       │   ├── stamp.py
│       │   └── status.py
│       ├── db
│       │   ├── __init__.py
│       │   ├── schema.sql
│       │   └── store.py
│       ├── model
│       │   ├── __init__.py
│       │   ├── jsonschema_export.py
│       │   ├── lifecycle.py
│       │   ├── schema.py
│       │   ├── validate.py
│       │   └── vocab.py
│       ├── tui
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── form.py
│       │   ├── term.py
│       │   └── widgets.py
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── document.py
│       ├── ids.py
│       ├── infer.py
│       ├── output.py
│       ├── regions.py
│       └── yamlsub.py
├── tests
│   ├── test_carriers.py
│   ├── test_commands.py
│   ├── test_config.py
│   ├── test_conformance.py
│   ├── test_document.py
│   ├── test_ids.py
│   ├── test_lifecycle.py
│   ├── test_regions.py
│   ├── test_store.py
│   ├── test_tui.py
│   ├── test_validate.py
│   └── test_yamlsub.py
├── .gitattributes
├── .gitignore
├── AGENTS.md
├── DECISIONS.md
├── PLAN.md
├── README.md
├── SPEC.md
├── Somnus Markdown Metadata Standard Research.md
├── filetree.md
└── pyproject.toml
```