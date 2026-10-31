# Fun facts

A few things about somnus-metadata that stood out while measuring it. Current measurements use committed HEAD `27408fa` on 2026-10-31 UTC; historical observations retain their original commit references. For the full figures, see [by the numbers](by-the-numbers.md) and [lore](lore.md). For what the project is, start at [the overview](overview/index.md).

## The retired specification is still longer

The retired `archive/v0.1/SOMNUS-METADATA-SPEC-v0.1.md` has 1,287 physical lines. The normative spec that replaced it, `SPEC.md`, is 961 lines. The same pattern holds for the validator: the archived `archive/v0.1/tools/validate.py` is 1,115 lines, while its replacement `src/somnus/model/validate.py` is 844. Both replacements remain shorter than the retired versions, even after the current spec added content-search requirements.

## Zero TODOs in live code

Running `rg -n -i "TODO|FIXME|XXX|HACK" src tests` returns exactly one hit, and it isn't a TODO. It is line 15 of `src/somnus/infer.py`, the regex `(r"task|todo", "task")`, which infers the `task` role from a filename. The v0.1 draft of `DECISIONS.md` was the opposite: every one of its five decisions carried a `TODO(needs-owner)` marker until the 2.0.0 ratification.

## The registry forbids JSON, but two commands have to speak it

Decision D4 in `DECISIONS.md` says "JSON IS FORBIDDEN, IT IS SLOW ON INFERENCE" and bans JSON from the registry entirely: no JSON columns, and query output is aligned text or TSV. Yet `somnus schema --json-schema`, implemented in `src/somnus/commands/schema.py`, exports a JSON Schema Draft 2020-12 document, because that is the format the JSON Schema standard requires. D4 lists this as one of only two places JSON is allowed, the other being json-pointer selectors into JSON host files. The MCP server added in `43ab360` brought a third: the protocol's stdio transport is JSON-RPC, so `somnus mcp` speaks JSON on the wire. D17 accepts that under the same "where a format requires it" reasoning, and `src/somnus/mcp.py` keeps each tool result's content as the CLI's plain text or TSV. The three retired v0.1 schemas remain in `archive/v0.1/schemas/v1/`, but they are not an inventory of every JSON configuration file in the repository. Runtime implementation remains Python plus `src/somnus/db/schema.sql` and `src/somnus/db/search.sql`.

## Search fits in twelve lines of SQL

The new `src/somnus/db/search.sql` is just 12 physical lines, including comments and blanks. It delegates tokenization to SQLite FTS5 with `porter unicode61 remove_diacritics 2`; `src/somnus/commands/query.py` asks SQLite for BM25 ranking and excerpts. No Python runtime dependency was added to `pyproject.toml`. The size of the DDL is not the size of the feature: `src/somnus/db/store.py` owns extraction, backfill, and removal of derived rows. D19 in `DECISIONS.md` explicitly keeps this searchable copy from becoming a source of truth. See [querying](features/querying.md).

## The mojibake was there from the first spec commit

When `SPEC.md` was first committed in `db1fd5a` (2026-10-11 06:26), 33 of its lines already contained `â€`, the cp1252 rendering of a UTF-8 dash. By `8f0db0d` at 07:05, the count of affected lines had grown to 69 across 11 files, spreading into `DECISIONS.md`, `AGENTS.md`, and source docstrings. The cause was a Windows cp1252 decoding step in the edit tool, which double-encoded every non-ASCII character it wrote. Commit `dc3c981` at 08:38 repaired 26 files with exactly 168 lines added and 168 removed. Between those two commits, the unit tests added in `8f0db0d` found four real bugs: `|+` keep-chomp at end of file, slug transliteration, `--` escaping inside HTML comments, and the final terminator in `body_digest`. More on encoding traps is in [pitfalls](background/pitfalls.md).
