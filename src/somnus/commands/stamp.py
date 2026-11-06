# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7f3d-71cd-bef4-805c42c9501a"
#   revision: 2
#   title: "somnus stamp: infer and inject a header into unmanaged files"
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
#       - target_ref: "urn:somnus:artifact:01a19a67-7f3d-71cd-bef4-805c42c9501a"
#         aspects: ["content"]
#   time:
#     updated_at: "2026-11-06T06:11:48+00:00"
#   names:
#     slug: "somnus-stamp-infer-and-inject-a-header-into-unmanaged-files"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7f3d-71cd-bef4-805c42c9501a"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""``somnus stamp``: infer and inject a header into unmanaged files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from somnus import document as D
from somnus.carriers.jsonhost import JSON_KEY, object_members
from somnus.commands._common import Ctx, check_text, display, inferred_payload, note, unified
from somnus.output import EXIT_OK, SomnusError, emit


def json_inline(host: Path, args, ctx: Ctx) -> bool:
    """True when a plain ``.json`` host should carry ``"$somnus"`` instead of a sidecar.

    Opt-in per call (``--inline``) or per configuration (``[carriers] json = "key"``);
    only object documents qualify (arrays and scalars always use a sidecar).
    """
    if host.suffix.lower() != ".json":
        return False
    if not (getattr(args, "inline", False) or ctx.cfg.json_carrier == "key"):
        return False
    try:
        object_members(host.read_text(encoding="utf-8-sig"), 0)
    except (OSError, ValueError):
        return False
    return True


def _plan(path: Path, args, ctx: Ctx) -> Optional[tuple[Path, str, str, dict]]:
    """Return (file to write, old text, new text, payload), or None when already managed."""
    doc = D.load(path)
    if doc.envelope is not None or doc.issues:
        return None
    if doc.is_sidecar and not doc.meta_path.exists() and json_inline(doc.path, args, ctx):
        doc = D.as_carrier(doc.path, JSON_KEY)
        if doc.envelope is not None or doc.issues:
            return None
    if doc.is_sidecar:
        if doc.meta_path.exists():
            return None
        if not doc.path.is_file():
            raise SomnusError(f"{display(doc.path)}: file not found")
        payload = inferred_payload(ctx.cfg, doc.path, [], type_=args.type, title=args.title)
        payload["bindings"] = [{"target": doc.path.name, "role": "primary", "required": True}]
        text = D.new_sidecar_text(payload)
        check_text(doc.meta_path, text)
        return doc.meta_path, "", text, payload
    payload = inferred_payload(ctx.cfg, doc.path, doc.lines, type_=args.type, title=args.title)
    text = doc.render(payload)
    check_text(doc.meta_path, text)
    old = "".join(line + end for line, end in zip(doc.lines, doc.endings, strict=True))
    return doc.meta_path, old, text, payload


def run(args, ctx: Ctx) -> int:
    """Dry-run diff by default; ``--write`` applies atomically."""
    status = EXIT_OK
    for raw in args.paths:
        path = Path(raw).resolve()
        try:
            plan = _plan(path, args, ctx)
        except SomnusError as exc:
            ctx.diagnostics(exc.diagnostics)
            status = max(status, exc.exit_code)
            continue
        if plan is None:
            note(f"{display(path)}: already managed; skipped")
            continue
        target, old, new, payload = plan
        if not args.write:
            emit(unified(old, new, display(target), old_label="/dev/null" if not old else None))
            continue
        D.atomic_write(target, new)
        ctx.record("stamp", path, payload["id"], 1, f"inferred {payload['classification']['type']}")
        note(f"{display(target)}: stamped {payload['id']}")
    return status
