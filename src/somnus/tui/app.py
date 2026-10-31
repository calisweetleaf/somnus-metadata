"""Full-screen document browser and header editor behind ``somnus edit``."""

from __future__ import annotations

import copy
import os
import shlex
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from somnus.commands._common import Ctx, capture_notes, commit, load_valid
from somnus.db import Store
from somnus.model.lifecycle import bump_revision
from somnus.output import EXIT_OK, EXIT_USAGE, SomnusError
from somnus.tui.form import FIELDS, FormModel
from somnus.tui.term import Terminal, TerminalError, usable_width
from somnus.tui.widgets import ListView, Picker, TextInput, fit, highlight, split, split_widths

QUIT_KEYS = ("q", "esc", "ctrl-c")
ROW_LABELS = ("ID", "Title", "Type", "Status", "Standing", "Revision", "Path")
BROWSER_RATIO = 0.55
LABEL_WIDTH = 12


class NoteBuffer:
    """Collects informational notes so the active screen can show them instead of stderr.

    ``app.main`` installs one as the process-wide note sink for the whole alternate-screen
    session; each screen drains it into its status line before every frame.
    """

    def __init__(self) -> None:
        """Start with no notes collected."""
        self._pending: list[str] = []

    def __call__(self, message: str) -> None:
        """Accept one note; used directly as the ``capture_notes`` sink."""
        self._pending.append(message)

    def drain(self) -> str:
        """Return every note collected since the last drain, joined with ``; ``."""
        pending, self._pending = self._pending, []
        return "; ".join(pending)


def first_message(exc: SomnusError) -> str:
    """First diagnostic of ``exc`` as one line."""
    if not exc.diagnostics:
        return str(exc)
    d = exc.diagnostics[0]
    return d.message if d.field in ("", "-") else f"{d.field}: {d.message}"


def load_rows(ctx: Ctx) -> list[tuple]:
    """Registry rows ``(id, title, type, status, standing, revision, path)`` via a read-only connection."""
    if not ctx.registry_exists():
        raise SomnusError("no registry; run 'somnus init' and 'somnus index'", EXIT_USAGE)
    conn = ctx.readonly()
    try:
        return Store(conn, ctx.cfg.db_path, ctx.actor).list_docs()
    finally:
        conn.close()


def editor_command(environ: Optional[Mapping[str, str]] = None) -> list[str]:
    """Argv prefix for the body editor: ``$EDITOR``, then ``$VISUAL``, then notepad/vi."""
    env = os.environ if environ is None else environ
    raw = (env.get("EDITOR") or env.get("VISUAL") or "").strip()
    if not raw:
        return ["notepad"] if os.name == "nt" else ["vi"]
    if os.path.exists(raw):
        return [raw]
    parts = shlex.split(raw, posix=os.name != "nt")
    return [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p for p in parts] or [raw]


def render_row(row: Sequence[Any]) -> str:
    """List label for a registry row."""
    title = row[1] or "(untitled)"
    return f"{title}  [{row[2]}, {row[3]}, r{row[5]}]"


def match_row(row: Sequence[Any]) -> str:
    """Text a registry row is filtered on (every column)."""
    return " ".join("" if v is None else str(v) for v in row)


def detail_lines(row: Optional[Sequence[Any]], width: int) -> list[str]:
    """Wrapped ``Label: value`` lines describing one registry row."""
    if row is None:
        return ["(no document selected)"]
    out: list[str] = []
    for label, value in zip(ROW_LABELS, row, strict=True):
        text = f"{label}: {'' if value is None else value}"
        out.extend(textwrap.wrap(text, max(10, width), subsequent_indent="  ",
                                 break_on_hyphens=False) or [f"{label}:"])
    return out


def _frame_size(screen: Terminal) -> tuple[int, int]:
    cols, rows = screen.size()
    return usable_width(cols), rows


