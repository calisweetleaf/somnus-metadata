"""Carriers: envelope extraction, insertion, preambles, host preservation (SPEC section 17)."""

from __future__ import annotations

import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path

from somnus import carriers
from somnus import document as D
from somnus.carriers.sidecar import SIDECAR, binding_issues, primary_target
from somnus.output import SomnusError

CORE = "somnus://metadata/core/2.0.0"
PAYLOAD = {"schema": CORE, "title": "Carrier test", "classification": {"tags": ["a", "b"]}}

# (file name, unmanaged host text, expected envelope kind)
HOSTS = [
    ("plain.md", "# Title\n\nBody text.\n", "frontmatter-full"),
    ("hosted.md", "---\ntitle: Host title\nlayout: post\n---\nBody\n", "frontmatter"),
    ("tool.py", "import os\n\nprint(os.name)\n", "python"),
    ("run.sh", "#!/bin/sh\necho hi\n", "shell"),
    ("mod.ps1", "#Requires -Version 7\nWrite-Host hi\n", "powershell"),
    ("analysis.R", "x <- 1\n", "r"),
    ("pyproject.toml", '[project]\nname = "x"\nversion = "1.0"\n', "toml"),
    ("conf.yaml", "key: value\nlist:\n  - 1\n  - two\n", "yaml"),
    ("paper.tex", "% !TeX program = lualatex\n\\documentclass{article}\n", "tex"),
    ("app.js", "#!/usr/bin/env node\nconsole.log(1);\n", "js"),
    ("main.rs", "fn main() {}\n", "slash"),
    ("query.sql", "SELECT 1;\n", "sql"),
    ("style.css", '@charset "utf-8";\nbody { color: red; }\n', "css"),
    ("data.xml", '<?xml version="1.0" encoding="utf-8"?>\n<root/>\n', "xml"),
    ("icon.svg", '<?xml version="1.0"?>\n<!DOCTYPE svg>\n<svg/>\n', "xml"),
    ("page.html", "<!DOCTYPE html>\n<html></html>\n", "xml"),
]


def strip_envelope(text: str, doc: D.Document) -> str:
    lines = text.splitlines(keepends=True)
    env = doc.envelope
    return "".join(lines[: env.start] + lines[env.end:])


def embed(path: str, host: str) -> tuple[str, D.Document]:
    """Render PAYLOAD into an unmanaged host; return the new text and its reparsed document."""
    doc = D.from_text(Path(path), host)
    text = doc.render(PAYLOAD)
    return text, D.from_text(Path(path), text)


class TestDetection(unittest.TestCase):
    def test_extension_table(self) -> None:
        # SPEC section 17 table: extension -> envelope syntax.
        prefixes = {
            "# ": [".py", ".pyw", ".sh", ".bash", ".zsh", ".ps1", ".psm1", ".psd1", ".toml", ".yaml", ".yml",
                   ".r", ".R"],
            "% ": [".tex", ".sty", ".cls", ".ltx"],
            "// ": [".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".rs", ".c", ".h", ".cc", ".cpp", ".hpp", ".go",
                    ".java", ".kt", ".swift", ".cs"],
            "-- ": [".sql"],
        }
        for prefix, exts in prefixes.items():
            for ext in exts:
                with self.subTest(ext=ext):
                    carrier = carriers.for_path(Path("f" + ext))
                    self.assertIsNotNone(carrier)
                    self.assertEqual(carrier.prefix, prefix)
        for ext in (".css", ".scss", ".less"):
            with self.subTest(ext=ext):
                self.assertEqual(carriers.for_path(Path("f" + ext)).opener, "/* somnus:metadata:v2")
        for ext in (".html", ".htm", ".xhtml", ".xml", ".svg"):
            with self.subTest(ext=ext):
                self.assertEqual(carriers.for_path(Path("f" + ext)).opener, "<!-- somnus:metadata:v2")
        for ext in (".md", ".markdown", ".mdx"):
            with self.subTest(ext=ext):
                self.assertEqual(carriers.for_path(Path("f" + ext)).name, "markdown")

    def test_sidecar_required(self) -> None:
        for name in ("state.json", "doc.pdf", "img.png", "nb.ipynb", "noext", "x.somnus.yaml", "a.json.somnus.yaml"):
            with self.subTest(name=name):
                self.assertIsNone(carriers.for_path(Path(name)))

    def test_sidecar_paths(self) -> None:
        self.assertEqual(carriers.sidecar_for(Path("d/state.json")), Path("d/state.json.somnus.yaml"))
        self.assertEqual(carriers.host_for(Path("d/state.json.somnus.yaml")), Path("d/state.json"))
        self.assertTrue(carriers.is_sidecar_path(Path("conf.yaml.somnus.yaml")))
        self.assertFalse(carriers.is_sidecar_path(Path("conf.yaml")))


