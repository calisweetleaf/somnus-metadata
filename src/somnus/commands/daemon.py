# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1af7c-0a01-706c-8a98-619b5a23d480"
#   revision: 2
#   title: "somnus daemon: install, inspect, and stop the 24/7 watcher service (D20)"
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
#       - target_ref: "urn:somnus:artifact:01a1af7c-0a01-706c-8a98-619b5a23d480"
#         aspects: ["content"]
#   time:
#     updated_at: "2026-11-06T08:15:27+00:00"
#   names:
#     slug: "somnus-daemon-install-inspect-and-stop-the-24-7-watcher-service-d20"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1af7c-0a01-706c-8a98-619b5a23d480"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""``somnus daemon``: install, inspect, and stop the 24/7 watcher service (D20)."""

from __future__ import annotations

import os
import signal
import time

from somnus import service
from somnus.commands._common import Ctx, note
from somnus.output import EXIT_INVALID, EXIT_OK, emit
from somnus.heartbeat import read_status
from somnus.watch import Settings, Watcher


def _status(ctx: Ctx) -> int:
    data = read_status(ctx.cfg.home)
    if data is None:
        emit("watcher: never ran (install it with 'somnus daemon install', or run 'somnus watch')")
        return EXIT_INVALID
    counters = data.get("counters", {})
    settings = data.get("settings", {})
    rows = [
        ("state", "running" if data.get("running") else "stopped"),
        ("pid", data.get("pid")),
        ("version", data.get("version")),
        ("started", data.get("started_at")),
        ("last pass", data.get("last_tick_at")),
        ("stamp mode", settings.get("stamp")),
        ("interval", f"{settings.get('interval')}s (settle {settings.get('settle')}s)"),
        ("roots", ", ".join(data.get("roots", [])) or "(none registered)"),
        ("tracked files", data.get("tracked_files")),
        ("stamped", counters.get("stamped")),
        ("revised", counters.get("revised")),
        ("indexed", counters.get("indexed")),
        ("errors", counters.get("errors")),
    ]
    ctx.table(["field", "value"], rows)
    return EXIT_OK if data.get("running") else EXIT_INVALID


def _stop(ctx: Ctx) -> int:
    data = read_status(ctx.cfg.home)
    if not data or not data.get("running"):
        note("watcher is not running")
        return EXIT_OK
    pid = int(data.get("pid", 0))
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        note(f"cannot signal pid {pid}: {exc}")
        return EXIT_INVALID
    for _ in range(40):
        time.sleep(0.25)
        fresh = read_status(ctx.cfg.home)
        if not fresh or not fresh.get("running"):
            note(f"stopped watcher pid {pid} (a service manager with restart-on-failure may not restart a clean stop)")
            return EXIT_OK
    note(f"watcher pid {pid} did not stop within 10s")
    return EXIT_INVALID


def run(args, ctx: Ctx) -> int:
    """Dispatch the daemon action."""
    action = args.action
    if action == "status":
        return _status(ctx)
    if action == "stop":
        return _stop(ctx)
    if action == "once":
        settings = Settings.from_config(ctx.cfg, adopt=True if args.adopt else None)
        return Watcher(ctx.cfg.home, settings, log=note).run(once=True)
    if action in ("install", "uninstall"):
        plan = service.install_plan(ctx.cfg.home) if action == "install" else service.uninstall_plan()
        if args.dry_run:
            if plan.path is not None:
                emit(f"# {plan.path}\n{plan.content}" if plan.content else f"# remove {plan.path}")
            for argv in plan.commands:
                emit("$ " + " ".join(argv))
            return EXIT_OK
        lines = service.apply(plan, install=action == "install")
        for line in lines:
            note(line)
        failed = any(": exit " in line for line in lines)
        return EXIT_INVALID if failed else EXIT_OK
    return EXIT_INVALID
