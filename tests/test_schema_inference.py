from evd_orchestration.assets.bronze.schema_inference import (
    canonical_hash,
    diff_new_columns,
    flatten_record,
    infer_pg_type,
    sanitize_column_name,
)

LIMS_RECORD = {
    "specimenId": "SPEC-001",
    "patient": {
        "id": "PAT-42",
        "address": {"city": "Nairobi", "county": "Nairobi"},
    },
    "collectedAt": "2026-07-01T08:00:00Z",
    "results": [
        {"analyte": "HIV", "value": "Positive", "abnormal": True},
        {"analyte": "CD4", "value": "512", "abnormal": False},
    ],
    "notes": None,
}


def test_flatten_record_dot_paths_and_array_indices():
    flat = flatten_record(LIMS_RECORD)

    assert flat["specimenId"] == "SPEC-001"  # flatten_record does not sanitize keys
    assert flat["patient__id"] == "PAT-42"
    assert flat["patient__address__city"] == "Nairobi"
    assert flat["results__0__analyte"] == "HIV"
    assert flat["results__0__abnormal"] is True
    assert flat["results__1__value"] == "512"
    assert flat["notes"] is None


def test_flatten_record_depth_cap_collapses_to_json_text():
    nested = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "too_deep"}}}}}}}
    flat = flatten_record(nested, max_depth=3)
    # past max_depth, remainder collapses to a single JSON-string leaf
    assert isinstance(flat["a__b__c__d"], str)
    assert "too_deep" in flat["a__b__c__d"]


def test_flatten_record_empty_dict_and_list_become_none():
    flat = flatten_record({"empty_obj": {}, "empty_list": []})
    assert flat["empty_obj"] is None
    assert flat["empty_list"] is None


def test_sanitize_column_name_basic():
    assert sanitize_column_name("patient__address__city") == "patient__address__city"
    assert sanitize_column_name("Patient.Address.City") == "patient_address_city"


def test_sanitize_column_name_strips_leading_underscore_reserved_for_envelope():
    assert sanitize_column_name("_raw_hash") == "raw_hash"


def test_sanitize_column_name_leading_digit_gets_prefixed():
    assert sanitize_column_name("123abc") == "_123abc"


def test_sanitize_column_name_truncates_long_names_uniquely():
    long_path = "a" * 100
    other_long_path = "a" * 99 + "b"
    name1 = sanitize_column_name(long_path)
    name2 = sanitize_column_name(other_long_path)
    assert len(name1) <= 63
    assert len(name2) <= 63
    assert name1 != name2


def test_infer_pg_type_boolean_vs_text():
    assert infer_pg_type(True) == "boolean"
    assert infer_pg_type(False) == "boolean"
    assert infer_pg_type("Positive") == "text"
    assert infer_pg_type(512) == "text"
    assert infer_pg_type(None) == "text"


def test_canonical_hash_stable_and_sensitive_to_change():
    record_a = {"x": 1, "y": {"z": 2}}
    record_b = {"y": {"z": 2}, "x": 1}  # same content, different key order
    record_c = {"x": 1, "y": {"z": 3}}

    assert canonical_hash(record_a) == canonical_hash(record_b)
    assert canonical_hash(record_a) != canonical_hash(record_c)


def test_diff_new_columns_is_additive_only():
    existing = {"a": "text", "b": "boolean"}
    required = {"a": "text", "c": "text"}
    assert diff_new_columns(existing, required) == {"c": "text"}
