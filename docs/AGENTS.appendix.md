# Global `AGENTS.md` Appendix for Somnus Metadata

Copy the single fenced Markdown block below and paste it into your global agent instruction file (`~/.factory/AGENTS.md` for Factory Droid, `~/.codex/AGENTS.md` for Codex CLI, `~/.config/opencode/AGENTS.md` for OpenCode, or your global Google Antigravity rules).

Why this block is needed: installing `somnus-metadata-plugin` registers the `somnus-metadata` skill and the `somnus-metadata` MCP server in each host, but an agent only activates a skill or calls an MCP tool before writing a new document if its always-on instructions tell it that the global registry exists. This block is kept compact so it fits cleanly inside your always-on prompt budget.

````markdown
## Somnus Metadata — Global Document and Artifact Registry

A global Somnus Metadata SQLite registry (`~/.somnus/somnus.db`, core `somnus://metadata/core/2.0.0`) tracks documents, source files, configurations, and sidecar-backed artifacts across registered repositories. Two equivalent surfaces reach it:

- **MCP server `somnus-metadata`**: 16 tools (`q`, `ls`, `check`, `stamp`, `new`, `set`, `status`, `bump`, `index`, `stale`, `fork`, `regions`, `migrate`, `schema`, `init`, `brief`).
- **CLI `somnus`** (alias `somnus-metadata` in 2.1.0+): identical subcommands and flags (`~/.local/bin/somnus`). Activate the `somnus-metadata` skill when available, or run `somnus brief` (MCP: `brief`) for the live command table.

### Proactive use

1. **Search before creating.** Before creating a new specification, plan, decision record, runbook, report, or architecture record, search the registry with `q --text "key words"` (every word must match; `word*` is a prefix) and `ls --type TYPE` or `ls --tag TAG`. If a matching artifact exists, extend or `fork` it instead of creating a duplicate.
2. **Adopt files the operator wants tracked.** Unmanaged files are invisible to `ls` and `q --text`. Preview adoption with `stamp /abs/file`, then apply with `stamp /abs/file --write` (inserts frontmatter in Markdown, a comment envelope in code/config while preserving host bytes, or a `<file>.somnus.yaml` sidecar for any other file type).
3. **Validate after edits.** After editing any managed file, run `check /abs/file --level semantic`.
4. **Close substantial doc work with a health check.** Run `index`, `q --conflicts`, and `stale`.

### Hard rules

- **Never hand-edit `somnus:` headers or invent metadata.** Never hand-edit `id`, `revision`, `lifecycle.status`, `authority`, or `time`, and never fabricate dates, actors, licenses, evidence, or acceptance records.
- **Use the owning commands for mutations:**
  - Header fields (`title`, `summary`, `purpose`, `classification.{category,type,role,scope,tags}`, `access.visibility`, `ingestion.disposition`): `set /abs/file "title=..." "classification.tags=a, b" --reason "..."` (always write `classification.tags=`, never bare `tags=`).
  - Lifecycle transitions: `status /abs/file NEW_STATUS --reason "..."` (`superseded` requires `--replacement URN`).
  - Body edits on an indexed file: `bump /abs/file --reason "..."` so the next `index` does not open a `revision` conflict.
- **Always pass absolute paths to MCP tools.** Relative paths resolve against the MCP server's working directory.
- **Full operator and agent guide:** `/home/daeron/Repositories/somnus-metadata/docs/USAGE_GUIDE.md`.
````
