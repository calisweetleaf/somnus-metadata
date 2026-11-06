# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1af7c-0a93-7715-b17d-9eed021e4f98"
#   revision: 4
#   title: "Carrier routing beyond extensions, JSON-tree carriers, and inline migration (SPEC §17, D20)"
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
#       - target_ref: "urn:somnus:artifact:01a1af7c-0a93-7715-b17d-9eed021e4f98"
#         aspects: ["content"]
#   time:
#     updated_at: "2026-11-06T23:17:28+00:00"
#   names:
#     slug: "carrier-routing-beyond-extensions-json-tree-carriers-and-inline-migration-spec-1"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1af7c-0a93-7715-b17d-9eed021e4f98"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Carrier routing beyond extensions, JSON-tree carriers, and inline migration (SPEC §17, D20)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from somnus import carriers
from somnus import document as D
from somnus.carriers.jsonhost import JSON_KEY, NOTEBOOK, object_members
from somnus.model.validate import validate
from somnus.output import SomnusError

from test_commands import CliCase

NOTEBOOK_TEXT = """{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": ["print('hello world')"]
  }
 ],
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "name": "python3"}
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
"""


class TempDirCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def put(self, name: str, text: str) -> Path:
        path = self.dir / name
        path.write_text(text, encoding="utf-8", newline="")
        return path


class TestFilenameRouting(TempDirCase):
    def test_exact_filenames(self) -> None:
        for name, expected in (("CODEOWNERS", "hash"), ("MANIFEST.in", "hash"), ("Makefile", "hash"),
                               ("Dockerfile", "dockerfile"), (".gitignore", "hash"), (".env", "hash"),
                               ("Gemfile", "hash"), ("tsconfig.json", "jsonc"), ("CMakeLists.txt", "hash"),
                               ("Pipfile", "toml"), ("BUILD.bazel", "python"),
                               (".importlinter", "hash"), (".pre-commit-config.yaml", "yaml"),
                               (".ruff.toml", "toml")):
            with self.subTest(name=name):
                self.assertEqual(carriers.carrier_name_for(Path(name), sniff=False), expected)

    def test_patterns(self) -> None:
        for name, expected in (("requirements-dev.txt", "hash"), ("requirements.txt", "hash"),
                               (".env.local", "hash"), ("Dockerfile.prod", "dockerfile"),
                               ("tsconfig.build.json", "jsonc")):
            with self.subTest(name=name):
                self.assertEqual(carriers.carrier_name_for(Path(name), sniff=False), expected)

    def test_new_extensions(self) -> None:
        for name, expected in (("a.rb", "hash"), ("a.tf", "hash"), ("a.ini", "hash"), ("a.lua", "lua"),
                               ("a.hs", "lua"), ("a.zig", "slash"), ("a.vue", "xml"), ("a.jsonc", "jsonc"),
                               ("a.json5", "jsonc"), ("a.ipynb", "ipynb"), ("a.pyi", "python")):
            with self.subTest(name=name):
                self.assertEqual(carriers.carrier_name_for(Path(name), sniff=False), expected)

    def test_plain_text_and_binaries_stay_sidecar(self) -> None:
        for name in ("notes.txt", "a.png", "a.pdf", "a.log", "config.h.in", "data.csv"):
            with self.subTest(name=name):
                self.assertIsNone(carriers.carrier_name_for(Path(name), sniff=False))

    def test_sidecar_files_are_never_hosts(self) -> None:
        self.assertIsNone(carriers.carrier_name_for(Path("Dockerfile.somnus.yaml")))


