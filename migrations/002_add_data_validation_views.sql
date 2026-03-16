-- Migration 002: Create views for data quality monitoring
-- These views help identify and track data quality issues

-- View: Records with duplicate national IDs (excluding placeholders)
CREATE VIEW IF NOT EXISTS v_duplicate_national_ids AS
SELECT r.id, r.first_name, r.father_name, r.last_name, r.national_id, r.status
FROM records r
INNER JOIN (
    SELECT national_id, COUNT(*) AS cnt
    FROM records
    WHERE national_id != ''
      AND national_id NOT LIKE '%فلسطيني%'
      AND national_id NOT LIKE '%لا يوجد%'
      AND national_id != 'لايوجد'
    GROUP BY national_id
    HAVING cnt > 1
) dups ON r.national_id = dups.national_id
ORDER BY r.national_id, r.id;

-- View: Records with placeholder/invalid national IDs
CREATE VIEW IF NOT EXISTS v_invalid_national_ids AS
SELECT id, first_name, father_name, last_name, national_id, status
FROM records
WHERE national_id = ''
   OR national_id LIKE '%فلسطيني%'
   OR national_id LIKE '%لا يوجد%'
   OR national_id = 'لايوجد'
ORDER BY national_id, id;

-- View: Records with potentially invalid date fields
CREATE VIEW IF NOT EXISTS v_invalid_dates AS
SELECT id, first_name, last_name,
    CASE WHEN birth_month IS NOT NULL AND birth_month != 0 AND (birth_month < 1 OR birth_month > 12) THEN 'invalid birth_month: ' || birth_month ELSE NULL END AS bad_birth_month,
    CASE WHEN birth_day IS NOT NULL AND birth_day != 0 AND (birth_day < 1 OR birth_day > 31) THEN 'invalid birth_day: ' || birth_day ELSE NULL END AS bad_birth_day,
    CASE WHEN arrest_month IS NOT NULL AND arrest_month != 0 AND (arrest_month < 1 OR arrest_month > 12) THEN 'invalid arrest_month: ' || arrest_month ELSE NULL END AS bad_arrest_month,
    CASE WHEN arrest_day IS NOT NULL AND arrest_day != 0 AND (arrest_day < 1 OR arrest_day > 31) THEN 'invalid arrest_day: ' || arrest_day ELSE NULL END AS bad_arrest_day,
    CASE WHEN birth_year IS NOT NULL AND birth_year != 0 AND birth_year > 2026 THEN 'future birth_year: ' || birth_year ELSE NULL END AS bad_birth_year
FROM records
WHERE (birth_month IS NOT NULL AND birth_month != 0 AND (birth_month < 1 OR birth_month > 12))
   OR (birth_day IS NOT NULL AND birth_day != 0 AND (birth_day < 1 OR birth_day > 31))
   OR (arrest_month IS NOT NULL AND arrest_month != 0 AND (arrest_month < 1 OR arrest_month > 12))
   OR (arrest_day IS NOT NULL AND arrest_day != 0 AND (arrest_day < 1 OR arrest_day > 31))
   OR (birth_year IS NOT NULL AND birth_year != 0 AND birth_year > 2026);

-- View: Records missing critical fields
CREATE VIEW IF NOT EXISTS v_incomplete_records AS
SELECT id, first_name, father_name, last_name, status,
    CASE WHEN phone IS NULL OR phone = '' THEN 1 ELSE 0 END AS missing_phone,
    CASE WHEN province IS NULL OR province = '' THEN 1 ELSE 0 END AS missing_province,
    CASE WHEN birth_year IS NULL OR birth_year = 0 THEN 1 ELSE 0 END AS missing_birth_year,
    CASE WHEN arrest_year IS NULL OR arrest_year = 0 THEN 1 ELSE 0 END AS missing_arrest_year
FROM records
WHERE (phone IS NULL OR phone = '')
   OR (birth_year IS NULL OR birth_year = 0)
   OR (arrest_year IS NULL OR arrest_year = 0);

-- View: Orphaned records check (records referenced in child tables but deleted)
CREATE VIEW IF NOT EXISTS v_orphaned_custom_list_items AS
SELECT cli.id, cli.list_id, cli.record_id
FROM custom_list_items cli
LEFT JOIN records r ON cli.record_id = r.id
LEFT JOIN custom_lists cl ON cli.list_id = cl.id
WHERE r.id IS NULL OR cl.id IS NULL;

-- View: Overall data quality summary
CREATE VIEW IF NOT EXISTS v_data_quality_summary AS
SELECT
    (SELECT COUNT(*) FROM v_duplicate_national_ids) AS duplicate_national_id_records,
    (SELECT COUNT(*) FROM v_invalid_national_ids) AS invalid_national_id_records,
    (SELECT COUNT(*) FROM v_invalid_dates) AS invalid_date_records,
    (SELECT COUNT(*) FROM v_incomplete_records) AS incomplete_records,
    (SELECT COUNT(*) FROM v_orphaned_custom_list_items) AS orphaned_list_items,
    (SELECT COUNT(*) FROM records) AS total_records;
