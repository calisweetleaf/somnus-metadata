#!/usr/bin/env python3
"""Somnus Markdown Metadata Standard validator (stdlib-only).

Three-stage pipeline per Somnus Markdown Metadata Standard Research:
  Stage 1: Grammar and structural parse (YAML 1.2 strict subset).
  Stage 2: Schema conformance (jsonschema if available, else structural fallback).
  Stage 3: Semantic and referential integrity.

CLI:
  python3 tools/validate.py <path>

Exit codes:
  0 = valid (warnings allowed)
  1 = validation failed (Stage 1/2/3 errors)
  2 = usage or I/O error (missing file, unreadable, no frontmatter)

Only the Python standard library is used. The optional ``jsonschema``
third-party package is used opportunistically; absence never crashes.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UUIDV7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PROFILE_RE = re.compile(r"^somnus://profiles/[a-z0-9/\-]+$")
CORE_SCHEMA_RE = re.compile(r"^somnus://core/v[0-9]+$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
DATETIME_Z_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
URN_DOI_RE = re.compile(r"^(urn:[a-z0-9][a-z0-9\-]*:.+|doi:10\.[0-9]{4,9}/.+)$")
ACTOR_ID_RE = re.compile(r"^(user|agent|system):.+$")
COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")
# Version-like means SemVer-shaped (at least two dots, e.g. 0.1.0). Plain
# floats such as 1.42 or 4.87 are legitimate numbers for metric fields and
# must NOT warn; they fall through to numeric parsing below.
VERSION_LIKE_RE = re.compile(r"^\d+\.\d+\.\d+(\.\d+)*$")
DATE_LIKE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ].*)?$")

# YAML 1.1-only boolean spellings that must warn under YAML 1.2 Core.
AMBIGUOUS_BOOLEANS = {
    "y", "Y", "n", "N",
    "yes", "Yes", "YES", "no", "No", "NO",
    "on", "On", "ON", "off", "Off", "OFF",
    "True", "TRUE", "False", "FALSE",
}

CATEGORY_ENUM = ["research", "engineering", "operations", "governance", "context", "archive"]
TYPE_ENUM = [
    "whitepaper", "specification", "architecture-record", "report", "task",
    "plan", "notepad", "benchmark", "test-result", "decision-record",
    "runbook", "index", "state", "memory",
]
ROLE_ENUM = ["normative", "informative", "working", "exploratory", "historical"]
SCOPE_ENUM = ["ecosystem", "fleet", "repository", "subsystem", "module", "component"]
STATUS_ENUM = [
    "draft", "provisional", "active", "experimental",
    "superseded", "deprecated", "historical", "archived",
]
ACTIONS_ENUM = [
    "authored", "generated", "edited", "reviewed", "verified",
    "tested", "migrated", "reformatted", "canonized", "deprecated",
]
VERIFICATION_STATUS_ENUM = ["passed", "failed", "pending"]

REQUIRED_ROOT = [
    "somnus", "id", "slug", "title",
    "classification", "lifecycle", "location", "origin", "provenance",
]

PROFILE_TO_FILE = {
    "somnus://profiles/engineering/specification/v1": "schemas/v1/profiles/engineering-specification-v1.json",
    "somnus://profiles/engineering/benchmark/v1": "schemas/v1/profiles/engineering-benchmark-v1.json",
    "somnus://core/v1": "schemas/v1/core.json",
}

SUBMATTER_OPEN_RE = re.compile(r"^(?P<colons>:{3,})submatter:(?P<kind>[A-Za-z0-9_\-]+)(?P<rest>.*)$")
SUBMATTER_CLOSE_RE = re.compile(r"^:{3,}\s*$")
SUBMATTER_ID_RE = re.compile(r'id\s*=\s*"([^"]+)"')


# ---------------------------------------------------------------------------
# Small YAML-subset parser (strict, stdlib-only)
# ---------------------------------------------------------------------------

class FrontmatterParser:
    """Minimal block-YAML parser for Somnus frontmatter.

    Supports the subset emitted by Somnus examples:
      - nested maps via indentation (spaces only)
      - block sequences via ``- ``
      - sequences of scalars and sequences of maps (including nested
        ``actions:`` lists inside operator maps)
      - quoted strings, ``true``/``false`` booleans, ints, floats,
        ``[]`` empty lists, simple inline ``[a, b]`` lists
      - ``#`` full-line comments and trailing `` #`` comments on
        unquoted scalars

    Tracks duplicate keys and unquoted ambiguous scalars.
    """

    def __init__(self, raw: str) -> None:
        self.raw: str = raw
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.lines: list[tuple[int, int, str]] = []

    def _prepare_lines(self) -> None:
        for idx, raw_line in enumerate(self.raw.splitlines(), start=1):
            if "\t" in raw_line:
                # Tab check is also performed globally; record per-line context.
                self.errors.append(f"[Stage1] line {idx}: tab character is forbidden in YAML frontmatter")
            stripped = raw_line.strip()
            if stripped == "" or stripped.startswith("#"):
                continue
            # Indent measured in spaces; tabs already rejected.
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            # If line has leading tabs mixed with spaces, indent calc above
            # still works because tabs were flagged; treat remainder as content.
            content = stripped
            # Skip document markers if any leak in (should not happen).
            if content in ("---", "..."):
                continue
            self.lines.append((idx, indent, content))

    def parse(self) -> Optional[dict[str, Any]]:
        self._prepare_lines()
        if self.errors:
            return None
        if not self.lines:
            self.errors.append("[Stage1] frontmatter block is empty")
            return None
        try:
            data, pos = self._parse_map(0, -1)
        except RecursionError as exc:
            self.errors.append(f"[Stage1] frontmatter nesting too deep: {exc}")
            return None
        if pos != len(self.lines):
            lineno, _indent, content = self.lines[pos]
            self.errors.append(
                f"[Stage1] line {lineno}: unexpected trailing content {content!r}"
            )
            return None
        if not isinstance(data, dict):
            self.errors.append("[Stage1] frontmatter root must be a mapping")
            return None
        return data

    # -- scalar helpers ----------------------------------------------------

    def _strip_trailing_comment(self, value: str) -> str:
        if " #" in value:
            return value.split(" #", 1)[0].rstrip()
        return value

    def _is_mapping_item(self, after: str) -> bool:
        """True when a ``- <text>`` list line starts a mapping item.

        Quoted scalars (e.g. ``- "urn:somnus:doc:..."``) and bare
        URN/DOI/URI scalars contain colons but are NOT mappings.
        """
        s = after.strip()
        if s == "":
            return False
        if s[0] in ("\"", "'"):
            return False
        if s.startswith("urn:") or s.startswith("doi:"):
            return False
        if "://" in s.split(":")[0] or "://" in s:
            # Catches unquoted URIs such as somnus://... if ever listed bare.
            # Quoted ones already returned False above.
            if s[0] not in ("\"", "'") and re.match(r"^[A-Za-z0-9_\-\.]+://", s) is None:
                pass
            elif "://" in s:
                return False
        if ":" not in s:
            return False
        key, _val = s.split(":", 1)
        key = key.strip()
        if key == "":
            return False
        if not re.match(r"^[A-Za-z0-9_\-\.]+$", key):
            return False
        return True

    def _parse_inline_list(self, text: str, lineno: int) -> list[Any]:
        inner = text[1:-1].strip()
        if inner == "":
            return []
        items: list[Any] = []
        # Simple comma split respecting double/single quotes.
        cur = ""
        in_single = False
        in_double = False
        for ch in inner:
            if ch == "'" and not in_double:
                in_single = not in_single
                cur += ch
            elif ch == '"' and not in_single:
                in_double = not in_double
                cur += ch
            elif ch == "," and not in_single and not in_double:
                items.append(self._parse_scalar(cur.strip(), lineno))
                cur = ""
            else:
                cur += ch
        if cur.strip() != "" or inner.endswith(","):
            items.append(self._parse_scalar(cur.strip(), lineno))
        return items

    def _parse_scalar(self, text: str, lineno: int) -> Any:
        v = self._strip_trailing_comment(text.strip())
        if v == "":
            return ""
        if v == "[]":
            return []
        if v == "{}":
            return {}
        if v.startswith("[") and v.endswith("]"):
            return self._parse_inline_list(v, lineno)
        if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
            return v[1:-1]
        # Unquoted scalar.
        if v in ("true", "false"):
            return v == "true"
        if v in ("null", "Null", "NULL", "~"):
            return None
        if v in AMBIGUOUS_BOOLEANS:
            self.warnings.append(
                f"[Stage1] line {lineno}: unquoted ambiguous scalar {v!r} "
                f"(YAML 1.1 boolean trap; quote it, e.g. \"{v}\")"
            )
            return v
        if VERSION_LIKE_RE.match(v):
            self.warnings.append(
                f"[Stage1] line {lineno}: unquoted version-like scalar {v!r} "
                f"(would coerce to float; quote it, e.g. \"{v}\")"
            )
            return v
        if DATE_LIKE_RE.match(v):
            self.warnings.append(
                f"[Stage1] line {lineno}: unquoted date-like scalar {v!r} "
                f"(implicit timestamp trap; quote it, e.g. \"{v}\")"
            )
            return v
        # Numeric coercion for genuine numbers (memory_gb, metric values).
        try:
            return int(v)
        except ValueError:
            pass
        try:
            return float(v)
        except ValueError:
            pass
        return v

    # -- map / list parsing -------------------------------------------------

    def _parse_map(self, pos: int, parent_indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        seen: set[str] = set()
        n = len(self.lines)
        while pos < n:
            lineno, indent, content = self.lines[pos]
            if indent <= parent_indent:
                break
            if content.startswith("- ") or content == "-":
                break
            if ":" not in content:
                self.errors.append(f"[Stage1] line {lineno}: expected 'key: value', got {content!r}")
                pos += 1
                continue
            key, raw_val = content.split(":", 1)
            key = key.strip()
            raw_val = raw_val.strip()
            if key == "":
                self.errors.append(f"[Stage1] line {lineno}: empty mapping key")
                pos += 1
                continue
            if not re.match(r"^[A-Za-z0-9_\-\.]+$", key):
                self.errors.append(f"[Stage1] line {lineno}: invalid mapping key {key!r}")
                pos += 1
                continue
            if key in seen:
                self.errors.append(f"[Stage1] line {lineno}: duplicate mapping key {key!r}")
                pos += 1
                continue
            seen.add(key)
            # Empty value -> nested block follows.
            if raw_val == "":
                if pos + 1 >= n:
                    self.errors.append(f"[Stage1] line {lineno}: key {key!r} expects nested block, found end of frontmatter")
                    result[key] = None
                    pos += 1
                    continue
                _nl, next_indent, next_content = self.lines[pos + 1]
                if next_indent <= indent:
                    self.errors.append(
                        f"[Stage1] line {lineno}: key {key!r} expects indented block, "
                        f"next line indent {next_indent} is not deeper than {indent}"
                    )
                    result[key] = None
                    pos += 1
                    continue
                if next_content.startswith("- ") or next_content == "-":
                    val, pos = self._parse_list(pos + 1, indent)
                    result[key] = val
                    continue
                val, pos = self._parse_map(pos + 1, indent)
                result[key] = val
                continue
            # Inline value.
            raw_val = self._strip_trailing_comment(raw_val)
            if raw_val == "":
                result[key] = ""
            else:
                result[key] = self._parse_scalar(raw_val, lineno)
            pos += 1
        return result, pos

    def _parse_list(self, pos: int, parent_indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        n = len(self.lines)
        if pos >= n:
            self.errors.append("[Stage1] expected list items, found end of frontmatter")
            return result, pos
        _fl, list_indent, _fc = self.lines[pos]
        if list_indent <= parent_indent:
            self.errors.append("[Stage1] list items must be indented deeper than parent key")
            return result, pos
        while pos < n:
            lineno, indent, content = self.lines[pos]
            if indent < list_indent:
                break
            if indent > list_indent:
                self.errors.append(
                    f"[Stage1] line {lineno}: unexpected indent {indent} "
                    f"(list level is {list_indent}; possible missing '- '?)"
                )
                pos += 1
                continue
            # indent == list_indent
            if not (content.startswith("- ") or content == "-"):
                break
            if content == "-":
                # Bare dash: nested block follows or null item.
                if pos + 1 < n and self.lines[pos + 1][1] > indent:
                    _nl, _ni, nc = self.lines[pos + 1]
                    if nc.startswith("- ") or nc == "-":
                        val, pos = self._parse_list(pos + 1, indent)
                    else:
                        val, pos = self._parse_map(pos + 1, indent)
                    result.append(val)
                    continue
                result.append(None)
                pos += 1
                continue
            after = content[2:].strip()
            if after == "":
                if pos + 1 < n and self.lines[pos + 1][1] > indent:
                    _nl, _ni, nc = self.lines[pos + 1]
                    if nc.startswith("- ") or nc == "-":
                        val, pos = self._parse_list(pos + 1, indent)
                    else:
                        val, pos = self._parse_map(pos + 1, indent)
                    result.append(val)
                    continue
                result.append(None)
                pos += 1
                continue
            if self._is_mapping_item(after):
                # First key of a mapping item (e.g. "- name: ...").
                # Quoted scalars with colons (URNs/DOIs/URIs) fall through
                # to the scalar branch below.
                k, v = after.split(":", 1)
                k = k.strip()
                v = v.strip()
                if k == "":
                    self.errors.append(f"[Stage1] line {lineno}: empty key in list item")
                    pos += 1
                    continue
                item: dict[str, Any] = {}
                seen: set[str] = set()
                seen.add(k)
                if v == "":
                    # Value is nested block.
                    if pos + 1 < n and self.lines[pos + 1][1] > indent:
                        _nl, _ni, nc = self.lines[pos + 1]
                        # Nested under k: indent must be deeper than list level.
                        # Peek: list or map?
                        tmp_pos = pos + 1
                        if nc.startswith("- ") or nc == "-":
                            nested, tmp_pos = self._parse_list(pos + 1, indent + 2)
                        else:
                            # The nested map's parent indent is indent+2-ish;
                            # use indent as parent so keys at any deeper indent parse.
                            nested, tmp_pos = self._parse_map(pos + 1, indent)
                        item[k] = nested
                        pos = tmp_pos
                    else:
                        item[k] = None
                        pos += 1
                else:
                    v = self._strip_trailing_comment(v)
                    item[k] = self._parse_scalar(v, lineno)
                    pos += 1
                # Consume continuation keys belonging to the same mapping item.
                while pos < n:
                    nl2, ni2, nc2 = self.lines[pos]
                    if ni2 <= indent:
                        break
                    if ni2 == list_indent and (nc2.startswith("- ") or nc2 == "-"):
                        break
                    if nc2.startswith("- ") or nc2 == "-":
                        self.errors.append(
                            f"[Stage1] line {nl2}: unexpected list item inside mapping item"
                        )
                        pos += 1
                        continue
                    if ":" not in nc2:
                        self.errors.append(
                            f"[Stage1] line {nl2}: expected 'key: value' in mapping item, got {nc2!r}"
                        )
                        pos += 1
                        continue
                    ck, cv = nc2.split(":", 1)
                    ck = ck.strip()
                    cv = cv.strip()
                    if ck in seen:
                        self.errors.append(
                            f"[Stage1] line {nl2}: duplicate mapping key {ck!r} in list item"
                        )
                        pos += 1
                        continue
                    seen.add(ck)
                    if cv == "":
                        if pos + 1 < n and self.lines[pos + 1][1] > ni2:
                            nn_c = self.lines[pos + 1][2]
                            if nn_c.startswith("- ") or nn_c == "-":
                                nested2, pos = self._parse_list(pos + 1, ni2)
                                item[ck] = nested2
                                continue
                            nested2, pos = self._parse_map(pos + 1, ni2)
                            item[ck] = nested2
                            continue
                        item[ck] = None
                        pos += 1
                        continue
                    cv = self._strip_trailing_comment(cv)
                    item[ck] = self._parse_scalar(cv, nl2)
                    pos += 1
                result.append(item)
                continue
            # Scalar item.
            result.append(self._parse_scalar(after, lineno))
            pos += 1
        return result, pos


# ---------------------------------------------------------------------------
# Stage 1: frontmatter extraction + submatter scan
# ---------------------------------------------------------------------------

def extract_frontmatter(text: str) -> tuple[Optional[str], str, list[str]]:
    """Split Markdown into (frontmatter_raw, body, errors)."""
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append("[Stage1] missing opening '---' frontmatter delimiter on line 1")
        return None, text, errors
    end: Optional[int] = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        errors.append("[Stage1] missing closing '---' frontmatter delimiter")
        return None, text, errors
    raw = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:])
    return raw, body, errors


def check_submatter(body: str) -> tuple[list[str], list[str]]:
    """Validate :::submatter directive balance and id attributes.

    Returns (errors, warnings). Nesting uses colon-count stacking:
    ``::::`` outer may contain ``:::`` inner; closers must match.
    """
    errors: list[str] = []
    warnings: list[str] = []
    stack: list[tuple[int, str, int]] = []
    for lineno, raw_line in enumerate(body.splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped == "":
            continue
        m_open = SUBMATTER_OPEN_RE.match(stripped)
        if m_open:
            colons = len(m_open.group("colons"))
            kind = m_open.group("kind")
            rest = m_open.group("rest") or ""
            # Rest should look like {attr="..."} or be empty.
            if rest.strip() != "" and not rest.strip().startswith("{"):
                warnings.append(
                    f"[Stage1] body line {lineno}: submatter:{kind} attributes "
                    f"should use {{key=\"value\"}} form, got {rest.strip()!r}"
                )
            m_id = SUBMATTER_ID_RE.search(rest)
            if not m_id:
                warnings.append(
                    f"[Stage1] body line {lineno}: submatter:{kind} is missing id=\"...\" attribute"
                )
            else:
                sid = m_id.group(1)
                if not UUIDV7_RE.match(sid.lower()):
                    warnings.append(
                        f"[Stage1] body line {lineno}: submatter id {sid!r} "
                        f"is not a lowercase UUIDv7"
                    )
            stack.append((colons, kind, lineno))
            continue
        if SUBMATTER_CLOSE_RE.match(stripped):
            if not stack:
                errors.append(f"[Stage1] body line {lineno}: closing '{stripped}' without opening submatter")
                continue
            opened_colons, opened_kind, opened_line = stack.pop()
            if len(stripped) != opened_colons:
                errors.append(
                    f"[Stage1] body line {lineno}: closing '{stripped}' "
                    f"does not match opening :::*{opened_colons} for submatter:{opened_kind} "
                    f"(opened line {opened_line})"
                )
            continue
    for colons, kind, opened_line in stack:
        errors.append(
            f"[Stage1] body line {opened_line}: unclosed :::submatter:{kind} "
            f"(expected closing ':'*{colons})"
        )
    return errors, warnings


# ---------------------------------------------------------------------------
# Stage 2: structural fallback + optional jsonschema
# ---------------------------------------------------------------------------

def _err(path: str, msg: str) -> str:
    return f"[Stage2] {path}: {msg}"


def validate_structural(data: dict[str, Any]) -> list[str]:
    """Closed structural check mirroring schemas/v1/core.json + profiles."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["[Stage2] frontmatter root must be a mapping"]

    allowed_root = {
        "somnus", "id", "slug", "title", "aliases", "description",
        "created_at", "updated_at", "classification", "lifecycle",
        "relations", "location", "origin", "provenance", "extensions",
        "specification", "benchmark",
    }
    for key in data:
        if key not in allowed_root:
            errors.append(_err(key, f"unknown root property {key!r} (unevaluatedProperties false)"))

    for key in REQUIRED_ROOT:
        if key not in data:
            errors.append(_err(key, "missing required property"))

    # somnus block
    somnus = data.get("somnus")
    if isinstance(somnus, dict):
        if "version" not in somnus:
            errors.append(_err("somnus.version", "missing required property"))
        elif not isinstance(somnus["version"], str) or not VERSION_RE.match(somnus["version"]):
            errors.append(_err("somnus.version", f"must be SemVer string, got {somnus.get('version')!r}"))
        if "schema" not in somnus:
            errors.append(_err("somnus.schema", "missing required property"))
        elif not isinstance(somnus["schema"], str) or not CORE_SCHEMA_RE.match(somnus["schema"]):
            errors.append(_err("somnus.schema", f"must match somnus://core/vN, got {somnus.get('schema')!r}"))
        for k in somnus:
            if k not in ("version", "schema"):
                errors.append(_err(f"somnus.{k}", f"unknown property {k!r}"))
    elif "somnus" in data:
        errors.append(_err("somnus", f"must be object, got {type(somnus).__name__}"))

    # identity
    if "id" in data:
        if not isinstance(data["id"], str) or not UUIDV7_RE.match(data["id"]):
            errors.append(_err("id", f"must be lowercase RFC 9562 UUIDv7, got {data.get('id')!r}"))
    if "slug" in data:
        if not isinstance(data["slug"], str) or not KEBAB_RE.match(data["slug"]):
            errors.append(_err("slug", f"must be kebab-case, got {data.get('slug')!r}"))
    if "title" in data:
        if not isinstance(data["title"], str) or data["title"].strip() == "":
            errors.append(_err("title", "must be non-empty string"))
    if "aliases" in data:
        aliases = data["aliases"]
        if not isinstance(aliases, list):
            errors.append(_err("aliases", "must be array"))
        else:
            for i, a in enumerate(aliases):
                if not isinstance(a, str) or not KEBAB_RE.match(a):
                    errors.append(_err(f"aliases[{i}]", f"must be kebab-case string, got {a!r}"))
    for tkey in ("created_at", "updated_at"):
        if tkey in data and data[tkey] is not None:
            if not isinstance(data[tkey], str) or not DATETIME_Z_RE.match(data[tkey]):
                errors.append(_err(tkey, f"must be ISO 8601 UTC Zulu string, got {data.get(tkey)!r}"))

    # classification
    cls = data.get("classification")
    if isinstance(cls, dict):
        for req in ("category", "type", "role", "scope", "profile"):
            if req not in cls:
                errors.append(_err(f"classification.{req}", "missing required property"))
        if "category" in cls and cls["category"] not in CATEGORY_ENUM:
            errors.append(_err("classification.category", f"must be one of {CATEGORY_ENUM}, got {cls.get('category')!r}"))
        if "type" in cls and cls["type"] not in TYPE_ENUM:
            errors.append(_err("classification.type", f"must be one of {TYPE_ENUM}, got {cls.get('type')!r}"))
        if "role" in cls and cls["role"] not in ROLE_ENUM:
            errors.append(_err("classification.role", f"must be one of {ROLE_ENUM}, got {cls.get('role')!r}"))
        if "scope" in cls and cls["scope"] not in SCOPE_ENUM:
            errors.append(_err("classification.scope", f"must be one of {SCOPE_ENUM}, got {cls.get('scope')!r}"))
        if "subtype" in cls and cls["subtype"] is not None:
            if not isinstance(cls["subtype"], str) or not KEBAB_RE.match(cls["subtype"]):
                errors.append(_err("classification.subtype", f"must be kebab-case, got {cls.get('subtype')!r}"))
        if "profile" in cls:
            if not isinstance(cls["profile"], str) or not PROFILE_RE.match(cls["profile"]):
                errors.append(_err("classification.profile", f"must match ^somnus://profiles/[a-z0-9/-]+$, got {cls.get('profile')!r}"))
        if "tags" in cls and cls["tags"] is not None:
            tags = cls["tags"]
            if not isinstance(tags, list):
                errors.append(_err("classification.tags", "must be array"))
            else:
                for i, t in enumerate(tags):
                    if not isinstance(t, str) or not KEBAB_RE.match(t):
                        errors.append(_err(f"classification.tags[{i}]", f"must be kebab-case string, got {t!r}"))
        for k in cls:
            if k not in ("category", "type", "subtype", "profile", "role", "scope", "tags"):
                errors.append(_err(f"classification.{k}", f"unknown property {k!r}"))
    elif "classification" in data:
        errors.append(_err("classification", "must be object"))

    # lifecycle
    life = data.get("lifecycle")
    if isinstance(life, dict):
        if "status" not in life:
            errors.append(_err("lifecycle.status", "missing required property"))
        elif life["status"] not in STATUS_ENUM:
            errors.append(_err("lifecycle.status", f"must be one of {STATUS_ENUM}, got {life.get('status')!r}"))
        if "is_canonical" not in life:
            errors.append(_err("lifecycle.is_canonical", "missing required property"))
        elif not isinstance(life["is_canonical"], bool):
            errors.append(_err("lifecycle.is_canonical", f"must be boolean, got {life.get('is_canonical')!r}"))
        if "reviewed_at" in life and life["reviewed_at"] is not None:
            if not isinstance(life["reviewed_at"], str) or not DATETIME_Z_RE.match(life["reviewed_at"]):
                errors.append(_err("lifecycle.reviewed_at", f"must be ISO 8601 UTC Zulu, got {life.get('reviewed_at')!r}"))
        for k in life:
            if k not in ("status", "is_canonical", "reviewed_at"):
                errors.append(_err(f"lifecycle.{k}", f"unknown property {k!r}"))
    elif "lifecycle" in data:
        errors.append(_err("lifecycle", "must be object"))

    # relations
    rel = data.get("relations")
    if rel is not None and isinstance(rel, dict):
        for rk in ("supersedes", "superseded_by", "derived_from", "cites", "complements"):
            if rk in rel and rel[rk] is not None:
                arr = rel[rk]
                if not isinstance(arr, list):
                    errors.append(_err(f"relations.{rk}", "must be array"))
                    continue
                for i, v in enumerate(arr):
                    if not isinstance(v, str) or not URN_DOI_RE.match(v):
                        errors.append(_err(f"relations.{rk}[{i}]", f"must be URN or DOI string, got {v!r}"))
        for k in rel:
            if k not in ("supersedes", "superseded_by", "derived_from", "cites", "complements"):
                errors.append(_err(f"relations.{k}", f"unknown property {k!r}"))
    elif "relations" in data and rel is not None:
        errors.append(_err("relations", "must be object"))

    # location / origin
    for block_name in ("location", "origin"):
        blk = data.get(block_name)
        if isinstance(blk, dict):
            if "repository" not in blk:
                errors.append(_err(f"{block_name}.repository", "missing required property"))
            elif not isinstance(blk["repository"], str) or blk["repository"].strip() == "":
                errors.append(_err(f"{block_name}.repository", "must be non-empty string"))
            if "path" not in blk:
                errors.append(_err(f"{block_name}.path", "missing required property"))
            elif not isinstance(blk["path"], str) or blk["path"].strip() == "":
                errors.append(_err(f"{block_name}.path", "must be non-empty string"))
            if block_name == "location":
                if "historical_paths" in blk and blk["historical_paths"] is not None:
                    hp = blk["historical_paths"]
                    if not isinstance(hp, list):
                        errors.append(_err("location.historical_paths", "must be array"))
                    else:
                        for i, p in enumerate(hp):
                            if not isinstance(p, str) or p.strip() == "":
                                errors.append(_err(f"location.historical_paths[{i}]", "must be non-empty string"))
                for k in blk:
                    if k not in ("repository", "repository_root", "path", "historical_paths"):
                        errors.append(_err(f"location.{k}", f"unknown property {k!r}"))
            else:
                if "initial_commit" in blk and blk["initial_commit"] is not None:
                    if not isinstance(blk["initial_commit"], str) or not COMMIT_RE.match(blk["initial_commit"]):
                        errors.append(_err("origin.initial_commit", f"must be hex commit hash, got {blk.get('initial_commit')!r}"))
                for k in blk:
                    if k not in ("repository", "path", "initial_commit"):
                        errors.append(_err(f"origin.{k}", f"unknown property {k!r}"))
        elif block_name in data:
            errors.append(_err(block_name, "must be object"))

    # provenance
    prov = data.get("provenance")
    if isinstance(prov, dict):
        if "authors" not in prov:
            errors.append(_err("provenance.authors", "missing required property"))
        elif not isinstance(prov["authors"], list) or len(prov["authors"]) == 0:
            errors.append(_err("provenance.authors", "must be non-empty array"))
        else:
            for i, a in enumerate(prov["authors"]):
                if not isinstance(a, dict):
                    errors.append(_err(f"provenance.authors[{i}]", "must be object"))
                    continue
                if "name" not in a or not isinstance(a.get("name"), str) or str(a.get("name")).strip() == "":
                    errors.append(_err(f"provenance.authors[{i}].name", "missing or empty"))
                if "id" not in a or not isinstance(a.get("id"), str) or not ACTOR_ID_RE.match(str(a.get("id"))):
                    errors.append(_err(f"provenance.authors[{i}].id", f"must match ^(user|agent|system):.+, got {a.get('id')!r}"))
                for k in a:
                    if k not in ("name", "id", "role"):
                        errors.append(_err(f"provenance.authors[{i}].{k}", f"unknown property {k!r}"))
        if "operators" in prov and prov["operators"] is not None:
            ops = prov["operators"]
            if not isinstance(ops, list):
                errors.append(_err("provenance.operators", "must be array"))
            else:
                for i, o in enumerate(ops):
                    if not isinstance(o, dict):
                        errors.append(_err(f"provenance.operators[{i}]", "must be object"))
                        continue
                    for req in ("name", "operator", "interaction_at", "actions"):
                        if req not in o:
                            errors.append(_err(f"provenance.operators[{i}].{req}", "missing required property"))
                    if "name" in o and (not isinstance(o.get("name"), str) or str(o.get("name")).strip() == ""):
                        errors.append(_err(f"provenance.operators[{i}].name", "must be non-empty string"))
                    if "id" in o and o["id"] is not None:
                        if not isinstance(o["id"], str) or not ACTOR_ID_RE.match(o["id"]):
                            errors.append(_err(f"provenance.operators[{i}].id", f"must match ^(user|agent|system):.+, got {o.get('id')!r}"))
                    if "interaction_at" in o and o["interaction_at"] is not None:
                        if not isinstance(o["interaction_at"], str) or not DATETIME_Z_RE.match(o["interaction_at"]):
                            errors.append(_err(f"provenance.operators[{i}].interaction_at", f"must be ISO 8601 UTC Zulu, got {o.get('interaction_at')!r}"))
                    if "actions" in o and o["actions"] is not None:
                        acts = o["actions"]
                        if not isinstance(acts, list) or len(acts) == 0:
                            errors.append(_err(f"provenance.operators[{i}].actions", "must be non-empty array"))
                        else:
                            for j, act in enumerate(acts):
                                if act not in ACTIONS_ENUM:
                                    errors.append(_err(
                                        f"provenance.operators[{i}].actions[{j}]",
                                        f"must be one of {ACTIONS_ENUM}, got {act!r}",
                                    ))
                    for k in o:
                        if k not in ("name", "id", "role", "model", "operator", "interaction_at", "actions"):
                            errors.append(_err(f"provenance.operators[{i}].{k}", f"unknown property {k!r}"))
        if "verification" in prov and prov["verification"] is not None:
            ver = prov["verification"]
            if not isinstance(ver, dict):
                errors.append(_err("provenance.verification", "must be object"))
            else:
                if "verified_at" in ver and ver["verified_at"] is not None:
                    if not isinstance(ver["verified_at"], str) or not DATETIME_Z_RE.match(ver["verified_at"]):
                        errors.append(_err("provenance.verification.verified_at", f"must be ISO 8601 UTC Zulu, got {ver.get('verified_at')!r}"))
                if "status" in ver and ver["status"] is not None:
                    if ver["status"] not in VERIFICATION_STATUS_ENUM:
                        errors.append(_err("provenance.verification.status", f"must be one of {VERIFICATION_STATUS_ENUM}, got {ver.get('status')!r}"))
                for k in ver:
                    if k not in ("verified_by", "verified_at", "status"):
                        errors.append(_err(f"provenance.verification.{k}", f"unknown property {k!r}"))
        if "history_ledger" in prov and prov["history_ledger"] is not None:
            if not isinstance(prov["history_ledger"], str):
                errors.append(_err("provenance.history_ledger", "must be string"))
        for k in prov:
            if k not in ("authors", "operators", "verification", "history_ledger"):
                errors.append(_err(f"provenance.{k}", f"unknown property {k!r}"))
    elif "provenance" in data:
        errors.append(_err("provenance", "must be object"))

    # extensions (open)
    if "extensions" in data and data["extensions"] is not None:
        if not isinstance(data["extensions"], dict):
            errors.append(_err("extensions", "must be object"))

    # profile-scoped payloads
    profile = ""
    if isinstance(cls, dict) and isinstance(cls.get("profile"), str):
        profile = str(cls["profile"])
    if profile == "somnus://profiles/engineering/specification/v1":
        spec = data.get("specification")
        if not isinstance(spec, dict):
            errors.append(_err("specification", "missing required profile payload object for engineering/specification/v1"))
        else:
            for req in ("system_target", "compliance_level", "verification_suite"):
                if req not in spec:
                    errors.append(_err(f"specification.{req}", "missing required property"))
                elif not isinstance(spec[req], str) or spec[req].strip() == "":
                    errors.append(_err(f"specification.{req}", "must be non-empty string"))
            for k in spec:
                if k not in ("system_target", "compliance_level", "verification_suite"):
                    errors.append(_err(f"specification.{k}", f"unknown property {k!r}"))
        if "benchmark" in data:
            errors.append(_err("benchmark", "must not be present when profile is engineering/specification/v1"))
    elif profile == "somnus://profiles/engineering/benchmark/v1":
        bench = data.get("benchmark")
        if not isinstance(bench, dict):
            errors.append(_err("benchmark", "missing required profile payload object for engineering/benchmark/v1"))
        else:
            if "workload" not in bench or not isinstance(bench.get("workload"), str) or str(bench.get("workload")).strip() == "":
                errors.append(_err("benchmark.workload", "missing or empty"))
            env = bench.get("environment")
            if not isinstance(env, dict):
                errors.append(_err("benchmark.environment", "missing required object"))
            else:
                for req in ("cpu", "memory_gb", "os"):
                    if req not in env:
                        errors.append(_err(f"benchmark.environment.{req}", "missing required property"))
                if "cpu" in env and (not isinstance(env.get("cpu"), str) or str(env.get("cpu")).strip() == ""):
                    errors.append(_err("benchmark.environment.cpu", "must be non-empty string"))
                if "memory_gb" in env and not isinstance(env.get("memory_gb"), (int, float)):
                    errors.append(_err("benchmark.environment.memory_gb", f"must be number, got {env.get('memory_gb')!r}"))
                if "os" in env and (not isinstance(env.get("os"), str) or str(env.get("os")).strip() == ""):
                    errors.append(_err("benchmark.environment.os", "must be non-empty string"))
                for k in env:
                    if k not in ("cpu", "memory_gb", "os"):
                        errors.append(_err(f"benchmark.environment.{k}", f"unknown property {k!r}"))
            metrics = bench.get("metrics")
            if not isinstance(metrics, list) or len(metrics) == 0:
                errors.append(_err("benchmark.metrics", "must be non-empty array"))
            else:
                for i, m in enumerate(metrics):
                    if not isinstance(m, dict):
                        errors.append(_err(f"benchmark.metrics[{i}]", "must be object"))
                        continue
                    for req in ("name", "value", "unit"):
                        if req not in m:
                            errors.append(_err(f"benchmark.metrics[{i}].{req}", "missing required property"))
                    if "name" in m and (not isinstance(m.get("name"), str) or str(m.get("name")).strip() == ""):
                        errors.append(_err(f"benchmark.metrics[{i}].name", "must be non-empty string"))
                    if "value" in m and not isinstance(m.get("value"), (int, float)):
                        errors.append(_err(f"benchmark.metrics[{i}].value", f"must be number, got {m.get('value')!r}"))
                    if "unit" in m and (not isinstance(m.get("unit"), str) or str(m.get("unit")).strip() == ""):
                        errors.append(_err(f"benchmark.metrics[{i}].unit", "must be non-empty string"))
                    for k in m:
                        if k not in ("name", "value", "unit"):
                            errors.append(_err(f"benchmark.metrics[{i}].{k}", f"unknown property {k!r}"))
            for k in bench:
                if k not in ("workload", "environment", "metrics"):
                    errors.append(_err(f"benchmark.{k}", f"unknown property {k!r}"))
        if "specification" in data:
            errors.append(_err("specification", "must not be present when profile is engineering/benchmark/v1"))
    elif profile != "":
        # Unknown profile: structural check cannot enforce payload; Stage 3 reports resolution.
        pass

    return errors