class EditorScreen:
    """Header editor for one loaded document."""

    def __init__(self, ctx: Ctx, screen: Terminal, doc: Any, notes: Optional[NoteBuffer] = None) -> None:
        self.ctx = ctx
        self.screen = screen
        self.doc = doc
        self.notes = notes
        self.form = FormModel(doc.copy_payload())
        self.cursor = 0
        self.overlay: Optional[Picker | TextInput] = None
        self.overlay_field = FIELDS[0]
        self.confirming = False
        self.stale = False
        self.message = "status changes use 'somnus status'"

    # ------------------------------------------------------------- loop
    def run(self) -> None:
        """Interact until the user quits."""
        while True:
            self._absorb_notes()
            self.screen.draw(self.render(*_frame_size(self.screen)))
            try:
                key = self.screen.read_key()
            except EOFError:
                return
            if not self.handle(key):
                return

    def _absorb_notes(self) -> None:
        """Fold notes captured since the last frame into the status line."""
        if self.notes is None:
            return
        pending = self.notes.drain()
        if pending:
            self.message = f"{self.message}; {pending}" if self.message else pending

    def handle(self, key: str) -> bool:
        """Apply one key; return False when the editor should close."""
        if self.overlay is not None:
            self._handle_overlay(key)
            return True
        if self.confirming:
            self.confirming = False
            if key in ("y", "Y"):
                return False
            self.message = "quit cancelled"
            return True
        if key in QUIT_KEYS:
            return self._request_quit()
        actions = {"up": self._up, "down": self._down, "enter": self._open_field, "s": self.save,
                   "e": self.edit_body, "u": self._revert}
        action = actions.get(key)
        if action is not None:
            action()
        return True

    def _up(self) -> None:
        self.cursor = max(0, self.cursor - 1)

    def _down(self) -> None:
        self.cursor = min(len(FIELDS) - 1, self.cursor + 1)

    def _revert(self) -> None:
        self.form.revert()
        self.message = "changes discarded"

    def _request_quit(self) -> bool:
        if not self.form.dirty:
            return False
        self.confirming = True
        self.message = "unsaved changes; quit anyway? [y/N]"
        return True

    def _open_field(self) -> None:
        field = FIELDS[self.cursor]
        self.overlay_field = field
        if field.kind == "choice":
            self.overlay = Picker(field.label, field.choices, self.form.value(field.path))
        else:
            self.overlay = TextInput(field.label, self.form.text(field))

    def _handle_overlay(self, key: str) -> None:
        overlay = self.overlay
        if overlay is None:
            return
        overlay.handle(key)
        if not overlay.done:
            return
        self.overlay = None
        if overlay.cancelled or overlay.value is None:
            self.message = "edit cancelled"
            return
        try:
            self.form.apply(self.overlay_field, overlay.value)
        except ValueError as exc:
            self.message = str(exc)
            return
        self.message = f"{self.overlay_field.label.lower()} updated"

    # ------------------------------------------------------------- actions
    def save(self) -> None:
        """Bump the revision, commit the header, record the edit, and reload."""
        if self.stale:
            self.message = "document failed to reload; fix it with 'e' or quit"
            return
        if self.form.errors:
            self.message = f"not saved: {self.form.status()}"
            return
        if not self.form.dirty:
            self.message = "no changes to save"
            return
        payload = copy.deepcopy(self.form.payload)
        bump_revision(payload)
        try:
            commit(self.doc, payload)
        except SomnusError as exc:
            self.message = f"not saved: {first_message(exc)}"
            return
        except OSError as exc:
            self.message = f"not saved: {exc}"
            return
        note = f"saved revision {payload['revision']}"
        try:
            self.ctx.record("edit", self.doc.path, payload["id"], payload["revision"],
                            "header edited in TUI", resolve=("revision",))
        except SomnusError as exc:
            note += f"; registry not updated: {first_message(exc)}"
        self.screen.invalidate()
        self.reload(note)

    def edit_body(self) -> None:
        """Open the document in the external editor, then reload it."""
        if self.form.dirty:
            self.message = "save (s) or discard (u) header changes before editing the body"
            return
        argv = editor_command() + [str(self.doc.path)]
        try:
            with self.screen.suspended():
                code = subprocess.call(argv)
        except TerminalError:
            raise
        except OSError as exc:
            self.message = f"cannot run {argv[0]}: {exc}"
            return
        self.reload(f"body edited ({argv[0]} exited {code})")

    def reload(self, note: str) -> None:
        """Re-read the document from disk; on failure keep the old view and block saving."""
        try:
            doc = load_valid(self.doc.path)
        except SomnusError as exc:
            self.stale = True
            self.message = f"reload failed: {first_message(exc)}"
            return
        except OSError as exc:
            self.stale = True
            self.message = f"reload failed: {exc}"
            return
        self.stale = False
        self.doc = doc
        self.form = FormModel(doc.copy_payload())
        self.message = note

    # ------------------------------------------------------------- render
    def render(self, width: int, height: int) -> list[str]:
        """Full frame: header, form or picker, validation line, message/input line, key help."""
        revision = self.form.value("revision")
        lines = [highlight(f"somnus edit: {self.doc.display}  (revision {revision})", width), ""]
        body_h = max(0, height - 5)
        if isinstance(self.overlay, Picker):
            body = self.overlay.render(width, body_h)
        else:
            body = self._form_lines(width, body_h)
        lines.extend(body[:body_h])
        lines.extend("" for _ in range(body_h - len(body)))
        state = self.form.status() + ("  (modified)" if self.form.dirty else "")
        lines.append(state)
        if isinstance(self.overlay, TextInput):
            lines.extend(self.overlay.render(width))
        else:
            lines.append(self.message)
        lines.append(self._help())
        return [fit(line, width) for line in lines[:height]]

    def _form_lines(self, width: int, height: int) -> list[str]:
        rows = []
        for i, field in enumerate(FIELDS):
            text = f"  {field.label.ljust(LABEL_WIDTH)} {self.form.text(field) or '-'}"
            rows.append(highlight(text, width) if i == self.cursor else text)
        rows.append("")
        rows.append("Read-only (status changes use 'somnus status'):")
        rows.extend(f"  {label.ljust(LABEL_WIDTH)} {text or '-'}" for label, text in self.form.readonly_rows())
        if self.stale:
            rows.extend(["", "! the file on disk no longer validates; saving is disabled"])
        start = max(0, self.cursor - height + 1) if height > 0 else 0
        return rows[start:start + height]

    def _help(self) -> str:
        if self.overlay is not None:
            return "[enter] accept  [esc] cancel"
        if self.confirming:
            return "[y] quit without saving  [any other key] stay"
        return "[up/down] field  [enter] edit  [s] save  [u] undo edits  [e] body in editor  [q] quit"


