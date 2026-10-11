"""``somnus fork``: new artifact (UUIDv7, revision 1) derived from an existing revision."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

from somnus import carriers, ids
from somnus import document as D
from somnus.commands._common import Ctx, check_text, display, load_valid, note, refuse
from somnus.model.lifecycle import now_utc
from somnus.output import EXIT_OK, SomnusError, emit


def _unique_id(existing: set, base: str) -> str:
    candidate, n = base, 2
    while candidate in existing:
        candidate, n = f"{base}-{n}", n + 1
    return candidate


def forked_payload(parent: dict, title: str, standing: str, at: str) -> dict:
    """Derive a revision-1 payload from ``parent`` with a ``derived_from`` lineage relation."""
    new = copy.deepcopy({k: v for k, v in parent.items() if k not in ("locations", "representations")})
    parent_id, aid = parent["id"], ids.new_artifact_urn()
    new["id"], new["revision"], new["title"] = aid, 1, title
    new["lifecycle"] = {"status": "draft"}
    scopes = [] if standing == "unasserted" else [{"target_ref": aid, "aspects": ["content"]}]
    new["authority"] = {"standing": standing, "scopes": scopes}
    new["time"] = {"created_at": at}
    new["names"] = {"slug": ids.slugify(title)}
    knowledge = new.setdefault("knowledge", {"coverage": "artifact", "subjects": []})
    knowledge["subjects"] = [aid if s == parent_id else s for s in knowledge.get("subjects", [])] or [aid]
    relations = knowledge.setdefault("relations", [])
    for rel in relations:
        if rel["subject"].get("ref") == parent_id:
            rel["subject"]["ref"] = aid
    rid = _unique_id({r["id"] for r in relations}, "rel-derived-from-parent")
    relations.append({
        "id": rid,
        "subject": {"ref": aid},
        "predicate": "derived_from",
        "object": {"ref": parent_id, "revision": parent["revision"]},
        "assessment": "unassessed",
        "valid_time": {"basis": "open", "from": at},
    })
    return new


def run(args, ctx: Ctx) -> int:
    """Write the fork next to the parent (or at ``--out``) and record lineage."""
    path = Path(args.path).resolve()
    doc = load_valid(path)
    parent = doc.copy_payload()
    title = (args.title or f"{parent['title']} (fork)").strip()
    standing = ctx.cfg.defaults["standing"]
    if standing == "accepted":
        standing = "candidate"
    new = forked_payload(parent, title, standing, now_utc())
    host = doc.path
    out = Path(args.out).resolve() if args.out else host.with_name(ids.slugify(title) + "".join(host.suffixes))
    if out.exists():
        raise refuse(out, "E_IO", "output file already exists; use --out")
    if doc.is_sidecar:
        sidecar = carriers.sidecar_for(out)
        if sidecar.exists():
            raise refuse(sidecar, "E_IO", "output sidecar already exists")
        for binding in new.get("bindings", []):
            if binding.get("role") == "primary":
                binding["target"] = out.name
        shutil.copyfile(host, out)
        text = D.new_sidecar_text(new)
        try:
            check_text(sidecar, text)
        except SomnusError:
            out.unlink()
            raise
        D.atomic_write(sidecar, text)
    else:
        if carriers.carrier_name_for(out) != carriers.carrier_name_for(host):
            raise refuse(out, "E_HOST", "--out must use the same carrier type as the parent")
        text = doc.render(new)
        check_text(out, text)
        D.atomic_write(out, text)
    ctx.record("fork", out, new["id"], 1, f"derived from {parent['id']} revision {parent['revision']}")
    emit(str(out))
    note(f"forked {parent['id']} -> {new['id']} ({display(out)})")
    return EXIT_OK
