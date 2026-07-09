select
    cast("Code" as integer)          as facility_key,
    "Code"                           as mfl_code,
    trim("Facility Name")            as facility_name,
    trim("Province")                 as province,
    trim("County")                   as county,
    trim("Sub County")               as sub_county,
    trim("Ward")                     as ward,
    current_timestamp                as loaded_at

from {{ ref('facility_list_dump_20260528') }}