class BrowserScreen:
    """Filterable registry list with a detail pane; enter opens the header editor."""

    def __init__(self, ctx: Ctx, screen: Terminal, rows: Sequence[tuple],
                 notes: Optional[NoteBuffer] = None) -> None:
        self.ctx = ctx
        self.screen = screen
        self.notes = notes
        self.list = ListView(rows, render_row, match_text=match_row)
        self.message = f"{len(rows)} documents"

    def run(self) -> None:
        """Interact until the user quits."""
        while True:
            self._absorb_notes()
            self.screen.draw(self.render(*_frame_size(self.screen)))
            try:
                key = self.screen.read_key()
            except EOFError:
                return
            if not self.handle(key):
                return

    def _absorb_notes(self) -> None:
        """Fold notes captured since the last frame into the status line."""
        if self.notes is None:
            return
        pending = self.notes.drain()
        if pending:
            self.message = f"{self.message}; {pending}" if self.message else pending

    def handle(self, key: str) -> bool:
        """Apply one key; return False when the browser should close."""
        if self.list.handle(key):
            return True
        if key in QUIT_KEYS:
            return False
        if key == "r":
            self.reload()
        elif key == "enter":
            self.open_selected()
        return True

    def reload(self) -> None:
        """Re-read the registry rows."""
        try:
            rows = load_rows(self.ctx)
        except SomnusError as exc:
            self.message = f"reload failed: {first_message(exc)}"
            return
        self.list.set_items(rows)
        self.message = f"{len(rows)} documents"

    def open_selected(self) -> None:
        """Open the highlighted document in the editor; invalid documents stay in the browser."""
        row = self.list.selected
        if row is None:
            return
        try:
            doc = load_valid(Path(row[6]))
        except SomnusError as exc:
            self.message = f"cannot edit {row[6]}: {first_message(exc)}"
            return
        except OSError as exc:
            self.message = f"cannot edit {row[6]}: {exc}"
            return
        EditorScreen(self.ctx, self.screen, doc, self.notes).run()
        self.screen.invalidate()
        self.reload()

    def render(self, width: int, height: int) -> list[str]:
        """Full frame: header, list and detail columns, message, key help."""
        body_h = max(0, height - 3)
        left_w, right_w = split_widths(width, BROWSER_RATIO)
        left = self.list.render(left_w, body_h)
        right = detail_lines(self.list.selected, right_w)[:body_h]
        lines = [highlight(f"somnus edit: {len(self.list.items)} documents in registry", width)]
        lines.extend(split(left, right, width, BROWSER_RATIO))
        lines.append(self.message)
        lines.append("[/] filter  [enter] edit header  [r] reload  [q] quit")
        return [fit(line, width) for line in lines[:height]]


def main(ctx: Ctx, path: Optional[Path]) -> int:
    """Run the browser (``path`` is None) or the editor for ``path``; return the exit code."""
    notes = NoteBuffer()
    try:
        with capture_notes(notes):
            if path is not None:
                doc = load_valid(path)
                with Terminal() as term:
                    EditorScreen(ctx, term, doc, notes).run()
            else:
                rows = load_rows(ctx)
                with Terminal() as term:
                    BrowserScreen(ctx, term, rows, notes).run()
    except TerminalError as exc:
        raise SomnusError(f"cannot use the terminal: {exc}", EXIT_USAGE) from exc
    return EXIT_OK
