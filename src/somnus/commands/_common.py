"""Shared command context: configuration, output, registry access, and header commits."""

from __future__ import annotations

import contextlib
import difflib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Iterator, Literal, Optional, Sequence

from somnus import CORE_SCHEMA, carriers, config, ids
from somnus import document as D
from somnus.db import Store, connect_readonly, glob_regex, matches_any
from somnus.infer import infer
from somnus.model.validate import Resolver, validate, validate_payload
from somnus.output import EXIT_USAGE, Diagnostic, SomnusError, emit, render, table

_COLORS = {"error": "\x1b[31m", "warning": "\x1b[33m"}

# Informational notes normally go to stderr. The terminal UI installs a sink for the
# duration of its alternate-screen session so registry diagnostics reach its status
# line instead of being written over the frame (issue #3).
_note_sink: Optional[Callable[[str], None]] = None


def _enable_vt() -> bool:
    if sys.platform != "win32":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError):
        return False


@dataclass
class Ctx:
    """Per-invocation state shared by every command."""

    actor_override: Optional[str] = None
    tsv: bool = False
    no_color: bool = False
    debug: bool = False
    _cfg: Optional[config.Config] = field(default=None, repr=False)
    _color: Optional[bool] = field(default=None, repr=False)

    # ------------------------------------------------------------- config
    @property
    def cfg(self) -> config.Config:
        """Resolved configuration (cwd-based); errors become exit 2."""
        if self._cfg is None:
            try:
                self._cfg = config.load(Path.cwd(), actor=self.actor_override)
            except config.ConfigError as exc:
                raise SomnusError([Diagnostic("-", 0, 0, "error", "E_IO", "-", str(exc))], EXIT_USAGE) from exc
        return self._cfg

    @property
    def actor(self) -> str:
        """Actor name recorded in the event ledger."""
        return self.cfg.actor

    @property
    def fmt(self) -> Literal["text", "tsv"]:
        """Output format: ``text`` or ``tsv``."""
        return "tsv" if self.tsv else "text"

    # ------------------------------------------------------------- output
    @property
    def color(self) -> bool:
        """Whether ANSI color is used on stdout."""
        if self._color is None:
            self._color = (not self.no_color and not self.tsv and "NO_COLOR" not in os.environ
                           and sys.stdout.isatty() and _enable_vt())
        return self._color

    def diagnostics(self, diags: Sequence[Diagnostic]) -> None:
        """Print diagnostics in text or TSV form."""
        text = render(diags, self.fmt)
        if self.color and text:
            for severity, code in _COLORS.items():
                text = text.replace(f": {severity} ", f": {code}{severity}\x1b[0m ")
        emit(text)

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
        """Print an aligned table (or TSV with a header row)."""
        if rows or self.tsv:
            emit(table(headers, rows, self.fmt))
        else:
            note("no rows")

    # ------------------------------------------------------------- registry
    def registry_exists(self) -> bool:
        """True when the global registry database exists."""
        return self.cfg.db_path.exists()

    def store(self) -> Store:
        """Open the registry for writing; it must already exist."""
        return Store.open(self.cfg.db_path, actor=self.actor, create=False)

    def readonly(self):
        """Open the registry read-only."""
        return connect_readonly(self.cfg.db_path)

    def resolver(self) -> Resolver:
        """Registry-backed resolver, or an empty one when no registry exists."""
        if not self.registry_exists():
            return Resolver()
        conn = self.readonly()
        try:
            return Store(conn, self.cfg.db_path, self.actor).resolver()
        finally:
            conn.close()

    def record(self, action: str, path: Path, artifact_id: Optional[str] = None,
               revision: Optional[int] = None, detail: Optional[str] = None,
               resolve: Sequence[str] = ()) -> None:
        """Log a mutating action and re-observe the file when a registry exists."""
        if not self.registry_exists():
            return
        with self.store() as st:
            st.log(action, artifact_id, revision, path_text(path), detail)
            if resolve and artifact_id:
                st.resolve_conflicts(list(resolve), artifact_id=artifact_id, reason=action)
            report = st.observe(path)
            if report is not None:
                for d in report.diagnostics:
                    if d.is_error:
                        note(f"registry: {d.code} {d.message}")


def note(message: str) -> None:
    """Write an informational line to stderr, or to the active sink when one is installed."""
    text = message.rstrip("\n")
    sink = _note_sink
    if sink is not None:
        sink(text)
        return
    sys.stderr.write(text + "\n")


@contextlib.contextmanager
def capture_notes(sink: Callable[[str], None]) -> Iterator[None]:
    """Route :func:`note` output to ``sink`` for the duration of the block.

    The terminal UI uses this so a registry diagnostic produced during a save is shown
    in the active screen's status line rather than drawn over the alternate screen.
    Ordinary commands never install a sink and keep the stderr channel unchanged.
    """
    global _note_sink
    previous = _note_sink
    _note_sink = sink
    try:
        yield
    finally:
        _note_sink = previous


def path_text(path: Path) -> str:
    """Absolute POSIX-style path for ledger rows."""
    return str(Path(path).resolve()).replace("\\", "/")


