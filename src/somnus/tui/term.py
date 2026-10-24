"""Terminal abstraction: raw key input, alternate screen, and differential redraw.

Windows uses ``msvcrt`` for keys and ``kernel32`` console modes for VT output; POSIX uses
``termios``/``tty`` raw mode. Key decoding is factored into pure functions so it can be
tested without a terminal.
"""

from __future__ import annotations

import codecs
import contextlib
import os
import shutil
import sys
from typing import Any, Iterator, Optional, Sequence, TextIO

from somnus.tui.widgets import fit

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty

ENTER_SCREEN = "\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H"
LEAVE_SCREEN = "\x1b[0m\x1b[?25h\x1b[?1049l"

ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
_STD_INPUT_HANDLE = -10 & 0xFFFFFFFF
_STD_OUTPUT_HANDLE = -11 & 0xFFFFFFFF

_WINDOWS_SPECIAL = {
    "H": "up", "P": "down", "K": "left", "M": "right", "G": "home", "O": "end",
    "I": "pgup", "Q": "pgdn", "S": "delete",
}
_CSI_LETTERS = {"A": "up", "B": "down", "C": "right", "D": "left", "H": "home", "F": "end"}
_CSI_TILDE = {"1": "home", "7": "home", "4": "end", "8": "end", "3": "delete", "5": "pgup", "6": "pgdn"}
_PLAIN = {"\r": "enter", "\n": "enter", "\x1b": "esc", "\x08": "backspace", "\x7f": "backspace",
          "\t": "tab", "\x03": "ctrl-c"}

_ESC_TIMEOUT = 0.05
_MAX_SEQUENCE = 16


class TerminalError(OSError):
    """The terminal could not be switched into (or out of) full-screen mode."""


# --------------------------------------------------------------------------- pure decoding


def decode_char(ch: str) -> str:
    """Normalize one non-prefixed input character to a key name (or the character itself)."""
    return _PLAIN.get(ch, ch)


def decode_windows_special(second: str) -> str:
    """Key name for the character following a ``\\x00``/``\\xe0`` prefix; "" when unknown."""
    return _WINDOWS_SPECIAL.get(second, "")


def decode_escape(seq: str) -> str:
    """Key name for the characters after ESC (``[A``, ``OH``, ``[5~``, ``[1;5C``...); "" when unknown."""
    if len(seq) < 2 or seq[0] not in "[O":
        return ""
    final = seq[-1]
    if final == "~" and seq[0] == "[":
        return _CSI_TILDE.get(seq[1:-1].split(";")[0], "")
    return _CSI_LETTERS.get(final, "")


def is_sequence_final(ch: str) -> bool:
    """True for a CSI/SS3 final byte (``@`` through ``~``)."""
    return "\x40" <= ch <= "\x7e"


def frame_updates(prev: Sequence[str], lines: Sequence[str], cols: int,
                  rows: int) -> tuple[list[str], list[tuple[int, str]]]:
    """Normalize ``lines`` into a full frame and list the ``(row, text)`` pairs that changed.

    Rows are clipped and padded to ``cols - 1`` cells: leaving the last column empty keeps
    terminals that scroll on a write to the bottom-right cell from scrolling the frame.
    """
    width = max(1, cols - 1)
    frame = [fit(lines[i] if i < len(lines) else "", width) for i in range(max(0, rows))]
    updates = [(i, row) for i, row in enumerate(frame) if i >= len(prev) or prev[i] != row]
    return frame, updates


def usable_width(cols: int) -> int:
    """Width that callers should render to, matching ``frame_updates`` clipping."""
    return max(1, cols - 1)


# --------------------------------------------------------------------------- platform modes


class _WindowsConsole:
    """Saves console modes, enables VT output, and restores the saved modes."""

    _ctypes: Any
    _dword: Any
    _k: Any

    def __init__(self) -> None:
        if sys.platform != "win32":  # defensive: instantiated only on Windows
            raise TerminalError("Windows console modes are unavailable")
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        self._dword = wintypes.DWORD
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel32.GetStdHandle.restype = wintypes.HANDLE
        kernel32.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetConsoleMode.restype = wintypes.BOOL
        kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.SetConsoleMode.restype = wintypes.BOOL
        self._k = kernel32
        self._saved: list[tuple[int, int]] = []

    def _mode(self, handle: int) -> Optional[int]:
        mode = self._dword()
        if not self._k.GetConsoleMode(handle, self._ctypes.byref(mode)):
            return None
        return int(mode.value)

    def enable(self) -> None:
        """Record both console modes and turn on VT processing for stdout."""
        stdin_handle = self._k.GetStdHandle(_STD_INPUT_HANDLE)
        stdin_mode = self._mode(stdin_handle)
        if stdin_mode is not None:
            self._saved.append((stdin_handle, stdin_mode))
        stdout_handle = self._k.GetStdHandle(_STD_OUTPUT_HANDLE)
        stdout_mode = self._mode(stdout_handle)
        if stdout_mode is None:
            raise TerminalError("stdout is not a console")
        self._saved.append((stdout_handle, stdout_mode))
        if not self._k.SetConsoleMode(stdout_handle, stdout_mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING):
            raise TerminalError("console does not support virtual terminal sequences")

    def restore(self) -> None:
        """Put back every recorded console mode."""
        while self._saved:
            handle, mode = self._saved.pop()
            self._k.SetConsoleMode(handle, mode)


