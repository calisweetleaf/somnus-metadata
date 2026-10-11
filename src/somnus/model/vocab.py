"""Controlled vocabularies of core schema 2.0.0 (SPEC §5, §7–§15)."""

from __future__ import annotations

CATEGORIES = ("research", "engineering", "operations", "governance", "context", "archive")
TYPES = (
    "whitepaper", "specification", "architecture-record", "report", "task", "plan", "notepad",
    "benchmark", "test-result", "decision-record", "runbook", "index", "state", "memory",
    "source-code", "configuration", "dataset", "equation-set", "conversation", "asset",
)
ROLES = ("normative", "informative", "working", "exploratory", "historical")
SCOPES = ("ecosystem", "fleet", "repository", "subsystem", "module", "component", "artifact")
STATUSES = (
    "draft", "proposed", "provisional", "active", "experimental", "superseded", "deprecated",
    "historical", "archived", "rejected",
)
STANDINGS = ("unasserted", "candidate", "accepted", "retired", "rejected")
VISIBILITIES = ("operator-only", "internal", "public")
ALLOWED_USES = ("archive", "search", "reason", "quote", "export", "training", "execute")
DISPOSITIONS = ("candidate", "archive-only", "excluded", "canonical-candidate")
BODY_ROLES = ("narrative", "specification", "instruction", "configuration", "source", "conversation",
              "dataset", "mixed")
REGION_KINDS = ("section", "definition", "invariant", "decision", "hypothesis", "evidence", "equation",
                "table", "code", "example", "archive")

ASPECTS = ("content", "semantic-model", "terminology", "interface", "behavior", "configuration",
           "performance", "embedding", "ingestion", "migration", "governance", "process", "security")
CONSTRAINT_LANGUAGES = ("semver-range@1", "pep440-specifier@1", "path-glob@1", "platform-tag@1")
CAPABILITIES = (
    "somnus-adapter-markdown@1", "somnus-adapter-html-comment@1", "somnus-adapter-hash-comment@1",
    "somnus-adapter-tex@1", "somnus-adapter-slash-comment@1", "somnus-adapter-sql-comment@1",
    "somnus-adapter-block-comment@1", "somnus-adapter-sidecar@1",
)

VALID_TIME_BASES = ("bounded", "open", "timeless", "unknown")
COVERAGES = ("artifact", "selected-claims", "structured-claims")
ENTITY_KINDS = ("project", "system", "component", "agent", "agent-role", "framework", "concept",
                "organization", "dataset", "model", "tool")
ENTITY_ALIAS_KINDS = ("former-name", "short-name", "acronym", "spelling", "translation")
ARTIFACT_ALIAS_KINDS = ("former-title", "short-name", "acronym", "spelling", "translation")
CLAIM_PREDICATES = ("definition", "has_role", "has_property", "requires", "predicts", "measures")
CLAIM_KINDS = ("observation", "definition", "requirement", "hypothesis", "inference", "prediction",
               "measurement")
ASSESSMENTS = ("unassessed", "supported", "contested", "refuted", "withdrawn")
SELECTOR_KINDS = ("marker", "tex-label", "symbol", "json-pointer", "heading", "line-range")
MATH_FORMATS = ("tex", "mathml", "unicode", "raster", "mixed")
RESOURCE_ROLES = ("macro-source", "figure", "table-source", "attachment", "rendered-output")
EXTRACTION_STATES = ("complete", "partial", "unverified")
RIGHTS_STATUSES = ("specified", "unspecified", "restricted")
LOCATION_KINDS = ("repository-path", "filesystem-path", "library-item", "uri")
LOCATION_ROLES = ("origin", "primary", "mirror", "historical")
REPRESENTATION_ROLES = ("source", "rendered", "translation", "projection")
BINDING_ROLES = ("primary", "attachment", "representation")
COMPLIANCE_LEVELS = ("mandatory", "recommended", "optional")

# predicate -> (inverse view name, acyclic)
RELATION_PREDICATES: dict[str, tuple[str, bool]] = {
    "supersedes": ("superseded_by", True),
    "derived_from": ("has_derivative", True),
    "describes": ("described_by", False),
    "implements": ("implemented_by", False),
    "depends_on": ("required_by", False),
    "part_of": ("has_part", True),
    "cites": ("cited_by", False),
    "supports": ("supported_by", False),
    "contradicts": ("contradicts", False),
    "renamed_to": ("renamed_from", False),
    "role_expanded_to": ("role_expanded_from", False),
    "specializes": ("generalizes", False),
    "equivalent_to": ("equivalent_to", False),
    "distinct_from": ("distinct_from", False),
}

VISIBILITY_RANK = {"operator-only": 0, "internal": 1, "public": 2}
LEVELS = ("carrier", "core", "semantic", "canon")
