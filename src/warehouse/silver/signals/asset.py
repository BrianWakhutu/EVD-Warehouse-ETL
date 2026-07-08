"""Silver layer: typed, de-identified signals table.

Rebuilds silver.signals from bronze.mdharura_signals on every run (see
transform.sql for the query and the PII de-identification convention).
Depends on the bronze dlt asset so it never runs against a stale/partial
load.
"""

from pathlib import Path

import dagster as dg

from warehouse.resources import PostgresResource

SQL = (Path(__file__).parent / "transform.sql").read_text()


@dg.asset(
    deps=[dg.AssetKey(["mdharura_signals"])],
    group_name="silver",
)
def signals(postgres: PostgresResource) -> None:
    postgres.execute(SQL)
