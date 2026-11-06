# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1af7c-0a13-77c5-8433-54c3d9210784"
#   revision: 1
#   title: "somnus migrate --inline: move sidecar headers into hosts that now have an embedded carrier (D20)"
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
#       - target_ref: "urn:somnus:artifact:01a1af7c-0a13-77c5-8433-54c3d9210784"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-migrate-inline-move-sidecar-headers-into-hosts-that-now-have-an-embedded"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1af7c-0a13-77c5-8433-54c3d9210784"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""``somnus migrate --inline``: move sidecar headers into hosts that now have an embedded carrier (D20).

A sidecar created before a host type gained a carrier (CODEOWNERS, Dockerfile,
``.ipynb``, shebang scripts, ...) keeps working, but the operator intent is one
envelope inside every file that can carry it. This command moves the payload
into the host, keeps the artifact ID, drops the sidecar-only ``bindings`` field,
records a new revision, and deletes the sidecar only after the host write
re-extracts cleanly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Optional

from somnus import carriers
from somnus import document as D
from somnus.carriers.jsonhost import JSON_KEY, object_members
from somnus.commands._common import Ctx, display, note, unified
from somnus.model.lifecycle import bump_revision
from somnus.model.validate import validate
from somnus.output import EXIT_INVALID, EXIT_OK, SomnusError, emit
from somnus.db.store import glob_regex, matches_any


def sidecars(paths: list[Path], exclude: list[str]) -> Iterator[Path]:
    """Sidecar files named directly, or found under named directories."""
    patterns = [glob_regex(p) for p in exclude]
    for path in paths:
        if path.is_file():
            side = path if carriers.is_sidecar_path(path) else carriers.sidecar_for(path)
            if side.is_file():
                yield side
            continue
        for dirpath, dirnames, filenames in os.walk(path):
            rel_dir = Path(os.path.relpath(dirpath, path)).as_posix()
            prefix = "" if rel_dir == "." else rel_dir + "/"
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in (".git", ".hg", ".svn") and not matches_any(prefix + d + "/", patterns))
            for name in sorted(filenames):
                if name.endswith(carriers.SIDECAR_SUFFIX) and not matches_any(prefix + name, patterns):
                    yield Path(dirpath) / name


def target_carrier(host: Path, json_key: bool):
    """Embedded carrier the host should use now, or None when it must stay a sidecar."""
    carrier = carriers.for_path(host)
    if carrier is not None:
        return carrier
    if json_key and host.suffix.lower() == ".json":
        try:
            object_members(host.read_text(encoding="utf-8-sig"), 0)
        except (OSError, ValueError):
            return None
        return JSON_KEY
    return None


def plan(sidecar: Path, json_key: bool) -> Optional[tuple[Path, str, str, dict, str]]:
    """Return (host, old host text, new host text, payload, reason) or None with a reason noted."""
    host = carriers.host_for(sidecar)
    if not host.is_file():
        note(f"{display(sidecar)}: host is missing; skipped")
        return None
    carrier = target_carrier(host, json_key)
    if carrier is None:
        return None
    meta = D.load(sidecar)
    if meta.payload is None or [d for d in validate(meta, "core") if d.is_error]:
        note(f"{display(sidecar)}: sidecar does not validate at core; fix it first (somnus check)")
        return None
    bindings = meta.payload.get("bindings", [])
    if any(isinstance(b, dict) and b.get("role") != "primary" for b in bindings):
        note(f"{display(sidecar)}: has attachment/representation bindings; it stays a sidecar")
        return None
    try:
        doc = D.as_carrier(host, carrier)
    except SomnusError:
        note(f"{display(host)}: host is not UTF-8 text; it stays a sidecar")
        return None
    if doc.envelope is not None or doc.issues:
        note(f"{display(host)}: host already has an envelope (or a malformed one); resolve with somnus check")
        return None
    payload = meta.copy_payload()
    payload.pop("bindings", None)
    bump_revision(payload)
    new = doc.render(payload)
    old = "".join(line + end for line, end in zip(doc.lines, doc.endings, strict=True))
    return host, old, new, payload, carrier.name


def run(args, ctx: Ctx) -> int:
    """Dry-run diff by default; ``--write`` moves each header and removes its sidecar."""
    status = EXIT_OK
    json_key = bool(getattr(args, "json_key", False)) or ctx.cfg.json_carrier == "key"
    moved = 0
    for side in sidecars([Path(p).resolve() for p in args.paths], ctx.cfg.exclude):
        try:
            result = plan(side, json_key)
        except SomnusError as exc:
            ctx.diagnostics(exc.diagnostics)
            status = max(status, exc.exit_code)
            continue
        if result is None:
            continue
        host, old, new, payload, cname = result
        carrier = target_carrier(host, json_key)
        if [d for d in validate(D.from_text(host, new), "core") if d.is_error]:
            note(f"{display(host)}: inline result does not validate; left as a sidecar")
            status = EXIT_INVALID
            continue
        if not args.write:
            emit(unified(old, new, display(host)))
            emit(f"--- {display(side)}\n+++ /dev/null (sidecar removed)\n")
            continue
        D.atomic_write(host, new)
        reread = D.as_carrier(host, carrier)
        if reread.envelope is None or reread.issues:
            D.atomic_write(host, old)
            note(f"{display(host)}: write did not re-extract; host restored, sidecar kept")
            status = EXIT_INVALID
            continue
        side.unlink()
        moved += 1
        ctx.record("inline", host, payload["id"], payload["revision"],
                   f"sidecar -> {cname} carrier", resolve=("revision",))
        note(f"{display(host)}: header moved inline ({cname}), revision {payload['revision']}")
    if args.write:
        note(f"moved {moved} sidecar header(s) inline")
    return status
