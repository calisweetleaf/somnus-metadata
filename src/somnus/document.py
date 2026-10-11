"""Document loading and atomic saving with byte preservation (SPEC §16.3, §17)."""

from __future__ import annotations

import copy
import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from somnus import carriers, yamlsub
from somnus.carriers import CarrierError, Envelope, Issue, Splice
from somnus.carriers.sidecar import SIDECAR
from somnus.model.schema import make_order
from somnus.output import Diagnostic, SomnusError, EXIT_USAGE


def _split(text: str) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    endings: list[str] = []
    for raw in text.splitlines(keepends=True):
        if raw.endswith("\r\n"):
            lines.append(raw[:-2])
            endings.append("\r\n")
        elif raw.endswith(("\n", "\r")):
            lines.append(raw[:-1])
            endings.append(raw[-1])
        else:
            lines.append(raw)
            endings.append("")
    return lines, endings


def _dominant_newline(endings: list[str]) -> str:
    crlf = endings.count("\r\n")
    lf = endings.count("\n")
    return "\r\n" if crlf > lf else "\n"


@dataclass
class Document:
    """A managed file: its lines, carrier, envelope, and parsed payload."""

    path: Path  # the artifact's host file
    meta_path: Path  # file holding the envelope (== path, or the sidecar)
    carrier: Any
    lines: list[str]
    endings: list[str]
    had_bom: bool
    envelope: Optional[Envelope] = None
    data: Optional[dict] = None  # parsed root mapping {"somnus": {...}}
    spans: dict = field(default_factory=dict)
    issues: list[Diagnostic] = field(default_factory=list)
    host_bytes: Optional[bytes] = None  # sidecar host content

    # ------------------------------------------------------------- properties
    @property
    def is_sidecar(self) -> bool:
        """True when metadata lives in a ``.somnus.yaml`` sidecar."""
        return self.carrier is SIDECAR

    @property
    def newline(self) -> str:
        """Line ending used for lines the tool writes."""
        return _dominant_newline(self.endings)

    @property
    def payload(self) -> Optional[dict]:
        """The ``somnus`` mapping, when it parsed."""
        if isinstance(self.data, dict) and isinstance(self.data.get("somnus"), dict):
            return self.data["somnus"]
        return None

    @property
    def display(self) -> str:
        """Path shown in diagnostics."""
        return _display(self.meta_path)

    @property
    def ignore_span(self) -> tuple[int, int]:
        """0-based [start, end) span hidden from body scans."""
        if self.envelope is None or self.is_sidecar:
            return (-1, -1)
        return (self.envelope.mask_start, self.envelope.mask_end)

    def body_lines(self) -> list[str]:
        """Lines outside the envelope (host content)."""
        if self.is_sidecar:
            return []
        if self.envelope is None:
            return list(self.lines)
        return self.lines[: self.envelope.start] + self.lines[self.envelope.end :]

    def body_digest(self) -> str:
        """SHA-256 of host content outside the envelope, LF-normalized."""
        if self.is_sidecar:
            data = self.host_bytes if self.host_bytes is not None else b""
            return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
        keep = range(len(self.lines))
        if self.envelope is not None:
            keep = [i for i in keep if not self.envelope.start <= i < self.envelope.end]
        data = "".join(self.lines[i] + ("\n" if self.endings[i] else "") for i in keep)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def payload_digest(self) -> str:
        """SHA-256 of the canonical serialization of the payload."""
        return hashlib.sha256(canonical_yaml(self.data or {}).encode("utf-8")).hexdigest()

    def pos(self, path: tuple) -> tuple[int, int]:
        """Map a payload path to a 1-based file (line, col)."""
        if self.envelope is None:
            return (1, 1)
        p = tuple(path)
        while p and p not in self.spans:
            p = p[:-1]
        line, col = self.spans.get(p, (1, 1))
        return (self.envelope.payload_start + line, col + self.envelope.col_offset)

    def diag(self, path: tuple, code: str, message: str, severity: str = "error",
             line: Optional[int] = None, col: Optional[int] = None) -> Diagnostic:
        """Build a diagnostic anchored at a payload path (or explicit position)."""
        if line is None:
            line, col = self.pos(path)
        return Diagnostic(self.display, line, col or 1, severity, code, field_name(path), message)

    # ------------------------------------------------------------- rendering
    def render(self, payload: dict, style: Optional[str] = None) -> str:
        """Return the full file text with ``payload`` written into the envelope."""
        root = {"somnus": payload}
        kind = self.envelope.kind if self.envelope is not None else style
        forbid = "html" if kind == "html-comment" else self.carrier.forbid
        text = canonical_yaml(root, forbid=forbid)
        try:
            splice = self.carrier.render(self.lines, text, self.envelope, style)
        except CarrierError as exc:
            raise SomnusError([Diagnostic(self.display, exc.line, 1, "error", exc.code, "-", str(exc))])
        return self._apply(splice)

    def _apply(self, splice: Splice) -> str:
        nl = self.newline
        lines = self.lines[: splice.start] + splice.new_lines + self.lines[splice.end :]
        endings = self.endings[: splice.start] + [nl] * len(splice.new_lines) + self.endings[splice.end :]
        if splice.start > 0 and self.endings[splice.start - 1] == "" and splice.new_lines:
            endings[splice.start - 1] = nl
        if splice.new_lines and splice.start + len(splice.new_lines) == len(lines) and splice.end == len(self.lines):
            if self.endings and splice.end > 0:
                endings[-1] = self.endings[splice.end - 1] or nl
        text = "".join(l + e for l, e in zip(lines, endings))
        self._verify_preserved(text)
        return text

    def _verify_preserved(self, text: str) -> None:
        """Re-extract the envelope from ``text`` and require identical host content."""
        if self.is_sidecar:
            return
        new_lines, _ = _split(text)
        extraction = self.carrier.extract(new_lines)
        env = extraction.envelope
        ok = env is not None and not extraction.issues
        if ok:
            new_body = new_lines[: env.start] + new_lines[env.end :]
            ok = new_body == self.body_lines()
        if not ok:
            raise SomnusError([Diagnostic(self.display, 1, 1, "error", "E_HOST", "-",
                                          "refusing to write: content outside the envelope would change")])

    def save(self, payload: dict, style: Optional[str] = None) -> str:
        """Atomically write ``payload`` into the envelope; return the new text."""
        text = self.render(payload, style)
        atomic_write(self.meta_path, text)
        return text

    def copy_payload(self) -> dict:
        """Deep copy of the current payload (empty dict when unparsed)."""
        return copy.deepcopy(self.payload or {})


