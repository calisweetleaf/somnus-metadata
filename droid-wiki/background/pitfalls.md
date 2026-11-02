# Pitfalls

These are the ways a change in this repository most often goes wrong: corrupting host bytes, breaking identity or revision history, or tripping over Windows, PowerShell, and OneDrive portability constraints. Historical environment observations do not establish the current runner's setup.

## Host-byte preservation

Every write re-extracts the result and refuses with `E_HOST` unless the bytes outside the envelope are unchanged (D8, SPEC section 17; the check is in `src/somnus/document.py`). Code that writes files must keep that guarantee:

- Write with explicit bytes or `newline=""`. Python's default text mode on Windows turns `\n` into `\r\n`, which changes every line outside the envelope. Tests use `write_text(..., encoding="utf-8", newline="")` or `write_bytes` for this reason.
- Preserve the detected newline style (`doc.newline`), a missing final newline, and trailing whitespace. A leading BOM is accepted on read and never emitted.
- Do not "tidy" host frontmatter keys next to `somnus:`. They belong to the host (D1).
- If a host cannot hold an envelope safely (multi-line XML declaration or DOCTYPE, a payload containing `--` or `*/`), the answer is a `<file>.somnus.yaml` sidecar, not a weaker check.

Follow [runbooks/host-write-incident.md](https://github.com/calisweetleaf/somnus-metadata/blob/main/runbooks/host-write-incident.md) for `E_HOST` incidents and [runbooks/registry-recovery.md](https://github.com/calisweetleaf/somnus-metadata/blob/main/runbooks/registry-recovery.md) for registry backup and reconciliation. Never bypass preservation checks or append-only ledger triggers to clear an incident.

## Never edit `id`

The `id` is the artifact's identity across renames, copies, and formats. Changing it by hand makes the registry see a new artifact at an old path and opens an `identity` conflict. Copying another document's header duplicates its `id` and opens a `duplicate-id` conflict. Create documents with `somnus new`, and derive one from another with `somnus fork`, which mints a new UUIDv7 and records `derived_from`.

## Content changes are new revisions

Editing a managed file and re-indexing it at the same `revision` produces different digests for one artifact revision, which opens a `revision` conflict (SPEC section 18.3). Run `somnus bump PATH --reason "..."` after an edit; it also resolves the conflict.

## Lifecycle changes go through `somnus status`

Hand-editing `lifecycle.status` skips the SPEC 7.1 transition table, the required reasons for abandonment and reactivation, the replacement references required by `superseded`, and the reset of `accepted` standing to `candidate` on reactivation. `somnus status PATH NEW_STATUS --reason "..."` applies all of these and writes a new revision.

## Do not invent values

Tools never invent dates, actors, licenses, measurements, evidence, or acceptance records (D6, SPEC section 4.2), and contributors should not either. `somnus stamp` deliberately writes `time: {}`. A configured default standing of `accepted` is refused.

## OneDrive and WinError 5

`AGENTS.md` records a OneDrive-synced operator checkout where Surgeon's multi-file transactions (`multi_edit`, `prepare`/`commit`) fail with WinError 5. Preserve its one-file-per-call rule; this is not evidence that every checkout uses OneDrive or Windows. A failed transaction may leave prepared state; inspect the installed Surgeon's recovery interface before acting.

## Encoding

An earlier Surgeon session decoded its input as cp1252 and wrote it back as UTF-8, so every non-ASCII character (`§`, en dashes, arrows, `≥`) became mojibake such as `Â§` in 26 files. Commit `dc3c981` repaired them. A historical `PYTHONUTF8=1` server setting is not a current repository declaration or proof of this runner's encoding. Two related traps remain:

- Windows PowerShell 5.1 `Get-Content` reads files as the ANSI code page unless given `-Encoding UTF8`, so correct files can look corrupted in a terminal. Check bytes before "fixing" anything.
- The toolkit refuses non-UTF-8 files for embedded carriers (`E_IO file is not valid UTF-8`); they need a sidecar.

## Line endings

`.gitattributes` sets `* text=auto eol=lf`, so git stores and checks out LF. The toolkit preserves whatever a file actually contains, including CRLF. Tests that need CRLF build it explicitly (the `crlf()` helper in `tests/test_document.py`) instead of relying on the checkout.

## PowerShell exit codes and stderr

Some Windows PowerShell 5.1 wrappers treat native stderr as an error surface even when the process exits 0. Unittest writes its progress and summary to stderr; inspect both the final `OK` or `FAILED` line and the native `$LASTEXITCODE` rather than equating stderr with failure. `somnus` also writes informational notes (`checked N file(s)...`, `registry: ...`) to stderr. PowerShell 5.1 lacks `&&` and `||`; chain with `;` and test `$LASTEXITCODE`.

## Digest changes

Before commit `8f0db0d`, `body_digest` dropped the final line terminator of the body. The fix changed the digest of every body that ends in a newline, so a registry indexed before that commit holds different stored values from what the current code computes for the same file. Incremental indexing skips files whose `(file_mtime, file_size)` is unchanged, so the mismatch usually appears on `somnus index --full` or after the file is touched; re-index into a fresh `SOMNUS_HOME` when in doubt. Any future change to canonical serialization or digest normalization has the same effect and should be treated as a registry-affecting change.

## Search is a snapshot

`src/somnus/db/store.py` indexes managed locations, not every file under a root. Adopt an unmanaged file with `somnus stamp` before expecting search results. `somnus q --text` reads the last indexed state; run `somnus index` after changes or `somnus index --full` when timestamps and sizes may be misleading. Binary/non-UTF-8 sidecar hosts have searchable metadata but an empty body, and body text is capped at 1,000,000 characters.

Schema-1 writers refuse a schema-2 registry (D19 in `DECISIONS.md`). Back up before upgrading; do not lower `PRAGMA user_version` to bypass the guard or treat a search hit as proof that a revision is conflict-free. A missing FTS5 index causes an exit-2 usage error, not permission to rewrite the database. See [Registry](../systems/registry.md) and [Debugging](../how-to-contribute/debugging.md).

## Doctor false positives

Scanning from the repository root with `.somnus-debug/python_doctor.yaml` reports every `somnus.*` import as missing. Use `.somnus-debug/python_doctor.src.yaml` with scan root `src` for import checks. See [tooling](../how-to-contribute/tooling.md).

## Archive imports

Nothing under `src/` may import from `archive/` (D15), and nothing there is normative. The v0.1 examples are used only as migration test inputs.
