# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7ce9-703e-abd4-42f16c7c1680"
#   revision: 2
#   title: "Carrier protocol, registry, and extension-based auto-detection (SPEC §17)"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a19a67-7ce9-703e-abd4-42f16c7c1680"
#         aspects: ["content"]
#   time:
#     updated_at: "2026-11-06T06:11:47+00:00"
#   names:
#     slug: "carrier-protocol-registry-and-extension-based-auto-detection-spec-17"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7ce9-703e-abd4-42f16c7c1680"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Carrier protocol, registry, and extension-based auto-detection (SPEC §17).

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
    from somnus.carriers.jsonhost import JSON_KEY, NOTEBOOK
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
        "hash": HashCarrier("hash"),
        "dockerfile": HashCarrier("dockerfile"),
        "lua": LineCarrier("lua", "-- ", "somnus-adapter-sql-comment@1", "lua"),
        "jsonc": LineCarrier("jsonc", "// ", "somnus-adapter-slash-comment@1", "jsonc"),
        "ipynb": NOTEBOOK,
        "json": JSON_KEY,
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
    # v2.2: hash-comment hosts beyond the original matrix (SPEC §17 routing table)
    ".rb": "hash", ".rake": "hash", ".gemspec": "hash", ".pl": "hash", ".pm": "hash",
    ".tf": "hash", ".tfvars": "hash", ".hcl": "hash", ".nix": "hash", ".jl": "hash", ".ex": "hash",
    ".exs": "hash", ".cr": "hash", ".nim": "hash", ".tcl": "hash", ".awk": "hash", ".sed": "hash",
    ".fish": "hash", ".mk": "hash", ".cmake": "hash", ".cfg": "hash", ".ini": "hash", ".conf": "hash",
    ".properties": "hash", ".env": "hash", ".gitignore": "hash", ".gitattributes": "hash",
    ".dockerignore": "hash", ".npmignore": "hash", ".editorconfig": "hash", ".graphql": "hash",
    ".gql": "hash", ".dockerfile": "dockerfile", ".containerfile": "dockerfile",
    ".mojo": "python", ".pyi": "python", ".pyx": "python",
    # slash-comment hosts
    ".zig": "slash", ".dart": "slash", ".scala": "slash", ".proto": "slash",
    ".groovy": "slash", ".gradle": "slash", ".mm": "slash", ".sol": "slash", ".hx": "slash", ".glsl": "slash", ".hlsl": "slash", ".wgsl": "slash",
    ".cu": "slash", ".cuh": "slash", ".mts": "js", ".cts": "js",
    # double-dash hosts
    ".lua": "lua", ".hs": "lua", ".elm": "lua", ".ada": "lua", ".adb": "lua", ".ads": "lua",
    # markup with HTML comments
    ".vue": "xml", ".svelte": "xml", ".astro": "xml", ".xsd": "xml", ".xsl": "xml", ".xslt": "xml",
    ".plist": "xml", ".csproj": "xml", ".vcxproj": "xml", ".resx": "xml",
    # JSON family
    ".jsonc": "jsonc", ".json5": "jsonc", ".ipynb": "ipynb",
}

# Exact filenames that have a comment syntax but no (or a misleading) extension.
FILENAMES: dict[str, str] = {
    "Dockerfile": "dockerfile", "Containerfile": "dockerfile",
    "Makefile": "hash", "makefile": "hash", "GNUmakefile": "hash", "CMakeLists.txt": "hash",
    "CODEOWNERS": "hash", "MANIFEST.in": "hash", "requirements.txt": "hash", "constraints.txt": "hash", "Gemfile": "hash", "Rakefile": "hash",
    "Vagrantfile": "hash", "Brewfile": "hash", "Podfile": "hash", "Fastfile": "hash",
    "Justfile": "hash", "justfile": "hash", "Snakefile": "python", "SConstruct": "python",
    "SConscript": "python", "BUILD": "python", "BUILD.bazel": "python", "WORKSPACE": "python",
    "Tiltfile": "python", "Pipfile": "toml", "Caddyfile": "hash",
    ".gitignore": "hash", ".gitattributes": "hash", ".gitmodules": "hash", ".dockerignore": "hash",
    ".npmignore": "hash", ".prettierignore": "hash", ".eslintignore": "hash", ".hgignore": "hash",
    ".editorconfig": "hash", ".env": "hash", ".flake8": "hash", ".pylintrc": "hash",
    ".coveragerc": "hash", ".bashrc": "shell", ".bash_profile": "shell", ".profile": "shell",
    ".zshrc": "shell", ".zprofile": "shell", ".inputrc": "hash", ".npmrc": "hash",
    ".yarnrc": "hash", ".condarc": "yaml", ".clang-format": "yaml", ".clang-tidy": "yaml",
    "tsconfig.json": "jsonc", "jsconfig.json": "jsonc", "devcontainer.json": "jsonc",
    ".devcontainer.json": "jsonc", ".eslintrc.json": "jsonc",
    ".babelrc": "jsonc", "tslint.json": "jsonc", "api-extractor.json": "jsonc",
}

