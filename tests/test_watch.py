# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1af7c-0ab0-70fe-bbb0-b763f149e729"
#   revision: 3
#   title: "The always-on watcher, its single-instance lock, config, and service plans (D20)"
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
#       - target_ref: "urn:somnus:artifact:01a1af7c-0ab0-70fe-bbb0-b763f149e729"
#         aspects: ["content"]
#   time:
#     updated_at: "2026-11-06T12:39:37+00:00"
#   names:
#     slug: "the-always-on-watcher-its-single-instance-lock-config-and-service-plans-d20"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1af7c-0ab0-70fe-bbb0-b763f149e729"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""The always-on watcher, its single-instance lock, config, and service plans (D20)."""

from __future__ import annotations

import os
import time
import unittest
from pathlib import Path

from somnus import config as C
from somnus import document as D
from somnus import service
from somnus.db.store import Store
from somnus.output import SomnusError
from somnus.watch import InstanceLock, Settings, Watcher, is_locked, read_status

from test_commands import CliCase


def age(path: Path, seconds: float = 60.0) -> None:
    """Backdate a file so the watcher treats it as settled."""
    then = time.time() - seconds
    os.utime(path, (then, then))


class WatchCase(CliCase):
    def watcher(self, **overrides) -> Watcher:
        cfg = C.load(self.ws)
        settings = Settings.from_config(cfg, **overrides)
        self.logs: list[str] = []
        return Watcher(cfg.home, settings, log=self.logs.append)

    def ids(self) -> set[str]:
        with Store.open(C.load(self.ws).db_path, create=False) as st:
            return {r[0] for r in st.conn.execute("SELECT id FROM artifacts")}


class TestTick(WatchCase):
    def test_existing_files_are_not_adopted_by_default(self) -> None:
        self.init()
        old = self.write("old.py", "x = 1\n")
        age(old)
        w = self.watcher()
        w.tick()
        self.assertIsNone(D.load(old).envelope)
        w.tick()
        self.assertIsNone(D.load(old).envelope)

    def test_adopt_stamps_existing(self) -> None:
        self.init()
        old = self.write("old.py", "x = 1\n")
        age(old)
        self.watcher(adopt=True).tick()
        self.assertIsNotNone(D.load(old).envelope)
        self.assertEqual(len(self.ids()), 1)

    def test_new_file_waits_for_settle_then_stamps(self) -> None:
        self.init()
        w = self.watcher(settle=30.0)
        w.tick()
        new = self.write("new.md", "# Hello\n\nbody\n")
        w.tick()
        self.assertIsNone(D.load(new).envelope)
        self.assertIn(str(new.resolve()), w.pending)
        age(new)
        w.tick()
        doc = D.load(new)
        self.assertIsNotNone(doc.envelope)
        self.assertEqual(doc.payload["title"], "Hello")
        self.assertEqual(w.counters.stamped, 1)
        self.assertNotIn(str(new.resolve()), w.pending)

    def test_inline_mode_never_creates_sidecars(self) -> None:
        self.init()
        w = self.watcher()
        w.tick()
        for name in ("data.csv", "img.png"):
            age(self.write(name, "x\n"))
        w.tick()
        self.assertEqual(sorted(p.name for p in self.ws.iterdir()), ["data.csv", "img.png"])

    def test_all_mode_creates_sidecars(self) -> None:
        self.init()
        w = self.watcher(stamp="all")
        w.tick()
        age(self.write("data.csv", "x\n"))
        w.tick()
        self.assertTrue((self.ws / "data.csv.somnus.yaml").exists())

    def test_off_mode_indexes_only(self) -> None:
        self.init()
        w = self.watcher(stamp="off")
        w.tick()
        age(self.write("new.py", "x = 1\n"))
        w.tick()
        self.assertIsNone(D.load(self.ws / "new.py").envelope)

    def test_excluded_dirs_are_never_touched(self) -> None:
        self.init()
        w = self.watcher(adopt=True)
        venv = self.ws / ".venv" / "lib"
        venv.mkdir(parents=True)
        lib = venv / "mod.py"
        lib.write_text("x = 1\n")
        age(lib)
        w.tick()
        self.assertIsNone(D.load(lib).envelope)

    def test_edit_in_place_becomes_new_revision(self) -> None:
        self.init()
        w = self.watcher()
        w.tick()
        path = self.write("note.md", "# Note\n\nfirst\n")
        age(path)
        w.tick()
        self.assertEqual(D.load(path).payload["revision"], 1)
        with path.open("a", encoding="utf-8") as fh:
            fh.write("second\n")
        age(path, 30)
        w.tick()
        doc = D.load(path)
        self.assertEqual(doc.payload["revision"], 2)
        self.assertTrue(path.read_text().endswith("first\nsecond\n"))
        _, out, _ = self.cli("q", "--conflicts")
        self.assertNotIn("revision ", out)

    def test_revise_off_leaves_conflict(self) -> None:
        self.init()
        w = self.watcher(revise="off")
        w.tick()
        path = self.write("note.md", "# Note\n\nfirst\n")
        age(path)
        w.tick()
        with path.open("a", encoding="utf-8") as fh:
            fh.write("second\n")
        age(path, 30)
        w.tick()
        self.assertEqual(D.load(path).payload["revision"], 1)
        _, out, _ = self.cli("q", "--conflicts")
        self.assertIn("revision", out)

    def test_deletion_marks_missing(self) -> None:
        self.init()
        w = self.watcher()
        w.tick()
        path = self.write("gone.md", "# Gone\n")
        age(path)
        w.tick()
        path.unlink()
        w.tick()
        _, out, _ = self.cli("ls")
        self.assertNotIn("gone.md", out)

    def test_missing_registry_waits(self) -> None:
        w = self.watcher()
        w.tick()
        self.assertTrue(any("registry missing" in line for line in self.logs))


