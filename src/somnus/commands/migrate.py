"""``somnus migrate``: upgrade v0.1 hybrid documents to core 2.0.0 (SPEC §22)."""

from __future__ import annotations

import copy
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from somnus import CORE_SCHEMA, MIGRATION_EXTENSION, ids, yamlsub
from somnus import document as D
from somnus.carriers.markdown import frontmatter_bounds
from somnus.commands._common import Ctx, display, note, unified
from somnus.config import Config
from somnus.infer import infer
from somnus.model import schema as S
from somnus.model import vocab
from somnus.model.validate import validate
from somnus.output import EXIT_INVALID, EXIT_OK, Diagnostic, SomnusError, emit
from somnus.regions import markdown_code_mask

EXTENSION_OWNER = "somnus-migration"
_OPEN = re.compile(r"^(:{3,})submatter:([A-Za-z][A-Za-z0-9_-]*)\{(.*)\}\s*$")
_CLOSE = re.compile(r"^(:{3,})\s*$")
_ATTR = re.compile(r'([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*"([^"]*)"')
_UUIDISH = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-")
_TS = re.compile(S.TIMESTAMP_PATTERN + r"\Z")
_DATE = re.compile(S.DATE_PATTERN + r"\Z")
_KEBAB = re.compile(S.KEBAB_PATTERN + r"\Z")
_RELATION_BUCKETS = ("supersedes", "derived_from", "cites")


class MigrationError(Exception):
    """Migration refused; the file is left untouched."""

    def __init__(self, line: int, message: str):
        super().__init__(message)
        self.line = line


# --------------------------------------------------------------------------- helpers


