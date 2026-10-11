"""SPEC Â§21 conformance fixtures: one test per row, numbered to match the table."""

from __future__ import annotations

import copy
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path

from somnus import CORE_SCHEMA, ids, yamlsub
from somnus import config as C
from somnus import document as D
from somnus.commands import migrate
from somnus.db import Store
from somnus.model.validate import permits_use, validate
from somnus.regions import scan_markers

DR_ID = "urn:somnus:artifact:01a12a94-8657-715c-9044-0000000000d1"
ENTITY = "urn:somnus:entity:memory-engine"


def payload(aid: str | None = None, **overrides) -> dict:
    """Minimal valid core 2.0.0 payload."""
    aid = aid or ids.new_artifact_urn()
    p = {
        "schema": CORE_SCHEMA,
        "id": aid,
        "revision": 1,
        "title": "Fixture",
        "classification": {"category": "engineering", "type": "specification", "role": "normative",
                           "scope": "component", "tags": ["fixture"]},
        "lifecycle": {"status": "draft"},
        "authority": {"standing": "candidate", "scopes": [{"target_ref": aid, "aspects": ["content"]}]},
        "time": {},
        "knowledge": {"coverage": "artifact", "subjects": [aid]},
        "access": {"visibility": "internal", "allowed_uses": ["archive", "search", "reason"]},
        "ingestion": {"disposition": "candidate", "body_role": "specification"},
    }
    p.update(overrides)
    return p


def markdown(p: dict, body: str = "# Fixture\n") -> str:
    return "---\n" + D.canonical_yaml({"somnus": p}) + "---\n" + body


def errors(diags, code: str | None = None) -> list:
    return [d for d in diags if d.is_error and (code is None or d.code == code)]


class RegistryCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "root"
        self.root.mkdir()
        self.store = Store.open(self.tmp / "home" / "somnus.db", actor="conformance")

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def put(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_bytes(text.encode("utf-8"))
        return path

    def scan(self):
        report = self.store.scan([self.root], full=True)
        self.assertFalse(errors(report.diagnostics), report.diagnostics)
        return report

    def q(self, sql: str, *params) -> list:
        return self.store.conn.execute(sql, params).fetchall()


class TestConformance(unittest.TestCase):
    # 1 ---------------------------------------------------------------------------
    def test_01_same_payload_in_every_carrier(self) -> None:
        p = payload(title="Shared")
        hosts = {
            "doc.md": "# Shared\n",
            "paper.tex": "\\documentclass{article}\n\\begin{document}\nx\n\\end{document}\n",
            "conf.yaml": "key: 1\nlist:\n  - a\n",
            "conf.toml": "a = 1\n[t]\nb = \"x\"\n",
        }
        for name, host in hosts.items():
            with self.subTest(carrier=name):
                rendered = D.from_text(Path(name), host).render(p)
                self.assertEqual(D.from_text(Path(name), rendered).payload, p)
        side = copy.deepcopy(p)
        side["bindings"] = [{"target": "data.json", "role": "primary", "required": True}]
        parsed = D.from_text(Path("data.json.somnus.yaml"), D.new_sidecar_text(side)).payload
        parsed.pop("bindings")
        self.assertEqual(parsed, p)

    # 2 ---------------------------------------------------------------------------
    def test_02_host_data_tree_unchanged(self) -> None:
        toml_host = 'title = "x"\n[server]\nport = 8080\nhosts = ["a", "b"]\n'
        rendered = D.from_text(Path("c.toml"), toml_host).render(payload())
        self.assertEqual(tomllib.loads(rendered), tomllib.loads(toml_host))
        yaml_host = 'name: "svc"\nreplicas: 3\nports:\n  - 80\n  - 443\n'
        rendered = D.from_text(Path("c.yaml"), yaml_host).render(payload())
        before = yamlsub.parse(yaml_host, lenient=True).data
        after = yamlsub.parse(rendered, lenient=True).data
        self.assertEqual(after, before)

    # 3 ---------------------------------------------------------------------------
    def test_03_preambles_preserved(self) -> None:
        py = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nimport os\n"
        lines = D.from_text(Path("t.py"), py).render(payload()).splitlines()
        self.assertEqual(lines[:2], ["#!/usr/bin/env python3", "# -*- coding: utf-8 -*-"])
        self.assertEqual(lines[2], "# somnus:metadata:v2")
        sh = "#!/bin/sh\necho hi\n"
        lines = D.from_text(Path("t.sh"), sh).render(payload()).splitlines()
        self.assertEqual(lines[0], "#!/bin/sh")
        self.assertEqual(lines[1], "# somnus:metadata:v2")
        self.assertEqual(lines[-1], "echo hi")

    # 4 ---------------------------------------------------------------------------
    def test_04_duplicate_nested_key_rejected(self) -> None:
        text = 'somnus:\n  a:\n    b: "1"\n    b: "2"\n'
        with self.assertRaises(yamlsub.YAMLError):
            yamlsub.parse(text)

    # 5 ---------------------------------------------------------------------------
    def test_05_quoted_scalars_stay_strings(self) -> None:
        data = yamlsub.parse('a: "NO"\nb: "on"\nc: "1.10"\nd: "2026-01-01"\ne: "0x1F"\n').data
        self.assertEqual(data, {"a": "NO", "b": "on", "c": "1.10", "d": "2026-01-01", "e": "0x1F"})
        for value in data.values():
            self.assertIsInstance(value, str)

    # 6 ---------------------------------------------------------------------------
    def test_06_metadata_in_code_example_is_inert(self) -> None:
        body = ("# Doc\n\n```markdown\n<!-- somnus:metadata:v2\nsomnus:\n  id: \"x\"\nsomnus:end -->\n"
                "<!-- somnus:region:begin r-fake -->\n<!-- somnus:region:end r-fake -->\n```\n\n"
                "    <!-- somnus:region:begin r-indented -->\n")
        doc = D.from_text(Path("d.md"), markdown(payload(), body))
        self.assertFalse(doc.issues)
        self.assertEqual(doc.envelope.kind, "frontmatter-full")
        scan = scan_markers(doc.lines, doc.carrier.region_style, doc.ignore_span)
        self.assertEqual(scan.ranges, {})
        self.assertFalse(errors(validate(doc, "semantic")))
        py = 'x = 1\nS = """\n# somnus:metadata:v2\n# somnus:\n# somnus:end\n"""\n'
        self.assertIsNone(D.from_text(Path("e.py"), py).envelope)

    # 7 ---------------------------------------------------------------------------
    def test_07_nested_regions_valid(self) -> None:
        body = ("\n<!-- somnus:region:begin r-outer -->\n\nA\n\n<!-- somnus:region:begin r-inner -->\n\nB\n\n"
                "<!-- somnus:region:end r-inner -->\n\n<!-- somnus:region:end r-outer -->\n")
        regions = [{"id": r, "kind": "section", "selector": {"kind": "marker", "name": r}}
                   for r in ("r-outer", "r-inner")]
        p = payload()
        p["knowledge"]["regions"] = regions
        doc = D.from_text(Path("n.md"), markdown(p, body))
        self.assertFalse(errors(validate(doc, "semantic")))
        scan = scan_markers(doc.lines, doc.carrier.region_style, doc.ignore_span)
        self.assertEqual(scan.ranges["r-inner"].parent, "r-outer")
        self.assertEqual(scan.ranges["r-inner"].depth, 1)

    # 8 ---------------------------------------------------------------------------
    def test_08_crossing_or_missing_marker_is_error(self) -> None:
        crossing = ("\n<!-- somnus:region:begin r-a -->\n\n<!-- somnus:region:begin r-b -->\n\n"
                    "<!-- somnus:region:end r-a -->\n\n<!-- somnus:region:end r-b -->\n")
        missing = "\n<!-- somnus:region:begin r-a -->\n\nText\n"
        for name, body in (("crossing", crossing), ("missing", missing)):
            with self.subTest(case=name):
                doc = D.from_text(Path("x.md"), markdown(payload(), body))
                self.assertTrue(errors(validate(doc, "core"), "E_REGION"))
        p = payload()
        p["knowledge"]["regions"] = [{"id": "r-gone", "kind": "section", "selector": {"kind": "marker", "name": "r-gone"}}]
        self.assertTrue(errors(validate(D.from_text(Path("y.md"), markdown(p)), "core"), "E_REGION"))

    # 9 ---------------------------------------------------------------------------
    def test_09_uuid4_import_keeps_id_and_invents_no_date(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        try:
            v4 = "3f2b8c1e-5d4a-4e6f-9a0b-1c2d3e4f5a6b"
            path = tmp / "legacy.md"
            path.write_text(f'---\nid: "{v4}"\ntitle: "Legacy"\nclassification:\n  type: report\n---\nBody\n',
                            encoding="utf-8")
            old, new, p = migrate.plan(path, C.load(tmp))
            self.assertEqual(p["id"], f"urn:somnus:artifact:{v4}")
            self.assertEqual(ids.uuid_version(p["id"]), 4)
            self.assertNotIn("created_at", p["time"])
            self.assertNotIn("authored_on", p["time"])
            self.assertFalse(errors(validate(D.from_text(path, new), "core")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # 10 --------------------------------------------------------------------------
    def test_10_mint_time_need_not_equal_creation(self) -> None:
        minted = f"urn:somnus:artifact:{ids.uuid7(unix_ms=1_577_836_800_000)}"  # 2020-01-01
        p = payload(minted, time={"created_at": "2026-03-30T10:00:00Z"})
        self.assertEqual(ids.uuid7_time(minted).year, 2020)
        self.assertFalse(errors(validate(D.from_text(Path("t.md"), markdown(p)), "semantic")))

    # 11 --------------------------------------------------------------------------
    def test_11_unknown_extension_preserved_not_trusted(self) -> None:
        ext = {"acme.tools": {"schema": "https://acme.example/meta/1", "data": {"claims": ["not trusted"],
                                                                                "n": 3}}}
        p = payload(extensions=ext)
        doc = D.from_text(Path("e.md"), markdown(p))
        self.assertFalse(errors(validate(doc, "semantic")))
        self.assertEqual(D.from_text(Path("e.md"), doc.render(doc.copy_payload())).payload["extensions"], ext)

    # 12 --------------------------------------------------------------------------
    def test_12_unknown_release_retained_but_refused(self) -> None:
        p = payload(schema="somnus://metadata/core/2.1.0")
        doc = D.from_text(Path("r.md"), markdown(p))
        self.assertTrue(errors(validate(doc, "core"), "E_SCHEMA"))
        self.assertEqual(doc.payload["schema"], "somnus://metadata/core/2.1.0")
        q = payload(profiles=[{"schema": "somnus://metadata/profile/unknown/9.9.9", "key": "unknown"}],
                    profile_data={"unknown": {"x": 1}})
        doc = D.from_text(Path("s.md"), markdown(q))
        self.assertTrue(errors(validate(doc, "semantic"), "E_SCHEMA"))
        self.assertEqual(doc.payload["profile_data"], {"unknown": {"x": 1}})

    # 18 --------------------------------------------------------------------------
    def test_18_partial_extraction_not_reconstructed(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        try:
            content = {"resources": [{"ref": "macros.sty", "media_type": "text/x-tex", "role": "macro-source",
                                      "required": False}],
                       "extraction": {"state": "partial", "limitations": ["macro \\Rk undefined; eq. 3 clipped"]}}
            p = payload(content=content)
            path = tmp / "paper.md"
            doc = D.from_text(path, markdown(p))
            self.assertFalse(errors(validate(doc, "semantic")))
            self.assertNotIn("claims", doc.payload["knowledge"])
            p2 = copy.deepcopy(p)
            p2["content"]["resources"][0]["required"] = True
            p2["content"]["extraction"]["state"] = "complete"
            self.assertTrue(errors(validate(D.from_text(path, markdown(p2)), "semantic"), "E_EXTRACTION"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # 21 --------------------------------------------------------------------------
    def test_21_reason_permitted_training_refused(self) -> None:
        p = payload()
        self.assertTrue(permits_use(p, "reason"))
        self.assertFalse(permits_use(p, "training"))
        archived = payload(ingestion={"disposition": "archive-only", "body_role": "narrative"})
        self.assertFalse(permits_use(archived, "reason"))


class TestRegistryConformance(RegistryCase):
    def accepted(self, name: str, start: str, claims: bool = False) -> tuple[str, Path]:
        aid = ids.new_artifact_urn()
        p = payload(aid, title=f"Accepted {name}")
        p["lifecycle"] = {"status": "active"}
        p["authority"] = {"standing": "accepted", "scopes": [{"target_ref": ENTITY, "aspects": ["behavior"]}],
                          "valid_time": {"basis": "open", "from": start}, "acceptance_ref": {"ref": DR_ID}}
        body = "# Accepted\n"
        if claims:
            p["knowledge"]["regions"] = [{"id": "r-h", "kind": "hypothesis", "selector": {"kind": "marker",
                                                                                           "name": "r-h"}}]
            p["knowledge"]["claims"] = [{
                "id": "c-latency", "subject_ref": ENTITY, "predicate": "predicts",
                "object": {"value": "p99 below 5 ms"}, "statement": "A 64KB tier lowers p99 latency.",
                "kind": "hypothesis", "assessment": "unassessed", "valid_time": {"basis": "unknown"},
                "region_ref": "r-h"}]
            body += "\n<!-- somnus:region:begin r-h -->\n\nHypothesis text.\n\n<!-- somnus:region:end r-h -->\n"
        return aid, self.put(f"{name}.md", markdown(p, body))

    def decision_record(self) -> None:
        p = payload(DR_ID, title="Accept the memory engine")
        p["classification"]["type"] = "decision-record"
        p["classification"]["category"] = "governance"
        p["lifecycle"] = {"status": "active"}
        p["knowledge"]["entities"] = [{"ref": ENTITY, "label": "Memory Engine", "kind": "system"}]
        self.put("decision.md", markdown(p))

    # 13 --------------------------------------------------------------------------
    def test_13_rename_and_representation_keep_identity(self) -> None:
        p = payload(representations=[{"locator": "out/fixture.pdf", "media_type": "application/pdf",
                                      "role": "rendered", "source_revision": 1}])
        path = self.put("a.md", markdown(p))
        self.scan()
        path.rename(self.root / "b.md")
        self.scan()
        self.assertEqual(self.q("SELECT id FROM artifacts"), [(p["id"],)])
        self.assertEqual(self.q("SELECT rel_path FROM locations WHERE present = 1"), [("b.md",)])
        self.assertEqual(self.q("SELECT count(*) FROM open_conflicts"), [(0,)])

    # 14 --------------------------------------------------------------------------
    def test_14_same_revision_distinct_states_conflict(self) -> None:
        p = payload()
        self.put("one.md", markdown(p, "# One\n"))
        self.scan()
        self.put("two.md", markdown(p, "# Two, different body\n"))
        self.store.scan([self.root], full=True)
        kinds = sorted(k for (k,) in self.q("SELECT kind FROM open_conflicts"))
        self.assertEqual(kinds, ["duplicate-id", "revision"])
        self.assertEqual(self.q("SELECT count(*) FROM revisions"), [(1,)])
        res = self.store.resolver()
        self.assertIn("revision", res.open_conflicts[p["id"]])

    # 15 --------------------------------------------------------------------------
    def test_15_overlapping_accepted_authorities_no_canon(self) -> None:
        self.decision_record()
        a_id, a_path = self.accepted("a", "2026-01-01T00:00:00Z")
        self.scan()
        self.assertFalse(errors(validate(D.load(a_path), "canon", self.store.resolver())))
        b_id, _ = self.accepted("b", "2026-06-01T00:00:00Z")
        self.store.scan([self.root], full=True)
        conflicted = sorted(aid for (aid,) in self.q("SELECT artifact_id FROM open_conflicts WHERE kind = 'authority'"))
        self.assertEqual(conflicted, sorted([a_id, b_id]))
        self.assertTrue(errors(validate(D.load(a_path), "canon", self.store.resolver()), "E_AUTHORITY"))

    # 16 --------------------------------------------------------------------------
    def test_16_shared_alias_does_not_merge_entities(self) -> None:
        old = payload(title="Old system note")
        old["knowledge"]["entities"] = [{
            "ref": "urn:somnus:entity:atlas-2019", "label": "Atlas", "kind": "system",
            "aliases": [{"id": "a-atlas", "label": "ATLAS", "kind": "acronym", "valid_time": {"basis": "unknown"}}]}]
        new = payload(title="New project note")
        new["knowledge"]["entities"] = [{"ref": "urn:somnus:entity:atlas-2026", "label": "ATLAS", "kind": "project"}]
        self.put("old.md", markdown(old))
        self.put("new.md", markdown(new))
        self.scan()
        refs = sorted(r for (r,) in self.q("SELECT DISTINCT ref FROM entities"))
        self.assertEqual(refs, ["urn:somnus:entity:atlas-2019", "urn:somnus:entity:atlas-2026"])
        self.assertEqual(self.store.resolver().entities, set(refs))

    # 17 --------------------------------------------------------------------------
    def test_17_hypothesis_in_accepted_artifact_stays_hypothesis(self) -> None:
        self.decision_record()
        aid, path = self.accepted("research", "2026-01-01T00:00:00Z", claims=True)
        self.scan()
        self.assertEqual(self.q("SELECT standing FROM artifacts WHERE id = ?", aid), [("accepted",)])
        self.assertEqual(self.q("SELECT kind, assessment FROM claims WHERE artifact_id = ?", aid),
                         [("hypothesis", "unassessed")])
        self.assertFalse(errors(validate(D.load(path), "canon", self.store.resolver())))
        self.assertEqual(D.load(path).payload["knowledge"]["claims"][0]["kind"], "hypothesis")

    # 19 --------------------------------------------------------------------------
    def test_19_reingestion_creates_no_duplicates(self) -> None:
        self.put("r.md", markdown(payload()))
        self.scan()
        counts = [self.q(f"SELECT count(*) FROM {t}") for t in ("artifacts", "revisions", "locations", "tags")]
        for _ in range(3):
            self.scan()
        self.assertEqual([self.q(f"SELECT count(*) FROM {t}") for t in ("artifacts", "revisions", "locations",
                                                                       "tags")], counts)

    # 20 --------------------------------------------------------------------------
    def test_20_disappearance_is_not_a_tombstone(self) -> None:
        p = payload()
        path = self.put("gone.md", markdown(p))
        self.scan()
        path.unlink()
        report = self.store.scan([self.root])
        self.assertEqual(report.missing, 1)
        self.assertEqual(self.q("SELECT present FROM locations"), [(0,)])
        self.assertEqual(self.q("SELECT id FROM artifacts"), [(p["id"],)])
        self.assertEqual(self.q("SELECT count(*) FROM revisions"), [(1,)])
        actions = [a for (a,) in self.q("SELECT action FROM events")]
        self.assertIn("missing", actions)
        self.assertNotIn("delete", actions)


if __name__ == "__main__":
    unittest.main()
