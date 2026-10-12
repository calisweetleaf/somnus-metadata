"""End-to-end CLI workflows through ``somnus.cli.main`` in isolated temp homes."""

from __future__ import annotations

import io
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from somnus import document as D
from somnus.cli import main

REPO = Path(__file__).resolve().parents[1]
V01 = REPO / "archive" / "v0.1" / "examples"


class CliCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = self.tmp / "ws"
        self.ws.mkdir()
        self._env = os.environ.get("SOMNUS_HOME")
        self._cwd = Path.cwd()
        os.environ["SOMNUS_HOME"] = str(self.tmp / "home")
        os.chdir(self.tmp)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        if self._env is None:
            os.environ.pop("SOMNUS_HOME", None)
        else:
            os.environ["SOMNUS_HOME"] = self._env
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def ok(self, *argv: str) -> str:
        code, out, err = self.cli(*argv)
        self.assertEqual(code, 0, f"{argv}: {out}{err}")
        return out

    def init(self) -> None:
        self.ok("init", "--root", str(self.ws))

    def write(self, name: str, text: str) -> Path:
        path = self.ws / name
        path.write_bytes(text.encode("utf-8"))
        return path

    def payload(self, path: Path) -> dict:
        doc = D.load(path)
        self.assertIsNotNone(doc.payload, doc.issues)
        return doc.payload

    def db(self) -> sqlite3.Connection:
        return sqlite3.connect(self.tmp / "home" / "somnus.db")


class TestBasics(CliCase):
    def test_version_and_usage(self) -> None:
        self.assertEqual(self.cli("--version")[0], 0)
        self.assertEqual(self.cli()[0], 2)
        self.assertEqual(self.cli("new", "not-a-type", "X")[0], 2)

    def test_init_is_idempotent(self) -> None:
        self.init()
        self.init()
        self.assertTrue((self.tmp / "home" / "config.toml").is_file())
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM roots").fetchone()[0], 1)

    def test_registry_required_for_index(self) -> None:
        code, out, _ = self.cli("index")
        self.assertEqual(code, 2)
        self.assertIn("somnus init", out)

    def test_brief_and_schema(self) -> None:
        self.assertIn("somnus status", self.ok("brief"))
        out = self.ok("schema", "classification.type")
        self.assertIn("specification", out)
        self.assertIn("required: yes", out)
        self.assertIn("kind", self.ok("schema", "knowledge.claims"))
        self.assertEqual(self.cli("schema", "nope.field")[0], 2)
        exported = json.loads(self.ok("schema", "--json-schema"))
        self.assertEqual(exported["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(exported["$defs"]["somnus"]["additionalProperties"])


class TestNew(CliCase):
    def test_new_creates_valid_document(self) -> None:
        self.init()
        out = self.ok("new", "specification", "Memory Engine Architecture", "--dir", str(self.ws))
        path = Path(out.strip())
        somnus = self.payload(path)
        self.assertEqual(somnus["revision"], 1)
        self.assertEqual(somnus["lifecycle"]["status"], "draft")
        self.assertEqual(somnus["authority"]["scopes"][0]["target_ref"], somnus["id"])
        self.assertTrue(somnus["id"].startswith("urn:somnus:artifact:"))
        self.assertIn("created_at", somnus["time"])
        self.ok("check", str(path), "--level", "semantic")
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM docs").fetchone()[0], 1)
            actions = [r[0] for r in conn.execute("SELECT action FROM events ORDER BY id")]
        self.assertIn("new", actions)

    def test_title_collision_refused_unless_forced(self) -> None:
        self.init()
        self.ok("new", "plan", "Rollout Plan", "--dir", str(self.ws))
        other = self.tmp / "other"
        other.mkdir()
        code, out, _ = self.cli("new", "plan", "Rollout plan", "--dir", str(other))
        self.assertEqual(code, 1)
        self.assertIn("collides", out)
        self.ok("new", "plan", "Rollout plan", "--dir", str(other), "--force")

    def test_existing_file_refused(self) -> None:
        self.ok("new", "plan", "Same", "--dir", str(self.ws))
        self.assertEqual(self.cli("new", "plan", "Same", "--dir", str(self.ws))[0], 1)

    def test_html_comment_carrier(self) -> None:
        out = self.ok("new", "report", "Hidden Header", "--dir", str(self.ws), "--carrier", "html-comment")
        text = Path(out.strip()).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("<!-- somnus:metadata:v2\n"))
        self.ok("check", out.strip())


class TestStamp(CliCase):
    def test_dry_run_then_write_preserves_body(self) -> None:
        body = "# Field Notes\r\n\r\nSome body text.\r\n"
        path = self.write("notes.md", body)
        diff = self.ok("stamp", str(path))
        self.assertIn("+somnus:", diff)
        self.assertEqual(path.read_bytes(), body.encode())
        self.ok("stamp", str(path), "--write")
        raw = path.read_bytes().decode("utf-8")
        self.assertTrue(raw.endswith(body))
        self.assertIn("\r\n", raw.split(body)[0])
        somnus = self.payload(path)
        self.assertEqual(somnus["title"], "Field Notes")
        self.assertEqual(somnus["time"], {})
        self.ok("check", str(path))
        out = self.ok("stamp", str(path), "--write")
        self.assertEqual(out, "")

    def test_python_preamble_preserved(self) -> None:
        src = '#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n"""Data loader utility."""\nprint(1)\n'
        path = self.write("tool.py", src)
        self.ok("stamp", str(path), "--write")
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[:2], ["#!/usr/bin/env python", "# -*- coding: utf-8 -*-"])
        self.assertEqual(lines[2], "# somnus:metadata:v2")
        self.assertTrue(path.read_text(encoding="utf-8").endswith('"""Data loader utility."""\nprint(1)\n'))
        self.assertEqual(self.payload(path)["classification"]["type"], "source-code")
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_json_gets_sidecar(self) -> None:
        data = '{"a": 1}'
        path = self.write("state.json", data)
        self.ok("stamp", str(path), "--write")
        sidecar = self.ws / "state.json.somnus.yaml"
        self.assertTrue(sidecar.is_file())
        self.assertEqual(path.read_text(encoding="utf-8"), data)
        self.assertEqual(self.payload(path)["bindings"][0]["target"], "state.json")
        self.ok("check", str(sidecar))


