"""In-body region markers: lexical scanning, pairing, and registry sync (SPEC §13)."""

from __future__ import annotations

import io
import re
import tokenize
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from somnus.ids import is_local_id

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_TEX_LABEL = re.compile(r"\\label\{([^}]*)\}")


@dataclass
class RegionRange:
    """A paired marker range (1-based inclusive marker lines)."""

    id: str
    begin_line: int
    end_line: int
    depth: int
    parent: Optional[str] = None


@dataclass
class MarkerScan:
    """Result of a marker scan: ranges plus (line, col, code, message) findings."""

    ranges: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)


def markdown_code_mask(lines: Sequence[str]) -> list[bool]:
    """Mark lines inside fenced code (fences included) and indented code blocks."""
    mask = [False] * len(lines)
    fence: Optional[str] = None
    prev_blank = True
    in_indented = False
    for i, line in enumerate(lines):
        if fence is not None:
            mask[i] = True
            m = _FENCE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
                fence = None
            prev_blank = False
            continue
        m = _FENCE.match(line)
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            fence = m.group(1)
            mask[i] = True
            in_indented = False
            prev_blank = False
            continue
        blank = not line.strip()
        indented = line.startswith("    ") or line.startswith("\t")
        if indented and not blank and (prev_blank or in_indented):
            mask[i] = True
            in_indented = True
        elif not blank:
            in_indented = False
        elif in_indented:
            mask[i] = True
        prev_blank = blank
    return mask


def _python_comment_lines(lines: Sequence[str]) -> Optional[set[int]]:
    """Return 0-based lines that are whole-line comments, or None if tokenizing fails."""
    source = "\n".join(lines) + "\n"
    eligible: set[int] = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                row, col = tok.start
                if not lines[row - 1][:col].strip():
                    eligible.add(row - 1)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return eligible


def _marker_pattern(style: tuple) -> tuple[re.Pattern, re.Pattern]:
    kind = style[0] if style else None
    if kind == "markdown":
        exact = re.compile(r"^<!-- somnus:region:(begin|end) (\S+) -->$")
        loose = re.compile(r"^\s*<!--\s*somnus:region:")
    elif kind == "prefix":
        bare = re.escape(style[1].rstrip())
        exact = re.compile(rf"^\s*{bare} somnus:region:(begin|end) (\S+)$")
        loose = re.compile(rf"^\s*{bare}\s*somnus:region:")
    elif kind == "block":
        exact = re.compile(r"^\s*/\* somnus:region:(begin|end) (\S+) \*/$")
        loose = re.compile(r"^\s*/\*\s*somnus:region:")
    else:
        raise ValueError("host has no in-body region markers")
    return exact, loose


def scan_markers(lines: Sequence[str], style: tuple, ignore: tuple[int, int] = (-1, -1),
                 host: Optional[str] = None) -> MarkerScan:
    """Scan live region markers, pairing them with a stack.

    ``ignore`` is a 0-based [start, end) span (the metadata envelope). Markdown
    code blocks are inert; for Python only real comment tokens are live.
    """
    scan = MarkerScan()
    if not style:
        return scan
    exact, loose = _marker_pattern(style)
    mask = markdown_code_mask(lines) if style[0] == "markdown" else [False] * len(lines)
    eligible = _python_comment_lines(lines) if host == "python" else None
    stack: list[tuple[str, int]] = []
    seen: set[str] = set()
    for i, raw in enumerate(lines):
        if ignore[0] <= i < ignore[1] or mask[i]:
            continue
        if eligible is not None and i not in eligible:
            continue
        line = raw.rstrip()
        m = exact.match(line)
        if not m:
            if loose.match(line):
                scan.issues.append((i + 1, 1, "E_REGION", "malformed region marker"))
            continue
        action, rid = m.groups()
        no = i + 1
        if not is_local_id(rid):
            scan.issues.append((no, 1, "E_REGION", f"region marker id {rid!r} is not a valid local ID"))
            continue
        if style[0] == "markdown":
            before = lines[i - 1].strip() if i > 0 and not (ignore[0] <= i - 1 < ignore[1]) else ""
            after = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if before or after:
                scan.issues.append((no, 1, "W_REGION_SPACING", "region markers should be separated by blank lines"))
        if action == "begin":
            if rid in seen:
                scan.issues.append((no, 1, "E_REGION", f"duplicate region marker {rid!r}"))
                continue
            seen.add(rid)
            stack.append((rid, no))
            continue
        if not stack:
            scan.issues.append((no, 1, "E_REGION", f"end marker {rid!r} has no matching begin"))
            continue
        if stack[-1][0] != rid:
            if any(s[0] == rid for s in stack):
                scan.issues.append((no, 1, "E_REGION", f"region {rid!r} crosses region {stack[-1][0]!r}"))
                idx = next(k for k, s in enumerate(stack) if s[0] == rid)
                stack.pop(idx)
            else:
                scan.issues.append((no, 1, "E_REGION", f"end marker {rid!r} has no matching begin"))
            continue
        _, begin = stack.pop()
        parent = stack[-1][0] if stack else None
        scan.ranges[rid] = RegionRange(rid, begin, no, len(stack), parent)
    for rid, begin in stack:
        scan.issues.append((begin, 1, "E_REGION", f"region {rid!r} is never closed"))
    return scan


def headings(lines: Sequence[str], ignore: tuple[int, int] = (-1, -1)) -> list[tuple[str, int]]:
    """Return (text, 1-based line) for ATX headings outside code and the envelope."""
    mask = markdown_code_mask(lines)
    out = []
    for i, line in enumerate(lines):
        if ignore[0] <= i < ignore[1] or mask[i]:
            continue
        m = _ATX.match(line)
        if m:
            out.append(((m.group(2) or "").strip(), i + 1))
    return out


def tex_labels(lines: Sequence[str], ignore: tuple[int, int] = (-1, -1)) -> list[tuple[str, int]]:
    """Return (label, 1-based line) for ``\\label{...}`` outside TeX comments."""
    out = []
    for i, line in enumerate(lines):
        if ignore[0] <= i < ignore[1]:
            continue
        code = re.split(r"(?<!\\)%", line, maxsplit=1)[0]
        for m in _TEX_LABEL.finditer(code):
            out.append((m.group(1), i + 1))
    return out


def sync_registry(somnus: dict, scan: MarkerScan) -> tuple[list[str], list[str]]:
    """Register unregistered marker ranges; return (added ids, registered-but-missing ids).

    Existing registry entries are never removed; missing markers are reported.
    """
    knowledge = somnus.setdefault("knowledge", {})
    regions: list[Any] = knowledge.setdefault("regions", [])
    registered = {r.get("id") for r in regions if isinstance(r, dict)}
    marker_names = {
        r.get("selector", {}).get("name")
        for r in regions
        if isinstance(r, dict) and isinstance(r.get("selector"), dict) and r["selector"].get("kind") == "marker"
    }
    added = []
    for rid in sorted(scan.ranges, key=lambda k: scan.ranges[k].begin_line):
        if rid in marker_names or rid in registered:
            continue
        regions.append({"id": rid, "kind": "section", "selector": {"kind": "marker", "name": rid}})
        added.append(rid)
    missing = sorted(n for n in marker_names if n and n not in scan.ranges)
    return added, missing
