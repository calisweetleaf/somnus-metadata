# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a1afed-4e98-763f-8e70-625b71c09b63"
#   revision: 1
#   title: "Watcher heartbeat and single-instance lock, readable without importing the watcher (D20)"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a1afed-4e98-763f-8e70-625b71c09b63"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "watcher-heartbeat-and-single-instance-lock-readable-without-importing-the-watche"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a1afed-4e98-763f-8e70-625b71c09b63"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Watcher heartbeat and single-instance lock, readable without importing the watcher (D20).

Kept below ``somnus.watch`` so the terminal UI and status commands can show the
watcher state without depending on the command layer the watcher uses.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, TextIO

STATUS_NAME = "watch.json"
LOCK_NAME = "watch.lock"


# --------------------------------------------------------------------------- single-instance lock


class InstanceLock:
    """Exclusive, process-lifetime lock on ``$SOMNUS_HOME/watch.lock``."""

    def __init__(self, home: Path):
        self.path = home / LOCK_NAME
        self.fh: Optional[TextIO] = None

    def acquire(self) -> bool:
        """Take the lock; False when another watcher holds it."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.path, "a+")
        try:
            _lock(fh)
        except OSError:
            fh.close()
            return False
        self.fh = fh
        return True

    def release(self) -> None:
        """Drop the lock."""
        fh = self.fh
        if fh is None:
            return
        try:
            _unlock(fh)
        except OSError:
            pass
        fh.close()
        self.fh = None


if sys.platform == "win32":
    import msvcrt

    def _lock(fh: TextIO) -> None:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)

    def _unlock(fh: TextIO) -> None:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock(fh: TextIO) -> None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(fh: TextIO) -> None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def is_locked(home: Path) -> bool:
    """True when a live watcher holds the lock."""
    probe = InstanceLock(home)
    if not probe.path.exists():
        return False
    if probe.acquire():
        probe.release()
        return False
    return True


def read_status(home: Path) -> Optional[dict]:
    """The heartbeat written by the running (or last) watcher, or None."""
    try:
        data = json.loads((home / STATUS_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    data["running"] = is_locked(home)
    return data
