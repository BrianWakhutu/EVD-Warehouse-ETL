-- Gold: signal counts per county, per signal type, per day.
-- This is the first data mart — the shape a dashboard/API actually wants,
-- not a raw table. Any future API layer should query gold (or silver, for
-- record-level reads), never bronze.

CREATE SCHEMA IF NOT EXISTS gold;

DROP TABLE IF EXISTS gold.county_signal_daily_counts;

CREATE TABLE gold.county_signal_daily_counts AS
SELECT
    county,
    signal_type,
    date_trunc('day', reported_at)::date AS report_date,
    count(*)                             AS signal_count
FROM silver.signals
GROUP BY county, signal_type, report_date
ORDER BY report_date, county, signal_type;
