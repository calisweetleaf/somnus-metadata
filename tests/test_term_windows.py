"""Windows console code paths of ``somnus.tui.term`` driven through fakes.

``sys.platform`` is patched to ``win32`` and ``ctypes.WinDLL``/``msvcrt`` are replaced with
fakes, so the console-mode bookkeeping, error paths, and key reading run on any host.
"""

from __future__ import annotations

import contextlib
import ctypes
import io
import sys
import unittest
from typing import Any, Callable, Iterator, Optional
from unittest import mock

from somnus.tui import term as T

STDIN_HANDLE = 101
STDOUT_HANDLE = 102


class FakeFunction:
    """Stand-in for a ctypes foreign function: callable, with assignable argtypes/restype."""

    def __init__(self, fn: Callable[..., Any]) -> None:
        self._fn = fn
        self.argtypes: object = None
        self.restype: object = None

    def __call__(self, *args: Any) -> Any:
        return self._fn(*args)


class FakeKernel32:
    """Console-mode table keyed by handle; ``None`` marks a handle that is not a console."""

    def __init__(self, stdin_mode: Optional[int], stdout_mode: Optional[int],
                 set_ok: bool = True) -> None:
        self.modes: dict[int, Optional[int]] = {STDIN_HANDLE: stdin_mode, STDOUT_HANDLE: stdout_mode}
        self.set_ok = set_ok
        self.set_calls: list[tuple[int, int]] = []
        self.GetStdHandle = FakeFunction(self._get_std_handle)
        self.GetConsoleMode = FakeFunction(self._get_console_mode)
        self.SetConsoleMode = FakeFunction(self._set_console_mode)

    def _get_std_handle(self, which: int) -> int:
        return STDIN_HANDLE if which == T._STD_INPUT_HANDLE else STDOUT_HANDLE

    def _get_console_mode(self, handle: int, ref: object) -> bool:
        mode = self.modes[handle]
        if mode is None:
            return False
        ref._obj.value = mode  # type: ignore[attr-defined]
        return True

    def _set_console_mode(self, handle: int, mode: int) -> bool:
        self.set_calls.append((handle, mode))
        if not self.set_ok:
            return False
        self.modes[handle] = mode
        return True


class FakeMsvcrt:
    """``msvcrt.getwch`` fed from a fixed key script."""

    def __init__(self, script: str) -> None:
        self._chars = iter(script)

    def getwch(self) -> str:
        return next(self._chars)


@contextlib.contextmanager
def windows_host(kernel: FakeKernel32 | None = None, keys: str = "") -> Iterator[None]:
    """Run the body as if on Windows with the given fake kernel and key script."""
    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(sys, "platform", "win32"))
        if kernel is not None:
            stack.enter_context(mock.patch.object(ctypes, "WinDLL", lambda *a, **k: kernel, create=True))
        stack.enter_context(mock.patch.object(T, "msvcrt", FakeMsvcrt(keys), create=True))
        yield


class WindowsConsoleModesTest(unittest.TestCase):
    def test_enable_turns_on_vt_for_stdout_only_and_restore_puts_both_back(self) -> None:
        kernel = FakeKernel32(stdin_mode=0x01F7, stdout_mode=0x0003)
        with windows_host(kernel):
            console = T._WindowsConsole()
            console.enable()
            self.assertEqual(kernel.modes[STDOUT_HANDLE], 0x0003 | T.ENABLE_VIRTUAL_TERMINAL_PROCESSING)
            self.assertEqual(kernel.modes[STDIN_HANDLE], 0x01F7, "stdin mode is recorded, not altered")
            console.restore()
        self.assertEqual(kernel.modes, {STDIN_HANDLE: 0x01F7, STDOUT_HANDLE: 0x0003})
        with windows_host(kernel):
            console.restore()
        self.assertEqual(len(kernel.set_calls), 3, "a second restore has nothing left to write")

    def test_piped_stdin_is_skipped_but_stdout_is_still_configured(self) -> None:
        kernel = FakeKernel32(stdin_mode=None, stdout_mode=0x0001)
        with windows_host(kernel):
            console = T._WindowsConsole()
            console.enable()
            console.restore()
        self.assertEqual(kernel.set_calls, [(STDOUT_HANDLE, 0x0005), (STDOUT_HANDLE, 0x0001)])

    def test_stdout_that_is_not_a_console_raises_and_leaves_stdin_restorable(self) -> None:
        kernel = FakeKernel32(stdin_mode=0x00F0, stdout_mode=None)
        with windows_host(kernel):
            console = T._WindowsConsole()
            with self.assertRaisesRegex(T.TerminalError, "stdout is not a console"):
                console.enable()
            console.restore()
        self.assertEqual(kernel.set_calls, [(STDIN_HANDLE, 0x00F0)])

    def test_console_without_vt_support_raises_and_restores_recorded_modes(self) -> None:
        kernel = FakeKernel32(stdin_mode=0x00F0, stdout_mode=0x0001, set_ok=False)
        with windows_host(kernel):
            console = T._WindowsConsole()
            with self.assertRaisesRegex(T.TerminalError, "virtual terminal"):
                console.enable()
            console.restore()
        self.assertEqual(kernel.set_calls[0], (STDOUT_HANDLE, 0x0005))
        self.assertEqual(kernel.set_calls[1:], [(STDOUT_HANDLE, 0x0001), (STDIN_HANDLE, 0x00F0)])

    def test_unsupported_platform_is_refused(self) -> None:
        with mock.patch.object(sys, "platform", "linux"):
            with self.assertRaises(T.TerminalError):
                T._WindowsConsole()


