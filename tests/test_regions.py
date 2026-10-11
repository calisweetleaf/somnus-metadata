"""Region markers: pairing, inert contexts, spacing, headings, TeX labels, registry sync (SPEC section 13)."""

from __future__ import annotations

import unittest

from somnus import regions as R

MD = ("markdown",)
HASH = ("prefix", "# ")
TEX = ("prefix", "% ")
SLASH = ("prefix", "// ")
SQL = ("prefix", "-- ")
BLOCK = ("block", "/* ", " */")


def md_begin(rid: str) -> str:
    return f"<!-- somnus:region:begin {rid} -->"


def md_end(rid: str) -> str:
    return f"<!-- somnus:region:end {rid} -->"


def spaced(*lines: str) -> list[str]:
    """Interleave blank lines so markers satisfy the spacing rule."""
    out: list[str] = []
    for ln in lines:
        out.extend([ln, ""])
    return out


def codes(scan: R.MarkerScan) -> list[str]:
    return [issue[2] for issue in scan.issues]


def errors(scan: R.MarkerScan) -> list[str]:
    return [c for c in codes(scan) if c.startswith("E_")]


class TestPairing(unittest.TestCase):
    def test_single_region(self) -> None:
        lines = spaced(md_begin("r-a"), "text", md_end("r-a"))
        scan = R.scan_markers(lines, MD)
        self.assertEqual(scan.issues, [])
        rng = scan.ranges["r-a"]
        self.assertEqual((rng.begin_line, rng.end_line, rng.depth, rng.parent), (1, 5, 0, None))

    def test_nested_regions_valid(self) -> None:
        # SPEC section 21 fixture 7.
        lines = spaced(md_begin("r-outer"), md_begin("r-inner"), "body", md_end("r-inner"), md_end("r-outer"))
        scan = R.scan_markers(lines, MD)
        self.assertEqual(scan.issues, [])
        self.assertEqual(scan.ranges["r-inner"].parent, "r-outer")
        self.assertEqual(scan.ranges["r-inner"].depth, 1)
        self.assertEqual(scan.ranges["r-outer"].depth, 0)
        outer, inner = scan.ranges["r-outer"], scan.ranges["r-inner"]
        self.assertLess(outer.begin_line, inner.begin_line)
        self.assertLess(inner.end_line, outer.end_line)

    def test_sibling_regions(self) -> None:
        lines = spaced(md_begin("r-a"), md_end("r-a"), md_begin("r-b"), md_end("r-b"))
        scan = R.scan_markers(lines, MD)
        self.assertEqual(scan.issues, [])
        self.assertEqual(set(scan.ranges), {"r-a", "r-b"})

    def test_region_errors(self) -> None:
        # SPEC section 21 fixture 8.
        cases = {
            "crossing": [md_begin("r-a"), md_begin("r-b"), md_end("r-a"), md_end("r-b")],
            "unclosed": [md_begin("r-a"), "text"],
            "duplicate": [md_begin("r-a"), md_end("r-a"), md_begin("r-a"), md_end("r-a")],
            "unmatched-end": ["text", md_end("r-a")],
            "end-for-other": [md_begin("r-a"), md_end("r-b"), md_end("r-a")],
            "bad-id": [md_begin("Bad_ID"), md_end("Bad_ID")],
            "malformed": ["<!--somnus:region:begin r-a-->", "<!--somnus:region:end r-a-->"],
            "missing-id": ["<!-- somnus:region:begin -->"],
        }
        for name, body in cases.items():
            with self.subTest(case=name):
                scan = R.scan_markers(spaced(*body), MD)
                self.assertIn("E_REGION", errors(scan))

    def test_crossing_does_not_produce_valid_range_for_crossed_region(self) -> None:
        scan = R.scan_markers(spaced(md_begin("r-a"), md_begin("r-b"), md_end("r-a"), md_end("r-b")), MD)
        self.assertNotIn("r-a", scan.ranges)

    def test_issue_lines_are_one_based(self) -> None:
        scan = R.scan_markers(["", md_end("r-a"), ""], MD)
        self.assertEqual(scan.issues[0][0], 2)

    def test_no_style_means_no_markers(self) -> None:
        scan = R.scan_markers([md_begin("r-a")], ())
        self.assertEqual((scan.ranges, scan.issues), ({}, []))

    def test_unknown_style_raises(self) -> None:
        with self.assertRaises(ValueError):
            R.scan_markers(["x"], ("weird",))


