"""Declarative schema tree for core 2.0.0 and its profiles (SPEC §4–§17).

Nodes describe types, required members, vocabularies, and formats. The
structural walker lives in ``somnus.model.validate``; the canonical key order
used by the serializer is derived from the ``Obj`` field declarations here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence, Union

from somnus import BENCHMARK_PROFILE, CORE_SCHEMA, SPEC_PROFILE
from somnus.model import vocab

TIMESTAMP_PATTERN = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
DATE_PATTERN = r"\d{4}-\d{2}-\d{2}"
LOCAL_PATTERN = r"[a-z][a-z0-9_]*(?:-[a-z0-9_]+)*"
KEBAB_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
ID_PATTERN = (
    r"urn:somnus:artifact:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    r"|urn:somnus:example:[a-z0-9][a-z0-9-]*"
)
SOMNUS_URN_PATTERN = r"urn:somnus:(?:artifact|entity|actor|concept|example):[A-Za-z0-9][A-Za-z0-9._:-]*"
REF_PATTERN = SOMNUS_URN_PATTERN + r"|doi:10\.\S+|https?://\S+|urn:(?!somnus:)[a-z0-9][a-z0-9-]*:\S+"
LANGUAGE_PATTERN = r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*"
MEDIA_TYPE_PATTERN = r"[a-z]+/[A-Za-z0-9.+-]+"
OWNER_PATTERN = r"[a-z][a-z0-9]*(?:[-.][a-z0-9]+)*"
PROFILE_KEY_PATTERN = r"[a-z][a-z0-9_]*"


@dataclass(frozen=True)
class Str:
    """String node; optional vocabulary, full-match pattern, or format."""

    enum: Optional[Sequence[str]] = None
    pattern: Optional[str] = None
    fmt: Optional[str] = None  # "timestamp" | "date"
    min_len: int = 1
    doc: str = ""


@dataclass(frozen=True)
class Int:
    """Integer node (booleans are not integers)."""

    minimum: Optional[int] = None
    doc: str = ""


@dataclass(frozen=True)
class Num:
    """Finite number node (integer or decimal)."""

    minimum: Optional[float] = None
    maximum: Optional[float] = None
    doc: str = ""


@dataclass(frozen=True)
class Bool:
    """Boolean node."""

    doc: str = ""


@dataclass(frozen=True)
class AnyValue:
    """Open JSON-compatible value (extension data, claim values)."""

    doc: str = ""


@dataclass(frozen=True)
class Arr:
    """Array node with an item schema."""

    item: "Node"
    min_items: int = 0
    unique: bool = False
    doc: str = ""


@dataclass(frozen=True)
class Field:
    """One declared member of an object."""

    name: str
    node: "Node"
    required: bool = False
    doc: str = ""


@dataclass(frozen=True)
class Obj:
    """Closed object node; members are emitted in declaration order."""

    name: str
    fields: tuple[Field, ...]
    doc: str = ""

    def get(self, key: str) -> Optional[Field]:
        """Return the declared field named ``key``."""
        for f in self.fields:
            if f.name == key:
                return f
        return None

    @property
    def order(self) -> list[str]:
        """Canonical member order."""
        return [f.name for f in self.fields]


@dataclass(frozen=True)
class MapOf:
    """Open-keyed mapping whose keys match a pattern and values share a schema."""

    key_pattern: str
    value: "Node"
    doc: str = ""


@dataclass(frozen=True)
class Tagged:
    """Object discriminated by a string member (selector ``kind``)."""

    name: str
    tag: str
    variants: dict = field(default_factory=dict)
    doc: str = ""

    @property
    def order(self) -> list[str]:
        """Canonical order: tag first, then members in first-seen variant order."""
        seen = [self.tag]
        for obj in self.variants.values():
            for f in obj.fields:
                if f.name not in seen:
                    seen.append(f.name)
        return seen


@dataclass(frozen=True)
class Union_:
    """Either a string or an object (sidecar binding targets)."""

    options: tuple
    doc: str = ""


Node = Union[Str, Int, Num, Bool, AnyValue, Arr, Obj, MapOf, Tagged, Union_]


def F(name: str, node: Node, required: bool = False, doc: str = "") -> Field:
    """Shorthand constructor for ``Field``."""
    return Field(name, node, required, doc)


def enum(values: Sequence[str], doc: str = "") -> Str:
    """Shorthand for a vocabulary-constrained string."""
    return Str(enum=tuple(values), doc=doc)


TEXT = Str()
LOCAL = Str(pattern=LOCAL_PATTERN, doc="Local ID")
REF_STR = Str(pattern=REF_PATTERN, doc="Somnus URN or external reference")
TIMESTAMP = Str(fmt="timestamp", doc="RFC 3339 timestamp with explicit offset")
DATE = Str(fmt="date", doc="Calendar date YYYY-MM-DD")
POS_INT = Int(minimum=1)

REF = Obj("reference", (
    F("ref", REF_STR, True, "Referenced identity"),
    F("revision", POS_INT, doc="Pinned revision"),
    F("region", LOCAL, doc="Local region ID in the target"),
    F("claim", LOCAL, doc="Local claim ID in the target"),
    F("locator_hint", TEXT, doc="Path or locator hint; never identity"),
), "Reference object (SPEC §3.3)")

VALID_TIME = Obj("valid_time", (
    F("basis", enum(vocab.VALID_TIME_BASES), True),
    F("from", TIMESTAMP),
    F("until", TIMESTAMP),
    F("note", TEXT),
), "Applicability interval (SPEC §9)")

CONSTRAINT = Obj("constraint", (
    F("target_ref", TEXT, True),
    F("language", TEXT, True, "Registered constraint language"),
    F("expression", TEXT, True),
), "Constraint object (SPEC §5.3)")

SCOPE = Obj("scope", (
    F("target_ref", REF_STR, True),
    F("aspects", Arr(enum(vocab.ASPECTS), min_items=1, unique=True), True),
    F("conditions", Arr(CONSTRAINT)),
), "Authority scope (SPEC §8)")

CLASSIFICATION = Obj("classification", (
    F("category", enum(vocab.CATEGORIES), True),
    F("type", enum(vocab.TYPES), True),
    F("subtype", Str(pattern=KEBAB_PATTERN)),
    F("role", enum(vocab.ROLES), True),
    F("scope", enum(vocab.SCOPES), True),
    F("tags", Arr(TEXT, unique=True), True),
), "Classification (SPEC §5)")

LIFECYCLE = Obj("lifecycle", (
    F("status", enum(vocab.STATUSES), True),
    F("reason", TEXT),
    F("replacement_refs", Arr(REF)),
), "Lifecycle (SPEC §7)")

AUTHORITY = Obj("authority", (
    F("standing", enum(vocab.STANDINGS), True),
    F("scopes", Arr(SCOPE), True),
    F("valid_time", VALID_TIME),
    F("acceptance_ref", REF),
    F("owner_ref", REF),
), "Scoped authority (SPEC §8)")

TIME = Obj("time", (
    F("created_at", TIMESTAMP),
    F("updated_at", TIMESTAMP),
    F("reviewed_at", TIMESTAMP),
    F("authored_on", DATE),
    F("note", TEXT),
), "Authorship clock (SPEC §9)")

ARTIFACT_ALIAS = Obj("artifact_alias", (
    F("id", LOCAL, True),
    F("label", TEXT, True),
    F("kind", enum(vocab.ARTIFACT_ALIAS_KINDS), True),
    F("valid_time", VALID_TIME, True),
))

NAMES = Obj("names", (
    F("slug", Str(pattern=KEBAB_PATTERN)),
    F("aliases", Arr(ARTIFACT_ALIAS)),
), "Artifact names (SPEC §10.1)")

CONTEXT = Obj("context", (
    F("project_refs", Arr(REF)),
    F("system_refs", Arr(REF)),
    F("division_refs", Arr(REF)),
    F("repository_refs", Arr(REF)),
    F("release_constraints", Arr(CONSTRAINT)),
    F("platform_constraints", Arr(CONSTRAINT)),
), "Subject context (SPEC §5.3)")

RIGHTS = Obj("rights", (
    F("status", enum(vocab.RIGHTS_STATUSES), True),
    F("license_expression", TEXT),
))

OWNERSHIP = Obj("ownership", (
    F("owner_ref", REF),
    F("maintainer_refs", Arr(REF)),
    F("rights", RIGHTS),
), "Ownership (SPEC §15.2)")

LOCATION = Obj("location", (
    F("kind", enum(vocab.LOCATION_KINDS), True),
    F("locator", TEXT, True),
    F("role", enum(vocab.LOCATION_ROLES), True),
    F("repository_ref", REF),
    F("observed_on", DATE),
))

REPRESENTATION = Obj("representation", (
    F("locator", TEXT, True),
    F("media_type", Str(pattern=MEDIA_TYPE_PATTERN), True),
    F("role", enum(vocab.REPRESENTATION_ROLES), True),
    F("source_revision", POS_INT),
    F("limitations", Arr(TEXT)),
))

MATH = Obj("math", (
    F("source_format", enum(vocab.MATH_FORMATS), True),
    F("delimiters", Arr(TEXT), True),
    F("macro_refs", Arr(TEXT), True),
    F("equation_region_ids", Arr(LOCAL, unique=True), True),
))

RESOURCE = Obj("resource", (
    F("ref", TEXT, True),
    F("media_type", Str(pattern=MEDIA_TYPE_PATTERN), True),
    F("role", enum(vocab.RESOURCE_ROLES), True),
    F("required", Bool(), True),
))

EXTRACTION = Obj("extraction", (
    F("state", enum(vocab.EXTRACTION_STATES), True),
    F("limitations", Arr(TEXT), True),
))

CONTENT = Obj("content", (
    F("math", MATH),
    F("resources", Arr(RESOURCE)),
    F("extraction", EXTRACTION),
), "Content and mathematics (SPEC §14)")

ENTITY_ALIAS = Obj("entity_alias", (
    F("id", LOCAL, True),
    F("label", TEXT, True),
    F("kind", enum(vocab.ENTITY_ALIAS_KINDS), True),
    F("valid_time", VALID_TIME, True),
))

ENTITY = Obj("entity", (
    F("ref", Str(pattern=SOMNUS_URN_PATTERN), True),
    F("label", TEXT, True),
    F("kind", enum(vocab.ENTITY_KINDS), True),
    F("description", TEXT),
    F("aliases", Arr(ENTITY_ALIAS)),
    F("external_refs", Arr(TEXT)),
), "Entity declaration (SPEC §10.2)")

TERM = Obj("term", (
    F("id", LOCAL, True),
    F("label", TEXT, True),
    F("definition", TEXT, True),
    F("entity_refs", Arr(REF_STR), True),
    F("valid_time", VALID_TIME, True),
    F("excluded_refs", Arr(REF_STR)),
    F("context_refs", Arr(REF)),
    F("region_ref", LOCAL),
), "Term (SPEC §10.3)")

SELECTOR = Tagged("selector", "kind", {
    "marker": Obj("marker", (F("kind", TEXT, True), F("name", LOCAL, True))),
    "tex-label": Obj("tex-label", (F("kind", TEXT, True), F("name", TEXT, True))),
    "symbol": Obj("symbol", (F("kind", TEXT, True), F("name", TEXT, True), F("language", TEXT, True))),
    "json-pointer": Obj("json-pointer", (F("kind", TEXT, True), F("pointer", Str(min_len=0), True))),
    "heading": Obj("heading", (F("kind", TEXT, True), F("text", TEXT, True), F("occurrence", POS_INT, True))),
    "line-range": Obj("line-range", (
        F("kind", TEXT, True), F("from", POS_INT, True), F("until", POS_INT, True), F("revision", POS_INT, True),
    )),
}, "Region selector (SPEC §13.2)")

REGION = Obj("region", (
    F("id", LOCAL, True),
    F("kind", enum(vocab.REGION_KINDS), True),
    F("selector", SELECTOR, True),
    F("title", TEXT),
    F("claim_ids", Arr(LOCAL, unique=True)),
    F("authority", Obj("region_authority", (F("standing", enum(vocab.STANDINGS), True),))),
    F("access", Obj("region_access", (
        F("visibility", enum(vocab.VISIBILITIES)),
        F("allowed_uses", Arr(enum(vocab.ALLOWED_USES), unique=True)),
    ))),
    F("valid_time", VALID_TIME),
    F("context_refs", Arr(REF)),
), "Region record (SPEC §13.1)")

CLAIM_OBJECT = Obj("claim_object", (
    F("ref", REF_STR),
    F("revision", POS_INT),
    F("region", LOCAL),
    F("claim", LOCAL),
    F("locator_hint", TEXT),
    F("value", AnyValue()),
), "Exactly one of ref or value")

CONFIDENCE = Obj("confidence", (
    F("value", Num(minimum=0.0, maximum=1.0), True),
    F("method", TEXT, True),
))

CLAIM = Obj("claim", (
    F("id", LOCAL, True),
    F("subject_ref", REF_STR, True),
    F("predicate", enum(vocab.CLAIM_PREDICATES), True),
    F("object", CLAIM_OBJECT, True),
    F("statement", TEXT, True),
    F("kind", enum(vocab.CLAIM_KINDS), True),
    F("assessment", enum(vocab.ASSESSMENTS), True),
    F("valid_time", VALID_TIME, True),
    F("region_ref", LOCAL, True),
    F("evidence_refs", Arr(REF)),
    F("assumption_refs", Arr(REF)),
    F("context_refs", Arr(REF)),
    F("conditions", Arr(CONSTRAINT)),
    F("confidence", CONFIDENCE),
), "Claim record (SPEC §11)")

RELATION = Obj("relation", (
    F("id", LOCAL, True),
    F("subject", REF, True),
    F("predicate", Str(pattern=r"[a-z][a-z0-9_]*"), True),
    F("object", REF, True),
    F("assessment", enum(vocab.ASSESSMENTS), True),
    F("valid_time", VALID_TIME, True),
    F("region_ref", LOCAL),
    F("evidence_refs", Arr(REF)),
    F("conditions", Arr(CONSTRAINT)),
    F("note", TEXT),
), "Qualified relation (SPEC §12)")

KNOWLEDGE = Obj("knowledge", (
    F("coverage", enum(vocab.COVERAGES), True),
    F("subjects", Arr(REF_STR, unique=True), True),
    F("entities", Arr(ENTITY)),
    F("terms", Arr(TERM)),
    F("regions", Arr(REGION)),
    F("claims", Arr(CLAIM)),
    F("relations", Arr(RELATION)),
), "Knowledge module (SPEC §10–§13)")

ACCESS = Obj("access", (
    F("visibility", enum(vocab.VISIBILITIES), True),
    F("allowed_uses", Arr(enum(vocab.ALLOWED_USES), unique=True), True),
), "Usage declaration (SPEC §15.1)")

INGESTION = Obj("ingestion", (
    F("disposition", enum(vocab.DISPOSITIONS), True),
    F("body_role", enum(vocab.BODY_ROLES), True),
    F("include_regions", Arr(LOCAL, unique=True)),
    F("exclude_regions", Arr(LOCAL, unique=True)),
    F("atomic_regions", Arr(LOCAL, unique=True)),
    F("requires", Arr(TEXT, unique=True)),
), "Ingestion intent (SPEC §15.4)")

PROFILE_DECL = Obj("profile", (
    F("schema", TEXT, True),
    F("key", Str(pattern=PROFILE_KEY_PATTERN), True),
))

BINDING = Obj("binding", (
    F("target", Union_((TEXT, REF)), True),
    F("role", enum(vocab.BINDING_ROLES), True),
    F("required", Bool(), True),
), "Sidecar binding (SPEC §17.6)")

EXTENSION = Obj("extension", (
    F("schema", TEXT, True),
    F("data", AnyValue(), True),
), "Owner-namespaced extension (SPEC §4.3)")

SOMNUS = Obj("somnus", (
    F("schema", Str(enum=(CORE_SCHEMA,)), True, "Exact core schema release"),
    F("id", Str(pattern=ID_PATTERN), True, "Artifact URN"),
    F("revision", POS_INT, True, "Authored revision"),
    F("title", TEXT, True),
    F("summary", TEXT),
    F("purpose", TEXT),
    F("language", Str(pattern=LANGUAGE_PATTERN)),
    F("edition", TEXT),
    F("classification", CLASSIFICATION, True),
    F("lifecycle", LIFECYCLE, True),
    F("authority", AUTHORITY, True),
    F("time", TIME, True),
    F("names", NAMES),
    F("context", CONTEXT),
    F("ownership", OWNERSHIP),
    F("locations", Arr(LOCATION)),
    F("representations", Arr(REPRESENTATION)),
    F("content", CONTENT),
    F("knowledge", KNOWLEDGE, True),
    F("access", ACCESS, True),
    F("ingestion", INGESTION, True),
    F("profiles", Arr(PROFILE_DECL)),
    F("profile_data", MapOf(PROFILE_KEY_PATTERN, AnyValue())),
    F("bindings", Arr(BINDING)),
    F("extensions", MapOf(OWNER_PATTERN, EXTENSION)),
), "Somnus core payload (SPEC §4.1)")

ROOT = Obj("root", (F("somnus", SOMNUS, True),), "Envelope payload root")

SPECIFICATION_PROFILE = Obj("specification", (
    F("target_refs", Arr(REF, min_items=1), True),
    F("acceptance_criteria", Arr(TEXT, min_items=1), True),
    F("normative_region_refs", Arr(LOCAL, unique=True)),
    F("compliance_level", enum(vocab.COMPLIANCE_LEVELS)),
    F("verification_refs", Arr(REF)),
), "Specification profile 1.0.0 (SPEC §6.1)")

BENCHMARK_PROFILE_NODE = Obj("benchmark", (
    F("workload", TEXT, True),
    F("environment", Obj("environment", (
        F("cpu", TEXT, True),
        F("memory_gb", Num(minimum=0.0), True),
        F("os", TEXT, True),
        F("accelerator", TEXT),
        F("runtime", TEXT),
    )), True),
    F("measurements", Arr(Obj("measurement", (
        F("name", TEXT, True),
        F("value", Num(), True),
        F("unit", TEXT, True),
        F("repetitions", POS_INT),
        F("uncertainty", Num(minimum=0.0)),
    )), min_items=1), True),
    F("baseline_ref", REF),
    F("conditions", Arr(TEXT)),
), "Benchmark profile 1.0.0 (SPEC §6.2)")

PROFILES: dict[str, Obj] = {
    SPEC_PROFILE: SPECIFICATION_PROFILE,
    BENCHMARK_PROFILE: BENCHMARK_PROFILE_NODE,
}


def _child(node: Any, key: Any, payload_profiles: dict[str, str]) -> Any:
    if isinstance(node, Obj):
        f = node.get(key)
        return f.node if f else None
    if isinstance(node, Tagged):
        for variant in node.variants.values():
            f = variant.get(key)
            if f:
                return f.node
        return None
    if isinstance(node, Arr):
        return node.item if key == "[]" else None
    if isinstance(node, MapOf):
        return node.value
    if isinstance(node, Union_):
        for option in node.options:
            if isinstance(option, Obj):
                return _child(option, key, payload_profiles)
    return None


def node_at(path: Sequence[Any], payload_profiles: Optional[dict[str, str]] = None) -> Any:
    """Return the schema node for a key path (sequence items as ``"[]"``)."""
    profiles = payload_profiles or {}
    node: Any = ROOT
    for i, key in enumerate(path):
        if (
            i == 2 and len(path) > 2 and path[0] == "somnus" and path[1] == "profile_data"
            and key in profiles and profiles[key] in PROFILES
        ):
            node = PROFILES[profiles[key]]
            continue
        node = _child(node, key, profiles)
        if node is None:
            return None
    return node


def make_order(payload: Optional[dict] = None):
    """Build the serializer ``order`` callback, aware of declared profiles."""
    profiles: dict[str, str] = {}
    if isinstance(payload, dict):
        somnus = payload.get("somnus", payload)
        for decl in somnus.get("profiles", []) if isinstance(somnus, dict) else []:
            if isinstance(decl, dict) and isinstance(decl.get("key"), str) and isinstance(decl.get("schema"), str):
                profiles[decl["key"]] = decl["schema"]

    def order(path: tuple) -> Optional[list[str]]:
        node = node_at(path, profiles)
        if isinstance(node, Union_):
            node = next((o for o in node.options if isinstance(o, Obj)), None)
        if isinstance(node, (Obj, Tagged)):
            return node.order
        return None

    return order


def describe(node: Any) -> str:
    """Return a short human type description of a node."""
    if isinstance(node, Str):
        if node.enum:
            return "one of: " + ", ".join(node.enum)
        if node.fmt:
            return node.doc or node.fmt
        if node.pattern:
            return f"string matching {node.pattern}"
        return "string"
    if isinstance(node, Int):
        return "integer" + (f" >= {node.minimum}" if node.minimum is not None else "")
    if isinstance(node, Num):
        bounds = []
        if node.minimum is not None:
            bounds.append(f">= {node.minimum}")
        if node.maximum is not None:
            bounds.append(f"<= {node.maximum}")
        return "number" + (" " + " and ".join(bounds) if bounds else "")
    if isinstance(node, Bool):
        return "boolean"
    if isinstance(node, AnyValue):
        return "any JSON-compatible value"
    if isinstance(node, Arr):
        extra = []
        if node.min_items:
            extra.append(f"min {node.min_items}")
        if node.unique:
            extra.append("unique")
        suffix = f" ({', '.join(extra)})" if extra else ""
        return f"array of {describe(node.item)}{suffix}"
    if isinstance(node, Obj):
        return f"object <{node.name}>"
    if isinstance(node, Tagged):
        return f"object <{node.name}> discriminated by {node.tag}: " + ", ".join(node.variants)
    if isinstance(node, MapOf):
        return f"mapping of keys matching {node.key_pattern} to {describe(node.value)}"
    if isinstance(node, Union_):
        return " or ".join(describe(o) for o in node.options)
    return "unknown"
