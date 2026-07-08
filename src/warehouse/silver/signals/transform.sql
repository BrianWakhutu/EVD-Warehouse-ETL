-- Silver: typed + de-identified signals, rebuilt from bronze.mdharura_signals.
--
-- PII CONVENTION (read this before adding a new silver model): any column
-- that could identify an individual — reporter name, phone number, patient
-- identifier, precise geolocation, free-text notes — must be hashed,
-- masked, or dropped in *this* query, before the row ever lands in silver.
-- Gold marts and any future API only ever read from silver/gold, never
-- bronze, so de-identifying once here is what makes that guarantee hold.
-- Example pattern for a future source that does carry PII:
--   encode(digest(reporter_phone, 'sha256'), 'hex') AS reporter_id_hash
--
-- mdharura's currently-captured fields (signal type, geography, timestamp)
-- contain no direct identifiers, so nothing is hashed below yet.
--
-- NOTE: column names below assume dlt's default normalization of the JSON
-- fields written by the ingestion repo's loader.py (id, signal,
-- community_unit, subcounty, county, created_at). Verify against the
-- actual bronze.mdharura_signals schema (`\d bronze.mdharura_signals` in
-- psql) before the first run — dlt may have normalized names slightly
-- differently than expected.

CREATE SCHEMA IF NOT EXISTS silver;

DROP TABLE IF EXISTS silver.signals;

CREATE TABLE silver.signals AS
SELECT
    _dlt_id                            AS row_id,
    id::text                           AS signal_id,
    signal::text                       AS signal_type,
    community_unit::text               AS community_unit,
    subcounty::text                    AS subcounty,
    county::text                       AS county,
    created_at::timestamptz            AS reported_at
FROM bronze.mdharura_signals;
