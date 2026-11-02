# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7cc0-724c-99c0-9556e5eb871e"
#   revision: 1
#   title: "Somnus metadata system: schema constants and package version"
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
#       - target_ref: "urn:somnus:artifact:01a19a67-7cc0-724c-99c0-9556e5eb871e"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnus-metadata-system-schema-constants-and-package-version"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7cc0-724c-99c0-9556e5eb871e"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Somnus metadata system: schema constants and package version."""

__version__ = "2.1.0"

CORE_SCHEMA = "somnus://metadata/core/2.0.0"
SPEC_PROFILE = "somnus://metadata/profile/specification/1.0.0"
BENCHMARK_PROFILE = "somnus://metadata/profile/benchmark/1.0.0"
MIGRATION_EXTENSION = "somnus://metadata/extension/migration-v0.1/1.0.0"
DB_USER_VERSION = 2