class WindowsTerminalLifecycleTest(unittest.TestCase):
    def test_context_manager_writes_screen_sequences_and_restores_modes(self) -> None:
        kernel = FakeKernel32(stdin_mode=0x01F7, stdout_mode=0x0003)
        out = io.StringIO()
        with windows_host(kernel):
            with T.Terminal(stream=out) as term:
                self.assertEqual(kernel.modes[STDOUT_HANDLE], 0x0003 | T.ENABLE_VIRTUAL_TERMINAL_PROCESSING)
                self.assertIsNotNone(term._modes)
        self.assertEqual(kernel.modes, {STDIN_HANDLE: 0x01F7, STDOUT_HANDLE: 0x0003})
        text = out.getvalue()
        self.assertLess(text.index(T.ENTER_SCREEN), text.index(T.LEAVE_SCREEN))

    def test_enter_failure_emits_leave_screen_and_restores_stdin(self) -> None:
        kernel = FakeKernel32(stdin_mode=0x00F0, stdout_mode=None)
        out = io.StringIO()
        with windows_host(kernel):
            with self.assertRaises(T.TerminalError):
                with T.Terminal(stream=out):
                    self.fail("body must not run when the console cannot be entered")
        self.assertNotIn(T.ENTER_SCREEN, out.getvalue())
        self.assertIn(T.LEAVE_SCREEN, out.getvalue())
        self.assertEqual(kernel.modes[STDIN_HANDLE], 0x00F0)

    def test_suspended_round_trips_the_console_modes(self) -> None:
        kernel = FakeKernel32(stdin_mode=0x01F7, stdout_mode=0x0003)
        out = io.StringIO()
        with windows_host(kernel):
            with T.Terminal(stream=out) as term:
                with term.suspended():
                    self.assertEqual(kernel.modes[STDOUT_HANDLE], 0x0003)
                self.assertEqual(kernel.modes[STDOUT_HANDLE], 0x0003 | T.ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        self.assertEqual(out.getvalue().count(T.ENTER_SCREEN), 2)


class WindowsKeyReadingTest(unittest.TestCase):
    def read(self, script: str) -> str:
        with windows_host(keys=script):
            return T.Terminal(stream=io.StringIO()).read_key()

    def test_prefixed_keys_decode_through_the_second_character(self) -> None:
        for script, expected in (("\xe0H", "up"), ("\xe0P", "down"), ("\x00K", "left"),
                                 ("\xe0M", "right"), ("\xe0S", "delete"), ("\x00Q", "pgdn")):
            self.assertEqual(self.read(script), expected, script)

    def test_unknown_prefixed_key_is_empty(self) -> None:
        self.assertEqual(self.read("\xe0?"), "")

    def test_plain_keys_use_the_shared_table(self) -> None:
        for script, expected in (("a", "a"), ("\r", "enter"), ("\x08", "backspace"),
                                 ("\x03", "ctrl-c"), ("\x1b", "esc")):
            self.assertEqual(self.read(script), expected, script)

    def test_posix_guard_in_windows_reader(self) -> None:
        with mock.patch.object(sys, "platform", "linux"):
            self.assertEqual(T.Terminal(stream=io.StringIO())._read_windows(), "")


if __name__ == "__main__":
    unittest.main()
