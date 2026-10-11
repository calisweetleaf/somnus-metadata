"""Restricted YAML 1.2.2 subset: strict parser and canonical serializer (SPEC §16).

The parser accepts block mappings and sequences with space indentation,
single-line flow collections, quoted scalars, integers, finite decimals,
booleans, block scalars, and comments. It rejects nulls, anchors, aliases,
merge keys, tags, directives, document markers, duplicate keys, tabs in
indentation, non-string keys, and integers outside the 53-bit safe range.

``lenient=True`` additionally accepts unquoted plain strings; it exists only
for reading legacy v0.1 headers during migration.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional, Sequence

SAFE_INT = 2**53 - 1

_INT_RE = re.compile(r"-?(?:0|[1-9][0-9]*)\Z")
_FLOAT_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?\Z")
_PLAIN_KEY_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_.$\-]*")
_RESERVED_PLAIN = {"null", "Null", "NULL", "~", "true", "false", "True", "False", "TRUE", "FALSE"}
_NULLS = {"null", "Null", "NULL", "~"}

Path = tuple


class YAMLError(ValueError):
    """Restricted-YAML violation with a 1-based payload line and column."""

    def __init__(self, message: str, line: int, col: int = 1):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(f"line {line}, col {col}: {message}")


@dataclass
class Parsed:
    """Parsed value plus source positions keyed by path tuples (str keys, int indices)."""

    data: Any
    spans: dict = field(default_factory=dict)

    def position(self, path: Sequence) -> tuple[int, int]:
        """Return the nearest recorded (line, col) for a path, walking up to the root."""
        p = tuple(path)
        while p:
            if p in self.spans:
                return self.spans[p]
            p = p[:-1]
        return self.spans.get((), (1, 1))


@dataclass
class _Line:
    no: int  # 1-based payload line number
    indent: int
    content: str  # comment-stripped, right-stripped, without indentation


# --------------------------------------------------------------------------- scanning


def _strip_comment(text: str, line_no: int, col0: int) -> str:
    """Remove a trailing ``#`` comment that is outside quotes."""
    i = 0
    n = len(text)
    quote: Optional[str] = None
    while i < n:
        ch = text[i]
        if quote == '"':
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                quote = None
        elif quote == "'":
            if ch == "'":
                if i + 1 < n and text[i + 1] == "'":
                    i += 2
                    continue
                quote = None
        else:
            if ch in "\"'" and (i == 0 or text[i - 1] in " \t[{,:-"):
                quote = ch
            elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
                return text[:i].rstrip()
        i += 1
    return text.rstrip()


def _measure(raw: str, line_no: int) -> tuple[int, str]:
    indent = 0
    for ch in raw:
        if ch == " ":
            indent += 1
        elif ch == "\t":
            raise YAMLError("tab characters are forbidden in indentation", line_no, indent + 1)
        else:
            break
    return indent, raw[indent:]


# --------------------------------------------------------------------------- scalars


_ESCAPES = {
    "0": "\0", "a": "\a", "b": "\b", "t": "\t", "\t": "\t", "n": "\n", "v": "\v", "f": "\f",
    "r": "\r", "e": "\x1b", " ": " ", '"': '"', "/": "/", "\\": "\\", "N": "\x85",
    "_": "\xa0", "L": "\u2028", "P": "\u2029",
}


def _read_double(s: str, start: int, line: int, col0: int) -> tuple[str, int]:
    out: list[str] = []
    i = start + 1
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == '"':
            return "".join(out), i + 1
        if ch == "\\":
            if i + 1 >= n:
                break
            e = s[i + 1]
            if e in _ESCAPES:
                out.append(_ESCAPES[e])
                i += 2
                continue
            width = {"x": 2, "u": 4, "U": 8}.get(e)
            if width is None:
                raise YAMLError(f"unknown escape sequence \\{e}", line, col0 + i + 1)
            digits = s[i + 2 : i + 2 + width]
            if len(digits) != width or not re.fullmatch(r"[0-9A-Fa-f]+", digits):
                raise YAMLError(f"malformed \\{e} escape", line, col0 + i + 1)
            code = int(digits, 16)
            if code > 0x10FFFF:
                raise YAMLError("escape outside the Unicode range", line, col0 + i + 1)
            out.append(chr(code))
            i += 2 + width
            continue
        out.append(ch)
        i += 1
    raise YAMLError("unterminated double-quoted string", line, col0 + start + 1)


