# How to contribute

This section explains how to pick up work, test it, and review it against the Somnus contract. Follow the active `AGENTS.md`: its rewritten First move (operator correction, 2026-11-01) defines the completion scope as release and installation, which the top sections of `PLAN.md` and `HANDOFF.md` record as complete. The earlier cross-root adoption job and its "Done means" list are superseded history, not gates. Orient on the current top section of `PLAN.md`, read only the relevant section of `CONTEXT.md`, and use `filetree.md` for navigation. `.codex/OPERATING.md` is an adaptive operating route, not a compulsory sequence or proof that its tools are installed. `AGENTS.v1.md` is preserved but superseded.

The newest top sections of `PLAN.md` and `HANDOFF.md` record toolkit 2.1.1, native plugin 1.2.1 installed in Codex and Factory from the clean production payload (source commit 35c228a, hosted CI 41402125903 passed, 26 plugin tests; both catalogs select the reproducible 8-file native export and both installed caches contain 0 .somnus.yaml files), the 1.2.0 native installed/enabled identity `somnus-metadata-plugin@somnus-metadata-plugin` (commit 4deee50), and five registered roots. The last recorded scan in `docs/USAGE_GUIDE.md` section 9 reports 2,659 managed hosts, 21,554 unmanaged, and no invalid/missing hosts or conflicts; the earlier 1,064 / 23,148 checkpoint is prior history and superseded older `CONTEXT.md` snapshots. Core/plugin adoption and nested-root consolidation are already complete; do not repeat them. Fresh Codex and Factory MCP lifecycle queries returned the same two real full paths, and the installed skill was read at both requested paths.

There is no remaining adoption job: the operator stopped bulk adoption on 2026-11-01 and retired the zero-unmanaged criterion, leaving the prior per-root counts (Repositories 2,780 unmanaged, LAB 19,736, Somnus-MCP 632) as history. The 2.1.1 repair in `src/somnus/db/store.py` counts hosts needing sidecars without reading unmanaged payloads, replacing the incomplete embedded-only inventory. If adoption is ever resumed under a new operator request, use the complete native unmanaged-path list and preserve deliberate exclusions, including the live Somnus-MCP data plane. Protected-source sidecar preservation has only an isolated fixture proof. Plugin 1.2.1 has recorded fresh tests (26), green hosted CI 41402125903, and a clean production payload (the checked-in 8-file native export, with both installed caches inspected after a clean native remove/install at 0 .somnus.yaml files); plugin 1.2.0 established the native installed/enabled records in both Codex and Factory after a native remove/install refresh and green hosted CI 41399524229; both native cached skill trees and the requested custom skill copies match the canonical shared skill, and fresh Codex and Factory sessions called the native-plugin MCP `q(text="lifecycle", limit=1, tsv=true)` returning the lifecycle.py source path. The earlier 1.1.1 clean-reinstall report was a superseded direct skill/MCP adapter account the operator corrected on 2026-11-02: direct adapter health is not native plugin registration. A wiki refresh documents this state; it does not perform bulk adoption or modify global configuration. See [Adopting files](../features/adopting-files.md) and [Agent integration](../features/agent-integration.md).

## Working model

- `.github/workflows/ci.yml` runs on pushes to `main`, pull requests, and manual dispatch. It defines cross-platform tests, policy guards, and an installed-wheel smoke test. The configuration does not establish required reviews or branch protection.
- `.github/workflows/droid-wiki-refresh.yml` generates the wiki on pushes to `main`, except pushes touching only `droid-wiki/**`, and opens or updates a rolling pull request from `factory/droid-wiki`. Review generated pages before merging. See [Automation](../deployment.md).
- The authority order is fixed by `AGENTS.md`: `SPEC.md` is normative, `DECISIONS.md` explains why, `tests/test_conformance.py` is the executable acceptance criteria, and `src/somnus/` is the runnable truth. When code and `SPEC.md` disagree, the spec wins and the code is the bug.
- `archive/` is historical. Nothing under `src/` may import from it, and nothing in it may be cited as an active rule (DECISIONS.md D15).
- `Somnus Markdown Metadata Standard Research.md` is evidence only and must never be overwritten.

## Definition of done

A change is finished when all of the following hold:

1. **Relevant checks pass.** From the root, run `PYTHONPATH=src python -m unittest discover -s tests` and inspect its exit status and final summary. The current suite has 537 tests in 14 modules. Run `python -m mypy`, the third verification gate. This refresh passed 537 existing tests, semantic validation, and isolated mypy 2.4.1 across 49 source files. Earlier symlink-root and 67/67 installed results were not repeated for this operator-document-only delta. System Python lacked mypy; the older isolated 1.18.2 metadata-comment failure remains unresolved. See [Testing](testing.md) for exact boundaries.
2. **Somnus-managed documents are clean.** `PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic` reports no errors.
3. **Diagnostics are reviewed.** When using somnus-debug, investigate new serious findings rather than assuming they are false positives. See [Tooling](tooling.md).
4. **The spec still wins.** Fix implementation drift in code. A material contract change needs explicit authorization, a new ratified decision where applicable, and the release procedure in `SPEC.md` section 23. See [Development workflow](development-workflow.md).
5. **No new dependencies.** `pyproject.toml` keeps `dependencies = []`.
6. **The diff is scoped.** Preserve existing user work and review all changed files. If a commit is requested, use the configured identity and a conventional prefix matching recent history.
7. **Verification claims are precise.** State what ran locally. An import or passing checkout suite does not prove an installed command, external MCP host, or live terminal works (`AGENTS.md`, `PLAN.md`).

## Pages in this section

`CONTRIBUTING.md` and `.github/pull_request_template.md` require exact results for all three gates (unittest, semantic validation, mypy), explicit SPEC/DECISIONS impact, and tests for new behavior. `CODEOWNERS` names `@calisweetleaf`, including owner review for the normative documents; this declaration alone does not prove branch protection enforces approval. Ratified rationale now runs through D19.

Development/build dependencies, hook revisions, and Actions updates must be at least seven days old before merge, except a reviewed critical-security fix with explicit maintainer sign-off (`CONTRIBUTING.md`). `.github/dependabot.yml` schedules weekly proposals but does not enforce this cooling-off period.

| Page | Covers |
| --- | --- |
| [Development workflow](development-workflow.md) | The edit, test, commit cycle and when a spec change needs a decision revision |
| [Testing](testing.md) | The 14 suites, what each covers, and the fixture patterns they use |
| [Debugging](debugging.md) | Diagnostic codes, `--debug`, reading the registry, common errors |
| [Tooling](tooling.md) | `pyproject.toml`, uv, somnus-debug, Surgeon, git attributes |
| [Patterns and conventions](patterns-and-conventions.md) | Code style and recurring idioms in `src/somnus/` |

## Rules for agents

The rules in `AGENTS.md` apply to every contributor, human or not:

- Create documents with `somnus new`, never by copying another header (that duplicates its `id`).
- Never edit `id`, and never hand-invent IDs, dates, actors, licenses, evidence, or acceptance records.
- Change lifecycle status with `somnus status`, and make indexed content changes new revisions with `somnus bump`.
- Change title, summary, purpose, classification, tags, visibility, and disposition with `somnus set`, not by editing the envelope by hand (DECISIONS.md D16).
- Put tool-specific data under `extensions.<owner>`; unknown fields are errors.