class TestRoundTrip(unittest.TestCase):
    def test_insert_then_extract(self) -> None:
        for name, host, kind in HOSTS:
            with self.subTest(host=name):
                text, doc = embed(name, host)
                self.assertEqual(doc.issues, [])
                self.assertIsNotNone(doc.envelope)
                self.assertEqual(doc.envelope.kind, kind)
                self.assertEqual(doc.payload, PAYLOAD)

    def test_host_content_unchanged(self) -> None:
        for name, host, _ in HOSTS:
            with self.subTest(host=name):
                text, doc = embed(name, host)
                self.assertEqual(doc.body_lines(), host.rstrip("\n").split("\n"))
                if doc.envelope.kind != "frontmatter":
                    self.assertEqual(strip_envelope(text, doc), host)

    def test_frontmatter_host_keys_preserved(self) -> None:
        text, doc = embed("hosted.md", "---\ntitle: Host title  # comment\nlayout: post\n---\nBody\n")
        self.assertEqual(doc.issues, [])
        lines = text.split("\n")
        self.assertEqual(lines[:3], ["---", "title: Host title  # comment", "layout: post"])
        self.assertEqual(doc.body_lines(), ["---", "title: Host title  # comment", "layout: post", "---", "Body"])

    def test_replace_existing_envelope(self) -> None:
        for name, host, _ in HOSTS:
            with self.subTest(host=name):
                text, doc = embed(name, host)
                body_before = doc.body_lines()
                updated = doc.render(dict(PAYLOAD, title="Second"))
                again = D.from_text(Path(name), updated)
                self.assertEqual(again.payload["title"], "Second")
                self.assertEqual(again.body_lines(), body_before)
                self.assertEqual(again.envelope.start, doc.envelope.start)

    def test_html_comment_style_in_markdown(self) -> None:
        doc = D.from_text(Path("x.md"), "# Title\n\nBody\n")
        text = doc.render(PAYLOAD, style="html-comment")
        self.assertTrue(text.startswith("<!-- somnus:metadata:v2\nsomnus:\n"))
        again = D.from_text(Path("x.md"), text)
        self.assertEqual(again.envelope.kind, "html-comment")
        self.assertEqual(again.payload, PAYLOAD)
        self.assertEqual(strip_envelope(text, again), "# Title\n\nBody\n")

    def test_html_comment_after_host_frontmatter(self) -> None:
        doc = D.from_text(Path("x.md"), "---\nlayout: post\n---\nBody\n")
        text = doc.render(PAYLOAD, style="html-comment")
        self.assertTrue(text.startswith("---\nlayout: post\n---\n<!-- somnus:metadata:v2\n"))
        self.assertEqual(D.from_text(Path("x.md"), text).payload, PAYLOAD)

    def test_equal_model_across_carriers(self) -> None:
        # SPEC section 21 fixture 1.
        models = []
        for name, host in [("a.md", "Body\n"), ("a.tex", "\\section{x}\n"), ("a.yaml", "k: 1\n"),
                           ("a.toml", "k = 1\n")]:
            models.append(embed(name, host)[1].payload)
        side = D.from_text(Path("a.json"), D.new_sidecar_text(PAYLOAD))
        models.append(side.payload)
        for model in models:
            self.assertEqual(model, PAYLOAD)

    def test_line_comment_payload_details(self) -> None:
        text = ("# somnus:metadata:v2\n# somnus:\n#\n#   title: \"T\"\n#   tags:\n#     - \"x\"\n# somnus:end\n"
                "x = 1\n")
        doc = D.from_text(Path("x.py"), text)
        self.assertEqual(doc.issues, [])
        self.assertEqual(doc.envelope.payload_lines, ["somnus:", "", "  title: \"T\"", "  tags:", "    - \"x\""])
        self.assertEqual(doc.payload, {"title": "T", "tags": ["x"]})

    def test_line_comment_foreign_line_is_envelope_error(self) -> None:
        text = "# somnus:metadata:v2\n# somnus:\nx = 1\n# somnus:end\n"
        self.assertIn("E_ENVELOPE", [i.code for i in D.from_text(Path("x.py"), text).issues])

    def test_line_comment_missing_space_is_envelope_error(self) -> None:
        text = "# somnus:metadata:v2\n#somnus:\n# somnus:end\n"
        self.assertIn("E_ENVELOPE", [i.code for i in D.from_text(Path("x.py"), text).issues])


