"""Terminal UI: pure widget logic, key decoding, frame diffing, and the header form model."""

from __future__ import annotations

import contextlib
import shutil
import tempfile
import unittest
from pathlib import Path

from somnus import CORE_SCHEMA, ids
from somnus import document as D
from somnus.commands._common import load_valid
from somnus.output import Diagnostic, SomnusError
from somnus.tui import app as A
from somnus.tui import form as F
from somnus.tui import term as T
from somnus.tui.widgets import (REVERSE, ListView, Picker, TextInput, fit, split, split_widths,
                                strip_styles, visible_width)


def payload(**overrides) -> dict:
    """Minimal valid core payload."""
    aid = ids.new_artifact_urn()
    p = {
        "schema": CORE_SCHEMA,
        "id": aid,
        "revision": 1,
        "title": "Fixture",
        "classification": {"category": "engineering", "type": "specification", "role": "normative",
                           "scope": "component", "tags": ["fixture"]},
        "lifecycle": {"status": "draft"},
        "authority": {"standing": "candidate", "scopes": [{"target_ref": aid, "aspects": ["content"]}]},
        "time": {},
        "knowledge": {"coverage": "artifact", "subjects": [aid]},
        "access": {"visibility": "internal", "allowed_uses": ["archive", "search", "reason"]},
        "ingestion": {"disposition": "candidate", "body_role": "specification"},
    }
    p.update(overrides)
    return p


def field(path: str) -> F.Field:
    return next(f for f in F.FIELDS if f.path == path)


def plain(lines: list[str]) -> list[str]:
    return [strip_styles(line) for line in lines]


class FitTest(unittest.TestCase):
    def test_pads_and_clips(self) -> None:
        self.assertEqual(fit("abc", 5), "abc  ")
        self.assertEqual(fit("abcdef", 4), "abcd")
        self.assertEqual(fit("x", 0), "")

    def test_styles_do_not_count_and_are_reset(self) -> None:
        out = fit(REVERSE + "abcdef", 3)
        self.assertEqual(strip_styles(out), "abc")
        self.assertTrue(out.endswith("\x1b[0m"))

    def test_control_characters_become_spaces(self) -> None:
        self.assertEqual(fit("a\tb\x1bc", 5), "a b c")

    def test_wide_characters(self) -> None:
        self.assertEqual(visible_width("\u4e2d\u6587"), 4)
        self.assertEqual(fit("\u4e2d\u6587", 3), "\u4e2d ")


class ListViewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.items = [f"item-{i:02d}" for i in range(30)]
        self.lv = ListView(self.items)

    def test_navigation(self) -> None:
        self.assertEqual(self.lv.selected, "item-00")
        self.assertTrue(self.lv.handle("down"))
        self.assertEqual(self.lv.selected, "item-01")
        self.lv.handle("up")
        self.lv.handle("up")
        self.assertEqual(self.lv.selected, "item-00")
        self.lv.handle("end")
        self.assertEqual(self.lv.selected, "item-29")
        self.lv.handle("down")
        self.assertEqual(self.lv.selected, "item-29")
        self.lv.handle("home")
        self.assertEqual(self.lv.selected, "item-00")

    def test_paging_uses_rendered_height(self) -> None:
        self.lv.render(20, 5)
        self.lv.handle("pgdn")
        self.assertEqual(self.lv.selected, "item-05")
        self.lv.handle("pgup")
        self.assertEqual(self.lv.selected, "item-00")

    def test_unhandled_keys(self) -> None:
        self.assertFalse(self.lv.handle("q"))
        self.assertFalse(self.lv.handle("esc"))
        self.assertFalse(self.lv.handle("enter"))

    def test_render_scrolls_and_clips(self) -> None:
        self.lv.handle("end")
        rows = self.lv.render(6, 4)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(visible_width(r) == 6 for r in rows))
        self.assertEqual(plain(rows), ["item-2", "item-2", "item-2", "item-2"])
        self.assertTrue(rows[-1].startswith(REVERSE))
        wide = plain(self.lv.render(10, 4))
        self.assertEqual(wide[-1], "item-29   ")

    def test_filter(self) -> None:
        lv = ListView(["Alpha", "beta", "Gamma", "alphabet"])
        self.assertTrue(lv.handle("/"))
        for ch in "ALP":
            lv.handle(ch)
        self.assertEqual(lv.visible, ["Alpha", "alphabet"])
        self.assertTrue(lv.handle("q"))
        self.assertEqual(lv.visible, [])
        lv.handle("backspace")
        self.assertEqual(lv.query, "ALP")
        lv.handle("enter")
        self.assertFalse(lv.searching)
        rows = plain(lv.render(20, 4))
        self.assertTrue(rows[-1].startswith("/ALP"))
        lv.handle("down")
        self.assertEqual(lv.selected, "alphabet")
        self.assertTrue(lv.handle("esc"))
        self.assertEqual(lv.query, "")
        self.assertEqual(lv.selected, "alphabet")
        self.assertFalse(lv.handle("esc"))

    def test_filter_with_no_matches(self) -> None:
        lv = ListView(["one", "two"])
        lv.handle("/")
        lv.handle("z")
        self.assertIsNone(lv.selected)
        rows = plain(lv.render(15, 3))
        self.assertEqual(rows[0].strip(), "(no matches)")

    def test_search_escape_clears_query(self) -> None:
        lv = ListView(["one", "two"])
        lv.handle("/")
        lv.handle("t")
        self.assertTrue(lv.handle("esc"))
        self.assertFalse(lv.searching)
        self.assertEqual(lv.visible, ["one", "two"])

    def test_match_text_and_set_items(self) -> None:
        rows = [("id1", "Title A", "/x/a.md"), ("id2", "Title B", "/x/b.md")]
        lv = ListView(rows, lambda r: r[1], match_text=lambda r: " ".join(r))
        lv.handle("/")
        for ch in "b.md":
            lv.handle(ch)
        self.assertEqual(lv.selected, rows[1])
        lv.set_items(rows + [("id3", "Other", "/x/c.md")])
        self.assertEqual(lv.visible, [rows[1]])


class PickerTest(unittest.TestCase):
    def test_choose(self) -> None:
        p = Picker("Role", ["normative", "informative", "working"], "informative")
        self.assertEqual(p.index, 1)
        p.handle("down")
        p.handle("enter")
        self.assertTrue(p.done)
        self.assertFalse(p.cancelled)
        self.assertEqual(p.value, "working")

    def test_cancel(self) -> None:
        p = Picker("Role", ["a", "b"], "b")
        p.handle("up")
        p.handle("esc")
        self.assertTrue(p.done)
        self.assertTrue(p.cancelled)
        self.assertIsNone(p.value)

    def test_letter_jump_and_render(self) -> None:
        p = Picker("Scope", ["ecosystem", "fleet", "module", "component"], "fleet")
        p.handle("m")
        self.assertEqual(p.choices[p.index], "module")
        rows = plain(p.render(30, 6))
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0].strip(), "Scope:")
        self.assertIn("(*) fleet", "".join(rows))
        self.assertIn("( ) module", "".join(rows))


class TextInputTest(unittest.TestCase):
    def test_editing(self) -> None:
        t = TextInput("Title", "helo")
        t.handle("left")
        t.handle("l")
        self.assertEqual(t.value, "hello")
        t.handle("home")
        t.handle("delete")
        self.assertEqual(t.value, "ello")
        t.handle("end")
        t.handle("backspace")
        self.assertEqual(t.value, "ell")
        t.handle("home")
        t.handle("backspace")
        self.assertEqual(t.value, "ell")
        t.handle("right")
        t.handle("X")
        self.assertEqual((t.value, t.cursor), ("eXll", 2))
        self.assertFalse(t.handle("up"))
        t.handle("enter")
        self.assertTrue(t.done)
        self.assertFalse(t.cancelled)

    def test_cancel(self) -> None:
        t = TextInput("Title", "x")
        t.handle("esc")
        self.assertTrue(t.done and t.cancelled)

    def test_render_scrolls_to_cursor(self) -> None:
        t = TextInput("T", "abcdefghij")
        row = t.render(8)[0]
        self.assertEqual(visible_width(row), 8)
        self.assertEqual(strip_styles(row), "T: ghij ")
        t.handle("home")
        self.assertEqual(strip_styles(t.render(8)[0]), "T: abcde")


