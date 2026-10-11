"""Carrier protocol, registry, and extension-based auto-detection (SPEC Â§17).

A carrier works on a file's lines (without line endings). ``extract`` finds
the single authoritative envelope; ``render`` returns a splice that replaces
or inserts the envelope without touching any other line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol

SIDECAR_SUFFIX = ".somnus.yaml"


@dataclass
class Envelope:
    """Location of an envelope inside a file's lines (0-based, end exclusive)."""

    kind: str
    start: int
    end: int
    payload_lines: list[str]
    payload_start: int  # 0-based file line of the first payload line
    col_offset: int = 0  # characters stripped from each payload line (prefix width)
    mask_start: int = -1  # region scanning ignores [mask_start, mask_end)
    mask_end: int = -1

    def __post_init__(self) -> None:
        if self.mask_start < 0:
            self.mask_start, self.mask_end = self.start, self.end

    @property
    def payload(self) -> str:
        """Payload YAML text with a trailing newline."""
        return "\n".join(self.payload_lines) + "\n"


@dataclass
class Issue:
    """Carrier-level problem at a 1-based file position."""

    line: int
    col: int
    code: str
    message: str


@dataclass
class Extraction:
    """Result of envelope extraction."""

    envelope: Optional[Envelope] = None
    issues: list[Issue] = field(default_factory=list)


@dataclass
class Splice:
    """Replace ``lines[start:end]`` with ``new_lines``."""

    start: int
    end: int
    new_lines: list[str]


class Carrier(Protocol):
    """Interface implemented by every carrier."""

    name: str
    capability: str
    forbid: Optional[str]
    region_style: tuple

    def extract(self, lines: list[str]) -> Extraction:
        """Locate the envelope."""
        ...

    def render(self, lines: list[str], payload: str, envelope: Optional[Envelope], style: Optional[str] = None) -> Splice:
        """Return the splice that writes ``payload`` into the file."""
        ...


class CarrierError(ValueError):
    """The carrier cannot place the envelope without altering host semantics."""

    def __init__(self, code: str, message: str, line: int = 1):
        self.code = code
        self.line = line
        super().__init__(message)


def _registry() -> dict[str, Carrier]:
    from somnus.carriers.blockcomment import CSS, XML
    from somnus.carriers.linecomment import HashCarrier, LineCarrier
    from somnus.carriers.markdown import MarkdownCarrier

    return {
        "markdown": MarkdownCarrier(),
        "python": HashCarrier("python"),
        "shell": HashCarrier("shell"),
        "powershell": HashCarrier("powershell"),
        "r": HashCarrier("r"),
        "toml": HashCarrier("toml"),
        "yaml": HashCarrier("yaml"),
        "tex": LineCarrier("tex", "% ", "somnus-adapter-tex@1", "tex"),
        "slash": LineCarrier("slash", "// ", "somnus-adapter-slash-comment@1", "slash"),
        "js": LineCarrier("js", "// ", "somnus-adapter-slash-comment@1", "js"),
        "sql": LineCarrier("sql", "-- ", "somnus-adapter-sql-comment@1", "sql"),
        "css": CSS,
        "xml": XML,
    }


EXTENSIONS: dict[str, str] = {
    ".md": "markdown", ".markdown": "markdown", ".mdx": "markdown",
    ".py": "python", ".pyw": "python",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".ps1": "powershell", ".psm1": "powershell", ".psd1": "powershell",
    ".r": "r",
    ".toml": "toml", ".yaml": "yaml", ".yml": "yaml",
    ".tex": "tex", ".sty": "tex", ".cls": "tex", ".ltx": "tex",
    ".js": "js", ".mjs": "js", ".cjs": "js", ".jsx": "js", ".ts": "js", ".tsx": "js",
    ".rs": "slash", ".c": "slash", ".h": "slash", ".cc": "slash", ".cpp": "slash", ".hpp": "slash",
    ".go": "slash", ".java": "slash", ".kt": "slash", ".swift": "slash", ".cs": "slash",
    ".sql": "sql",
    ".css": "css", ".scss": "css", ".less": "css",
    ".html": "xml", ".htm": "xml", ".xhtml": "xml", ".xml": "xml", ".svg": "xml",
}

_CACHE: dict[str, Carrier] = {}


def get(name: str) -> Carrier:
    """Return the carrier registered under ``name``."""
    if not _CACHE:
        _CACHE.update(_registry())
    return _CACHE[name]


def is_sidecar_path(path: Path) -> bool:
    """Return True for ``*.somnus.yaml`` sidecar files."""
    return path.name.endswith(SIDECAR_SUFFIX)


def sidecar_for(path: Path) -> Path:
    """Return the sidecar path for a host file."""
    return path.with_name(path.name + SIDECAR_SUFFIX)


def host_for(sidecar: Path) -> Path:
    """Return the host path a sidecar file describes by name."""
    return sidecar.with_name(sidecar.name[: -len(SIDECAR_SUFFIX)])


def carrier_name_for(path: Path) -> Optional[str]:
    """Return the embedded carrier name for a path, or None when a sidecar is required."""
    if is_sidecar_path(path):
        return None
    suffix = path.suffix if path.suffix in EXTENSIONS else path.suffix.lower()
    return EXTENSIONS.get(suffix)


def for_path(path: Path) -> Optional[Carrier]:
    """Return the embedded carrier for a path, or None when a sidecar is required."""
    name = carrier_name_for(path)
    return get(name) if name else None