def _workspace_root_for(doc_path: Path) -> Path:
    # tools/validate.py lives in <root>/tools/; schemas live in <root>/schemas/.
    # Walk upward from the doc and from this file to find a directory containing schemas/.
    candidates: list[Path] = []
    try:
        candidates.append(Path(__file__).resolve().parent.parent)
    except NameError:
        pass
    cur: Optional[Path] = doc_path.resolve().parent
    while cur is not None:
        candidates.append(cur)
        if cur.parent == cur:
            break
        cur = cur.parent
    for cand in candidates:
        if (cand / "schemas" / "v1" / "core.json").exists():
            return cand
    try:
        return Path(__file__).resolve().parent.parent
    except NameError:
        return Path.cwd()


def resolve_profile_path(profile_uri: str, doc_path: Path) -> Optional[Path]:
    root = _workspace_root_for(doc_path)
    if profile_uri in PROFILE_TO_FILE:
        p = root / PROFILE_TO_FILE[profile_uri]
        return p
    m = re.match(r"^somnus://profiles/([a-z0-9/\-]+)$", profile_uri)
    if m:
        slug = m.group(1).strip("/").replace("/", "-")
        return root / "schemas" / "v1" / "profiles" / f"{slug}-v1.json"
    return None


def _inline_core_ref(node: Any, core_schema: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if set(node.keys()) == {"$ref"} and node.get("$ref") == "somnus://core/v1":
            return copy.deepcopy(core_schema)
        return {k: _inline_core_ref(v, core_schema) for k, v in node.items()}
    if isinstance(node, list):
        return [_inline_core_ref(v, core_schema) for v in node]
    return node


def validate_with_jsonschema(
    data: dict[str, Any], doc_path: Path
) -> tuple[Optional[list[str]], str]:
    """Try jsonschema validation; return (errors_or_None, note).

    Returns None when jsonschema is unavailable or schemas are missing,
    signalling the caller to use the structural fallback. ``note`` is a
    human-readable explanation for verbose output.
    """
    try:
        import jsonschema  # type: ignore[import-not-found]
    except ImportError:
        return None, "jsonschema not installed; using structural fallback"
    try:
        profile_uri = str(data.get("classification", {}).get("profile", ""))
        root = _workspace_root_for(doc_path)
        core_path = root / "schemas" / "v1" / "core.json"
        if profile_uri in ("", "somnus://core/v1"):
            schema_path = core_path
        else:
            resolved = resolve_profile_path(profile_uri, doc_path)
            schema_path = resolved if resolved is not None else core_path
        if not schema_path.exists():
            return None, f"schema file {schema_path} missing; using structural fallback"
        if not core_path.exists():
            return None, f"core schema {core_path} missing; using structural fallback"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        core_schema = json.loads(core_path.read_text(encoding="utf-8"))
        # Inline somnus://core/v1 refs so no network fetch occurs.
        schema = _inline_core_ref(schema, core_schema)
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema, format_checker=jsonschema.FormatChecker())
        raw_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        errors = [f"[Stage2] {'/'.join(str(p) for p in e.path) or '(root)'}: {e.message}" for e in raw_errors]
        return errors, f"validated with jsonschema against {schema_path.name}"
    except Exception as exc:  # never crash on optional dependency
        return None, f"jsonschema path failed ({exc}); using structural fallback"


