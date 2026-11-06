---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19a67-78be-745c-b7a2-ded39bc0328a"
  revision: 16
  title: "HANDOFF — finish Somnus Metadata end to end (2026-11-01)"
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
      - target_ref: "urn:somnus:artifact:01a19a67-78be-745c-b7a2-ded39bc0328a"
        aspects: ["content"]
  time:
    updated_at: "2026-11-06T23:33:04+00:00"
  names:
    slug: "handoff-finish-somnus-metadata-end-to-end-2026-11-01"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19a67-78be-745c-b7a2-ded39bc0328a"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# HANDOFF — finish Somnus Metadata end to end (2026-11-01)

## Complete v2 integration follow-through: 2026-11-06

PR #11 completes the full archive comparison after PR #10's runtime repair.
Every supplied file is now accounted for. Five configuration sidecars moved
inline through the toolkit, preserving IDs and host content; the missing
WHERE-WE-ARE handoff is restored with current publication status. See
[docs/INTEGRATION_AUDIT.md](docs/INTEGRATION_AUDIT.md) for the complete disposition.

Issue #5 is addressed: the legacy migration mapper is split by field family,
with 3,000 differential cases matching ordered payloads/errors and preserving
caller input. All 579 unit tests pass, coverage is 87.47%, mypy and configured
Ruff pass, all six import contracts pass, and semantic checks are clean. Final
wheel/source bytes match and strict Twine checks pass; final hosted validation
is attached to PR #11. The stale wiki PR #9 is closed because it removes metadata
headers and describes pre-D20 state. Factory wiki refresh is manual-only.

Publication of 2.2.1 and inspection/cleanup of untracked nested extraction folders
on the laptop remain blocked by publisher access and the offline laptop. No
local installation or machine cleanup is claimed. The older entries below
record their own earlier state and are superseded by this follow-through.

## Supplied revision correction: 2.2.1 (prepared, not published)

On 2026-11-06, independent comparison established that PyPI 2.2.0 exactly matches
main at 8768811 but omits changes present in the supplied branch ZIP. PR #10
restores the supplied heartbeat module and its daemon/TUI consumers, and filename
routing for .importlinter, .pre-commit-config.yaml and .ruff.toml. The unnecessary
TUI-to-watch import exception is removed. Later cross-platform test repairs are
retained; metadata core remains 2.0.0.

Verification: 579 unit tests, mypy 56 files, configured Ruff checks, all six import
contracts, 87.44% coverage, 77/77 installed-package acceptance checks (real SQLite,
MCP, watcher and POSIX PTY), strict Twine validation of wheel and sdist, and green
hosted CI and CodeQL on implementation commit d0ee1e0.

Plugin 1.3.0 exactly matches the supplied ZIP; native export and all 28 tests pass.
It remains private. Issues #2, #3, #4 and #6 were already resolved and are closed:
D18 removed the undefined warning, registry notes use the TUI status line, real
POSIX PTY tests exist, and the working documents have valid metadata headers.
Issue #5 remains the outstanding migration-function refactor.

PyPI 2.2.1 is NOT published: this cloud environment has no publishing credentials,
and the connected laptop is offline. Complete the existing release runbook with
the authorized publisher, verify public artifact hashes and a fresh installation,
then update the README publication status. No tag or GitHub Release was created.
The expired Factory subscription still blocks wiki refresh.

## Canonical D20 release — 2026-11-06

Operator authorized the supplied 2.2.0/D20 patch and plugin 1.3.0 as canonical,
including D20 ratification. Applied `patch/somnus-metadata-2.2.0-D20.patch`
directly in the backend; overlaid the supplied `somnus-metadata-plugin-1.3.0/`
payload in the sibling plugin repository. No compatibility fork was introduced.
The plugin's old `.gitignore.somnus.yaml` was removed because the canonical
payload embeds that same identity in `.gitignore`. Pre-existing archive/wiki
moves, research files, supplied folders and ZIPs remain outside release commits.