class TestInert(unittest.TestCase):
    MARKERS = [md_begin("r-x"), "", md_end("r-x")]

    def assertInert(self, lines: list[str], style: tuple = MD, **kw) -> None:
        scan = R.scan_markers(lines, style, **kw)
        self.assertEqual(scan.ranges, {})
        self.assertEqual(errors(scan), [])

    def test_backtick_fence(self) -> None:
        # SPEC section 21 fixture 6.
        self.assertInert(["```markdown", *self.MARKERS, "```"])

    def test_tilde_fence(self) -> None:
        self.assertInert(["~~~", *self.MARKERS, "~~~"])

    def test_long_fence_containing_short_fence(self) -> None:
        self.assertInert(["````", "```", md_begin("r-x"), "```", md_end("r-x"), "````"])

    def test_fence_not_closed_by_other_char(self) -> None:
        self.assertInert(["```", "~~~", md_begin("r-x"), "~~~", md_end("r-x"), "```"])

    def test_unclosed_fence_hides_rest(self) -> None:
        self.assertInert(["```", md_begin("r-x")])

    def test_indented_fence(self) -> None:
        self.assertInert(["   ```", *self.MARKERS, "   ```"])

    def test_indented_code_block(self) -> None:
        self.assertInert(["Paragraph.", "", "    " + md_begin("r-x"), "", "    " + md_end("r-x"), ""])

    def test_unbalanced_markers_in_code_are_not_errors(self) -> None:
        self.assertInert(["```", md_end("r-z"), md_begin("r-y"), "```"])

    def test_envelope_span_is_inert(self) -> None:
        lines = ["---", md_begin("r-x"), md_end("r-x"), "---", ""]
        self.assertInert(lines, ignore=(0, 4))

    def test_markers_after_fence_are_live(self) -> None:
        lines = ["```", "code", "```", "", *spaced(md_begin("r-x"), md_end("r-x"))]
        scan = R.scan_markers(lines, MD)
        self.assertEqual(list(scan.ranges), ["r-x"])

    def test_code_mask(self) -> None:
        mask = R.markdown_code_mask(["text", "```", "code", "```", "", "    indented", "after"])
        self.assertEqual(mask, [False, True, True, True, False, True, False])

    def test_inline_backticks_are_not_a_fence(self) -> None:
        mask = R.markdown_code_mask(["```inline``` text", md_begin("r-x")])
        self.assertEqual(mask, [False, False])


class TestPython(unittest.TestCase):
    def test_comment_markers_count(self) -> None:
        lines = ["# somnus:region:begin r-a", "x = 1", "# somnus:region:end r-a"]
        scan = R.scan_markers(lines, HASH, host="python")
        self.assertEqual(scan.issues, [])
        self.assertEqual(list(scan.ranges), ["r-a"])

    def test_indented_comment_markers_count(self) -> None:
        lines = ["def f():", "    # somnus:region:begin r-a", "    return 1", "    # somnus:region:end r-a"]
        scan = R.scan_markers(lines, HASH, host="python")
        self.assertEqual(list(scan.ranges), ["r-a"])

    def test_markers_inside_string_literals_are_inert(self) -> None:
        lines = ['s = """', "# somnus:region:begin r-a", "# somnus:region:end r-b", '"""']
        scan = R.scan_markers(lines, HASH, host="python")
        self.assertEqual((scan.ranges, scan.issues), ({}, []))

    def test_trailing_comment_is_not_a_marker(self) -> None:
        lines = ["x = 1  # somnus:region:begin r-a"]
        scan = R.scan_markers(lines, HASH, host="python")
        self.assertEqual((scan.ranges, scan.issues), ({}, []))

    def test_string_literal_counts_for_non_python_hash_hosts(self) -> None:
        lines = ["# somnus:region:begin r-a", "# somnus:region:end r-a"]
        self.assertEqual(list(R.scan_markers(lines, HASH, host="toml").ranges), ["r-a"])


class TestOtherStyles(unittest.TestCase):
    def test_prefix_styles(self) -> None:
        for style, prefix in [(TEX, "%"), (SLASH, "//"), (SQL, "--")]:
            with self.subTest(prefix=prefix):
                lines = [f"{prefix} somnus:region:begin r-eq", "body", f"{prefix} somnus:region:end r-eq"]
                scan = R.scan_markers(lines, style)
                self.assertEqual(scan.issues, [])
                self.assertEqual(list(scan.ranges), ["r-eq"])

    def test_block_style(self) -> None:
        lines = ["/* somnus:region:begin r-x */", "a { }", "/* somnus:region:end r-x */"]
        scan = R.scan_markers(lines, BLOCK)
        self.assertEqual(scan.issues, [])
        self.assertEqual(list(scan.ranges), ["r-x"])

    def test_block_style_malformed(self) -> None:
        scan = R.scan_markers(["/*somnus:region:begin r-x*/"], BLOCK)
        self.assertIn("E_REGION", errors(scan))

    def test_wrong_prefix_is_ignored(self) -> None:
        scan = R.scan_markers(["# somnus:region:begin r-x"], SLASH)
        self.assertEqual((scan.ranges, scan.issues), ({}, []))


