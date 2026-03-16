-- Migration 007: Create organized views for the records table
-- The records table has 113 columns added over time in a disorganized order.
-- These views present columns in logical sections for easier querying.

-- ============================================================
-- v_records_identity — who is this person?
-- ============================================================
CREATE VIEW IF NOT EXISTS v_records_identity AS
SELECT
    id,
    record_status,
    record_slug,
    -- Name
    first_name,
    father_name,
    last_name,
    mother_name,
    -- Identity documents
    national_id,
    family_book_number,
    -- Demographics
    gender,
    birth_day,
    birth_month,
    birth_year,
    blood_type,
    -- Contact
    phone,
    province,
    address,
    housing_type,
    rent_amount,
    -- Media
    photo_path,
    photo_hash,
    document_path,
    document_hash
FROM records;

-- ============================================================
-- v_records_case — what happened to this person?
-- ============================================================
CREATE VIEW IF NOT EXISTS v_records_case AS
SELECT
    id,
    first_name,
    father_name,
    last_name,
    -- Case classification
    status,
    case_type,
    cause_number,
    -- Arrest
    arrest_day,
    arrest_month,
    arrest_year,
    arrest_place,
    arrest_authority,
    arrest_reason,
    arrest_causer,
    -- Release
    release_day,
    release_month,
    release_year,
    -- Death
    death_day,
    death_month,
    death_year,
    death_place,
    -- Detention
    detention_facilities_data,
    last_known_alive_date,
    last_known_location,
    -- Official registration
    is_officially_registered,
    civil_registry_status,
    civil_registry_date,
    civil_registry_document_path
FROM records;

-- ============================================================
-- v_records_family — family and dependents
-- ============================================================
CREATE VIEW IF NOT EXISTS v_records_family AS
SELECT
    id,
    first_name,
    father_name,
    last_name,
    -- Current family
    marital,
    spouse_name,
    spouse_phone,
    has_kids,
    kids_count,
    children_data,
    kids_under_18_count,
    -- Previous family
    ex_spouse_name,
    has_kids_w,
    kids_count_w,
    children_data_w,
    -- Guardian
    guardian_name,
    guardian_relation,
    guardian_phone,
    -- Financial
    breadwinner,
    breadwinner_job,
    breadwinner_relation,
    breadwinner_relation_other
FROM records;

-- ============================================================
-- v_records_background — socioeconomic profile
-- ============================================================
CREATE VIEW IF NOT EXISTS v_records_background AS
SELECT
    id,
    first_name,
    father_name,
    last_name,
    -- Education
    education,
    edu_type,
    edu_specialization,
    edu_university,
    -- Employment
    employment,
    profession,
    employer,
    -- Health
    blood_type,
    chronic,
    diseases,
    has_hypertension,
    has_diabetes,
    other_diseases,
    has_special_needs,
    special_needs_details,
    -- Legal
    legal,
    legal_details,
    assoc,
    assoc_name,
    service_type
FROM records;

-- ============================================================
-- v_records_evidence — documentation and source material
-- ============================================================
CREATE VIEW IF NOT EXISTS v_records_evidence AS
SELECT
    id,
    first_name,
    father_name,
    last_name,
    -- Source info
    source_type,
    source_url,
    collection_date,
    collector_name,
    -- Verification
    verification_status,
    evidence_level,
    evidence_sources_count,
    methodology_notes,
    has_conflicting_info,
    conflicting_info_details,
    -- Reporter
    reporter_name,
    reporter_relation,
    reporter_phone,
    reporter_id,
    informant_consent,
    -- Witnesses
    witnesses_data,
    -- Digital evidence
    digital_evidence_type,
    digital_evidence_url,
    digital_evidence_url_status,
    digital_evidence_screenshot_path,
    digital_evidence_date,
    digital_evidence_description,
    digital_evidence_person_name,
    digital_evidence_death_date,
    -- Survivor documentation
    survivor_cv_path,
    survivor_cv_text,
    survivor_cv_photo_path
FROM records;

-- ============================================================
-- v_records_summary — one-line overview per record (most common query)
-- ============================================================
CREATE VIEW IF NOT EXISTS v_records_summary AS
SELECT
    r.id,
    r.record_status,
    r.first_name || ' ' || r.father_name || ' ' || r.last_name AS full_name,
    r.gender,
    r.birth_year,
    r.national_id,
    r.province,
    r.phone,
    r.status,
    r.case_type,
    r.arrest_year,
    r.verification_status,
    r.evidence_level,
    r.created_at,
    -- Computed: approximate age at arrest
    CASE
        WHEN r.arrest_year > 0 AND r.birth_year > 1900
        THEN r.arrest_year - r.birth_year
        ELSE NULL
    END AS age_at_arrest,
    -- Computed: full arrest date as text
    CASE
        WHEN r.arrest_year > 0
        THEN printf('%04d-%02d-%02d', r.arrest_year,
                    COALESCE(NULLIF(r.arrest_month, 0), 1),
                    COALESCE(NULLIF(r.arrest_day, 0), 1))
        ELSE NULL
    END AS arrest_date,
    -- Computed: full birth date as text
    CASE
        WHEN r.birth_year > 1900
        THEN printf('%04d-%02d-%02d', r.birth_year,
                    COALESCE(NULLIF(r.birth_month, 0), 1),
                    COALESCE(NULLIF(r.birth_day, 0), 1))
        ELSE NULL
    END AS birth_date
FROM records r;
