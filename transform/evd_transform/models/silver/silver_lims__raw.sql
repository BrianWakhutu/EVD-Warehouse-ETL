-- Placeholder passthrough until real LIMS columns are known (run
-- `make explore SOURCE=lims` against live data first). Replace with explicit
-- casts/dedup once the actual bronze.lims_raw column set is visible — do not
-- leave `select *` in place long-term.
select *
from {{ source('bronze', 'lims_raw') }}
