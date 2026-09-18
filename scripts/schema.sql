-- Jev-Me audit. One file: scripts/jev-me.sqlite
-- sessions = interviews
-- events   = everything that happened, in order
-- payload  = JSON. Never store TYPESAFE_API_KEY.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('open', 'closed', 'abandoned')),
    started_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions (id),
    at TEXT NOT NULL,
    phase TEXT NOT NULL,
    kind TEXT NOT NULL,
    candidate_id TEXT,
    payload TEXT NOT NULL,
    CHECK (json_valid(payload))
);

CREATE INDEX IF NOT EXISTS events_by_session ON events (session_id, id);
