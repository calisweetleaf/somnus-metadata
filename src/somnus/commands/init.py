"""``somnus init``: create $SOMNUS_HOME, config.toml, and the registry; register roots."""

from __future__ import annotations

from pathlib import Path

from somnus import config
from somnus import document as D
from somnus.commands._common import Ctx, note
from somnus.db import Store
from somnus.output import EXIT_OK, EXIT_USAGE, SomnusError


def run(args, ctx: Ctx) -> int:
    """Initialize the global home; idempotent."""
    home = config.somnus_home()
    try:
        home.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SomnusError(f"cannot create {home}: {exc.strerror or exc}", EXIT_USAGE) from exc
    cfg_path = home / "config.toml"
    if cfg_path.exists():
        note(f"config exists: {cfg_path}")
    else:
        D.atomic_write(cfg_path, config.CONFIG_TEMPLATE)
        note(f"created config: {cfg_path}")
    roots = [Path(r).resolve() for r in args.root]
    for root in roots:
        if not root.is_dir():
            raise SomnusError(f"root {root} is not a directory", EXIT_USAGE)
    existed = ctx.cfg.db_path.exists()
    with Store.open(ctx.cfg.db_path, actor=ctx.actor, create=True) as st:
        if not existed:
            st.log("init", path=str(ctx.cfg.db_path), detail="registry created")
        for root in roots:
            st.add_root(root)
        registered = st.roots()
    note(f"registry: {ctx.cfg.db_path}" + ("" if existed else " (created)"))
    for _, root in registered:
        note(f"root: {root}")
    return EXIT_OK
