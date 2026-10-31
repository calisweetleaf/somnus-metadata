"""Installed-package acceptance for the somnus wheel (explicit invocation only).

Purpose
-------
Prove the *installed* distribution works through its real consumers: the `somnus`
console script, a real SQLite registry under an isolated ``$SOMNUS_HOME``, real
managed files on disk, a real stdio MCP client, and a real POSIX PTY for the
terminal UI (both the browser and the editor screen). This is not a unit test; it
never imports ``somnus`` from the source tree and never injects the checkout onto
``sys.path``.

Invocation (explicit; never discovered by ``unittest discover``)
---------------------------------------------------------------
    python tests/acceptance/installed_package_acceptance.py
    python tests/acceptance/installed_package_acceptance.py --repo /path/to/somnus-metadata
    python tests/acceptance/installed_package_acceptance.py --keep      # keep the temp run tree

The module is named without a ``test`` prefix and this directory has no
``__init__.py``, so ``python -m unittest discover -s tests`` does not collect it.
Running it explicitly must not silently skip: a missing prerequisite (no wheel
builder, no venv module, no POSIX PTY) is a harness error with exit code 2, and a
check that cannot run is reported as ``not_run`` in the artifacts and summary.

Prerequisites
-------------
- Python 3.11 or newer on ``PATH`` as the interpreter running this script.
- A wheel builder, tried in order: ``uv build``, ``python -m build``,
  ``python -m pip wheel``.
- A virtual-environment creator, tried in order: ``uv venv``, ``python -m venv``.
- POSIX with ``pty``/``termios`` for the terminal checks.

Isolation and cleanup ownership
-------------------------------
Everything is created under one ``tempfile.mkdtemp()`` tree:
``build-src/`` (a copy of ``pyproject.toml``, ``README.md``, and ``src/somnus``
used to build the wheel, so the checkout is never written to), ``dist/``,
``venv/``, ``home/`` (the isolated ``$SOMNUS_HOME`` and its real SQLite registry),
``work/``, and ``cycle/``. The user's real registry is never touched: this script
removes any inherited ``SOMNUS_HOME`` and sets its own for every child process.
The whole tree is deleted on exit unless ``--keep`` is given, in which case its
path is printed.

Artifacts
---------
Written under ``<tmp>/runs/<UTC timestamp>/``: ``result.json`` (machine-readable
check list with counts), ``result.md`` (per-check summary), and ``result.log``
(the exact commands and output). With ``--keep``, copy them somewhere durable.

Exit codes
----------
0  every check passed
1  at least one check failed
2  harness error (missing prerequisite, build/install failure, or a required
   check that could not run on this platform)
"""

from __future__ import annotations

import argparse
import json
import os
import pty
import re
import select
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

if os.name == "posix":
    import fcntl
    import termios

CHECK_TIMEOUT = 180
MCP_TIMEOUT = 120

EXPECTED_TOOLS = {
    "brief", "bump", "check", "fork", "index", "init", "ls", "migrate",
    "new", "q", "regions", "schema", "set", "stale", "stamp", "status",
}


class HarnessError(Exception):
    """The harness cannot proceed (missing prerequisite or failed build/install)."""


class Recorder:
    """Collects check results and the command log for one run."""

    def __init__(self) -> None:
        self.results: list[dict] = []
        self.log: list[str] = []

    def record(self, name: str, status: str, detail: str = "") -> None:
        if status not in ("pass", "fail", "not_run"):
            raise HarnessError(f"invalid check status {status!r}")
        self.results.append({"check": name, "status": status, "detail": detail[:600]})
        label = {"pass": "PASS", "fail": "FAIL", "not_run": "NOT RUN"}[status]
        line = f"[{label}] {name}" + (f" :: {detail[:200]}" if detail else "")
        self.log.append(line)
        print(line, flush=True)

    def note(self, line: str) -> None:
        self.log.append(line)