class TestPreambles(unittest.TestCase):
    def lines(self, name: str, host: str) -> list[str]:
        return embed(name, host)[0].split("\n")

    def test_python_shebang_and_cookie(self) -> None:
        # SPEC section 21 fixture 3.
        lines = self.lines("x.py", "#!/usr/bin/env python3\n# -*- coding: latin-1 -*-\nx = 1\n")
        self.assertEqual(lines[:3], ["#!/usr/bin/env python3", "# -*- coding: latin-1 -*-", "# somnus:metadata:v2"])

    def test_python_cookie_on_line_one(self) -> None:
        lines = self.lines("x.py", "# vim: set fileencoding=utf-8 :\nx = 1\n")
        self.assertEqual(lines[:2], ["# vim: set fileencoding=utf-8 :", "# somnus:metadata:v2"])

    def test_python_cookie_on_line_two_after_comment(self) -> None:
        lines = self.lines("x.py", "# header comment\n# coding=utf-8\nx = 1\n")
        self.assertEqual(lines[:3], ["# header comment", "# coding=utf-8", "# somnus:metadata:v2"])

    def test_python_without_preamble_inserts_at_top(self) -> None:
        self.assertEqual(self.lines("x.py", "x = 1\n")[0], "# somnus:metadata:v2")

    def test_shell_shebang(self) -> None:
        for name in ("run.sh", "run.bash", "run.zsh", "a.R", "a.js"):
            with self.subTest(name=name):
                lines = self.lines(name, "#!/usr/bin/env tool\nbody\n")
                self.assertEqual(lines[0], "#!/usr/bin/env tool")
                self.assertTrue(lines[1].endswith("somnus:metadata:v2"))

    def test_powershell_requires(self) -> None:
        lines = self.lines("m.ps1", "#!/usr/bin/env pwsh\n#Requires -Version 7\n#requires -Modules X\nWrite-Host 1\n")
        self.assertEqual(lines[:4], ["#!/usr/bin/env pwsh", "#Requires -Version 7", "#requires -Modules X",
                                     "# somnus:metadata:v2"])

    def test_tex_magic_comments(self) -> None:
        lines = self.lines("p.tex", "% !TeX program = lualatex\n%!tex root = main.tex\n\\documentclass{article}\n")
        self.assertEqual(lines[:3], ["% !TeX program = lualatex", "%!tex root = main.tex", "% somnus:metadata:v2"])

    def test_css_charset(self) -> None:
        lines = self.lines("s.css", '@charset "utf-8";\nbody {}\n')
        self.assertEqual(lines[:2], ['@charset "utf-8";', "/* somnus:metadata:v2"])

    def test_xml_declaration_and_doctype(self) -> None:
        lines = self.lines("i.svg", '<?xml version="1.0"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN">\n<svg/>\n')
        self.assertEqual(lines[2], "<!-- somnus:metadata:v2")
        self.assertTrue(lines[0].startswith("<?xml"))
        self.assertTrue(lines[1].startswith("<!DOCTYPE"))

    def test_unsafe_placement_refused(self) -> None:
        for name, host in [
            ("d.xml", '<?xml version="1.0"\n  encoding="utf-8"?>\n<root/>\n'),
            ("d.html", "<!DOCTYPE html\n>\n<html/>\n"),
            ("s.css", "@charset \"utf-8\"; body {}\n"),
        ]:
            with self.subTest(name=name):
                with self.assertRaises(SomnusError) as cm:
                    D.from_text(Path(name), host).render(PAYLOAD)
                self.assertEqual(cm.exception.diagnostics[0].code, "E_HOST")


