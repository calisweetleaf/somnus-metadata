"""Header form model: editable field definitions, payload edits, validation, dirty tracking."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from somnus.model import vocab
from somnus.model.validate import validate_payload
from somnus.output import Diagnostic


@dataclass(frozen=True)
class Field:
    """One editable header field; ``kind`` is ``text``, ``optional``, ``choice``, or ``tags``."""

    path: str
    label: str
    kind: str
    choices: tuple[str, ...] = ()


FIELDS: tuple[Field, ...] = (
    Field("title", "Title", "text"),
    Field("summary", "Summary", "optional"),
    Field("purpose", "Purpose", "optional"),
    Field("classification.category", "Category", "choice", tuple(vocab.CATEGORIES)),
    Field("classification.type", "Type", "choice", tuple(vocab.TYPES)),
    Field("classification.role", "Role", "choice", tuple(vocab.ROLES)),
    Field("classification.scope", "Scope", "choice", tuple(vocab.SCOPES)),
    Field("classification.tags", "Tags", "tags"),
    Field("access.visibility", "Visibility", "choice", tuple(vocab.VISIBILITIES)),
    Field("ingestion.disposition", "Disposition", "choice", tuple(vocab.DISPOSITIONS)),
)

READONLY: tuple[tuple[str, str], ...] = (
    ("id", "ID"),
    ("revision", "Revision"),
    ("lifecycle.status", "Status"),
    ("authority.standing", "Standing"),
    ("authority.scopes", "Authority scopes"),
)

_MISSING = object()


def parse_tags(raw: str) -> list[str]:
    """Comma-separated tags: trimmed, empties dropped, duplicates removed in order."""
    out: list[str] = []
    for part in raw.split(","):
        tag = part.strip()
        if tag and tag not in out:
            out.append(tag)
    return out


def get_path(payload: dict, path: str, default: Any = None) -> Any:
    """Value at dotted ``path``, or ``default`` when any segment is missing."""
    node: Any = payload
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def set_path(payload: dict, path: str, value: Any) -> None:
    """Set dotted ``path``, creating intermediate mappings as needed."""
    *parents, leaf = path.split(".")
    node = payload
    for key in parents:
        child = node.get(key)
        if not isinstance(child, dict):
            child = {}
            node[key] = child
        node = child
    node[leaf] = value


def remove_path(payload: dict, path: str) -> None:
    """Delete dotted ``path`` when present."""
    *parents, leaf = path.split(".")
    parent = get_path(payload, ".".join(parents)) if parents else payload
    if isinstance(parent, dict):
        parent.pop(leaf, None)


def format_value(value: Any) -> str:
    """Display text for a payload value; mappings render as ``key=value`` pairs."""
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{k}={'+'.join(map(str, v)) if isinstance(v, list) else v}" for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return ", ".join(format_value(v) for v in value)
    return str(value)


class FormModel:
    """Working copy of a payload with field-level edits and live validation."""

    def __init__(self, payload: dict,
                 validator: Callable[[dict], Sequence[Diagnostic]] = validate_payload) -> None:
        self.original = copy.deepcopy(payload)
        self.payload = copy.deepcopy(payload)
        self._validator = validator
        self.errors: list[Diagnostic] = []
        self.revalidate()

    @property
    def dirty(self) -> bool:
        """True when the working payload differs from the loaded one."""
        return self.payload != self.original

    def value(self, path: str) -> Any:
        """Current value at dotted ``path`` (None when absent)."""
        return get_path(self.payload, path)

    def text(self, field: Field) -> str:
        """Current value of ``field`` as editable text."""
        return format_value(self.value(field.path))

    def readonly_rows(self) -> list[tuple[str, str]]:
        """``(label, text)`` for fields shown but never edited here."""
        return [(label, format_value(get_path(self.payload, path))) for path, label in READONLY]

    def apply(self, field: Field, raw: str) -> None:
        """Apply text (or a choice) to ``field`` and revalidate.

        Raises ValueError for a choice outside the field's vocabulary.
        """
        text = raw.strip()
        if field.kind == "tags":
            tags = parse_tags(raw)
            if tags or get_path(self.payload, field.path, _MISSING) is not _MISSING:
                set_path(self.payload, field.path, tags)
        elif field.kind == "optional" and not text:
            remove_path(self.payload, field.path)
        elif field.kind == "choice" and text not in field.choices:
            raise ValueError(f"{text!r} is not a valid {field.label.lower()}")
        else:
            set_path(self.payload, field.path, text)
        self.revalidate()

    def revert(self) -> None:
        """Discard every edit."""
        self.payload = copy.deepcopy(self.original)
        self.revalidate()

    def revalidate(self) -> None:
        """Recompute ``errors`` from the validator."""
        self.errors = [d for d in self._validator(self.payload) if d.is_error]

    def status(self) -> str:
        """One-line validation summary: ``valid`` or the error count and first error."""
        if not self.errors:
            return "valid"
        first = self.errors[0]
        where = "" if first.field in ("", "-") else f"{first.field}: "
        noun = "error" if len(self.errors) == 1 else "errors"
        return f"{len(self.errors)} {noun}: {where}{first.message}"
