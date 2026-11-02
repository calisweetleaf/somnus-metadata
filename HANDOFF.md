# HANDOFF — finish Somnus Metadata end to end (2026-11-01)

Paste everything below the line into a fresh agent session (Droid or Codex) started in
`/home/daeron/Repositories/somnus-metadata`. It is self-contained.

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