def _read_single(s: str, start: int, line: int, col0: int) -> tuple[str, int]:
    out: list[str] = []
    i = start + 1
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "'":
            if i + 1 < n and s[i + 1] == "'":
                out.append("'")
                i += 2
                continue
            return "".join(out), i + 1
        out.append(ch)
        i += 1
    raise YAMLError("unterminated single-quoted string", line, col0 + start + 1)


def _plain_scalar(token: str, line: int, col: int, lenient: bool) -> Any:
    if not token:
        raise YAMLError("empty value; null is forbidden", line, col)
    first = token[0]
    if first == "&":
        raise YAMLError("anchors are forbidden", line, col)
    if first == "*":
        raise YAMLError("aliases are forbidden", line, col)
    if first == "!":
        raise YAMLError("tags are forbidden", line, col)
    if first in "@`%":
        raise YAMLError(f"reserved indicator {first!r} cannot start a scalar", line, col)
    if token in _NULLS:
        raise YAMLError("null is forbidden; omit the field instead", line, col)
    if token == "true":
        return True
    if token == "false":
        return False
    if _INT_RE.match(token):
        value = int(token)
        if abs(value) > SAFE_INT:
            raise YAMLError("integer outside the signed 53-bit safe range", line, col)
        return value
    if _FLOAT_RE.match(token):
        value = float(token)
        if not math.isfinite(value):
            raise YAMLError("non-finite number", line, col)
        return value
    if token.lower() in {".inf", "-.inf", "+.inf", ".nan"}:
        raise YAMLError("non-finite numbers are forbidden", line, col)
    if lenient:
        return token
    raise YAMLError(f"unquoted string {token!r}; strings must be quoted", line, col)


# --------------------------------------------------------------------------- flow collections


class _Flow:
    def __init__(self, s: str, line: int, col0: int, lenient: bool, spans: dict, path: Path):
        self.s = s
        self.i = 0
        self.line = line
        self.col0 = col0
        self.lenient = lenient
        self.spans = spans
        self.path = path

    def err(self, msg: str) -> YAMLError:
        return YAMLError(msg, self.line, self.col0 + self.i + 1)

    def ws(self) -> None:
        while self.i < len(self.s) and self.s[self.i] in " \t":
            self.i += 1

    def value(self, path: Path) -> Any:
        self.ws()
        if self.i >= len(self.s):
            raise self.err("unexpected end of flow collection")
        self.spans[path] = (self.line, self.col0 + self.i + 1)
        ch = self.s[self.i]
        if ch == "[":
            return self.seq(path)
        if ch == "{":
            return self.mapping(path)
        if ch == '"':
            text, self.i = _read_double(self.s, self.i, self.line, self.col0)
            return text
        if ch == "'":
            text, self.i = _read_single(self.s, self.i, self.line, self.col0)
            return text
        start = self.i
        while self.i < len(self.s) and self.s[self.i] not in ",]}":
            if self.s[self.i] == ":" and (self.i + 1 >= len(self.s) or self.s[self.i + 1] in " ,]}"):
                break
            self.i += 1
        token = self.s[start : self.i].strip()
        return _plain_scalar(token, self.line, self.col0 + start + 1, self.lenient)

    def seq(self, path: Path) -> list:
        self.i += 1
        items: list = []
        self.ws()
        if self.i < len(self.s) and self.s[self.i] == "]":
            self.i += 1
            return items
        while True:
            items.append(self.value(path + (len(items),)))
            self.ws()
            if self.i >= len(self.s):
                raise self.err("unterminated flow sequence")
            ch = self.s[self.i]
            self.i += 1
            if ch == "]":
                return items
            if ch != ",":
                raise self.err("expected ',' or ']' in flow sequence")
            self.ws()
            if self.i < len(self.s) and self.s[self.i] == "]":
                raise self.err("trailing comma in flow sequence")

    def key(self) -> str:
        self.ws()
        if self.i >= len(self.s):
            raise self.err("unexpected end of flow mapping")
        ch = self.s[self.i]
        if ch == '"':
            text, self.i = _read_double(self.s, self.i, self.line, self.col0)
            return text
        if ch == "'":
            text, self.i = _read_single(self.s, self.i, self.line, self.col0)
            return text
        m = _PLAIN_KEY_RE.match(self.s, self.i)
        if not m:
            raise self.err("mapping keys must be strings")
        token = m.group(0)
        _check_plain_key(token, self.line, self.col0 + self.i + 1)
        self.i = m.end()
        return token

    def mapping(self, path: Path) -> dict:
        self.i += 1
        result: dict = {}
        self.ws()
        if self.i < len(self.s) and self.s[self.i] == "}":
            self.i += 1
            return result
        while True:
            key_col = self.col0 + self.i + 1
            k = self.key()
            if k in result:
                raise YAMLError(f"duplicate key {k!r}", self.line, key_col)
            self.ws()
            if self.i >= len(self.s) or self.s[self.i] != ":":
                raise self.err("expected ':' after flow mapping key")
            self.i += 1
            result[k] = self.value(path + (k,))
            self.ws()
            if self.i >= len(self.s):
                raise self.err("unterminated flow mapping")
            ch = self.s[self.i]
            self.i += 1
            if ch == "}":
                return result
            if ch != ",":
                raise self.err("expected ',' or '}' in flow mapping")