class TestLifecycleCommands(CliCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()
        self.path = Path(self.ok("new", "specification", "Lifecycle Doc", "--dir", str(self.ws)).strip())

    def test_transitions(self) -> None:
        code, out, _ = self.cli("status", str(self.path), "active")
        self.assertEqual(code, 1)
        self.assertIn("E_LIFECYCLE", out)
        self.ok("status", str(self.path), "proposed")
        somnus = self.payload(self.path)
        self.assertEqual((somnus["lifecycle"]["status"], somnus["revision"]), ("proposed", 2))
        self.assertIn("updated_at", somnus["time"])
        code, out, _ = self.cli("status", str(self.path), "archived")
        self.assertEqual(code, 1)
        self.assertIn("requires --reason", out)
        self.ok("status", str(self.path), "archived", "--reason", "abandoned")
        self.assertEqual(self.payload(self.path)["lifecycle"]["reason"], "abandoned")

    def test_superseded_requires_replacement(self) -> None:
        self.ok("status", str(self.path), "proposed")
        self.ok("status", str(self.path), "active")
        self.assertEqual(self.cli("status", str(self.path), "superseded")[0], 1)
        repl = "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a"
        self.ok("status", str(self.path), "superseded", "--replacement", repl)
        self.assertEqual(self.payload(self.path)["lifecycle"]["replacement_refs"], [{"ref": repl}])

    def test_bump_resolves_revision_conflict(self) -> None:
        text = self.path.read_text(encoding="utf-8")
        self.path.write_text(text + "\nEdited without a bump.\n", encoding="utf-8", newline="")
        code, _, _ = self.cli("index")
        self.assertEqual(code, 1)
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT kind FROM open_conflicts").fetchall(), [("revision",)])
        self.ok("bump", str(self.path), "--reason", "edited body")
        self.assertEqual(self.payload(self.path)["revision"], 2)
        with self.db() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM open_conflicts").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT max(revision) FROM revisions").fetchone()[0], 2)

    def test_fork(self) -> None:
        out = self.ok("fork", str(self.path), "--title", "Lifecycle Doc V2")
        child_path = Path(out.strip())
        parent, child = self.payload(self.path), self.payload(child_path)
        self.assertNotEqual(parent["id"], child["id"])
        self.assertEqual(child["revision"], 1)
        rel = child["knowledge"]["relations"][-1]
        self.assertEqual((rel["predicate"], rel["object"]["ref"], rel["object"]["revision"]),
                         ("derived_from", parent["id"], 1))
        self.assertEqual(child["authority"]["scopes"][0]["target_ref"], child["id"])
        self.ok("check", str(child_path), "--level", "semantic")
        self.assertEqual(self.cli("fork", str(self.path), "--title", "Lifecycle Doc V2")[0], 1)

    def test_ls_q_stale(self) -> None:
        self.ok("index")
        out = self.ok("ls", "--type", "specification", "--tsv")
        self.assertEqual(len(out.strip().splitlines()), 2)
        self.assertIn("events", self.ok("q", "--tables"))
        self.assertIn("Lifecycle Doc", self.ok("q", "SELECT title FROM artifacts"))
        self.assertEqual(self.cli("q", "DELETE FROM events")[0], 2)
        self.path.unlink()
        self.ok("index")
        self.assertIn("missing-file", self.ok("stale"))