class TestHostDataTrees(unittest.TestCase):
    def test_toml_data_tree_unchanged(self) -> None:
        # SPEC section 21 fixture 2.
        host = '# existing comment\n[project]\nname = "x"\nkeywords = ["a", "b"]\n\n[tool.x]\nflag = true\n'
        text, doc = embed("pyproject.toml", host)
        self.assertEqual(tomllib.loads(text), tomllib.loads(host))
        self.assertEqual(doc.payload, PAYLOAD)

    def test_yaml_non_comment_lines_unchanged(self) -> None:
        host = "%YAML 1.2\n---\nkey: value\nlist:\n  - 1\n  - two  # trailing\nnested:\n  a: b\n"
        text, doc = embed("conf.yml", host)

        def data_lines(t: str) -> list[str]:
            return [ln for ln in t.split("\n") if not ln.lstrip().startswith("#")]

        self.assertEqual(data_lines(text), data_lines(host))
        self.assertEqual(doc.payload, PAYLOAD)


class TestEnvelopeErrors(unittest.TestCase):
    PY_ENV = '# somnus:metadata:v2\n# somnus:\n#   title: "T"\n# somnus:end\n'
    MD_HTML = '<!-- somnus:metadata:v2\nsomnus:\n  title: "T"\nsomnus:end -->\n'
    CSS_ENV = '/* somnus:metadata:v2\nsomnus:\n  title: "T"\nsomnus:end */\n'
    XML_ENV = '<!-- somnus:metadata:v2\nsomnus:\n  title: "T"\nsomnus:end -->\n'

    def issue_codes(self, name: str, text: str) -> list[str]:
        return [i.code for i in D.from_text(Path(name), text).issues]

    def test_duplicate_envelopes(self) -> None:
        for name, text in [
            ("x.py", self.PY_ENV + "\n" + self.PY_ENV + "x = 1\n"),
            ("x.md", "---\nsomnus:\n  title: \"T\"\n---\n\n" + self.MD_HTML),
            ("x.md", "---\nsomnus:\n  title: \"T\"\nsomnus:\n  title: \"U\"\n---\n"),
            ("x.md", "Body\n\n" + self.MD_HTML + "\n" + self.MD_HTML),
            ("x.css", self.CSS_ENV + self.CSS_ENV + "a {}\n"),
            ("x.xml", self.XML_ENV + self.XML_ENV + "<a/>\n"),
            ("x.sql", self.PY_ENV.replace("# ", "-- ") + self.PY_ENV.replace("# ", "-- ") + "SELECT 1;\n"),
        ]:
            with self.subTest(name=name, text=text[:30]):
                self.assertIn("E_ENVELOPE", self.issue_codes(name, text))

    def test_unclosed_envelopes(self) -> None:
        for name, text in [
            ("x.md", "---\nsomnus:\n  title: \"T\"\n"),
            ("x.md", "<!-- somnus:metadata:v2\nsomnus:\n"),
            ("x.py", "# somnus:metadata:v2\n# somnus:\n"),
            ("x.css", "/* somnus:metadata:v2\nsomnus:\n"),
            ("x.xml", "<!-- somnus:metadata:v2\nsomnus:\n"),
        ]:
            with self.subTest(name=name, text=text[:30]):
                self.assertIn("E_ENVELOPE", self.issue_codes(name, text))

    def test_forbidden_sequences_in_existing_envelopes(self) -> None:
        for name, text in [
            ("x.xml", '<!-- somnus:metadata:v2\nsomnus:\n  title: "a--b"\nsomnus:end -->\n'),
            ("x.html", '<!-- somnus:metadata:v2\nsomnus:\n  title: "a--b"\nsomnus:end -->\n'),
            ("x.md", '<!-- somnus:metadata:v2\nsomnus:\n  title: "a--b"\nsomnus:end -->\n'),
            ("x.css", '/* somnus:metadata:v2\nsomnus:\n  title: "a */ b"\nsomnus:end */\n'),
        ]:
            with self.subTest(name=name):
                self.assertIn("E_ENVELOPE", self.issue_codes(name, text))

    def test_forbidden_sequences_escaped_on_render(self) -> None:
        for name, host, value, forbidden in [
            ("x.xml", "<root/>\n", "a--b-->c", "--"),
            ("x.svg", "<svg/>\n", "---", "--"),
            ("x.css", "a {}\n", "a */ b", "*/"),
        ]:
            with self.subTest(name=name):
                text = D.from_text(Path(name), host).render(dict(PAYLOAD, title=value))
                doc = D.from_text(Path(name), text)
                payload_text = "\n".join(doc.envelope.payload_lines)
                self.assertNotIn(forbidden, payload_text)
                self.assertEqual(doc.issues, [])
                self.assertEqual(doc.payload["title"], value)

    def test_markdown_html_comment_escapes_dashes(self) -> None:
        doc = D.from_text(Path("x.md"), "Body\n")
        text = doc.render(dict(PAYLOAD, title="a--b"), style="html-comment")
        self.assertEqual(D.from_text(Path("x.md"), text).payload["title"], "a--b")

    def test_frontmatter_allows_dashes(self) -> None:
        text, doc = embed("x.md", "Body\n")
        updated = doc.render(dict(PAYLOAD, title="a--b"))
        self.assertEqual(D.from_text(Path("x.md"), updated).payload["title"], "a--b")