- PyPI **somnus-metadata 2.2.0** is published; wheel and sdist SHA256 values
  match the PyPI release API. Strict Twine validation passed for both.
- Global plain pip fetched **2.2.0** without cache from public PyPI; installed
  `somnus --version` reports 2.2.0 outside the checkout. Then `pip install
  somnus-debug` installed **0.1.0** in `~/.venvs/global`.
- Backend: **579 tests pass**, mypy **55 files clean**, configured Ruff selection
  passes, SPEC/DECISIONS semantic checks **0 errors / 0 warnings**.
- Source-built installed acceptance **77/77**; exact uploaded-wheel acceptance
  **77/77**, **0 failed / 0 not run**, including CLI, real files/SQLite, MCP,
  carriers/watcher and POSIX terminal consumers. Exact-wheel artifacts:
  `/tmp/somnus-exact-release-2.2.0-oi12ape7/runs/20261106T123507Z`.
- Plugin **1.3.0** native export check and **28 tests pass**. Only release repairs:
  removed an unused test import and narrowed two exception assertions to the
  actual `SomnusError`; runtime implementation remains the canonical patch.
- Doctor baseline/rescan cover **49 -> 55 source files**, **373 -> 439 findings**,
  **71 -> 103 serious**, **0 critical** in both. Delta exits **1**, not green.
  New findings include defensive parser/status fallbacks, lock/cleanup and
  watcher error handling, the argv-list/timeout service subprocess runner,
  a broad decoration-only TUI fallback, and the short JSON carrier class.
  These static findings are deferred for focused review, not suppressed or
  presented as runtime failures. No thresholds or scanning scope were weakened.
  Reports and the full delta: `/tmp/somnus-release-220/`.
- Initial `python -m build` used a different PATH interpreter without the build
  frontend; `uv build` successfully produced both artifacts. No source fix was
  needed. First lint run found the three test issues above; rerun passes.

Both main branches were committed and pushed with upstream tracking:
backend `5136ca9` and plugin `5514312`. Remote refs confirm those commits.
The uploaded wheel matches all **57 runtime files** in current source.
The GitHub backend push reported the existing required-check bypass while fresh
hosted checks had not completed; local gates above are independent evidence.
Plugin hosted CI **42219036607 passed**. Backend hosted CI exposed test-only
platform assumptions: fixture LF bytes were translated on Windows, pending-path
assertions did not resolve macOS/Windows aliases, the launchd dry-run expected a
Linux command string, and a Linux plan assertion hard-coded POSIX separators.
Commit `298517d` corrects the fixtures/assertions, with no runtime source change.
It also declares the exact authored TUI -> watcher status-read cross-link in
`.importlinter`; the watcher reuses stamp commands, just as the previously
sanctioned TUI -> command-context link does. No blanket exception or layer
removal was introduced. All **6 import contracts pass**; local statement/branch
coverage is **87.43%**, above the unchanged **85%** gate. Hosted backend rerun
**42219373561 passed** on implementation commit `298517d`: Linux Python
3.11–3.14, macOS/Windows Python 3.11 and 3.14, hooks/coverage, import contracts,
secret/policy guards and installed CLI acceptance all passed. No GitHub
release/tag was created.

The separate **Droid Wiki Refresh** workflow fails because the Factory service
returns **402 Payment Required: Organization does not have an active paid
subscription**. This external billing boundary is deferred; no workflow was
disabled and no billing/configuration mutation was attempted.

**Next boundary:** install the published plugin 1.3.0 through the native host
lifecycle, then prove installed/enabled records and live search. That installation,
any real-root inline migration, and enabling the global watcher are NOT RUN in
this release task. Physical Windows/macOS service execution is also NOT RUN.
No bulk adoption, user-root migration or daemon installation was authorized here.

## D20 implementation handoff — historical sandbox state (2026-11-05)

The following sandbox account predates canonical integration and publication; see the current release evidence above.