class TestRegions(CliCase):
    def test_sync_registers_markers(self) -> None:
        path = Path(self.ok("new", "specification", "Regions Doc", "--dir", str(self.ws)).strip())
        text = path.read_text(encoding="utf-8")
        path.write_text(text + "\n<!-- somnus:region:begin r-core -->\n\nBody.\n\n<!-- somnus:region:end r-core -->\n",
                        encoding="utf-8", newline="")
        code, out, err = self.cli("check", str(path))
        self.assertEqual(code, 0, out)
        self.assertIn("W_REGION_UNREGISTERED", out)
        out = self.ok("regions", str(path))
        self.assertIn("r-core", out)
        diff = self.ok("regions", str(path), "--sync")
        self.assertIn("r-core", diff)
        self.ok("regions", str(path), "--sync", "--write")
        somnus = self.payload(path)
        self.assertEqual(somnus["knowledge"]["regions"][0]["selector"], {"kind": "marker", "name": "r-core"})
        self.assertEqual(somnus["revision"], 2)
        code, out, _ = self.cli("check", str(path))
        self.assertNotIn("W_REGION_UNREGISTERED", out)

    def test_crossing_markers_refuse_sync(self) -> None:
        path = Path(self.ok("new", "report", "Crossed", "--dir", str(self.ws)).strip())
        text = path.read_text(encoding="utf-8")
        path.write_text(text + "\n<!-- somnus:region:begin r-a -->\n\n<!-- somnus:region:begin r-b -->\n\n"
                        "<!-- somnus:region:end r-a -->\n\n<!-- somnus:region:end r-b -->\n",
                        encoding="utf-8", newline="")
        self.assertEqual(self.cli("regions", str(path), "--sync", "--write")[0], 1)


class TestMigrate(CliCase):
    def test_migrate_v01_examples(self) -> None:
        for name in ("specification-example.md", "submatter-example.md", "benchmark-example.md"):
            with self.subTest(name=name):
                path = self.ws / name
                shutil.copyfile(V01 / name, path)
                before = path.read_bytes()
                diff = self.ok("migrate", str(path))
                self.assertIn('+  schema: "somnus://metadata/core/2.0.0"', diff)
                self.assertEqual(path.read_bytes(), before)
                self.ok("migrate", str(path), "--write")
                somnus = self.payload(path)
                self.assertEqual(somnus["revision"], 1)
                self.assertEqual(somnus["authority"]["standing"], "candidate")
                ext = somnus["extensions"]["somnus-migration"]
                self.assertEqual(ext["schema"], "somnus://metadata/extension/migration-v0.1/1.0.0")
                self.ok("check", str(path))
                self.assertIn("already", self.cli("migrate", str(path))[2])

    def test_directives_become_regions(self) -> None:
        path = self.ws / "spec.md"
        shutil.copyfile(V01 / "specification-example.md", path)
        self.ok("migrate", str(path), "--write")
        somnus = self.payload(path)
        ids = [r["id"] for r in somnus["knowledge"]["regions"]]
        self.assertIn("r-invariant-019d3e34", ids)
        self.assertEqual(len(ids), 4)
        text = path.read_text(encoding="utf-8")
        self.assertNotIn(":::submatter", text)
        self.assertIn("<!-- somnus:region:begin r-invariant-019d3e34 -->", text)
        self.assertEqual(somnus["id"], "urn:somnus:artifact:019d3e2f-9900-7fac-ad6e-4a50a7a72b34")
        preds = sorted(r["predicate"] for r in somnus["knowledge"]["relations"])
        self.assertEqual(preds, ["cites", "derived_from", "supersedes"])
        data = somnus["extensions"]["somnus-migration"]["data"]
        self.assertIn("provenance", data)
        self.assertIn("specification", data)
        self.assertTrue(data["lifecycle"]["is_canonical"])

    def test_missing_id_refused(self) -> None:
        path = self.write("bad.md", '---\ntitle: "No id"\n---\nBody\n')
        before = path.read_bytes()
        self.assertEqual(self.cli("migrate", str(path), "--write")[0], 1)
        self.assertEqual(path.read_bytes(), before)


