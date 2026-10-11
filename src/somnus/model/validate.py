"""Multi-stage validation pipeline: carrier, core, semantic, canon (SPEC §19)."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from somnus import ids
from somnus.carriers.sidecar import SIDECAR, binding_issues, primary_target
from somnus.document import Document
from somnus.model import schema as S
from somnus.model import vocab
from somnus.output import Diagnostic
from somnus.regions import MarkerScan, headings, scan_markers, tex_labels

LEVEL_RANK = {name: i for i, name in enumerate(vocab.LEVELS)}
_TS_RE = re.compile(S.TIMESTAMP_PATTERN + r"\Z")
_DATE_RE = re.compile(S.DATE_PATTERN + r"\Z")


# --------------------------------------------------------------------------- resolver


@dataclass
class ArtifactFacts:
    """What the resolver knows about one artifact."""

    id: str
    type: str = ""
    status: str = ""
    standing: str = ""
    current_revision: int = 0
    revisions: set = field(default_factory=set)
    regions: dict = field(default_factory=dict)  # revision -> set of region ids
    claims: dict = field(default_factory=dict)  # revision -> set of claim ids


@dataclass
class Resolver:
    """Reference resolution context: registry facts plus the current check set."""

    artifacts: dict = field(default_factory=dict)
    entities: set = field(default_factory=set)
    open_conflicts: dict = field(default_factory=dict)  # artifact id -> list of conflict kinds

    def add_payload(self, somnus: dict) -> None:
        """Register facts from a parsed payload (check-set member)."""
        aid = somnus.get("id")
        if not isinstance(aid, str):
            return
        rev = somnus.get("revision") if isinstance(somnus.get("revision"), int) else 0
        facts = self.artifacts.setdefault(aid, ArtifactFacts(aid))
        cls = somnus.get("classification", {}) if isinstance(somnus.get("classification"), dict) else {}
        if rev >= facts.current_revision:
            facts.current_revision = rev
            facts.type = cls.get("type", facts.type)
            facts.status = (somnus.get("lifecycle") or {}).get("status", facts.status)
            facts.standing = (somnus.get("authority") or {}).get("standing", facts.standing)
        facts.revisions.add(rev)
        knowledge = somnus.get("knowledge", {}) if isinstance(somnus.get("knowledge"), dict) else {}
        facts.regions[rev] = {r.get("id") for r in knowledge.get("regions", []) if isinstance(r, dict)}
        facts.claims[rev] = {c.get("id") for c in knowledge.get("claims", []) if isinstance(c, dict)}
        for ent in knowledge.get("entities", []):
            if isinstance(ent, dict) and isinstance(ent.get("ref"), str) and not ids.is_example_urn(ent["ref"]):
                self.entities.add(ent["ref"])


# --------------------------------------------------------------------------- helpers


def _parse_ts(value: str) -> Optional[datetime]:
    if not _TS_RE.match(value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


class _Run:
    """Accumulates diagnostics for one document."""

    def __init__(self, doc: Document):
        self.doc = doc
        self.out: list[Diagnostic] = []

    def err(self, path: tuple, code: str, message: str) -> None:
        self.out.append(self.doc.diag(path, code, message))

    def warn(self, path: tuple, code: str, message: str) -> None:
        self.out.append(self.doc.diag(path, code, message, severity="warning"))

    def at(self, line: int, col: int, code: str, message: str, severity: str = "error") -> None:
        self.out.append(Diagnostic(self.doc.display, line, col, severity, code, "-", message))


# --------------------------------------------------------------------------- stage 2: structure


def walk(run: _Run, node: Any, value: Any, path: tuple) -> None:
    """Check ``value`` against a schema node, recording E_SCHEMA findings."""
    if isinstance(node, S.Str):
        if not isinstance(value, str):
            run.err(path, "E_SCHEMA", f"expected a string, got {_kind(value)}")
            return
        if len(value) < node.min_len or (node.min_len and not value.strip()):
            run.err(path, "E_SCHEMA", "string must not be empty")
            return
        if node.enum is not None and value not in node.enum:
            shown = ", ".join(node.enum) if len(node.enum) <= 12 else ", ".join(node.enum[:12]) + ", ..."
            run.err(path, "E_SCHEMA", f"{value!r} is not one of: {shown}")
        if node.pattern is not None and not re.fullmatch(node.pattern, value):
            run.err(path, "E_SCHEMA", f"{value!r} does not match the required pattern")
        if node.fmt == "timestamp" and _parse_ts(value) is None:
            run.err(path, "E_TEMPORAL", f"{value!r} is not an RFC 3339 timestamp with an explicit offset")
        if node.fmt == "date":
            ok = bool(_DATE_RE.match(value))
            if ok:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    ok = False
            if not ok:
                run.err(path, "E_TEMPORAL", f"{value!r} is not a calendar date YYYY-MM-DD")
    elif isinstance(node, S.Int):
        if isinstance(value, bool) or not isinstance(value, int):
            run.err(path, "E_SCHEMA", f"expected an integer, got {_kind(value)}")
        elif node.minimum is not None and value < node.minimum:
            run.err(path, "E_SCHEMA", f"must be >= {node.minimum}")
    elif isinstance(node, S.Num):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            run.err(path, "E_SCHEMA", f"expected a number, got {_kind(value)}")
        else:
            if node.minimum is not None and value < node.minimum:
                run.err(path, "E_SCHEMA", f"must be >= {node.minimum}")
            if node.maximum is not None and value > node.maximum:
                run.err(path, "E_SCHEMA", f"must be <= {node.maximum}")
    elif isinstance(node, S.Bool):
        if not isinstance(value, bool):
            run.err(path, "E_SCHEMA", f"expected a boolean, got {_kind(value)}")
    elif isinstance(node, S.AnyValue):
        return
    elif isinstance(node, S.Arr):
        if not isinstance(value, list):
            run.err(path, "E_SCHEMA", f"expected an array, got {_kind(value)}")
            return
        if len(value) < node.min_items:
            run.err(path, "E_SCHEMA", f"requires at least {node.min_items} item(s)")
        if node.unique:
            seen: set[str] = set()
            for i, item in enumerate(value):
                key = _canon(item)
                if key in seen:
                    run.err(path + (i,), "E_SCHEMA", "duplicate array item")
                seen.add(key)
        for i, item in enumerate(value):
            walk(run, node.item, item, path + (i,))
    elif isinstance(node, S.Obj):
        _walk_obj(run, node, value, path)
    elif isinstance(node, S.Tagged):
        if not isinstance(value, dict):
            run.err(path, "E_SCHEMA", f"expected an object, got {_kind(value)}")
            return
        tag = value.get(node.tag)
        if tag not in node.variants:
            run.err(path + (node.tag,), "E_SCHEMA", f"{node.tag} must be one of: {', '.join(node.variants)}")
            return
        _walk_obj(run, node.variants[tag], value, path)
    elif isinstance(node, S.MapOf):
        if not isinstance(value, dict):
            run.err(path, "E_SCHEMA", f"expected a mapping, got {_kind(value)}")
            return
        for k, v in value.items():
            if not re.fullmatch(node.key_pattern, k):
                run.err(path + (k,), "E_SCHEMA", f"key {k!r} does not match {node.key_pattern}")
            walk(run, node.value, v, path + (k,))
    elif isinstance(node, S.Union_):
        for option in node.options:
            if isinstance(option, S.Str) and isinstance(value, str):
                walk(run, option, value, path)
                return
            if isinstance(option, S.Obj) and isinstance(value, dict):
                walk(run, option, value, path)
                return
        run.err(path, "E_SCHEMA", f"expected {S.describe(node)}, got {_kind(value)}")


def _walk_obj(run: _Run, node: S.Obj, value: Any, path: tuple) -> None:
    if not isinstance(value, dict):
        run.err(path, "E_SCHEMA", f"expected an object <{node.name}>, got {_kind(value)}")
        return
    for key in value:
        if node.get(key) is None:
            hint = "; experimental keys belong under somnus.extensions" if path == ("somnus",) else ""
            run.err(path + (key,), "E_SCHEMA", f"unknown field {key!r}{hint}")
    for f in node.fields:
        if f.name in value:
            walk(run, f.node, value[f.name], path + (f.name,))
        elif f.required:
            run.err(path, "E_SCHEMA", f"missing required field {f.name!r}")


def _kind(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


# --------------------------------------------------------------------------- stage 3: consistency


def _dicts(value: Any) -> list[dict]:
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def _iter_valid_times(value: Any, path: tuple) -> Iterable[tuple[tuple, dict]]:
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "extensions" and path == ("somnus",):
                continue
            if k == "valid_time" and isinstance(v, dict):
                yield path + (k,), v
            else:
                yield from _iter_valid_times(v, path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _iter_valid_times(v, path + (i,))


def _check_valid_time(run: _Run, path: tuple, vt: dict) -> None:
    basis = vt.get("basis")
    has_from, has_until = "from" in vt, "until" in vt
    if basis == "bounded":
        if not (has_from and has_until):
            run.err(path, "E_TEMPORAL", "basis 'bounded' requires both from and until")
        else:
            a, b = _parse_ts(str(vt["from"])), _parse_ts(str(vt["until"]))
            if a and b and not a < b:
                run.err(path + ("until",), "E_TEMPORAL", "until must be strictly after from")
    elif basis == "open":
        if not has_from:
            run.err(path, "E_TEMPORAL", "basis 'open' requires from")
        if has_until:
            run.err(path + ("until",), "E_TEMPORAL", "basis 'open' forbids until")
    elif basis in ("timeless", "unknown"):
        for bound in ("from", "until"):
            if bound in vt:
                run.err(path + (bound,), "E_TEMPORAL", f"basis {basis!r} forbids {bound}")


def _unique_ids(run: _Run, items: list, path: tuple, label: str) -> set:
    seen: set = set()
    for i, item in enumerate(items):
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            if item["id"] in seen:
                run.err(path + (i, "id"), "E_SCHEMA", f"duplicate {label} id {item['id']!r}")
            seen.add(item["id"])
    return seen


def consistency(run: _Run, somnus: dict) -> None:
    """Intra-document conditional requirements (core level)."""
    P = ("somnus",)
    authority = somnus.get("authority") if isinstance(somnus.get("authority"), dict) else {}
    standing = authority.get("standing")
    if isinstance(authority.get("scopes"), list) and not authority["scopes"] and standing not in (None, "unasserted"):
        run.err(P + ("authority", "scopes"), "E_AUTHORITY", "scopes may be empty only when standing is 'unasserted'")
    if standing == "accepted":
        for req in ("valid_time", "acceptance_ref"):
            if req not in authority:
                run.err(P + ("authority",), "E_AUTHORITY", f"standing 'accepted' requires {req}")

    lifecycle = somnus.get("lifecycle") if isinstance(somnus.get("lifecycle"), dict) else {}
    if lifecycle.get("status") == "superseded" and not lifecycle.get("replacement_refs"):
        run.err(P + ("lifecycle",), "E_SCHEMA", "status 'superseded' requires replacement_refs")

    time = somnus.get("time") if isinstance(somnus.get("time"), dict) else {}
    created = _parse_ts(str(time.get("created_at", "")))
    updated = _parse_ts(str(time.get("updated_at", "")))
    if created and updated and updated < created:
        run.err(P + ("time", "updated_at"), "E_TEMPORAL", "updated_at precedes created_at")

    for path, vt in _iter_valid_times(somnus, P):
        _check_valid_time(run, path, vt)

    ownership = somnus.get("ownership") if isinstance(somnus.get("ownership"), dict) else {}
    rights = ownership.get("rights") if isinstance(ownership.get("rights"), dict) else None
    if rights is not None:
        if rights.get("status") == "specified" and "license_expression" not in rights:
            run.err(P + ("ownership", "rights"), "E_SCHEMA", "status 'specified' requires license_expression")
        if rights.get("status") in ("unspecified", "restricted") and "license_expression" in rights:
            run.err(P + ("ownership", "rights", "license_expression"), "E_SCHEMA",
                    "license_expression is only allowed when status is 'specified'")

    names = somnus.get("names") if isinstance(somnus.get("names"), dict) else {}
    _unique_ids(run, names.get("aliases", []), P + ("names", "aliases"), "alias")

    knowledge = somnus.get("knowledge") if isinstance(somnus.get("knowledge"), dict) else {}
    K = P + ("knowledge",)
    regions = _dicts(knowledge.get("regions"))
    claims = _dicts(knowledge.get("claims"))
    region_ids = _unique_ids(run, knowledge.get("regions", []) if isinstance(knowledge.get("regions"), list) else [],
                             K + ("regions",), "region")
    claim_ids = _unique_ids(run, knowledge.get("claims", []) if isinstance(knowledge.get("claims"), list) else [],
                            K + ("claims",), "claim")
    _unique_ids(run, knowledge.get("relations", []) if isinstance(knowledge.get("relations"), list) else [],
                K + ("relations",), "relation")
    _unique_ids(run, knowledge.get("terms", []) if isinstance(knowledge.get("terms"), list) else [],
                K + ("terms",), "term")
    entity_refs: set = set()
    for i, ent in enumerate(knowledge.get("entities", []) if isinstance(knowledge.get("entities"), list) else []):
        if isinstance(ent, dict):
            if ent.get("ref") in entity_refs:
                run.err(K + ("entities", i, "ref"), "E_SCHEMA", f"entity {ent.get('ref')!r} declared twice")
            entity_refs.add(ent.get("ref"))
            _unique_ids(run, ent.get("aliases", []) if isinstance(ent.get("aliases"), list) else [],
                        K + ("entities", i, "aliases"), "entity alias")

    doc_vis = (somnus.get("access") or {}).get("visibility") if isinstance(somnus.get("access"), dict) else None
    doc_uses = set((somnus.get("access") or {}).get("allowed_uses", []) or []) if isinstance(somnus.get("access"), dict) else set()
    claims_by_id = {c.get("id"): c for c in claims}
    for i, reg in enumerate(knowledge.get("regions", []) if isinstance(knowledge.get("regions"), list) else []):
        if not isinstance(reg, dict):
            continue
        rp = K + ("regions", i)
        for j, cid in enumerate(reg.get("claim_ids", []) if isinstance(reg.get("claim_ids"), list) else []):
            if cid not in claim_ids:
                run.err(rp + ("claim_ids", j), "E_REGION", f"claim {cid!r} is not declared")
            elif claims_by_id[cid].get("region_ref") != reg.get("id"):
                run.err(rp + ("claim_ids", j), "E_REGION",
                        f"claim {cid!r} has region_ref {claims_by_id[cid].get('region_ref')!r}, not {reg.get('id')!r}")
        r_auth = reg.get("authority") if isinstance(reg.get("authority"), dict) else {}
        if r_auth.get("standing") == "accepted" and standing != "accepted":
            run.err(rp + ("authority", "standing"), "E_AUTHORITY", "a region cannot be accepted unless its document is")
        r_acc = reg.get("access") if isinstance(reg.get("access"), dict) else {}
        r_vis = r_acc.get("visibility")
        if r_vis in vocab.VISIBILITY_RANK and doc_vis in vocab.VISIBILITY_RANK:
            if vocab.VISIBILITY_RANK[r_vis] > vocab.VISIBILITY_RANK[doc_vis]:
                run.err(rp + ("access", "visibility"), "E_POLICY", "region visibility is wider than the document's")
        extra = set(r_acc.get("allowed_uses", []) or []) - doc_uses if isinstance(r_acc.get("allowed_uses"), list) else set()
        if extra:
            run.err(rp + ("access", "allowed_uses"), "E_POLICY",
                    f"region allows uses the document does not: {', '.join(sorted(extra))}")

    for i, claim in enumerate(knowledge.get("claims", []) if isinstance(knowledge.get("claims"), list) else []):
        if not isinstance(claim, dict):
            continue
        cp = K + ("claims", i)
        obj = claim.get("object")
        if isinstance(obj, dict):
            has_ref, has_value = "ref" in obj, "value" in obj
            if has_ref == has_value:
                run.err(cp + ("object",), "E_SCHEMA", "object must contain exactly one of ref or value")
            elif has_value and set(obj) - {"value"}:
                run.err(cp + ("object",), "E_SCHEMA", "an object value cannot carry reference fields")
        if claim.get("assessment") == "supported" and not claim.get("evidence_refs"):
            run.err(cp + ("assessment",), "E_SCHEMA", "assessment 'supported' requires evidence_refs")
        if isinstance(claim.get("region_ref"), str) and claim["region_ref"] not in region_ids:
            run.err(cp + ("region_ref",), "E_REGION", f"region {claim['region_ref']!r} is not declared")

    acyclic_edges: list[tuple[str, str, tuple]] = []
    for i, rel in enumerate(knowledge.get("relations", []) if isinstance(knowledge.get("relations"), list) else []):
        if not isinstance(rel, dict):
            continue
        rp = K + ("relations", i)
        pred = rel.get("predicate")
        if isinstance(pred, str) and pred not in vocab.RELATION_PREDICATES:
            run.warn(rp + ("predicate",), "W_PREDICATE", f"unregistered predicate {pred!r} is preserved but not used")
        if rel.get("assessment") == "supported" and not rel.get("evidence_refs"):
            run.err(rp + ("assessment",), "E_SCHEMA", "assessment 'supported' requires evidence_refs")
        if isinstance(rel.get("region_ref"), str) and rel["region_ref"] not in region_ids:
            run.err(rp + ("region_ref",), "E_REGION", f"region {rel['region_ref']!r} is not declared")
        subj = rel.get("subject", {}).get("ref") if isinstance(rel.get("subject"), dict) else None
        obj = rel.get("object", {}).get("ref") if isinstance(rel.get("object"), dict) else None
        if pred in vocab.RELATION_PREDICATES and vocab.RELATION_PREDICATES[pred][1] and subj and obj:
            if subj == obj and _ref_key(rel["subject"]) == _ref_key(rel["object"]):
                run.err(rp, "E_GRAPH", f"{pred} cannot relate an artifact to itself")
            acyclic_edges.append((pred, f"{subj}\x00{obj}", rp))
    for pred in {e[0] for e in acyclic_edges}:
        graph: dict[str, set[str]] = {}
        paths: dict[tuple[str, str], tuple] = {}
        for p, pair, rp in acyclic_edges:
            if p != pred:
                continue
            a, b = pair.split("\x00")
            if a != b:
                graph.setdefault(a, set()).add(b)
                paths[(a, b)] = rp
        cycle = find_cycle(graph)
        if cycle:
            run.err(paths.get((cycle[0], cycle[1]), K), "E_GRAPH", f"{pred} cycle: {' -> '.join(cycle)}")

    for i, term in enumerate(knowledge.get("terms", []) if isinstance(knowledge.get("terms"), list) else []):
        if isinstance(term, dict) and isinstance(term.get("region_ref"), str) and term["region_ref"] not in region_ids:
            run.err(K + ("terms", i, "region_ref"), "E_REGION", f"region {term['region_ref']!r} is not declared")

    ingestion = somnus.get("ingestion") if isinstance(somnus.get("ingestion"), dict) else {}
    for key in ("include_regions", "exclude_regions", "atomic_regions"):
        for j, rid in enumerate(ingestion.get(key, []) if isinstance(ingestion.get(key), list) else []):
            if rid not in region_ids:
                run.err(P + ("ingestion", key, j), "E_REGION", f"region {rid!r} is not declared")
    content = somnus.get("content") if isinstance(somnus.get("content"), dict) else {}
    math = content.get("math") if isinstance(content.get("math"), dict) else {}
    for j, rid in enumerate(math.get("equation_region_ids", []) if isinstance(math.get("equation_region_ids"), list) else []):
        if rid not in region_ids:
            run.err(P + ("content", "math", "equation_region_ids", j), "E_REGION", f"region {rid!r} is not declared")

    _profiles(run, somnus, region_ids)


def _ref_key(ref: dict) -> tuple:
    return (ref.get("ref"), ref.get("revision"), ref.get("region"), ref.get("claim"))


def find_cycle(graph: dict[str, set[str]]) -> Optional[list[str]]:
    """Return one cycle as a node list (first node repeated at the end), or None."""
    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> Optional[list[str]]:
        color[node] = GREY
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            state = color.get(nxt, WHITE)
            if state == GREY:
                return stack[stack.index(nxt):] + [nxt]
            if state == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    for start in sorted(graph):
        if color.get(start, WHITE) == WHITE:
            found = visit(start)
            if found:
                return found
    return None


def _profiles(run: _Run, somnus: dict, region_ids: set) -> None:
    P = ("somnus",)
    decls = somnus.get("profiles") if isinstance(somnus.get("profiles"), list) else []
    data = somnus.get("profile_data") if isinstance(somnus.get("profile_data"), dict) else {}
    keys: dict[str, str] = {}
    schemas: set = set()
    for i, decl in enumerate(decls):
        if not isinstance(decl, dict):
            continue
        key, uri = decl.get("key"), decl.get("schema")
        if key in keys:
            run.err(P + ("profiles", i, "key"), "E_SCHEMA", f"duplicate profile key {key!r}")
        if uri in schemas:
            run.err(P + ("profiles", i, "schema"), "E_SCHEMA", f"duplicate profile schema {uri!r}")
        if isinstance(uri, str) and uri not in S.PROFILES:
            run.err(P + ("profiles", i, "schema"), "E_SCHEMA",
                    f"unknown profile release {uri!r}; source retained, semantic acceptance refused")
        if isinstance(key, str):
            keys[key] = uri
        schemas.add(uri)
    for key in data:
        if key not in keys:
            run.err(P + ("profile_data", key), "E_SCHEMA", f"profile_data.{key} has no declared profile")
    for key, uri in keys.items():
        if key not in data:
            run.err(P + ("profile_data",), "E_SCHEMA", f"declared profile {key!r} has no profile_data entry")
            continue
        node = S.PROFILES.get(uri)
        if node is None:
            continue
        walk(run, node, data[key], P + ("profile_data", key))
        payload = data[key] if isinstance(data[key], dict) else {}
        refs = payload.get("normative_region_refs")
        for j, rid in enumerate(refs if isinstance(refs, list) else []):
            if rid not in region_ids:
                run.err(P + ("profile_data", key, "normative_region_refs", j), "E_REGION",
                        f"region {rid!r} is not declared")


def marker_regions(run: _Run, somnus: dict) -> Optional[MarkerScan]:
    """Pair body markers and match them against marker-selector regions."""
    doc = run.doc
    style = getattr(doc.carrier, "region_style", ())
    knowledge = somnus.get("knowledge") if isinstance(somnus.get("knowledge"), dict) else {}
    regions = knowledge.get("regions") if isinstance(knowledge.get("regions"), list) else []
    marker_regs = [(i, r) for i, r in enumerate(regions)
                   if isinstance(r, dict) and isinstance(r.get("selector"), dict) and r["selector"].get("kind") == "marker"]
    if not style:
        for i, _ in marker_regs:
            run.err(("somnus", "knowledge", "regions", i, "selector"), "E_REGION",
                    "marker selectors need an embedded host; sidecars cannot carry markers")
        return None
    scan = scan_markers(doc.lines, style, doc.ignore_span, getattr(doc.carrier, "host", None))
    for line, col, code, message in scan.issues:
        run.at(line, col, code, message, "warning" if code.startswith("W_") else "error")
    names = set()
    for i, reg in marker_regs:
        name = reg["selector"].get("name")
        names.add(name)
        if name not in scan.ranges:
            run.err(("somnus", "knowledge", "regions", i, "selector", "name"), "E_REGION",
                    f"no paired body markers for region {name!r}")
    for rid, rng in scan.ranges.items():
        if rid not in names:
            run.at(rng.begin_line, 1, "W_REGION_UNREGISTERED",
                   f"marker region {rid!r} is not registered in knowledge.regions", "warning")
    return scan


# --------------------------------------------------------------------------- semantic stage


def _collect_refs(node: Any, value: Any, path: tuple, out: list) -> None:
    """Collect (path, ref string, reference object or None) at reference positions."""
    if isinstance(node, S.Str):
        if node.pattern in (S.REF_PATTERN, S.SOMNUS_URN_PATTERN) and isinstance(value, str):
            out.append((path, value, None))
    elif isinstance(node, S.Arr) and isinstance(value, list):
        for i, item in enumerate(value):
            _collect_refs(node.item, item, path + (i,), out)
    elif isinstance(node, (S.Obj, S.Tagged)) and isinstance(value, dict):
        obj = node if isinstance(node, S.Obj) else node.variants.get(value.get(node.tag))
        if obj is None:
            return
        if obj is S.REF or obj is S.CLAIM_OBJECT:
            if isinstance(value.get("ref"), str):
                out.append((path + ("ref",), value["ref"], value))
            return
        for f in obj.fields:
            if f.name in value and not (obj is S.ENTITY and f.name == "ref"):
                _collect_refs(f.node, value[f.name], path + (f.name,), out)
    elif isinstance(node, S.MapOf) and isinstance(value, dict):
        if node is S.SOMNUS.get("extensions").node:
            return
        for k, v in value.items():
            _collect_refs(node.value, v, path + (k,), out)
    elif isinstance(node, S.Union_):
        for option in node.options:
            if isinstance(option, S.Obj) and isinstance(value, dict):
                _collect_refs(option, value, path, out)


def references(run: _Run, somnus: dict, resolver: Resolver) -> None:
    """Resolve every reference against this document, the check set, and the registry."""
    found: list = []
    _collect_refs(S.SOMNUS, somnus, ("somnus",), found)
    profiles = {d.get("key"): d.get("schema") for d in somnus.get("profiles", []) if isinstance(d, dict)}
    for key, payload in (somnus.get("profile_data") or {}).items() if isinstance(somnus.get("profile_data"), dict) else []:
        node = S.PROFILES.get(profiles.get(key))
        if node is not None:
            _collect_refs(node, payload, ("somnus", "profile_data", key), found)
    own_id = somnus.get("id")
    own_rev = somnus.get("revision")
    knowledge = somnus.get("knowledge") if isinstance(somnus.get("knowledge"), dict) else {}
    declared = {e.get("ref") for e in _dicts(knowledge.get("entities"))}
    own_regions = {r.get("id") for r in _dicts(knowledge.get("regions"))}
    own_claims = {c.get("id") for c in _dicts(knowledge.get("claims"))}
    for path, ref, obj in found:
        if ids.is_external_ref(ref):
            continue
        if ref == own_id:
            if obj:
                if obj.get("region") and obj["region"] not in own_regions:
                    run.err(path, "E_REFERENCE", f"region {obj['region']!r} is not declared in this artifact")
                if obj.get("claim") and obj["claim"] not in own_claims:
                    run.err(path, "E_REFERENCE", f"claim {obj['claim']!r} is not declared in this artifact")
                if isinstance(obj.get("revision"), int) and isinstance(own_rev, int) and obj["revision"] > own_rev:
                    run.err(path, "E_REFERENCE", f"revision {obj['revision']} does not exist yet")
            continue
        try:
            kind, _ = ids.parse_urn(ref)
        except ValueError:
            run.err(path, "E_REFERENCE", f"{ref!r} is not resolvable")
            continue
        if kind == "example":
            if ref not in declared:
                run.err(path, "E_REFERENCE", f"example reference {ref!r} is not declared in this document")
            continue
        if kind == "artifact":
            facts = resolver.artifacts.get(ref)
            if facts is None:
                run.err(path, "E_REFERENCE", f"artifact {ref!r} is not in the registry or the check set")
                continue
            if obj:
                rev = obj.get("revision")
                if isinstance(rev, int) and facts.revisions and rev not in facts.revisions and rev > facts.current_revision:
                    run.err(path, "E_REFERENCE", f"artifact {ref!r} has no revision {rev}")
                target_rev = rev if isinstance(rev, int) else facts.current_revision
                if obj.get("region") and target_rev in facts.regions and obj["region"] not in facts.regions[target_rev]:
                    run.err(path, "E_REFERENCE", f"region {obj['region']!r} not found in {ref} revision {target_rev}")
                if obj.get("claim") and target_rev in facts.claims and obj["claim"] not in facts.claims[target_rev]:
                    run.err(path, "E_REFERENCE", f"claim {obj['claim']!r} not found in {ref} revision {target_rev}")
            continue
        if ref not in declared and ref not in resolver.entities:
            run.err(path, "E_REFERENCE", f"{kind} {ref!r} is not declared here or in the registry")


def selectors(run: _Run, somnus: dict) -> None:
    """Resolve non-marker region selectors."""
    doc = run.doc
    knowledge = somnus.get("knowledge") if isinstance(somnus.get("knowledge"), dict) else {}
    regions = knowledge.get("regions") if isinstance(knowledge.get("regions"), list) else []
    lines = doc.lines
    for i, reg in enumerate(regions):
        sel = reg.get("selector") if isinstance(reg, dict) else None
        if not isinstance(sel, dict):
            continue
        sp = ("somnus", "knowledge", "regions", i, "selector")
        kind = sel.get("kind")
        if kind == "heading":
            hits = [ln for text, ln in headings(lines, doc.ignore_span) if text == sel.get("text")]
            occ = sel.get("occurrence")
            if not isinstance(occ, int) or occ < 1 or occ > len(hits):
                run.err(sp, "E_REGION", f"heading {sel.get('text')!r} occurrence {occ} not found ({len(hits)} present)")
        elif kind == "line-range":
            a, b, rev = sel.get("from"), sel.get("until"), sel.get("revision")
            if isinstance(a, int) and isinstance(b, int):
                if not a < b <= len(lines) + 1:
                    run.err(sp, "E_REGION", f"line range {a}..{b} is outside the file ({len(lines)} lines)")
            if rev != somnus.get("revision"):
                run.err(sp + ("revision",), "E_REGION", "line-range selector is pinned to a different revision")
        elif kind == "tex-label":
            hits = [ln for label, ln in tex_labels(lines, doc.ignore_span) if label == sel.get("name")]
            if len(hits) != 1:
                run.err(sp, "E_REGION", f"expected exactly one \\label{{{sel.get('name')}}}, found {len(hits)}")
        elif kind == "symbol":
            if sel.get("language") != "python":
                run.err(sp + ("language",), "E_REGION", f"no symbol resolver for language {sel.get('language')!r}")
                continue
            try:
                tree = ast.parse("\n".join(doc.body_lines()) + "\n")
            except SyntaxError as exc:
                run.err(sp, "E_REGION", f"cannot parse Python source: {exc.msg}")
                continue
            name = sel.get("name")
            count = sum(1 for n in ast.walk(tree)
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name)
            if count != 1:
                run.err(sp, "E_REGION", f"expected exactly one definition of {name!r}, found {count}")
        elif kind == "json-pointer":
            target = primary_target(somnus, doc.meta_path) if doc.is_sidecar else None
            if target is None or not target.is_file():
                run.err(sp, "E_REGION", "json-pointer selectors need a sidecar with a resolvable primary target")
                continue
            try:
                tree = json.loads(target.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                run.err(sp, "E_REGION", f"primary target is not readable JSON: {exc}")
                continue
            if not _resolve_pointer(tree, str(sel.get("pointer", ""))):
                run.err(sp + ("pointer",), "E_REGION", f"pointer {sel.get('pointer')!r} does not resolve")


def _resolve_pointer(tree: Any, pointer: str) -> bool:
    if pointer == "":
        return True
    if not pointer.startswith("/"):
        return False
    node = tree
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and token in node:
            node = node[token]
        elif isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        else:
            return False
    return True


def semantic_policies(run: _Run, somnus: dict) -> None:
    """Resources, constraint languages, and required capabilities."""
    P = ("somnus",)
    base = run.doc.meta_path.parent
    content = somnus.get("content") if isinstance(somnus.get("content"), dict) else {}
    missing_required = False
    for i, res in enumerate(_dicts(content.get("resources"))):
        ref = res.get("ref")
        if res.get("required") is True and isinstance(ref, str) and not ids.is_reference_string(ref):
            if not (base / ref).exists():
                missing_required = True
                run.err(P + ("content", "resources", i, "ref"), "E_EXTRACTION", f"required resource {ref!r} is missing")
    math = content.get("math") if isinstance(content.get("math"), dict) else {}
    for i, ref in enumerate(math.get("macro_refs", []) if isinstance(math.get("macro_refs"), list) else []):
        if isinstance(ref, str) and not ids.is_reference_string(ref) and not (base / ref).exists():
            missing_required = True
            run.err(P + ("content", "math", "macro_refs", i), "E_EXTRACTION", f"macro source {ref!r} is missing")
    extraction = content.get("extraction") if isinstance(content.get("extraction"), dict) else {}
    if missing_required and extraction.get("state") == "complete":
        run.err(P + ("content", "extraction", "state"), "E_EXTRACTION",
                "extraction declared complete while required sources are missing")
    for path, constraint in _constraints(somnus, P):
        if constraint.get("language") not in vocab.CONSTRAINT_LANGUAGES:
            run.err(path + ("language",), "E_REFERENCE", f"unregistered constraint language {constraint.get('language')!r}")
    ingestion = somnus.get("ingestion") if isinstance(somnus.get("ingestion"), dict) else {}
    for i, cap in enumerate(ingestion.get("requires", []) if isinstance(ingestion.get("requires"), list) else []):
        if cap not in vocab.CAPABILITIES:
            run.err(P + ("ingestion", "requires", i), "E_POLICY", f"required capability {cap!r} is not available")


def _constraints(value: Any, path: tuple) -> Iterable[tuple[tuple, dict]]:
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "extensions" and path == ("somnus",):
                continue
            if k in ("conditions", "release_constraints", "platform_constraints") and isinstance(v, list):
                for i, c in enumerate(v):
                    if isinstance(c, dict):
                        yield path + (k, i), c
            else:
                yield from _constraints(v, path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _constraints(v, path + (i,))


def canon(run: _Run, somnus: dict, resolver: Resolver) -> None:
    """Canon-level checks: verified acceptance, current status, no open conflicts."""
    P = ("somnus",)
    authority = somnus.get("authority") if isinstance(somnus.get("authority"), dict) else {}
    if authority.get("standing") != "accepted":
        run.err(P + ("authority", "standing"), "E_AUTHORITY", "canon requires standing 'accepted'")
    acc = authority.get("acceptance_ref")
    if isinstance(acc, dict):
        facts = resolver.artifacts.get(acc.get("ref"))
        if facts is None or facts.type != "decision-record" or facts.status != "active":
            run.err(P + ("authority", "acceptance_ref"), "E_AUTHORITY",
                    "acceptance_ref must resolve to an active decision-record artifact")
    status = (somnus.get("lifecycle") or {}).get("status") if isinstance(somnus.get("lifecycle"), dict) else None
    if status not in ("active", "provisional"):
        run.err(P + ("lifecycle", "status"), "E_AUTHORITY", f"status {status!r} is not eligible for current canon")
    for kind in resolver.open_conflicts.get(somnus.get("id"), []):
        code = {"revision": "E_REVISION", "authority": "E_AUTHORITY"}.get(kind, "E_REFERENCE")
        run.err(P + ("id",), code, f"open {kind} conflict blocks canon selection")


# --------------------------------------------------------------------------- entry points


def validate(doc: Document, level: str = "core", resolver: Optional[Resolver] = None) -> list[Diagnostic]:
    """Run the pipeline up to ``level``; later stages run only when earlier ones pass."""
    if level not in LEVEL_RANK:
        raise ValueError(f"unknown level {level!r}")
    run = _Run(doc)
    run.out.extend(doc.issues)
    if doc.envelope is None and not any(d.code == "E_ENVELOPE" for d in doc.issues):
        run.at(1, 1, "E_ENVELOPE", "no metadata envelope found")
    if any(d.code in ("E_ENVELOPE", "E_IO") for d in run.out) or doc.envelope is None:
        return run.out
    if doc.data is None:
        return run.out
    if doc.is_sidecar and isinstance(doc.payload, dict):
        for path, message in binding_issues(doc.payload, doc.meta_path):
            run.err(path, "E_ENVELOPE", message)
    if LEVEL_RANK[level] < LEVEL_RANK["core"]:
        return run.out
    if any(d.is_error for d in run.out):
        return run.out
    walk(run, S.ROOT, doc.data, ())
    somnus = doc.payload
    if somnus is None:
        return run.out
    consistency(run, somnus)
    marker_regions(run, somnus)
    if LEVEL_RANK[level] < LEVEL_RANK["semantic"] or any(d.is_error for d in run.out):
        return run.out
    resolver = resolver or Resolver()
    references(run, somnus, resolver)
    selectors(run, somnus)
    semantic_policies(run, somnus)
    if LEVEL_RANK[level] < LEVEL_RANK["canon"] or any(d.is_error for d in run.out):
        return run.out
    canon(run, somnus, resolver)
    return run.out


def validate_payload(somnus: dict, path: str = "<payload>") -> list[Diagnostic]:
    """Core structural + consistency checks for an in-memory payload (no body)."""
    from somnus.document import canonical_yaml, from_text

    text = canonical_yaml({"somnus": somnus})
    doc = from_text(Path(path), text)
    doc.carrier = SIDECAR
    doc.envelope = SIDECAR.extract(doc.lines).envelope
    run = _Run(doc)
    run.out.extend(doc.issues)
    if doc.data is None:
        return run.out
    walk(run, S.ROOT, doc.data, ())
    if isinstance(doc.payload, dict):
        consistency(run, doc.payload)
    return run.out


def permits_use(somnus: dict, use: str, region_id: Optional[str] = None) -> bool:
    """Header-level usage decision (external policy may be stricter)."""
    access = somnus.get("access") if isinstance(somnus.get("access"), dict) else {}
    allowed = set(access.get("allowed_uses", []) or [])
    disposition = (somnus.get("ingestion") or {}).get("disposition") if isinstance(somnus.get("ingestion"), dict) else None
    if disposition == "excluded":
        allowed &= {"archive"}
    elif disposition == "archive-only":
        allowed &= {"archive", "search"}
    if region_id is not None:
        knowledge = somnus.get("knowledge") if isinstance(somnus.get("knowledge"), dict) else {}
        for reg in _dicts(knowledge.get("regions")):
            if reg.get("id") == region_id and isinstance(reg.get("access"), dict) and "allowed_uses" in reg["access"]:
                allowed &= set(reg["access"]["allowed_uses"])
        excluded = (somnus.get("ingestion") or {}).get("exclude_regions", []) if isinstance(somnus.get("ingestion"), dict) else []
        if region_id in excluded:
            allowed &= {"archive"}
    return use in allowed
