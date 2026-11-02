-- somnus:metadata:v2
-- somnus:
--   schema: "somnus://metadata/core/2.0.0"
--   id: "urn:somnus:artifact:01a19a67-7f99-719a-b6bf-f208d18770f5"
--   revision: 1
--   title: "Search"
--   classification:
--     category: "engineering"
--     type: "source-code"
--     role: "informative"
--     scope: "component"
--     tags: []
--   lifecycle:
--     status: "draft"
--   authority:
--     standing: "candidate"
--     scopes:
--       - target_ref: "urn:somnus:artifact:01a19a67-7f99-719a-b6bf-f208d18770f5"
--         aspects: ["content"]
--   time: {}
--   names:
--     slug: "search"
--   knowledge:
--     coverage: "artifact"
--     subjects: ["urn:somnus:artifact:01a19a67-7f99-719a-b6bf-f208d18770f5"]
--   access:
--     visibility: "internal"
--     allowed_uses: ["archive", "search", "reason"]
--   ingestion:
--     disposition: "candidate"
--     body_role: "source"
-- somnus:end
-- Somnus full-text search index, schema version 2 (SPEC §18.4, D19).
-- Derived from each present location as observed at index time; never a source of truth.
-- rowid is locations.id. 'somnus index --full' rebuilds every row.

CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(
    path,
    title,
    summary,
    tags,
    body,
    tokenize = 'porter unicode61 remove_diacritics 2'
);
