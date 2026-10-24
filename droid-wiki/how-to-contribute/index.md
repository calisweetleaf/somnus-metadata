# How to contribute

This section explains how to pick up work, test it, and review it against the Somnus contract. Start with `AGENTS.md` for authority and safety rules, `filetree.md` for navigation, and `PLAN.md` for the current maintenance handoff.

## Working model

- `.github/workflows/ci.yml` runs on pushes to `main`, pull requests, and manual dispatch. It defines cross-platform tests, policy guards, and an installed-wheel smoke test. The configuration does not establish required reviews or branch protection.
- `.github/workflows/droid-wiki-refresh.yml` generates the wiki on pushes to `main` and opens or updates a rolling pull request from `factory/droid-wiki`. Review generated pages before merging. See [Automation](../deployment.md).
- The authority order is fixed by `AGENTS.md`: `SPEC.md` is normative, `DECISIONS.md` explains why, `tests/test_conformance.py` is the executable acceptance criteria, and `src/somnus/` is the runnable truth. When code and `SPEC.md` disagree, the spec wins and the code is the bug.
- `archive/` is historical. Nothing under `src/` may import from it, and nothing in it may be cited as an active rule (DECISIONS.md D15).
- `Somnus Markdown Metadata Standard Research.md` is evidence only and must never be overwritten.

## Definition of done

A change is finished when all of the following hold:

1. **Relevant checks pass.** From the root, run `PYTHONPATH=src python -m unittest discover -s tests` and inspect its exit status and final summary. The current suite has 476 tests in 13 modules. Also run `python -m mypy` (optional development tooling, required verification gate). See [Testing](testing.md) for PowerShell, targeted runs, and the observed mypy-version limitation.
2. **Somnus-managed documents are clean.** `PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic` reports no errors.
3. **Diagnostics are reviewed.** When using somnus-debug, investigate new serious findings rather than assuming they are false positives. See [Tooling](tooling.md).
4. **The spec still wins.** Fix implementation drift in code. A material contract change needs explicit authorization, a new ratified decision where applicable, and the release procedure in `SPEC.md` section 23. See [Development workflow](development-workflow.md).
5. **No new dependencies.** `pyproject.toml` keeps `dependencies = []`.
6. **The diff is scoped.** Preserve existing user work and review all changed files. If a commit is requested, use the configured identity and a conventional prefix matching recent history.
7. **Verification claims are precise.** State what ran locally. An import or passing checkout suite does not prove an installed command, external MCP host, or live terminal works (`AGENTS.md`, `PLAN.md`).

## Pages in this section

`CONTRIBUTING.md` and `.github/pull_request_template.md` require exact results for all three gates (unittest, semantic validation, mypy), explicit SPEC/DECISIONS impact, and tests for new behavior. `CODEOWNERS` names `@calisweetleaf`, including owner review for the normative documents; this declaration alone does not prove branch protection enforces approval. Ratified rationale now runs through D18.

Development/build dependencies, hook revisions, and Actions updates must be at least seven days old before merge, except a reviewed critical-security fix with explicit maintainer sign-off (`CONTRIBUTING.md`). `.github/dependabot.yml` schedules weekly proposals but does not enforce this cooling-off period.

| Page | Covers |
| --- | --- |
| [Development workflow](development-workflow.md) | The edit, test, commit cycle and when a spec change needs a decision revision |
| [Testing](testing.md) | The 13 suites, what each covers, and the fixture patterns they use |
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
