# Package release and installation

## Distribution identity

- Package index: PyPI, https://pypi.org/project/somnus-metadata/
- Distribution: somnus-metadata. Python package and console command: somnus.
- Current toolkit release: 2.0.0; metadata core is 2.0.0.
- The first 0.1.0 upload was a stale-metadata versioning error, not v1 canon.
- PyPI project owner observed after publication: somnus.
- Do not publish as somnus: that PyPI name belongs to an unrelated project.
- Install in an isolated tool environment; the unrelated somnus package also
  owns the import/command names and must not share that environment.

## User install

```sh
uv tool install somnus-metadata
somnus --version
somnus init --root /path/to/project
somnus edit
```

Alternative: `pipx install somnus-metadata`. For an existing application venv,
`python -m pip install somnus-metadata`. MCP clients launch `somnus mcp`.
The distributable agent plugin remains separate and deferred pending official
host-agnostic integration materials.

## Release procedure

1. Inspect source changes; preserve unrelated working-tree state. A package
   publication is not a Git commit, tag, repository visibility change, or license
   decision. No open-source license grant has been declared for release 0.1.0.
2. Update toolkit versions consistently in pyproject.toml and somnus.__version__
   for a NEW release. Never overwrite a published version. Core schema release
   changes follow SPEC independently.
3. Run native unit/conformance tests, semantic checks, mypy, selected lint,
   configured hooks/import contracts, installed-package acceptance, and Doctor
   diagnostic comparison. Document dispositions and unrun platform checks.
4. Build with `uv build --no-sources --out-dir dist`. Inspect both the source
   archive and wheel. MANIFEST.in excludes operator/session/research materials.
   Keep source distribution rebuildability and packaged db/schema.sql intact.
5. Run `uvx --from twine twine check --strict dist/*`.
6. Exercise the EXACT release wheel outside the checkout with isolated
   SOMNUS_HOME, real files/SQLite, CLI, MCP and terminal consumers.
7. Use the existing credential store with
   `uvx --from twine twine upload --non-interactive dist/<wheel> dist/<sdist>`.
   This uses ~/.pypirc; never paste its contents or a token into chat, source,
   logs, CLI arguments, or GitHub secrets by implication. If authorization
   fails, stop publication and report the exact boundary.
8. Verify the PyPI JSON release metadata, both file digests and fresh installation
   from the public index without source-path injection. Update PLAN.

The existing release.yml is a GitHub Release workflow, NOT an automatic PyPI
publisher. Trusted Publishing is a possible later improvement requiring the
actual PyPI/GitHub publisher binding; its existence is not implied here.
Keep future dev/build dependency updates at least seven days old per CONTRIBUTING.

## 2.0.0 correction (2026-10-24 UTC)

The operator corrected the intended release version. Source/runtime metadata and
acceptance assertion now agree on 2.0.0; no algorithm or schema changed.
Exact release wheel: 60/60 acceptance checks; 476 tests; semantic 0/0; mypy clean;
strict twine metadata and archive privacy checks passed. Both v2 files uploaded:
https://pypi.org/project/somnus-metadata/2.0.0/
Run artifacts: /tmp/somnus-v2-release-ednql0pq/runs/20261024T045338Z/.
Fresh no-cache public-index tool installation succeeded: somnus 2.0.0.
PyPI current-version API reports 2.0.0; both artifact hashes match local dist.
Wheel SHA256: 39e16de7e5187fce3d0a091f48eebc28b00b860e18bfd8cb578933a52664ac8a
Source SHA256: dfdd9fe824e1d187923d8ab4fed1c6640e186e4d1c9688363c8ddc358b8163ae
Yanking 0.1.0 was not possible through the connected surface: no browser was
available for release management. Do not claim it yanked or deleted.

## 0.1.0 actual publication evidence (2026-10-24 UTC)

- Uploaded successfully to https://pypi.org/project/somnus-metadata/0.1.0/
  using existing local credentials; GitHub repository remains private.
- Wheel: somnus_metadata-0.1.0-py3-none-any.whl
  SHA256 ebae3b9860a47e35319e8a17e664235b0ddb0d49974ba56bc42cb3412c80d058
- Source archive: somnus_metadata-0.1.0.tar.gz
  SHA256 600c81ed0b2c00eecca5d7109339118496597c84a0fb5a5ac8c0996d9e532f23
- PyPI reported both exact digests matching local dist files.
- Artifact audit: 55 wheel entries; 61 source-archive files; only runtime source,
  SQL schema, README, build configuration and generated package metadata.
  Zero runtime dependencies. Wheel built from the source distribution.
- 476 tests passed; semantic 0 errors/0 warnings; mypy 49 files clean; configured
  Ruff selection passed; strict twine check passed for both artifacts.
- Source-copy acceptance: 60/60. Exact release wheel acceptance: 60/60;
  artifacts /tmp/somnus-release-acceptance-3ikl8mdt/runs/20261024T044719Z/.
- Fresh public-index install into /tmp/somnus-pypi-verify-20261024 succeeded
  without cache; command printed somnus 0.1.0; import resolved inside that venv;
  installed metadata confirmed somnus-metadata 0.1.0 and zero runtime deps.
- Doctor rescan: 49 files, 371 findings, 0 critical, 70 serious, exit 1.
  No production Python changed during packaging. Prior dispositions in PLAN
  remain evidence with their own review limits, not a claim of a green scan.
- Windows native terminal behavior and hosted CI were not exercised here.
- No source commit, tag, GitHub push, visibility change or plugin publication
  was performed. Build/egg-info/dist are generated artifacts; do not confuse
  their missing Surgeon-write receipts with source changes.