class TestShebang(TempDirCase):
    def test_interpreters(self) -> None:
        for line, expected in (("#!/usr/bin/env python3", "python"), ("#!/bin/bash", "shell"),
                               ("#!/usr/bin/env -S node --no-warnings", "js"), ("#!/usr/bin/perl -w", "hash"),
                               ("#!/usr/bin/env python3.12", "python"), ("#!/usr/bin/env unknownthing", None)):
            with self.subTest(line=line):
                self.assertEqual(carriers.shebang_carrier((line + "\n").encode()), expected)

    def test_extensionless_script_on_disk(self) -> None:
        path = self.put("tool", "#!/usr/bin/env bash\necho hi\n")
        self.assertEqual(carriers.carrier_name_for(path), "shell")
        self.assertIsNone(carriers.carrier_name_for(self.put("blob", "no shebang\n")))

    def test_stamp_keeps_shebang_first(self) -> None:
        path = self.put("tool", "#!/usr/bin/env bash\necho hi\n")
        doc = D.load(path)
        text = doc.render({"schema": "x"})
        self.assertTrue(text.startswith("#!/usr/bin/env bash\n# somnus:metadata:v2\n"))


class TestDockerfile(TempDirCase):
    def test_parser_directives_stay_first(self) -> None:
        path = self.put("Dockerfile", "# syntax=docker/dockerfile:1\n# escape=`\nFROM python:3.12\n")
        text = D.load(path).render({"schema": "x"})
        lines = text.split("\n")
        self.assertEqual(lines[:3], ["# syntax=docker/dockerfile:1", "# escape=`", "# somnus:metadata:v2"])
        self.assertIn("FROM python:3.12", lines)


class TestJsonKey(TempDirCase):
    def test_detection_requires_leading_key(self) -> None:
        self.assertTrue(carriers.json_key_present(b'{\n  "$somnus": {}}'))
        self.assertFalse(carriers.json_key_present(b'{"a": 1, "$somnus": {}}'))
        self.assertFalse(carriers.json_key_present(b"[1, 2]"))

    def test_insert_preserves_members_and_indent(self) -> None:
        path = self.put("package.json", '{\n    "name": "x",\n    "v": [1, 2]\n}\n')
        doc = D.as_carrier(path, JSON_KEY)
        self.assertIsNone(doc.envelope)
        text = doc.render({"schema": "s", "id": "i"})
        data = json.loads(text)
        self.assertEqual(list(data), ["$somnus", "name", "v"])
        self.assertTrue(text.startswith('{\n    "$somnus": {\n        "schema": "s"'))
        self.assertTrue(text.endswith('    "name": "x",\n    "v": [1, 2]\n}\n'))

    def test_replace_touches_only_the_value(self) -> None:
        path = self.put("a.json", '{"$somnus": {"schema": "old"}, "keep": {"z": 1,  "a": 2}}\n')
        doc = D.load(path)
        self.assertEqual(doc.carrier.name, "json")
        self.assertEqual(doc.payload, {"schema": "old"})
        text = doc.render({"schema": "new"})
        self.assertEqual(text, '{"$somnus": {"schema":"new"}, "keep": {"z": 1,  "a": 2}}\n')

    def test_host_view_excludes_payload(self) -> None:
        path = self.put("a.json", '{"$somnus": {"schema": "old"}, "k": 1}\n')
        doc = D.load(path)
        self.assertNotIn("$somnus", "\n".join(doc.body_lines()))
        before = doc.body_digest()
        path.write_text('{"$somnus": {"schema": "new"}, "k": 1}\n', encoding="utf-8")
        self.assertEqual(D.load(path).body_digest(), before)

    def test_object_members_errors(self) -> None:
        with self.assertRaises(ValueError):
            object_members("[1]", 0)


class TestNotebook(TempDirCase):
    def test_round_trip(self) -> None:
        path = self.put("nb.ipynb", NOTEBOOK_TEXT)
        doc = D.load(path)
        self.assertIs(doc.carrier, NOTEBOOK)
        self.assertIsNone(doc.envelope)
        text = doc.render({"schema": "s", "title": "T"})
        nb = json.loads(text)
        self.assertEqual(nb["metadata"]["somnus"], {"schema": "s", "title": "T"})
        self.assertEqual(nb["metadata"]["kernelspec"]["name"], "python3")
        self.assertEqual(nb["cells"], json.loads(NOTEBOOK_TEXT)["cells"])
        path.write_text(text, encoding="utf-8")
        again = D.load(path)
        self.assertEqual(again.payload["title"], "T")
        self.assertIn("print('hello world')", "\n".join(again.body_lines()))

    def test_without_metadata_refuses(self) -> None:
        path = self.put("nb.ipynb", '{"cells": []}\n')
        with self.assertRaises(SomnusError):
            D.load(path).render({"schema": "s"})


