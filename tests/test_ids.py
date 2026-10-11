"""Identifiers: UUIDv7 minting, Somnus URNs, legacy references, slugs (SPEC section 3.1)."""

from __future__ import annotations

import unittest
import uuid
from datetime import datetime, timezone

from somnus import ids

A = "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a"
V4 = "urn:somnus:artifact:2f1c3b9e-6d4a-4c1b-9e3f-0a1b2c3d4e5f"


class TestUUID7(unittest.TestCase):
    def test_version_and_variant(self) -> None:
        for _ in range(50):
            u = ids.uuid7()
            self.assertEqual(u.version, 7)
            self.assertEqual(u.variant, uuid.RFC_4122)
            self.assertEqual(str(u)[14], "7")
            self.assertIn(str(u)[19], "89ab")

    def test_monotonic_within_process(self) -> None:
        minted = [ids.uuid7().int for _ in range(5000)]
        self.assertEqual(minted, sorted(minted))
        self.assertEqual(len(set(minted)), len(minted))

    def test_explicit_timestamp_is_encoded(self) -> None:
        ms = 1_760_000_000_123
        u = ids.uuid7(ms)
        self.assertEqual(u.int >> 80, ms)
        self.assertEqual(u.version, 7)

    def test_uuid7_time_round_trip(self) -> None:
        ms = 1_760_000_000_123
        urn = f"urn:somnus:artifact:{ids.uuid7(ms)}"
        got = ids.uuid7_time(urn)
        self.assertEqual(got, datetime.fromtimestamp(ms / 1000, tz=timezone.utc))
        self.assertEqual(got.utcoffset().total_seconds(), 0)

    def test_uuid7_time_rejects_other_versions(self) -> None:
        self.assertIsNone(ids.uuid7_time(V4))
        self.assertIsNone(ids.uuid7_time("urn:somnus:example:x"))
        self.assertIsNone(ids.uuid7_time("not a urn"))

    def test_new_artifact_urn(self) -> None:
        urn = ids.new_artifact_urn()
        self.assertTrue(ids.is_artifact_urn(urn))
        self.assertEqual(ids.uuid_version(urn), 7)

    def test_uuid_version(self) -> None:
        self.assertEqual(ids.uuid_version(A), 7)
        self.assertEqual(ids.uuid_version(V4), 4)
        self.assertIsNone(ids.uuid_version("urn:somnus:example:a"))


class TestURNs(unittest.TestCase):
    def test_parse_urn(self) -> None:
        for urn, expected in [
            (A, ("artifact", A.split(":", 3)[3])),
            ("urn:somnus:entity:somnus-core", ("entity", "somnus-core")),
            ("urn:somnus:actor:trey", ("actor", "trey")),
            ("urn:somnus:concept:metadata-standard", ("concept", "metadata-standard")),
            ("urn:somnus:example:fixture-1", ("example", "fixture-1")),
            ("urn:somnus:concept:a.b_c:d-E", ("concept", "a.b_c:d-E")),
        ]:
            with self.subTest(urn=urn):
                self.assertEqual(ids.parse_urn(urn), expected)

    def test_parse_urn_rejects(self) -> None:
        for bad in ["urn:somnus:doc:x", "urn:somnus:entity:", "urn:somnus:entity:-x", "urn:other:x:y",
                    "urn:somnus:entity:a b", "somnus:entity:x", ""]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    ids.parse_urn(bad)

    def test_is_artifact_urn(self) -> None:
        self.assertTrue(ids.is_artifact_urn(A))
        self.assertTrue(ids.is_artifact_urn(V4))
        for bad in [A.upper(), "urn:somnus:artifact:01A12A94-8657-715c-9044-852de0e3f08a",
                    "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08", A + "0", A + "\n",
                    "urn:somnus:artifact:01a12a948657715c9044852de0e3f08a", "urn:somnus:example:a"]:
            with self.subTest(bad=bad):
                self.assertFalse(ids.is_artifact_urn(bad))

    def test_is_example_urn(self) -> None:
        self.assertTrue(ids.is_example_urn("urn:somnus:example:a"))
        self.assertTrue(ids.is_example_urn("urn:somnus:example:fixture-21"))
        for bad in ["urn:somnus:example:A", "urn:somnus:example:-a", "urn:somnus:example:",
                    "urn:somnus:example:a_b", A]:
            with self.subTest(bad=bad):
                self.assertFalse(ids.is_example_urn(bad))

    def test_is_external_ref(self) -> None:
        for good in ["doi:10.1000/xyz", "https://example.org/a", "http://example.org", "urn:isbn:0451450523",
                     "urn:ietf:rfc:9562"]:
            with self.subTest(good=good):
                self.assertTrue(ids.is_external_ref(good))
        for bad in [A, "urn:somnus:entity:x", "doi:11.1/x", "ftp://x", "https://", "relative/path.md", "urn:x"]:
            with self.subTest(bad=bad):
                self.assertFalse(ids.is_external_ref(bad))

    def test_is_reference_string(self) -> None:
        for good in [A, "urn:somnus:entity:x", "urn:somnus:example:e", "doi:10.1/x", "https://a.b"]:
            with self.subTest(good=good):
                self.assertTrue(ids.is_reference_string(good))
        for bad in ["docs/spec.md", "urn:somnus:doc:" + A[-36:], "", "title"]:
            with self.subTest(bad=bad):
                self.assertFalse(ids.is_reference_string(bad))


