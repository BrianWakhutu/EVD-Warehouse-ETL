"""Wires bronze/silver/gold assets and resources together.

Unlike the ingestion repo (evd-surveillance-scripts), sources here are NOT
autoloaded through a component system — silver/gold were deliberately kept
as plain Python + SQL (see AGENTS.md for why), so each new asset must be
imported and added to the lists below by hand. Adding a source/model means:
1. Add the new module under bronze/, silver/, or gold/.
2. Import it here.
3. Add it to the `assets` list.
"""

import dagster as dg
from dagster_dlt import DagsterDltResource

from warehouse.bronze.mdharura.assets import mdharura_bronze_assets
from warehouse.gold.county_signal_daily_counts.asset import county_signal_daily_counts
from warehouse.resources import PostgresResource
from warehouse.silver.signals.asset import signals

postgres_resource = PostgresResource(
    host=dg.EnvVar("POSTGRES_HOST"),
    port=dg.EnvVar.int("POSTGRES_PORT"),
    database=dg.EnvVar("POSTGRES_DB"),
    username=dg.EnvVar("POSTGRES_USER"),
    password=dg.EnvVar("POSTGRES_PASSWORD"),
)

defs = dg.Definitions(
    assets=[
        mdharura_bronze_assets,
        signals,
        county_signal_daily_counts,
    ],
    resources={
        "dlt": DagsterDltResource(),
        "postgres": postgres_resource,
    },
)
