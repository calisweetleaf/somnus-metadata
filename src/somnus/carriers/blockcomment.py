"""Block-comment carriers: CSS ``/* */`` and XML/HTML/SVG ``<!-- -->`` (SPEC Â§17.4â€“Â§17.5)."""

from __future__ import annotations

import re
from typing import Optional

from somnus.carriers import CarrierError, Envelope, Extraction, Issue, Splice

_CHARSET = re.compile(r'^@charset "[^"]*";\s*$')


class BlockCarrier:
    """Envelope delimited by a block-comment opener and closer line."""

    def __init__(self, name: str, opener: str, closer: str, forbidden: str, forbid: str, region_style: tuple):
        self.name = name
        self.capability = "somnus-adapter-block-comment@1"
        self.opener = opener
        self.closer = closer
        self.forbidden = forbidden
        self.forbid: Optional[str] = forbid
        self.region_style = region_style

    def preamble_end(self, lines: list[str]) -> int:
        """Return the index after the host's mandatory leading declarations."""
        i = 0
        if self.name == "css":
            if lines and lines[0].startswith("@charset"):
                if not _CHARSET.match(lines[0]):
                    raise CarrierError("E_HOST", "@charset declaration must be alone on the first line", 1)
                i = 1
            return i
        while i < len(lines):
            stripped = lines[i].lstrip()
            if stripped.startswith("<?xml"):
                if "?>" not in stripped:
                    raise CarrierError("E_HOST", "multi-line XML declaration cannot be preserved safely", i + 1)
                i += 1
            elif stripped[:9].upper() == "<!DOCTYPE":
                if ">" not in stripped:
                    raise CarrierError("E_HOST", "multi-line DOCTYPE cannot be preserved safely", i + 1)
                i += 1
            else:
                break
        return i

    def _skippable(self, line: str) -> bool:
        s = line.strip()
        if not s:
            return True
        if self.name == "xml":
            return s.startswith("<!--") and s.endswith("-->") and s != self.opener
        return s.startswith("/*") and s.endswith("*/") and s != self.opener

    def extract(self, lines: list[str]) -> Extraction:
        """Scan the leading area (after declarations) for one envelope."""
        result = Extraction()
        try:
            i = self.preamble_end(lines)
        except CarrierError:
            i = 0
        found: list[Envelope] = []
        n = len(lines)
        while i < n:
            if lines[i].rstrip() == self.opener:
                j = i + 1
                while j < n and lines[j].rstrip() != self.closer:
                    j += 1
                if j >= n:
                    result.issues.append(Issue(i + 1, 1, "E_ENVELOPE", "metadata envelope is never closed"))
                    break
                payload = lines[i + 1 : j]
                for k, text in enumerate(payload):
                    if self.forbidden in text:
                        result.issues.append(Issue(i + 2 + k, text.index(self.forbidden) + 1, "E_ENVELOPE",
                                                   f"{self.forbidden!r} is forbidden inside this envelope"))
                found.append(Envelope(self.name, i, j + 1, payload, i + 1))
                i = j + 1
                continue
            if self._skippable(lines[i]):
                i += 1
                continue
            break
        for extra in found[1:]:
            result.issues.append(Issue(extra.start + 1, 1, "E_ENVELOPE", "more than one metadata envelope"))
        if found:
            result.envelope = found[0]
        return result

    def render(self, lines: list[str], payload: str, envelope: Optional[Envelope], style: Optional[str] = None) -> Splice:
        """Replace the envelope, or insert it after the leading declarations."""
        body = payload.rstrip("\n").split("\n")
        for k, text in enumerate(body):
            if self.forbidden in text:
                raise CarrierError("E_HOST", f"payload contains {self.forbidden!r}; use a sidecar", k + 1)
        block = [self.opener, *body, self.closer]
        if envelope is not None:
            return Splice(envelope.start, envelope.end, block)
        at = self.preamble_end(lines)
        return Splice(at, at, block)


CSS = BlockCarrier("css", "/* somnus:metadata:v2", "somnus:end */", "*/", "block", ("block", "/* ", " */"))
XML = BlockCarrier("xml", "<!-- somnus:metadata:v2", "somnus:end -->", "--", "html", ("markdown",))
