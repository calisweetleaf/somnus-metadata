"""Diagnostics, compiler-style rendering, tables, and process exit codes."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterable, Literal, Sequence

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_USAGE = 2

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class Diagnostic:
    """One finding, addressed by file position and dotted payload field path."""

    path: str
    line: int
    col: int
    severity: Severity
    code: str
    field: str
    message: str

    @property
    def is_error(self) -> bool:
        """Return True when the diagnostic is an error rather than a warning."""
        return self.severity == "error"


class SomnusError(Exception):
    """Operation refused; carries diagnostics and the exit code to return."""

    def __init__(self, diagnostics: Sequence[Diagnostic] | str, exit_code: int = EXIT_INVALID):
        if isinstance(diagnostics, str):
            diagnostics = [Diagnostic("-", 0, 0, "error", "E_IO", "-", diagnostics)]
        self.diagnostics = list(diagnostics)
        self.exit_code = exit_code
        super().__init__("; ".join(d.message for d in self.diagnostics))


def _clean(value: str) -> str:
    return value.replace("\t", " ").replace("\r", " ").replace("\n", " ")


def render_one(d: Diagnostic, fmt: Literal["text", "tsv"] = "text") -> str:
    """Render a single diagnostic line in text or TSV form."""
    if fmt == "tsv":
        return "\t".join(
            [_clean(d.path), str(d.line), str(d.col), d.severity, d.code, _clean(d.field), _clean(d.message)]
        )
    return f"{d.path}:{d.line}:{d.col}: {d.severity} {d.code} {d.field}: {d.message}"


def render(diagnostics: Iterable[Diagnostic], fmt: Literal["text", "tsv"] = "text") -> str:
    """Render diagnostics sorted by path, line, column; one per line."""
    ordered = sorted(diagnostics, key=lambda d: (d.path, d.line, d.col, d.code, d.field))
    return "\n".join(render_one(d, fmt) for d in ordered)


def has_errors(diagnostics: Iterable[Diagnostic]) -> bool:
    """Return True when any diagnostic is an error."""
    return any(d.is_error for d in diagnostics)


def table(headers: Sequence[str], rows: Sequence[Sequence[object]], fmt: Literal["text", "tsv"] = "text",
          max_width: int = 60) -> str:
    """Format rows as an aligned plain-text table or header-first TSV."""
    cells = [["" if v is None else _clean(str(v)) for v in row] for row in rows]
    if fmt == "tsv":
        return "\n".join(["\t".join(headers)] + ["\t".join(r) for r in cells])
    clipped = [[c if len(c) <= max_width else c[: max_width - 1] + "\u2026" for c in r] for r in cells]
    widths = [len(h) for h in headers]
    for r in clipped:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))
    def line(values: Sequence[str]) -> str:
        return "  ".join(v.ljust(widths[i]) for i, v in enumerate(values)).rstrip()
    out = [line(headers), line(["-" * w for w in widths])]
    out.extend(line(r) for r in clipped)
    return "\n".join(out)


def emit(text: str, stream=None) -> None:
    """Write text plus newline to stdout (or stream), skipping empty output."""
    if not text:
        return
    target = stream or sys.stdout
    target.write(text if text.endswith("\n") else text + "\n")