class TestSpacing(unittest.TestCase):
    def test_adjacent_text_warns(self) -> None:
        lines = ["text", md_begin("r-a"), "body", md_end("r-a"), "after"]
        scan = R.scan_markers(lines, MD)
        self.assertEqual(codes(scan), ["W_REGION_SPACING", "W_REGION_SPACING"])
        self.assertIn("r-a", scan.ranges)

    def test_blank_lines_do_not_warn(self) -> None:
        scan = R.scan_markers(["text", "", md_begin("r-a"), "", "body", "", md_end("r-a"), "", "after"], MD)
        self.assertEqual(scan.issues, [])

    def test_line_after_envelope_counts_as_separated(self) -> None:
        lines = ["---", "x: 1", "---", md_begin("r-a"), "", md_end("r-a")]
        scan = R.scan_markers(lines, MD, ignore=(0, 3))
        self.assertEqual(scan.issues, [])

    def test_spacing_only_applies_to_markdown(self) -> None:
        scan = R.scan_markers(["x", "# somnus:region:begin r-a", "y", "# somnus:region:end r-a", "z"], HASH)
        self.assertEqual(scan.issues, [])


class TestHeadings(unittest.TestCase):
    def test_atx_headings(self) -> None:
        lines = ["# One", "text", "## Two ##", "   ### Three", "#NoSpace", "####### Seven", "#", "###### Six  "]
        self.assertEqual(R.headings(lines), [("One", 1), ("Two", 3), ("Three", 4), ("", 7), ("Six", 8)])

    def test_headings_in_code_and_envelope_ignored(self) -> None:
        lines = ["---", "# not heading", "---", "```", "# code", "```", "    # indented code", "", "# Real"]
        self.assertEqual(R.headings(lines, ignore=(0, 3)), [("Real", 9)])


class TestTexLabels(unittest.TestCase):
    def test_labels(self) -> None:
        lines = [
            r"\begin{equation}\label{eq:one}",
            r"% \label{eq:commented}",
            r"x = 1 % trailing \label{eq:trailing}",
            r"50\% done \label{eq:escaped}",
            r"\label{a}\label{b}",
        ]
        self.assertEqual(R.tex_labels(lines), [("eq:one", 1), ("eq:escaped", 4), ("a", 5), ("b", 5)])

    def test_ignore_span(self) -> None:
        self.assertEqual(R.tex_labels([r"\label{x}", r"\label{y}"], ignore=(0, 1)), [("y", 2)])


class TestSyncRegistry(unittest.TestCase):
    def scan(self, *ids: str) -> R.MarkerScan:
        lines: list[str] = []
        for rid in ids:
            lines += [md_begin(rid), "", md_end(rid), ""]
        return R.scan_markers(lines, MD)

    def test_adds_unregistered_in_document_order(self) -> None:
        somnus: dict = {}
        added, missing = R.sync_registry(somnus, self.scan("r-b", "r-a"))
        self.assertEqual(added, ["r-b", "r-a"])
        self.assertEqual(missing, [])
        self.assertEqual(somnus["knowledge"]["regions"], [
            {"id": "r-b", "kind": "section", "selector": {"kind": "marker", "name": "r-b"}},
            {"id": "r-a", "kind": "section", "selector": {"kind": "marker", "name": "r-a"}},
        ])

    def test_never_removes_and_reports_missing(self) -> None:
        existing = {"id": "r-gone", "kind": "definition", "selector": {"kind": "marker", "name": "r-gone"}}
        heading = {"id": "r-head", "kind": "section", "selector": {"kind": "heading", "text": "X", "occurrence": 1}}
        somnus = {"knowledge": {"regions": [existing, heading]}}
        added, missing = R.sync_registry(somnus, self.scan("r-new"))
        self.assertEqual(added, ["r-new"])
        self.assertEqual(missing, ["r-gone"])
        self.assertEqual(somnus["knowledge"]["regions"][:2], [existing, heading])
        self.assertEqual(len(somnus["knowledge"]["regions"]), 3)

    def test_registered_markers_not_duplicated(self) -> None:
        reg = {"id": "r-alias", "kind": "section", "selector": {"kind": "marker", "name": "r-a"}}
        same_id = {"id": "r-b", "kind": "section", "selector": {"kind": "heading", "text": "B", "occurrence": 1}}
        somnus = {"knowledge": {"regions": [reg, same_id]}}
        added, missing = R.sync_registry(somnus, self.scan("r-a", "r-b"))
        self.assertEqual(added, [])
        self.assertEqual(missing, [])
        self.assertEqual(len(somnus["knowledge"]["regions"]), 2)

    def test_idempotent(self) -> None:
        somnus: dict = {}
        scan = self.scan("r-a")
        R.sync_registry(somnus, scan)
        added, _ = R.sync_registry(somnus, scan)
        self.assertEqual(added, [])
        self.assertEqual(len(somnus["knowledge"]["regions"]), 1)


if __name__ == "__main__":
    unittest.main()
