"""Lifecycle state machine (SPEC section 7)."""

from __future__ import annotations

import copy
import unittest

from somnus.model import lifecycle as L
from somnus.model import vocab

STATUSES = ["draft", "proposed", "provisional", "active", "experimental", "superseded", "deprecated",
            "historical", "archived", "rejected"]

# Transcribed from the SPEC section 7.1 table, independent of the implementation.
SPEC_TABLE = {
    "draft": {"proposed", "experimental", "rejected", "archived"},
    "proposed": {"provisional", "active", "rejected", "experimental", "superseded", "archived"},
    "provisional": {"active", "experimental", "rejected", "superseded", "deprecated", "archived"},
    "experimental": {"draft", "proposed", "provisional", "rejected", "deprecated", "historical", "archived"},
    "active": {"superseded", "deprecated", "historical"},
    "superseded": {"historical", "active"},
    "deprecated": {"historical", "archived"},
    "historical": {"archived", "active"},
    "rejected": {"archived"},
    "archived": {"active"},
}
ABANDONMENTS = {(s, "archived") for s in ("draft", "proposed", "provisional", "experimental")}
REACTIVATIONS = {(s, "active") for s in ("superseded", "historical", "archived")}
REF = {"ref": "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a", "revision": 1}
OTHER = {"ref": "urn:somnus:artifact:2f1c3b9e-6d4a-4c1b-9e3f-0a1b2c3d4e5f"}


def payload(status: str = "active", standing: str = "candidate", **time) -> dict:
    p = {
        "revision": 3,
        "lifecycle": {"status": status},
        "authority": {"standing": standing, "scopes": [{"target_ref": REF["ref"], "aspects": ["content"]}]},
        "time": dict(time),
    }
    if standing == "accepted":
        p["authority"]["valid_time"] = {"basis": "open", "from": "2026-01-01T00:00:00Z"}
        p["authority"]["acceptance_ref"] = dict(OTHER)
    return p


class TestTransitionTable(unittest.TestCase):
    def test_status_vocabulary_matches_spec(self) -> None:
        self.assertEqual(set(vocab.STATUSES), set(STATUSES))
        self.assertEqual(set(L.TRANSITIONS), set(STATUSES))

    def test_every_pair(self) -> None:
        for current in STATUSES:
            for target in STATUSES:
                with self.subTest(current=current, target=target):
                    problems = L.check_transition(current, target, reason="because", replacement_refs=[REF])
                    if target in SPEC_TABLE[current]:
                        self.assertEqual(problems, [])
                    else:
                        self.assertTrue(problems)

    def test_same_status_refused(self) -> None:
        for status in STATUSES:
            with self.subTest(status=status):
                self.assertTrue(L.check_transition(status, status, reason="r"))

    def test_unknown_statuses_refused(self) -> None:
        self.assertTrue(L.check_transition("bogus", "active", reason="r"))
        self.assertTrue(L.check_transition("draft", "bogus", reason="r"))


class TestReasons(unittest.TestCase):
    def test_abandonment_requires_reason(self) -> None:
        for current, target in sorted(ABANDONMENTS):
            with self.subTest(current=current):
                self.assertTrue(L.is_abandonment(current, target))
                self.assertTrue(L.check_transition(current, target))
                self.assertTrue(L.check_transition(current, target, reason="   "))
                self.assertEqual(L.check_transition(current, target, reason="dropped"), [])

    def test_reactivation_requires_reason(self) -> None:
        for current, target in sorted(REACTIVATIONS):
            with self.subTest(current=current):
                self.assertTrue(L.is_reactivation(current, target))
                self.assertTrue(L.check_transition(current, target))
                self.assertTrue(L.check_transition(current, target, reason=""))
                self.assertEqual(L.check_transition(current, target, reason="back"), [])

    def test_other_permitted_transitions_need_no_reason(self) -> None:
        for current, targets in SPEC_TABLE.items():
            for target in targets:
                if (current, target) in ABANDONMENTS | REACTIVATIONS or target == "superseded":
                    continue
                with self.subTest(current=current, target=target):
                    self.assertEqual(L.check_transition(current, target), [])

    def test_deprecated_to_archived_is_not_abandonment(self) -> None:
        self.assertFalse(L.is_abandonment("deprecated", "archived"))
        self.assertEqual(L.check_transition("deprecated", "archived"), [])

    def test_superseded_requires_replacements(self) -> None:
        for current in ("proposed", "provisional", "active"):
            with self.subTest(current=current):
                self.assertTrue(L.check_transition(current, "superseded"))
                self.assertEqual(L.check_transition(current, "superseded", replacement_refs=[REF]), [])