class SplitTest(unittest.TestCase):
    def test_columns(self) -> None:
        left_w, right_w = split_widths(23, 0.5)
        self.assertEqual(left_w + right_w + 3, 23)
        rows = split(["left", "longer-left-text"], ["r"], 23, 0.5)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(visible_width(r) == 23 for r in rows))
        self.assertEqual(rows[0], "left" + " " * 6 + " \u2502 " + "r" + " " * 9)
        self.assertTrue(rows[1].startswith("longer-lef"))

    def test_tiny_width(self) -> None:
        rows = split(["a"], ["b"], 2)
        self.assertEqual(visible_width(rows[0]), 3)


class KeyDecodingTest(unittest.TestCase):
    def test_plain_keys(self) -> None:
        self.assertEqual(T.decode_char("\r"), "enter")
        self.assertEqual(T.decode_char("\n"), "enter")
        self.assertEqual(T.decode_char("\x1b"), "esc")
        self.assertEqual(T.decode_char("\x08"), "backspace")
        self.assertEqual(T.decode_char("\x7f"), "backspace")
        self.assertEqual(T.decode_char("\t"), "tab")
        self.assertEqual(T.decode_char("a"), "a")

    def test_windows_prefix(self) -> None:
        expected = {"H": "up", "P": "down", "K": "left", "M": "right", "G": "home", "O": "end",
                    "I": "pgup", "Q": "pgdn", "S": "delete"}
        for ch, name in expected.items():
            self.assertEqual(T.decode_windows_special(ch), name)
        self.assertEqual(T.decode_windows_special(";"), "")

    def test_escape_sequences(self) -> None:
        cases = {"[A": "up", "[B": "down", "[C": "right", "[D": "left", "[H": "home", "[F": "end",
                 "OH": "home", "OF": "end", "OA": "up", "[1~": "home", "[4~": "end", "[3~": "delete",
                 "[5~": "pgup", "[6~": "pgdn", "[1;5C": "right", "[3;2~": "delete"}
        for seq, name in cases.items():
            self.assertEqual(T.decode_escape(seq), name, seq)
        self.assertEqual(T.decode_escape("[Z"), "")
        self.assertEqual(T.decode_escape("x"), "")

    def test_sequence_final(self) -> None:
        self.assertTrue(T.is_sequence_final("A"))
        self.assertTrue(T.is_sequence_final("~"))
        self.assertFalse(T.is_sequence_final("5"))
        self.assertFalse(T.is_sequence_final(";"))


class FrameTest(unittest.TestCase):
    def test_only_changed_rows(self) -> None:
        frame, updates = T.frame_updates([], ["a", "b"], 6, 3)
        self.assertEqual(frame, ["a    ", "b    ", "     "])
        self.assertEqual([r for r, _ in updates], [0, 1, 2])
        frame2, updates2 = T.frame_updates(frame, ["a", "c"], 6, 3)
        self.assertEqual(updates2, [(1, "c    ")])
        _, updates3 = T.frame_updates(frame2, ["a", "c"], 6, 3)
        self.assertEqual(updates3, [])

    def test_clips_long_rows(self) -> None:
        frame, _ = T.frame_updates([], ["abcdefgh"], 5, 1)
        self.assertEqual(frame, ["abcd"])