- Routing is now filename → pattern → extension → opt-in `"$somnus"` JSON → shebang
  (`src/somnus/carriers/__init__.py`). `CODEOWNERS`, `MANIFEST.in`, `Dockerfile`,
  `Makefile`, `.gitignore`, `.env*`, `requirements*.txt`, shebang scripts, `.jsonc`,
  `tsconfig*.json`, `.ipynb`, and ~50 more extensions embed instead of writing sidecars.
- New JSON-tree carriers (`carriers/jsonhost.py`): notebooks (`metadata.somnus`, always)
  and plain JSON (`"$somnus"`, opt-in via `stamp --inline` or `[carriers] json = "key"`).
- `somnus migrate --inline [--json-key]` moves old sidecars into their hosts (same id,
  revision + 1). This repo's own `CODEOWNERS` and `MANIFEST.in` were moved.
- `somnus watch` (foreground loop, `src/somnus/watch.py`) and `somnus daemon
  status|install|uninstall|stop|once` (`service.py`): stdlib polling, settle-before-stamp,
  auto-revise of in-place edits, single-instance lock, `watch.json` heartbeat shown in
  `daemon status`, the TUI browser header, and MCP (`daemon` tool). `watch` is not an
  MCP tool.
- Config gains `[carriers]` and `[watch]`; built-in excludes now cover virtualenvs,
  `site-packages`, `build/`, `dist/`, egg-info.
- Evidence: 579 unit tests OK; mypy clean (55 files); installed-wheel acceptance
  77/77 including the new carriers/watch phase.
- Historical next steps are superseded: D20 is now ratified and 2.2.0 published.
  Plugin installation is next; root migration and daemon installation require their own task scope.

## Production payload correction — 2026-11-02

Native plugin **1.2.1**, pushed as **35c228a**, no longer ships the development
checkout as the runtime. Both catalogs target native/somnus-metadata-plugin, a
checked-in reproducible export of exactly **8 runtime files**. Both installed
caches were inspected after clean native remove/install: **0 .somnus.yaml files**,
no package.json/.gitignore or Node development adapter code. SKILL.md retains its
embedded YAML frontmatter. Source indexing annotations are not runtime assets.
No other repositories or registry adoption were changed by this correction.
The build's --check and new packaging regression reject stale/unexpected export
files. **26 tests pass**, and hosted CI **41402125903** passed. The globally
installed/published backend remains **2.1.1**. No hooks were added or copied.

## Previous native-plugin verification — 2026-11-02

The operator caught a real verification error: a direct skill/MCP adapter was
reported as a native installed plugin. Those are different surfaces. Version
**1.2.0** of somnus-metadata-plugin now supplies the portable plugin.json/mcp.json,
Codex compatibility manifest and catalog, Factory manifest and catalog, and the
same shared skill. Plugin source is pushed as **4deee50**; **25 tests pass** and
hosted CI **41399524229** passed. The Python backend remains published/globally
pip-installed **2.1.1**; no backend code or PyPI release was changed in this fix.

Verified native identity: **somnus-metadata-plugin@somnus-metadata-plugin**.
- Codex plugin list reports installed=true, enabled=true, version **1.2.0**.
  Cache: /home/daeron/.codex/plugins/cache/somnus-metadata-plugin/somnus-metadata-plugin/1.2.0.
- Factory plugin list reports **Enabled**, **user**, commit **4deee507dc7a**.
  Cache: /home/daeron/.factory/plugins/cache/somnus-metadata-plugin-7b5df6c61269/somnus-metadata-plugin-7b5df6c61269/4deee507dc7a.
- Native remove/uninstall then install refreshed both caches. Factory's first
  reinstallation returned a settings-resolution error without changes; the next
  native install succeeded. No speculative settings repair was performed.
- Both native cached skill trees AND the requested Codex/Factory custom skill
  copies match the canonical shared source. Custom skill copies are compatibility
  projections; they are not evidence of native installation on their own.
