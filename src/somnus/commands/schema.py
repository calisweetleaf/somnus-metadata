"""``somnus schema``: field documentation, or JSON Schema Draft 2020-12 export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from somnus import BENCHMARK_PROFILE, SPEC_PROFILE
from somnus import document as D
from somnus.commands._common import Ctx, note
from somnus.model import schema as S
from somnus.output import EXIT_OK, EXIT_USAGE, SomnusError, emit

_PROFILE_KEYS = {"specification": SPEC_PROFILE, "benchmark": BENCHMARK_PROFILE}


def resolve(field: str) -> tuple[list[Any], Any, Optional[S.Field]]:
    """Resolve a dotted field (array items stepped through automatically)."""
    parts = [p for p in field.replace("[]", "").split(".") if p]
    if parts and parts[0] == "somnus":
        parts = parts[1:]
    path: list[Any] = ["somnus"]
    node: Any = S.node_at(path)
    decl: Optional[S.Field] = S.ROOT.get("somnus")
    for part in parts:
        while isinstance(node, S.Arr):
            path.append("[]")
            node = node.item
        parent = node
        path.append(part)
        node = S.node_at(path, _PROFILE_KEYS)
        if node is None:
            raise SomnusError(f"unknown field {field!r} (no member {part!r})", EXIT_USAGE)
        decl = parent.get(part) if isinstance(parent, S.Obj) else None
    return path, node, decl


def _members(node: Any) -> list[list[str]]:
    while isinstance(node, S.Arr):
        node = node.item
    rows = []
    if isinstance(node, S.Obj):
        for f in node.fields:
            rows.append([f.name, "yes" if f.required else "", S.describe(f.node), f.doc])
    elif isinstance(node, S.Tagged):
        for kind, variant in node.variants.items():
            for f in variant.fields:
                if f.name != node.tag:
                    rows.append([f"{node.tag}={kind}: {f.name}", "yes" if f.required else "", S.describe(f.node),
                                 f.doc])
    return rows


def run(args, ctx: Ctx) -> int:
    """Print documentation for one field (default: the payload root) or export JSON Schema."""
    if args.json_schema:
        from somnus.model.jsonschema_export import export

        text = json.dumps(export(), indent=2, ensure_ascii=False) + "\n"
        if args.out:
            out = Path(args.out).resolve()
            D.atomic_write(out, text)
            note(f"wrote {out}")
        else:
            emit(text)
        return EXIT_OK
    if args.out:
        raise SomnusError("--out is only valid with --json-schema", EXIT_USAGE)
    path, node, decl = resolve(args.field or "somnus")
    shown = ".".join(str(p) for p in path if p != "[]")
    lines = [f"field: {shown}", f"type: {S.describe(node)}"]
    if decl is not None:
        lines.append(f"required: {'yes' if decl.required else 'no'}")
        if decl.doc:
            lines.append(f"about: {decl.doc}")
    doc = getattr(node, "doc", "") or getattr(getattr(node, "item", None), "doc", "")
    if doc and (decl is None or doc != decl.doc):
        lines.append(f"about: {doc}")
    emit("\n".join(lines))
    rows = _members(node)
    if rows:
        emit("")
        ctx.table(["member", "required", "type", "about"], rows)
    return EXIT_OK
