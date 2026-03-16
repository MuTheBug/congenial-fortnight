-- Migration 003: Add triggers for data integrity enforcement
-- SQLite doesn't support ALTER TABLE ADD CONSTRAINT, so we use triggers

-- Trigger: Validate birth date fields on INSERT
CREATE TRIGGER IF NOT EXISTS trg_records_validate_birth_insert
BEFORE INSERT ON records
BEGIN
    SELECT CASE
        WHEN NEW.birth_month IS NOT NULL AND NEW.birth_month != 0 AND (NEW.birth_month < 1 OR NEW.birth_month > 12)
        THEN RAISE(ABORT, 'birth_month must be between 1 and 12')
    END;
    SELECT CASE
        WHEN NEW.birth_day IS NOT NULL AND NEW.birth_day != 0 AND (NEW.birth_day < 1 OR NEW.birth_day > 31)
        THEN RAISE(ABORT, 'birth_day must be between 1 and 31')
    END;
    SELECT CASE
        WHEN NEW.birth_year IS NOT NULL AND NEW.birth_year != 0 AND NEW.birth_year > 2026
        THEN RAISE(ABORT, 'birth_year cannot be in the future')
    END;
END;

-- Trigger: Validate birth date fields on UPDATE
CREATE TRIGGER IF NOT EXISTS trg_records_validate_birth_update
BEFORE UPDATE ON records
BEGIN
    SELECT CASE
        WHEN NEW.birth_month IS NOT NULL AND NEW.birth_month != 0 AND (NEW.birth_month < 1 OR NEW.birth_month > 12)
        THEN RAISE(ABORT, 'birth_month must be between 1 and 12')
    END;
    SELECT CASE
        WHEN NEW.birth_day IS NOT NULL AND NEW.birth_day != 0 AND (NEW.birth_day < 1 OR NEW.birth_day > 31)
        THEN RAISE(ABORT, 'birth_day must be between 1 and 31')
    END;
    SELECT CASE
        WHEN NEW.birth_year IS NOT NULL AND NEW.birth_year != 0 AND NEW.birth_year > 2026
        THEN RAISE(ABORT, 'birth_year cannot be in the future')
    END;
END;

-- Trigger: Validate arrest date fields on INSERT
CREATE TRIGGER IF NOT EXISTS trg_records_validate_arrest_insert
BEFORE INSERT ON records
BEGIN
    SELECT CASE
        WHEN NEW.arrest_month IS NOT NULL AND NEW.arrest_month != 0 AND (NEW.arrest_month < 1 OR NEW.arrest_month > 12)
        THEN RAISE(ABORT, 'arrest_month must be between 1 and 12')
    END;
    SELECT CASE
        WHEN NEW.arrest_day IS NOT NULL AND NEW.arrest_day != 0 AND (NEW.arrest_day < 1 OR NEW.arrest_day > 31)
        THEN RAISE(ABORT, 'arrest_day must be between 1 and 31')
    END;
END;

-- Trigger: Validate arrest date fields on UPDATE
CREATE TRIGGER IF NOT EXISTS trg_records_validate_arrest_update
BEFORE UPDATE ON records
BEGIN
    SELECT CASE
        WHEN NEW.arrest_month IS NOT NULL AND NEW.arrest_month != 0 AND (NEW.arrest_month < 1 OR NEW.arrest_month > 12)
        THEN RAISE(ABORT, 'arrest_month must be between 1 and 12')
    END;
    SELECT CASE
        WHEN NEW.arrest_day IS NOT NULL AND NEW.arrest_day != 0 AND (NEW.arrest_day < 1 OR NEW.arrest_day > 31)
        THEN RAISE(ABORT, 'arrest_day must be between 1 and 31')
    END;
END;

-- Trigger: Auto-update updated_at on members table
CREATE TRIGGER IF NOT EXISTS trg_members_updated_at
AFTER UPDATE ON members
BEGIN
    UPDATE members SET updated_at = datetime('now','localtime') WHERE id = NEW.id;
END;

-- Trigger: Auto-update updated_at on volunteers table
CREATE TRIGGER IF NOT EXISTS trg_volunteers_updated_at
AFTER UPDATE ON volunteers
BEGIN
    UPDATE volunteers SET updated_at = datetime('now','localtime') WHERE id = NEW.id;
END;

-- Trigger: Prevent duplicate national_id on INSERT (for valid IDs only)
CREATE TRIGGER IF NOT EXISTS trg_records_unique_national_id_insert
BEFORE INSERT ON records
WHEN NEW.national_id != ''
  AND NEW.national_id NOT LIKE '%فلسطيني%'
  AND NEW.national_id NOT LIKE '%لا يوجد%'
  AND NEW.national_id != 'لايوجد'
BEGIN
    SELECT CASE
        WHEN (SELECT COUNT(*) FROM records WHERE national_id = NEW.national_id) > 0
        THEN RAISE(ABORT, 'A record with this national_id already exists')
    END;
END;
