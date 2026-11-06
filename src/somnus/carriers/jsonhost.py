# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1af7c-09e6-770f-95ff-1f5cf45f6a6e"
#   revision: 1
#   title: "JSON-tree carriers: the \"$somnus\" key and Jupyter notebook metadata (SPEC §17.7, §17.8)"
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
#       - target_ref: "urn:somnus:artifact:01a1af7c-09e6-770f-95ff-1f5cf45f6a6e"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "json-tree-carriers-the-somnus-key-and-jupyter-notebook-metadata-spec-17-7-17-8"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1af7c-09e6-770f-95ff-1f5cf45f6a6e"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""JSON-tree carriers: the ``"$somnus"`` key and Jupyter notebook metadata (SPEC §17.7, §17.8).

Strict JSON has no comments, so these carriers store the payload as a JSON
object inside the host's own data tree and splice it in as text: every byte
outside the carrier's value is left alone. The host-preservation contract is
the data tree: the host parsed with the carrier key removed must be identical
before and after a write (``E_HOST`` otherwise).

* ``json`` (opt-in): a leading top-level ``"$somnus"`` key in an object document.
* ``ipynb``: ``metadata.somnus`` in a notebook (nbformat preserves unknown
  metadata keys, so Jupyter round-trips it).
"""

from __future__ import annotations

import json
from typing import Any, Optional

from somnus import yamlsub
from somnus.carriers import CarrierError, Envelope, Extraction, Issue, Splice

_WS = " \t\r\n"
_DECODER = json.JSONDecoder()


class _Span:
    __slots__ = ("key", "key_start", "value_start", "value_end", "member_end")

    def __init__(self, key: str, key_start: int, value_start: int, value_end: int, member_end: int):
        self.key = key
        self.key_start = key_start
        self.value_start = value_start
        self.value_end = value_end
        self.member_end = member_end  # index after the trailing comma, or value_end for the last member


def _skip(text: str, i: int) -> int:
    while i < len(text) and text[i] in _WS:
        i += 1
    return i


def object_members(text: str, start: int) -> tuple[list[_Span], int, int]:
    """Members of the JSON object opening at ``start``; returns (spans, open brace index, close brace index)."""
    i = _skip(text, start)
    if i >= len(text) or text[i] != "{":
        raise ValueError("not a JSON object")
    open_at = i
    i = _skip(text, i + 1)
    spans: list[_Span] = []
    if i < len(text) and text[i] == "}":
        return spans, open_at, i
    while True:
        key_start = i
        key, i = _DECODER.raw_decode(text, i)
        if not isinstance(key, str):
            raise ValueError("object key is not a string")
        i = _skip(text, i)
        if i >= len(text) or text[i] != ":":
            raise ValueError("expected ':'")
        value_start = _skip(text, i + 1)
        _, value_end = _DECODER.raw_decode(text, value_start)
        i = _skip(text, value_end)
        if i < len(text) and text[i] == ",":
            spans.append(_Span(key, key_start, value_start, value_end, i + 1))
            i = _skip(text, i + 1)
            continue
        if i < len(text) and text[i] == "}":
            spans.append(_Span(key, key_start, value_start, value_end, value_end))
            return spans, open_at, i
        raise ValueError("expected ',' or '}'")


def _indent_unit(text: str) -> str:
    """Indentation step used by the host (defaults to two spaces; ``""`` for minified JSON)."""
    if "\n" not in text.strip():
        return ""
    for line in text.split("\n")[1:]:
        stripped = line.lstrip(" \t")
        if stripped and len(stripped) < len(line):
            return line[: len(line) - len(stripped)]
    return "  "


def _line_col(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index)
    col = index - (text.rfind("\n", 0, index) + 1)
    return line, col


class _TreeCarrier:
    """Shared machinery: locate a key inside a nested object path and splice its value."""

    name = "json"
    capability = "somnus-adapter-json-key@1"
    forbid: Optional[str] = None
    region_style: tuple = ()
    container: tuple[str, ...] = ()
    key = "$somnus"
    first = True  # insert as the first member of the container

    # -------------------------------------------------------------- locating
    def _container(self, text: str) -> tuple[list[_Span], int, int, int]:
        """Spans of the container object, its brace indexes, and its depth."""
        spans, open_at, close_at = object_members(text, 0)
        if _skip(text, close_at + 1) != len(text):
            raise ValueError("trailing content after the JSON document")
        depth = 1
        for part in self.container:
            hit = [s for s in spans if s.key == part]
            if len(hit) != 1:
                raise KeyError(part)
            spans, open_at, close_at = object_members(text, hit[0].value_start)
            depth += 1
        return spans, open_at, close_at, depth

    def tree_without_key(self, text: str) -> Any:
        """Parsed host with the carrier key removed (the preserved data tree)."""
        tree = json.loads(text)
        node = tree
        for part in self.container:
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, dict):
            node.pop(self.key, None)
        return tree

    # -------------------------------------------------------------- protocol
    def extract(self, lines: list[str]) -> Extraction:
        """Find the carrier key; its value (a mapping) becomes the YAML payload."""
        text = "\n".join(lines)
        result = Extraction()
        try:
            spans, _, _, _ = self._container(text)
        except KeyError:
            return result
        except ValueError as exc:
            result.issues.append(Issue(1, 1, "E_ENVELOPE", f"host is not a JSON object document: {exc}"))
            return result
        hits = [s for s in spans if s.key == self.key]
        if not hits:
            return result
        if len(hits) > 1:
            line, col = _line_col(text, hits[1].key_start)
            result.issues.append(Issue(line + 1, col + 1, "E_ENVELOPE", f"duplicate {self.key!r} key"))
        span = hits[0]
        line, col = _line_col(text, span.key_start)
        value = json.loads(text[span.value_start:span.value_end])
        if not isinstance(value, dict):
            result.issues.append(Issue(line + 1, col + 1, "E_ENVELOPE", f"{self.key!r} must be an object"))
            return result
        try:
            payload = yamlsub.dumps({"somnus": value})
        except (yamlsub.YAMLError, TypeError, ValueError) as exc:
            result.issues.append(Issue(line + 1, col + 1, "E_YAML", f"{self.key!r} value is outside the Somnus "
                                                                   f"subset: {getattr(exc, 'message', exc)}"))
            return result
        result.envelope = Envelope(self.name, 0, len(lines), payload.rstrip("\n").split("\n"), line,
                                   mask_start=0, mask_end=len(lines))
        return result

    def render(self, lines: list[str], payload: str, envelope: Optional[Envelope], style: Optional[str] = None) -> Splice:
        """Splice the payload object into the host text without touching other members."""
        text = "\n".join(lines)
        data = yamlsub.parse(payload).data
        value = data["somnus"] if isinstance(data, dict) else None
        if not isinstance(value, dict):
            raise CarrierError("E_ENVELOPE", "payload must be a mapping")
        try:
            spans, open_at, close_at, depth = self._container(text)
        except KeyError as exc:
            raise CarrierError("E_HOST", f"host has no {'.'.join(self.container)!r} object") from exc
        except ValueError as exc:
            raise CarrierError("E_HOST", f"host is not a JSON object document: {exc}") from exc
        unit = _indent_unit(text)
        if unit:
            rendered = json.dumps(value, indent=unit, ensure_ascii=False)
            rendered = rendered.replace("\n", "\n" + unit * depth)
        else:
            rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        hits = [s for s in spans if s.key == self.key]
        if hits:
            span = hits[0]
            new_text = text[: span.value_start] + rendered + text[span.value_end:]
        else:
            member = json.dumps(self.key) + (": " if unit else ":") + rendered
            if not spans:
                if unit:
                    inner = "\n" + unit * depth + member + "\n" + unit * (depth - 1)
                else:
                    inner = member
                new_text = text[: open_at + 1] + inner + text[close_at:]
            elif self.first:
                lead = text[open_at + 1: spans[0].key_start]
                new_text = text[: open_at + 1] + lead + member + "," + lead + text[spans[0].key_start:]
            else:
                last = spans[-1]
                lead = text[spans[-2].member_end:last.key_start] if len(spans) > 1 else text[open_at + 1:last.key_start]
                new_text = text[: last.value_end] + "," + lead + member + text[last.value_end:]
        new_lines = new_text.split("\n")
        if new_lines and new_lines[-1] == "" and lines and lines[-1] != "":
            new_lines.pop()
        return Splice(0, len(lines), new_lines)

    def host_view(self, lines: list[str]) -> list[str]:
        """Canonical text of the preserved data tree (the 'body' for digests and search)."""
        try:
            tree = self.tree_without_key("\n".join(lines))
        except ValueError:
            return list(lines)
        return json.dumps(tree, ensure_ascii=False, sort_keys=True, indent=1).split("\n")


class JsonKeyCarrier(_TreeCarrier):
    """Opt-in ``"$somnus"`` first member of a top-level JSON object."""

    name = "json"
    capability = "somnus-adapter-json-key@1"
    container = ()
    key = "$somnus"
    first = True


class NotebookCarrier(_TreeCarrier):
    """``metadata.somnus`` inside a Jupyter notebook."""

    name = "ipynb"
    capability = "somnus-adapter-notebook@1"
    container = ("metadata",)
    key = "somnus"
    first = False

    def host_view(self, lines: list[str]) -> list[str]:
        """Cell sources (what a reader searches for), falling back to the canonical tree."""
        try:
            tree = self.tree_without_key("\n".join(lines))
        except ValueError:
            return list(lines)
        out: list[str] = []
        for cell in tree.get("cells", []) if isinstance(tree, dict) else []:
            src = cell.get("source", "") if isinstance(cell, dict) else ""
            out.extend(("".join(src) if isinstance(src, list) else str(src)).split("\n"))
        return out if out else json.dumps(tree, ensure_ascii=False, sort_keys=True, indent=1).split("\n")


JSON_KEY = JsonKeyCarrier()
NOTEBOOK = NotebookCarrier()