class TestStampAndInline(CliCase):
    def test_stamp_new_hosts_inline(self) -> None:
        self.init()
        files = {
            "CODEOWNERS": "* @owner\n",
            "Dockerfile": "FROM x\n",
            "tool": "#!/usr/bin/env python3\nprint(1)\n",
            "conf.jsonc": "{\n  // c\n  \"a\": 1\n}\n",
            "nb.ipynb": NOTEBOOK_TEXT,
        }
        for name, text in files.items():
            self.write(name, text)
        self.ok("stamp", "--write", *[str(self.ws / n) for n in files])
        for name in files:
            with self.subTest(name=name):
                self.assertFalse((self.ws / (name + ".somnus.yaml")).exists())
                doc = D.load(self.ws / name)
                self.assertFalse(doc.is_sidecar)
                self.assertFalse([d for d in validate(doc, "core") if d.is_error])
        self.assertEqual(D.load(self.ws / "CODEOWNERS").payload["classification"]["type"], "configuration")
        self.assertEqual(D.load(self.ws / "tool").payload["classification"]["type"], "source-code")

    def test_plain_json_needs_opt_in(self) -> None:
        self.init()
        self.write("a.json", '{"k": 1}\n')
        self.ok("stamp", "--write", str(self.ws / "a.json"))
        self.assertTrue((self.ws / "a.json.somnus.yaml").exists())
        self.write("b.json", '{"k": 1}\n')
        self.ok("stamp", "--write", "--inline", str(self.ws / "b.json"))
        self.assertFalse((self.ws / "b.json.somnus.yaml").exists())
        self.assertEqual(json.loads((self.ws / "b.json").read_text())["k"], 1)
        self.write("c.json", "[1, 2]\n")
        self.ok("stamp", "--write", "--inline", str(self.ws / "c.json"))
        self.assertTrue((self.ws / "c.json.somnus.yaml").exists())

    def test_migrate_inline_moves_sidecar(self) -> None:
        self.init()
        host = self.write("CODEOWNERS", "* @owner\n")
        sidecar = self.ws / "CODEOWNERS.somnus.yaml"
        # Build a legacy sidecar the way <=2.1 stamped extensionless hosts.
        from somnus.commands._common import inferred_payload
        from somnus import config as C

        legacy = inferred_payload(C.load(self.ws), host, [])
        legacy["bindings"] = [{"target": "CODEOWNERS", "role": "primary", "required": True}]
        sidecar.write_text(D.new_sidecar_text(legacy), encoding="utf-8")
        self.ok("index", str(self.ws))
        code, out, _ = self.cli("migrate", "--inline", str(self.ws))
        self.assertEqual(code, 0)
        self.assertIn("sidecar removed", out)
        self.assertTrue(sidecar.exists())
        self.ok("migrate", "--inline", "--write", str(self.ws))
        self.assertFalse(sidecar.exists())
        doc = D.load(host)
        self.assertEqual(doc.payload["id"], legacy["id"])
        self.assertEqual(doc.payload["revision"], 2)
        self.assertNotIn("bindings", doc.payload)
        self.assertTrue(host.read_text().endswith("* @owner\n"))
        _, out, err = self.cli("q", "--conflicts")
        self.assertNotIn("revision ", out)

    def test_migrate_inline_keeps_true_sidecars(self) -> None:
        self.init()
        self.write("data.csv", "a,b\n")
        self.ok("stamp", "--write", str(self.ws / "data.csv"))
        self.ok("migrate", "--inline", "--write", str(self.ws))
        self.assertTrue((self.ws / "data.csv.somnus.yaml").exists())


if __name__ == "__main__":
    unittest.main()
