"""Hierarchical configuration: CLI flag > nearest .somnus.toml > $SOMNUS_HOME/config.toml > defaults."""

from __future__ import annotations

import copy
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from somnus.model import vocab

LOCAL_NAME = ".somnus.toml"

BUILTIN: dict[str, Any] = {
    "actor": "operator",
    "defaults": {
        "category": "engineering",
        "role": "normative",
        "scope": "component",
        "visibility": "internal",
        "allowed_uses": ["archive", "search", "reason"],
        "standing": "candidate",
        "disposition": "candidate",
        "body_role": "specification",
    },
    "index": {
        "roots": ["."],
        "exclude": ["archive/**", ".git/**", "node_modules/**", "**/__pycache__/**"],
    },
}

CONFIG_TEMPLATE = '''# Somnus global configuration (precedence: CLI flag > .somnus.toml > this file > built-ins)
actor = "operator"

[defaults]
category = "engineering"
role = "normative"
scope = "component"
visibility = "internal"
allowed_uses = ["archive", "search", "reason"]
standing = "candidate"
disposition = "candidate"
body_role = "specification"

[index]
roots = []
exclude = ["archive/**", ".git/**", "node_modules/**", "**/__pycache__/**"]
'''

_ENUMS = {
    "category": vocab.CATEGORIES,
    "role": vocab.ROLES,
    "scope": vocab.SCOPES,
    "visibility": vocab.VISIBILITIES,
    "standing": vocab.STANDINGS,
    "disposition": vocab.DISPOSITIONS,
    "body_role": vocab.BODY_ROLES,
}


class ConfigError(ValueError):
    """Configuration file is malformed or contains unknown or invalid values."""


@dataclass
class Config:
    """Resolved configuration with the files that contributed to it."""

    actor: str
    defaults: dict[str, Any]
    roots: list[Path]
    exclude: list[str]
    home: Path
    sources: list[Path] = field(default_factory=list)

    @property
    def db_path(self) -> Path:
        """Location of the global registry database."""
        return self.home / "somnus.db"


def somnus_home() -> Path:
    """Return $SOMNUS_HOME, defaulting to ~/.somnus."""
    env = os.environ.get("SOMNUS_HOME")
    return Path(env).expanduser().resolve() if env else (Path.home() / ".somnus").resolve()


def find_local_config(start: Path) -> Optional[Path]:
    """Return the nearest .somnus.toml at or above ``start``."""
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        candidate = directory / LOCAL_NAME
        if candidate.is_file():
            return candidate
    return None


def _read(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"{path}: {exc.strerror}") from exc
    _check(data, path)
    return data


def _check(data: dict[str, Any], path: Path) -> None:
    unknown = set(data) - {"actor", "defaults", "index"}
    if unknown:
        raise ConfigError(f"{path}: unknown keys {sorted(unknown)}")
    if "actor" in data and (not isinstance(data["actor"], str) or not data["actor"].strip()):
        raise ConfigError(f"{path}: actor must be a nonempty string")
    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ConfigError(f"{path}: [defaults] must be a table")
    for key, value in defaults.items():
        if key == "allowed_uses":
            if not isinstance(value, list) or any(v not in vocab.ALLOWED_USES for v in value):
                raise ConfigError(f"{path}: defaults.allowed_uses must list values from {vocab.ALLOWED_USES}")
        elif key in _ENUMS:
            if value not in _ENUMS[key]:
                raise ConfigError(f"{path}: defaults.{key} = {value!r} is not one of {_ENUMS[key]}")
        else:
            raise ConfigError(f"{path}: unknown key defaults.{key}")
    index = data.get("index", {})
    if not isinstance(index, dict):
        raise ConfigError(f"{path}: [index] must be a table")
    for key, value in index.items():
        if key not in ("roots", "exclude"):
            raise ConfigError(f"{path}: unknown key index.{key}")
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ConfigError(f"{path}: index.{key} must be an array of strings")


def load(start: Optional[Path] = None, actor: Optional[str] = None) -> Config:
    """Resolve configuration for work rooted at ``start`` (default: cwd)."""
    start = (start or Path.cwd()).resolve()
    home = somnus_home()
    merged = copy.deepcopy(BUILTIN)
    roots: list[Path] = [start if start.is_dir() else start.parent]
    sources: list[Path] = []
    layers: list[Path] = []
    global_cfg = home / "config.toml"
    if global_cfg.is_file():
        layers.append(global_cfg)
    local = find_local_config(start)
    if local is not None:
        layers.append(local)
    for layer in layers:
        data = _read(layer)
        sources.append(layer)
        if "actor" in data:
            merged["actor"] = data["actor"]
        merged["defaults"].update(data.get("defaults", {}))
        index = data.get("index", {})
        if "exclude" in index:
            merged["index"]["exclude"] = list(index["exclude"])
        if index.get("roots"):
            roots = [(layer.parent / r).resolve() for r in index["roots"]]
    if actor:
        merged["actor"] = actor
    return Config(
        actor=merged["actor"],
        defaults=merged["defaults"],
        roots=roots,
        exclude=list(merged["index"]["exclude"]),
        home=home,
        sources=sources,
    )