class Installed:
    """A built wheel installed into an isolated venv, plus isolated home/work trees."""

    def __init__(self, repo: Path, root: Path, rec: Recorder) -> None:
        self.repo = repo
        self.root = root
        self.rec = rec
        self.python = root / "venv" / "bin" / "python"
        self.somnus = root / "venv" / "bin" / "somnus"
        self.home = root / "home"
        self.work = root / "work"
        self.cycle = root / "cycle"
        self.cycle_home = root / "cycle-home"
        self.wheel: Optional[Path] = None

    # ------------------------------------------------------------- build/install
    def _tool(self, args: list[str], *, cwd: Path, env: Optional[dict] = None) -> subprocess.CompletedProcess:
        full = dict(os.environ)
        full.pop("SOMNUS_HOME", None)
        full.pop("PYTHONPATH", None)
        if env:
            full.update(env)
        proc = subprocess.run(args, cwd=str(cwd), env=full, capture_output=True, text=True, timeout=CHECK_TIMEOUT)
        self.rec.note(f"$ {' '.join(args)}  (exit {proc.returncode})")
        if proc.stdout.strip():
            self.rec.note(proc.stdout.rstrip())
        if proc.stderr.strip():
            self.rec.note("[stderr] " + proc.stderr.rstrip())
        return proc

    def build(self) -> None:
        """Build the wheel from a temp copy of the source so the checkout stays clean."""
        src = self.root / "build-src"
        src.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.repo / "pyproject.toml", src / "pyproject.toml")
        readme = self.repo / "README.md"
        if readme.is_file():
            shutil.copy2(readme, src / "README.md")
        shutil.copytree(self.repo / "src", src / "src",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
        dist = self.root / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        attempts = (
            (["uv", "build", "--wheel", "--out-dir", str(dist)], "uv build"),
            ([sys.executable, "-m", "build", "--wheel", "--outdir", str(dist)], "python -m build"),
            ([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(dist), "."], "pip wheel"),
        )
        errors = []
        for args, label in attempts:
            if shutil.which(args[0]) is None and args[0] != sys.executable:
                errors.append(f"{label}: {args[0]} not found")
                continue
            try:
                proc = self._tool(args, cwd=src)
            except (OSError, subprocess.TimeoutExpired) as exc:
                errors.append(f"{label}: {exc}")
                continue
            wheels = sorted(dist.glob("somnus_metadata-*.whl"))
            if proc.returncode == 0 and wheels:
                self.wheel = wheels[-1]
                self.rec.note(f"built {self.wheel.name} with {label}")
                return
            errors.append(f"{label}: exit {proc.returncode}")
        raise HarnessError("no wheel builder succeeded: " + "; ".join(errors))

    def install(self) -> None:
        """Create the venv and install the wheel; no source path is injected."""
        if self.wheel is None:
            raise HarnessError("install called before a successful build")
        venv = self.root / "venv"
        attempts = (
            (["uv", "venv", str(venv)], "uv venv"),
            ([sys.executable, "-m", "venv", str(venv)], "python -m venv"),
        )
        errors = []
        for args, label in attempts:
            if shutil.which(args[0]) is None and args[0] != sys.executable:
                errors.append(f"{label}: {args[0]} not found")
                continue
            try:
                proc = self._tool(args, cwd=self.root)
            except (OSError, subprocess.TimeoutExpired) as exc:
                errors.append(f"{label}: {exc}")
                continue
            if proc.returncode == 0 and self.python.is_file():
                break
            errors.append(f"{label}: exit {proc.returncode}")
        else:
            raise HarnessError("no venv creator succeeded: " + "; ".join(errors))
        if shutil.which("uv"):
            proc = self._tool(["uv", "pip", "install", "--python", str(self.python), str(self.wheel)],
                              cwd=self.root)
        else:
            proc = self._tool([str(self.python), "-m", "pip", "install", str(self.wheel)], cwd=self.root)
        if proc.returncode != 0:
            raise HarnessError(f"wheel install failed: exit {proc.returncode}")
        self.home.mkdir(parents=True, exist_ok=True)
        self.work.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------- invocation
    def run(self, args: list[str], *, cwd: Optional[Path] = None,
            home: Optional[Path] = None, env: Optional[dict] = None) -> tuple[int, str, str, str]:
        """Run the installed CLI; return (exit, combined, stdout, stderr)."""
        full = dict(os.environ)
        full["SOMNUS_HOME"] = str(home or self.home)
        full["NO_COLOR"] = "1"
        full.pop("PYTHONPATH", None)
        full.pop("EDITOR", None)
        full.pop("VISUAL", None)
        if env:
            full.update(env)
        proc = subprocess.run([str(self.somnus), *args], cwd=str(cwd or self.work), env=full,
                              capture_output=True, text=True, timeout=CHECK_TIMEOUT)
        self.rec.note(f"$ somnus {' '.join(args)}  (exit {proc.returncode})")
        if proc.stdout.strip():
            self.rec.note(proc.stdout.rstrip())
        if proc.stderr.strip():
            self.rec.note("[stderr] " + proc.stderr.rstrip())
        return proc.returncode, proc.stdout + proc.stderr, proc.stdout, proc.stderr


class McpClient:
    """Minimal MCP stdio client: newline-delimited JSON-RPC over real pipes."""

    def __init__(self, installed: Installed, cwd: Path) -> None:
        env = dict(os.environ)
        env["SOMNUS_HOME"] = str(installed.home)
        env["NO_COLOR"] = "1"
        env.pop("PYTHONPATH", None)
        self.proc = subprocess.Popen([str(installed.somnus), "mcp"], cwd=str(cwd), env=env,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.rec = installed.rec
        self.watchdog = threading.Timer(MCP_TIMEOUT, self._abort)
        self.watchdog.daemon = True
        self.watchdog.start()

    def _abort(self) -> None:
        """Kill the server so a hung request cannot block the harness."""
        try:
            self.proc.kill()
        except OSError:
            pass

    def request(self, mid: int, method: str, params: Optional[dict] = None) -> dict:
        assert self.proc.stdin is not None and self.proc.stdout is not None
        msg: dict = {"jsonrpc": "2.0", "id": mid, "method": method}
        if params is not None:
            msg["params"] = params
        self.rec.note("-> " + json.dumps(msg))
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise EOFError("mcp server closed stdout")
        self.rec.note("<- " + line.rstrip())
        return json.loads(line)

    def raw(self, line: str) -> dict:
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.rec.note("-> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        reply = self.proc.stdout.readline()
        if not reply:
            raise EOFError("mcp server closed stdout")
        self.rec.note("<- " + reply.rstrip())
        return json.loads(reply)

    def close(self) -> None:
        self.watchdog.cancel()
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.wait(timeout=15)
        except (subprocess.TimeoutExpired, BrokenPipeError, OSError):
            self.proc.kill()


# --------------------------------------------------------------------------- phases


def phase_install(inst: Installed) -> None:
    rec = inst.rec
    proc = subprocess.run([str(inst.somnus), "--version"], capture_output=True, text=True,
                          timeout=CHECK_TIMEOUT)
    rec.record("install: somnus --version", "pass" if proc.returncode == 0 and proc.stdout.strip() == "somnus 2.1.0" else "fail",
               proc.stdout.strip() or proc.stderr.strip())
    probe = subprocess.run([str(inst.python), "-c", "import somnus; print(somnus.__file__)"],
                           capture_output=True, text=True, timeout=CHECK_TIMEOUT)
    path = probe.stdout.strip()
    inside = str(inst.root / "venv") in path and str(inst.repo) not in path
    rec.record("install: import resolves inside the isolated venv, not the checkout",
               "pass" if inside else "fail", path)
    data = subprocess.run([str(inst.python), "-c", "from importlib import resources; "
                           "print(resources.files('somnus.db').joinpath('schema.sql').is_file())"],
                          capture_output=True, text=True, timeout=CHECK_TIMEOUT)
    rec.record("install: packaged schema.sql is present",
               "pass" if data.stdout.strip() == "True" else "fail", data.stdout.strip())


def phase_lifecycle(inst: Installed) -> None:
    rec = inst.rec
    code, out, so, se = inst.run(["init", "--root", str(inst.work)])
    rec.record("lifecycle: init creates config.toml and a real SQLite registry",
               "pass" if code == 0 and (inst.home / "config.toml").is_file()
               and (inst.home / "somnus.db").is_file() else "fail", se.strip() or out.strip())

    code, out, so, se = inst.run(["new", "specification", "Widget Spec", "--dir", str(inst.work)])
    target = inst.work / "widget-spec.md"
    rec.record("lifecycle: new scaffolds a conformant artifact and prints its path on stdout",
               "pass" if code == 0 and target.is_file() and str(target) in so else "fail",
               out.strip().replace("\n", " | "))

    code, out, so, se = inst.run(["check", str(target)])
    rec.record("lifecycle: check is clean at core level",
               "pass" if code == 0 and "0 error(s)" in se else "fail", se.strip())

    code, out, so, se = inst.run(["index"])
    rec.record("lifecycle: index is idempotent for a file `new` already observed",
               "pass" if code == 0 and "unchanged 1" in se else "fail", se.strip())

    code, out, so, se = inst.run(["ls"])
    rec.record("lifecycle: ls lists one present artifact",
               "pass" if code == 0 and "Widget Spec" in so else "fail", so.strip()[:100])

    code, out, so, se = inst.run(["q", "--docs"])
    rec.record("lifecycle: q --docs returns the artifact row",
               "pass" if code == 0 and "widget-spec.md" in so else "fail", so.strip()[:100])

    code, out, so, se = inst.run(["q", "--history"])
    rec.record("lifecycle: q --history shows ledger events",
               "pass" if code == 0 and "new" in so and "observe" in so else "fail",
               so.strip().splitlines()[0] if so.strip() else se.strip())

    before = target.read_text(encoding="utf-8")
    body_before = before.split("---\n", 2)[2]
    code, out, so, se = inst.run(["set", str(target), "title=Widget Spec Revised"])
    after = target.read_text(encoding="utf-8")
    rec.record("lifecycle: set creates revision 2",
               "pass" if code == 0 and "revision 2" in se else "fail", se.strip() or so.strip())
    rec.record("lifecycle: set preserves host bytes outside the envelope byte-for-byte",
               "pass" if after.split("---\n", 2)[2] == body_before else "fail", "body compared byte-for-byte")

    code, out, so, se = inst.run(["bump", str(target), "--reason", "review pass"])
    rec.record("lifecycle: bump creates revision 3",
               "pass" if code == 0 and "revision 2 -> 3" in se else "fail", se.strip() or so.strip())

    code, out, so, se = inst.run(["status", str(target), "active", "--reason", "approved"])
    rec.record("lifecycle: an illegal transition is refused with E_LIFECYCLE",
               "pass" if code == 1 and "E_LIFECYCLE" in out and "not permitted" in out else "fail",
               out.strip().replace("\n", " | ")[:200])
    code, out, so, se = inst.run(["status", str(target), "proposed", "--reason", "ready for review"])
    rec.record("lifecycle: a legal transition creates revision 4 and sets proposed",
               "pass" if code == 0 and "draft -> proposed" in se and "revision 4" in se else "fail",
               se.strip() or so.strip())

    fork = inst.work / "widget-fork.md"
    code, out, so, se = inst.run(["fork", str(target), "--out", str(fork), "--title", "Widget Fork"])
    rec.record("lifecycle: fork mints a new artifact recording derived_from",
               "pass" if code == 0 and fork.is_file() and "derived_from" in fork.read_text(encoding="utf-8")
               else "fail", se.strip() or so.strip())

    code, out, so, se = inst.run(["index"])
    rec.record("lifecycle: re-index is idempotent",
               "pass" if code == 0 and "unchanged 2" in se else "fail", se.strip())

    code, out, so, se = inst.run(["stale", "--days", "0"])
    rec.record("lifecycle: stale reports findings as a table",
               "pass" if code == 0 and "finding" in so and "stale-" in so else "fail",
               so.strip().replace("\n", " | ")[:200])

    code, out, so, se = inst.run(["regions", str(target)])
    rec.record("lifecycle: regions audits markers", "pass" if code == 0 else "fail",
               (so.strip() or se.strip())[:140])

    js = inst.work / "schema.json"
    code, out, so, se = inst.run(["schema", "--json-schema", "--out", str(js)])
    ok = code == 0 and js.is_file()
    if ok:
        data = json.loads(js.read_text(encoding="utf-8"))
        ok = data.get("$id") == "somnus://metadata/core/2.0.0" and "$defs" in data
    rec.record("lifecycle: schema --json-schema exports Draft 2020-12 with the core $id",
               "pass" if ok else "fail", se.strip() or so.strip())

    code, out, so, se = inst.run(["brief"])
    rec.record("lifecycle: brief prints the agent cheat sheet",
               "pass" if code == 0 and len(so) > 400 and "somnus" in so.lower() else "fail", so.strip()[:100])

    code, out, so, se = inst.run(["q", "--tables"])
    rec.record("lifecycle: q --tables lists the schema",
               "pass" if code == 0 and "artifacts" in so else "fail", so.strip()[:100])


def strip_envelope(text: str, opener: str, closer: str) -> list[str]:
    """Host lines of a stamped file with its envelope block removed."""
    out: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.rstrip() == opener:
            inside = True
            continue
        if inside:
            if line.rstrip() == closer:
                inside = False
            continue
        out.append(line)
    return out


def phase_host_preservation(inst: Installed) -> None:
    rec = inst.rec
    toml = inst.work / "host.toml"
    toml.write_text('[package]\nname = "widget"\nversion = "1.0.0"\n', encoding="utf-8")
    original = toml.read_text(encoding="utf-8")
    code, out, so, se = inst.run(["stamp", str(toml)])
    rec.record("host: stamp dry-run shows a diff and does not write",
               "pass" if code == 0 and toml.read_text(encoding="utf-8") == original else "fail",
               so.strip()[:140])

    code, out, so, se = inst.run(["stamp", str(toml), "--write"])
    stamped = toml.read_text(encoding="utf-8")
    kept = strip_envelope(stamped, "# somnus:metadata:v2", "# somnus:end")
    rec.record("host: stamp --write inserts an envelope and keeps every host line byte-for-byte",
               "pass" if code == 0 and kept == original.splitlines()
               and "# somnus:metadata:v2" in stamped else "fail", f"{len(kept)} host lines preserved")

    xml = inst.work / "host.xml"
    xml.write_text('<?xml version="1.0"\n  encoding="UTF-8"?>\n<root/>\n', encoding="utf-8")
    before = xml.read_text(encoding="utf-8")
    code, out, so, se = inst.run(["stamp", str(xml), "--write"])
    rec.record("host: an unpreservable preamble is refused with E_HOST and the file is untouched",
               "pass" if code == 1 and "E_HOST" in out and xml.read_text(encoding="utf-8") == before
               else "fail", out.strip()[:200])


def phase_conflicts_and_recovery(inst: Installed) -> None:
    rec = inst.rec
    inst.run(["new", "report", "Conflict Subject", "--dir", str(inst.work)])
    subject = inst.work / "conflict-subject.md"
    inst.run(["index"])
    subject.write_text(subject.read_text(encoding="utf-8") + "\nDrifted body line.\n", encoding="utf-8")
    code, out, so, se = inst.run(["index"])
    rec.record("conflict: index reports the divergent revision",
               "pass" if code == 1 and "conflicts opened 1" in se else "fail", se.strip())

    code, out, so, se = inst.run(["q", "--conflicts"])
    rec.record("conflict: q --conflicts shows an open revision conflict",
               "pass" if "revision" in so and "open" in so else "fail",
               so.strip().replace("\n", " | ")[:200])

    code, out, so, se = inst.run(["bump", str(subject), "--reason", "accept drifted state"])
    rec.record("conflict: bump resolves the revision conflict",
               "pass" if code == 0 else "fail", (se.strip() or so.strip())[:140])
    code, out, so, se = inst.run(["q", "--conflicts"])
    rec.record("conflict: no open conflicts remain",
               "pass" if "open" not in so else "fail", so.strip().replace("\n", " | ")[:200])

    inst.run(["new", "report", "Vanish Subject", "--dir", str(inst.work)])
    gone = inst.work / "vanish-subject.md"
    inst.run(["index"])
    payload = gone.read_text(encoding="utf-8")
    gone.unlink()
    code, out, so, se = inst.run(["index"])
    rec.record("recovery: a vanished file is marked absent, not deleted",
               "pass" if code == 0 and "missing 1" in se else "fail", se.strip())
    code, out, so, se = inst.run(["stale", "--days", "0"])
    rec.record("recovery: stale reports the missing file",
               "pass" if "missing-file" in so else "fail", so.strip().replace("\n", " | ")[:200])
    gone.write_text(payload, encoding="utf-8")
    code, out, so, se = inst.run(["index"])
    rec.record("recovery: restoring the file re-observes it",
               "pass" if code == 0 and "missing 0" in se else "fail", se.strip())


def phase_migrate(inst: Installed) -> None:
    rec = inst.rec
    legacy = inst.work / "legacy-v01.md"
    legacy.write_text("---\nsomnus:\n  id: urn:somnus:artifact:legacy-0001\n"
                      "  title: Legacy Doc\n  revision: 1\n  schema: somnus://metadata/v0.1\n"
                      "---\n# Legacy\n\nBody.\n", encoding="utf-8")
    before = legacy.read_text(encoding="utf-8")
    code, out, so, se = inst.run(["migrate", str(legacy)])
    rec.record("migrate: a malformed legacy header is refused and the file is untouched",
               "pass" if code == 1 and legacy.read_text(encoding="utf-8") == before else "fail",
               out.strip().replace("\n", " | ")[:160])
    legacy.unlink()

    source = inst.repo / "archive" / "v0.1" / "examples" / "specification-example.md"
    if not source.is_file():
        rec.record("migrate: a real v0.1 document upgrades and validates", "not_run",
                   f"fixture missing: {source}")
        return
    real = inst.work / "v01-specification.md"
    shutil.copyfile(source, real)
    original = real.read_text(encoding="utf-8")
    code, out, so, se = inst.run(["migrate", str(real)])
    rec.record("migrate: dry run of a real v0.1 document shows a diff and does not write",
               "pass" if code == 0 and "+++ b/" in so and real.read_text(encoding="utf-8") == original
               else "fail", so.strip().splitlines()[0] if so.strip() else "")
    code, out, so, se = inst.run(["migrate", str(real), "--write"])
    migrated = real.read_text(encoding="utf-8")
    code2, out2, so2, se2 = inst.run(["check", str(real)])
    rec.record("migrate: --write upgrades the document and it validates at core level",
               "pass" if code == 0 and migrated != original
               and "somnus://metadata/core/2.0.0" in migrated and code2 == 0 else "fail", se2.strip()[:140])
    code, out, so, se = inst.run(["index"])
    rec.record("migrate: the migrated document indexes cleanly",
               "pass" if code == 0 and "invalid 0" in se else "fail", se.strip())


def phase_diagnostics(inst: Installed) -> None:
    rec = inst.rec
    unstamped = inst.work / "unstamped-note.md"
    unstamped.write_text("# An ordinary markdown file\n\nNo Somnus header here.\n", encoding="utf-8")
    code, out, so, se = inst.run(["check", "--all"])
    rec.record("diagnostics: check --all reports W_UNMANAGED as a warning and still exits 0",
               "pass" if code == 0 and "warning W_UNMANAGED" in so else "fail",
               " | ".join(ln for ln in so.splitlines() if "W_UNMANAGED" in ln)[:200])

    broken = inst.work / "broken.md"
    broken.write_text("---\nsomnus:\n  schema: \"somnus://metadata/core/2.0.0\"\n"
                      "  id: \"urn:somnus:artifact:01920000-0000-7000-8000-0000000000f1\"\n"
                      "  revision: 1\n  title: \"Broken\"\n"
                      "  classification:\n    category: \"engineering\"\n    type: \"nonsense\"\n"
                      "    role: \"informative\"\n    scope: \"component\"\n    tags: []\n"
                      "  lifecycle:\n    status: \"draft\"\n"
                      "  authority:\n    standing: \"candidate\"\n"
                      "    scopes:\n      - target_ref: \"urn:somnus:artifact:01920000-0000-7000-8000-0000000000f1\"\n"
                      "        aspects: [\"content\"]\n  time: {}\n"
                      "  knowledge:\n    coverage: \"artifact\"\n"
                      "    subjects: [\"urn:somnus:artifact:01920000-0000-7000-8000-0000000000f1\"]\n"
                      "  access:\n    visibility: \"internal\"\n    allowed_uses: [\"archive\", \"search\", \"reason\"]\n"
                      "  ingestion:\n    disposition: \"candidate\"\n    body_role: \"specification\"\n"
                      "---\n# Broken\n", encoding="utf-8")
    code, out, so, se = inst.run(["check", str(broken)])
    shaped = re.match(r"^broken\.md:\d+:\d+: error E_SCHEMA somnus\.classification\.type: ", so.strip())
    rec.record("diagnostics: an invalid document exits 1 with a compiler-style diagnostic on stdout",
               "pass" if code == 1 and shaped is not None else "fail",
               so.strip().splitlines()[0] if so.strip() else "")

    code, out, so, se = inst.run(["check", str(broken), "--tsv"])
    rows = so.strip().splitlines()
    rec.record("diagnostics: --tsv emits seven tab-separated fields with no header",
               "pass" if code == 1 and rows and all(len(r.split("\t")) == 7 for r in rows) else "fail",
               repr(rows[0])[:160] if rows else "")

    code, out, so, se = inst.run(["--no-color", "check", str(broken)])
    rec.record("diagnostics: --no-color emits no ANSI escapes",
               "pass" if "\x1b[" not in so else "fail", repr(so.strip()[:60]))
    broken.unlink()


def phase_agent_hints(inst: Installed) -> None:
    """Agent-facing behaviors the skill relies on: full-text search, adoption hints, refusals."""
    rec = inst.rec
    code, out, so, se = inst.run(["q", "--text", "widget", "spec"])
    rec.record("hints: q --text matches an unquoted multi-word search",
               "pass" if code == 0 and "widget-spec.md" in so else "fail", so.strip()[:160])

    code, out, so, se = inst.run(["q", "--text", "zzqxblank"])
    rec.record("hints: an empty full-text result prints the adoption hint",
               "pass" if code == 0 and "no matches" in out and "stamp" in out else "fail",
               out.strip().replace("\n", " | ")[:200])

    unmanaged = inst.work / "unmanaged-note.md"
    unmanaged.write_text("# An ordinary markdown file\n\nNo Somnus header here.\n", encoding="utf-8")
    code, out, so, se = inst.run(["index"])
    rec.record("hints: index reports unmanaged files and how to adopt them",
               "pass" if code == 0 and "unmanaged (no Somnus header" in out and "somnus stamp" in out else "fail",
               " | ".join(ln for ln in out.splitlines() if "unmanaged" in ln or "adopt" in ln)[:200])

    broad = inst.root / "home-broad"
    broad.mkdir(parents=True, exist_ok=True)
    inst.run(["init"], cwd=broad, home=broad)
    code, out, so, se = inst.run(["index"], cwd=broad, home=broad, env={"HOME": str(broad)})
    rec.record("hints: index with no registered roots refuses a home-directory fallback",
               "pass" if code == 2 and "too broad to scan" in out else "fail",
               out.strip().replace("\n", " | ")[:200])


def phase_mcp(inst: Installed) -> None:
    rec = inst.rec
    client = McpClient(inst, inst.work)
    try:
        resp = client.request(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                               "clientInfo": {"name": "acceptance", "version": "1"}})
        info = resp.get("result", {})
        rec.record("mcp: initialize negotiates the protocol version",
                   "pass" if info.get("protocolVersion") == "2024-11-05"
                   and info.get("serverInfo", {}).get("name") == "somnus" else "fail",
                   json.dumps(info.get("serverInfo", {})))

        resp = client.request(2, "tools/list")
        tools = resp.get("result", {}).get("tools", [])
        names = {t["name"] for t in tools}
        rec.record("mcp: tools/list exposes exactly the non-interactive commands",
                   "pass" if names == EXPECTED_TOOLS else "fail",
                   f"{len(tools)} tools: {','.join(sorted(names))}")
        rec.record("mcp: the interactive and recursive commands are excluded",
                   "pass" if "edit" not in names and "mcp" not in names else "fail", ",".join(sorted(names)))
        rec.record("mcp: every tool declares a closed input schema",
                   "pass" if all(t["inputSchema"]["type"] == "object"
                                 and t["inputSchema"]["additionalProperties"] is False for t in tools)
                   else "fail", "")

        resp = client.request(3, "tools/call", {"name": "ls", "arguments": {}})
        result = resp.get("result", {})
        text = result.get("content", [{}])[0].get("text", "")
        rec.record("mcp: tools/call returns plain text content",
                   "pass" if result.get("isError") is False and "Widget Spec" in text and "{" not in text
                   else "fail", text.replace("\n", " | ")[:200])

        resp = client.request(4, "tools/call", {"name": "check", "arguments": {"paths": [str(inst.work / "nope.md")]}})
        result = resp.get("result", {})
        text = result.get("content", [{}])[0].get("text", "")
        rec.record("mcp: a failing command returns isError with the diagnostic text",
                   "pass" if result.get("isError") is True and "E_IO" in text else "fail",
                   text.replace("\n", " | ")[:200])

        resp = client.request(5, "tools/call", {"name": "ls", "arguments": {"bogus": 1}})
        result = resp.get("result", {})
        rec.record("mcp: an unknown argument is a tool error, not a crash",
                   "pass" if result.get("isError") is True
                   and "unknown argument" in result["content"][0]["text"] else "fail",
                   result.get("content", [{}])[0].get("text", "")[:140])

        resp = client.request(6, "no/such/method")
        rec.record("mcp: an unknown method returns JSON-RPC -32601",
                   "pass" if resp.get("error", {}).get("code") == -32601 else "fail",
                   json.dumps(resp.get("error", {})))

        resp = client.raw("{not json")
        rec.record("mcp: a parse error returns JSON-RPC -32700",
                   "pass" if resp.get("error", {}).get("code") == -32700 else "fail",
                   json.dumps(resp.get("error", {})))

        resp = client.request(7, "tools/call", {"name": "ls", "arguments": {"tsv": True}})
        text = resp.get("result", {}).get("content", [{}])[0].get("text", "")
        rec.record("mcp: --tsv tool content stays tab-separated text",
                   "pass" if "\t" in text and "{" not in text else "fail",
                   repr(text.splitlines()[0])[:140] if text else "")

        resp = client.request(8, "ping")
        rec.record("mcp: the session survives every error above",
                   "pass" if resp.get("result") == {} else "fail", json.dumps(resp)[:140])

        resp = client.request(9, "tools/call", {"name": "check", "arguments": {"paths": ["nope.md"]}})
        result = resp.get("result", {})
        text = result.get("content", [{}])[0].get("text", "")
        rec.record("mcp: a failed call with a relative path notes the server-directory resolution",
                   "pass" if result.get("isError") is True and "note: relative path(s) nope.md" in text
                   and "pass absolute paths" in text else "fail",
                   text.replace("\n", " | ")[:200])
    finally:
        client.close()
    stderr = client.proc.stderr.read() if client.proc.stderr else ""
    rec.record("mcp: the server writes nothing unexpected to stderr",
               "pass" if stderr.strip() == "" else "fail", stderr.strip()[:200])


def build_cycle(inst: Installed) -> Path:
    """Two artifacts whose `part_of` relations form a registry-wide cycle."""
    inst.cycle.mkdir(parents=True, exist_ok=True)
    a = "urn:somnus:artifact:01920000-0000-7000-8000-0000000000a1"
    b = "urn:somnus:artifact:01920000-0000-7000-8000-0000000000b1"
    program = ("import json,sys;from somnus import document as D;"
               "p=json.loads(sys.stdin.read());"
               "sys.stdout.write('---\\n'+D.canonical_yaml({'somnus':p})+'---\\n# '+p['title']+'\\n\\nBody.\\n')")
    for aid, title, other, name in ((a, "Alpha", b, "alpha.md"), (b, "Bravo", a, "bravo.md")):
        payload = {
            "schema": "somnus://metadata/core/2.0.0", "id": aid, "revision": 1, "title": title,
            "classification": {"category": "engineering", "type": "specification", "role": "informative",
                               "scope": "component", "tags": ["acceptance"]},
            "lifecycle": {"status": "draft"},
            "authority": {"standing": "candidate", "scopes": [{"target_ref": aid, "aspects": ["content"]}]},
            "time": {},
            "knowledge": {"coverage": "artifact", "subjects": [aid],
                          "relations": [{"id": "r-1", "subject": {"ref": aid}, "predicate": "part_of",
                                         "object": {"ref": other}, "assessment": "unassessed",
                                         "valid_time": {"basis": "timeless"}}]},
            "access": {"visibility": "internal", "allowed_uses": ["archive", "search", "reason"]},
            "ingestion": {"disposition": "candidate", "body_role": "specification"},
        }
        env = dict(os.environ)
        env.pop("SOMNUS_HOME", None)
        env.pop("PYTHONPATH", None)
        proc = subprocess.run([str(inst.python), "-c", program], input=json.dumps(payload),
                              capture_output=True, text=True, env=env, timeout=CHECK_TIMEOUT)
        if proc.returncode != 0:
            raise HarnessError(f"could not serialize the cycle fixture: {proc.stderr.strip()}")
        (inst.cycle / name).write_text(proc.stdout, encoding="utf-8")
    return inst.cycle / "alpha.md"


def phase_tui_pty(inst: Installed) -> None:
    rec = inst.rec
    if os.name != "posix":
        rec.record("tui: registry note stays inside the TUI frame under a real PTY", "not_run",
                   "requires a POSIX PTY; Windows terminal paths are not exercised here")
        return
    inst.cycle_home.mkdir(parents=True, exist_ok=True)
    target = build_cycle(inst)
    inst.run(["init", "--root", str(inst.cycle)], home=inst.cycle_home)
    code, out, so, se = inst.run(["index"], cwd=inst.cycle, home=inst.cycle_home)
    rec.record("tui: the fixture cycle is a real registry error",
               "pass" if code == 1 and "E_GRAPH" in out else "fail", out.strip()[:200])

    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    env = dict(os.environ, SOMNUS_HOME=str(inst.cycle_home), TERM="xterm", NO_COLOR="1")
    env.pop("PYTHONPATH", None)
    env.pop("EDITOR", None)
    env.pop("VISUAL", None)
    err_read, err_write = os.pipe()
    proc = subprocess.Popen([str(inst.somnus), "edit", str(target)], cwd=str(inst.cycle), env=env,
                            stdin=slave, stdout=slave, stderr=err_write, start_new_session=True)
    os.close(slave)
    os.close(err_write)
    out_bytes = bytearray()
    err_bytes = bytearray()
    try:
        for key in ("\r", "\x1b[F", " two", "\r", "s", "q"):
            time.sleep(0.3)
            os.write(master, key.encode())
        deadline = time.time() + 20
        while time.time() < deadline and proc.poll() is None:
            ready, _, _ = select.select([master, err_read], [], [], 0.2)
            for fd in ready:
                try:
                    data = os.read(fd, 65536)
                except OSError:
                    data = b""
                (out_bytes if fd == master else err_bytes).extend(data)
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGKILL)
        for fd, sink in ((master, out_bytes), (err_read, err_bytes)):
            try:
                while True:
                    data = os.read(fd, 65536)
                    if not data:
                        break
                    sink.extend(data)
            except OSError:
                pass
        os.close(master)
        os.close(err_read)
        proc.wait()

    stream = out_bytes.decode("utf-8", "replace")
    stderr = err_bytes.decode("utf-8", "replace")
    rec.record("tui: installed `somnus edit` writes no registry note to stderr",
               "pass" if "registry:" not in stderr else "fail", repr(stderr[:160]))
    rec.record("tui: the registry note is rendered inside the TUI frame",
               "pass" if "registry: E_GRAPH" in stream else "fail",
               repr(stream[stream.find("registry:"):][:100]) if "registry:" in stream else "absent")
    positioned = re.compile(r"\x1b\[\d+;1H")
    hits = list(positioned.finditer(stream))
    overflow = []
    for i, hit in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(stream)
        chunk = re.split(r"\x1b\[", stream[hit.end():end])[0]
        if "registry: E_GRAPH" in chunk and len(chunk) > 80:
            overflow.append(chunk[:60])
    rec.record("tui: the note stays within a positioned frame row", "pass" if not overflow else "fail",
               "; ".join(overflow)[:200])
    rec.record("tui: the save reached disk as revision 2",
               "pass" if "revision: 2" in target.read_text(encoding="utf-8") else "fail", "")


def drive_pty(inst: Installed, args: list[str], keys: str, *, cwd: Path,
              home: Optional[Path] = None, settle: float = 0.3) -> tuple[int, str, str]:
    """Run the installed CLI under a real PTY, write ``keys``, and return (exit, stream, stderr)."""
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    env = dict(os.environ, SOMNUS_HOME=str(home or inst.home), TERM="xterm", NO_COLOR="1")
    env.pop("PYTHONPATH", None)
    env.pop("EDITOR", None)
    env.pop("VISUAL", None)
    err_read, err_write = os.pipe()
    proc = subprocess.Popen([str(inst.somnus), *args], cwd=str(cwd), env=env,
                            stdin=slave, stdout=slave, stderr=err_write, start_new_session=True)
    os.close(slave)
    os.close(err_write)
    out_bytes = bytearray()
    err_bytes = bytearray()
    try:
        for key in keys:
            time.sleep(settle)
            os.write(master, key.encode())
        deadline = time.time() + 20
        while time.time() < deadline and proc.poll() is None:
            ready, _, _ = select.select([master, err_read], [], [], 0.2)
            for fd in ready:
                try:
                    data = os.read(fd, 65536)
                except OSError:
                    data = b""
                (out_bytes if fd == master else err_bytes).extend(data)
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGKILL)
        for fd, sink in ((master, out_bytes), (err_read, err_bytes)):
            try:
                while True:
                    data = os.read(fd, 65536)
                    if not data:
                        break
                    sink.extend(data)
            except OSError:
                pass
        os.close(master)
        os.close(err_read)
        proc.wait()
    inst.rec.note(f"$ somnus {' '.join(args)}  (pty, exit {proc.returncode})")
    return proc.returncode, out_bytes.decode("utf-8", "replace"), err_bytes.decode("utf-8", "replace")


