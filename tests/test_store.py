"""Registry store: indexing semantics of SPEC §18.3."""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from somnus import DB_USER_VERSION
from somnus import document as D
from somnus.db import Store, connect_readonly, glob_regex, matches_any, run_query
from somnus.carriers.sidecar import SIDECAR
from somnus.db.store import SEARCH_BODY_LIMIT, fts_query, intervals_overlap, searchable_body
from somnus.output import SomnusError

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


class _NoFts5:
    """Connection stand-in whose ``executescript`` fails like a SQLite built without FTS5."""

    def __init__(self, conn: sqlite3.Connection, message: str) -> None:
        self._conn = conn
        self._message = message

    def executescript(self, script: str) -> None:
        raise sqlite3.OperationalError(self._message)


class TestOpenFailures(StoreTestCase):
    def test_registry_newer_than_the_tool_is_refused_untouched(self) -> None:
        self.store.close()
        conn = sqlite3.connect(self.db)
        conn.execute(f"PRAGMA user_version = {DB_USER_VERSION + 1}")
        conn.commit()
        conn.close()
        with self.assertRaises(SomnusError) as cm:
            Store.open(self.db, actor="test")
        self.assertEqual(cm.exception.exit_code, 2)
        self.assertEqual([d.code for d in cm.exception.diagnostics], ["E_IO"])
        self.assertIn("newer than this tool", str(cm.exception))
        check = sqlite3.connect(self.db)
        try:
            self.assertEqual(check.execute("PRAGMA user_version").fetchone()[0], DB_USER_VERSION + 1)
        finally:
            check.close()
        self.store = Store.open(self.tmp / "fresh" / "somnus.db", actor="test")

    def test_file_that_is_not_a_database_is_an_io_error_with_its_cause(self) -> None:
        junk = self.tmp / "junk.db"
        junk.write_bytes(b"this is not a sqlite database" * 64)
        with self.assertRaises(SomnusError) as cm:
            Store.open(junk, actor="test")
        self.assertEqual(cm.exception.exit_code, 2)
        self.assertIn("cannot open registry", str(cm.exception))
        self.assertIsInstance(cm.exception.__cause__, sqlite3.Error)

    def refused_open_connections(self, path: Path) -> list[sqlite3.Connection]:
        """Connections created by a ``Store.open`` that is expected to fail."""
        opened: list[sqlite3.Connection] = []
        real_connect = sqlite3.connect

        def tracking(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            opened.append(conn)
            return conn

        with mock.patch.object(sqlite3, "connect", tracking):
            with self.assertRaises(SomnusError):
                Store.open(path, actor="test")
        return opened

    def test_refused_open_releases_its_connection(self) -> None:
        self.store.close()
        conn = sqlite3.connect(self.db)
        conn.execute(f"PRAGMA user_version = {DB_USER_VERSION + 1}")
        conn.commit()
        conn.close()
        junk = self.tmp / "junk.db"
        junk.write_bytes(b"this is not a sqlite database" * 64)
        for path in (self.db, junk):
            opened = self.refused_open_connections(path)
            self.assertEqual(len(opened), 1, path)
            with self.assertRaises(sqlite3.ProgrammingError, msg=f"{path} connection still open"):
                opened[0].execute("SELECT 1")
        self.store = Store.open(self.tmp / "fresh" / "somnus.db", actor="test")

    def test_readonly_connect_failure_releases_its_connection(self) -> None:
        real_connect = sqlite3.connect
        opened: list[sqlite3.Connection] = []

        class Refusing:
            def __init__(self, conn: sqlite3.Connection) -> None:
                self.conn = conn
                opened.append(conn)

            def execute(self, sql: str) -> None:
                raise sqlite3.OperationalError("attempt to write a readonly database")

            def close(self) -> None:
                self.conn.close()

        with mock.patch.object(sqlite3, "connect", lambda *a, **k: Refusing(real_connect(*a, **k))):
            with self.assertRaises(SomnusError) as cm:
                connect_readonly(self.db)
        self.assertEqual(cm.exception.exit_code, 2)
        self.assertIsInstance(cm.exception.__cause__, sqlite3.OperationalError)
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].execute("SELECT 1")

    def test_readonly_connect_to_a_missing_registry_names_init(self) -> None:
        with self.assertRaises(SomnusError) as cm:
            connect_readonly(self.tmp / "nowhere" / "somnus.db")
        self.assertIn("somnus init", str(cm.exception))

    def test_sqlite_without_fts5_degrades_to_no_text_search(self) -> None:
        real = self.store.conn
        self.store.conn = _NoFts5(real, "no such module: fts5")
        try:
            self.store._ensure_search()
            self.assertFalse(self.store.search)
            self.assertTrue(self.store._search_current(1), "nothing to backfill without an index")
        finally:
            self.store.conn = real

    def test_other_search_ddl_failures_are_not_swallowed(self) -> None:
        real = self.store.conn
        self.store.conn = _NoFts5(real, "disk I/O error")
        try:
            with self.assertRaises(sqlite3.OperationalError):
                self.store._ensure_search()
        finally:
            self.store.conn = real


class TestScanFailures(StoreTestCase):
    def test_undecodable_file_is_counted_invalid_with_a_diagnostic(self) -> None:
        (self.root / "bad.md").write_bytes(b"\xff\xfe\x00")
        shutil.copy(SPEC, self.root / "spec.md")
        report = self.store.scan([self.root])
        self.assertEqual((report.invalid, report.indexed), (1, 1))
        self.assertEqual([d.code for d in report.diagnostics], ["E_IO"])
        self.assertEqual(self.count("SELECT count(*) FROM locations"), 1)

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symlink support")
    def test_unstatable_file_is_reported_and_the_scan_continues(self) -> None:
        try:
            os.symlink(self.root / "nowhere.md", self.root / "dangling.md")
        except OSError as exc:
            self.skipTest(f"cannot create symlinks: {exc}")
        shutil.copy(SPEC, self.root / "spec.md")
        report = self.store.scan([self.root])
        self.assertEqual((report.invalid, report.indexed), (1, 1))
        self.assertEqual([d.code for d in report.diagnostics], ["E_IO"])

    def test_root_that_is_not_a_directory_is_reported(self) -> None:
        gone = self.tmp / "gone"
        report = self.store.scan([gone])
        self.assertEqual([d.message for d in report.diagnostics], ["root is not a directory"])
        self.assertEqual(report.indexed, 0)

    def test_unreadable_stored_header_is_reported_not_fatal(self) -> None:
        shutil.copy(SPEC, self.root / "spec.md")
        self.store.scan([self.root])
        self.store.conn.execute("UPDATE artifacts SET standing = 'accepted'")
        self.store.conn.execute("UPDATE revisions SET header_yaml = 'unrelated: 1\n'")
        self.store.conn.commit()
        report = self.store.scan([self.root])
        codes = [d.code for d in report.diagnostics]
        self.assertIn("E_AUTHORITY", codes)
        message = next(d.message for d in report.diagnostics if d.code == "E_AUTHORITY")
        self.assertIn("unreadable", message)


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