def _check_plain_key(token: str, line: int, col: int) -> None:
    if token == "<<":
        raise YAMLError("merge keys are forbidden", line, col)
    if token in _RESERVED_PLAIN:
        raise YAMLError(f"non-string mapping key {token!r}", line, col)


# --------------------------------------------------------------------------- block parser


class _Parser:
    def __init__(self, text: str, lenient: bool):
        if text.startswith("\ufeff"):
            text = text[1:]
        self.raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        self.i = 0
        self.pending: Optional[_Line] = None
        self.lenient = lenient
        self.spans: dict = {}

    # -- line access
    def peek(self) -> Optional[_Line]:
        if self.pending is not None:
            return self.pending
        while self.i < len(self.raw):
            raw = self.raw[self.i]
            no = self.i + 1
            if not raw.strip():
                self.i += 1
                continue
            indent, rest = _measure(raw, no)
            if rest.startswith("#"):
                self.i += 1
                continue
            if indent == 0 and (rest.rstrip() in ("---", "...") or rest.startswith("--- ")):
                raise YAMLError("document markers are forbidden inside the payload", no, 1)
            if indent == 0 and rest.startswith("%"):
                raise YAMLError("directives are forbidden", no, 1)
            content = _strip_comment(rest, no, indent)
            self.pending = _Line(no, indent, content)
            self.i += 1
            return self.pending
        return None

    def take(self) -> _Line:
        line = self.peek()
        assert line is not None
        self.pending = None
        return line

    # -- entry
    def document(self) -> Any:
        first = self.peek()
        if first is None:
            raise YAMLError("empty payload", 1, 1)
        if first.indent != 0:
            raise YAMLError("top-level content must start at column 1", first.no, first.indent + 1)
        value = self.block(0, ())
        trailing = self.peek()
        if trailing is not None:
            raise YAMLError("unexpected content after the top-level block", trailing.no, trailing.indent + 1)
        return value

    def block(self, indent: int, path: Path) -> Any:
        line = self.peek()
        assert line is not None
        if _is_seq_item(line.content):
            return self.sequence(line.indent, path)
        return self.mapping(line.indent, path)

    def mapping(self, indent: int, path: Path) -> dict:
        result: dict = {}
        while True:
            line = self.peek()
            if line is None or line.indent < indent:
                return result
            if line.indent > indent:
                raise YAMLError("unexpected indentation", line.no, line.indent + 1)
            if _is_seq_item(line.content):
                raise YAMLError("sequence item where a mapping key was expected", line.no, line.indent + 1)
            self.take()
            key, rest, key_col, rest_col = self.split_key(line)
            if key in result:
                raise YAMLError(f"duplicate key {key!r}", line.no, key_col)
            child = path + (key,)
            self.spans[child] = (line.no, key_col)
            result[key] = self.value_after_key(line, indent, rest, rest_col, child)

    def value_after_key(self, line: _Line, indent: int, rest: str, rest_col: int, path: Path) -> Any:
        if rest:
            if rest[0] in "|>":
                return self.block_scalar(rest, line, indent, rest_col)
            return self.inline(rest, line.no, rest_col, path)
        nxt = self.peek()
        if nxt is not None and nxt.indent > indent:
            return self.block(nxt.indent, path)
        if nxt is not None and nxt.indent == indent and _is_seq_item(nxt.content):
            return self.sequence(indent, path)
        raise YAMLError("missing value; null is forbidden", line.no, rest_col)

    def sequence(self, indent: int, path: Path) -> list:
        items: list = []
        while True:
            line = self.peek()
            if line is None or line.indent < indent:
                return items
            if line.indent > indent:
                raise YAMLError("unexpected indentation", line.no, line.indent + 1)
            if not _is_seq_item(line.content):
                return items
            self.take()
            child = path + (len(items),)
            self.spans[child] = (line.no, line.indent + 1)
            body = line.content[1:]
            gap = len(body) - len(body.lstrip(" "))
            rest = body.lstrip(" ")
            if not rest:
                nxt = self.peek()
                if nxt is None or nxt.indent <= indent:
                    raise YAMLError("empty sequence item; null is forbidden", line.no, line.indent + 1)
                items.append(self.block(nxt.indent, child))
                continue
            inner_indent = line.indent + 1 + gap
            if _is_seq_item(rest) or (rest[0] not in "\"'[{" and _looks_like_key(rest)) or (
                rest[0] in "\"'" and _quoted_key_follows(rest)
            ):
                self.pending = _Line(line.no, inner_indent, rest)
                items.append(self.block(inner_indent, child))
                continue
            if rest[0] in "|>":
                items.append(self.block_scalar(rest, line, indent, inner_indent + 1))
                continue
            items.append(self.inline(rest, line.no, inner_indent + 1, child))

    def split_key(self, line: _Line) -> tuple[str, str, int, int]:
        c = line.content
        key_col = line.indent + 1
        if c[0] in "\"'":
            reader = _read_double if c[0] == '"' else _read_single
            key, end = reader(c, 0, line.no, line.indent)
        elif c[0] in "[{":
            raise YAMLError("mapping keys must be strings", line.no, key_col)
        else:
            m = _PLAIN_KEY_RE.match(c)
            if not m:
                if c.startswith("<<"):
                    raise YAMLError("merge keys are forbidden", line.no, key_col)
                if c[0] in "&*!":
                    raise YAMLError("anchors, aliases, and tags are forbidden", line.no, key_col)
                raise YAMLError("expected a 'key: value' mapping entry", line.no, key_col)
            key = m.group(0)
            _check_plain_key(key, line.no, key_col)
            end = m.end()
        if end >= len(c) or c[end] != ":":
            if c.startswith("<<"):
                raise YAMLError("merge keys are forbidden", line.no, key_col)
            raise YAMLError("expected ':' after mapping key", line.no, line.indent + end + 1)
        after = c[end + 1 :]
        if after and after[0] != " ":
            raise YAMLError("a space is required after ':'", line.no, line.indent + end + 2)
        rest = after.strip()
        rest_col = line.indent + end + 2 + (len(after) - len(after.lstrip(" ")))
        return key, rest, key_col, rest_col

    def inline(self, s: str, line_no: int, col: int, path: Path) -> Any:
        self.spans.setdefault(path, (line_no, col))
        ch = s[0]
        if ch in "[{":
            flow = _Flow(s, line_no, col - 1, self.lenient, self.spans, path)
            value = flow.value(path)
            flow.ws()
            if flow.i != len(s):
                raise YAMLError("unexpected text after flow collection", line_no, col + flow.i)
            return value
        if ch in "\"'":
            reader = _read_double if ch == '"' else _read_single
            text, end = reader(s, 0, line_no, col - 1)
            if s[end:].strip():
                raise YAMLError("unexpected text after quoted string", line_no, col + end)
            return text
        return _plain_scalar(s, line_no, col, self.lenient)

    def block_scalar(self, header: str, line: _Line, parent_indent: int, col: int) -> str:
        m = re.fullmatch(r"([|>])([-+]?)", header)
        if not m:
            raise YAMLError("unsupported block scalar header", line.no, col)
        style, chomp = m.groups()
        if self.pending is not None:
            raise YAMLError("block scalar must end its line", line.no, col)
        start = self.i
        block_indent: Optional[int] = None
        collected: list[str] = []
        j = start
        while j < len(self.raw):
            raw = self.raw[j]
            if not raw.strip():
                collected.append("")
                j += 1
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if raw[indent:indent + 1] == "\t":
                raise YAMLError("tab characters are forbidden in indentation", j + 1, indent + 1)
            if block_indent is None:
                if indent <= parent_indent:
                    break
                block_indent = indent
            if indent < block_indent:
                break
            collected.append(raw[block_indent:])
            j += 1
        if j == len(self.raw) and collected and collected[-1] == "" and self.raw and self.raw[-1] == "":
            # the empty element after the payload's final newline is not a kept blank line
            collected.pop()
            j -= 1
        trailing = 0
        while collected and collected[-1] == "":
            collected.pop()
            trailing += 1
        self.i = start + len(collected) + trailing
        if block_indent is None:
            body = ""
        elif style == "|":
            body = "\n".join(collected)
        else:
            body = _fold(collected)
        if chomp == "-":
            return body
        if chomp == "+":
            return body + "\n" * (trailing + 1) if body else "\n" * trailing
        return body + "\n" if body else ""