- Duplicate direct user MCP entries were removed through Surgeon, retaining the
  custom skill copies. With those entries absent, fresh Codex and Factory sessions
  successfully called native-plugin MCP q(text="lifecycle", limit=1, tsv=true).
  Factory session **52dcef09-320e-4d43-851c-e60b1025cf83** returned the lifecycle.py
  source path. Codex returned the identical path through mcp__somnus_metadata__q.
  An earlier test that explicitly disabled that server name also disabled the
  plugin's same-named server; its empty-tool result was not counted as success.
- The Factory Superintelligence skill, its harness-customization guide and
  plugins/hooks references were used. Codex and Factory hook event/payload
  contracts remain distinct. This plugin declares no hooks; global hooks were
  not copied or changed. Native MCP uses actor somnus-metadata-plugin; legacy
  direct adapters retain their per-host actors.

Use native plugin lists plus native MCP execution to validate native installation.
The Node installer/doctor is explicitly labeled as a direct compatibility-adapter
surface; its success does not imply a native plugin record. Bulk file adoption
is not this task and must not resume without a new request.

## Superseded direct-adapter completion report — 2026-11-01

Finished means the software is released and installed, not that all files on the
machine have been adopted. The operator explicitly corrected this distinction.
The earlier cross-root adoption job and its zero-unmanaged acceptance criterion
below are superseded history. Do not resume them without a new request.

- PyPI latest and global plain-pip install: **somnus-metadata 2.1.1**.
  Fresh pip index verification and no-cache pip upgrade both confirm it.
- Both repository main branches were pushed with **git push -u origin main**.
- Shared host-agnostic plugin/skill: **1.1.1**, source commit **3000082**.
- Clean uninstall removed the owned Codex and Droid skills/MCP entries; the host
  inventory then confirmed both absent. Reinstall recreated them, with native
  configuration backups. Both fresh 16-tool / backend-2.1.1 handshakes and
  complete skill-tree fidelity checks pass.
- Codex cache inventory contained **no Somnus Metadata files**. This adapter uses
  direct skills plus MCP configuration, not that cache; unrelated plugins were
  not deleted. The fresh installed skill was read at both requested paths:
  /home/daeron/.codex/skills/custom/somnus-metadata/SKILL.md and
  /home/daeron/.factory/skills/somnus-metadata/SKILL.md.
- Fresh source gates: **537 tests pass**, semantic SPEC/DECISIONS **0 errors /
  0 warnings**, mypy **49 files clean**. Fresh plugin tests: **21 pass**.
- Prior exact uploaded-wheel acceptance remains **67/67**. No runtime change or
  new package version was introduced by this final reinstall/document correction.
- Fresh Codex and Factory MCP lifecycle queries both returned the same two real
  full paths. Factory session: 039db1c1-ba79-4868-919b-9c9c6f8fd137.
- The corrected release/install commission is complete; no adoption gate remains.

Existing cross-root metadata changes are preserved, not silently rolled back or
committed into unrelated projects. Their adoption count is not release readiness.
New host sessions load the refreshed skill; already-running sessions may retain
previously loaded context. No user application was forcibly restarted.

## Superseded adoption frontier (historical, not an active job)

Read the top of PLAN.md, not the original five-artifact baseline below.
The all-file discovery defect is fixed and released as **2.1.1** on PyPI,
installed via plain pip. Source tests **537**, installed acceptance **67**,
mypy **49 files**, and all four plugin handshakes are green. Core schema stays
2.0.0 and registry schema stays 2. No carrier or authored algorithm was replaced.

