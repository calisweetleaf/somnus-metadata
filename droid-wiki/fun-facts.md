# Fun facts

A few things about somnus-metadata that stood out while measuring it. Counts were taken on 2026-10-11 at commit `dc3c981`. For the full figures, see [by the numbers](by-the-numbers.md) and [lore](lore.md). For what the project is, start at [the overview](overview/index.md).

## The longest file is the one that was retired

The longest tracked file is `archive/v0.1/SOMNUS-METADATA-SPEC-v0.1.md` at 1,287 lines. The normative spec that replaced it, `SPEC.md`, is 908 lines. The same pattern holds for the validator: the archived `archive/v0.1/tools/validate.py` is 1,115 lines, while its replacement `src/somnus/model/validate.py` is 832. In both cases the 2.0.0 versions came out shorter than what they replaced.

## Zero TODOs in live code

Running `rg -n -i "TODO|FIXME|XXX|HACK" src tests` returns exactly one hit, and it isn't a TODO. It is line 15 of `src/somnus/infer.py`, the regex `(r"task|todo", "task")`, which infers the `task` role from a filename. The v0.1 draft of `DECISIONS.md` was the opposite: every one of its five decisions carried a `TODO(needs-owner)` marker until the 2.0.0 ratification.

## The registry forbids JSON, but one command has to emit it

Decision D4 says "JSON IS FORBIDDEN, IT IS SLOW ON INFERENCE" and bans JSON from the registry entirely: no JSON columns, and query output is aligned text or TSV. Yet `somnus schema --json-schema` exports a JSON Schema Draft 2020-12 document, because that is the format the JSON Schema standard requires. D4 lists this as one of only two places JSON is allowed, the other being json-pointer selectors into JSON host files. The only JSON files committed to the repository are the three retired v0.1 schemas in `archive/v0.1/schemas/v1/`.

## Where the names come from

"Somnus" is Latin for sleep and the name of the Roman god of sleep. The repository never explains the choice, so any link to the meaning is a guess. The operator's name is clearer. The v2 proposal is addressed as a "candidate for Daeron's adoption", the v0.1 spec mentions a working path under `/home/daeron/LAB/`, and the all-caps override quoted in D4 is the operator's message demanding "A GLOBAL .DB". The `DAERON-MESSAGE` label for that override does not appear anywhere in tracked history. Only the quoted text survived into `DECISIONS.md` in `df72af4`.

## The mojibake was there from the first spec commit

When `SPEC.md` was first committed in `db1fd5a` (2026-10-11 06:26), 33 of its lines already contained `â€`, the cp1252 rendering of a UTF-8 dash. By `8f0db0d` at 07:05, the count of affected lines had grown to 69 across 11 files, spreading into `DECISIONS.md`, `AGENTS.md`, and source docstrings. The cause was a Windows cp1252 decoding step in the edit tool, which double-encoded every non-ASCII character it wrote. Commit `dc3c981` at 08:38 repaired 26 files with exactly 168 lines added and 168 removed. Between those two commits, the unit tests added in `8f0db0d` found four real bugs: `|+` keep-chomp at end of file, slug transliteration, `--` escaping inside HTML comments, and the final terminator in `body_digest`. More on encoding traps is in [pitfalls](background/pitfalls.md).