class TestLegacy(unittest.TestCase):
    UUID = "01a12a94-8657-715c-9044-852de0e3f08a"

    def test_doc_urn_normalizes(self) -> None:
        self.assertEqual(ids.normalize_legacy_ref(f"urn:somnus:doc:{self.UUID}"), A)

    def test_doc_urn_uppercase_normalizes_to_lowercase(self) -> None:
        self.assertEqual(ids.normalize_legacy_ref(f"urn:somnus:doc:{self.UUID.upper()}"), A)

    def test_bare_uuid_normalizes(self) -> None:
        self.assertEqual(ids.normalize_legacy_ref(self.UUID), A)
        self.assertEqual(ids.normalize_legacy_ref(self.UUID.upper()), A)

    def test_other_values_unchanged(self) -> None:
        for value in [A, "urn:somnus:entity:x", "https://x.y", "not-a-uuid", self.UUID + "0"]:
            with self.subTest(value=value):
                self.assertEqual(ids.normalize_legacy_ref(value), value)

    def test_imported_v4_is_not_reminted(self) -> None:
        self.assertEqual(ids.normalize_legacy_ref("2f1c3b9e-6d4a-4c1b-9e3f-0a1b2c3d4e5f"), V4)


class TestSlugify(unittest.TestCase):
    def test_cases(self) -> None:
        for title, expected in [
            ("Hello World", "hello-world"),
            ("  Leading and trailing  ", "leading-and-trailing"),
            ("Somnus: Normative Specification!", "somnus-normative-specification"),
            ("Caf\u00e9 \u00dcn\u00efc\u00f6d\u00e9", "cafe-unicode"),
            ("a---b___c", "a-b-c"),
            ("v2.0 / API", "v2-0-api"),
            ("ALL CAPS", "all-caps"),
        ]:
            with self.subTest(title=title):
                slug = ids.slugify(title)
                self.assertEqual(slug, expected)
                self.assertRegex(slug, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def test_transliterated_letters(self) -> None:
        self.assertEqual(ids.slugify("\u00d8resund Stra\u00dfe"), "oresund-strasse")
        self.assertEqual(ids.slugify("\u00c6r\u00f8 \u0141\u00f3d\u017a"), "aero-lodz")

    def test_empty_becomes_untitled(self) -> None:
        for title in ["", "   ", "!!!", "\u65e5\u672c\u8a9e", "---"]:
            with self.subTest(title=title):
                self.assertEqual(ids.slugify(title), "untitled")

    def test_max_len(self) -> None:
        slug = ids.slugify("word " * 40, max_len=20)
        self.assertLessEqual(len(slug), 20)
        self.assertFalse(slug.endswith("-"))
        self.assertEqual(ids.slugify("abcdef", max_len=3), "abc")
        self.assertLessEqual(len(ids.slugify("x" * 200)), 80)


class TestLocalId(unittest.TestCase):
    def test_valid(self) -> None:
        for value in ["a", "r-lifecycle", "claim_1", "r-a-b", "x9", "a_b-c_d"]:
            with self.subTest(value=value):
                self.assertTrue(ids.is_local_id(value))

    def test_invalid(self) -> None:
        for value in ["", "1a", "A", "r-", "-r", "r--x", "r.x", "r x", "_a", "r-X"]:
            with self.subTest(value=value):
                self.assertFalse(ids.is_local_id(value))


if __name__ == "__main__":
    unittest.main()
