# Development workflow

Changes follow a short loop: read the relevant `SPEC.md` section, edit one file at a time, run the test suite, check the managed documents, and commit on `main`. Changes to the standard itself carry extra obligations because `SPEC.md` and `DECISIONS.md` are Somnus-managed artifacts with their own revisions.

## The loop

1. **Orient.** Find the governing rule in `SPEC.md` (sections 3 to 13 for fields, 16 and 17 for carriers, 18 for the registry, 19 for validation, 20 for the CLI). `filetree.md` maps where code lives; [architecture](../overview/architecture.md) explains the layers.
2. **Branch (optional).** The project commits directly to `main`. A local topic branch is fine for longer work but is not required.
3. **Edit.** Use the Surgeon tool, one file per call (see [tooling](tooling.md)). Multi-file Surgeon transactions fail with WinError 5 in this OneDrive-synced folder.
4. **Test.** Run the suite from the repository root:

   ```powershell
   $env:PYTHONPATH="src"; python -m unittest discover -s tests
   ```

   For one suite, use `python -m unittest discover -s tests -p test_validate.py` with the same `PYTHONPATH` (`tests/` is not a package, so `tests.test_validate` does not import).
5. **Check documents.** `somnus check SPEC.md DECISIONS.md --level semantic` (or `python -m somnus.cli check ...` without an installed tool).
6. **Doctor.** Run somnus-debug with both configs when Python code changed and disposition any new serious finding.
7. **Commit.** Use a conventional prefix that matches the history: `feat:`, `fix:`, `test:`, `docs:`, `chore:` (for example `fix: repair double-encoded UTF-8 (cp1252 mojibake) in 26 files`).

## When the code and the spec disagree

`SPEC.md` is normative. If a test or a user report shows the toolkit doing something the spec does not say, the default fix is in `src/somnus/`. Only change the spec when the spec itself is wrong or incomplete, and do that as a deliberate step before touching code.

## Changing the standard

`SPEC.md` and `DECISIONS.md` both carry `somnus:` headers, so the toolkit applies its own rules to them:

- **Content edits are new revisions.** After editing a managed document, run `somnus bump PATH --reason "..."`. Re-indexing an edited file at an unchanged revision opens a `revision` conflict (SPEC section 18.3), and `somnus bump` is what resolves it.
- **Lifecycle changes go through `somnus status`**, never by editing `lifecycle.status` by hand.
- **Changing a ratified decision** requires a new revision of `DECISIONS.md` and a matching SPEC release under section 23. The closing paragraph of `DECISIONS.md` states this rule.

SPEC section 23 defines what kind of release a change is:

| Change | Release type |
| --- | --- |
| Add an optional feature | Minor |
| Remove an enum value | Major |
| Tighten a pattern | Major |
| Change a field's meaning | Major |

Because a 2.0.0 validator accepts only `somnus://metadata/core/2.0.0` and rejects other releases with `E_SCHEMA`, any release bump also means updating `CORE_SCHEMA` in `src/somnus/__init__.py`, the schema tree in `src/somnus/model/schema.py`, and the conformance tests.

## Adding a conformance fixture

SPEC section 21 says each fixture row maps to a test in `tests/test_conformance.py`, numbered to match (`test_01_...` through `test_21_...`). A new row in the table needs a new numbered test in the same change. See [testing](testing.md).

## Related pages

- [How to contribute](index.md) for the definition of done
- [Design decisions](../background/design-decisions.md) for D1 to D17
- [Lifecycle and revisions](../features/lifecycle-and-revisions.md) for `bump` and `status`
