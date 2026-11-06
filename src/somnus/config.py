# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7f68-7721-b807-1f454021e4af"
#   revision: 2
#   title: "Hierarchical configuration: CLI flag > nearest .somnus.toml > $SOMNUSHOME/config.toml > defaults"
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
#       - target_ref: "urn:somnus:artifact:01a19a67-7f68-7721-b807-1f454021e4af"
#         aspects: ["content"]
#   time:
#     updated_at: "2026-11-06T06:11:48+00:00"
#   names:
#     slug: "hierarchical-configuration-cli-flag-nearest-somnus-toml-somnushome-config-toml-d"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7f68-7721-b807-1f454021e4af"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
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
        "exclude": ["archive/**", ".git/**", "node_modules/**", "**/__pycache__/**", "**/node_modules/**",
                    "**/.venv/**", "**/venv/**", "**/site-packages/**", "**/.tox/**", "**/.mypy_cache/**",
                    "build/**", "dist/**", "**/*.egg-info/**"],
    },
    "carriers": {"json": "sidecar"},
    "watch": {"interval": 5.0, "settle": 10.0, "stamp": "inline", "rescan": 300.0, "adopt": False,
              "revise": "auto"},
}

JSON_CARRIERS = ("sidecar", "key")
WATCH_STAMP = ("off", "inline", "all")
WATCH_REVISE = ("off", "auto")

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
exclude = ["archive/**", ".git/**", "node_modules/**", "**/__pycache__/**", "**/node_modules/**",
           "**/.venv/**", "**/venv/**", "**/site-packages/**", "**/.tox/**", "**/.mypy_cache/**",
           "build/**", "dist/**", "**/*.egg-info/**"]

[carriers]
# Plain .json has no comments: "sidecar" writes <file>.somnus.yaml, "key" embeds a leading "$somnus" member.
json = "sidecar"

[watch]
# somnus watch: poll interval and settle time (seconds), and what to do with unmanaged files:
# "off" index only, "inline" stamp files with an embedded carrier, "all" also create sidecars.
interval = 5.0
settle = 10.0
stamp = "inline"
rescan = 300.0
# adopt = true also stamps files that were unmanaged before the watcher started.
adopt = false
# revise = "auto" records an in-place edit (same revision, changed content) as a new revision.
revise = "auto"
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
    json_carrier: str = "sidecar"
    watch: dict[str, Any] = field(default_factory=lambda: dict(BUILTIN["watch"]))

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
    unknown = set(data) - {"actor", "defaults", "index", "carriers", "watch"}
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
    carriers_t = data.get("carriers", {})
    if not isinstance(carriers_t, dict):
        raise ConfigError(f"{path}: [carriers] must be a table")
    for key, value in carriers_t.items():
        if key != "json":
            raise ConfigError(f"{path}: unknown key carriers.{key}")
        if value not in JSON_CARRIERS:
            raise ConfigError(f"{path}: carriers.json = {value!r} is not one of {JSON_CARRIERS}")
    watch = data.get("watch", {})
    if not isinstance(watch, dict):
        raise ConfigError(f"{path}: [watch] must be a table")
    for key, value in watch.items():
        if key == "stamp":
            if value not in WATCH_STAMP:
                raise ConfigError(f"{path}: watch.stamp = {value!r} is not one of {WATCH_STAMP}")
        elif key == "revise":
            if value not in WATCH_REVISE:
                raise ConfigError(f"{path}: watch.revise = {value!r} is not one of {WATCH_REVISE}")
        elif key == "adopt":
            if not isinstance(value, bool):
                raise ConfigError(f"{path}: watch.adopt must be true or false")
        elif key in ("interval", "settle", "rescan"):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ConfigError(f"{path}: watch.{key} must be a non-negative number")
        else:
            raise ConfigError(f"{path}: unknown key watch.{key}")
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
        merged["carriers"].update(data.get("carriers", {}))
        merged["watch"].update(data.get("watch", {}))
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
        json_carrier=merged["carriers"]["json"],
        watch=dict(merged["watch"]),
    )
