-- Migration 006: Rebuild members and volunteers tables with proper column ordering
-- These tables grew via ALTER TABLE ADD COLUMN, leaving name fields (first_name,
-- last_name, father_name, mother_name) scattered at the end instead of grouped
-- with the other identity columns.
--
-- New column order groups related fields together:
--   Identity → Contact → Membership → Meta

BEGIN TRANSACTION;

-- ============================================================
-- Rebuild: members
-- ============================================================
CREATE TABLE members_new (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Identity
    first_name        TEXT DEFAULT '',
    father_name       TEXT DEFAULT '',
    last_name         TEXT DEFAULT '',
    mother_name       TEXT DEFAULT '',
    full_name         TEXT NOT NULL,
    gender            TEXT DEFAULT '',
    national_id       TEXT DEFAULT '',
    birth_year        INTEGER DEFAULT 0,
    -- Contact
    phone             TEXT DEFAULT '',
    email             TEXT DEFAULT '',
    province          TEXT DEFAULT '',
    address           TEXT DEFAULT '',
    -- Membership
    membership_type   TEXT DEFAULT '',
    membership_number TEXT DEFAULT '',
    join_date         TEXT DEFAULT '',
    status            TEXT DEFAULT 'active',
    notes             TEXT DEFAULT '',
    -- Meta
    created_at        TEXT DEFAULT (datetime('now','localtime')),
    updated_at        TEXT DEFAULT (datetime('now','localtime'))
);

INSERT INTO members_new
    (id, first_name, father_name, last_name, mother_name,
     full_name, gender, national_id, birth_year,
     phone, email, province, address,
     membership_type, membership_number, join_date, status, notes,
     created_at, updated_at)
SELECT
    id, first_name, father_name, last_name, mother_name,
    full_name, gender, national_id, birth_year,
    phone, email, province, address,
    membership_type, membership_number, join_date, status, notes,
    created_at, updated_at
FROM members;

DROP TABLE members;
ALTER TABLE members_new RENAME TO members;

-- Recreate indexes for members
CREATE INDEX idx_members_full_name ON members(full_name);
CREATE INDEX idx_members_status    ON members(status);

-- ============================================================
-- Rebuild: volunteers
-- ============================================================
CREATE TABLE volunteers_new (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Identity
    first_name       TEXT DEFAULT '',
    father_name      TEXT DEFAULT '',
    last_name        TEXT DEFAULT '',
    mother_name      TEXT DEFAULT '',
    full_name        TEXT NOT NULL,
    national_id      TEXT DEFAULT '',
    -- Contact
    phone            TEXT DEFAULT '',
    email            TEXT DEFAULT '',
    province         TEXT DEFAULT '',
    address          TEXT DEFAULT '',
    -- Role
    role             TEXT DEFAULT '',
    specialization   TEXT DEFAULT '',
    join_date        TEXT DEFAULT '',
    status           TEXT DEFAULT 'active',
    notes            TEXT DEFAULT '',
    -- Meta
    created_at       TEXT DEFAULT (datetime('now','localtime')),
    updated_at       TEXT DEFAULT (datetime('now','localtime'))
);

INSERT INTO volunteers_new
    (id, first_name, father_name, last_name, mother_name,
     full_name, national_id,
     phone, email, province, address,
     role, specialization, join_date, status, notes,
     created_at, updated_at)
SELECT
    id, first_name, father_name, last_name, mother_name,
    full_name, national_id,
    phone, email, province, address,
    role, specialization, join_date, status, notes,
    created_at, updated_at
FROM volunteers;

DROP TABLE volunteers;
ALTER TABLE volunteers_new RENAME TO volunteers;

-- Recreate indexes for volunteers
CREATE INDEX idx_volunteers_full_name ON volunteers(full_name);
CREATE INDEX idx_volunteers_status    ON volunteers(status);

COMMIT;
