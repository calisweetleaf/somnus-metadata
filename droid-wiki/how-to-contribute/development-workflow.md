# Development workflow

Changes follow a short loop: read the governing contract, make a scoped edit, run relevant tests, and review the diff. `AGENTS.md` defines the safety rules; `.github/workflows/ci.yml` adds checks on pull requests and pushes to `main`. Changes to the standard carry extra obligations because `SPEC.md` and `DECISIONS.md` are Somnus-managed artifacts with their own revisions.

## The loop

1. **Orient.** Follow the mission-first `AGENTS.md`: recover the integrated objective, current evidence, and next action in `PLAN.md`, then read the relevant relationships in `CONTEXT.md`. Use `.codex/OPERATING.md` as a transition map, not a mandatory ceremony. Find the governing rule in `SPEC.md` (sections 3 to 13 for fields, 16 and 17 for carriers, 18 for the registry, 19 for validation, 20 for the CLI). `filetree.md` maps where code lives; [architecture](../overview/architecture.md) explains the layers. Preserve the superseded `AGENTS.v1.md`; it is not the active entry.
2. **Inspect the working tree.** Preserve existing changes. Use a topic branch when appropriate. `CODEOWNERS` names `@calisweetleaf` and calls for owner review of `SPEC.md` and `DECISIONS.md`; required approval enforcement depends on repository settings.
3. **Edit.** Keep changes at their owning code path. In OneDrive-synced checkouts, edit one file per call: multi-file Surgeon transactions fail with WinError 5 (`AGENTS.md`). See [Tooling](tooling.md).
4. **Test.** Run the suite from the repository root:

   ```sh
   PYTHONPATH=src python -m unittest discover -s tests
   ```

   In PowerShell, set `$env:PYTHONPATH="src"` and run the same Python module. For one suite, use `python -m unittest discover -s tests -p test_validate.py` with that environment (`tests/` is not a package).
5. **Check documents.** `PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic`.
6. **Type-check and review diagnostics.** Run `python -m mypy`, the third required gate in `CONTRIBUTING.md`; `python -m pip install -e ".[dev]"` installs the optional development extra. See [Testing](testing.md) for the passing isolated 1.18.2 check and historical 1.9.0 finding. Use the somnus-debug configs when appropriate. Record separately whether an installed wheel, external MCP client, or live terminal was exercised.
7. **Review and deliver.** Inspect the diff and test results before a requested commit or pull request. `.github/pull_request_template.md` asks for exact gate results, explicit normative-document impact, and test coverage. Use conventional prefixes matching history, including `ci:` for workflow changes. The CI matrix, policy guards, and installed-wheel test are described in [Automation](../deployment.md); configured jobs are not proof of a successful run.

Run `pre-commit run --all-files` when installed. `.pre-commit-config.yaml` has Ruff, mypy, and hygiene checks, but no formatter. Only the whitespace fixers skip Markdown, `archive/`, `archives/`, and `tests/`; those exclusions are not global.

Dependency and Actions updates must wait seven calendar days (168 hours) after upstream release before merge (`CONTRIBUTING.md`). A younger critical-security fix requires manual diff inspection and explicit maintainer sign-off. Dependabot's weekly schedule does not enforce release age.

## Reconciling git history

`AGENTS.md` records a local `pull.ff=only` policy. An ordinary pull must fast-forward. If branches diverge, inspect status, fetch, compare commits and trees on both sides, and preserve a named local ref before any authorized re-anchor or reset. Do not discard local commits based only on ahead/behind counts.

## When the code and the spec disagree

`SPEC.md` is normative. If a test or a user report shows the toolkit contradicting the spec, the default fix is in `src/somnus/`. A contract change requires an explicit decision and the versioning steps in `SPEC.md` section 23, not an incidental documentation edit.

## Changing the standard

`SPEC.md` and `DECISIONS.md` both carry `somnus:` headers, so the toolkit applies its own rules to them:

- **Content edits are new revisions.** After editing a managed document, run `somnus bump PATH --reason "..."`. Re-indexing an edited file at an unchanged revision opens a `revision` conflict (SPEC section 18.3), and `somnus bump` is what resolves it.
- **Lifecycle changes go through `somnus status`**, never by editing `lifecycle.status` by hand.
- **Changing a ratified decision** must not silently replace its rationale. `AGENTS.md` requires a new ratified decision for a material change; the closing paragraph of `DECISIONS.md` also requires a new document revision and a matching SPEC release under section 23.

SPEC section 23 defines what kind of release a change is:

| Change | Release type |
| --- | --- |
| Add an optional feature | Minor |
| Remove an enum value | Major |
| Tighten a pattern | Major |
| Change a field's meaning | Major |

A core metadata release change requires updating `CORE_SCHEMA` in `src/somnus/__init__.py`, the schema tree in `src/somnus/model/schema.py`, and the conformance tests: a core-2.0.0 validator rejects other schema URIs with `E_SCHEMA`. A package or registry version change does not automatically change the core schema. D19 in `DECISIONS.md` is the example: package 2.1.0 and registry schema 2 add derived full-text search while artifact core stays 2.0.0. `SPEC.md` and `DECISIONS.md` advance their document revisions independently.

## Adding a conformance fixture

SPEC section 21 says each fixture row maps to a test in `tests/test_conformance.py`, numbered to match (`test_01_...` through `test_21_...`). A new row in the table needs a new numbered test in the same change. See [testing](testing.md).

## Related pages

- [How to contribute](index.md) for the definition of done
- [Design decisions](../background/design-decisions.md) for D1 to D19
- [Lifecycle and revisions](../features/lifecycle-and-revisions.md) for `bump` and `status`
