"""Pure-logic widgets: they consume normalized key names and render to lists of strings.

No widget performs I/O. Rendered rows are exactly ``width`` visible cells wide; the only
escape sequences emitted are SGR styles, which ``fit`` understands when clipping.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Optional, Sequence

REVERSE = "\x1b[7m"
RESET = "\x1b[0m"
SEP = " \u2502 "

_SGR = re.compile(r"\x1b\[[0-9;]*m")


def char_width(ch: str) -> int:
    """Terminal cells occupied by one character (0 for combining marks, 2 for wide CJK)."""
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def strip_styles(text: str) -> str:
    """Remove SGR style sequences."""
    return _SGR.sub("", text)


def visible_width(text: str) -> int:
    """Visible cell width of ``text``, ignoring SGR sequences."""
    return sum(char_width(ch) for ch in strip_styles(text))


def fit(text: str, width: int) -> str:
    """Clip ``text`` to ``width`` visible cells and pad with spaces to exactly that width.

    SGR sequences are kept and do not count toward the width; any other control character
    is replaced by a space so it cannot move the cursor. A reset is appended whenever the
    input carried styles, so a clipped style never leaks into the next row.
    """
    width = max(0, width)
    out: list[str] = []
    used = 0
    styled = False
    pos = 0
    while pos < len(text):
        match = _SGR.match(text, pos)
        if match:
            out.append(match.group())
            styled = True
            pos = match.end()
            continue
        ch = text[pos]
        pos += 1
        if not ch.isprintable():
            ch = " "
        cells = char_width(ch)
        if used + cells > width:
            break
        out.append(ch)
        used += cells
    out.append(" " * (width - used))
    if styled:
        out.append(RESET)
    return "".join(out)


def highlight(text: str, width: int) -> str:
    """Render ``text`` as a full-width reverse-video row."""
    return REVERSE + fit(text, width) + RESET


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def _scroll_top(top: int, index: int, height: int) -> int:
    """First visible row so that ``index`` lies inside a window of ``height`` rows."""
    if height <= 0:
        return top
    if index < top:
        return index
    if index >= top + height:
        return index - height + 1
    return max(0, top)


def _step(key: str, index: int, count: int, page: int) -> Optional[int]:
    """New cursor position for a navigation key, or None when ``key`` is not navigation."""
    last = max(0, count - 1)
    if key == "home":
        return 0
    if key == "end":
        return last
    steps = {"up": -1, "down": 1, "pgup": -page, "pgdn": page}
    if key not in steps:
        return None
    return _clamp(index + steps[key], 0, last)


def is_text_key(key: str) -> bool:
    """True when ``key`` is a single printable character."""
    return len(key) == 1 and key.isprintable()


class ListView:
    """Scrolling selection list with a ``/`` case-insensitive substring filter.

    ``handle`` returns True when the key was consumed. While the filter prompt is open,
    printable keys extend the query, backspace shortens it, enter closes the prompt, and
    esc closes it and clears the query. With the prompt closed, esc clears an active
    filter; when no filter is active it is left to the caller.
    """

    def __init__(self, items: Sequence[Any], render_item: Callable[[Any], str] = str,
                 match_text: Optional[Callable[[Any], str]] = None) -> None:
        self.items: list[Any] = list(items)
        self.render_item = render_item
        self.match_text = match_text or render_item
        self.query = ""
        self.searching = False
        self.index = 0
        self.top = 0
        self._page = 10
        self._visible: list[int] = list(range(len(self.items)))

    # ------------------------------------------------------------- state
    @property
    def visible(self) -> list[Any]:
        """Items that pass the current filter, in order."""
        return [self.items[i] for i in self._visible]

    @property
    def selected(self) -> Optional[Any]:
        """The highlighted item, or None when nothing is visible."""
        if not self._visible:
            return None
        return self.items[self._visible[self.index]]

    def set_items(self, items: Sequence[Any]) -> None:
        """Replace the items, keeping the filter and (where possible) the cursor position."""
        self.items = list(items)
        self._refilter(keep=None)
        self.index = _clamp(self.index, 0, max(0, len(self._visible) - 1))

    def _refilter(self, keep: Optional[int]) -> None:
        needle = self.query.casefold()
        self._visible = [i for i, item in enumerate(self.items)
                         if needle in self.match_text(item).casefold()]
        if keep is not None:
            self.index = self._visible.index(keep) if keep in self._visible else 0
        self.top = 0

    def _current(self) -> Optional[int]:
        return self._visible[self.index] if self._visible else None

    # ------------------------------------------------------------- keys
    def handle(self, key: str) -> bool:
        """Apply one key; return True when it was consumed."""
        if self.searching and self._handle_search(key):
            return True
        if key == "/":
            self.searching = True
            return True
        if key == "esc" and self.query:
            self.query = ""
            self._refilter(self._current())
            return True
        moved = _step(key, self.index, len(self._visible), self._page)
        if moved is None:
            return False
        self.index = moved
        return True

    def _handle_search(self, key: str) -> bool:
        if key in ("enter", "esc"):
            self.searching = False
            if key == "esc":
                self.query = ""
                self._refilter(self._current())
            return True
        if key == "backspace":
            self.query = self.query[:-1]
        elif is_text_key(key):
            self.query += key
        else:
            return False
        self._refilter(self._current())
        return True

    # ------------------------------------------------------------- render
    def render(self, width: int, height: int) -> list[str]:
        """Rows for a ``width`` x ``height`` area; the last row is the filter bar when active."""
        if height <= 0:
            return []
        bar = self.searching or bool(self.query)
        body = height - 1 if bar else height
        self._page = max(1, body)
        self.top = _scroll_top(self.top, self.index, body)
        out: list[str] = []
        for pos in range(self.top, min(len(self._visible), self.top + body)):
            text = self.render_item(self.items[self._visible[pos]])
            out.append(highlight(text, width) if pos == self.index else fit(text, width))
        if not self._visible and body > 0:
            out.append(fit("(no matches)" if self.query else "(empty)", width))
        out.extend(fit("", width) for _ in range(body - len(out)))
        if bar:
            suffix = "_" if self.searching else f"  ({len(self._visible)} of {len(self.items)})"
            out.append(fit(f"/{self.query}{suffix}", width))
        return out


class Picker:
    """Radio-list picker over a fixed vocabulary.

    Enter sets ``value`` to the highlighted choice and ``done``; esc sets ``cancelled`` and
    ``done``. A printable key jumps to the next choice starting with that character.
    """

    def __init__(self, title: str, choices: Sequence[str], current: Optional[str] = None) -> None:
        self.title = title
        self.choices = list(choices)
        self.current = current
        self.index = self.choices.index(current) if current in self.choices else 0
        self.top = 0
        self.done = False
        self.cancelled = False
        self.value: Optional[str] = None
        self._page = 10

    def handle(self, key: str) -> bool:
        """Apply one key; return True when it was consumed."""
        if key == "enter":
            if self.choices:
                self.value = self.choices[self.index]
                self.done = True
            return True
        if key == "esc":
            self.cancelled = True
            self.done = True
            return True
        moved = _step(key, self.index, len(self.choices), self._page)
        if moved is not None:
            self.index = moved
            return True
        if is_text_key(key):
            return self._jump(key.casefold())
        return False

    def _jump(self, letter: str) -> bool:
        count = len(self.choices)
        for offset in range(1, count + 1):
            pos = (self.index + offset) % count
            if self.choices[pos].casefold().startswith(letter):
                self.index = pos
                return True
        return False

    def render(self, width: int, height: int) -> list[str]:
        """Title, scrolling choices marked ``(*)`` for the current value, and a key hint."""
        if height <= 0:
            return []
        body = max(0, height - 3)
        self._page = max(1, body)
        self.top = _scroll_top(self.top, self.index, body)
        out = [fit(f"{self.title}:", width)]
        for pos in range(self.top, min(len(self.choices), self.top + body)):
            choice = self.choices[pos]
            mark = "(*)" if choice == self.current else "( )"
            text = f"  {mark} {choice}"
            out.append(highlight(text, width) if pos == self.index else fit(text, width))
        out.extend(fit("", width) for _ in range(1 + body - len(out)))
        out.append(fit("", width))
        out.append(fit("[up/down] move  [enter] choose  [esc] cancel", width))
        return out[:height]


class TextInput:
    """Single-line editor. Enter sets ``done``; esc sets ``cancelled`` and ``done``."""

    def __init__(self, label: str, value: str = "") -> None:
        self.label = label
        self.value = value
        self.cursor = len(value)
        self.done = False
        self.cancelled = False

    def handle(self, key: str) -> bool:
        """Apply one key; return True when it was consumed."""
        if key in ("enter", "esc"):
            self.done = True
            self.cancelled = key == "esc"
            return True
        return self._move(key) or self._edit(key)

    def _move(self, key: str) -> bool:
        targets = {"left": self.cursor - 1, "right": self.cursor + 1, "home": 0, "end": len(self.value)}
        if key not in targets:
            return False
        self.cursor = _clamp(targets[key], 0, len(self.value))
        return True

    def _edit(self, key: str) -> bool:
        pos = self.cursor
        if key == "backspace":
            if pos > 0:
                self.value = self.value[: pos - 1] + self.value[pos:]
                self.cursor = pos - 1
        elif key == "delete":
            self.value = self.value[:pos] + self.value[pos + 1:]
        elif is_text_key(key):
            self.value = self.value[:pos] + key + self.value[pos:]
            self.cursor = pos + 1
        else:
            return False
        return True

    def render(self, width: int, height: int = 1) -> list[str]:
        """``label: value`` with a reverse-video cursor; scrolls horizontally to keep it visible."""
        prefix = f"{self.label}: "
        avail = max(1, width - visible_width(prefix))
        start = max(0, self.cursor - avail + 1)
        shown = self.value[start:start + avail]
        cur = self.cursor - start
        under = shown[cur] if cur < len(shown) else " "
        line = prefix + shown[:cur] + REVERSE + under + RESET + shown[cur + 1:]
        return [fit(line, width)] + [fit("", width) for _ in range(max(0, height - 1))]


def split_widths(width: int, ratio: float = 0.5, sep: str = SEP) -> tuple[int, int]:
    """Left and right column widths for ``split``."""
    inner = max(0, width - visible_width(sep))
    left = _clamp(int(inner * ratio), 0, inner)
    return left, inner - left


def split(left_lines: Sequence[str], right_lines: Sequence[str], width: int, ratio: float = 0.5,
          sep: str = SEP) -> list[str]:
    """Join two columns row by row into lines exactly ``width`` cells wide."""
    left_w, right_w = split_widths(width, ratio, sep)
    rows = max(len(left_lines), len(right_lines))
    out = []
    for i in range(rows):
        left = left_lines[i] if i < len(left_lines) else ""
        right = right_lines[i] if i < len(right_lines) else ""
        out.append(fit(left, left_w) + sep + fit(right, right_w))
    return out