class _PosixTty:
    """Saves termios attributes of stdin, enters raw mode, and restores them."""

    def __init__(self, fd: int) -> None:
        self.fd = fd
        self._saved: Optional[list] = None

    def enable(self) -> None:
        """Record the current attributes and switch stdin to raw mode."""
        try:
            self._saved = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
        except termios.error as exc:
            raise TerminalError(f"cannot enter raw mode: {exc}") from exc

    def restore(self) -> None:
        """Restore the recorded attributes (no-op when none were recorded)."""
        saved, self._saved = self._saved, None
        if saved is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, saved)


# --------------------------------------------------------------------------- terminal


class Terminal:
    """Full-screen terminal session; use as a context manager.

    Entering switches to the alternate screen, hides the cursor, and sets raw/VT modes.
    Leaving (normally or by exception) restores the screen, cursor, and saved modes.
    """

    def __init__(self, stream: Optional[TextIO] = None) -> None:
        self._out = stream or sys.stdout
        self._prev: list[str] = []
        self._size: Optional[tuple[int, int]] = None
        self._modes: Optional[_WindowsConsole | _PosixTty] = None
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")

    # ------------------------------------------------------------- lifecycle
    def __enter__(self) -> "Terminal":
        self._enter()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._leave()

    def _enter(self) -> None:
        try:
            modes = _WindowsConsole() if sys.platform == "win32" else _PosixTty(sys.stdin.fileno())
            self._modes = modes
            modes.enable()
            self._write(ENTER_SCREEN)
        except BaseException:
            self._leave()
            raise
        self.invalidate()

    def _leave(self) -> None:
        try:
            self._write(LEAVE_SCREEN)
        finally:
            modes, self._modes = self._modes, None
            if modes is not None:
                modes.restore()

    @contextlib.contextmanager
    def suspended(self) -> Iterator[None]:
        """Temporarily restore the normal screen and modes (e.g. to run an external editor)."""
        self._leave()
        try:
            yield
        finally:
            self._enter()

    # ------------------------------------------------------------- output
    def _write(self, text: str) -> None:
        self._out.write(text)
        self._out.flush()

    def size(self) -> tuple[int, int]:
        """Current ``(columns, rows)``."""
        cols, rows = shutil.get_terminal_size()
        return cols, rows

    def invalidate(self) -> None:
        """Forget the previous frame so the next ``draw`` repaints everything."""
        self._prev = []
        self._size = None

    def draw(self, lines: Sequence[str]) -> None:
        """Paint ``lines``, writing only rows that differ from the previous frame."""
        cols, rows = self.size()
        if (cols, rows) != self._size:
            self._size = (cols, rows)
            self._prev = []
            self._out.write("\x1b[2J")
        frame, updates = frame_updates(self._prev, lines, cols, rows)
        if updates:
            self._write("".join(f"\x1b[{row + 1};1H{text}" for row, text in updates))
        self._prev = frame

    # ------------------------------------------------------------- input
    def read_key(self) -> str:
        """Block for one key and return its normalized name ("" for unrecognized sequences)."""
        if sys.platform == "win32":
            return self._read_windows()
        return self._read_posix()

    def _read_windows(self) -> str:
        if sys.platform != "win32":  # defensive: callers route by platform
            return ""
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return decode_windows_special(msvcrt.getwch())
        return decode_char(ch)

    def _read_posix(self) -> str:
        fd = sys.stdin.fileno()
        ch = self._read_char(fd)
        if ch != "\x1b":
            return decode_char(ch)
        if not self._ready(fd):
            return "esc"
        intro = self._read_char(fd)
        if intro not in ("[", "O"):
            return "esc"
        body = ""
        while len(body) < _MAX_SEQUENCE and self._ready(fd):
            body += self._read_char(fd)
            if is_sequence_final(body[-1]):
                break
        return decode_escape(intro + body)

    @staticmethod
    def _ready(fd: int) -> bool:
        readable, _, _ = select.select([fd], [], [], _ESC_TIMEOUT)
        return bool(readable)

    def _read_char(self, fd: int) -> str:
        while True:
            data = os.read(fd, 1)
            if not data:
                raise EOFError("terminal input closed")
            text = self._decoder.decode(data)
            if text:
                return text
