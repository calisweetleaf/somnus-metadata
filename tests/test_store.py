"""Registry store: indexing semantics of SPEC §18.3."""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from somnus import DB_USER_VERSION
from somnus import document as D
from somnus.db import Store, connect_readonly, glob_regex, matches_any, run_query
from somnus.carriers.sidecar import SIDECAR
from somnus.db.store import SEARCH_BODY_LIMIT, fts_query, intervals_overlap, searchable_body

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "SPEC.md"


class StoreTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "root"
        self.root.mkdir()
        self.db = self.tmp / "home" / "somnus.db"
        self.store = Store.open(self.db, actor="test")

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def count(self, sql: str) -> int:
        return self.store.conn.execute(sql).fetchone()[0]

    def conflicts(self) -> list[tuple]:
        return self.store.conn.execute("SELECT kind, state FROM conflicts ORDER BY id").fetchall()


class TestOpen(StoreTestCase):
    def test_schema_version_and_pragmas(self) -> None:
        self.assertEqual(self.count("PRAGMA user_version"), DB_USER_VERSION)
        self.assertEqual(self.store.conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(self.count("PRAGMA foreign_keys"), 1)

    def test_reopen_is_stable(self) -> None:
        self.store.close()
        self.store = Store.open(self.db, actor="test")
        self.assertEqual(self.count("PRAGMA user_version"), DB_USER_VERSION)

    def test_events_append_only(self) -> None:
        self.store.log("test")
        self.store.conn.commit()
        with self.assertRaises(sqlite3.DatabaseError):
            self.store.conn.execute("DELETE FROM events")
        with self.assertRaises(sqlite3.DatabaseError):
            self.store.conn.execute("UPDATE events SET action = 'x'")

    def test_no_json_columns(self) -> None:
        names = [r[0] for r in self.store.conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        for table in names:
            for col in self.store.conn.execute(f"PRAGMA table_info({table})"):
                self.assertNotIn("json", col[1].lower(), f"{table}.{col[1]}")


class TestIndexing(StoreTestCase):
    def setUp(self) -> None:
        super().setUp()
        shutil.copy(SPEC, self.root / "spec.md")

    def test_index_and_idempotence(self) -> None:
        first = self.store.scan([self.root])
        self.assertEqual(first.indexed, 1, first.diagnostics)
        self.assertEqual(first.new_revisions, 1)
        second = self.store.scan([self.root])
        self.assertEqual(second.unchanged, 1)
        third = self.store.scan([self.root], full=True)
        self.assertEqual(third.indexed, 1)
        self.assertEqual(third.new_revisions, 0)
        self.assertEqual(self.count("SELECT count(*) FROM revisions"), 1)
        self.assertEqual(self.count("SELECT count(*) FROM locations"), 1)

    def test_rename_keeps_identity(self) -> None:
        self.store.scan([self.root])
        (self.root / "spec.md").rename(self.root / "renamed.md")
        report = self.store.scan([self.root])
        self.assertEqual(report.missing, 1)
        rows = dict(self.store.conn.execute("SELECT rel_path, present FROM locations").fetchall())
        self.assertEqual(rows, {"spec.md": 0, "renamed.md": 1})
        self.assertEqual(self.count("SELECT count(*) FROM artifacts"), 1)
        self.assertEqual(self.conflicts(), [])

    def test_disappearance_is_not_tombstone(self) -> None:
        self.store.scan([self.root])
        (self.root / "spec.md").unlink()
        self.store.scan([self.root])
        self.assertEqual(self.count("SELECT count(*) FROM artifacts"), 1)
        self.assertEqual(self.count("SELECT count(*) FROM revisions"), 1)
        self.assertEqual(self.count("SELECT present FROM locations"), 0)

    def test_identical_mirror_allowed(self) -> None:
        shutil.copy(self.root / "spec.md", self.root / "mirror.md")
        self.store.scan([self.root])
        self.assertEqual(self.conflicts(), [])

    def test_divergent_copy_opens_and_resolves_conflicts(self) -> None:
        self.store.scan([self.root])
        text = (self.root / "spec.md").read_text(encoding="utf-8").replace("## 1. Scope", "## 1. Scope changed")
        (self.root / "mirror.md").write_text(text, encoding="utf-8", newline="")
        report = self.store.scan([self.root])
        kinds = sorted(k for k, s in self.conflicts() if s == "open")
        self.assertEqual(kinds, ["duplicate-id", "revision"], report.diagnostics)
        detail = self.store.conn.execute("SELECT detail FROM conflicts WHERE kind = 'revision'").fetchone()[0]
        self.assertIn("candidate header", detail)
        self.assertEqual(self.count("SELECT count(*) FROM revisions"), 1)
        self.assertIn(self.store.resolver().open_conflicts.get(self._aid(), [None])[0], ("duplicate-id", "revision"))
        (self.root / "mirror.md").unlink()
        self.store.scan([self.root])
        self.assertTrue(all(s == "resolved" for _, s in self.conflicts()))

    def test_identity_change_opens_conflict(self) -> None:
        self.store.scan([self.root])
        text = (self.root / "spec.md").read_text(encoding="utf-8")
        old = self._aid()
        new = "urn:somnus:artifact:01a12a94-8657-715c-9044-000000000001"
        (self.root / "spec.md").write_text(text.replace(old, new), encoding="utf-8", newline="")
        self.store.scan([self.root])
        self.assertIn(("identity", "open"), self.conflicts())
        self.assertEqual(self.store.resolve_conflicts(["identity"], artifact_id=new), 1)

    def test_resolver_and_queries(self) -> None:
        self.store.scan([self.root])
        res = self.store.resolver()
        facts = res.artifacts[self._aid()]
        self.assertEqual(facts.current_revision, D.load(SPEC).payload["revision"])
        self.assertEqual(len(self.store.list_docs()), 1)
        self.assertEqual(self.store.list_docs(type="index"), [])
        title = self.store.list_docs()[0][1]
        self.assertTrue(self.store.similar_titles(title.upper()))
        self.store.close()
        ro = connect_readonly(self.db)
        try:
            headers, rows = run_query(ro, "SELECT id, path FROM docs")
            self.assertEqual(headers, ["id", "path"])
            self.assertEqual(len(rows), 1)
            with self.assertRaises(sqlite3.DatabaseError):
                ro.execute("DELETE FROM roots")
        finally:
            ro.close()
        self.store = Store.open(self.db, actor="test")

    def test_exclude_and_unmanaged(self) -> None:
        (self.root / "archive").mkdir()
        shutil.copy(SPEC, self.root / "archive" / "old.md")
        (self.root / "plain.md").write_text("# no header\n", encoding="utf-8")
        report = self.store.scan([self.root], exclude=["archive/**"])
        self.assertEqual(report.indexed, 1)
        self.assertEqual(report.unmanaged, 1)

    def test_observe_outside_root(self) -> None:
        outside = self.tmp / "elsewhere.md"
        shutil.copy(SPEC, outside)
        self.assertIsNone(self.store.observe(outside))
        self.store.add_root(self.root)
        self.assertEqual(self.store.observe(self.root / "spec.md").indexed, 1)

    def _aid(self) -> str:
        return self.store.conn.execute("SELECT id FROM artifacts").fetchone()[0]


class TestSearchIndex(StoreTestCase):
    def setUp(self) -> None:
        super().setUp()
        shutil.copy(SPEC, self.root / "spec.md")

    def search(self, words: str) -> list[str]:
        sql = ("SELECT l.rel_path FROM search JOIN locations l ON l.id = search.rowid"
               " WHERE search MATCH ? ORDER BY l.rel_path")
        return [r[0] for r in self.store.conn.execute(sql, (fts_query(words),))]

    def test_title_and_body_are_searchable(self) -> None:
        self.store.scan([self.root])
        self.assertTrue(self.store.search)
        self.assertEqual(self.search("normative specification"), ["spec.md"])
        self.assertEqual(self.search("restricted yaml subset"), ["spec.md"])
        self.assertEqual(self.search("zebraquokka"), [])

    def test_changed_file_refreshes_and_missing_file_leaves_index(self) -> None:
        self.store.scan([self.root])
        with (self.root / "spec.md").open("a", encoding="utf-8") as fh:
            fh.write("\nzebraquokka\n")
        self.store.scan([self.root])
        self.assertEqual(self.search("zebraquokka"), ["spec.md"])
        (self.root / "spec.md").unlink()
        self.store.scan([self.root])
        self.assertEqual(self.search("zebraquokka"), [])
        self.assertEqual(self.count("SELECT count(*) FROM search"), 0)

    def test_unchanged_file_is_skipped_but_missing_row_is_backfilled(self) -> None:
        self.store.scan([self.root])
        self.assertEqual(self.store.scan([self.root]).unchanged, 1)
        self.store.conn.execute("DELETE FROM search")
        self.store.conn.commit()
        report = self.store.scan([self.root])
        self.assertEqual((report.indexed, report.new_revisions), (1, 0))
        self.assertEqual(self.search("normative"), ["spec.md"])

    def test_version_1_registry_migrates(self) -> None:
        self.store.close()
        conn = sqlite3.connect(self.db)
        conn.execute("DROP TABLE search")
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
        conn.close()
        self.store = Store.open(self.db, actor="test")
        self.assertEqual(self.count("PRAGMA user_version"), DB_USER_VERSION)
        self.assertEqual(self.count("SELECT count(*) FROM sqlite_master WHERE name = 'search'"), 1)

    def test_sidecar_host_text(self) -> None:
        def body(host: bytes) -> str:
            doc = D.Document(Path("a.bin"), Path("a.bin.somnus.yaml"), SIDECAR, [], [], False, host_bytes=host)
            return searchable_body(doc)
        self.assertEqual(body(b"\xef\xbb\xbfhello"), "hello")
        self.assertEqual(body(b"\xff\xfe\x00binary"), "")
        self.assertEqual(len(body(b"x" * (SEARCH_BODY_LIMIT + 10))), SEARCH_BODY_LIMIT)


class TestFtsQuery(unittest.TestCase):
    def test_words_are_quoted_and_required(self) -> None:
        self.assertEqual(fts_query("host  bytes"), '"host" "bytes"')
        self.assertEqual(fts_query('pre* "x" a-b'), '"pre"* """x""" "a-b"')
        self.assertEqual(fts_query(" * ** "), "")


class TestHelpers(unittest.TestCase):
    def test_globs(self) -> None:
        pats = [glob_regex(p) for p in ("archive/**", "**/__pycache__/**", "*.tmp")]
        self.assertTrue(matches_any("archive/x/y.md", pats))
        self.assertTrue(matches_any("src/a/__pycache__/m.pyc", pats))
        self.assertTrue(matches_any("x.tmp", pats))
        self.assertFalse(matches_any("dir/x.tmp", pats))
        self.assertFalse(matches_any("src/archive.md", pats))

    def test_interval_overlap(self) -> None:
        a = {"basis": "bounded", "from": "2024-01-01T00:00:00Z", "until": "2025-01-01T00:00:00Z"}
        b = {"basis": "open", "from": "2025-01-01T00:00:00Z"}
        c = {"basis": "open", "from": "2024-06-01T00:00:00Z"}
        self.assertFalse(intervals_overlap(a, b))
        self.assertTrue(intervals_overlap(a, c))
        self.assertTrue(intervals_overlap(a, {"basis": "unknown"}))


if __name__ == "__main__":
    unittest.main()