class TestRunAndStatus(WatchCase):
    def test_once_writes_heartbeat(self) -> None:
        self.init()
        w = self.watcher()
        self.assertEqual(w.run(once=True), 0)
        data = read_status(w.home)
        self.assertIsNotNone(data)
        self.assertFalse(data["running"])
        self.assertEqual(data["roots"], [str(self.ws.resolve())])
        self.assertEqual(data["counters"]["ticks"], 1)

    def test_lock_is_exclusive(self) -> None:
        self.init()
        home = C.load(self.ws).home
        first = InstanceLock(home)
        self.assertTrue(first.acquire())
        try:
            self.assertTrue(is_locked(home))
            with self.assertRaises(SomnusError):
                self.watcher().run(once=True)
        finally:
            first.release()
        self.assertFalse(is_locked(home))

    def test_daemon_status_cli(self) -> None:
        self.init()
        code, out, _ = self.cli("daemon", "status")
        self.assertNotEqual(code, 0)
        self.assertIn("never ran", out)
        self.ok("watch", "--once", "--quiet")
        code, out, _ = self.cli("daemon", "status")
        self.assertIn("stopped", out)

    def test_install_dry_run_changes_nothing(self) -> None:
        self.init()
        out = self.ok("daemon", "install", "--dry-run")
        expected = "<string>somnus</string><string>watch</string>" if service.platform_name() == "darwin" else "somnus watch"
        self.assertIn(expected, out)


class TestConfig(WatchCase):
    def test_watch_and_carrier_tables(self) -> None:
        local = self.ws / ".somnus.toml"
        local.write_text('[watch]\ninterval = 2\nstamp = "off"\nrevise = "off"\nadopt = true\n'
                         '[carriers]\njson = "key"\n', encoding="utf-8")
        cfg = C.load(self.ws)
        self.assertEqual(cfg.json_carrier, "key")
        s = Settings.from_config(cfg)
        self.assertEqual((s.interval, s.stamp, s.revise, s.adopt), (2.0, "off", "off", True))

    def test_invalid_values(self) -> None:
        local = self.ws / ".somnus.toml"
        for text in ('[watch]\nstamp = "sometimes"\n', '[watch]\ninterval = -1\n', '[watch]\nbogus = 1\n',
                     '[carriers]\njson = "comment"\n', '[watch]\nadopt = "yes"\n'):
            with self.subTest(text=text):
                local.write_text(text, encoding="utf-8")
                with self.assertRaises(C.ConfigError):
                    C.load(self.ws)

    def test_template_parses(self) -> None:
        home = self.tmp / "home"
        home.mkdir(exist_ok=True)
        (home / "config.toml").write_text(C.CONFIG_TEMPLATE, encoding="utf-8")
        cfg = C.load(self.ws)
        self.assertEqual(cfg.watch["stamp"], "inline")


class TestServicePlans(unittest.TestCase):
    def test_linux_unit(self) -> None:
        plan = service.install_plan(Path("/h/.somnus"), "linux")
        self.assertIn("-m somnus watch", plan.content)
        self.assertIn(f"SOMNUS_HOME={Path('/h/.somnus')}", plan.content)
        self.assertEqual(plan.commands[-1][-2:], ["--now", service.UNIT_NAME])

    def test_darwin_plist(self) -> None:
        plan = service.install_plan(Path("/h/.somnus"), "darwin")
        self.assertIn("<key>KeepAlive</key><true/>", plan.content)
        self.assertTrue(str(plan.path).endswith("dev.somnus.watch.plist"))

    def test_windows_task(self) -> None:
        plan = service.install_plan(Path("C:/h"), "windows")
        self.assertIn(service.TASK_NAME, plan.commands[0])
        self.assertIsNone(plan.path)

    def test_apply_with_fake_runner(self) -> None:
        calls: list[list[str]] = []

        def runner(argv):
            calls.append(list(argv))
            return 0, ""

        plan = service.Plan("windows", None, "", [["a"], ["b"]])
        lines = service.apply(plan, runner=runner)
        self.assertEqual(calls, [["a"], ["b"]])
        self.assertTrue(all(": ok" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