class TestSet(CliCase):
    def setUp(self) -> None:
        super().setUp()
        self.init()
        self.path = Path(self.ok("new", "specification", "Set Doc", "--dir", str(self.ws)).strip())

    def events(self) -> list[tuple]:
        with self.db() as conn:
            return conn.execute("SELECT action, revision, detail FROM events WHERE action = 'set'").fetchall()

    def test_fields_change_in_one_revision(self) -> None:
        self.ok("set", str(self.path), "title=Set Doc Renamed", "classification.tags=b, a, b",
                "somnus.summary=Short summary.", "classification.role=working", "--reason", "tidy")
        somnus = self.payload(self.path)
        self.assertEqual(somnus["revision"], 2)
        self.assertEqual(somnus["title"], "Set Doc Renamed")
        self.assertEqual(somnus["classification"]["tags"], ["b", "a"])
        self.assertEqual(somnus["summary"], "Short summary.")
        self.assertEqual(somnus["classification"]["role"], "working")
        self.assertIn("updated_at", somnus["time"])
        self.assertEqual(self.events(), [("set", 2, "set title, classification.tags, summary, "
                                                    "classification.role: tidy")])
        self.ok("check", str(self.path), "--level", "semantic")

    def test_value_may_contain_equals_and_empty_optional_removes(self) -> None:
        self.ok("set", str(self.path), "summary=a=b")
        self.assertEqual(self.payload(self.path)["summary"], "a=b")
        self.ok("set", str(self.path), "summary=")
        somnus = self.payload(self.path)
        self.assertNotIn("summary", somnus)
        self.assertEqual(somnus["revision"], 3)

    def test_unchanged_values_write_nothing(self) -> None:
        before = self.path.read_bytes()
        code, _, err = self.cli("set", str(self.path), "title=Set Doc")
        self.assertEqual(code, 0)
        self.assertIn("no changes", err)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.events(), [])

    def test_refusals_leave_file_untouched(self) -> None:
        before = self.path.read_bytes()
        for argv, code in ((("id=urn:somnus:artifact:x",), 2), (("lifecycle.status=active",), 2),
                           (("title",), 2), (("title=A", "title=B"), 2),
                           (("classification.type=nonsense",), 1), (("title=",), 1)):
            got, out, _ = self.cli("set", str(self.path), *argv)
            self.assertEqual(got, code, f"{argv}: {out}")
        self.assertIn("E_SCHEMA", self.cli("set", str(self.path), "classification.type=nonsense")[1])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.events(), [])

    def test_comment_carrier_host_bytes_preserved(self) -> None:
        src = '#!/usr/bin/env python\n"""Data loader utility."""\nprint(1)\n'
        tool = self.write("tool.py", src)
        self.ok("stamp", str(tool), "--write")
        self.ok("set", str(tool), "title=Loader", "classification.tags=io")
        text = tool.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("#!/usr/bin/env python\n"))
        self.assertTrue(text.endswith('"""Data loader utility."""\nprint(1)\n'))
        self.assertEqual(self.payload(tool)["title"], "Loader")
        compile(text, str(tool), "exec")


if __name__ == "__main__":
    unittest.main()
