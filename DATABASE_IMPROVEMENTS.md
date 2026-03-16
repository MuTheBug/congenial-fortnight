# Database Improvements and Fixes

## Issues Found

### 1. Missing Indexes on Foreign Key Columns (Performance)
The following foreign key columns lacked indexes, causing slow JOINs and lookups:
- `custom_list_items.record_id`
- `record_services.record_id`
- `record_companions.record_id` and `linked_record_id`
- `volunteer_attendance.volunteer_id`
- `volunteer_activity_participants.activity_id` and `volunteer_id`
- `custom_list_manual_items.list_id`

**Fix:** Migration `001_add_missing_indexes.sql` adds all missing indexes.

### 2. No Data Validation / Integrity Enforcement
- No triggers to prevent invalid date values (month > 12, day > 31, future birth years)
- No protection against duplicate national IDs
- `updated_at` columns on `members` and `volunteers` not auto-updated

**Fix:** Migration `003_add_triggers_and_constraints.sql` adds validation triggers.

### 3. Foreign Keys Disabled
SQLite's `PRAGMA foreign_keys` was OFF, meaning foreign key constraints were not enforced at all. Orphaned records could be created.

**Fix:** Migration `004_enable_foreign_keys.sql` documents the requirement. The application must run `PRAGMA foreign_keys = ON` on every new connection.

### 4. Data Quality Issues
- **12 duplicate national IDs** (valid numeric IDs appearing on 2 records each)
- **~22 records** with placeholder/invalid national IDs (Arabic text like "فلسطيني", "لا يوجد")
- **Records with missing phone numbers** (NULL values)

**Fix:** Migration `002_add_data_validation_views.sql` creates monitoring views:
- `v_duplicate_national_ids` — find duplicate IDs
- `v_invalid_national_ids` — find placeholder/invalid IDs
- `v_invalid_dates` — find records with bad date values
- `v_incomplete_records` — find records missing critical fields
- `v_orphaned_custom_list_items` — find orphaned references
- `v_data_quality_summary` — one-row overview of all issues

### 5. No Migration Tracking
No system existed to track which schema changes had been applied.

**Fix:** `apply_migrations.py` creates a `_migrations` table and tracks applied migrations.

## How to Apply

```bash
# Back up the database first!
cp registry.db registry.db.backup

# Run all migrations
python3 migrations/apply_migrations.py
```

## Recommendations for Future Work
1. **Normalize date columns** — Consider storing dates as ISO 8601 TEXT (`YYYY-MM-DD`) instead of separate day/month/year integers
2. **Normalize structured data** — `children_data`, `witnesses_data`, `detention_facilities_data` contain serialized text; consider extracting into proper related tables
3. **Add application-level validation** — Ensure `PRAGMA foreign_keys = ON` is set on every database connection
4. **Clean up duplicate national IDs** — Use `v_duplicate_national_ids` to review and merge/fix the 12 duplicate pairs
5. **Add CHECK constraints** — For enum-like fields (`status`, `gender`, `verification_status`) when creating new tables