def _fold(lines: list[str]) -> str:
    out = ""
    prev_blank = True
    for ln in lines:
        if ln == "":
            out += "\n"
            prev_blank = True
            continue
        if ln.startswith(" "):
            out += ("" if prev_blank or out.endswith("\n") else "\n") + ln
            prev_blank = False
            continue
        if out and not prev_blank and not out.endswith("\n"):
            out += " "
        out += ln
        prev_blank = False
    return out


def _is_seq_item(content: str) -> bool:
    return content == "-" or content.startswith("- ")


def _looks_like_key(s: str) -> bool:
    m = _PLAIN_KEY_RE.match(s)
    return bool(m) and m.end() < len(s) + 1 and s[m.end() : m.end() + 1] == ":" and (
        m.end() + 1 == len(s) or s[m.end() + 1] == " "
    )


def _quoted_key_follows(s: str) -> bool:
    try:
        reader = _read_double if s[0] == '"' else _read_single
        _, end = reader(s, 0, 0, 0)
    except YAMLError:
        return False
    return s[end : end + 1] == ":" and (end + 1 == len(s) or s[end + 1] == " ")


# --------------------------------------------------------------------------- public parse API


def parse(text: str, *, lenient: bool = False) -> Parsed:
    """Parse a restricted-YAML document, returning data and source spans."""
    parser = _Parser(text, lenient)
    data = parser.document()
    parser.spans.setdefault((), (1, 1))
    return Parsed(data, parser.spans)


