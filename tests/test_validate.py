"""Validation pipeline: levels, diagnostic codes, field paths, usage policy (SPEC section 19)."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from somnus import CORE_SCHEMA, SPEC_PROFILE
from somnus import document as D
from somnus.model.validate import Resolver, permits_use, validate, validate_payload

A = "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08a"
B = "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08b"
C = "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f08c"
DR = "urn:somnus:artifact:01a12a94-8657-715c-9044-852de0e3f0dd"
V4 = "urn:somnus:artifact:2f1c3b9e-6d4a-4c1b-9e3f-0a1b2c3d4e5f"

BASE = {
    "schema": CORE_SCHEMA,
    "id": A,
    "revision": 1,
    "title": "Doc",
    "classification": {"category": "engineering", "type": "specification", "role": "normative",
                       "scope": "component", "tags": []},
    "lifecycle": {"status": "draft"},
    "authority": {"standing": "candidate", "scopes": [{"target_ref": A, "aspects": ["content"]}]},
    "time": {},
    "knowledge": {"coverage": "artifact", "subjects": [A]},
    "access": {"visibility": "internal", "allowed_uses": ["archive", "search", "reason"]},
    "ingestion": {"disposition": "candidate", "body_role": "specification"},
}
BODY = "\n# Body\n\nText.\n"
REGION = {"id": "r-body", "kind": "section", "selector": {"kind": "heading", "text": "Body", "occurrence": 1}}
CLAIM = {
    "id": "c-one", "subject_ref": A, "predicate": "has_property", "object": {"value": 1},
    "statement": "S", "kind": "observation", "assessment": "unassessed",
    "valid_time": {"basis": "unknown"}, "region_ref": "r-body",
}
OPEN_VT = {"basis": "open", "from": "2026-01-01T00:00:00Z"}


def base() -> dict:
    return copy.deepcopy(BASE)


def relation(pred: str, subj: str, obj: str, rid: str = "rel-one") -> dict:
    return {"id": rid, "subject": {"ref": subj}, "predicate": pred, "object": {"ref": obj},
            "assessment": "unassessed", "valid_time": {"basis": "unknown"}}


def make(payload: dict, body: str = BODY, path: str = "x.md") -> D.Document:
    return D.from_text(Path(path), "---\n" + D.canonical_yaml({"somnus": payload}) + "---\n" + body)


def check(payload: dict, level: str = "core", resolver: Resolver | None = None, body: str = BODY) -> list:
    return validate(make(payload, body), level, resolver)


def errs(diags: list) -> set:
    return {(d.code, d.field) for d in diags if d.is_error}


def warns(diags: list) -> set:
    return {(d.code, d.field) for d in diags if not d.is_error}


def accepted() -> dict:
    p = base()
    p["lifecycle"]["status"] = "active"
    p["authority"].update({"standing": "accepted", "valid_time": dict(OPEN_VT), "acceptance_ref": {"ref": DR}})
    return p


def decision_record(status: str = "active", type_: str = "decision-record") -> dict:
    p = base()
    p["id"] = DR
    p["classification"]["type"] = type_
    p["lifecycle"]["status"] = status
    return p


class TestBaseline(unittest.TestCase):
    def test_minimal_payload_valid_at_every_level_below_canon(self) -> None:
        for level in ("carrier", "core", "semantic"):
            with self.subTest(level=level):
                self.assertEqual(check(base(), level), [])

    def test_validate_payload_accepts_base(self) -> None:
        self.assertEqual([d for d in validate_payload(base()) if d.is_error], [])

    def test_unknown_level(self) -> None:
        with self.assertRaises(ValueError):
            check(base(), "strict")

    def test_imported_uuid4_without_creation_date(self) -> None:
        # SPEC section 21 fixture 9.
        p = base()
        p["id"] = V4
        p["authority"]["scopes"][0]["target_ref"] = V4
        p["knowledge"]["subjects"] = [V4]
        self.assertEqual(errs(check(p, "semantic")), set())

    def test_uuid7_mint_time_not_compared_with_created_at(self) -> None:
        # SPEC section 21 fixture 10: the ID's timestamp is 2026 but the authored date is far earlier.
        p = base()
        p["time"] = {"created_at": "1999-01-01T00:00:00Z", "authored_on": "1999-01-01"}
        self.assertEqual(errs(check(p)), set())


class TestSchema(unittest.TestCase):
    def test_unknown_fields(self) -> None:
        for path, mutate in [
            ("somnus.extra", lambda p: p.__setitem__("extra", 1)),
            ("somnus.classification.colour", lambda p: p["classification"].__setitem__("colour", "red")),
            ("somnus.authority.scopes[0].why", lambda p: p["authority"]["scopes"][0].__setitem__("why", "x")),
            ("somnus.time.created", lambda p: p["time"].__setitem__("created", "x")),
        ]:
            with self.subTest(path=path):
                p = base()
                mutate(p)
                self.assertIn(("E_SCHEMA", path), errs(check(p)))

    def test_unknown_field_line_points_at_key(self) -> None:
        p = base()
        p["extra"] = 1
        doc = make(p)
        line = next(i for i, ln in enumerate(doc.lines, 1) if ln.startswith("  extra:"))
        diag = next(d for d in validate(doc) if d.field == "somnus.extra")
        self.assertEqual((diag.line, diag.col), (line, 3))

    def test_wrong_types(self) -> None:
        for path, mutate in [
            ("somnus.revision", lambda p: p.__setitem__("revision", "1")),
            ("somnus.revision", lambda p: p.__setitem__("revision", True)),
            ("somnus.title", lambda p: p.__setitem__("title", 5)),
            ("somnus.classification.tags", lambda p: p["classification"].__setitem__("tags", "x")),
            ("somnus.time", lambda p: p.__setitem__("time", [])),
            ("somnus.access.allowed_uses[0]", lambda p: p["access"].__setitem__("allowed_uses", [1])),
        ]:
            with self.subTest(path=path):
                p = base()
                mutate(p)
                self.assertIn(("E_SCHEMA", path), errs(check(p)))

    def test_vocabulary_values(self) -> None:
        for path, mutate in [
            ("somnus.classification.type", lambda p: p["classification"].__setitem__("type", "novel")),
            ("somnus.classification.category", lambda p: p["classification"].__setitem__("category", "x")),
            ("somnus.lifecycle.status", lambda p: p["lifecycle"].__setitem__("status", "live")),
            ("somnus.authority.standing", lambda p: p["authority"].__setitem__("standing", "canon")),
            ("somnus.authority.scopes[0].aspects[0]", lambda p: p["authority"]["scopes"][0].__setitem__("aspects", ["style"])),
            ("somnus.access.visibility", lambda p: p["access"].__setitem__("visibility", "secret")),
            ("somnus.ingestion.disposition", lambda p: p["ingestion"].__setitem__("disposition", "canon")),
        ]:
            with self.subTest(path=path):
                p = base()
                mutate(p)
                self.assertIn(("E_SCHEMA", path), errs(check(p)))

    def test_missing_required_fields(self) -> None:
        for key in ("schema", "id", "revision", "title", "classification", "lifecycle", "authority", "time",
                    "knowledge", "access", "ingestion"):
            with self.subTest(key=key):
                p = base()
                del p[key]
                diags = [d for d in check(p) if d.code == "E_SCHEMA" and d.field == "somnus"]
                self.assertTrue(any(key in d.message for d in diags))

    def test_missing_nested_required(self) -> None:
        p = base()
        del p["classification"]["tags"]
        self.assertIn(("E_SCHEMA", "somnus.classification"), errs(check(p)))

    def test_wrong_core_release(self) -> None:
        for release in ("somnus://metadata/core/1.0.0", "somnus://metadata/core/2.1.0", "somnus://metadata/core/2.0"):
            with self.subTest(release=release):
                p = base()
                p["schema"] = release
                self.assertIn(("E_SCHEMA", "somnus.schema"), errs(check(p)))

    def test_identity_and_formats(self) -> None:
        for path, mutate in [
            ("somnus.id", lambda p: p.__setitem__("id", A.upper())),
            ("somnus.id", lambda p: p.__setitem__("id", "urn:somnus:doc:x")),
            ("somnus.revision", lambda p: p.__setitem__("revision", 0)),
            ("somnus.title", lambda p: p.__setitem__("title", "   ")),
            ("somnus.language", lambda p: p.__setitem__("language", "english!")),
            ("somnus.classification.subtype", lambda p: p["classification"].__setitem__("subtype", "Not Kebab")),
            ("somnus.classification.tags[1]", lambda p: p["classification"].__setitem__("tags", ["a", "a"])),
        ]:
            with self.subTest(path=path):
                p = base()
                mutate(p)
                self.assertIn(("E_SCHEMA", path), errs(check(p)))

    def test_example_urn_and_language_accepted(self) -> None:
        p = base()
        p["id"] = "urn:somnus:example:fixture"
        p["authority"]["scopes"][0]["target_ref"] = p["id"]
        p["knowledge"]["subjects"] = [p["id"]]
        p["language"] = "en-US"
        self.assertEqual(errs(check(p)), set())

    def test_null_is_a_yaml_error(self) -> None:
        text = "---\n" + D.canonical_yaml({"somnus": base()}).replace('  title: "Doc"', "  title: null") + "---\n"
        diags = validate(D.from_text(Path("x.md"), text))
        self.assertEqual([d.code for d in diags], ["E_YAML"])

    def test_rights_license_rules(self) -> None:
        p = base()
        p["ownership"] = {"rights": {"status": "specified"}}
        self.assertIn(("E_SCHEMA", "somnus.ownership.rights"), errs(check(p)))
        p["ownership"] = {"rights": {"status": "unspecified", "license_expression": "MIT"}}
        self.assertIn(("E_SCHEMA", "somnus.ownership.rights.license_expression"), errs(check(p)))
        p["ownership"] = {"rights": {"status": "specified", "license_expression": "MIT"}}
        self.assertEqual(errs(check(p)), set())

    def test_superseded_requires_replacements(self) -> None:
        p = base()
        p["lifecycle"]["status"] = "superseded"
        self.assertIn(("E_SCHEMA", "somnus.lifecycle"), errs(check(p)))
        p["lifecycle"]["replacement_refs"] = [{"ref": B}]
        self.assertEqual(errs(check(p)), set())

    def test_claim_object_exactly_one(self) -> None:
        p = base()
        claim = dict(CLAIM, object={"ref": B, "value": 1})
        p["knowledge"].update(regions=[REGION], claims=[claim])
        self.assertIn(("E_SCHEMA", "somnus.knowledge.claims[0].object"), errs(check(p)))
        claim["object"] = {}
        self.assertIn(("E_SCHEMA", "somnus.knowledge.claims[0].object"), errs(check(p)))


class TestTemporal(unittest.TestCase):
    def test_updated_before_created(self) -> None:
        p = base()
        p["time"] = {"created_at": "2026-02-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}
        self.assertIn(("E_TEMPORAL", "somnus.time.updated_at"), errs(check(p)))

    def test_offsets_compared_as_instants(self) -> None:
        p = base()
        p["time"] = {"created_at": "2026-01-01T05:00:00+05:00", "updated_at": "2026-01-01T00:30:00Z"}
        self.assertEqual(errs(check(p)), set())

    def test_bad_timestamps_and_dates(self) -> None:
        for field, value in [
            ("created_at", "2026-01-01T00:00:00"), ("created_at", "2026-01-01"),
            ("created_at", "2026-02-30T00:00:00Z"), ("reviewed_at", "2026-01-01 00:00:00Z"),
            ("authored_on", "2026-02-30"), ("authored_on", "2026-1-1"),
        ]:
            with self.subTest(field=field, value=value):
                p = base()
                p["time"] = {field: value}
                self.assertIn(("E_TEMPORAL", f"somnus.time.{field}"), errs(check(p)))

    def test_valid_time_basis_rules(self) -> None:
        bad = [
            ({"basis": "bounded", "from": "2026-01-01T00:00:00Z"}, "somnus.authority.valid_time"),
            ({"basis": "bounded", "from": "2026-01-02T00:00:00Z", "until": "2026-01-01T00:00:00Z"},
             "somnus.authority.valid_time.until"),
            ({"basis": "bounded", "from": "2026-01-01T00:00:00Z", "until": "2026-01-01T00:00:00Z"},
             "somnus.authority.valid_time.until"),
            ({"basis": "open"}, "somnus.authority.valid_time"),
            ({"basis": "open", "from": "2026-01-01T00:00:00Z", "until": "2027-01-01T00:00:00Z"},
             "somnus.authority.valid_time.until"),
            ({"basis": "timeless", "from": "2026-01-01T00:00:00Z"}, "somnus.authority.valid_time.from"),
            ({"basis": "unknown", "until": "2026-01-01T00:00:00Z"}, "somnus.authority.valid_time.until"),
        ]
        for vt, path in bad:
            with self.subTest(vt=vt):
                p = base()
                p["authority"]["valid_time"] = vt
                self.assertIn(("E_TEMPORAL", path), errs(check(p)))

    def test_valid_time_accepted_shapes(self) -> None:
        for vt in [
            {"basis": "bounded", "from": "2026-01-01T00:00:00Z", "until": "2026-01-02T00:00:00Z"},
            {"basis": "open", "from": "2026-01-01T00:00:00Z", "note": "since release"},
            {"basis": "timeless"}, {"basis": "unknown"},
        ]:
            with self.subTest(vt=vt):
                p = base()
                p["authority"]["valid_time"] = vt
                self.assertEqual(errs(check(p)), set())

    def test_valid_time_on_claims(self) -> None:
        p = base()
        p["knowledge"].update(regions=[REGION], claims=[dict(CLAIM, valid_time={"basis": "open"})])
        self.assertIn(("E_TEMPORAL", "somnus.knowledge.claims[0].valid_time"), errs(check(p)))


class TestAuthority(unittest.TestCase):
    def test_accepted_requires_valid_time_and_acceptance_ref(self) -> None:
        p = base()
        p["authority"]["standing"] = "accepted"
        diags = [d for d in check(p) if d.code == "E_AUTHORITY"]
        self.assertEqual({d.field for d in diags}, {"somnus.authority"})
        self.assertEqual(len(diags), 2)

    def test_empty_scopes(self) -> None:
        for standing in ("candidate", "accepted", "retired", "rejected"):
            with self.subTest(standing=standing):
                p = base()
                p["authority"].update(standing=standing, scopes=[])
                self.assertIn(("E_AUTHORITY", "somnus.authority.scopes"), errs(check(p)))

    def test_empty_scopes_allowed_when_unasserted(self) -> None:
        p = base()
        p["authority"] = {"standing": "unasserted", "scopes": []}
        self.assertEqual(errs(check(p)), set())

    def test_region_cannot_widen_authority_or_access(self) -> None:
        p = base()
        region = dict(REGION, authority={"standing": "accepted"},
                      access={"visibility": "public", "allowed_uses": ["archive", "training"]})
        p["knowledge"]["regions"] = [region]
        found = errs(check(p))
        self.assertIn(("E_AUTHORITY", "somnus.knowledge.regions[0].authority.standing"), found)
        self.assertIn(("E_POLICY", "somnus.knowledge.regions[0].access.visibility"), found)
        self.assertIn(("E_POLICY", "somnus.knowledge.regions[0].access.allowed_uses"), found)

    def test_region_may_narrow_access(self) -> None:
        p = base()
        p["knowledge"]["regions"] = [dict(REGION, access={"visibility": "operator-only", "allowed_uses": ["archive"]})]
        self.assertEqual(errs(check(p)), set())


class TestClaimsAndRegions(unittest.TestCase):
    def test_supported_claim_requires_evidence(self) -> None:
        p = base()
        p["knowledge"].update(regions=[REGION], claims=[dict(CLAIM, assessment="supported")])
        self.assertIn(("E_SCHEMA", "somnus.knowledge.claims[0].assessment"), errs(check(p)))
        p["knowledge"]["claims"][0]["evidence_refs"] = [{"ref": "https://example.org/evidence"}]
        self.assertEqual(errs(check(p)), set())

    def test_claim_region_ref_must_exist(self) -> None:
        p = base()
        p["knowledge"].update(regions=[REGION], claims=[dict(CLAIM, region_ref="r-missing")])
        self.assertIn(("E_REGION", "somnus.knowledge.claims[0].region_ref"), errs(check(p)))

    def test_region_claim_ids_consistency(self) -> None:
        p = base()
        other = {"id": "r-other", "kind": "section", "selector": {"kind": "heading", "text": "Body", "occurrence": 1}}
        p["knowledge"].update(regions=[dict(REGION, claim_ids=["c-one", "c-nope"]), dict(other, claim_ids=["c-one"])],
                              claims=[CLAIM])
        found = errs(check(p))
        self.assertIn(("E_REGION", "somnus.knowledge.regions[0].claim_ids[1]"), found)
        self.assertIn(("E_REGION", "somnus.knowledge.regions[1].claim_ids[0]"), found)
        self.assertNotIn(("E_REGION", "somnus.knowledge.regions[0].claim_ids[0]"), found)

    def test_duplicate_local_ids(self) -> None:
        p = base()
        p["knowledge"].update(regions=[REGION, REGION])
        self.assertIn(("E_SCHEMA", "somnus.knowledge.regions[1].id"), errs(check(p)))

    def test_other_region_references_must_exist(self) -> None:
        p = base()
        p["ingestion"]["exclude_regions"] = ["r-ghost"]
        self.assertIn(("E_REGION", "somnus.ingestion.exclude_regions[0]"), errs(check(p)))

    def test_marker_regions(self) -> None:
        body = "\n<!-- somnus:region:begin r-m -->\n\nText.\n\n<!-- somnus:region:end r-m -->\n"
        p = base()
        p["knowledge"]["regions"] = [{"id": "r-m", "kind": "section", "selector": {"kind": "marker", "name": "r-m"}}]
        self.assertEqual(check(p, body=body), [])
        self.assertIn(("E_REGION", "somnus.knowledge.regions[0].selector.name"), errs(check(p, body=BODY)))
        diags = check(base(), body=body)
        self.assertEqual(errs(diags), set())
        self.assertIn("W_REGION_UNREGISTERED", {d.code for d in diags})

    def test_marker_errors_are_core_region_errors(self) -> None:
        body = "\n<!-- somnus:region:begin r-m -->\n\nText.\n"
        self.assertIn("E_REGION", {d.code for d in check(base(), body=body) if d.is_error})

    def test_heading_selector_resolved_at_semantic(self) -> None:
        p = base()
        p["knowledge"]["regions"] = [dict(REGION, selector={"kind": "heading", "text": "Nope", "occurrence": 1})]
        self.assertEqual(errs(check(p, "core")), set())
        self.assertIn(("E_REGION", "somnus.knowledge.regions[0].selector"), errs(check(p, "semantic")))

    def test_selector_closed_per_kind(self) -> None:
        p = base()
        p["knowledge"]["regions"] = [dict(REGION, selector={"kind": "heading", "text": "Body", "occurrence": 1,
                                                            "name": "x"})]
        self.assertIn(("E_SCHEMA", "somnus.knowledge.regions[0].selector.name"), errs(check(p)))


class TestGraph(unittest.TestCase):
    def test_self_edge_on_acyclic_predicate(self) -> None:
        for pred in ("supersedes", "derived_from", "part_of"):
            with self.subTest(pred=pred):
                p = base()
                p["knowledge"]["relations"] = [relation(pred, A, A)]
                self.assertIn(("E_GRAPH", "somnus.knowledge.relations[0]"), errs(check(p)))

    def test_cycle(self) -> None:
        p = base()
        p["knowledge"]["relations"] = [relation("supersedes", A, B, "rel-a"), relation("supersedes", B, C, "rel-b"),
                                       relation("supersedes", C, A, "rel-c")]
        self.assertIn("E_GRAPH", {d.code for d in check(p)})

    def test_depends_on_cycles_allowed(self) -> None:
        p = base()
        p["knowledge"]["relations"] = [relation("depends_on", A, B, "rel-a"), relation("depends_on", B, A, "rel-b")]
        self.assertEqual(errs(check(p)), set())

    def test_acyclic_chain_ok(self) -> None:
        p = base()
        p["knowledge"]["relations"] = [relation("supersedes", A, B, "rel-a"), relation("supersedes", B, C, "rel-b")]
        self.assertEqual(errs(check(p)), set())

    def test_unknown_predicate_warns(self) -> None:
        p = base()
        p["knowledge"]["relations"] = [relation("frobnicates", A, A)]
        diags = check(p)
        self.assertEqual(errs(diags), set())
        self.assertIn(("W_PREDICATE", "somnus.knowledge.relations[0].predicate"), warns(diags))

    def test_supported_relation_requires_evidence(self) -> None:
        p = base()
        p["knowledge"]["relations"] = [dict(relation("cites", A, B), assessment="supported")]
        self.assertIn(("E_SCHEMA", "somnus.knowledge.relations[0].assessment"), errs(check(p)))


class TestReferences(unittest.TestCase):
    def test_unresolved_artifact_reference(self) -> None:
        p = base()
        p["authority"]["owner_ref"] = {"ref": B}
        self.assertEqual(errs(check(p, "core")), set())
        self.assertIn(("E_REFERENCE", "somnus.authority.owner_ref.ref"), errs(check(p, "semantic")))

    def test_resolved_through_check_set(self) -> None:
        p = base()
        p["authority"]["owner_ref"] = {"ref": B}
        other = base()
        other["id"] = B
        resolver = Resolver()
        resolver.add_payload(other)
        self.assertEqual(errs(check(p, "semantic", resolver)), set())

    def test_reference_region_must_exist_in_target(self) -> None:
        p = base()
        p["authority"]["owner_ref"] = {"ref": B, "revision": 1, "region": "r-missing"}
        other = base()
        other["id"] = B
        other["knowledge"]["regions"] = [REGION]
        resolver = Resolver()
        resolver.add_payload(other)
        self.assertIn(("E_REFERENCE", "somnus.authority.owner_ref.ref"), errs(check(p, "semantic", resolver)))
        p["authority"]["owner_ref"]["region"] = "r-body"
        self.assertEqual(errs(check(p, "semantic", resolver)), set())

    def test_external_references_count_as_resolved(self) -> None:
        p = base()
        p["knowledge"]["subjects"] = [A, "https://example.org/x", "doi:10.1000/1", "urn:isbn:0451450523"]
        self.assertEqual(errs(check(p, "semantic")), set())

    def test_entity_references_need_declaration(self) -> None:
        p = base()
        p["knowledge"]["subjects"] = ["urn:somnus:concept:thing"]
        self.assertIn(("E_REFERENCE", "somnus.knowledge.subjects[0]"), errs(check(p, "semantic")))
        p["knowledge"]["entities"] = [{"ref": "urn:somnus:concept:thing", "label": "Thing", "kind": "concept"}]
        self.assertEqual(errs(check(p, "semantic")), set())

    def test_example_urns_resolve_only_when_declared_here(self) -> None:
        p = base()
        p["knowledge"]["subjects"] = ["urn:somnus:example:widget"]
        resolver = Resolver()
        other = base()
        other["id"] = B
        other["knowledge"]["entities"] = [{"ref": "urn:somnus:example:widget", "label": "W", "kind": "tool"}]
        resolver.add_payload(other)
        self.assertIn(("E_REFERENCE", "somnus.knowledge.subjects[0]"), errs(check(p, "semantic", resolver)))
        p["knowledge"]["entities"] = [{"ref": "urn:somnus:example:widget", "label": "W", "kind": "tool"}]
        self.assertEqual(errs(check(p, "semantic", resolver)), set())

    def test_self_reference_to_future_revision(self) -> None:
        p = base()
        p["authority"]["owner_ref"] = {"ref": A, "revision": 5}
        self.assertIn(("E_REFERENCE", "somnus.authority.owner_ref.ref"), errs(check(p, "semantic")))

    def test_superseded_replacement_must_resolve(self) -> None:
        p = base()
        p["lifecycle"] = {"status": "superseded", "replacement_refs": [{"ref": B}]}
        self.assertIn(("E_REFERENCE", "somnus.lifecycle.replacement_refs[0].ref"), errs(check(p, "semantic")))

    def test_unregistered_constraint_language(self) -> None:
        p = base()
        p["context"] = {"release_constraints": [{"target_ref": A, "language": "regex@1", "expression": ".*"}]}
        self.assertEqual(errs(check(p, "core")), set())
        self.assertIn(("E_REFERENCE", "somnus.context.release_constraints[0].language"), errs(check(p, "semantic")))
        p["context"]["release_constraints"][0]["language"] = "semver-range@1"
        self.assertEqual(errs(check(p, "semantic")), set())

    def test_unregistered_capability(self) -> None:
        p = base()
        p["ingestion"]["requires"] = ["somnus-adapter-markdown@1", "magic@9"]
        self.assertIn(("E_POLICY", "somnus.ingestion.requires[1]"), errs(check(p, "semantic")))

    def test_missing_required_resource(self) -> None:
        p = base()
        p["content"] = {
            "resources": [{"ref": "definitely-missing-macros.tex", "media_type": "text/x-tex", "role": "macro-source",
                           "required": True}],
            "extraction": {"state": "complete", "limitations": []},
        }
        found = errs(check(p, "semantic"))
        self.assertIn(("E_EXTRACTION", "somnus.content.resources[0].ref"), found)
        self.assertIn(("E_EXTRACTION", "somnus.content.extraction.state"), found)


class TestCanon(unittest.TestCase):
    def resolver(self, **kw) -> Resolver:
        r = Resolver()
        r.add_payload(decision_record(**kw))
        return r

    def test_candidate_refused(self) -> None:
        p = base()
        p["lifecycle"]["status"] = "active"
        self.assertIn(("E_AUTHORITY", "somnus.authority.standing"), errs(check(p, "canon")))

    def test_accepted_with_active_decision_record(self) -> None:
        self.assertEqual(errs(check(accepted(), "canon", self.resolver())), set())

    def test_acceptance_record_must_be_decision_record(self) -> None:
        found = errs(check(accepted(), "canon", self.resolver(type_="report")))
        self.assertIn(("E_AUTHORITY", "somnus.authority.acceptance_ref"), found)

    def test_acceptance_record_must_be_active(self) -> None:
        found = errs(check(accepted(), "canon", self.resolver(status="draft")))
        self.assertIn(("E_AUTHORITY", "somnus.authority.acceptance_ref"), found)

    def test_unresolved_acceptance_record_stops_at_semantic(self) -> None:
        found = errs(check(accepted(), "canon", Resolver()))
        self.assertIn(("E_REFERENCE", "somnus.authority.acceptance_ref.ref"), found)
        self.assertNotIn(("E_AUTHORITY", "somnus.authority.acceptance_ref"), found)

    def test_status_must_be_active_or_provisional(self) -> None:
        for status, ok in [("active", True), ("provisional", True), ("draft", False), ("deprecated", False)]:
            with self.subTest(status=status):
                p = accepted()
                p["lifecycle"]["status"] = status
                found = errs(check(p, "canon", self.resolver()))
                self.assertEqual(("E_AUTHORITY", "somnus.lifecycle.status") in found, not ok)

    def test_open_conflict_blocks_canon(self) -> None:
        r = self.resolver()
        r.open_conflicts[A] = ["revision"]
        self.assertIn(("E_REVISION", "somnus.id"), errs(check(accepted(), "canon", r)))


class TestProfiles(unittest.TestCase):
    def spec_profile(self) -> dict:
        p = base()
        p["profiles"] = [{"schema": SPEC_PROFILE, "key": "specification"}]
        p["profile_data"] = {"specification": {"target_refs": [{"ref": A}], "acceptance_criteria": ["works"]}}
        return p

    def test_valid_profile(self) -> None:
        self.assertEqual(errs(check(self.spec_profile(), "semantic")), set())

    def test_profile_keys_must_equal_declarations(self) -> None:
        p = self.spec_profile()
        p["profile_data"]["other"] = {}
        self.assertIn(("E_SCHEMA", "somnus.profile_data.other"), errs(check(p)))
        p = self.spec_profile()
        del p["profile_data"]["specification"]
        self.assertIn(("E_SCHEMA", "somnus.profile_data"), errs(check(p)))

    def test_duplicate_profile_declarations(self) -> None:
        p = self.spec_profile()
        p["profiles"].append({"schema": SPEC_PROFILE, "key": "specification"})
        found = errs(check(p))
        self.assertIn(("E_SCHEMA", "somnus.profiles[1].key"), found)
        self.assertIn(("E_SCHEMA", "somnus.profiles[1].schema"), found)

    def test_unknown_profile_release(self) -> None:
        # SPEC section 21 fixture 12: the source is retained but acceptance is refused.
        p = self.spec_profile()
        p["profiles"][0]["schema"] = "somnus://metadata/profile/specification/9.0.0"
        doc = make(p)
        self.assertIn(("E_SCHEMA", "somnus.profiles[0].schema"), errs(validate(doc)))
        self.assertEqual(doc.payload["profiles"][0]["schema"], "somnus://metadata/profile/specification/9.0.0")

    def test_profile_payload_validated(self) -> None:
        p = self.spec_profile()
        p["profile_data"]["specification"]["acceptance_criteria"] = []
        p["profile_data"]["specification"]["normative_region_refs"] = ["r-ghost"]
        found = errs(check(p))
        self.assertIn(("E_SCHEMA", "somnus.profile_data.specification.acceptance_criteria"), found)
        self.assertIn(("E_REGION", "somnus.profile_data.specification.normative_region_refs[0]"), found)


class TestLevelGating(unittest.TestCase):
    def test_core_errors_stop_semantic(self) -> None:
        p = base()
        p["revision"] = "one"
        p["authority"]["owner_ref"] = {"ref": B}
        codes = {d.code for d in check(p, "semantic")}
        self.assertIn("E_SCHEMA", codes)
        self.assertNotIn("E_REFERENCE", codes)

    def test_semantic_errors_stop_canon(self) -> None:
        p = base()
        p["authority"]["owner_ref"] = {"ref": B}
        codes = {d.code for d in check(p, "canon")}
        self.assertEqual(codes, {"E_REFERENCE"})

    def test_carrier_level_skips_schema(self) -> None:
        p = base()
        p["extra"] = 1
        self.assertEqual(check(p, "carrier"), [])

    def test_missing_envelope(self) -> None:
        diags = validate(D.from_text(Path("x.md"), "# Just a body\n"))
        self.assertEqual([d.code for d in diags], ["E_ENVELOPE"])

    def test_envelope_error_stops_everything(self) -> None:
        text = "---\n" + D.canonical_yaml({"somnus": base()}) + "\n"
        self.assertEqual({d.code for d in validate(D.from_text(Path("x.md"), text), "canon")}, {"E_ENVELOPE"})

    def test_yaml_error_stops_schema(self) -> None:
        text = "---\nsomnus:\n  title: plain\n  extra: 1\n---\n"
        self.assertEqual({d.code for d in validate(D.from_text(Path("x.md"), text), "semantic")}, {"E_YAML"})


class TestPermitsUse(unittest.TestCase):
    def test_reason_permitted_training_refused(self) -> None:
        # SPEC section 21 fixture 21.
        p = base()
        self.assertTrue(permits_use(p, "reason"))
        self.assertFalse(permits_use(p, "training"))
        self.assertFalse(permits_use(p, "execute"))

    def test_disposition_caps(self) -> None:
        p = base()
        p["access"]["allowed_uses"] = ["archive", "search", "reason", "training"]
        for disposition, allowed in [
            ("candidate", {"archive", "search", "reason", "training"}),
            ("canonical-candidate", {"archive", "search", "reason", "training"}),
            ("archive-only", {"archive", "search"}),
            ("excluded", {"archive"}),
        ]:
            with self.subTest(disposition=disposition):
                p["ingestion"]["disposition"] = disposition
                got = {u for u in ("archive", "search", "reason", "quote", "export", "training", "execute")
                       if permits_use(p, u)}
                self.assertEqual(got, allowed)

    def test_region_narrowing_and_exclusion(self) -> None:
        p = base()
        p["knowledge"]["regions"] = [dict(REGION, access={"allowed_uses": ["archive"]}),
                                     dict(REGION, id="r-two")]
        p["ingestion"]["exclude_regions"] = ["r-two"]
        self.assertFalse(permits_use(p, "reason", "r-body"))
        self.assertTrue(permits_use(p, "archive", "r-body"))
        self.assertFalse(permits_use(p, "search", "r-two"))
        self.assertTrue(permits_use(p, "reason"))

    def test_missing_access_permits_nothing(self) -> None:
        self.assertFalse(permits_use({}, "archive"))


class TestExtensions(unittest.TestCase):
    def ext_payload(self) -> dict:
        p = base()
        p["extensions"] = {"acme.tools": {"schema": "https://acme.example/ext/1",
                                          "data": {"zeta": 1, "alpha": [{"ref": B}], "note": "keep"}}}
        return p

    def test_unknown_extension_preserved(self) -> None:
        # SPEC section 21 fixture 11.
        doc = make(self.ext_payload())
        self.assertEqual(errs(validate(doc, "semantic")), set())
        again = D.from_text(Path("x.md"), doc.render(doc.copy_payload()))
        self.assertEqual(again.payload["extensions"], self.ext_payload()["extensions"])
        self.assertEqual(list(again.payload["extensions"]["acme.tools"]["data"]), ["zeta", "alpha", "note"])

    def test_extension_refs_excluded_from_resolution(self) -> None:
        self.assertNotIn("E_REFERENCE", {d.code for d in check(self.ext_payload(), "semantic")})

    def test_extension_shape_enforced(self) -> None:
        p = base()
        p["extensions"] = {"Acme": {"schema": "x", "data": 1}, "ok": {"schema": "x"}}
        found = errs(check(p))
        self.assertIn(("E_SCHEMA", "somnus.extensions.Acme"), found)
        self.assertIn(("E_SCHEMA", "somnus.extensions.ok"), found)


if __name__ == "__main__":
    unittest.main()