# ---------------------------------------------------------------------------
# Stage 3: semantic checks
# ---------------------------------------------------------------------------

def uuidv7_timestamp_ms(uuid_str: str) -> Optional[int]:
    try:
        hexpart = uuid_str.replace("-", "")[:12]
        return int(hexpart, 16)
    except ValueError:
        return None


def validate_semantic(data: dict[str, Any], doc_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    # 3a: UUIDv7 timestamp vs created_at year-match (warning only).
    doc_id = str(data.get("id", ""))
    created = data.get("created_at")
    if UUIDV7_RE.match(doc_id) and isinstance(created, str) and DATETIME_Z_RE.match(created):
        ts_ms = uuidv7_timestamp_ms(doc_id)
        if ts_ms is not None:
            try:
                uuid_dt = datetime.datetime.fromtimestamp(ts_ms / 1000, tz=datetime.timezone.utc)
                created_dt = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=datetime.timezone.utc
                )
                if uuid_dt.year != created_dt.year:
                    warnings.append(
                        f"[Stage3] id timestamp year {uuid_dt.year} does not match "
                        f"created_at year {created_dt.year} (UUIDv7 embeds creation ms)"
                    )
            except (ValueError, OverflowError, OSError) as exc:
                warnings.append(f"[Stage3] could not compare UUID timestamp vs created_at: {exc}")

    # 3b: superseded must have superseded_by.
    life = data.get("lifecycle", {})
    rel = data.get("relations", {}) if isinstance(data.get("relations"), dict) else {}
    if isinstance(life, dict) and life.get("status") == "superseded":
        targets = rel.get("superseded_by", []) if isinstance(rel, dict) else []
        if not isinstance(targets, list) or len(targets) == 0:
            errors.append("[Stage3] lifecycle.status is 'superseded' but relations.superseded_by is empty")

    # 3c: profile URI resolves to a local schemas/ file.
    cls = data.get("classification", {})
    profile = str(cls.get("profile", "")) if isinstance(cls, dict) else ""
    if profile:
        resolved = resolve_profile_path(profile, doc_path)
        if resolved is None or not resolved.exists():
            errors.append(
                f"[Stage3] classification.profile {profile!r} does not resolve "
                f"to a local schema file (expected under schemas/v1/profiles/)"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def validate_file(path: Path) -> tuple[int, list[str], list[str]]:
    """Validate one Markdown file. Returns (exit_code, errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return 2, [f"[IO] file not found: {path}"], []
    except OSError as exc:
        return 2, [f"[IO] cannot read {path}: {exc}"], []

    raw, body, extract_errors = extract_frontmatter(text)
    errors.extend(extract_errors)
    if raw is None:
        return 2, errors, warnings

    if "\t" in raw:
        errors.append("[Stage1] tab character (\\t) is forbidden for indentation in YAML frontmatter")

    parser = FrontmatterParser(raw)
    data = parser.parse()
    errors.extend(parser.errors)
    warnings.extend(parser.warnings)
    if data is None:
        return 1, errors, warnings

    sub_errors, sub_warnings = check_submatter(body)
    errors.extend(sub_errors)
    warnings.extend(sub_warnings)

    # Stage 2: prefer jsonschema, fall back to structural.
    js_errors: Optional[list[str]] = None
    js_note = ""
    if not errors:
        js_errors, js_note = validate_with_jsonschema(data, path)
    else:
        # Still report which path would have been used, but skip jsonschema
        # when Stage 1 already failed to avoid cascading noise.
        js_note = "skipped jsonschema because Stage 1 failed"
    if js_errors is None:
        struct_errors = validate_structural(data)
        errors.extend(struct_errors)
        if js_note:
            warnings.append(f"[Stage2] note: {js_note}")
    else:
        errors.extend(js_errors)
        # Belt-and-braces: structural unknown-root check already covered by
        # unevaluatedProperties in schema, but keep note for transparency.
        if js_note:
            warnings.append(f"[Stage2] note: {js_note}")

    # Stage 3 always runs when parsing succeeded (even if Stage 2 failed,
    # to surface all semantic issues at once).
    sem_errors, sem_warnings = validate_semantic(data, path)
    errors.extend(sem_errors)
    warnings.extend(sem_warnings)

    code = 0 if not errors else 1
    return code, errors, warnings


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a Somnus Markdown file (3-stage pipeline).")
    ap.add_argument("path", help="Markdown file to validate")
    args = ap.parse_args(argv)

    path = Path(args.path)
    code, errors, warnings = validate_file(path)

    for w in warnings:
        print(f"WARN {w}")
    if code == 0:
        print(f"PASS {path} (warnings: {len(warnings)})")
        return 0
    for e in errors:
        print(f"ERROR {e}")
    if code == 2:
        print(f"FAIL {path}: I/O or frontmatter error ({len(errors)} error(s))")
    else:
        print(f"FAIL {path}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return code


if __name__ == "__main__":
    sys.exit(main())
