"""Lifecycle transition state machine (SPEC §7)."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Optional, Sequence

TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"proposed", "experimental", "rejected", "archived"}),
    "proposed": frozenset({"provisional", "active", "rejected", "experimental", "superseded", "archived"}),
    "provisional": frozenset({"active", "experimental", "rejected", "superseded", "deprecated", "archived"}),
    "experimental": frozenset({"draft", "proposed", "provisional", "rejected", "deprecated", "historical",
                               "archived"}),
    "active": frozenset({"superseded", "deprecated", "historical"}),
    "superseded": frozenset({"historical", "active"}),
    "deprecated": frozenset({"historical", "archived"}),
    "historical": frozenset({"archived", "active"}),
    "rejected": frozenset({"archived"}),
    "archived": frozenset({"active"}),
}

ABANDONABLE = frozenset({"draft", "proposed", "provisional", "experimental"})
REACTIVATABLE = frozenset({"historical", "superseded", "archived"})


def is_abandonment(current: str, target: str) -> bool:
    """Work abandoned before it became current."""
    return target == "archived" and current in ABANDONABLE


def is_reactivation(current: str, target: str) -> bool:
    """A retired artifact returned to active use."""
    return target == "active" and current in REACTIVATABLE


def check_transition(current: str, target: str, reason: Optional[str] = None,
                     replacement_refs: Sequence[dict] = ()) -> list[str]:
    """Return the reasons a transition is refused (empty when permitted)."""
    problems: list[str] = []
    if current not in TRANSITIONS:
        return [f"unknown current status {current!r}"]
    if target not in TRANSITIONS:
        return [f"unknown target status {target!r}"]
    if target == current:
        return [f"artifact is already {current!r}"]
    if target not in TRANSITIONS[current]:
        allowed = ", ".join(sorted(TRANSITIONS[current]))
        return [f"transition {current} -> {target} is not permitted (allowed: {allowed})"]
    needs_reason = is_abandonment(current, target) or is_reactivation(current, target)
    if needs_reason and not (reason and reason.strip()):
        kind = "abandonment" if is_abandonment(current, target) else "reactivation"
        problems.append(f"{kind} ({current} -> {target}) requires --reason")
    if target == "superseded" and not replacement_refs:
        problems.append("superseded requires at least one replacement reference (--replacement)")
    return problems


def now_utc() -> str:
    """Current instant as an RFC 3339 UTC timestamp with seconds precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def apply_transition(payload: dict, target: str, reason: Optional[str] = None,
                     replacement_refs: Sequence[dict] = (), at: Optional[str] = None) -> dict:
    """Return a new payload in ``target`` status with the revision incremented.

    Callers must run ``check_transition`` first.
    """
    new = copy.deepcopy(payload)
    current = new["lifecycle"]["status"]
    lifecycle = new["lifecycle"]
    lifecycle["status"] = target
    if reason and reason.strip():
        lifecycle["reason"] = reason.strip()
    else:
        lifecycle.pop("reason", None)
    if replacement_refs:
        existing = list(lifecycle.get("replacement_refs", []))
        for ref in replacement_refs:
            if ref not in existing:
                existing.append(ref)
        lifecycle["replacement_refs"] = existing
    elif target not in ("superseded", "historical", "archived"):
        lifecycle.pop("replacement_refs", None)
    if is_reactivation(current, target):
        authority = new.get("authority", {})
        if authority.get("standing") == "accepted":
            authority["standing"] = "candidate"
            authority.pop("valid_time", None)
            authority.pop("acceptance_ref", None)
    bump_revision(new, at)
    return new


def bump_revision(payload: dict, at: Optional[str] = None) -> dict:
    """Increment ``revision`` and set ``time.updated_at`` in place."""
    payload["revision"] = int(payload.get("revision", 0)) + 1
    stamp = at or now_utc()
    time = payload.setdefault("time", {})
    created = time.get("created_at")
    if isinstance(created, str) and _instant(created) and _instant(stamp) and _instant(stamp) < _instant(created):
        stamp = created
    time["updated_at"] = stamp
    return payload


def _instant(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
