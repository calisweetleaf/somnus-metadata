"""Markdown carriers: YAML frontmatter and the hidden HTML comment envelope (SPEC §17.1–§17.2)."""

from __future__ import annotations

import re
from typing import Optional

from somnus.carriers import Envelope, Extraction, Issue, Splice
from somnus.regions import markdown_code_mask

HTML_OPEN = "<!-- somnus:metadata:v2"
HTML_CLOSE = "somnus:end -->"
_TOP_KEY = re.compile(r"[A-Za-z_$\"'][^:]*:(?:\s|$)")


def frontmatter_bounds(lines: list[str]) -> tuple[Optional[int], bool]:
    """Return (closing index, opened) for leading frontmatter."""
    if not lines or lines[0] != "---":
        return None, False
    for i in range(1, len(lines)):
        if lines[i] == "---":
            return i, True
    return None, True


class MarkdownCarrier:
    """Frontmatter by default; also recognizes the HTML comment envelope."""

    name = "markdown"
    capability = "somnus-adapter-markdown@1"
    forbid: Optional[str] = None
    region_style = ("markdown",)

    def extract(self, lines: list[str]) -> Extraction:
        """Find the unique frontmatter ``somnus`` block or HTML envelope."""
        result = Extraction()
        found: list[Envelope] = []
        close, opened = frontmatter_bounds(lines)
        body_start = 0
        if opened and close is None:
            result.issues.append(Issue(1, 1, "E_ENVELOPE", "frontmatter opener '---' is never closed"))
            return result
        if close is not None:
            body_start = close + 1
            blocks = self._top_blocks(lines, 1, close)
            somnus_blocks = [b for b in blocks if lines[b[0]].startswith("somnus:")]
            for extra in somnus_blocks[1:]:
                result.issues.append(Issue(extra[0] + 1, 1, "E_ENVELOPE", "duplicate 'somnus' key in frontmatter"))
            if somnus_blocks:
                s, e = somnus_blocks[0]
                if len(blocks) == 1 and s == 1 and e == close:
                    found.append(Envelope("frontmatter-full", 0, close + 1, lines[s:e], s))
                else:
                    found.append(Envelope("frontmatter", s, e, lines[s:e], s, 0, 0, close + 1))
        mask = markdown_code_mask(lines)
        i = body_start
        while i < len(lines):
            if lines[i] == HTML_OPEN and not mask[i]:
                j = i + 1
                while j < len(lines) and lines[j] != HTML_CLOSE:
                    j += 1
                if j >= len(lines):
                    result.issues.append(Issue(i + 1, 1, "E_ENVELOPE", "HTML comment envelope is never closed"))
                    break
                payload = lines[i + 1 : j]
                for k, text in enumerate(payload):
                    if "--" in text:
                        result.issues.append(Issue(i + 2 + k, text.index("--") + 1, "E_ENVELOPE",
                                                   "'--' is forbidden inside an HTML comment envelope"))
                found.append(Envelope("html-comment", i, j + 1, payload, i + 1))
                i = j + 1
                continue
            i += 1
        for dup in found[1:]:
            result.issues.append(Issue(dup.start + 1, 1, "E_ENVELOPE", "more than one metadata envelope"))
        if found:
            result.envelope = found[0]
        return result

    @staticmethod
    def _top_blocks(lines: list[str], start: int, end: int) -> list[tuple[int, int]]:
        heads = [i for i in range(start, end) if lines[i] and _TOP_KEY.match(lines[i])]
        blocks = []
        for n, head in enumerate(heads):
            stop = heads[n + 1] if n + 1 < len(heads) else end
            while stop > head + 1 and (not lines[stop - 1].strip() or lines[stop - 1].lstrip().startswith("#")):
                stop -= 1
            blocks.append((head, stop))
        return blocks

    def render(self, lines: list[str], payload: str, envelope: Optional[Envelope], style: Optional[str] = None) -> Splice:
        """Replace the existing envelope, or insert one in the requested style."""
        body = payload.rstrip("\n").split("\n")
        if envelope is not None:
            if envelope.kind == "html-comment":
                return Splice(envelope.start, envelope.end, [HTML_OPEN, *body, HTML_CLOSE])
            if envelope.kind == "frontmatter-full":
                return Splice(envelope.start, envelope.end, ["---", *body, "---"])
            return Splice(envelope.start, envelope.end, body)
        close, _ = frontmatter_bounds(lines)
        if (style or "frontmatter") == "html-comment":
            at = close + 1 if close is not None else 0
            return Splice(at, at, [HTML_OPEN, *body, HTML_CLOSE])
        if close is not None:
            return Splice(close, close, body)
        return Splice(0, 0, ["---", *body, "---"])