class TestInertLookalikes(unittest.TestCase):
    def test_after_code_is_inert(self) -> None:
        for name, text in [
            ("x.py", 'x = 1\n# somnus:metadata:v2\n# somnus:\n#   title: "T"\n# somnus:end\n'),
            ("x.py", 's = """\n# somnus:metadata:v2\n# somnus:\n#   title: "T"\n# somnus:end\n"""\n'),
            ("x.py", '"""Docstring."""\n# somnus:metadata:v2\n# somnus:\n#   title: "T"\n# somnus:end\n'),
            ("x.toml", 'a = 1\n# somnus:metadata:v2\n# somnus:\n#   title: "T"\n# somnus:end\n'),
            ("x.js", 'const s = `\n// somnus:metadata:v2\n// somnus:\n//   title: "T"\n// somnus:end\n`;\n'),
            ("x.css", 'a {}\n/* somnus:metadata:v2\nsomnus:\n  title: "T"\nsomnus:end */\n'),
            ("x.xml", '<root>\n<!-- somnus:metadata:v2\nsomnus:\n  title: "T"\nsomnus:end -->\n</root>\n'),
            ("x.md", 'Text\n\n```\n<!-- somnus:metadata:v2\nsomnus:\n  title: "T"\nsomnus:end -->\n```\n'),
            ("x.md", 'Text\n\n~~~~\n---\nsomnus:\n---\n<!-- somnus:metadata:v2\nsomnus:end -->\n~~~~\n'),
            ("x.md", 'Text\n\n    <!-- somnus:metadata:v2\n    somnus:end -->\n'),
            ("x.md", "Text\n---\nsomnus:\n  title: \"T\"\n---\n"),
        ]:
            with self.subTest(name=name, text=text[:24]):
                doc = D.from_text(Path(name), text)
                self.assertIsNone(doc.envelope)
                self.assertEqual(doc.issues, [])

    def test_comments_before_envelope_are_allowed(self) -> None:
        text = '# license header\n\n# somnus:metadata:v2\n# somnus:\n#   title: "T"\n# somnus:end\nx = 1\n'
        doc = D.from_text(Path("x.py"), text)
        self.assertEqual(doc.payload, {"title": "T"})
        self.assertEqual(doc.envelope.start, 2)

    def test_render_into_file_with_lookalike(self) -> None:
        host = 'x = 1\n# somnus:metadata:v2\n# somnus:\n#   title: "Fake"\n# somnus:end\n'
        text, doc = embed("x.py", host)
        self.assertEqual(doc.issues, [])
        self.assertEqual(doc.payload, PAYLOAD)
        self.assertEqual(strip_envelope(text, doc), host)


