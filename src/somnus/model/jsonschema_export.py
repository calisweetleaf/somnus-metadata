"""Export the declarative schema tree as JSON Schema Draft 2020-12 (interchange only; never stored)."""

from __future__ import annotations

from typing import Any

from somnus import CORE_SCHEMA
from somnus.model import schema as S

DRAFT = "https://json-schema.org/draft/2020-12/schema"


class _Exporter:
    def __init__(self) -> None:
        self.defs: dict[str, Any] = {}
        self._names: dict[int, str] = {}

    def ref(self, node: S.Obj | S.Tagged) -> dict:
        key = id(node)
        if key not in self._names:
            name, n = node.name, 2
            while name in self.defs:
                name, n = f"{node.name}-{n}", n + 1
            self._names[key] = name
            self.defs[name] = {}
            self.defs[name] = self.obj(node) if isinstance(node, S.Obj) else self.tagged(node)
        return {"$ref": f"#/$defs/{self._names[key]}"}

    def obj(self, node: S.Obj, tag: tuple[str, str] | None = None) -> dict:
        props: dict[str, Any] = {}
        for f in node.fields:
            props[f.name] = self.node(f.node)
            if f.doc:
                props[f.name] = {**props[f.name], "description": f.doc}
        if tag is not None:
            props[tag[0]] = {"const": tag[1]}
        out: dict[str, Any] = {"type": "object", "properties": props, "additionalProperties": False}
        required = [f.name for f in node.fields if f.required]
        if required:
            out["required"] = required
        if node.doc:
            out["description"] = node.doc
        return out

    def tagged(self, node: S.Tagged) -> dict:
        out: dict[str, Any] = {"oneOf": [self.obj(v, (node.tag, k)) for k, v in node.variants.items()]}
        if node.doc:
            out["description"] = node.doc
        return out

    def node(self, node: Any) -> dict:
        if isinstance(node, S.Str):
            out: dict[str, Any] = {"type": "string"}
            if node.enum:
                out["enum"] = list(node.enum)
            if node.fmt == "timestamp":
                out["format"] = "date-time"
                out["pattern"] = f"^{S.TIMESTAMP_PATTERN}$"
            elif node.fmt == "date":
                out["format"] = "date"
                out["pattern"] = f"^{S.DATE_PATTERN}$"
            elif node.pattern:
                out["pattern"] = f"^(?:{node.pattern})$"
            if node.min_len and not node.enum:
                out["minLength"] = node.min_len
            return out
        if isinstance(node, S.Int):
            out = {"type": "integer"}
            if node.minimum is not None:
                out["minimum"] = node.minimum
            return out
        if isinstance(node, S.Num):
            out = {"type": "number"}
            if node.minimum is not None:
                out["minimum"] = node.minimum
            if node.maximum is not None:
                out["maximum"] = node.maximum
            return out
        if isinstance(node, S.Bool):
            return {"type": "boolean"}
        if isinstance(node, S.AnyValue):
            return {"not": {"type": "null"}}
        if isinstance(node, S.Arr):
            out = {"type": "array", "items": self.node(node.item)}
            if node.min_items:
                out["minItems"] = node.min_items
            if node.unique:
                out["uniqueItems"] = True
            return out
        if isinstance(node, (S.Obj, S.Tagged)):
            return self.ref(node)
        if isinstance(node, S.MapOf):
            return {"type": "object", "propertyNames": {"pattern": f"^(?:{node.key_pattern})$"},
                    "additionalProperties": self.node(node.value)}
        if isinstance(node, S.Union_):
            return {"anyOf": [self.node(o) for o in node.options]}
        raise TypeError(f"unsupported schema node {node!r}")


def export() -> dict:
    """Core 2.0.0 envelope schema with profile payload schemas under ``$defs``."""
    ex = _Exporter()
    root = ex.obj(S.ROOT)
    for uri, profile in S.PROFILES.items():
        ref = ex.ref(profile)
        ex.defs[ref["$ref"].rsplit("/", 1)[1]]["$comment"] = f"profile payload for {uri}"
    return {
        "$schema": DRAFT,
        "$id": CORE_SCHEMA,
        "title": "Somnus metadata envelope (core 2.0.0)",
        "$comment": ("Restricted YAML rules, cross-field consistency, references, regions, and profile key "
                     "binding are enforced by the somnus validator and are not expressible here."),
        **root,
        "$defs": ex.defs,
    }
