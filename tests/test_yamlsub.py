"""Restricted YAML subset: strict parser, lenient mode, spans, canonical serializer (SPEC section 16)."""

from __future__ import annotations

import unittest

from somnus import yamlsub
from somnus.yamlsub import YAMLError, dumps, loads, parse

CANONICAL = (
    "somnus:\n"
    "  schema: \"somnus://metadata/core/2.0.0\"\n"
    "  revision: 1\n"
    "  ratio: 0.5\n"
    "  negative: -3\n"
    "  flag: true\n"
    "  off: false\n"
    "  tags: [\"a\", \"b\"]\n"
    "  items:\n"
    "    - id: \"one\"\n"
    "      n: 2\n"
    "    - id: \"two\"\n"
    "      nested:\n"
    "        deep: \"x\"\n"
    "  empty_list: []\n"
    "  empty_map: {}\n"
)

CANONICAL_DATA = {
    "somnus": {
        "schema": "somnus://metadata/core/2.0.0",
        "revision": 1,
        "ratio": 0.5,
        "negative": -3,
        "flag": True,
        "off": False,
        "tags": ["a", "b"],
        "items": [{"id": "one", "n": 2}, {"id": "two", "nested": {"deep": "x"}}],
        "empty_list": [],
        "empty_map": {},
    }
}


class TestStrictAccepts(unittest.TestCase):
    def test_canonical_subset_parses(self) -> None:
        self.assertEqual(loads(CANONICAL), CANONICAL_DATA)

    def test_single_quoted_strings(self) -> None:
        self.assertEqual(loads("a: 'it''s'\n"), {"a": "it's"})

    def test_single_quoted_backslash_is_literal(self) -> None:
        self.assertEqual(loads("a: 'x\\ny'\n"), {"a": "x\\ny"})

    def test_empty_quoted_string_is_a_string(self) -> None:
        self.assertEqual(loads('a: ""\n'), {"a": ""})

    def test_flow_mapping_is_accepted(self) -> None:
        # SPEC section 16.1 allows "block or flow sequences and mappings".
        self.assertEqual(loads('a: {b: 1, "c": "d"}\n'), {"a": {"b": 1, "c": "d"}})

    def test_nested_flow_collections(self) -> None:
        self.assertEqual(loads('a: [[1, 2], {b: ["c"]}]\n'), {"a": [[1, 2], {"b": ["c"]}]})

    def test_block_sequence_of_scalars(self) -> None:
        self.assertEqual(loads('a:\n  - "x"\n  - 2\n'), {"a": ["x", 2]})

    def test_block_sequence_at_key_indent(self) -> None:
        self.assertEqual(loads('a:\n- "x"\n- "y"\n'), {"a": ["x", "y"]})

    def test_quoted_keys(self) -> None:
        self.assertEqual(loads('"a b": 1\n\'c\': 2\n'), {"a b": 1, "c": 2})

    def test_comments_and_blank_lines_are_ignored(self) -> None:
        text = '# leading\n\na: "x"  # trailing\n\n  # indented comment\nb: ["y"] # after flow\n# end\n'
        self.assertEqual(loads(text), {"a": "x", "b": ["y"]})

    def test_hash_inside_quotes_is_not_a_comment(self) -> None:
        self.assertEqual(loads('a: "x # y"\nb: \'p # q\'\n'), {"a": "x # y", "b": "p # q"})

    def test_crlf_input(self) -> None:
        self.assertEqual(loads('a: "x"\r\nb:\r\n  c: 1\r\n'), {"a": "x", "b": {"c": 1}})

    def test_leading_bom_is_ignored(self) -> None:
        self.assertEqual(loads('\ufeffa: 1\n'), {"a": 1})