def loads(text: str, *, lenient: bool = False) -> Any:
    """Parse a restricted-YAML document and return its value."""
    return parse(text, lenient=lenient).data


# --------------------------------------------------------------------------- serializer

OrderFn = Callable[[tuple], Optional[Sequence[str]]]


def _quote(s: str, forbid: Optional[str]) -> str:
    out = ['"']
    prev = ""
    for ch in s:
        o = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif o < 0x20 or o == 0x7F or 0x80 <= o < 0xA0 or ch in "\u2028\u2029\ufeff":
            out.append(f"\\u{o:04x}")
        elif forbid == "html" and ch == "-" and prev == "-":
            out.append("\\u002d")
        elif forbid == "block" and ch == "/" and prev == "*":
            out.append("\\u002f")
        else:
            out.append(ch)
        prev = ch
    out.append('"')
    return "".join(out)


def _key(k: Any) -> str:
    if not isinstance(k, str):
        raise TypeError(f"mapping keys must be strings, got {type(k).__name__}")
    if _PLAIN_KEY_RE.fullmatch(k) and k not in _RESERVED_PLAIN and k != "<<":
        return k
    return _quote(k, None)


def _scalar(v: Any, forbid: Optional[str]) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        if abs(v) > SAFE_INT:
            raise ValueError("integer outside the signed 53-bit safe range")
        return str(v)
    if isinstance(v, float):
        if not math.isfinite(v):
            raise ValueError("non-finite numbers cannot be serialized")
        return repr(v)
    if isinstance(v, str):
        return _quote(v, forbid)
    if v is None:
        raise ValueError("null cannot be serialized; omit the field")
    raise TypeError(f"unsupported value type {type(v).__name__}")


