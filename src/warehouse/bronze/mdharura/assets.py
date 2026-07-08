"""Bronze layer: land raw mdharura signal records from MinIO into Postgres.

Reads the `.jsonl.gz` files the sibling ingestion repo
(evd-surveillance-scripts) writes to `s3://evd/mdharura_raw/signals/`, and
loads them as-is — one row per record, no reshaping — into Postgres schema
`bronze`, table `mdharura_signals`. This is a straight copy of what's
already in MinIO; it exists so silver/gold can query with SQL instead of
re-reading object storage on every transform. No typing, joins, or PII
handling happens here — that's the silver layer's job (see
../../silver/signals/).

Credentials (MinIO read access + Postgres write access) come from
.dlt/secrets.toml locally, or the equivalent env vars in deployment:
    SOURCES__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID
    SOURCES__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY
    SOURCES__FILESYSTEM__CREDENTIALS__ENDPOINT_URL
    DESTINATION__POSTGRES__CREDENTIALS__*

The MinIO access key should be a scoped, read-only-in-practice service user
for this one source's prefix (e.g. `mdharura-svc`, created in the ingestion
repo's MinIO setup) — never the MinIO root user.
"""

import dlt
from dagster import AssetExecutionContext
from dagster_dlt import DagsterDltResource, dlt_assets
from dlt.sources.filesystem import filesystem, read_jsonl

source = (
    filesystem(bucket_url="s3://evd/mdharura_raw/signals", file_glob="*.jsonl.gz")
    | read_jsonl()
).with_name("mdharura_signals")

pipeline = dlt.pipeline(
    pipeline_name="mdharura_bronze",
    destination="postgres",
    dataset_name="bronze",
)


@dlt_assets(dlt_source=source, dlt_pipeline=pipeline, name="mdharura_bronze")
def mdharura_bronze_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)