Five roots are registered with exclusions. Latest complete scan: **1,064 managed
hosts**, **23,148 unmanaged**, **0 invalid / 0 conflicts**.
**Documents (899 hosts) and Projects (4 hosts) are fully adopted** under those
exclusions. Their two nested Git repos were committed locally, not pushed.
The earlier core/plugin adoption commits are already pushed and CI passed.
The current patch release/source finalization is tracked in PLAN.md.
Plugin **1.1.1**, committed/pushed as **3000082**, updates the canonical shared
skill for host-agnostic use. Factory Droid, Codex, Antigravity and OpenCode all
have matching skill copies and fresh 16-tool handshakes against installed 2.1.1.
All 21 plugin tests and hosted CI passed. Droid read the installed skill and
successfully queried MCP; Codex independently queried MCP, but its attempted
Surgeon skill read was NOT RUN because that child could not find Surgeon.
Surgeon is available here by the absolute cached CLI path, not PATH. Do not
expand this into host-tool configuration changes; use the known path if needed.
The final expanded-corpus search proof and final skill/plugin alignment remain
part of completion, not an optional Codex-only afterthought.

**Still open:** 2,780 Repositories hosts, 19,736 LAB hosts and 632 Somnus-MCP hosts.
These counts now include sidecar-only files: do not return to the incomplete
embedded-carrier-only inventory. Use native
`Store.scan(...).unmanaged_paths` to get all paths; the CLI shows ten examples.
Keep the live Somnus-MCP data plane and generated dependency stores excluded.
Do not re-register nested roots; it creates duplicate observations. Preserve the
original exceptions and cross-repository commit/push limits below.

The original packet below is retained for history only. Its adoption objective and
"Done means" list do not govern the corrected release/install commission.

---

You are finishing Somnus Metadata for Daeron. Do the whole job in one session, without
asking for permission between steps. Stop only for a decision you truly cannot make
yourself, and when you do, say exactly which one.

## Verified state on 2026-11-01 (re-check it, don't re-derive it)

- **Backend:** PyPI `somnus-metadata` serves **2.1.0** (versions 2.1.0, 2.0.0, 0.1.0). It is
  installed with plain **pip** in `~/.venvs/global` (Python 3.14). `~/.local/bin/somnus` and
  `~/.local/bin/somnus-metadata` are links to that pip install, so non-interactive shells
  find it. No uv copy remains. `somnus --version` prints `somnus 2.1.0`.
- **Repo:** `main` is at `61412d8`, pushed, and CI is green. On 2026-11-01 the tests ran
  534/534 OK, the semantic check reported 0 errors, and the installed-package acceptance
  harness passed 66/66 (`~/.venvs/global/bin/python tests/acceptance/installed_package_acceptance.py`).
- **Files of any type still work:** `src/somnus/carriers/` has `markdown` (frontmatter),
  `linecomment` (py, sh, toml, yaml, ...), `blockcomment` (js/ts, rs, c, go, java, html/xml,
  ...), and `sidecar` (`<file>.somnus.yaml` for everything else, including binaries). The 176
  carrier, conformance, document, store, and command tests pass. Nothing in `src/` or
  `tests/` was deleted after 2026-10-15: `src/` gained 387 lines and lost 127 (edits in
  `store.py`, `validate.py`, `tui/app.py`, `query.py`, `document.py`, `yamlsub.py`), and
  the test count grew. Confirm this with `git log --since=2026-10-15 --stat -- src tests`
  before you claim anything was reduced or restored.
- **Plugin:** private repo `calisweetleaf/somnus-metadata-plugin` 1.1.0 at `34c0c95`, at
  `/home/daeron/Repositories/somnus-metadata-plugin`. It is installed for Droid
  (`~/.factory/skills/`), Codex (`~/.codex/skills/custom/`), Antigravity (`~/.gemini/skills/`),
  and OpenCode (`~/.config/opencode/skills/`). `node bin/somnus-plugin.mjs doctor` passes
  every host (16 tools each). Live MCP calls were proven from Droid and from `codex exec`.
- **Registry:** `~/.somnus/config.toml` has `roots = []`. Only 5 artifacts are indexed.
  **This is the unfinished work.**
- **Working tree:** these are Daeron's changes; leave them alone: `archives/*.zip` were
  deleted, and `archive/zip-archives/` and `SYMBOL-CRASH.md` are untracked.

## The job