class TestBlockScalars(unittest.TestCase):
    def test_literal_clip(self) -> None:
        self.assertEqual(loads("a: |\n  one\n  two\nb: 1\n"), {"a": "one\ntwo\n", "b": 1})

    def test_literal_strip(self) -> None:
        self.assertEqual(loads("a: |-\n  one\n  two\n"), {"a": "one\ntwo"})

    def test_folded(self) -> None:
        self.assertEqual(loads("a: >\n  one\n  two\n\n  three\n"), {"a": "one two\nthree\n"})

    def test_literal_keep_with_following_key(self) -> None:
        self.assertEqual(loads("a: |+\n  x\n\nb: 1\n"), {"a": "x\n\n", "b": 1})

    def test_literal_keep_at_end_of_payload(self) -> None:
        # the empty split() element after the payload's final newline is not a kept blank line
        self.assertEqual(loads("a: |+\n  x\n"), {"a": "x\n"})

    def test_block_scalar_keeps_hash_lines(self) -> None:
        self.assertEqual(loads("a: |\n  # not a comment\n"), {"a": "# not a comment\n"})


class TestStrictRejects(unittest.TestCase):
    def assertRejected(self, cases: list[str], lenient: bool = False) -> None:
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(YAMLError):
                    loads(text, lenient=lenient)

    def test_plain_scalars_require_quoting(self) -> None:
        self.assertRejected([
            "a: hello\n", "a: hello world\n", "a: yes\n", "a: no\n", "a: NO\n", "a: on\n",
            "a: off\n", "a: True\n", "a: FALSE\n", "a: 2024-01-01\n", "a: 1.0.0\n", "a: 01\n",
            "a: +1\n", "a: 0x1F\n", "a: [x]\n", "a: {b: c}\n", "a:\n  - plain\n",
        ])

    def test_null_and_empty_values(self) -> None:
        self.assertRejected([
            "a: null\n", "a: Null\n", "a: NULL\n", "a: ~\n", "a:\n", "a:\nb: 1\n",
            "a: [1, ~]\n", "a: [null]\n", "a: {b: }\n", "a:\n  -\n", "a:\n  - null\n",
        ])

    def test_null_rejected_in_lenient_mode_too(self) -> None:
        self.assertRejected(["a: null\n", "a: ~\n", "a:\n"], lenient=True)

    def test_anchors_aliases_tags(self) -> None:
        self.assertRejected([
            'a: &x "v"\n', "a: *x\n", 'a: !!str "v"\n', 'a: !tag "v"\n', 'a: [&x "v"]\n',
            "a: [*x]\n", '&x a: "v"\n', '*x: "v"\n', '!t a: "v"\n',
        ])

    def test_anchors_rejected_in_lenient_mode(self) -> None:
        self.assertRejected(['a: &x "v"\n', "a: *x\n", 'a: !!str v\n'], lenient=True)

    def test_merge_keys(self) -> None:
        self.assertRejected(['<<: {"b": 1}\n', 'a:\n  <<: {"b": 1}\n', "a: {<<: 1}\n"])

    def test_tabs_in_indentation(self) -> None:
        self.assertRejected(["\ta: 1\n", "a:\n\tb: 1\n", "a:\n  \tb: 1\n", "a: |\n\tx\n"])

    def test_document_markers_and_directives(self) -> None:
        self.assertRejected([
            "---\na: 1\n", "a: 1\n---\n", "a: 1\n...\n", '--- a: 1\n', "%YAML 1.2\na: 1\n",
            "%TAG ! tag:x\na: 1\n",
        ])

    def test_duplicate_keys_at_any_depth(self) -> None:
        # SPEC section 21 fixture 4.
        self.assertRejected([
            "a: 1\na: 2\n",
            '"a": 1\na: 2\n',
            "a:\n  b: 1\n  b: 2\n",
            "a:\n  b:\n    c: 1\n    c: 1\n",
            "a:\n  - b: 1\n    b: 2\n",
            "a: {b: 1, b: 2}\n",
            'a: [{"b": 1, b: 2}]\n',
        ])

    def test_non_string_keys(self) -> None:
        self.assertRejected([
            '1: "x"\n', 'true: "x"\n', 'false: "x"\n', 'null: "x"\n', '~: "x"\n', "[a]: 1\n",
            "{a: 1}: 2\n", 'a: {1: "x"}\n', 'a: {true: "x"}\n',
        ])

    def test_integers_outside_safe_range(self) -> None:
        self.assertRejected(["a: 9007199254740992\n", "a: -9007199254740992\n", "a: [99999999999999999999]\n"])

    def test_non_finite_numbers(self) -> None:
        self.assertRejected(["a: .inf\n", "a: -.inf\n", "a: +.inf\n", "a: .nan\n", "a: .NaN\n", "a: 1e400\n"])

    def test_malformed_strings_and_flow(self) -> None:
        self.assertRejected([
            'a: "unterminated\n', "a: 'unterminated\n", 'a: "x" trailing\n', "a: [1, 2\n",
            "a: [1, ]\n", "a: [1,, 2]\n", "a: [1 2]\n", "a: {b: 1\n", "a: {b 1}\n",
            'a:"x"\n', 'a: "x"#c\n',
        ])

    def test_malformed_escapes(self) -> None:
        self.assertRejected(['a: "\\q"\n', 'a: "\\u12"\n', 'a: "\\u12G4"\n', 'a: "\\U00110000"\n', 'a: "\\x4"\n'])

    def test_structural_errors(self) -> None:
        self.assertRejected([
            "", "# only a comment\n", "  a: 1\n", "a:\n  b: 1\n   c: 2\n", "a: 1\n  b: 2\n",
            "a: 1\n- 2\n", "@a: 1\n", "a: @x\n", "a: `x`\n", "a: |x\n",
        ])


