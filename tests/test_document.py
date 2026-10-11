"""Document loading, byte-preserving atomic saves, digests, positions (SPEC section 16.3, section 17, section 18.3)."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from somnus import document as D
from somnus.output import SomnusError

A = "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a"
CORE = "somnus://metadata/core/2.0.0"

HEADER = (
    "---\n"
    "somnus:\n"
    f"  schema: \"{CORE}\"\n"
    f"  id: \"{A}\"\n"
    "  revision: 1\n"
    "  title: \"Doc\"\n"
    "---\n"
)
BODY = "\n# Heading\n\nBody line with trailing spaces   \n\t tabbed line\n"


def crlf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", "\r\n")


def frontmatter_body(raw: bytes) -> bytes:
    """Bytes after the closing frontmatter delimiter."""
    lines = raw.splitlines(keepends=True)
    closes = [i for i, ln in enumerate(lines) if ln.rstrip(b"\r\n") == b"---"]
    return b"".join(lines[closes[1] + 1:])


class DocTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name: str, data: bytes | str) -> Path:
        path = self.tmp / name
        path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return path


class TestLoadSave(DocTestCase):
    def test_round_trip(self) -> None:
        path = self.write("doc.md", HEADER + BODY)
        doc = D.load(path)
        self.assertEqual(doc.issues, [])
        self.assertEqual(doc.payload, {"schema": CORE, "id": A, "revision": 1, "title": "Doc"})
        payload = doc.copy_payload()
        payload["title"] = "Renamed"
        doc.save(payload)
        again = D.load(path)
        self.assertEqual(again.payload["title"], "Renamed")
        self.assertEqual(again.issues, [])
        self.assertEqual(frontmatter_body(path.read_bytes()), BODY.encode("utf-8"))

    def test_save_is_idempotent_for_canonical_input(self) -> None:
        path = self.write("doc.md", HEADER + BODY)
        before = path.read_bytes()
        doc = D.load(path)
        doc.save(doc.copy_payload())
        self.assertEqual(path.read_bytes(), before)

    def test_copy_payload_is_deep(self) -> None:
        doc = D.from_text(Path("x.md"), HEADER + BODY)
        copy = doc.copy_payload()
        copy["title"] = "changed"
        self.assertEqual(doc.payload["title"], "Doc")

    def test_crlf_preserved(self) -> None:
        path = self.write("doc.md", crlf(HEADER + BODY))
        doc = D.load(path)
        self.assertEqual(doc.newline, "\r\n")
        payload = doc.copy_payload()
        payload["summary"] = "Added"
        doc.save(payload)
        raw = path.read_bytes()
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"))
        self.assertEqual(frontmatter_body(raw), crlf(BODY).encode("utf-8"))
        self.assertEqual(D.load(path).payload["summary"], "Added")

    def test_lf_used_for_unmanaged_lf_file(self) -> None:
        path = self.write("doc.md", "# Title\n\nBody\n")
        doc = D.load(path)
        self.assertIsNone(doc.envelope)
        doc.save({"schema": CORE, "title": "T"})
        raw = path.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertTrue(raw.endswith(b"---\n# Title\n\nBody\n"))

    def test_new_sidecar_written_with_lf(self) -> None:
        host = self.write("data.json", b'{"a": 1}\r\n')
        doc = D.load(host)
        self.assertTrue(doc.is_sidecar)
        self.assertIsNone(doc.envelope)
        doc.save({"schema": CORE, "title": "T"})
        sidecar = self.tmp / "data.json.somnus.yaml"
        raw = sidecar.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(host.read_bytes(), b'{"a": 1}\r\n')
        self.assertNotIn("\r", D.new_sidecar_text({"title": "T"}))

    def test_bom_accepted_and_not_emitted(self) -> None:
        path = self.write("doc.md", b"\xef\xbb\xbf" + (HEADER + BODY).encode("utf-8"))
        doc = D.load(path)
        self.assertTrue(doc.had_bom)
        self.assertEqual(doc.issues, [])
        self.assertEqual(doc.payload["title"], "Doc")
        doc.save(doc.copy_payload())
        raw = path.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(frontmatter_body(raw), BODY.encode("utf-8"))

    def test_bom_in_from_text(self) -> None:
        doc = D.from_text(Path("x.md"), "\ufeff" + HEADER + BODY)
        self.assertTrue(doc.had_bom)
        self.assertEqual(doc.payload["id"], A)

    def test_body_without_trailing_newline_preserved(self) -> None:
        path = self.write("doc.md", HEADER + "last line, no newline")
        doc = D.load(path)
        payload = doc.copy_payload()
        payload["title"] = "X"
        doc.save(payload)
        self.assertEqual(frontmatter_body(path.read_bytes()), b"last line, no newline")

    def test_hash_host_bytes_outside_envelope_identical(self) -> None:
        original = "#!/usr/bin/env python\nimport os  \n\n\nprint(os.name)\r\n"
        path = self.write("tool.py", original)
        doc = D.load(path)
        doc.save({"schema": CORE, "title": "T"})
        text = path.read_bytes().decode("utf-8")
        lines = text.splitlines(keepends=True)
        start = next(i for i, ln in enumerate(lines) if ln.startswith("# somnus:metadata:v2"))
        end = next(i for i, ln in enumerate(lines) if ln.startswith("# somnus:end"))
        self.assertEqual("".join(lines[:start] + lines[end + 1:]), original)

    def test_yaml_errors_recorded_with_file_position(self) -> None:
        doc = D.from_text(Path("x.md"), "---\nsomnus:\n  title: plain\n---\n")
        self.assertEqual([(d.code, d.line, d.col) for d in doc.issues], [("E_YAML", 3, 10)])
        self.assertIsNone(doc.payload)

    def test_invalid_utf8_raises_e_io(self) -> None:
        path = self.write("bad.md", b"---\nsomnus:\n  title: \"\xff\"\n---\n")
        with self.assertRaises(SomnusError) as cm:
            D.load(path)
        self.assertEqual([d.code for d in cm.exception.diagnostics], ["E_IO"])

    def test_missing_file_raises_e_io(self) -> None:
        with self.assertRaises(SomnusError) as cm:
            D.load(self.tmp / "missing.md")
        self.assertEqual(cm.exception.diagnostics[0].code, "E_IO")
        self.assertEqual(cm.exception.exit_code, 2)


class TestAtomicWrite(DocTestCase):
    def test_no_temp_files_left(self) -> None:
        target = self.tmp / "out.txt"
        D.atomic_write(target, "one\n")
        D.atomic_write(target, "two\r\n")
        self.assertEqual(os.listdir(self.tmp), ["out.txt"])
        self.assertEqual(target.read_bytes(), b"two\r\n")

    def test_writes_utf8_without_newline_translation(self) -> None:
        target = self.tmp / "u.txt"
        D.atomic_write(target, "a\nb\r\n\u00e9")
        self.assertEqual(target.read_bytes(), "a\nb\r\n\u00e9".encode("utf-8"))

    def test_failure_removes_temp_file(self) -> None:
        blocker = self.tmp / "dir"
        blocker.mkdir()
        (blocker / "keep").write_bytes(b"x")
        with self.assertRaises(OSError):
            D.atomic_write(blocker, "data")
        self.assertEqual(sorted(os.listdir(self.tmp)), ["dir"])


class TestDigests(DocTestCase):
    def test_body_digest_lf_normalized(self) -> None:
        lf = D.from_text(Path("x.md"), HEADER + BODY)
        cr = D.from_text(Path("x.md"), crlf(HEADER + BODY))
        self.assertEqual(lf.body_digest(), cr.body_digest())

    def test_body_digest_ignores_envelope(self) -> None:
        a = D.from_text(Path("x.md"), HEADER + BODY)
        b = D.from_text(Path("x.md"), HEADER.replace('"Doc"', '"Other"') + BODY)
        self.assertEqual(a.body_digest(), b.body_digest())

    def test_body_digest_detects_body_change(self) -> None:
        a = D.from_text(Path("x.md"), HEADER + BODY)
        b = D.from_text(Path("x.md"), HEADER + BODY + "more\n")
        self.assertNotEqual(a.body_digest(), b.body_digest())

    def test_body_digest_is_sha256_of_outside_bytes(self) -> None:
        doc = D.from_text(Path("x.md"), HEADER + BODY)
        self.assertEqual(doc.body_digest(), hashlib.sha256(BODY.encode("utf-8")).hexdigest())

    def test_sidecar_body_digest_lf_normalized(self) -> None:
        self.write("a.json", b'{\r\n"a": 1\r\n}\r\n')
        self.write("b.json", b'{\n"a": 1\n}\n')
        side = 'somnus:\n  title: "T"\n'
        self.write("a.json.somnus.yaml", side)
        self.write("b.json.somnus.yaml", side)
        a = D.load(self.tmp / "a.json")
        b = D.load(self.tmp / "b.json")
        self.assertEqual(a.body_digest(), b.body_digest())
        self.assertEqual(a.body_digest(), hashlib.sha256(b'{\n"a": 1\n}\n').hexdigest())

    def test_payload_digest_stable_across_formatting(self) -> None:
        canonical = D.from_text(Path("x.md"), HEADER + BODY)
        messy = D.from_text(Path("x.md"), (
            "---\nsomnus:\n  # comment\n  title: 'Doc'\n  revision: 1\n"
            f"  id: '{A}'\n  schema: \"{CORE}\"\n---\n" + BODY
        ))
        self.assertEqual(messy.issues, [])
        self.assertEqual(canonical.payload_digest(), messy.payload_digest())
        expected = hashlib.sha256(D.canonical_yaml(canonical.data).encode("utf-8")).hexdigest()
        self.assertEqual(canonical.payload_digest(), expected)

    def test_payload_digest_changes_with_payload(self) -> None:
        a = D.from_text(Path("x.md"), HEADER + BODY)
        b = D.from_text(Path("x.md"), HEADER.replace("revision: 1", "revision: 2") + BODY)
        self.assertNotEqual(a.payload_digest(), b.payload_digest())

    def test_payload_digest_ignores_body_and_carrier(self) -> None:
        md = D.from_text(Path("x.md"), HEADER + BODY)
        md2 = D.from_text(Path("x.md"), HEADER + "different body\n")
        prefixed = "".join("# " + ln + "\n" for ln in md.envelope.payload_lines)
        py = D.from_text(Path("x.py"), "# somnus:metadata:v2\n" + prefixed + "# somnus:end\nx = 1\n")
        self.assertEqual(py.issues, [])
        self.assertEqual(md.payload_digest(), md2.payload_digest())
        self.assertEqual(md.payload_digest(), py.payload_digest())


class TestPositions(DocTestCase):
    def test_frontmatter_positions(self) -> None:
        doc = D.from_text(Path("x.md"), HEADER + BODY)
        self.assertEqual(doc.pos(("somnus",)), (2, 1))
        self.assertEqual(doc.pos(("somnus", "title")), (6, 3))
        self.assertEqual(doc.pos(("somnus", "title", "missing")), (6, 3))
        self.assertEqual(doc.pos(("somnus", "revision")), (5, 3))

    def test_frontmatter_with_host_keys(self) -> None:
        text = "---\ntitle: host\nother: 1\nsomnus:\n  title: \"T\"\n---\nbody\n"
        doc = D.from_text(Path("x.md"), text)
        self.assertEqual(doc.issues, [])
        self.assertEqual(doc.pos(("somnus", "title")), (5, 3))

    def test_line_comment_positions_include_prefix(self) -> None:
        text = "# somnus:metadata:v2\n# somnus:\n#   title: \"T\"\n# somnus:end\nx = 1\n"
        doc = D.from_text(Path("x.py"), text)
        self.assertEqual(doc.pos(("somnus", "title")), (3, 5))

    def test_diag_uses_field_path(self) -> None:
        doc = D.from_text(Path("x.md"), HEADER + BODY)
        d = doc.diag(("somnus", "title"), "E_SCHEMA", "msg")
        self.assertEqual((d.line, d.col, d.field, d.code, d.severity), (6, 3, "somnus.title", "E_SCHEMA", "error"))

    def test_no_envelope_position(self) -> None:
        self.assertEqual(D.from_text(Path("x.md"), "plain\n").pos(("somnus", "x")), (1, 1))

    def test_field_name(self) -> None:
        self.assertEqual(D.field_name(()), "-")
        self.assertEqual(D.field_name(("somnus", "knowledge", "claims", 0, "region_ref")),
                         "somnus.knowledge.claims[0].region_ref")


class TestSidecar(DocTestCase):
    SIDE = (
        "somnus:\n"
        "  title: \"State\"\n"
        "  bindings:\n"
        "    - target: \"state.json\"\n"
        "      role: \"primary\"\n"
        "      required: true\n"
    )

    def test_host_loaded_through_sidecar(self) -> None:
        host = self.write("state.json", b'{"a": 1}\n')
        side = self.write("state.json.somnus.yaml", self.SIDE)
        doc = D.load(host)
        self.assertTrue(doc.is_sidecar)
        self.assertEqual(doc.path, host)
        self.assertEqual(doc.meta_path, side)
        self.assertEqual(doc.payload["title"], "State")
        self.assertEqual(doc.host_bytes, b'{"a": 1}\n')
        self.assertEqual(doc.body_lines(), [])
        self.assertEqual(doc.issues, [])

    def test_sidecar_path_loads_same_document(self) -> None:
        host = self.write("state.json", b"{}\n")
        side = self.write("state.json.somnus.yaml", self.SIDE)
        doc = D.load(side)
        self.assertTrue(doc.is_sidecar)
        self.assertEqual(doc.path, host)
        self.assertEqual(doc.payload["title"], "State")

    def test_embedded_host_prefers_envelope_but_sidecar_conflicts(self) -> None:
        self.write("doc.md", HEADER + BODY)
        self.write("doc.md.somnus.yaml", self.SIDE)
        doc = D.load(self.tmp / "doc.md")
        self.assertIn("E_ENVELOPE", [d.code for d in doc.issues])

    def test_embedded_host_without_envelope_uses_sidecar(self) -> None:
        self.write("notes.md", "# Just notes\n")
        self.write("notes.md.somnus.yaml", self.SIDE)
        doc = D.load(self.tmp / "notes.md")
        self.assertTrue(doc.is_sidecar)
        self.assertEqual(doc.payload["title"], "State")

    def test_sidecar_save_leaves_host_untouched(self) -> None:
        host = self.write("state.json", b'{"a": 1}')
        self.write("state.json.somnus.yaml", self.SIDE)
        doc = D.load(host)
        payload = doc.copy_payload()
        payload["title"] = "New"
        doc.save(payload)
        self.assertEqual(host.read_bytes(), b'{"a": 1}')
        self.assertEqual(D.load(host).payload["title"], "New")


if __name__ == "__main__":
    unittest.main()
