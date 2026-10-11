"""``somnus brief``: a Markdown cheat sheet for agent instruction files."""

from __future__ import annotations

from somnus import CORE_SCHEMA
from somnus.commands._common import Ctx
from somnus.output import EXIT_OK, emit

BRIEF = f"""## Somnus metadata (core `{CORE_SCHEMA}`)

Normative contract: `SPEC.md`. Every managed file carries exactly one `somnus:` envelope
(Markdown frontmatter, a comment envelope in code/config files, or a `<file>.somnus.yaml` sidecar).

**Rules for agents**

- Never hand-invent IDs, dates, actors, licenses, evidence, or acceptance records.
- Never edit `id`. Any change to the header or body that should be indexed is a new `revision` (`somnus bump`).
- Lifecycle changes go through `somnus status`, never by editing `lifecycle.status` directly.
- Unknown fields are errors. Put tool-specific data under `extensions.<owner>`.
- Region markers (`<!-- somnus:region:begin r-id -->` â€¦ `end`) carry identity only; register them with
  `somnus regions PATH --sync --write`.
- `normative` role is intent, not acceptance. Only `authority.standing: accepted` with an acceptance
  record is authoritative.

**Commands**

| Need | Command |
| --- | --- |
| New document | `somnus new TYPE "Title" [--dir DIR]` |
| Adopt an existing file | `somnus stamp PATH` (diff) then `--write` |
| Validate | `somnus check PATHâ€¦ [--level core\\|semantic\\|canon]` |
| Change status | `somnus status PATH NEW_STATUS [--reason â€¦] [--replacement URN]` |
| New revision | `somnus bump PATH [--reason â€¦]` |
| Derive a copy | `somnus fork PATH [--title â€¦]` |
| Upgrade v0.1 | `somnus migrate PATH` then `--write` |
| Registry | `somnus index`, `somnus ls`, `somnus q --docs\\|--conflicts\\|--history`, `somnus stale` |
| Field docs | `somnus schema classification.type` |

Exit codes: `0` ok, `1` validation errors/refusals/conflicts, `2` usage or I/O errors.
"""


def run(args, ctx: Ctx) -> int:
    """Print the cheat sheet."""
    emit(BRIEF)
    return EXIT_OK