class TestScalars(unittest.TestCase):
    def test_quoted_values_remain_strings(self) -> None:
        # SPEC section 16.1 and section 21 fixture 5.
        for text, expected in [
            ('"NO"', "NO"), ('"on"', "on"), ('"1.0"', "1.0"), ('"2026-10-11"', "2026-10-11"),
            ('"2024-01-01"', "2024-01-01"), ("'true'", "true"), ('"null"', "null"), ('"~"', "~"),
            ('"123"', "123"), ("'1.2.3'", "1.2.3"), ('"yes"', "yes"),
        ]:
            with self.subTest(text=text):
                value = loads(f"a: {text}\n")["a"]
                self.assertIsInstance(value, str)
                self.assertEqual(value, expected)

    def test_quoted_values_in_flow_remain_strings(self) -> None:
        self.assertEqual(loads('a: ["NO", "on", "1.0", "2026-10-11"]\n'), {"a": ["NO", "on", "1.0", "2026-10-11"]})

    def test_integers(self) -> None:
        for text, expected in [("0", 0), ("-0", 0), ("42", 42), ("-17", -17),
                               ("9007199254740991", 2**53 - 1), ("-9007199254740991", -(2**53 - 1))]:
            with self.subTest(text=text):
                value = loads(f"a: {text}\n")["a"]
                self.assertIs(type(value), int)
                self.assertEqual(value, expected)

    def test_decimals(self) -> None:
        for text, expected in [("1.5", 1.5), ("-0.25", -0.25), ("0.0", 0.0), ("10.125", 10.125)]:
            with self.subTest(text=text):
                value = loads(f"a: {text}\n")["a"]
                self.assertIs(type(value), float)
                self.assertEqual(value, expected)

    def test_booleans(self) -> None:
        self.assertEqual(loads("a: true\nb: false\nc: [true, false]\n"), {"a": True, "b": False, "c": [True, False]})
        self.assertIs(loads("a: true\n")["a"], True)

    def test_double_quoted_escapes(self) -> None:
        for text, expected in [
            ('"\\u00e9"', "\u00e9"), ('"\\U0001F600"', "\U0001F600"), ('"\\x41"', "A"),
            ('"a\\nb"', "a\nb"), ('"a\\tb"', "a\tb"), ('"\\\\"', "\\"), ('"\\""', '"'), ('"\\/"', "/"),
            ('"\\r"', "\r"), ('"\\0"', "\0"), ('"\\u002d\\u002d"', "--"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(loads(f"a: {text}\n")["a"], expected)

    def test_literal_unicode(self) -> None:
        self.assertEqual(loads('a: "\u65e5\u672c\u8a9e \u00e9 \U0001F600"\n'), {"a": "\u65e5\u672c\u8a9e \u00e9 \U0001F600"})


class TestLenient(unittest.TestCase):
    def test_plain_scalars_become_strings(self) -> None:
        data = loads("title: Hello world\ndate: 2024-01-01\nversion: 1.0.0\n", lenient=True)
        self.assertEqual(data, {"title": "Hello world", "date": "2024-01-01", "version": "1.0.0"})

    def test_numbers_and_booleans_keep_types(self) -> None:
        self.assertEqual(loads("n: 3\nf: 1.5\nb: true\n", lenient=True), {"n": 3, "f": 1.5, "b": True})

    def test_comments_after_plain_scalars(self) -> None:
        self.assertEqual(loads("a: plain value # comment\n# full line\n", lenient=True), {"a": "plain value"})

    def test_plain_flow_items(self) -> None:
        self.assertEqual(loads("tags: [alpha, beta]\n", lenient=True), {"tags": ["alpha", "beta"]})

    def test_plain_block_items(self) -> None:
        self.assertEqual(loads("tags:\n  - alpha\n  - beta gamma\n", lenient=True), {"tags": ["alpha", "beta gamma"]})

    def test_duplicates_still_rejected(self) -> None:
        with self.assertRaises(YAMLError):
            loads("a: x\na: y\n", lenient=True)


class TestSpans(unittest.TestCase):
    TEXT = 'a: 1\nb:\n  c: "x"\n  d:\n    - "y"\n    - e: 2\nf: [1, 2]\n'

    def test_key_positions(self) -> None:
        spans = parse(self.TEXT).spans
        self.assertEqual(spans[("a",)], (1, 1))
        self.assertEqual(spans[("b",)], (2, 1))
        self.assertEqual(spans[("b", "c")], (3, 3))
        self.assertEqual(spans[("b", "d")], (4, 3))
        self.assertEqual(spans[("b", "d", 0)], (5, 5))
        self.assertEqual(spans[("b", "d", 1)], (6, 5))
        self.assertEqual(spans[("b", "d", 1, "e")], (6, 7))
        # A flow value records its own opening column for the key path; only the line is contractual.
        self.assertEqual(spans[("f",)][0], 7)
        self.assertEqual(spans[("f", 1)], (7, 8))

    def test_position_walks_up_to_nearest_parent(self) -> None:
        parsed = parse(self.TEXT)
        self.assertEqual(parsed.position(("b", "c", "missing")), (3, 3))
        self.assertEqual(parsed.position(("nope",)), (1, 1))
        self.assertEqual(parsed.position(()), (1, 1))

    def test_error_positions(self) -> None:
        with self.assertRaises(YAMLError) as cm:
            loads("a: 1\nb: hello\n")
        self.assertEqual((cm.exception.line, cm.exception.col), (2, 4))
        with self.assertRaises(YAMLError) as cm:
            loads("a:\n  b: 1\n  b: 2\n")
        self.assertEqual((cm.exception.line, cm.exception.col), (3, 3))
        with self.assertRaises(YAMLError) as cm:
            loads("a: 1\n\tb: 2\n")
        self.assertEqual(cm.exception.line, 2)


class TestDumps(unittest.TestCase):
    def test_canonical_input_is_a_fixed_point(self) -> None:
        self.assertEqual(dumps(loads(CANONICAL)), CANONICAL)

    def test_dump_parse_dump_fixed_point(self) -> None:
        samples = [
            CANONICAL_DATA,
            {"a": "x\ny\t\"z\"\\", "b": [1, -2, 0.5, True, False], "c": {"d": {"e": []}}},
            {"u": "\u65e5\u672c \u00e9 \U0001F600", "ctrl": "\x01\x7f\x85\u2028", "quote": "'"},
            {"seq": [{"a": 1}, {}, [], ["x", "y"], "s"], "k": {"a b": 1, "true": 2, "<<": 3}},
            {"long": ["item-%02d-with-some-padding" % i for i in range(12)]},
        ]
        for data in samples:
            with self.subTest(data=data):
                first = dumps(data)
                self.assertEqual(loads(first), data)
                self.assertEqual(dumps(loads(first)), first)

    def test_byte_stable(self) -> None:
        self.assertEqual(dumps(CANONICAL_DATA), dumps(CANONICAL_DATA))
        self.assertTrue(dumps({"a": 1}).endswith("\n"))

    def test_non_canonical_input_normalizes(self) -> None:
        text = "b: 'x'\na:\n  - 'p'\n  - \"q\"\nc: {d: 1}\n"
        out = dumps(loads(text))
        self.assertEqual(out, 'b: "x"\na: ["p", "q"]\nc:\n  d: 1\n')
        self.assertEqual(dumps(loads(out)), out)

    def test_strings_are_double_quoted(self) -> None:
        self.assertEqual(dumps({"a": "x", "b": "NO", "c": "1.0"}), 'a: "x"\nb: "NO"\nc: "1.0"\n')

    def test_escaping(self) -> None:
        for value, expected in [
            ("\\", '"\\\\"'), ('"', '"\\""'), ("\n", '"\\n"'), ("\t", '"\\t"'), ("\r", '"\\r"'),
            ("\x01", '"\\u0001"'), ("\x1f", '"\\u001f"'), ("\x7f", '"\\u007f"'), ("\u00e9", '"\u00e9"'),
            ("\u65e5\u672c", '"\u65e5\u672c"'), ("\U0001F600", '"\U0001F600"'),
        ]:
            with self.subTest(value=value):
                self.assertEqual(dumps({"a": value}), f"a: {expected}\n")

    def test_numbers_and_booleans(self) -> None:
        self.assertEqual(dumps({"i": 3, "n": -1, "f": 1.5, "t": True, "x": False}),
                         "i: 3\nn: -1\nf: 1.5\nt: true\nx: false\n")

    def test_empty_containers(self) -> None:
        self.assertEqual(dumps({"a": [], "b": {}}), "a: []\nb: {}\n")
        self.assertEqual(dumps({"a": [{}, []]}), "a:\n  - {}\n  - []\n")

    def test_nested_indentation(self) -> None:
        data = {"a": {"b": {"c": "d"}, "e": [{"f": 1, "g": {"h": 2}}]}}
        self.assertEqual(dumps(data), 'a:\n  b:\n    c: "d"\n  e:\n    - f: 1\n      g:\n        h: 2\n')

    def test_scalar_sequence_flow_when_it_fits(self) -> None:
        self.assertEqual(dumps({"tags": ["a", "b", 1]}), 'tags: ["a", "b", 1]\n')

    def test_flow_width_boundary(self) -> None:
        # "k: [" + '"' + s + '"' + "]" is len(s) + 7 columns.
        fits = dumps({"k": ["x" * 81]})
        self.assertEqual(len(fits.rstrip("\n")), 88)
        self.assertTrue(fits.startswith("k: ["))
        too_wide = dumps({"k": ["x" * 82]})
        self.assertEqual(too_wide, 'k:\n  - "' + "x" * 82 + '"\n')

    def test_nested_flow_width_counts_indentation(self) -> None:
        out = dumps({"a": {"b": {"k": ["x" * 77]}}})
        self.assertIn('    k: ["', out)
        out = dumps({"a": {"b": {"k": ["x" * 78]}}})
        self.assertIn('    k:\n      - "', out)

    def test_sequence_of_mappings_is_block(self) -> None:
        self.assertEqual(dumps({"a": [{"x": 1}, {"y": "z"}]}), 'a:\n  - x: 1\n  - y: "z"\n')

    def test_mixed_sequence_is_block(self) -> None:
        self.assertEqual(dumps({"a": ["s", {"x": 1}]}), 'a:\n  - "s"\n  - x: 1\n')

    def test_multiline_string_is_never_a_block_scalar(self) -> None:
        out = dumps({"a": "one\ntwo\n"})
        self.assertEqual(out, 'a: "one\\ntwo\\n"\n')
        self.assertNotIn("|", out)

    def test_keys_needing_quotes(self) -> None:
        out = dumps({"a b": 1, "true": 2, "null": 3, "<<": 4, "x-y.z": 5})
        self.assertEqual(out, '"a b": 1\n"true": 2\n"null": 3\n"<<": 4\nx-y.z: 5\n')
        self.assertEqual(loads(out), {"a b": 1, "true": 2, "null": 3, "<<": 4, "x-y.z": 5})

    def test_order_callback(self) -> None:
        calls: list[tuple] = []

        def order(path: tuple):
            calls.append(path)
            if path == ():
                return ["b", "a", "missing"]
            if path == ("items", "[]"):
                return ["z", "y"]
            return None

        data = {"a": 1, "extra2": 2, "b": 3, "extra1": 4, "items": [{"y": 1, "z": 2}]}
        out = dumps(data, order=order)
        self.assertEqual(out, "b: 3\na: 1\nextra2: 2\nextra1: 4\nitems:\n  - z: 2\n    y: 1\n")
        self.assertIn((), calls)
        self.assertIn(("items", "[]"), calls)

    def test_order_independent_of_insertion(self) -> None:
        def order(path: tuple):
            return ["a", "b", "c"] if path == () else None

        self.assertEqual(dumps({"c": 1, "a": 2, "b": 3}, order=order), dumps({"b": 3, "c": 1, "a": 2}, order=order))

    def test_forbid_html(self) -> None:
        self.assertEqual(dumps({"a": "a--b"}, forbid="html"), 'a: "a-\\u002db"\n')
        self.assertEqual(dumps({"a": "a---b"}, forbid="html"), 'a: "a-\\u002d\\u002db"\n')
        self.assertEqual(dumps({"a": "a-b"}, forbid="html"), 'a: "a-b"\n')
        self.assertEqual(dumps({"a": "a--b"}), 'a: "a--b"\n')
        out = dumps({"a": "x-->y", "l": ["--"]}, forbid="html")
        self.assertNotIn("--", out)
        self.assertEqual(loads(out), {"a": "x-->y", "l": ["--"]})

    def test_forbid_block(self) -> None:
        self.assertEqual(dumps({"a": "a*/b"}, forbid="block"), 'a: "a*\\u002fb"\n')
        self.assertEqual(dumps({"a": "/* x"}, forbid="block"), 'a: "/* x"\n')
        out = dumps({"a": "end */ here", "b": "**/"}, forbid="block")
        self.assertNotIn("*/", out)
        self.assertEqual(loads(out), {"a": "end */ here", "b": "**/"})

    def test_forbid_html_does_not_touch_block_sequences(self) -> None:
        self.assertEqual(dumps({"a": "*/"}, forbid="html"), 'a: "*/"\n')
        self.assertEqual(dumps({"a": "--"}, forbid="block"), 'a: "--"\n')

    def test_unserializable_values(self) -> None:
        for value, exc in [(None, ValueError), (float("inf"), ValueError), (float("nan"), ValueError),
                           (2**53, ValueError), (object(), TypeError)]:
            with self.subTest(value=value):
                with self.assertRaises(exc):
                    dumps({"a": value})

    def test_top_level_must_be_mapping(self) -> None:
        with self.assertRaises(TypeError):
            dumps(["a"])  # type: ignore[arg-type]

    def test_non_string_keys_refused(self) -> None:
        with self.assertRaises(TypeError):
            dumps({1: "a"})  # type: ignore[dict-item]


class TestIterStrings(unittest.TestCase):
    def test_yields_keys_and_values(self) -> None:
        got = list(yamlsub.iter_strings({"a": ["b", {"c": "d"}, 1], "e": True}))
        self.assertEqual(got, ["a", "b", "c", "d", "e"])


if __name__ == "__main__":
    unittest.main()
