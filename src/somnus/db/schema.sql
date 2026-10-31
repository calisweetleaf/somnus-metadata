-- Somnus global registry, schema version 2 (SPEC §18). The full-text index ships in search.sql (D19).
-- Zero JSON: headers are canonical restricted YAML text; every column is a plain value.

CREATE TABLE IF NOT EXISTS roots (
    id            INTEGER PRIMARY KEY,
    path          TEXT    NOT NULL UNIQUE,
    added_at      TEXT    NOT NULL,
    last_scan_at  TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    id                TEXT    PRIMARY KEY,
    title             TEXT    NOT NULL,
    type              TEXT    NOT NULL,
    category          TEXT    NOT NULL,
    role              TEXT    NOT NULL,
    scope             TEXT    NOT NULL,
    status            TEXT    NOT NULL,
    standing          TEXT    NOT NULL,
    visibility        TEXT    NOT NULL,
    current_revision  INTEGER NOT NULL CHECK (current_revision >= 1),
    first_seen_at     TEXT    NOT NULL,
    last_seen_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS revisions (
    artifact_id     TEXT    NOT NULL REFERENCES artifacts(id),
    revision        INTEGER NOT NULL CHECK (revision >= 1),
    title           TEXT    NOT NULL,
    status          TEXT    NOT NULL,
    standing        TEXT    NOT NULL,
    header_yaml     TEXT    NOT NULL,
    payload_digest  TEXT    NOT NULL,
    body_digest     TEXT    NOT NULL,
    observed_at     TEXT    NOT NULL,
    PRIMARY KEY (artifact_id, revision)
);

CREATE TABLE IF NOT EXISTS locations (
    id              INTEGER PRIMARY KEY,
    root_id         INTEGER NOT NULL REFERENCES roots(id),
    rel_path        TEXT    NOT NULL,
    artifact_id     TEXT    NOT NULL REFERENCES artifacts(id),
    revision        INTEGER NOT NULL,
    carrier         TEXT    NOT NULL,
    file_mtime      REAL    NOT NULL,
    file_size       INTEGER NOT NULL,
    payload_digest  TEXT    NOT NULL,
    body_digest     TEXT    NOT NULL,
    present         INTEGER NOT NULL DEFAULT 1 CHECK (present IN (0, 1)),
    first_seen_at   TEXT    NOT NULL,
    last_seen_at    TEXT    NOT NULL,
    UNIQUE (root_id, rel_path)
);
CREATE INDEX IF NOT EXISTS locations_artifact ON locations(artifact_id);

CREATE TABLE IF NOT EXISTS tags (
    artifact_id  TEXT NOT NULL REFERENCES artifacts(id),
    tag          TEXT NOT NULL,
    PRIMARY KEY (artifact_id, tag)
);

CREATE TABLE IF NOT EXISTS regions (
    artifact_id    TEXT    NOT NULL,
    revision       INTEGER NOT NULL,
    region_id      TEXT    NOT NULL,
    kind           TEXT    NOT NULL,
    selector_kind  TEXT    NOT NULL,
    title          TEXT,
    standing       TEXT,
    PRIMARY KEY (artifact_id, revision, region_id),
    FOREIGN KEY (artifact_id, revision) REFERENCES revisions(artifact_id, revision)
);

CREATE TABLE IF NOT EXISTS relations (
    artifact_id      TEXT    NOT NULL,
    revision         INTEGER NOT NULL,
    relation_id      TEXT    NOT NULL,
    subject_ref      TEXT    NOT NULL,
    predicate        TEXT    NOT NULL,
    object_ref       TEXT    NOT NULL,
    object_revision  INTEGER,
    assessment       TEXT    NOT NULL,
    time_basis       TEXT    NOT NULL,
    valid_from       TEXT,
    valid_until      TEXT,
    known_predicate  INTEGER NOT NULL CHECK (known_predicate IN (0, 1)),
    PRIMARY KEY (artifact_id, revision, relation_id),
    FOREIGN KEY (artifact_id, revision) REFERENCES revisions(artifact_id, revision)
);
CREATE INDEX IF NOT EXISTS relations_object ON relations(object_ref);

CREATE TABLE IF NOT EXISTS entities (
    artifact_id  TEXT    NOT NULL,
    revision     INTEGER NOT NULL,
    ref          TEXT    NOT NULL,
    label        TEXT    NOT NULL,
    kind         TEXT    NOT NULL,
    PRIMARY KEY (artifact_id, revision, ref),
    FOREIGN KEY (artifact_id, revision) REFERENCES revisions(artifact_id, revision)
);

CREATE TABLE IF NOT EXISTS claims (
    artifact_id  TEXT    NOT NULL,
    revision     INTEGER NOT NULL,
    claim_id     TEXT    NOT NULL,
    subject_ref  TEXT    NOT NULL,
    predicate    TEXT    NOT NULL,
    kind         TEXT    NOT NULL,
    assessment   TEXT    NOT NULL,
    statement    TEXT    NOT NULL,
    region_ref   TEXT    NOT NULL,
    object_ref   TEXT,
    PRIMARY KEY (artifact_id, revision, claim_id),
    FOREIGN KEY (artifact_id, revision) REFERENCES revisions(artifact_id, revision)
);

CREATE TABLE IF NOT EXISTS conflicts (
    id           INTEGER PRIMARY KEY,
    kind         TEXT    NOT NULL CHECK (kind IN ('revision', 'duplicate-id', 'authority', 'identity')),
    conflict_key TEXT    NOT NULL,
    artifact_id  TEXT    NOT NULL,
    revision     INTEGER,
    path         TEXT,
    detail       TEXT    NOT NULL,
    state        TEXT    NOT NULL DEFAULT 'open' CHECK (state IN ('open', 'resolved')),
    opened_at    TEXT    NOT NULL,
    resolved_at  TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS conflicts_one_open ON conflicts(kind, conflict_key) WHERE state = 'open';

CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    at           TEXT    NOT NULL,
    actor        TEXT    NOT NULL,
    action       TEXT    NOT NULL,
    artifact_id  TEXT,
    revision     INTEGER,
    path         TEXT,
    detail       TEXT
);

CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'events are append-only');
END;

CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'events are append-only');
END;

CREATE VIEW IF NOT EXISTS docs AS
SELECT a.id               AS id,
       a.title            AS title,
       a.type             AS type,
       a.status           AS status,
       a.standing         AS standing,
       a.current_revision AS revision,
       l.revision         AS file_revision,
       l.carrier          AS carrier,
       rtrim(r.path, '/\') || '/' || l.rel_path AS path
FROM artifacts a
JOIN locations l ON l.artifact_id = a.id AND l.present = 1
JOIN roots r ON r.id = l.root_id;

CREATE VIEW IF NOT EXISTS open_conflicts AS
SELECT id, kind, artifact_id, revision, path, detail, opened_at
FROM conflicts
WHERE state = 'open';

CREATE VIEW IF NOT EXISTS history AS
SELECT id, at, actor, action, artifact_id, revision, path, detail
FROM events
ORDER BY id DESC;
