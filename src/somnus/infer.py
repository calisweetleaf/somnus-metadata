"""Heuristic title and classification inference for ``somnus stamp``."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

_MD_KEYWORDS: list[tuple[str, str]] = [
    (r"spec", "specification"),
    (r"decision|adr", "decision-record"),
    (r"plan|roadmap", "plan"),
    (r"task|todo", "task"),
    (r"notepad|notes?|scratch", "notepad"),
    (r"runbook|playbook|howto", "runbook"),
    (r"memory", "memory"),
    (r"context|state", "state"),
    (r"bench", "benchmark"),
    (r"readme|index|filetree|toc", "index"),
    (r"architecture|design", "architecture-record"),
    (r"paper|whitepaper", "whitepaper"),
    (r"report|results?|summary", "report"),
    (r"conversation|transcript|chat", "conversation"),
]

_TYPE_DEFAULTS: dict[str, tuple[str, str, str]] = {
    # type -> (category, role, body_role)
    "specification": ("engineering", "normative", "specification"),
    "decision-record": ("governance", "normative", "narrative"),
    "plan": ("operations", "working", "narrative"),
    "task": ("operations", "working", "instruction"),
    "notepad": ("context", "working", "narrative"),
    "runbook": ("operations", "normative", "instruction"),
    "memory": ("context", "informative", "narrative"),
    "state": ("context", "informative", "narrative"),
    "benchmark": ("engineering", "informative", "narrative"),
    "index": ("context", "informative", "narrative"),
    "architecture-record": ("engineering", "normative", "narrative"),
    "whitepaper": ("research", "informative", "narrative"),
    "report": ("engineering", "informative", "narrative"),
    "conversation": ("context", "historical", "conversation"),
    "source-code": ("engineering", "informative", "source"),
    "configuration": ("engineering", "normative", "configuration"),
    "dataset": ("research", "informative", "dataset"),
    "equation-set": ("research", "informative", "specification"),
    "asset": ("engineering", "informative", "mixed"),
    "test-result": ("engineering", "informative", "narrative"),
}

_SOURCE = {".py", ".pyw", ".sh", ".bash", ".zsh", ".ps1", ".psm1", ".r", ".js", ".mjs", ".cjs", ".jsx", ".ts",
           ".tsx", ".rs", ".c", ".h", ".cc", ".cpp", ".hpp", ".go", ".java", ".kt", ".swift", ".cs", ".sql",
           ".css", ".scss", ".less", ".html", ".htm"}
_CONFIG = {".toml", ".yaml", ".yml", ".ini", ".cfg", ".psd1", ".xml"}
_DATA = {".json", ".csv", ".tsv", ".parquet", ".jsonl", ".ndjson", ".sqlite", ".db"}
_ASSET = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".docx", ".pptx", ".xlsx", ".zip", ".ico", ".webp"}


@dataclass
class Inference:
    """Inferred header values for an unmanaged file."""

    title: str
    type: str
    category: str
    role: str
    body_role: str


def infer_type(path: Path, lines: Sequence[str]) -> str:
    """Infer the artifact type from extension, filename keywords, and content."""
    suffix = path.suffix.lower()
    stem = path.stem.lower()
    if suffix in (".md", ".markdown", ".mdx", ".txt", ".rst"):
        for pattern, kind in _MD_KEYWORDS:
            if re.search(pattern, stem):
                return kind
        return "report"
    if suffix in (".tex", ".ltx"):
        text = "\n".join(lines)
        envs = len(re.findall(r"\\begin\{(?:equation|align|gather|multline)\*?\}", text))
        return "equation-set" if envs >= 3 and "\\section" not in text else "whitepaper"
    if suffix in _CONFIG:
        return "configuration"
    if suffix in _SOURCE:
        return "source-code"
    if suffix in _DATA:
        return "dataset"
    if suffix in _ASSET:
        return "asset"
    if suffix == ".ipynb":
        return "report"
    return "asset"


def infer_title(path: Path, lines: Sequence[str]) -> str:
    """Infer a human title from headings, TeX titles, docstrings, or the filename."""
    suffix = path.suffix.lower()
    if suffix in (".md", ".markdown", ".mdx"):
        in_front = bool(lines) and lines[0] == "---"
        fence = False
        for i, line in enumerate(lines):
            if in_front:
                if i > 0 and line == "---":
                    in_front = False
                continue
            if line.startswith(("```", "~~~")):
                fence = not fence
                continue
            m = re.match(r"^#{1,2}\s+(.+?)\s*#*\s*$", line)
            if m and not fence:
                return _clean(m.group(1))
    if suffix in (".tex", ".ltx"):
        m = re.search(r"\\title\{([^}]*)\}", "\n".join(lines))
        if m and m.group(1).strip():
            return _clean(m.group(1))
    if suffix in (".py", ".pyw"):
        try:
            doc = ast.get_docstring(ast.parse("\n".join(lines) + "\n"))
        except SyntaxError:
            doc = None
        if doc and doc.strip():
            return _clean(doc.strip().splitlines()[0].rstrip("."))
    return _from_filename(path)


def _clean(text: str) -> str:
    text = re.sub(r"[*_`]", "", text).strip()
    return text or "Untitled"


def _from_filename(path: Path) -> str:
    stem = path.name.split(".")[0] or path.stem
    words = re.split(r"[-_\s]+", stem)
    title = " ".join(w if w.isupper() else w.capitalize() for w in words if w)
    return title or "Untitled"


def infer(path: Path, lines: Sequence[str], type_override: Optional[str] = None,
          title_override: Optional[str] = None) -> Inference:
    """Infer title and classification defaults for an unmanaged file."""
    kind = type_override or infer_type(path, lines)
    category, role, body_role = _TYPE_DEFAULTS.get(kind, ("engineering", "informative", "mixed"))
    return Inference(title_override or infer_title(path, lines), kind, category, role, body_role)
