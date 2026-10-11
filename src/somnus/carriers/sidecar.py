"""Detached sidecar bindings: ``<file>.somnus.yaml`` (SPEC Â§17.6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from somnus.carriers import Envelope, Extraction, Issue, Splice


class SidecarCarrier:
    """The whole sidecar file is the restricted-YAML payload."""

    name = "sidecar"
    capability = "somnus-adapter-sidecar@1"
    forbid: Optional[str] = None
    region_style: tuple = ()

    def extract(self, lines: list[str]) -> Extraction:
        """Treat every line as payload (trailing empty line excluded)."""
        end = len(lines)
        while end > 0 and lines[end - 1] == "":
            end -= 1
        if end == 0:
            return Extraction(None, [Issue(1, 1, "E_ENVELOPE", "sidecar file is empty")])
        return Extraction(Envelope("sidecar", 0, end, lines[:end], 0))

    def render(self, lines: list[str], payload: str, envelope: Optional[Envelope], style: Optional[str] = None) -> Splice:
        """Replace the whole sidecar content."""
        body = payload.rstrip("\n").split("\n")
        end = envelope.end if envelope is not None else len(lines)
        return Splice(0, end, body)


SIDECAR = SidecarCarrier()


def binding_issues(somnus: Any, sidecar_path: Path) -> list[tuple[tuple, str]]:
    """Check the primary binding contract; return (field path, message) pairs."""
    problems: list[tuple[tuple, str]] = []
    bindings = somnus.get("bindings") if isinstance(somnus, dict) else None
    if not isinstance(bindings, list) or not bindings:
        return [(("somnus", "bindings"), "a sidecar requires a 'bindings' array with one primary binding")]
    primaries = [(i, b) for i, b in enumerate(bindings) if isinstance(b, dict) and b.get("role") == "primary"]
    if len(primaries) != 1:
        problems.append((("somnus", "bindings"), f"exactly one primary binding is required, found {len(primaries)}"))
        return problems
    index, primary = primaries[0]
    if primary.get("required") is not True:
        problems.append((("somnus", "bindings", index, "required"), "the primary binding must set required: true"))
    target = primary.get("target")
    locator = target if isinstance(target, str) else (target.get("locator_hint") if isinstance(target, dict) else None)
    if isinstance(target, str):
        resolved = (sidecar_path.parent / target)
        if not resolved.exists():
            problems.append((("somnus", "bindings", index, "target"), f"primary target {target!r} does not exist"))
        else:
            expected = sidecar_path.name[: -len(".somnus.yaml")]
            if resolved.resolve() != (sidecar_path.parent / expected).resolve():
                problems.append((("somnus", "bindings", index, "target"),
                                 f"primary target {target!r} does not match sidecar host {expected!r}"))
    elif locator is None and not isinstance(target, dict):
        problems.append((("somnus", "bindings", index, "target"), "primary target must be a locator or reference"))
    return problems


def primary_target(somnus: Any, sidecar_path: Path) -> Optional[Path]:
    """Return the resolved primary target path of a sidecar, when it is a relative locator."""
    for b in somnus.get("bindings", []) if isinstance(somnus, dict) else []:
        if isinstance(b, dict) and b.get("role") == "primary" and isinstance(b.get("target"), str):
            return (sidecar_path.parent / b["target"]).resolve()
    return None