class FakeScreen:
    def size(self) -> tuple[int, int]:
        return 80, 24

    def draw(self, lines) -> None:
        self.last = list(lines)

    def read_key(self) -> str:
        raise EOFError

    def invalidate(self) -> None:
        pass

    @contextlib.contextmanager
    def suspended(self):
        yield


class FakeCtx:
    def __init__(self) -> None:
        self.records = []

    def record(self, *args, **kwargs) -> None:
        self.records.append((args, kwargs))


class FormModelTest(unittest.TestCase):
    def test_valid_and_clean_initially(self) -> None:
        form = F.FormModel(payload())
        self.assertEqual(form.errors, [])
        self.assertEqual(form.status(), "valid")
        self.assertFalse(form.dirty)

    def test_apply_text_and_choice(self) -> None:
        form = F.FormModel(payload())
        form.apply(field("title"), "  New title ")
        form.apply(field("classification.role"), "working")
        self.assertEqual(form.payload["title"], "New title")
        self.assertEqual(form.payload["classification"]["role"], "working")
        self.assertTrue(form.dirty)
        self.assertEqual(form.original["title"], "Fixture")
        with self.assertRaises(ValueError):
            form.apply(field("classification.role"), "bogus")

    def test_optional_empty_removes_key(self) -> None:
        form = F.FormModel(payload(summary="old"))
        form.apply(field("summary"), "   ")
        self.assertNotIn("summary", form.payload)
        form.apply(field("purpose"), "")
        self.assertNotIn("purpose", form.payload)
        self.assertEqual(form.errors, [])

    def test_tags(self) -> None:
        form = F.FormModel(payload())
        self.assertEqual(form.text(field("classification.tags")), "fixture")
        form.apply(field("classification.tags"), "a, b,, a ,c")
        self.assertEqual(form.payload["classification"]["tags"], ["a", "b", "c"])
        self.assertEqual(F.parse_tags(" , "), [])

    def test_validation_errors_and_revert(self) -> None:
        form = F.FormModel(payload())
        form.apply(field("title"), "")
        self.assertTrue(form.errors)
        self.assertTrue(form.status().startswith(f"{len(form.errors)} error"))
        form.revert()
        self.assertFalse(form.dirty)
        self.assertEqual(form.errors, [])

    def test_custom_validator_status(self) -> None:
        diag = Diagnostic("-", 0, 0, "error", "E_X", "somnus.title", "bad title")
        form = F.FormModel({"title": "x"}, validator=lambda p: [diag, diag])
        self.assertEqual(form.status(), "2 errors: somnus.title: bad title")

    def test_readonly_rows(self) -> None:
        p = payload()
        rows = dict(F.FormModel(p).readonly_rows())
        self.assertEqual(rows["ID"], p["id"])
        self.assertEqual(rows["Status"], "draft")
        self.assertIn("aspects=content", rows["Authority scopes"])

    def test_path_helpers(self) -> None:
        p: dict = {}
        F.set_path(p, "a.b.c", 1)
        self.assertEqual(F.get_path(p, "a.b.c"), 1)
        self.assertIsNone(F.get_path(p, "a.x"))
        F.remove_path(p, "a.b.c")
        self.assertEqual(p, {"a": {"b": {}}})
        F.remove_path(p, "missing.key")


class EditorScreenTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "doc.md"
        text = "---\n" + D.canonical_yaml({"somnus": payload()}) + "---\n# Fixture\n\nBody text.\n"
        self.path.write_text(text, encoding="utf-8")
        self.ctx = FakeCtx()
        self.screen = FakeScreen()
        self.editor = A.EditorScreen(self.ctx, self.screen, load_valid(self.path))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def type_text(self, text: str) -> None:
        for ch in text:
            self.editor.handle(ch)

    def test_edit_title_and_save(self) -> None:
        ed = self.editor
        ed.handle("enter")
        self.assertIsInstance(ed.overlay, TextInput)
        ed.handle("end")
        self.type_text(" two")
        ed.handle("enter")
        self.assertIsNone(ed.overlay)
        self.assertTrue(ed.form.dirty)
        self.assertEqual(ed.form.payload["title"], "Fixture two")
        ed.handle("s")
        self.assertEqual(ed.form.value("revision"), 2, ed.message)
        self.assertFalse(ed.form.dirty)
        self.assertEqual(load_valid(self.path).payload["title"], "Fixture two")
        self.assertIn("Body text.", self.path.read_text(encoding="utf-8"))
        args, kwargs = self.ctx.records[0]
        self.assertEqual(args[0], "edit")
        self.assertEqual(args[3], 2)
        self.assertEqual(kwargs["resolve"], ("revision",))

    def test_picker_and_invalid_save_blocked(self) -> None:
        ed = self.editor
        for _ in range(5):
            ed.handle("down")
        ed.handle("enter")
        self.assertIsInstance(ed.overlay, Picker)
        ed.handle("down")
        ed.handle("enter")
        self.assertEqual(ed.form.value("classification.role"), "informative")
        ed.handle("up")
        ed.handle("up")
        ed.handle("up")
        ed.handle("up")
        ed.handle("up")
        ed.handle("enter")
        for _ in range(len("Fixture")):
            ed.handle("backspace")
        ed.handle("enter")
        self.assertTrue(ed.form.errors)
        ed.handle("s")
        self.assertTrue(ed.message.startswith("not saved"))
        self.assertEqual(load_valid(self.path).payload["revision"], 1)

    def test_quit_confirmation(self) -> None:
        ed = self.editor
        self.assertFalse(ed.handle("q"))
        ed.handle("enter")
        self.type_text("!")
        ed.handle("enter")
        self.assertTrue(ed.handle("q"))
        self.assertTrue(ed.confirming)
        self.assertTrue(ed.handle("n"))
        self.assertFalse(ed.confirming)
        self.assertTrue(ed.handle("esc"))
        self.assertFalse(ed.handle("y"))

    def test_save_without_changes(self) -> None:
        self.editor.handle("s")
        self.assertEqual(self.editor.message, "no changes to save")
        self.assertEqual(self.ctx.records, [])

    def test_render_fits_screen(self) -> None:
        rows = self.editor.render(79, 24)
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(visible_width(r) == 79 for r in rows))
        text = "\n".join(plain(rows))
        self.assertIn("somnus status", text)
        self.assertIn("valid", text)
        self.editor.run()


class AppHelpersTest(unittest.TestCase):
    def test_editor_command(self) -> None:
        self.assertEqual(A.editor_command({"EDITOR": "code --wait"}), ["code", "--wait"])
        self.assertEqual(A.editor_command({"VISUAL": "nano"}), ["nano"])
        self.assertEqual(len(A.editor_command({})), 1)

    def test_browser_render_and_keys(self) -> None:
        rows = [("urn:1", "Alpha", "specification", "draft", "candidate", 1, "/tmp/a.md"),
                ("urn:2", None, "report", "active", "accepted", 3, "/tmp/b.md")]
        browser = A.BrowserScreen(FakeCtx(), FakeScreen(), rows)
        frame = plain(browser.render(79, 10))
        self.assertEqual(len(frame), 10)
        self.assertIn("Alpha", frame[1])
        self.assertIn("ID: urn:1", frame[1])
        self.assertTrue(browser.handle("down"))
        self.assertIn("(untitled)", A.render_row(browser.list.selected))
        self.assertFalse(browser.handle("q"))
        detail = A.detail_lines(rows[0], 12)
        self.assertTrue(all(len(line) <= 12 for line in detail))

    def test_first_message(self) -> None:
        exc = SomnusError([Diagnostic("p", 1, 1, "error", "E", "somnus.title", "bad")])
        self.assertEqual(A.first_message(exc), "somnus.title: bad")
        self.assertEqual(A.first_message(SomnusError("plain")), "plain")


if __name__ == "__main__":
    unittest.main()
