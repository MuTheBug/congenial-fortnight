-- Migration 008: Add record_photos table for multiple evidence photos
-- Personal photo and ID document use existing records.photo_path / document_path.
-- Evidence photos (one or many) use this table.

CREATE TABLE IF NOT EXISTS record_photos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id     INTEGER NOT NULL,
    photo_type    TEXT    NOT NULL DEFAULT 'evidence',  -- 'personal' | 'id_doc' | 'evidence'
    filename      TEXT    NOT NULL,                     -- relative path under uploads/
    original_name TEXT    DEFAULT '',
    caption       TEXT    DEFAULT '',
    uploaded_at   TEXT    DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_record_photos_record_id ON record_photos(record_id);
CREATE INDEX IF NOT EXISTS idx_record_photos_type      ON record_photos(record_id, photo_type);
