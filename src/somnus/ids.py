"""Identifier minting and parsing: RFC 9562 UUIDv7, Somnus URNs, slugs."""

from __future__ import annotations

import os
import re
import threading
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Optional

UUID_HEX = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
ARTIFACT_URN_RE = re.compile(rf"urn:somnus:artifact:({UUID_HEX})\Z")
EXAMPLE_URN_RE = re.compile(r"urn:somnus:example:[a-z0-9][a-z0-9-]*\Z")
SOMNUS_URN_RE = re.compile(r"urn:somnus:(artifact|entity|actor|concept|example):([A-Za-z0-9][A-Za-z0-9._:-]*)\Z")
EXTERNAL_REF_RE = re.compile(r"(?:doi:10\.\S+|https?://\S+|urn:(?!somnus:)[a-z0-9][a-z0-9-]*:\S+)\Z")
LEGACY_DOC_RE = re.compile(rf"urn:somnus:doc:({UUID_HEX})\Z", re.IGNORECASE)
BARE_UUID_RE = re.compile(rf"{UUID_HEX}\Z", re.IGNORECASE)
LOCAL_ID_RE = re.compile(r"[a-z][a-z0-9_]*(?:-[a-z0-9_]+)*\Z")

_lock = threading.Lock()
_last_ms = 0
_last_seq = 0


def uuid7(unix_ms: Optional[int] = None) -> uuid.UUID:
    """Mint a UUIDv7 (RFC 9562 §5.7) with a monotonic 12-bit sequence in rand_a."""
    global _last_ms, _last_seq
    with _lock:
        ms = int(time.time() * 1000) if unix_ms is None else unix_ms
        if unix_ms is None and ms <= _last_ms:
            ms = _last_ms
            seq = _last_seq + 1
            if seq > 0xFFF:
                ms += 1
                seq = int.from_bytes(os.urandom(2), "big") & 0x7FF
        else:
            seq = int.from_bytes(os.urandom(2), "big") & 0x7FF
        if unix_ms is None:
            _last_ms, _last_seq = ms, seq
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
    value = (ms & ((1 << 48) - 1)) << 80
    value |= 0x7 << 76
    value |= seq << 64
    value |= 0b10 << 62
    value |= rand_b
    return uuid.UUID(int=value)


def new_artifact_urn() -> str:
    """Return a freshly minted ``urn:somnus:artifact:<uuidv7>``."""
    return f"urn:somnus:artifact:{uuid7()}"


def parse_urn(urn: str) -> tuple[str, str]:
    """Split a Somnus URN into (kind, key); raise ValueError when malformed."""
    m = SOMNUS_URN_RE.match(urn)
    if not m:
        raise ValueError(f"not a Somnus URN: {urn!r}")
    return m.group(1), m.group(2)


def is_artifact_urn(value: str) -> bool:
    """Return True for a lowercase ``urn:somnus:artifact:<uuid>``."""
    return bool(ARTIFACT_URN_RE.match(value))


def is_example_urn(value: str) -> bool:
    """Return True for a fixture-only ``urn:somnus:example:*`` identifier."""
    return bool(EXAMPLE_URN_RE.match(value))


def is_external_ref(value: str) -> bool:
    """Return True for DOI, HTTP(S), or non-Somnus URN references."""
    return bool(EXTERNAL_REF_RE.match(value))


def is_reference_string(value: str) -> bool:
    """Return True when ``value`` is a Somnus URN or an external reference."""
    return bool(SOMNUS_URN_RE.match(value)) or is_external_ref(value)


def uuid_version(urn: str) -> Optional[int]:
    """Return the UUID version nibble of an artifact URN, or None."""
    m = ARTIFACT_URN_RE.match(urn)
    return uuid.UUID(m.group(1)).version if m else None


def uuid7_time(urn: str) -> Optional[datetime]:
    """Return the ID-generation instant of a UUIDv7 artifact URN (never an authored date)."""
    m = ARTIFACT_URN_RE.match(urn)
    if not m:
        return None
    u = uuid.UUID(m.group(1))
    if u.version != 7:
        return None
    return datetime.fromtimestamp((u.int >> 80) / 1000, tz=timezone.utc)


def normalize_legacy_ref(value: str) -> str:
    """Map v0.1 ``urn:somnus:doc:<uuid>`` or a bare UUID to an artifact URN."""
    m = LEGACY_DOC_RE.match(value)
    if m:
        return f"urn:somnus:artifact:{m.group(1).lower()}"
    if BARE_UUID_RE.match(value):
        return f"urn:somnus:artifact:{value.lower()}"
    return value


_TRANSLIT = {"\u00f8": "o", "\u00d8": "o", "\u00e6": "ae", "\u00c6": "ae", "\u00df": "ss", "\u0111": "d",
             "\u0110": "d", "\u0142": "l", "\u0141": "l", "\u0153": "oe", "\u0152": "oe",
             "\u00fe": "th", "\u00de": "th"}


def slugify(title: str, max_len: int = 80) -> str:
    """Normalize a title into a filesystem-safe kebab-case slug."""
    text = "".join(_TRANSLIT.get(ch, ch) for ch in title)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text or "untitled"


def is_local_id(value: str) -> bool:
    """Return True for a valid local region/claim/relation identifier."""
    return bool(LOCAL_ID_RE.match(value))
