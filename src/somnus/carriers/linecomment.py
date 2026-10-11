"""Comment-prefixed carriers: ``# ``, ``% ``, ``// ``, ``-- `` (SPEC §17.3, §17.5)."""

from __future__ import annotations

import re
from typing import Optional

from somnus.carriers import Envelope, Extraction, Issue, Splice

_COOKIE = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*[-\w.]+")
_REQUIRES = re.compile(r"^#requires\b", re.IGNORECASE)
_TEX_MAGIC = re.compile(r"^%\s*!tex\b", re.IGNORECASE)


def preamble_end(host: str, lines: list[str]) -> int:
    """Return the index of the first line after mandatory host preamble lines."""
    i = 0
    n = len(lines)
    if host in ("python", "shell", "r", "js", "powershell") and n and lines[0].startswith("#!"):
        i = 1
    if host == "python":
        if i == 0 and n and _COOKIE.match(lines[0]):
            i = 1
        elif n > 1 and lines[0].lstrip().startswith("#") and _COOKIE.match(lines[1]):
            i = 2
    elif host == "powershell":
        while i < n and _REQUIRES.match(lines[i]):
            i += 1
    elif host == "tex":
        while i < n and _TEX_MAGIC.match(lines[i]):
            i += 1
    return i


class LineCarrier:
    """Envelope made of prefixed comment lines in the host's leading comment area."""

    forbid: Optional[str] = None

    def __init__(self, host: str, prefix: str, capability: str, name: Optional[str] = None):
        self.host = host
        self.prefix = prefix
        self.bare = prefix.rstrip()
        self.capability = capability
        self.name = name or host
        self.opener = f"{prefix}somnus:metadata:v2"
        self.closer = f"{prefix}somnus:end"
        self.region_style = ("prefix", prefix)

    def _is_comment(self, line: str) -> bool:
        return line.lstrip().startswith(self.bare)

    def extract(self, lines: list[str]) -> Extraction:
        """Scan the leading comment area for exactly one envelope."""
        result = Extraction()
        found: list[Envelope] = []
        i = preamble_end(self.host, lines)
        n = len(lines)
        while i < n:
            line = lines[i]
            if line.rstrip() == self.opener.rstrip():
                j = i + 1
                payload: list[str] = []
                ok = True
                while j < n and lines[j].rstrip() != self.closer.rstrip():
                    text = lines[j]
                    if text.rstrip() == self.bare:
                        payload.append("")
                    elif text.startswith(self.prefix):
                        payload.append(text[len(self.prefix):])
                    else:
                        result.issues.append(Issue(j + 1, 1, "E_ENVELOPE",
                                                   f"envelope line must start with {self.prefix!r}"))
                        ok = False
                        break
                    j += 1
                if ok and j >= n:
                    result.issues.append(Issue(i + 1, 1, "E_ENVELOPE", "metadata envelope is never closed"))
                    break
                if not ok:
                    break
                found.append(Envelope(self.name, i, j + 1, payload, i + 1, len(self.prefix)))
                i = j + 1
                continue
            if not line.strip() or self._is_comment(line):
                i += 1
                continue
            break
        for extra in found[1:]:
            result.issues.append(Issue(extra.start + 1, 1, "E_ENVELOPE", "more than one metadata envelope"))
        if found:
            result.envelope = found[0]
        return result

    def render(self, lines: list[str], payload: str, envelope: Optional[Envelope], style: Optional[str] = None) -> Splice:
        """Replace the envelope, or insert it right after the mandatory preamble."""
        body = [self.prefix + ln if ln else self.prefix for ln in payload.rstrip("\n").split("\n")]
        block = [self.opener, *body, self.closer]
        if envelope is not None:
            return Splice(envelope.start, envelope.end, block)
        at = preamble_end(self.host, lines)
        return Splice(at, at, block)


class HashCarrier(LineCarrier):
    """``# `` carrier for Python, shell, PowerShell, R, TOML, and YAML hosts."""

    def __init__(self, host: str):
        super().__init__(host, "# ", "somnus-adapter-hash-comment@1", host)
