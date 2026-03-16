-- Migration 001: Add missing indexes on foreign key columns
-- These indexes improve JOIN and lookup performance on related tables

-- custom_list_items: already has idx_custom_list_items_list_id, but missing record_id index
CREATE INDEX IF NOT EXISTS idx_custom_list_items_record_id ON custom_list_items(record_id);

-- record_services: missing index on record_id (foreign key)
CREATE INDEX IF NOT EXISTS idx_record_services_record_id ON record_services(record_id);

-- record_companions: missing indexes on both foreign keys
CREATE INDEX IF NOT EXISTS idx_record_companions_record_id ON record_companions(record_id);
CREATE INDEX IF NOT EXISTS idx_record_companions_linked_record_id ON record_companions(linked_record_id);

-- volunteer_attendance: missing index on volunteer_id (foreign key)
CREATE INDEX IF NOT EXISTS idx_volunteer_attendance_volunteer_id ON volunteer_attendance(volunteer_id);

-- volunteer_activity_participants: missing indexes on both foreign keys
CREATE INDEX IF NOT EXISTS idx_volunteer_activity_participants_activity_id ON volunteer_activity_participants(activity_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_activity_participants_volunteer_id ON volunteer_activity_participants(volunteer_id);

-- custom_list_manual_items: missing index on list_id (foreign key)
CREATE INDEX IF NOT EXISTS idx_custom_list_manual_items_list_id ON custom_list_manual_items(list_id);

-- record_services: useful composite index for querying services by record and date
CREATE INDEX IF NOT EXISTS idx_record_services_record_date ON record_services(record_id, service_date);

-- volunteer_attendance: useful composite index for querying attendance by volunteer and date
CREATE INDEX IF NOT EXISTS idx_volunteer_attendance_volunteer_date ON volunteer_attendance(volunteer_id, date);