# Filename patterns (prefix, suffix) checked after exact names.
_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("requirements", ".txt", "hash"), ("constraints", ".txt", "hash"), (".env.", "", "hash"),
    ("Dockerfile.", "", "dockerfile"), ("Containerfile.", "", "dockerfile"),
    ("tsconfig.", ".json", "jsonc"), ("jsconfig.", ".json", "jsonc"),
)

# Shebang interpreter -> carrier, for extensionless executables.
_SHEBANG = {
    "python": "python", "python3": "python", "python2": "python", "pypy": "python", "pypy3": "python",
    "sh": "shell", "bash": "shell", "zsh": "shell", "dash": "shell", "ksh": "shell", "fish": "shell",
    "node": "js", "deno": "js", "bun": "js", "tsx": "js", "ts-node": "js",
    "ruby": "hash", "perl": "hash", "Rscript": "r", "pwsh": "powershell", "awk": "hash",
    "julia": "hash", "elixir": "hash", "tclsh": "hash", "lua": "lua", "make": "hash",
}

SNIFF_BYTES = 512

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


def _sniff(path: Path) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read(SNIFF_BYTES)
    except OSError:
        return b""


def shebang_carrier(head: bytes) -> Optional[str]:
    """Carrier for a ``#!`` interpreter line, or None."""
    if head.startswith(b"\xef\xbb\xbf"):
        head = head[3:]
    if not head.startswith(b"#!"):
        return None
    first = head.split(b"\n", 1)[0].decode("utf-8", "replace").strip()[2:].split()
    if not first:
        return None
    prog = first[0].rsplit("/", 1)[-1]
    if prog == "env":
        rest = [a for a in first[1:] if not a.startswith("-") and "=" not in a]
        if not rest:
            return None
        prog = rest[0].rsplit("/", 1)[-1]
    if prog not in _SHEBANG:
        prog = prog.rstrip("0123456789.")
    return _SHEBANG.get(prog)


def carrier_name_for(path: Path, *, sniff: bool = True) -> Optional[str]:
    """Return the embedded carrier name for a path, or None when a sidecar is required.

    Routing order (SPEC §17): sidecar files, exact filenames, filename patterns,
    extensions, then (for extensionless files) the shebang interpreter. Plain
    ``.json`` is embedded only when the file already carries a leading
    ``"$somnus"`` key (opt-in, §17.8); otherwise it stays a sidecar host.
    """
    if is_sidecar_path(path):
        return None
    name = path.name
    if name in FILENAMES:
        return FILENAMES[name]
    for prefix, suffix, carrier in _PATTERNS:
        if name.startswith(prefix) and name.endswith(suffix) and len(name) > len(prefix) + len(suffix):
            return carrier
    suffix = path.suffix if path.suffix in EXTENSIONS else path.suffix.lower()
    if suffix in EXTENSIONS:
        return EXTENSIONS[suffix]
    if suffix == ".json":
        if sniff and json_key_present(_sniff(path)):
            return "json"
        return None
    if sniff and (not suffix or suffix not in _KNOWN_BINARY) and path.is_file():
        return shebang_carrier(_sniff(path))
    return None


_KNOWN_BINARY = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".tgz", ".xz", ".bz2",
                 ".whl", ".so", ".dll", ".dylib", ".exe", ".bin", ".o", ".a", ".pyc", ".db", ".sqlite",
                 ".parquet", ".docx", ".xlsx", ".pptx", ".mp3", ".mp4", ".wav", ".mov", ".ttf", ".woff", ".woff2"}


def json_key_present(head: bytes) -> bool:
    """True when JSON text opens with an object whose first key is ``"$somnus"``."""
    text = head.decode("utf-8", "ignore").lstrip("\ufeff \t\r\n")
    if not text.startswith("{"):
        return False
    return text[1:].lstrip(" \t\r\n").startswith('"$somnus"')


def for_text(path: Path, text: str) -> Optional[Carrier]:
    """Embedded carrier for in-memory ``text`` claimed to live at ``path`` (no disk access)."""
    name = carrier_name_for(path, sniff=False)
    if name is None and not is_sidecar_path(path):
        head = text.encode("utf-8")[:SNIFF_BYTES]
        suffix = path.suffix.lower()
        if suffix == ".json":
            name = "json" if json_key_present(head) else None
        elif not suffix or suffix not in EXTENSIONS:
            name = shebang_carrier(head)
    return get(name) if name else None


def for_path(path: Path) -> Optional[Carrier]:
    """Return the embedded carrier for a path, or None when a sidecar is required."""
    name = carrier_name_for(path)
    return get(name) if name else None