class TestApply(unittest.TestCase):
    AT = "2026-06-01T12:00:00+00:00"

    def test_bumps_revision_and_sets_updated_at(self) -> None:
        before = payload("draft", created_at="2026-01-01T00:00:00Z")
        after = L.apply_transition(before, "proposed", at=self.AT)
        self.assertEqual(after["revision"], 4)
        self.assertEqual(after["lifecycle"]["status"], "proposed")
        self.assertEqual(after["time"]["updated_at"], self.AT)
        self.assertEqual(after["time"]["created_at"], "2026-01-01T00:00:00Z")

    def test_input_not_mutated(self) -> None:
        before = payload("draft")
        snapshot = copy.deepcopy(before)
        L.apply_transition(before, "archived", reason="x", at=self.AT)
        self.assertEqual(before, snapshot)

    def test_reason_stored_stripped_and_cleared(self) -> None:
        after = L.apply_transition(payload("draft"), "archived", reason="  abandoned  ", at=self.AT)
        self.assertEqual(after["lifecycle"]["reason"], "abandoned")
        p = payload("draft")
        p["lifecycle"]["reason"] = "stale reason"
        self.assertNotIn("reason", L.apply_transition(p, "proposed", at=self.AT)["lifecycle"])

    def test_replacements_merged_without_duplicates(self) -> None:
        p = payload("active")
        p["lifecycle"]["replacement_refs"] = [dict(REF)]
        after = L.apply_transition(p, "superseded", replacement_refs=[dict(REF), dict(OTHER)], at=self.AT)
        self.assertEqual(after["lifecycle"]["replacement_refs"], [REF, OTHER])

    def test_reactivation_resets_accepted_authority(self) -> None:
        for current in ("superseded", "historical", "archived"):
            with self.subTest(current=current):
                after = L.apply_transition(payload(current, "accepted"), "active", reason="back", at=self.AT)
                auth = after["authority"]
                self.assertEqual(auth["standing"], "candidate")
                self.assertNotIn("valid_time", auth)
                self.assertNotIn("acceptance_ref", auth)
                self.assertEqual(auth["scopes"], payload()["authority"]["scopes"])

    def test_non_reactivation_keeps_accepted_authority(self) -> None:
        after = L.apply_transition(payload("active", "accepted"), "deprecated", at=self.AT)
        self.assertEqual(after["authority"]["standing"], "accepted")
        self.assertIn("acceptance_ref", after["authority"])

    def test_reactivation_keeps_non_accepted_standing(self) -> None:
        after = L.apply_transition(payload("archived", "retired"), "active", reason="back", at=self.AT)
        self.assertEqual(after["authority"]["standing"], "retired")


class TestBumpRevision(unittest.TestCase):
    def test_increments(self) -> None:
        p = {"revision": 1, "time": {}}
        L.bump_revision(p, "2026-01-01T00:00:00Z")
        self.assertEqual(p["revision"], 2)
        self.assertEqual(p["time"]["updated_at"], "2026-01-01T00:00:00Z")

    def test_missing_revision_and_time(self) -> None:
        p: dict = {}
        L.bump_revision(p, "2026-01-01T00:00:00Z")
        self.assertEqual(p, {"revision": 1, "time": {"updated_at": "2026-01-01T00:00:00Z"}})

    def test_never_before_created_at(self) -> None:
        for created, at in [
            ("2030-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
            ("2026-01-01T05:00:00+05:00", "2025-12-31T23:59:59Z"),
        ]:
            with self.subTest(created=created):
                p = {"revision": 1, "time": {"created_at": created}}
                L.bump_revision(p, at)
                self.assertEqual(p["time"]["updated_at"], created)

    def test_offsets_compared_as_instants(self) -> None:
        # 2026-01-01T05:00:00+05:00 is 00:00Z, so 00:30Z is later even though it sorts earlier as text.
        p = {"revision": 1, "time": {"created_at": "2026-01-01T05:00:00+05:00"}}
        L.bump_revision(p, "2026-01-01T00:30:00Z")
        self.assertEqual(p["time"]["updated_at"], "2026-01-01T00:30:00Z")

    def test_default_stamp_is_utc_now(self) -> None:
        p = {"revision": 1, "time": {"created_at": "2000-01-01T00:00:00Z"}}
        L.bump_revision(p)
        self.assertRegex(p["time"]["updated_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")
        self.assertGreater(p["time"]["updated_at"], "2000-01-01")


if __name__ == "__main__":
    unittest.main()