def _is_scalar(v: Any) -> bool:
    return isinstance(v, (str, int, float, bool))


class _Dumper:
    def __init__(self, order: Optional[OrderFn], forbid: Optional[str], width: int):
        self.order = order
        self.forbid = forbid
        self.width = width

    def keys(self, d: dict, path: tuple) -> list:
        declared = list(self.order(path) or []) if self.order else []
        known = [k for k in declared if k in d]
        return known + [k for k in d if k not in declared]

    def flow(self, items: list) -> str:
        return "[" + ", ".join(_scalar(v, self.forbid) for v in items) + "]"

    def mapping(self, d: dict, indent: int, path: tuple) -> list[str]:
        lines: list[str] = []
        pad = " " * indent
        for k in self.keys(d, path):
            v = d[k]
            head = f"{pad}{_key(k)}:"
            if isinstance(v, dict):
                if not v:
                    lines.append(head + " {}")
                else:
                    lines.append(head)
                    lines.extend(self.mapping(v, indent + 2, path + (k,)))
            elif isinstance(v, list):
                lines.extend(self.list_after(head, v, indent, path + (k,)))
            else:
                lines.append(f"{head} {_scalar(v, self.forbid)}")
        return lines

    def list_after(self, head: str, v: list, indent: int, path: tuple) -> list[str]:
        if not v:
            return [head + " []"]
        if all(_is_scalar(x) for x in v):
            candidate = f"{head} {self.flow(v)}"
            if len(candidate) <= self.width:
                return [candidate]
        return [head] + self.sequence(v, indent + 2, path)

    def sequence(self, items: list, indent: int, path: tuple) -> list[str]:
        lines: list[str] = []
        pad = " " * indent
        item_path = path + ("[]",)
        for item in items:
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{pad}- {{}}")
                    continue
                sub = self.mapping(item, indent + 2, item_path)
                sub[0] = f"{pad}- " + sub[0][indent + 2 :]
                lines.extend(sub)
            elif isinstance(item, list):
                if not item:
                    lines.append(f"{pad}- []")
                elif all(_is_scalar(x) for x in item) and len(pad) + 2 + len(self.flow(item)) <= self.width:
                    lines.append(f"{pad}- {self.flow(item)}")
                else:
                    sub = self.sequence(item, indent + 2, item_path)
                    sub[0] = f"{pad}- " + sub[0][indent + 2 :]
                    lines.extend(sub)
            else:
                lines.append(f"{pad}- {_scalar(item, self.forbid)}")
        return lines


def dumps(value: dict, *, order: Optional[OrderFn] = None, forbid: Optional[str] = None,
          width: int = 88) -> str:
    """Serialize a mapping in canonical form; output always ends with a newline.

    ``order(path)`` returns the declared key order for the mapping at ``path``
    (keys as str, sequence items as ``"[]"``). ``forbid`` is ``"html"`` or
    ``"block"`` to escape carrier-forbidden sequences inside strings.
    """
    if not isinstance(value, dict):
        raise TypeError("top-level value must be a mapping")
    lines = _Dumper(order, forbid, width).mapping(value, 0, ())
    return "\n".join(lines) + "\n"


def iter_strings(value: Any) -> Iterable[str]:
    """Yield every string (keys and values) inside a parsed value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from iter_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from iter_strings(v)