def field_name(path: tuple) -> str:
    """Format a payload path as ``somnus.a.b[0].c`` (or ``-``)."""
    if not path:
        return "-"
    out = ""
    for part in path:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += ("." if out else "") + str(part)
    return out


def canonical_yaml(root: dict, forbid: Optional[str] = None) -> str:
    """Serialize a root mapping in canonical order."""
    return yamlsub.dumps(root, order=make_order(root), forbid=forbid)


def _display(path: Path) -> str:
    try:
        return os.path.relpath(path, Path.cwd()).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def atomic_write(path: Path, text: str) -> None:
    """Write UTF-8 text via a same-directory temp file and ``os.replace``."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        if path.exists():
            try:
                os.chmod(tmp, path.stat().st_mode)
            except OSError:
                pass
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _decode(raw: bytes, path: Path) -> tuple[str, bool]:
    bom = raw.startswith(b"\xef\xbb\xbf")
    if bom:
        raw = raw[3:]
    try:
        return raw.decode("utf-8"), bom
    except UnicodeDecodeError as exc:
        raise SomnusError([Diagnostic(_display(path), 1, 1, "error", "E_IO", "-",
                                      f"file is not valid UTF-8 (byte {exc.start}); use a sidecar")])


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SomnusError([Diagnostic(_display(path), 0, 0, "error", "E_IO", "-", exc.strerror or str(exc))],
                          EXIT_USAGE)


def _issue_diag(path: Path, issue: Issue) -> Diagnostic:
    return Diagnostic(_display(path), issue.line, issue.col, "error", issue.code, "-", issue.message)


def _parse_into(doc: Document, lenient: bool = False) -> None:
    env = doc.envelope
    if env is None:
        return
    try:
        parsed = yamlsub.parse(env.payload, lenient=lenient)
    except yamlsub.YAMLError as exc:
        doc.issues.append(Diagnostic(doc.display, env.payload_start + exc.line, exc.col + env.col_offset,
                                     "error", "E_YAML", "-", exc.message))
        return
    if not isinstance(parsed.data, dict):
        doc.issues.append(doc.diag((), "E_YAML", "payload must be a mapping"))
        return
    doc.data = parsed.data
    doc.spans = parsed.spans


def load(path: Path | str, *, lenient: bool = False) -> Document:
    """Load a file (or its sidecar) and parse its envelope.

    Envelope and YAML problems are recorded in ``doc.issues``; only I/O and
    encoding failures raise ``SomnusError``.
    """
    path = Path(path).resolve()
    if carriers.is_sidecar_path(path):
        return _load_sidecar(carriers.host_for(path), path, lenient)
    if not path.is_file():
        raise SomnusError([Diagnostic(_display(path), 0, 0, "error", "E_IO", "-", "file not found")], EXIT_USAGE)
    carrier = carriers.for_path(path)
    sidecar = carriers.sidecar_for(path)
    if carrier is None:
        return _load_sidecar(path, sidecar, lenient)
    raw = _read(path)
    text, bom = _decode(raw, path)
    lines, endings = _split(text)
    doc = Document(path, path, carrier, lines, endings, bom)
    extraction = carrier.extract(lines)
    doc.envelope = extraction.envelope
    doc.issues.extend(_issue_diag(path, i) for i in extraction.issues)
    if sidecar.exists():
        if doc.envelope is not None:
            doc.issues.append(Diagnostic(doc.display, doc.envelope.start + 1, 1, "error", "E_ENVELOPE", "-",
                                         f"both an embedded envelope and sidecar {sidecar.name} exist"))
        else:
            return _load_sidecar(path, sidecar, lenient)
    _parse_into(doc, lenient)
    return doc


def _load_sidecar(host: Path, sidecar: Path, lenient: bool) -> Document:
    host_bytes = host.read_bytes() if host.is_file() else None
    if not sidecar.is_file():
        doc = Document(host, sidecar, SIDECAR, [], [], False, host_bytes=host_bytes)
        return doc
    text, bom = _decode(_read(sidecar), sidecar)
    lines, endings = _split(text)
    doc = Document(host, sidecar, SIDECAR, lines, endings, bom, host_bytes=host_bytes)
    extraction = SIDECAR.extract(lines)
    doc.envelope = extraction.envelope
    doc.issues.extend(_issue_diag(sidecar, i) for i in extraction.issues)
    _parse_into(doc, lenient)
    return doc


def from_text(path: Path | str, text: str, *, lenient: bool = False) -> Document:
    """Build a document from in-memory text (used by tests and dry runs)."""
    path = Path(path)
    carrier = carriers.for_path(path) or SIDECAR
    if text.startswith("\ufeff"):
        text, bom = text[1:], True
    else:
        bom = False
    lines, endings = _split(text)
    doc = Document(path, path, carrier, lines, endings, bom)
    extraction = carrier.extract(lines)
    doc.envelope = extraction.envelope
    doc.issues.extend(_issue_diag(path, i) for i in extraction.issues)
    _parse_into(doc, lenient)
    return doc


def new_sidecar_text(payload: dict) -> str:
    """Canonical text for a brand-new sidecar file."""
    return canonical_yaml({"somnus": payload})
