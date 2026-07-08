from dagster import AssetSelection, define_asset_job

from evd_orchestration.assets import evd_dbt_assets

ingest_job = define_asset_job(
    name="ingest_job",
    description="Load all sending systems from MinIO into bronze tables.",
    selection=AssetSelection.assets(
        "bronze_lims_raw",
    ),
)

dbt_job = define_asset_job(
    name="dbt_job",
    description="Run dbt build — silver, gold, and tests.",
    selection=AssetSelection.assets(evd_dbt_assets),
)
