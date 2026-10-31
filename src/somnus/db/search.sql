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
