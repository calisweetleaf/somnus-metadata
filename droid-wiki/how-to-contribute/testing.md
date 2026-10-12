# Testing

The test suite is 12 stdlib `unittest` modules under `tests/` with 443 test methods, run with `python -m unittest discover -s tests`. One module, `tests/test_conformance.py`, is the executable form of the SPEC section 21 conformance table; the rest are unit and end-to-end suites per subsystem.

## Running

```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests
```

A full run takes about 3 seconds. In PowerShell 5.1 the command reports exit code 1 whenever anything is written to stderr, even when the summary says `OK`, so read the final `Ran 443 tests ... OK` line instead of `$LASTEXITCODE`. To run one suite: `python -m unittest tests.test_yamlsub`.

## Suites

Counts are `def test_` occurrences per file.

| File | Tests | Lines | Covers |
| --- | --- | --- | --- |
| `tests/test_validate.py` | 80 | 693 | Validation pipeline: levels, diagnostic codes, field paths, usage policy (SPEC 19) |
| `tests/test_yamlsub.py` | 75 | 449 | Restricted YAML subset: strict parser, lenient mode, spans, canonical serializer (SPEC 16) |
| `tests/test_tui.py` | 42 | 493 | Terminal UI widget logic, key decoding, frame diffing, header form model |
| `tests/test_regions.py` | 41 | 295 | Region markers: pairing, inert contexts, spacing, headings, TeX labels, registry sync (SPEC 13) |
| `tests/test_carriers.py` | 40 | 404 | Envelope extraction, insertion, preambles, host preservation (SPEC 17) |
| `tests/test_document.py` | 35 | 335 | Document loading, byte-preserving atomic saves, digests, positions (SPEC 16.3, 17, 18.3) |
| `tests/test_config.py` | 28 | 198 | Configuration precedence and validation (SPEC 18.1, 20) |
| `tests/test_ids.py` | 24 | 181 | UUIDv7 minting, Somnus URNs, legacy references, slugs (SPEC 3.1) |
| `tests/test_commands.py` | 21 | 317 | End-to-end CLI workflows through `somnus.cli.main` in temporary homes |
| `tests/test_conformance.py` | 21 | 365 | One test per SPEC section 21 fixture |
| `tests/test_lifecycle.py` | 21 | 193 | Lifecycle state machine against a transcription of the SPEC 7.1 table |
| `tests/test_store.py` | 15 | 188 | Registry store and the indexing semantics of SPEC 18.3 |
| **Total** | **443** | **4,111** | |

## Patterns worth knowing

### Temporary `SOMNUS_HOME`

No test touches the real `~/.somnus/somnus.db`. `CliCase.setUp` in `tests/test_commands.py` creates a temp directory, saves the current `SOMNUS_HOME`, points `SOMNUS_HOME` at `<tmp>/home`, and changes the working directory into the temp tree. `tearDown` restores the working directory and the environment variable (removing it if it was unset) and deletes the tree. The helper `cli(*argv)` calls `somnus.cli.main` with redirected stdout and stderr and returns `(exit_code, stdout, stderr)`; `ok(*argv)` asserts exit 0. `tests/test_config.py` uses the same save-and-restore pattern for `SOMNUS_HOME`, and `tests/test_store.py` opens a `Store` against a database path inside a temp directory.

### Byte preservation

Host-byte preservation (SPEC section 17, D8) is tested at the byte level:

- `tests/test_document.py` compares `path.read_bytes()` before and after saves, checks that CRLF files stay CRLF (`test_crlf_preserved`), that a JSON host next to a sidecar keeps its exact `b'{"a": 1}\r\n'`, that a leading BOM is accepted and never emitted, and that a final line without a newline survives.
- Tests that simulate a hand edit write with `write_text(..., encoding="utf-8", newline="")` (for example `tests/test_commands.py` lines 206, 247, 267 and `tests/test_store.py` lines 107, 124). `newline=""` stops Python from translating `\n` to `\r\n` on Windows, so the bytes on disk are exactly what the test intends and digests stay comparable.
- `CliCase.write` uses `write_bytes(text.encode("utf-8"))` for the same reason.

### Independent transcriptions

`tests/test_lifecycle.py` holds `SPEC_TABLE`, a copy of the SPEC 7.1 transition table typed in independently of `src/somnus/model/lifecycle.py`, and checks the implementation against it. This catches drift between spec and code rather than testing the code against itself.

### Conformance fixtures

`tests/test_conformance.py` has two classes. `TestConformance` covers fixtures that need no registry (1 to 12, 18, 21). `TestRegistryConformance` builds a temp registry for fixtures 13 to 17, 19, and 20. Test names carry the fixture number, for example `test_14_same_revision_distinct_states_conflict` and `test_20_disappearance_is_not_a_tombstone`. A `payload()` helper returns a minimal valid core 2.0.0 payload that tests mutate with `copy.deepcopy`.

### Archived inputs

`tests/test_commands.py` reads v0.1 examples from `archive/v0.1/examples/` as migration inputs. This is the one sanctioned use of `archive/` from tests; `src/` never imports from it.

## What is not tested

The TUI tests cover pure logic (widgets, key decoding, frame diffs, the form model) with fake screens. The live terminal path in `src/somnus/tui/term.py` (raw mode through `termios`/`tty` or `msvcrt`/`ctypes`) has no automated test. See [cleanup opportunities](../cleanup-opportunities.md).
