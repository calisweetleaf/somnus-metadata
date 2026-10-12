# How to contribute

somnus-metadata is a solo project: one operator, one `main` branch, and local commits. This section explains how a change is made, tested, and judged finished, whether the author is the operator or an agent working on the operator's behalf.

## Working model

- There are no pull requests, reviewers, or CI pipelines. Work is committed locally on `main` (14 commits at the time of writing, from `5f1df5d` to `dc3c981`).
- The authority order is fixed by `AGENTS.md`: `SPEC.md` is normative, `DECISIONS.md` explains why, `tests/test_conformance.py` is the executable acceptance criteria, and `src/somnus/` is the runnable truth. When code and `SPEC.md` disagree, the spec wins and the code is the bug.
- `archive/` is historical. Nothing under `src/` may import from it, and nothing in it may be cited as an active rule (DECISIONS.md D15).
- `Somnus Markdown Metadata Standard Research.md` is evidence only and must never be overwritten.

## Definition of done

A change is finished when all of the following hold:

1. **Tests pass.** `$env:PYTHONPATH="src"; python -m unittest discover -s tests` ends with `OK` (443 tests at the time of writing). Read the `OK`/`FAILED` line, not the PowerShell exit code; see [pitfalls](../background/pitfalls.md).
2. **Somnus-managed documents are clean.** `somnus check SPEC.md DECISIONS.md --level semantic` reports no errors.
3. **Doctor findings are dispositioned.** Every serious finding from the two somnus-debug configs is either fixed or recognized as a reviewed false positive (intentional reporting handlers, protocol stubs, short dataclasses). See [tooling](tooling.md).
4. **The spec still wins.** If the change alters behavior described in `SPEC.md`, either the code now matches the spec, or the spec was revised first (with a matching `DECISIONS.md` revision when a ratified decision changes). See [development workflow](development-workflow.md).
5. **No new dependencies.** `pyproject.toml` keeps `dependencies = []`.
6. **Committed** with a conventional prefix (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).

## Pages in this section

| Page | Covers |
| --- | --- |
| [Development workflow](development-workflow.md) | The edit, test, commit cycle and when a spec change needs a decision revision |
| [Testing](testing.md) | The 12 suites, what each covers, and the fixture patterns they use |
| [Debugging](debugging.md) | Diagnostic codes, `--debug`, reading the registry, common errors |
| [Tooling](tooling.md) | `pyproject.toml`, uv, somnus-debug, Surgeon, git attributes |
| [Patterns and conventions](patterns-and-conventions.md) | Code style and recurring idioms in `src/somnus/` |

## Rules for agents

The rules in `AGENTS.md` apply to every contributor, human or not:

- Create documents with `somnus new`, never by copying another header (that duplicates its `id`).
- Never edit `id`, and never hand-invent IDs, dates, actors, licenses, evidence, or acceptance records.
- Change lifecycle status with `somnus status`, and make indexed content changes new revisions with `somnus bump`.
- Put tool-specific data under `extensions.<owner>`; unknown fields are errors.