def unified(old: str, new: str, path: str, old_label: Optional[str] = None) -> str:
    """Unified diff of two texts."""
    lines = difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                 fromfile=old_label or f"a/{path}", tofile=f"b/{path}")
    out = "".join(l if l.endswith(("\n", "\r")) else l + "\n\\ No newline at end of file\n" for l in lines)
    return out.replace("\r\n", "\n")


# --------------------------------------------------------------------------- documents


def load_valid(path: Path, level: str = "core") -> D.Document:
    """Load a managed document and refuse when it does not pass ``level``."""
    doc = D.load(path)
    errors = [d for d in validate(doc, level) if d.is_error]
    if errors:
        raise SomnusError(errors)
    return doc


def commit(doc: D.Document, payload: dict, style: Optional[str] = None, write: bool = True) -> str:
    """Render ``payload`` into ``doc``, validate the result at core level, and write it atomically."""
    text = doc.render(payload, style)
    check_text(doc.meta_path, text)
    if write:
        D.atomic_write(doc.meta_path, text)
    return text


def check_text(meta_path: Path, text: str) -> None:
    """Refuse text whose envelope does not pass core validation."""
    candidate = D.from_text(meta_path, text)
    errors = [d for d in validate(candidate, "core") if d.is_error]
    if errors:
        raise SomnusError(errors)


def display(path: Path) -> str:
    """Path as shown in diagnostics (relative to cwd when possible)."""
    try:
        return os.path.relpath(Path(path), Path.cwd()).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def refuse(path: Path | str, code: str, message: str, field_path: str = "-") -> SomnusError:
    """Build a refusal error anchored at a file."""
    shown = path if isinstance(path, str) else display(path)
    return SomnusError([Diagnostic(shown, 1, 1, "error", code, field_path, message)])


def new_payload(cfg: config.Config, *, title: str, type_: str, category: str, role: str, body_role: str,
                status: str = "draft", artifact_id: Optional[str] = None,
                created_at: Optional[str] = None) -> dict:
    """Build a conformant revision-1 payload from configuration defaults."""
    d = cfg.defaults
    aid = artifact_id or ids.new_artifact_urn()
    standing = d["standing"]
    if standing == "accepted":
        raise SomnusError("configured default standing 'accepted' would invent an acceptance record; "
                          "use 'candidate'", EXIT_USAGE)
    scopes = [] if standing == "unasserted" else [{"target_ref": aid, "aspects": ["content"]}]
    payload = {
        "schema": CORE_SCHEMA,
        "id": aid,
        "revision": 1,
        "title": title,
        "classification": {
            "category": category, "type": type_, "role": role, "scope": d["scope"], "tags": [],
        },
        "lifecycle": {"status": status},
        "authority": {"standing": standing, "scopes": scopes},
        "time": {"created_at": created_at} if created_at else {},
        "names": {"slug": ids.slugify(title)},
        "knowledge": {"coverage": "artifact", "subjects": [aid]},
        "access": {"visibility": d["visibility"], "allowed_uses": list(d["allowed_uses"])},
        "ingestion": {"disposition": d["disposition"], "body_role": body_role},
    }
    errors = [x for x in validate_payload(payload) if x.is_error]
    if errors:
        raise SomnusError(errors)
    return payload


def inferred_payload(cfg: config.Config, path: Path, lines: Sequence[str], *, type_: Optional[str] = None,
                     title: Optional[str] = None, status: str = "draft",
                     created_at: Optional[str] = None) -> dict:
    """Payload whose classification is inferred from the file."""
    guess = infer(path, lines, type_override=type_, title_override=title)
    return new_payload(cfg, title=guess.title, type_=guess.type, category=guess.category, role=guess.role,
                       body_role=guess.body_role, status=status, created_at=created_at)


# --------------------------------------------------------------------------- file discovery


def is_candidate(path: Path) -> bool:
    """A file that can carry metadata (embedded carrier or sidecar)."""
    return carriers.is_sidecar_path(path) or carriers.for_path(path) is not None


def walk(roots: Iterable[Path], exclude: Sequence[str]) -> Iterator[Path]:
    """Yield candidate files under ``roots`` honoring exclude globs (hosts with sidecars yield the sidecar)."""
    patterns = [glob_regex(p) for p in exclude]
    seen: set[Path] = set()
    for root in roots:
        root = Path(root).resolve()
        if root.is_file():
            if root not in seen:
                seen.add(root)
                yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            here = Path(dirpath)
            rel_dir = Path(os.path.relpath(here, root)).as_posix()
            prefix = "" if rel_dir == "." else rel_dir + "/"
            dirnames[:] = sorted(n for n in dirnames
                                 if n not in (".git", ".hg", ".svn") and not matches_any(prefix + n + "/", patterns))
            names = set(filenames)
            for name in sorted(filenames):
                if matches_any(prefix + name, patterns):
                    continue
                path = here / name
                if not carriers.is_sidecar_path(path):
                    if name + carriers.SIDECAR_SUFFIX in names or carriers.for_path(path) is None:
                        continue
                if path not in seen:
                    seen.add(path)
                    yield path
