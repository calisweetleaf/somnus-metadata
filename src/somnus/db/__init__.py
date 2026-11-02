# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7f78-755a-aae3-d4570d3d564d"
#   revision: 1
#   title: "Global SQLite registry (SPEC §18)"
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
#       - target_ref: "urn:somnus:artifact:01a19a67-7f78-755a-aae3-d4570d3d564d"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "global-sqlite-registry-spec-18"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7f78-755a-aae3-d4570d3d564d"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Global SQLite registry (SPEC §18)."""

from somnus.db.store import ScanReport, Store, connect_readonly, glob_regex, matches_any, now_iso, run_query

__all__ = ["ScanReport", "Store", "connect_readonly", "glob_regex", "matches_any", "now_iso", "run_query"]