def phase_tui_browser(inst: Installed) -> None:
    """Exercise the browser screen through a real PTY: clean quit and an editor round-trip."""
    rec = inst.rec
    if os.name != "posix":
        rec.record("tui: browser screen enters and leaves the alternate screen under a real PTY",
                   "not_run", "requires a POSIX PTY; Windows terminal paths are not exercised here")
        return
    enter = "\x1b[?1049h"
    leave = "\x1b[?1049l"

    code, stream, stderr = drive_pty(inst, ["edit"], "q", cwd=inst.work)
    rec.record("tui: browser screen quits cleanly under a real PTY",
               "pass" if code == 0 and enter in stream and leave in stream
               and stream.index(enter) < stream.index(leave) and stderr.strip() == "" else "fail",
               f"exit {code}; enter/leave ordered: {enter in stream and leave in stream}; stderr {stderr.strip()[:80]!r}")
    rec.record("tui: the browser renders the registry document count",
               "pass" if "documents in registry" in stream else "fail",
               repr(stream[stream.find("somnus edit:"):][:80]) if "somnus edit:" in stream else "absent")

    # enter opens the highlighted document in the editor; q closes it, then q closes the browser.
    code, stream, stderr = drive_pty(inst, ["edit"], "\rqq", cwd=inst.work)
    rec.record("tui: the browser opens the editor and returns to it, then exits 0",
               "pass" if code == 0 and stream.count(enter) == 1 and stream.count(leave) == 1
               and stderr.strip() == "" else "fail",
               f"exit {code}; enter {stream.count(enter)} leave {stream.count(leave)}; stderr {stderr.strip()[:80]!r}")