def _clean(value: Any) -> Any:
    """Drop nulls recursively so extension data stays serializable."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_clean(v) for v in value if v is not None]
    return value


def _timestamp(value: Any) -> Optional[str]:
    if isinstance(value, str) and _TS.match(value):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value
        except ValueError:
            return None
    return None


def _date(value: Any) -> Optional[str]:
    if isinstance(value, str) and _DATE.match(value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            return None
    return None


def _unique(base: str, used: set) -> str:
    candidate, n = base, 2
    while candidate in used:
        candidate, n = f"{base}-{n}", n + 1
    used.add(candidate)
    return candidate


def _region_id(kind: str, raw: Optional[str], used: set, ordinal: int) -> str:
    kind_slug = ids.slugify(kind)
    if raw and ids.is_local_id(raw) and raw not in used:
        used.add(raw)
        return raw
    if raw and _UUIDISH.match(raw):
        return _unique(f"r-{kind_slug}-{raw[:8].lower()}", used)
    return _unique(f"r-{kind_slug}-{ordinal}", used)


# --------------------------------------------------------------------------- directives


def convert_directives(lines: list[str], offset: int) -> tuple[list[str], list[dict], list[dict]]:
    """Replace live ``:::submatter`` directives with marker pairs.

    Returns (new body lines, region records, preserved directive attributes).
    ``offset`` is the 0-based file line of ``lines[0]`` (for error positions).
    """
    mask = markdown_code_mask(lines)
    out: list[str] = []
    regions: list[dict] = []
    preserved: list[dict] = []
    stack: list[tuple[int, str, int]] = []
    used: set = set()
    marker_rows: set = set()
    for i, line in enumerate(lines):
        if mask[i]:
            out.append(line)
            continue
        m = _OPEN.match(line)
        if m:
            colons, kind, attr_text = len(m.group(1)), m.group(2), m.group(3)
            attrs = dict(_ATTR.findall(attr_text))
            rid = _region_id(kind, attrs.get("id"), used, len(regions) + 1)
            stack.append((colons, rid, offset + i + 1))
            region_kind = kind if kind in vocab.REGION_KINDS else "section"
            regions.append({"id": rid, "kind": region_kind, "selector": {"kind": "marker", "name": rid}})
            record = {"region": rid, "directive": kind}
            if attrs:
                record["attributes"] = attrs
            preserved.append(record)
            marker_rows.add(len(out))
            out.append(f"<!-- somnus:region:begin {rid} -->")
            continue
        c = _CLOSE.match(line)
        if c and stack and len(c.group(1)) == stack[-1][0]:
            _, rid, _ = stack.pop()
            marker_rows.add(len(out))
            out.append(f"<!-- somnus:region:end {rid} -->")
            continue
        out.append(line)
    if stack:
        raise MigrationError(stack[-1][2], f"submatter directive {stack[-1][1]!r} is never closed")
    spaced: list[str] = []
    for i, line in enumerate(out):
        if i in marker_rows and spaced and spaced[-1].strip():
            spaced.append("")
        spaced.append(line)
        if i in marker_rows and i + 1 < len(out) and out[i + 1].strip():
            spaced.append("")
    return spaced, regions, preserved


# --------------------------------------------------------------------------- header


def build_payload(legacy: dict, cfg: Config, path: Path, regions: list[dict], directives: list[dict]) -> dict:
    """Map a lenient-parsed v0.1 header to a core 2.0.0 payload (SPEC §22 steps 1–8)."""
    rest = copy.deepcopy(legacy)
    unmapped: dict[str, Any] = {}

    raw_id = rest.pop("id", None)
    if not isinstance(raw_id, str):
        raise MigrationError(1, "legacy header has no 'id'")
    aid = ids.normalize_legacy_ref(raw_id.strip())
    if not ids.is_artifact_urn(aid):
        raise MigrationError(1, f"legacy id {raw_id!r} is not a UUID")

    legacy_somnus = rest.pop("somnus", None)
    if legacy_somnus is not None:
        unmapped["somnus"] = legacy_somnus

    cls_in = rest.pop("classification", {}) or {}
    cls_in = cls_in if isinstance(cls_in, dict) else {"value": cls_in}
    type_ = cls_in.pop("type", None)
    if type_ not in vocab.TYPES:
        if type_ is not None:
            unmapped.setdefault("classification", {})["type"] = type_
        type_ = infer(path, []).type
    guess = infer(path, [], type_override=type_)
    classification: dict[str, Any] = {"type": type_}
    for key, values, fallback in (("category", vocab.CATEGORIES, guess.category),
                                  ("role", vocab.ROLES, guess.role),
                                  ("scope", vocab.SCOPES, cfg.defaults["scope"])):
        value = cls_in.pop(key, None)
        if value in values:
            classification[key] = value
        else:
            if value is not None:
                unmapped.setdefault("classification", {})[key] = value
            classification[key] = fallback
    subtype = cls_in.pop("subtype", None)
    if isinstance(subtype, str) and _KEBAB.match(subtype):
        classification["subtype"] = subtype
    elif subtype is not None:
        unmapped.setdefault("classification", {})["subtype"] = subtype
    tags_in = cls_in.pop("tags", []) or []
    tags: list[str] = []
    for tag in tags_in if isinstance(tags_in, list) else [tags_in]:
        if isinstance(tag, str) and tag.strip() and tag not in tags:
            tags.append(tag)
    classification["tags"] = tags
    if cls_in:
        unmapped.setdefault("classification", {}).update(cls_in)

    life_in = rest.pop("lifecycle", {}) or {}
    life_in = life_in if isinstance(life_in, dict) else {"value": life_in}
    status = life_in.pop("status", None)
    if status not in vocab.STATUSES:
        if status is not None:
            unmapped.setdefault("lifecycle", {})["status"] = status
        status = "draft"
    lifecycle: dict[str, Any] = {"status": status}
    reviewed_at = life_in.pop("reviewed_at", None)
    if life_in:
        unmapped.setdefault("lifecycle", {}).update(life_in)

    rel_in = rest.pop("relations", {}) or {}
    rel_in = rel_in if isinstance(rel_in, dict) else {"value": rel_in}
    if status == "superseded":
        replacements = [ids.normalize_legacy_ref(r) for r in rel_in.get("superseded_by", []) or []
                        if isinstance(r, str)]
        replacements = [r for r in replacements if ids.is_reference_string(r)]
        if not replacements:
            raise MigrationError(1, "status 'superseded' has no resolvable superseded_by reference")
        lifecycle["replacement_refs"] = [{"ref": r} for r in replacements]
    relations: list[dict] = []
    used_rel: set = set()
    for bucket in _RELATION_BUCKETS:
        values = rel_in.pop(bucket, []) or []
        leftovers = []
        for value in values if isinstance(values, list) else [values]:
            ref = ids.normalize_legacy_ref(value.strip()) if isinstance(value, str) else None
            if ref is None or not ids.is_reference_string(ref):
                leftovers.append(value)
                continue
            relations.append({
                "id": _unique(f"rel-{bucket.replace('_', '-')}-{len(relations) + 1}", used_rel),
                "subject": {"ref": aid},
                "predicate": bucket,
                "object": {"ref": ref},
                "assessment": "unassessed",
                "valid_time": {"basis": "unknown"},
            })
        if leftovers:
            unmapped.setdefault("relations", {})[bucket] = leftovers
    if rel_in:
        unmapped.setdefault("relations", {}).update(rel_in)

    time: dict[str, Any] = {}
    for key, value in (("created_at", rest.pop("created_at", None)), ("updated_at", rest.pop("updated_at", None)),
                       ("reviewed_at", reviewed_at)):
        if value is None:
            continue
        if _timestamp(value):
            time[key] = value
        elif key == "created_at" and _date(value):
            time["authored_on"] = value
        else:
            unmapped.setdefault("time", {})[key] = value
    if "created_at" in time and "updated_at" in time:
        if datetime.fromisoformat(time["updated_at"].replace("Z", "+00:00")) < \
                datetime.fromisoformat(time["created_at"].replace("Z", "+00:00")):
            unmapped.setdefault("time", {})["updated_at"] = time.pop("updated_at")
    ordered_time = {k: time[k] for k in ("created_at", "updated_at", "reviewed_at", "authored_on") if k in time}

    names: dict[str, Any] = {}
    slug = rest.pop("slug", None)
    if isinstance(slug, str) and _KEBAB.match(slug):
        names["slug"] = slug
    elif slug is not None:
        unmapped["slug"] = slug
    aliases_in = rest.pop("aliases", []) or []
    aliases, used_alias, bad_aliases = [], set(), []
    for alias in aliases_in if isinstance(aliases_in, list) else [aliases_in]:
        if isinstance(alias, str) and alias.strip():
            aliases.append({"id": _unique(f"alias-{ids.slugify(alias)}", used_alias), "label": alias,
                            "kind": "short-name", "valid_time": {"basis": "unknown"}})
        else:
            bad_aliases.append(alias)
    if aliases:
        names["aliases"] = aliases
    if bad_aliases:
        unmapped["aliases"] = bad_aliases

    locations: list[dict] = []
    for key, role in (("location", "primary"), ("origin", "origin")):
        block = rest.pop(key, None)
        if block is None:
            continue
        if not isinstance(block, dict):
            unmapped[key] = block
            continue
        block = dict(block)
        primary = block.pop("path", None)
        if isinstance(primary, str) and primary.strip():
            locations.append({"kind": "repository-path", "locator": primary, "role": role})
        elif primary is not None:
            block["path"] = primary
        if key == "location":
            history = block.pop("historical_paths", []) or []
            for old in history if isinstance(history, list) else [history]:
                if isinstance(old, str) and old.strip():
                    locations.append({"kind": "repository-path", "locator": old, "role": "historical"})
        if block:
            unmapped[key] = block

    title = rest.pop("title", None)
    if not isinstance(title, str) or not title.strip():
        if title is not None:
            unmapped["title"] = title
        title = infer(path, []).title

    payload: dict[str, Any] = {"schema": CORE_SCHEMA, "id": aid, "revision": 1, "title": title.strip()}
    for src, dst in (("description", "summary"), ("purpose", "purpose")):
        value = rest.pop(src, None)
        if isinstance(value, str) and value.strip():
            payload[dst] = value.strip()
        elif value is not None:
            unmapped[src] = value
    payload["classification"] = classification
    payload["lifecycle"] = lifecycle
    payload["authority"] = {"standing": "candidate", "scopes": [{"target_ref": aid, "aspects": ["content"]}]}
    payload["time"] = ordered_time
    if names:
        payload["names"] = names
    if locations:
        payload["locations"] = locations
    knowledge: dict[str, Any] = {"coverage": "artifact", "subjects": [aid]}
    if regions:
        knowledge["regions"] = regions
    if relations:
        knowledge["relations"] = relations
    payload["knowledge"] = knowledge
    d = cfg.defaults
    payload["access"] = {"visibility": d["visibility"], "allowed_uses": list(d["allowed_uses"])}
    payload["ingestion"] = {"disposition": d["disposition"], "body_role": guess.body_role}
    unmapped.update(rest)
    if directives:
        unmapped["directives"] = directives
    data = _clean(unmapped)
    if data:
        payload["extensions"] = {EXTENSION_OWNER: {"schema": MIGRATION_EXTENSION, "data": data}}
    return payload


# --------------------------------------------------------------------------- driver


def plan(path: Path, cfg: Config) -> Optional[tuple[str, str, dict]]:
    """Return (old text, new text, payload), or None when the file is already core 2.0.0."""
    doc = D.load(path, lenient=True)
    if doc.is_sidecar:
        raise MigrationError(1, "migrate converts Markdown frontmatter documents only")
    lines = doc.lines
    close, opened = frontmatter_bounds(lines)
    if close is None:
        raise MigrationError(1, "no closed YAML frontmatter to migrate")
    try:
        parsed = yamlsub.parse("\n".join(lines[1:close]) + "\n", lenient=True).data
    except yamlsub.YAMLError as exc:
        raise MigrationError(1 + exc.line, f"legacy frontmatter cannot be parsed: {exc.message}") from exc
    if not isinstance(parsed, dict):
        raise MigrationError(1, "legacy frontmatter is not a mapping")
    somnus = parsed.get("somnus")
    if isinstance(somnus, dict) and somnus.get("schema") == CORE_SCHEMA:
        return None
    body, regions, directives = convert_directives(lines[close + 1:], close + 1)
    payload = build_payload(parsed, cfg, doc.path, regions, directives)
    header = D.canonical_yaml({"somnus": payload}).rstrip("\n").split("\n")
    nl = doc.newline
    new_lines = ["---", *header, "---", *body]
    trailing = nl if (doc.endings and doc.endings[-1]) else ""
    new = nl.join(new_lines) + trailing
    old = "".join(line + end for line, end in zip(doc.lines, doc.endings))
    return old, new, payload


def run(args, ctx: Ctx) -> int:
    """Dry-run diff by default; ``--write`` writes after core validation."""
    status = EXIT_OK
    for raw in args.paths:
        path = Path(raw).resolve()
        shown = display(path)
        try:
            result = plan(path, ctx.cfg)
        except MigrationError as exc:
            ctx.diagnostics([Diagnostic(shown, exc.line, 1, "error", "E_SCHEMA", "-", str(exc))])
            status = EXIT_INVALID
            continue
        except SomnusError as exc:
            ctx.diagnostics(exc.diagnostics)
            status = max(status, exc.exit_code)
            continue
        if result is None:
            note(f"{shown}: already core 2.0.0; skipped")
            continue
        old, new, payload = result
        errors = [d for d in validate(D.from_text(path, new), "core") if d.is_error]
        if errors:
            ctx.diagnostics(errors)
            note(f"{shown}: migration result does not validate; file left untouched")
            status = EXIT_INVALID
            continue
        if not args.write:
            emit(unified(old, new, shown))
            continue
        D.atomic_write(path, new)
        regions = len(payload["knowledge"].get("regions", []))
        ctx.record("migrate", path, payload["id"], 1, f"v0.1 -> core 2.0.0; {regions} region(s)")
        note(f"{shown}: migrated {payload['id']} ({regions} region(s))")
    return status
