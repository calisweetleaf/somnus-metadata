# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1af7c-0a61-70f2-8ce7-61d2c079acd6"
#   revision: 2
#   title: "The always-on watcher: poll registered roots, stamp new files, keep the registry current (D20)"
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
#       - target_ref: "urn:somnus:artifact:01a1af7c-0a61-70f2-8ce7-61d2c079acd6"
#         aspects: ["content"]
#   time:
#     updated_at: "2026-11-06T08:15:27+00:00"
#   names:
#     slug: "the-always-on-watcher-poll-registered-roots-stamp-new-files-keep-the-registry-cu"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1af7c-0a61-70f2-8ce7-61d2c079acd6"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""The always-on watcher: poll registered roots, stamp new files, keep the registry current (D20).

The watcher is the system's 24/7 loop. It is not the MCP server: MCP serves the
CLI to agents on demand, while the watcher runs continuously under the user's
service manager (systemd user unit, launchd agent, or a Windows logon task).

Design (stdlib only, every platform):

* **Polling with a stat snapshot.** Each tick walks the registered roots, honoring
  the configured excludes, and compares ``(mtime_ns, size)`` per file. Only files
  that changed are opened. Roots registered later with ``somnus init --root`` are
  picked up on the next tick.
* **Settle before stamping.** A new unmanaged file is stamped only after it has
  not changed for ``settle`` seconds, so editors and generators finish writing.
* **Stamp policy.** ``off`` indexes only; ``inline`` stamps files that have an
  embedded carrier (never creates sidecars); ``all`` also creates sidecars.
  Existing unmanaged files are adopted on start only with ``adopt``.
* **Single instance.** An OS file lock in ``$SOMNUS_HOME/watch.lock`` prevents two
  watchers; ``$SOMNUS_HOME/watch.json`` is the heartbeat read by
  ``somnus daemon status``, the TUI, and MCP.
* **Reconciliation.** Changed managed files go through ``Store.observe``; a
  deletion or every ``rescan`` seconds triggers an incremental ``Store.scan`` so
  missing locations and cross-file conflicts stay correct.
