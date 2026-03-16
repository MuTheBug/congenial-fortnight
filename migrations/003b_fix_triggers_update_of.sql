-- Migration 003b: Fix triggers to use UPDATE OF syntax
-- The original triggers in 003 fired on ALL updates to the records table,
-- blocking unrelated column updates (e.g. updating has_kids on a row that
-- happens to have an invalid birth_year). This migration drops and recreates
-- the date-validation triggers so they only fire when the specific date
-- columns are modified.

-- Drop the old broad-scope triggers
DROP TRIGGER IF EXISTS trg_records_validate_birth_insert;
DROP TRIGGER IF EXISTS trg_records_validate_birth_update;
DROP TRIGGER IF EXISTS trg_records_validate_arrest_insert;
DROP TRIGGER IF EXISTS trg_records_validate_arrest_update;

-- Birth date validation on INSERT
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

-- Birth date validation on UPDATE — only fires when date columns change
CREATE TRIGGER IF NOT EXISTS trg_records_validate_birth_update
BEFORE UPDATE OF birth_day, birth_month, birth_year ON records
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

-- Arrest date validation on INSERT
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

-- Arrest date validation on UPDATE — only fires when date columns change
CREATE TRIGGER IF NOT EXISTS trg_records_validate_arrest_update
BEFORE UPDATE OF arrest_day, arrest_month, arrest_year ON records
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

-- Also fix the invalid birth_year=19749 (clearly a typo, set to NULL for review)
-- The correct year is ambiguous (1974? 1949?) so NULL is safer than guessing.
UPDATE records SET birth_year = NULL WHERE birth_year = 19749;
