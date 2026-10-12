"""``somnus set``: non-interactive header edit; the CLI twin of the ``somnus edit`` form."""

from __future__ import annotations

from pathlib import Path

from somnus.commands._common import Ctx, commit, display, load_valid, note, refuse
from somnus.model.lifecycle import bump_revision
from somnus.output import EXIT_OK, EXIT_USAGE, SomnusError
from somnus.tui.form import FIELDS, Field, FormModel, get_path

SETTABLE = {f.path: f for f in FIELDS}


def parse_assignment(raw: str) -> tuple[Field, str]:
    """Split ``FIELD=VALUE`` (leading ``somnus.`` optional) into a settable field and its text."""
    name, sep, value = raw.partition("=")
    name = name.strip().removeprefix("somnus.")
    if not sep or not name:
        raise SomnusError(f"{raw!r} is not FIELD=VALUE", EXIT_USAGE)
    field = SETTABLE.get(name)
    if field is None:
        raise SomnusError(f"{name!r} cannot be set; settable fields: {', '.join(SETTABLE)}", EXIT_USAGE)
    return field, value


def run(args, ctx: Ctx) -> int:
    """Apply every assignment, then write one new revision (or nothing when no value changed)."""
    assignments = [parse_assignment(raw) for raw in args.assignments]
    names = [f.path for f, _ in assignments]
    repeated = sorted({n for n in names if names.count(n) > 1})
    if repeated:
        raise SomnusError(f"assigned more than once: {', '.join(repeated)}", EXIT_USAGE)
    doc = load_valid(Path(args.path).resolve())
    form = FormModel(doc.copy_payload())
    for field, value in assignments:
        try:
            form.apply(field, value)
        except ValueError as exc:
            raise refuse(doc.meta_path, "E_SCHEMA", f"{value.strip()!r} is not one of: {', '.join(field.choices)}",
                         f"somnus.{field.path}") from exc
    changed = [n for n in names if get_path(form.payload, n) != get_path(form.original, n)]
    if not changed:
        note(f"{display(doc.meta_path)}: no changes")
        return EXIT_OK
    payload = form.payload
    bump_revision(payload)
    commit(doc, payload)
    detail = "set " + ", ".join(changed) + (f": {args.reason.strip()}" if args.reason else "")
    ctx.record("set", doc.path, payload["id"], payload["revision"], detail, resolve=("revision",))
    note(f"{display(doc.meta_path)}: set {', '.join(changed)} (revision {payload['revision']})")
    return EXIT_OK