1. **Confirm the install and the plugin are still healthy.** Run
   `~/.venvs/global/bin/pip install -U somnus-metadata` (pip only; this is not a uv
   project), `somnus --version`, and `node /home/daeron/Repositories/somnus-metadata-plugin/bin/somnus-plugin.mjs doctor`.
   If anything fails, fix it at the cause before going on.
2. **Index all of Daeron's files.** The roots are `~/Repositories` (20 repos, ~59k files),
   `~/LAB` (~25k), `~/Somnus-MCP` (~1.2k), `~/Documents` (~2k), and `~/Projects`. File
   counts exclude `.git`, `node_modules`, venvs, `__pycache__`, `dist`, `build`, `target`,
   and `.cache`.
   - First add those directories (and lock files, `*.pyc`, model weights, and archives you
     identify) to `[index].exclude` in `~/.somnus/config.toml`. Every remaining authored file
     is in scope.
   - Register each root with `somnus init --root DIR`, then run `somnus index` to get the
     list of untracked files.
   - Adopt them in batches with `somnus stamp PATH... --write` (stamp takes files, not
     directories; pass many paths per call). Let the carrier rules choose frontmatter,
     comment envelope, or sidecar. Never hand-write headers or invent IDs, dates, actors,
     or licenses.
   - **Before the bulk run**, stamp one sample of each kind and check the result:
     a Markdown file with existing frontmatter (for example a `SKILL.md` with
     `name`/`description`: those keys must survive and the skill must still load), a
     Python file with a shebang or encoding line, a TOML/YAML config, a JSON file, an
     HTML file, and a binary. If one is wrong, fix the backend in this repo first (see Rules).
   - Never stamp `Somnus Markdown Metadata Standard Research.md` (frozen evidence) or
     anything under `archive/`. Change `SPEC.md` and `DECISIONS.md` only through
     `somnus bump`/`status`.
   - An `E_HOST` refusal means the file was left untouched. Record each one in PLAN.md
     with its path, and keep going.
   - Commit the stamped files in each git repo with one commit per repo, using that repo's
     message style. Push only `calisweetleaf/somnus-metadata` and the plugin repo; for
     other repos, commit locally and list them in your report.
3. **Prove that agents can find things.** From Droid (its MCP tools) and from `codex exec`
   (its MCP tool, not the shell), run `q --text` for 3 known topics, `ls --type
   specification`, `stale`, and `q --conflicts`. Every search must return real hits. Resolve
   open conflicts with `bump` where that applies.
4. **Record it.** Update `PLAN.md` (top section): roots, counts adopted per root, E_HOST
   list, conflicts, and the search proof. Update `docs/USAGE_GUIDE.md` section 9 to match.

## Rules

- Edit local source and docs with Surgeon only (no shell redirects, `sed -i`, or
  apply_patch). Edit one file per call.
- Full feature fidelity: never delete, simplify, or stub existing behavior to make a step
  pass. A backend fix needs a test, and these must stay green:
  `PYTHONPATH=src python -m unittest discover -s tests`,
  `PYTHONPATH=src python -m somnus.cli check SPEC.md DECISIONS.md --level semantic`,
  `python -m mypy`, and the acceptance harness. A fix that ships means bumping the version
  in `pyproject.toml`, building, uploading with `~/.venvs/global/bin/twine` (credentials
  are in `~/.pypirc`), then `pip install -U somnus-metadata` and re-running the harness
  against the installed copy.
- Keep `pyproject.toml` runtime dependencies empty (stdlib only).
- Don't print secrets. `~/.config/opencode/opencode.jsonc` contains a Graphify bearer token;
  never echo it.

## Done means

All of these were run and shown, not described: the pip install is at the newest version;
the plugin `doctor` passes all hosts; every root is registered; the untracked count from
`somnus index` is 0 apart from recorded E_HOST files and deliberate excludes; searches from
Droid and Codex return hits; all gates are green; PLAN.md is updated; and the repos are
committed (and pushed where stated above).