"""

from __future__ import annotations

import json
import os
import signal
import time
import types
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from somnus import __version__, carriers
from somnus import config as C
from somnus import document as D
from somnus.db.store import Store, glob_regex, matches_any, now_iso
from somnus.heartbeat import STATUS_NAME, InstanceLock, is_locked, read_status  # noqa: F401 - re-exported
from somnus.output import SomnusError

WATCH_ACTOR = "somnus-watch"
_PRUNE = {".git", ".hg", ".svn"}


@dataclass
class Counters:
    """Running totals reported in the heartbeat."""

    ticks: int = 0
    indexed: int = 0
    stamped: int = 0
    revised: int = 0
    skipped: int = 0
    errors: int = 0
    scans: int = 0


@dataclass
class Settings:
    """Watcher settings resolved from config and flags."""

    interval: float = 5.0
    settle: float = 10.0
    stamp: str = "inline"
    rescan: float = 300.0
    adopt: bool = False
    revise: str = "auto"

    @classmethod
    def from_config(cls, cfg: C.Config, **overrides) -> "Settings":
        """Config ``[watch]`` values with non-None overrides applied."""
        w = cfg.watch
        s = cls(float(w.get("interval", 5.0)), float(w.get("settle", 10.0)), str(w.get("stamp", "inline")),
                float(w.get("rescan", 300.0)), bool(w.get("adopt", False)), str(w.get("revise", "auto")))
        for key, value in overrides.items():
            if value is not None:
                setattr(s, key, value)
        if s.stamp not in C.WATCH_STAMP:
            raise SomnusError(f"watch stamp mode must be one of {C.WATCH_STAMP}")
        if s.revise not in C.WATCH_REVISE:
            raise SomnusError(f"watch revise mode must be one of {C.WATCH_REVISE}")
        s.interval = max(0.5, s.interval)
        return s


# --------------------------------------------------------------------------- the watcher


@dataclass
class Watcher:
    """Polling reconciler for the registered roots."""

    home: Path
    settings: Settings
    roots: list[Path] = field(default_factory=list)  # empty: every registered root
    log: Callable[[str], None] = lambda message: None
    snapshot: dict[str, tuple[int, int]] = field(default_factory=dict)
    pending: dict[str, float] = field(default_factory=dict)
    counters: Counters = field(default_factory=Counters)
    started_at: str = field(default_factory=now_iso)
    last_scan: float = 0.0
    first_pass: bool = True
    stopping: bool = False
    _configs: dict[str, C.Config] = field(default_factory=dict)
    _written: set[str] = field(default_factory=set)

    @property
    def db_path(self) -> Path:
        """The global registry."""
        return self.home / "somnus.db"

    # ------------------------------------------------------------ helpers
    def _cfg(self, root: Path) -> C.Config:
        key = str(root)
        if key not in self._configs:
            self._configs[key] = C.load(root)
        return self._configs[key]

    def _roots(self, st: Store) -> list[Path]:
        if self.roots:
            return [r.resolve() for r in self.roots]
        return [r for _, r in st.roots()]

    def _walk(self, root: Path, exclude: list[str]):
        patterns = [glob_regex(p) for p in exclude]
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = Path(os.path.relpath(dirpath, root)).as_posix()
            prefix = "" if rel_dir == "." else rel_dir + "/"
            dirnames[:] = [d for d in dirnames if d not in _PRUNE and not matches_any(prefix + d + "/", patterns)]
            for name in filenames:
                if name.startswith(".") and name.endswith(".tmp"):
                    continue  # atomic_write temp files
                if not matches_any(prefix + name, patterns):
                    yield Path(dirpath) / name

    # ------------------------------------------------------------ one pass
    def tick(self) -> None:
        """One reconciliation pass over every root."""
        if not self.db_path.exists():
            self.log("registry missing; run 'somnus init --root DIR' (waiting)")
            return
        with Store.open(self.db_path, actor=WATCH_ACTOR, create=False) as st:
            roots = self._roots(st)
            seen: dict[str, tuple[int, int]] = {}
            changed: list[tuple[Path, Path]] = []
            for root in roots:
                if not root.is_dir():
                    continue
                cfg = self._cfg(root)
                for path in self._walk(root, cfg.exclude):
                    try:
                        stat = path.stat()
                    except OSError:
                        continue
                    key = str(path)
                    sig = (stat.st_mtime_ns, stat.st_size)
                    seen[key] = sig
                    if self.snapshot.get(key) != sig or key in self.pending:
                        changed.append((root, path))
            removed = [k for k in self.snapshot if k not in seen]
            now = time.time()
            for root, path in changed:
                self._handle(st, root, path, seen, now)
            for key in removed:
                self.pending.pop(key, None)
            fresh = {k: v for k, v in self.snapshot.items() if k in self._written}
            self.snapshot = {k: v for k, v in seen.items() if k not in self.pending}
            self.snapshot.update(fresh)
            self._written.clear()
            if removed or now - self.last_scan >= self.settings.rescan:
                for root in roots:
                    if not root.is_dir():
                        continue
                    report = st.scan([root], exclude=self._cfg(root).exclude)
                    if report.missing:
                        self.log(f"{root}: marked {report.missing} location(s) missing")
                self.counters.scans += 1
                self.last_scan = now
        self.first_pass = False
        self.counters.ticks += 1

    def _handle(self, st: Store, root: Path, path: Path, seen: dict, now: float) -> None:
        key = str(path)
        cfg = self._cfg(root)
        side = carriers.is_sidecar_path(path)
        has_side = not side and carriers.sidecar_for(path).exists()
        embedded = side or carriers.for_path(path) is not None or (
            cfg.json_carrier == "key" and path.suffix.lower() == ".json")
        mode = self.settings.stamp
        if not (side or has_side or embedded) and mode != "all":
            self.pending.pop(key, None)  # sidecar-only host and sidecars are not wanted: never open it
            return
        try:
            doc = D.load(path)
        except SomnusError:
            self.counters.skipped += 1
            self.pending.pop(key, None)
            return
        if doc.envelope is not None or doc.issues:
            edited = self._edited_in_place(st, doc)
            if edited and self.settings.revise == "auto":
                if now - seen[key][0] / 1e9 < self.settings.settle:
                    self.pending[key] = seen[key][0] / 1e9
                    return
                self.pending.pop(key, None)
                if self._revise(st, doc, seen[key]):
                    return
            report = st.observe(path)
            if report is not None:
                self.counters.indexed += 1
                errors = [d for d in report.diagnostics if d.is_error]
                if errors:
                    self.counters.errors += len(errors)
                    self.log(f"{path}: {errors[0].code} {errors[0].message}")
            self.pending.pop(key, None)
            return
        if side or mode == "off" or (self.first_pass and not self.settings.adopt):
            self.pending.pop(key, None)
            return
        if now - seen[key][0] / 1e9 < self.settings.settle:
            self.pending[key] = seen[key][0] / 1e9
            return
        self.pending.pop(key, None)
        self._stamp(st, root, path, seen[key])

    def _edited_in_place(self, st: Store, doc: D.Document) -> bool:
        """True when this location's registered revision was edited without a revision bump."""
        somnus = doc.payload
        if doc.issues or somnus is None or not isinstance(somnus.get("id"), str):
            return False
        found = st.root_for(doc.meta_path)
        if found is None:
            return False
        rel = Path(os.path.relpath(doc.path, found[1])).as_posix()
        row = st.conn.execute("SELECT artifact_id, revision FROM locations WHERE root_id = ? AND rel_path = ?"
                              " AND present = 1", (found[0], rel)).fetchone()
        if row is None or row[0] != somnus["id"] or row[1] != somnus.get("revision"):
            return False
        stored = st.conn.execute("SELECT payload_digest, body_digest FROM revisions WHERE artifact_id = ?"
                                 " AND revision = ?", (row[0], row[1])).fetchone()
        return stored is not None and tuple(stored) != (doc.payload_digest(), doc.body_digest())

    def _revise(self, st: Store, doc: D.Document, sig: tuple[int, int]) -> bool:
        """Record an in-place edit as a new revision (``watch.revise = "auto"``)."""
        from somnus.commands._common import commit
        from somnus.model.lifecycle import bump_revision
        from somnus.model.validate import validate

        if [d for d in validate(doc, "core") if d.is_error]:
            return False
        payload = doc.copy_payload()
        old = payload["revision"]
        bump_revision(payload)
        try:
            current = doc.meta_path.stat()
            if doc.meta_path == doc.path and (current.st_mtime_ns, current.st_size) != sig:
                return False
            commit(doc, payload)
        except (SomnusError, OSError) as exc:
            self.counters.errors += 1
            self.log(f"{doc.path}: cannot record revision: {exc}")
            return False
        st.log("bump", payload["id"], payload["revision"], doc.path.as_posix(), f"watch: edited in place, {old} -> "
               f"{payload['revision']}")
        st.resolve_conflicts(["revision"], artifact_id=payload["id"], reason="watch revision")
        st.observe(doc.meta_path)
        self.counters.revised += 1
        self.log(f"revision {old} -> {payload['revision']}: {doc.path}")
        for written in {doc.meta_path, doc.path}:
            try:
                s = written.stat()
                self.snapshot[str(written)] = (s.st_mtime_ns, s.st_size)
                self._written.add(str(written))
            except OSError:
                pass
        return True

    def _stamp(self, st: Store, root: Path, host: Path, sig: tuple[int, int]) -> None:
        from somnus.commands._common import Ctx
        from somnus.commands.stamp import _plan

        ctx = Ctx(_cfg=self._cfg(root))
        args = types.SimpleNamespace(type=None, title=None, inline=False)
        try:
            plan = _plan(host, args, ctx)
        except SomnusError as exc:
            self.counters.errors += 1
            self.log(f"{host}: cannot stamp: {exc.diagnostics[0].message if exc.diagnostics else exc}")
            return
        if plan is None:
            return
        target, _old, new, payload = plan
        try:
            current = host.stat()
            if (current.st_mtime_ns, current.st_size) != sig:
                return  # changed while we planned; the next tick settles it again
            D.atomic_write(target, new)
        except OSError as exc:
            self.counters.errors += 1
            self.log(f"{host}: write failed: {exc}")
            return
        st.log("stamp", payload["id"], 1, host.as_posix(), f"watch: inferred {payload['classification']['type']}")
        st.observe(target)
        self.counters.stamped += 1
        self.log(f"stamped {target} ({payload['classification']['type']})")
        for written in {target, host}:
            try:
                s = written.stat()
                self.snapshot[str(written)] = (s.st_mtime_ns, s.st_size)
                self._written.add(str(written))
            except OSError:
                pass

    # ------------------------------------------------------------ heartbeat and loop
    def write_status(self, roots: list[Path]) -> None:
        """Atomically publish the heartbeat."""
        data = {
            "pid": os.getpid(),
            "version": __version__,
            "started_at": self.started_at,
            "last_tick_at": now_iso(),
            "roots": [str(r) for r in roots],
            "settings": asdict(self.settings),
            "counters": asdict(self.counters),
            "pending": len(self.pending),
            "tracked_files": len(self.snapshot),
        }
        D.atomic_write(self.home / STATUS_NAME, json.dumps(data, indent=2) + "\n")

    def run(self, once: bool = False) -> int:
        """Loop until signalled (or one pass with ``once``)."""
        lock = InstanceLock(self.home)
        if not lock.acquire():
            raise SomnusError("another somnus watcher is already running (see 'somnus daemon status')")

        def _stop(signum, frame) -> None:  # noqa: ARG001 - signal handler signature
            self.stopping = True

        for name in ("SIGTERM", "SIGINT", "SIGBREAK", "SIGHUP"):
            sig = getattr(signal, name, None)
            if sig is not None:
                try:
                    signal.signal(sig, _stop)
                except (ValueError, OSError):
                    pass
        self.log(f"somnus watch {__version__}: interval {self.settings.interval}s, stamp {self.settings.stamp}")
        try:
            while not self.stopping:
                started = time.monotonic()
                try:
                    self.tick()
                except SomnusError as exc:
                    self.counters.errors += 1
                    self.log(f"pass failed: {exc}")
                except Exception as exc:  # noqa: BLE001 - a daemon reports and keeps running
                    self.counters.errors += 1
                    self.log(f"pass failed: {type(exc).__name__}: {exc}")
                roots = list(self.roots)
                if not roots and self.db_path.exists():
                    try:
                        with Store.open(self.db_path, actor=WATCH_ACTOR, create=False) as st:
                            roots = [r for _, r in st.roots()]
                    except SomnusError:
                        roots = []
                self.write_status(roots)
                if once:
                    break
                deadline = started + self.settings.interval
                while not self.stopping and time.monotonic() < deadline:
                    time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))
        finally:
            lock.release()
        self.log("somnus watch stopped")
        return 0
