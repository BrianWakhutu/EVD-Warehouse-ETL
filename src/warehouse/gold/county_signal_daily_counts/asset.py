"""Gold layer: daily signal counts by county — the first data mart.

Aggregates silver.signals into gold.county_signal_daily_counts. Add new
marts as sibling folders (asset.py + transform.sql) the same way — each
mart is independent and can depend on whichever silver model(s) it needs.
"""

from pathlib import Path

import dagster as dg

from warehouse.resources import PostgresResource

SQL = (Path(__file__).parent / "transform.sql").read_text()


@dg.asset(deps=["signals"], group_name="gold")
def county_signal_daily_counts(postgres: PostgresResource) -> None:
    postgres.execute(SQL)