class TestSidecarCarrier(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_extract_whole_file(self) -> None:
        ext = SIDECAR.extract(["somnus:", '  title: "T"', "", ""])
        self.assertEqual(ext.issues, [])
        self.assertEqual((ext.envelope.start, ext.envelope.end), (0, 2))
        self.assertEqual(ext.envelope.payload, 'somnus:\n  title: "T"\n')

    def test_empty_sidecar(self) -> None:
        self.assertEqual([i.code for i in SIDECAR.extract([]).issues], ["E_ENVELOPE"])
        self.assertEqual([i.code for i in SIDECAR.extract(["", ""]).issues], ["E_ENVELOPE"])

    def test_render_replaces_everything(self) -> None:
        splice = SIDECAR.render(["old", "lines"], 'somnus:\n  title: "N"\n', None)
        self.assertEqual((splice.start, splice.end, splice.new_lines), (0, 2, ["somnus:", '  title: "N"']))

    def binding(self, **kw) -> dict:
        b = {"target": "state.json", "role": "primary", "required": True}
        b.update(kw)
        return {"bindings": [b]}

    def test_binding_contract(self) -> None:
        (self.tmp / "state.json").write_bytes(b"{}")
        side = self.tmp / "state.json.somnus.yaml"
        self.assertEqual(binding_issues(self.binding(), side), [])
        self.assertEqual(primary_target(self.binding(), side), (self.tmp / "state.json").resolve())
        self.assertTrue(binding_issues({}, side))
        self.assertTrue(binding_issues({"bindings": []}, side))
        self.assertTrue(binding_issues(self.binding(required=False), side))
        self.assertTrue(binding_issues(self.binding(target="missing.json"), side))
        two = self.binding()
        two["bindings"].append({"target": "state.json", "role": "primary", "required": True})
        self.assertTrue(binding_issues(two, side))
        (self.tmp / "other.json").write_bytes(b"{}")
        self.assertTrue(binding_issues(self.binding(target="other.json"), side))

    def test_reference_object_target_accepted(self) -> None:
        side = self.tmp / "state.json.somnus.yaml"
        payload = self.binding(target={"ref": "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a"})
        self.assertEqual(binding_issues(payload, side), [])

    def test_attachment_bindings_alongside_primary(self) -> None:
        (self.tmp / "state.json").write_bytes(b"{}")
        payload = self.binding()
        payload["bindings"].append({"target": "extra.bin", "role": "attachment", "required": False})
        self.assertEqual(binding_issues(payload, self.tmp / "state.json.somnus.yaml"), [])


if __name__ == "__main__":
    unittest.main()