def write_artifacts(rec: Recorder, root: Path, wheel: Optional[Path], repo: Path) -> Path:
    """Write result.json/md/log under <root>/runs/<UTC timestamp>/ and return the directory."""
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_dir = root / "runs" / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for r in rec.results if r["status"] == "pass")
    failed = sum(1 for r in rec.results if r["status"] == "fail")
    not_run = sum(1 for r in rec.results if r["status"] == "not_run")
    payload = {
        "harness": "installed_package_acceptance",
        "repo": str(repo),
        "wheel": wheel.name if wheel else None,
        "wheel_sha256": sha256(wheel) if wheel else None,
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "checks": rec.results,
        "passed": passed,
        "failed": failed,
        "not_run": not_run,
    }
    (run_dir / "result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (run_dir / "result.log").write_text("\n".join(rec.log) + "\n", encoding="utf-8")
    lines = [
        "# Installed-package acceptance run", "",
        "I built the wheel, installed it into an isolated virtual environment, and drove the",
        "installed `somnus` entry point against a fresh `$SOMNUS_HOME`, real files, a real SQLite",
        "registry, a real stdio MCP client, and a real POSIX PTY.", "",
        f"- checks: {len(rec.results)}",
        f"- passed: {passed}",
        f"- failed: {failed}",
        f"- not run: {not_run}",
        f"- wheel: {payload['wheel']} sha256 {payload['wheel_sha256']}",
        f"- interpreter: {payload['python']} on {payload['platform']}", "",
    ]
    for r in rec.results:
        label = {"pass": "PASS", "fail": "FAIL", "not_run": "NOT RUN"}[r["status"]]
        lines.append(f"- {label} — {r['check']}" + (f" ({r['detail']})" if r["detail"] else ""))
    (run_dir / "result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return run_dir


def sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args(argv: Optional[list[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Installed-package acceptance for the somnus wheel (explicit invocation only).")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]),
                        help="repository root to build the wheel from (default: two levels above this file)")
    parser.add_argument("--keep", action="store_true",
                        help="keep the temporary build/venv/home/work tree and print its path")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    if not (repo / "pyproject.toml").is_file() or not (repo / "src" / "somnus").is_dir():
        print(f"harness error: {repo} is not a somnus source checkout", file=sys.stderr)
        return 2
    rec = Recorder()
    root = Path(tempfile.mkdtemp(prefix="somnus-acceptance-"))
    try:
        inst = Installed(repo, root, rec)
        try:
            inst.build()
            inst.install()
        except HarnessError as exc:
            print(f"harness error: {exc}", file=sys.stderr)
            return 2
        for phase in (phase_install, phase_lifecycle, phase_host_preservation,
                      phase_conflicts_and_recovery, phase_migrate, phase_diagnostics,
                      phase_agent_hints, phase_mcp, phase_tui_browser, phase_tui_pty):
            phase(inst)
        run_dir = write_artifacts(rec, root, inst.wheel, repo)
        failed = [r for r in rec.results if r["status"] == "fail"]
        not_run = [r for r in rec.results if r["status"] == "not_run"]
        print(f"\nartifacts: {run_dir}")
        print(f"passed {len(rec.results) - len(failed) - len(not_run)} / {len(rec.results)} "
              f"({len(failed)} failed, {len(not_run)} not run)")
        for r in failed:
            print("  FAIL", r["check"], "::", r["detail"])
        for r in not_run:
            print("  NOT RUN", r["check"], "::", r["detail"])
        if failed:
            return 1
        if not_run:
            print("harness error: required checks could not run on this platform", file=sys.stderr)
            return 2
        return 0
    finally:
        if args.keep:
            print(f"kept temp tree: {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
