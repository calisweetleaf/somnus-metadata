"""Global SQLite registry: open/migrate, indexing, conflicts, and read-only queries (SPEC §18)."""

from __future__ import annotations

import difflib
import os
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Iterable, Optional, Sequence

from somnus import DB_USER_VERSION, carriers, ids, yamlsub
from somnus import document as D
from somnus.model import vocab
from somnus.model.validate import ArtifactFacts, Resolver, find_cycle, validate
from somnus.output import EXIT_USAGE, Diagnostic, SomnusError

_PRUNE_DIRS = {".git", ".hg", ".svn"}


def now_iso() -> str:
    """Current UTC instant as an RFC 3339 timestamp with a ``Z`` offset."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _io_error(message: str) -> SomnusError:
    return SomnusError([Diagnostic("-", 0, 0, "error", "E_IO", "-", message)], EXIT_USAGE)


# --------------------------------------------------------------------------- full-text search (D19)

SEARCH_BODY_LIMIT = 1_000_000  # characters of host text indexed per location


def searchable_body(doc: D.Document) -> str:
    """Host text outside the envelope, truncated to ``SEARCH_BODY_LIMIT``; empty for non-UTF-8 sidecar hosts."""
    if doc.is_sidecar:
        try:
            text = (doc.host_bytes or b"").decode("utf-8-sig")
        except UnicodeDecodeError:
            return ""
    else:
        text = "\n".join(doc.body_lines())
    return text[:SEARCH_BODY_LIMIT]


def fts_query(words: str) -> str:
    """Plain search words as an FTS5 query: every word is required and ``word*`` matches a prefix."""
    terms = []
    for word in words.split():
        core = word.rstrip("*")
        if core:
            terms.append('"' + core.replace('"', '""') + '"' + ("*" if word.endswith("*") else ""))
    return " ".join(terms)


# --------------------------------------------------------------------------- globs


def glob_regex(pattern: str) -> re.Pattern:
    """Compile a path glob (``**`` crosses directories, ``*`` and ``?`` do not)."""
    out = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(out + r"\Z")


def matches_any(rel_path: str, patterns: Sequence[re.Pattern]) -> bool:
    """True when a POSIX relative path matches any compiled glob."""
    return any(p.match(rel_path) for p in patterns)


def _rel(path: Path, root: Path) -> str:
    return Path(os.path.relpath(path, root)).as_posix()


def _join(root: str, rel_path: str) -> str:
    return root.rstrip("/\\") + "/" + rel_path


# --------------------------------------------------------------------------- reports


@dataclass
class ScanReport:
    """Outcome of one reconciliation pass."""

    scanned: int = 0
    indexed: int = 0
    unchanged: int = 0
    unmanaged: int = 0
    examples: int = 0
    invalid: int = 0
    missing: int = 0
    new_revisions: int = 0
    conflicts_opened: int = 0
    conflicts_resolved: int = 0
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def summary(self) -> str:
        """One-line plain-English summary."""
        return (f"scanned {self.scanned}, indexed {self.indexed}, unchanged {self.unchanged}, "
                f"new revisions {self.new_revisions}, unmanaged {self.unmanaged}, examples {self.examples}, "
                f"invalid {self.invalid}, missing {self.missing}, conflicts opened {self.conflicts_opened}, "
                f"resolved {self.conflicts_resolved}")


# --------------------------------------------------------------------------- intervals


def _instant(value: Optional[str]) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _interval(vt: object) -> tuple[Optional[datetime], Optional[datetime]]:
    """Half-open interval; ``None`` bounds are unbounded (unknown extent cannot prove disjointness)."""
    if not isinstance(vt, dict):
        return (None, None)
    basis = vt.get("basis")
    if basis == "bounded":
        return (_instant(vt.get("from")), _instant(vt.get("until")))
    if basis == "open":
        return (_instant(vt.get("from")), None)
    return (None, None)


def intervals_overlap(a: object, b: object) -> bool:
    """True when two valid_time objects can overlap."""
    a_start, a_end = _interval(a)
    b_start, b_end = _interval(b)
    if a_end is not None and b_start is not None and not b_start < a_end:
        return False
    if b_end is not None and a_start is not None and not a_start < b_end:
        return False
    return True


# --------------------------------------------------------------------------- store


class Store:
    """Connection to the global registry with indexing and query helpers."""

    def __init__(self, conn: sqlite3.Connection, path: Path, actor: str):
        self.conn = conn
        self.path = path
        self.actor = actor
        self.search = False  # set by _ensure_search when the FTS5 index exists

    # ------------------------------------------------------------- lifecycle
    @classmethod
    def open(cls, db_path: Path, actor: str = "operator", create: bool = True) -> "Store":
        """Open (and when ``create``, create or migrate) the registry database."""
        db_path = Path(db_path)
        if not db_path.exists():
            if not create:
                raise _io_error(f"registry {db_path} does not exist; run 'somnus init'")
            db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = sqlite3.connect(str(db_path), timeout=10)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            store = cls(conn, db_path, actor)
            store._migrate()
        except sqlite3.Error as exc:
            raise _io_error(f"cannot open registry {db_path}: {exc}") from exc
        return store

    def _migrate(self) -> None:
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version > DB_USER_VERSION:
            raise _io_error(f"registry schema version {version} is newer than this tool ({DB_USER_VERSION})")
        if version < DB_USER_VERSION:
            ddl = resources.files("somnus.db").joinpath("schema.sql").read_text(encoding="utf-8")
            self.conn.executescript(ddl)
            self.conn.execute(f"PRAGMA user_version = {DB_USER_VERSION}")
            self.conn.commit()
        self._ensure_search()

    def _ensure_search(self) -> None:
        # Builds of SQLite without FTS5 still get a working registry; only `q --text` is unavailable.
        ddl = resources.files("somnus.db").joinpath("search.sql").read_text(encoding="utf-8")
        try:
            self.conn.executescript(ddl)
        except sqlite3.OperationalError as exc:
            if "fts5" not in str(exc).lower():
                raise
            self.search = False
            return
        self.search = True

    def _search_current(self, loc_id: int) -> bool:
        """True when the location's full-text row exists (or no index is available to fill)."""
        if not self.search:
            return True
        return self.conn.execute("SELECT 1 FROM search WHERE rowid = ?", (loc_id,)).fetchone() is not None

    def _index_text(self, loc_id: int, path_text: str, doc: D.Document, somnus: dict) -> None:
        """Replace the location's full-text row with the file as observed now."""
        if not self.search:
            return
        self.conn.execute("DELETE FROM search WHERE rowid = ?", (loc_id,))
        self.conn.execute(
            "INSERT INTO search (rowid, path, title, summary, tags, body) VALUES (?, ?, ?, ?, ?, ?)",
            (loc_id, path_text, somnus["title"], somnus.get("summary", ""),
             " ".join(somnus["classification"].get("tags", [])), searchable_body(doc)),
        )

    def close(self) -> None:
        """Commit pending work and close the connection."""
        self.conn.commit()
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.conn.rollback()
        self.close()

    # ------------------------------------------------------------- ledger
    def log(self, action: str, artifact_id: Optional[str] = None, revision: Optional[int] = None,
            path: Optional[str] = None, detail: Optional[str] = None) -> None:
        """Append one row to the append-only event ledger."""
        self.conn.execute(
            "INSERT INTO events (at, actor, action, artifact_id, revision, path, detail) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (now_iso(), self.actor, action, artifact_id, revision, path, detail),
        )

    # ------------------------------------------------------------- roots
    def add_root(self, path: Path) -> int:
        """Register a root directory (idempotent); return its id."""
        resolved = Path(path).resolve().as_posix()
        row = self.conn.execute("SELECT id FROM roots WHERE path = ?", (resolved,)).fetchone()
        if row:
            return int(row[0])
        cur = self.conn.execute("INSERT INTO roots (path, added_at) VALUES (?, ?)", (resolved, now_iso()))
        self.log("root.add", path=resolved)
        self.conn.commit()
        new_id = cur.lastrowid
        assert new_id is not None  # sqlite3 assigns lastrowid on INSERT
        return new_id

    def roots(self) -> list[tuple[int, Path]]:
        """Registered roots as ``(id, path)``."""
        return [(r[0], Path(r[1])) for r in self.conn.execute("SELECT id, path FROM roots ORDER BY path")]

    def root_for(self, path: Path) -> Optional[tuple[int, Path]]:
        """The deepest registered root containing ``path``."""
        path = Path(path).resolve()
        best: Optional[tuple[int, Path]] = None
        for root_id, root in self.roots():
            if path == root or root in path.parents:
                if best is None or len(root.parts) > len(best[1].parts):
                    best = (root_id, root)
        return best

    # ------------------------------------------------------------- conflicts
    def _open_conflict(self, report: ScanReport, kind: str, key: str, artifact_id: str,
                       revision: Optional[int], path: Optional[str], detail: str) -> None:
        exists = self.conn.execute(
            "SELECT 1 FROM conflicts WHERE kind = ? AND conflict_key = ? AND state = 'open'", (kind, key)
        ).fetchone()
        if exists:
            return
        self.conn.execute(
            "INSERT INTO conflicts (kind, conflict_key, artifact_id, revision, path, detail, opened_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (kind, key, artifact_id, revision, path, detail, now_iso()),
        )
        self.log("conflict.open", artifact_id, revision, path, f"{kind}: {key}")
        report.conflicts_opened += 1

    def _resolve_rows(self, rows: Iterable[tuple], reason: str, report: Optional[ScanReport] = None) -> int:
        count = 0
        for cid, kind, key, aid, rev, path in rows:
            self.conn.execute("UPDATE conflicts SET state = 'resolved', resolved_at = ? WHERE id = ?", (now_iso(), cid))
            self.log("conflict.resolve", aid, rev, path, f"{kind}: {key} ({reason})")
            count += 1
        if report is not None:
            report.conflicts_resolved += count
        return count

    def resolve_conflicts(self, kinds: Sequence[str], *, path: Optional[str] = None,
                          artifact_id: Optional[str] = None, reason: str = "operator") -> int:
        """Resolve open conflicts of ``kinds`` filtered by path and/or artifact; return the count."""
        sql = ("SELECT id, kind, conflict_key, artifact_id, revision, path FROM conflicts WHERE state = 'open'"
               f" AND kind IN ({','.join('?' * len(kinds))})")
        params: list = list(kinds)
        if path is not None:
            sql += " AND path = ?"
            params.append(path)
        if artifact_id is not None:
            sql += " AND artifact_id = ?"
            params.append(artifact_id)
        count = self._resolve_rows(self.conn.execute(sql, params).fetchall(), reason)
        self.conn.commit()
        return count

    # ------------------------------------------------------------- indexing
    def scan(self, roots: Optional[Iterable[Path]] = None, exclude: Sequence[str] = (),
             full: bool = False) -> ScanReport:
        """Reconcile roots (default: all registered) into the registry."""
        report = ScanReport()
        patterns = [glob_regex(p) for p in exclude]
        targets = [(self.add_root(r), Path(r).resolve()) for r in roots] if roots else self.roots()
        for root_id, root in targets:
            if not root.is_dir():
                report.diagnostics.append(Diagnostic(str(root), 0, 0, "error", "E_IO", "-", "root is not a directory"))
                continue
            seen: set[str] = set()
            for dirpath, dirnames, filenames in os.walk(root):
                here = Path(dirpath)
                rel_dir = _rel(here, root)
                prefix = "" if rel_dir == "." else rel_dir + "/"
                dirnames[:] = sorted(d for d in dirnames
                                     if d not in _PRUNE_DIRS and not matches_any(prefix + d + "/", patterns))
                names = set(filenames)
                for name in sorted(filenames):
                    rel = prefix + name
                    if matches_any(rel, patterns):
                        continue
                    file_path = here / name
                    if carriers.is_sidecar_path(file_path):
                        pass
                    elif name + carriers.SIDECAR_SUFFIX in names or carriers.for_path(file_path) is None:
                        continue
                    host_rel = self._visit(root_id, root, file_path, full, report)
                    if host_rel is not None:
                        seen.add(host_rel)
            self._mark_missing(root_id, root, seen, report)
            self.conn.execute("UPDATE roots SET last_scan_at = ? WHERE id = ?", (now_iso(), root_id))
            self.conn.commit()
        self._reconcile(report)
        self.log("index", detail=report.summary())
        self.conn.commit()
        return report

    def observe(self, path: Path) -> Optional[ScanReport]:
        """Index one file when it lies under a registered root; None otherwise."""
        path = Path(path).resolve()
        if carriers.is_sidecar_path(path):
            meta = path
        else:
            sidecar = carriers.sidecar_for(path)
            meta = sidecar if sidecar.exists() else path
        found = self.root_for(meta)
        if found is None:
            return None
        report = ScanReport()
        self._visit(found[0], found[1], meta, True, report)
        self._reconcile(report)
        self.conn.commit()
        return report

    def _visit(self, root_id: int, root: Path, file_path: Path, full: bool, report: ScanReport) -> Optional[str]:
        """Index one file; return the host rel_path when the location is still observed."""
        is_side = carriers.is_sidecar_path(file_path)
        host = carriers.host_for(file_path) if is_side else file_path
        host_rel = _rel(host, root)
        report.scanned += 1
        try:
            st = file_path.stat()
            mtime, size = st.st_mtime, st.st_size
            if is_side and host.is_file():
                hst = host.stat()
                mtime, size = max(mtime, hst.st_mtime), size + hst.st_size
        except OSError as exc:
            report.diagnostics.append(Diagnostic(str(file_path), 0, 0, "error", "E_IO", "-", exc.strerror or str(exc)))
            report.invalid += 1
            return host_rel
        loc = self.conn.execute(
            "SELECT id, present, file_mtime, file_size FROM locations WHERE root_id = ? AND rel_path = ?",
            (root_id, host_rel),
        ).fetchone()
        if (not full and loc is not None and loc[1] == 1 and loc[2] == mtime and loc[3] == size
                and self._search_current(loc[0])):
            report.unchanged += 1
            return host_rel
        try:
            doc = D.load(file_path)
        except SomnusError as exc:
            report.diagnostics.extend(exc.diagnostics)
            report.invalid += 1
            return host_rel
        if doc.envelope is None and not doc.issues:
            report.unmanaged += 1
            return None
        problems = [d for d in validate(doc, "core") if d.is_error]
        if problems:
            report.diagnostics.extend(problems)
            report.invalid += 1
            return host_rel
        somnus = doc.payload
        if somnus is None:
            report.diagnostics.append(Diagnostic(str(file_path), 0, 0, "error", "E_ENVELOPE", "-",
                                                 "no metadata envelope found"))
            report.invalid += 1
            return host_rel
        if ids.is_example_urn(somnus["id"]):
            report.examples += 1
            return None
        self._index_document(root_id, root, host_rel, doc, somnus, mtime, size, report)
        report.indexed += 1
        self.conn.commit()
        return host_rel

    def _index_document(self, root_id: int, root: Path, rel_path: str, doc: D.Document, somnus: dict,
                        mtime: float, size: int, report: ScanReport) -> None:
        aid = somnus["id"]
        rev = somnus["revision"]
        header = D.canonical_yaml(doc.data or {})
        pd, bd = doc.payload_digest(), doc.body_digest()
        now = now_iso()
        path_text = _join(root.as_posix(), rel_path)
        cls = somnus["classification"]
        fields = (somnus["title"], cls["type"], cls["category"], cls["role"], cls["scope"],
                  somnus["lifecycle"]["status"], somnus["authority"]["standing"], somnus["access"]["visibility"])

        art = self.conn.execute("SELECT current_revision FROM artifacts WHERE id = ?", (aid,)).fetchone()
        if art is None:
            self.conn.execute(
                "INSERT INTO artifacts (id, title, type, category, role, scope, status, standing, visibility,"
                " current_revision, first_seen_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (aid, *fields, rev, now, now),
            )
            current = 0
        else:
            current = art[0]

        stored = self.conn.execute(
            "SELECT payload_digest, body_digest FROM revisions WHERE artifact_id = ? AND revision = ?", (aid, rev)
        ).fetchone()
        revision_key = f"{aid}#{rev}@{path_text}"
        conflicting = False
        if stored is None:
            self.conn.execute(
                "INSERT INTO revisions (artifact_id, revision, title, status, standing, header_yaml,"
                " payload_digest, body_digest, observed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (aid, rev, somnus["title"], fields[5], fields[6], header, pd, bd, now),
            )
            self._materialize(aid, rev, somnus)
            self.log("observe", aid, rev, path_text, "new revision")
            report.new_revisions += 1
        elif stored != (pd, bd):
            conflicting = True
            self._open_conflict(report, "revision", revision_key, aid, rev, path_text,
                                "candidate state differs from stored revision; candidate header:\n" + header)
        stale = self.conn.execute(
            "SELECT id, kind, conflict_key, artifact_id, revision, path FROM conflicts"
            " WHERE kind = 'revision' AND state = 'open' AND path = ? AND conflict_key != ?",
            (path_text, revision_key if conflicting else ""),
        ).fetchall()
        self._resolve_rows(stale, "no longer observed", report)

        if not conflicting and rev >= current:
            self.conn.execute(
                "UPDATE artifacts SET title = ?, type = ?, category = ?, role = ?, scope = ?, status = ?,"
                " standing = ?, visibility = ?, current_revision = ?, last_seen_at = ? WHERE id = ?",
                (*fields, rev, now, aid),
            )
            self.conn.execute("DELETE FROM tags WHERE artifact_id = ?", (aid,))
            self.conn.executemany("INSERT OR IGNORE INTO tags (artifact_id, tag) VALUES (?, ?)",
                                  [(aid, t) for t in cls.get("tags", [])])
        else:
            self.conn.execute("UPDATE artifacts SET last_seen_at = ? WHERE id = ?", (now, aid))

        loc = self.conn.execute(
            "SELECT id, artifact_id FROM locations WHERE root_id = ? AND rel_path = ?", (root_id, rel_path)
        ).fetchone()
        carrier = doc.carrier.name
        if loc is None:
            cur = self.conn.execute(
                "INSERT INTO locations (root_id, rel_path, artifact_id, revision, carrier, file_mtime, file_size,"
                " payload_digest, body_digest, present, first_seen_at, last_seen_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (root_id, rel_path, aid, rev, carrier, mtime, size, pd, bd, now, now),
            )
            loc_id = cur.lastrowid
            assert loc_id is not None  # sqlite3 assigns lastrowid on INSERT
        else:
            loc_id = loc[0]
            if loc[1] != aid:
                self._open_conflict(report, "identity", path_text, aid, rev, path_text,
                                    f"path previously held {loc[1]}; now holds {aid}")
            self.conn.execute(
                "UPDATE locations SET artifact_id = ?, revision = ?, carrier = ?, file_mtime = ?, file_size = ?,"
                " payload_digest = ?, body_digest = ?, present = 1, last_seen_at = ? WHERE id = ?",
                (aid, rev, carrier, mtime, size, pd, bd, now, loc[0]),
            )
        self._index_text(loc_id, path_text, doc, somnus)

    def _materialize(self, aid: str, rev: int, somnus: dict) -> None:
        """Write trusted knowledge rows for a new revision (extensions never feed these tables)."""
        knowledge = somnus.get("knowledge", {})
        for reg in knowledge.get("regions", []):
            self.conn.execute(
                "INSERT OR IGNORE INTO regions (artifact_id, revision, region_id, kind, selector_kind, title, standing)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (aid, rev, reg["id"], reg["kind"], reg["selector"]["kind"], reg.get("title"),
                 (reg.get("authority") or {}).get("standing")),
            )
        for rel in knowledge.get("relations", []):
            vt = rel["valid_time"]
            self.conn.execute(
                "INSERT OR IGNORE INTO relations (artifact_id, revision, relation_id, subject_ref, predicate, object_ref,"
                " object_revision, assessment, time_basis, valid_from, valid_until, known_predicate)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (aid, rev, rel["id"], rel["subject"]["ref"], rel["predicate"], rel["object"]["ref"],
                 rel["object"].get("revision"), rel["assessment"], vt["basis"], vt.get("from"), vt.get("until"),
                 1 if rel["predicate"] in vocab.RELATION_PREDICATES else 0),
            )
        for ent in knowledge.get("entities", []):
            self.conn.execute(
                "INSERT OR IGNORE INTO entities (artifact_id, revision, ref, label, kind) VALUES (?, ?, ?, ?, ?)",
                (aid, rev, ent["ref"], ent["label"], ent["kind"]),
            )
        for claim in knowledge.get("claims", []):
            self.conn.execute(
                "INSERT OR IGNORE INTO claims (artifact_id, revision, claim_id, subject_ref, predicate, kind,"
                " assessment, statement, region_ref, object_ref) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (aid, rev, claim["id"], claim["subject_ref"], claim["predicate"], claim["kind"],
                 claim["assessment"], claim["statement"], claim["region_ref"], claim["object"].get("ref")),
            )

    def _mark_missing(self, root_id: int, root: Path, seen: set[str], report: ScanReport) -> None:
        rows = self.conn.execute(
            "SELECT id, rel_path, artifact_id, revision FROM locations WHERE root_id = ? AND present = 1", (root_id,)
        ).fetchall()
        for loc_id, rel_path, aid, rev in rows:
            if rel_path in seen:
                continue
            path_text = _join(root.as_posix(), rel_path)
            self.conn.execute("UPDATE locations SET present = 0 WHERE id = ?", (loc_id,))
            if self.search:
                self.conn.execute("DELETE FROM search WHERE rowid = ?", (loc_id,))
            self.log("missing", aid, rev, path_text, "not observed during scan")
            report.missing += 1
            stale = self.conn.execute(
                "SELECT id, kind, conflict_key, artifact_id, revision, path FROM conflicts"
                " WHERE kind = 'revision' AND state = 'open' AND path = ?", (path_text,)
            ).fetchall()
            self._resolve_rows(stale, "location no longer observed", report)

    # ------------------------------------------------------------- registry-wide reconciliation
    def _reconcile(self, report: ScanReport) -> None:
        self._reconcile_duplicates(report)
        self._reconcile_authority(report)
        report.diagnostics.extend(self.graph_cycles())

    def _present_paths(self) -> dict[str, list[tuple[str, str, str]]]:
        out: dict[str, list[tuple[str, str, str]]] = {}
        for aid, rel_path, root, pd, bd in self.conn.execute(
            "SELECT l.artifact_id, l.rel_path, r.path, l.payload_digest, l.body_digest"
            " FROM locations l JOIN roots r ON r.id = l.root_id WHERE l.present = 1"
        ):
            out.setdefault(aid, []).append((_join(root, rel_path), pd, bd))
        return out

    def _reconcile_duplicates(self, report: ScanReport) -> None:
        wanted: dict[str, str] = {}
        for aid, locs in self._present_paths().items():
            if len({(pd, bd) for _, pd, bd in locs}) > 1:
                wanted[aid] = ", ".join(sorted(p for p, _, _ in locs))
        open_rows = self.conn.execute(
            "SELECT id, kind, conflict_key, artifact_id, revision, path FROM conflicts"
            " WHERE kind = 'duplicate-id' AND state = 'open'"
        ).fetchall()
        self._resolve_rows([r for r in open_rows if r[2] not in wanted], "mirrors now identical or gone", report)
        for aid, paths in wanted.items():
            self._open_conflict(report, "duplicate-id", aid, aid, None, None,
                                f"distinct states at: {paths}")

    def _accepted_scopes(self, report: ScanReport) -> list[tuple[str, list, object]]:
        out = []
        for aid, header in self.conn.execute(
            "SELECT a.id, r.header_yaml FROM artifacts a"
            " JOIN revisions r ON r.artifact_id = a.id AND r.revision = a.current_revision"
            " WHERE a.standing = 'accepted'"
            " AND EXISTS (SELECT 1 FROM locations l WHERE l.artifact_id = a.id AND l.present = 1)"
            " ORDER BY a.id"
        ):
            try:
                authority = yamlsub.parse(header).data["somnus"]["authority"]
            except (yamlsub.YAMLError, KeyError, TypeError) as exc:
                report.diagnostics.append(Diagnostic("-", 0, 0, "error", "E_AUTHORITY", "-",
                                                     f"stored header for {aid} is unreadable; authority overlap"
                                                     f" not checked for it: {exc}"))
                continue
            out.append((aid, authority.get("scopes", []), authority.get("valid_time")))
        return out

    def _reconcile_authority(self, report: ScanReport) -> None:
        accepted = self._accepted_scopes(report)
        wanted: dict[str, tuple[str, str]] = {}
        for i, (a_id, a_scopes, a_vt) in enumerate(accepted):
            for b_id, b_scopes, b_vt in accepted[i + 1:]:
                if not intervals_overlap(a_vt, b_vt):
                    continue
                for sa in a_scopes:
                    for sb in b_scopes:
                        if sa.get("target_ref") != sb.get("target_ref"):
                            continue
                        for aspect in sorted(set(sa.get("aspects", [])) & set(sb.get("aspects", []))):
                            target = sa["target_ref"]
                            detail = f"{a_id} and {b_id} both accepted for {target} aspect {aspect}"
                            wanted[f"{a_id}|{b_id}|{target}|{aspect}"] = (a_id, detail)
                            wanted[f"{b_id}|{a_id}|{target}|{aspect}"] = (b_id, detail)
        open_rows = self.conn.execute(
            "SELECT id, kind, conflict_key, artifact_id, revision, path FROM conflicts"
            " WHERE kind = 'authority' AND state = 'open'"
        ).fetchall()
        self._resolve_rows([r for r in open_rows if r[2] not in wanted], "overlap no longer observed", report)
        for key, (aid, detail) in wanted.items():
            self._open_conflict(report, "authority", key, aid, None, None, detail)

    def graph_cycles(self) -> list[Diagnostic]:
        """Cycles on acyclic predicates across the current revisions of present artifacts."""
        graphs: dict[str, dict[str, set[str]]] = {}
        for subject, predicate, obj in self.conn.execute(
            "SELECT rel.subject_ref, rel.predicate, rel.object_ref FROM relations rel"
            " JOIN artifacts a ON a.id = rel.artifact_id AND a.current_revision = rel.revision"
            " WHERE EXISTS (SELECT 1 FROM locations l WHERE l.artifact_id = a.id AND l.present = 1)"
        ):
            info = vocab.RELATION_PREDICATES.get(predicate)
            if info is None or not info[1]:
                continue
            graphs.setdefault(predicate, {}).setdefault(subject, set()).add(obj)
        out = []
        for predicate in sorted(graphs):
            cycle = find_cycle(graphs[predicate])
            if cycle:
                out.append(Diagnostic("-", 0, 0, "error", "E_GRAPH", "-",
                                      f"{predicate} cycle across registry: {' -> '.join(cycle)}"))
        return out

    # ------------------------------------------------------------- reads
    def resolver(self) -> Resolver:
        """Reference-resolution facts from the registry."""
        res = Resolver()
        for aid, typ, status, standing, cur in self.conn.execute(
            "SELECT id, type, status, standing, current_revision FROM artifacts"
        ):
            res.artifacts[aid] = ArtifactFacts(aid, typ, status, standing, cur)
        for aid, rev in self.conn.execute("SELECT artifact_id, revision FROM revisions"):
            facts = res.artifacts.get(aid)
            if facts is not None:
                facts.revisions.add(rev)
        for aid, rev, rid in self.conn.execute("SELECT artifact_id, revision, region_id FROM regions"):
            if aid in res.artifacts:
                res.artifacts[aid].regions.setdefault(rev, set()).add(rid)
        for aid, rev, cid in self.conn.execute("SELECT artifact_id, revision, claim_id FROM claims"):
            if aid in res.artifacts:
                res.artifacts[aid].claims.setdefault(rev, set()).add(cid)
        for (ref,) in self.conn.execute("SELECT DISTINCT ref FROM entities"):
            if not ids.is_example_urn(ref):
                res.entities.add(ref)
        for aid, kind in self.conn.execute("SELECT artifact_id, kind FROM open_conflicts"):
            res.open_conflicts.setdefault(aid, []).append(kind)
        return res

    def list_docs(self, *, type: Optional[str] = None, status: Optional[str] = None,
                  standing: Optional[str] = None, tag: Optional[str] = None,
                  path_contains: Optional[str] = None) -> list[tuple]:
        """Present artifacts as ``(id, title, type, status, standing, revision, path)`` rows."""
        sql = "SELECT id, title, type, status, standing, revision, path FROM docs WHERE 1 = 1"
        params: list = []
        for column, value in (("type", type), ("status", status), ("standing", standing)):
            if value is not None:
                sql += f" AND {column} = ?"
                params.append(value)
        if tag is not None:
            sql += " AND EXISTS (SELECT 1 FROM tags t WHERE t.artifact_id = docs.id AND t.tag = ?)"
            params.append(tag)
        if path_contains is not None:
            sql += " AND instr(path, ?) > 0"
            params.append(path_contains)
        sql += " ORDER BY path"
        return self.conn.execute(sql, params).fetchall()

    def similar_titles(self, title: str, threshold: float = 0.85,
                       exclude_id: Optional[str] = None) -> list[tuple[str, str, float]]:
        """Present artifacts whose titles are near ``title``: ``(id, title, ratio)`` best first."""
        wanted = title.casefold().strip()
        out = []
        for aid, other in self.conn.execute(
            "SELECT DISTINCT id, title FROM docs"
        ):
            if aid == exclude_id:
                continue
            ratio = difflib.SequenceMatcher(None, wanted, other.casefold().strip()).ratio()
            if ratio >= threshold:
                out.append((aid, other, ratio))
        return sorted(out, key=lambda r: (-r[2], r[1]))


# --------------------------------------------------------------------------- read-only access


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    """Open the registry read-only (``mode=ro`` plus ``query_only``)."""
    db_path = Path(db_path)
    if not db_path.exists():
        raise _io_error(f"registry {db_path} does not exist; run 'somnus init'")
    try:
        conn = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
        conn.execute("PRAGMA query_only = ON")
    except sqlite3.Error as exc:
        raise _io_error(f"cannot open registry {db_path}: {exc}") from exc
    return conn


def run_query(conn: sqlite3.Connection, sql: str, params: Sequence = (),
              limit: Optional[int] = None) -> tuple[list[str], list[tuple]]:
    """Run one read-only statement; return ``(headers, rows)``."""
    try:
        cur = conn.execute(sql, params)
    except sqlite3.Error as exc:
        raise SomnusError([Diagnostic("-", 0, 0, "error", "E_IO", "-", f"query failed: {exc}")], EXIT_USAGE) from exc
    headers = [d[0] for d in cur.description or ()]
    rows = cur.fetchmany(limit) if limit is not None else cur.fetchall()
    return headers, rows
