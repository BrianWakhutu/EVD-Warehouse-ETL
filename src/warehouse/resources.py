"""Postgres connection resource for the plain-SQL silver/gold assets.

Bronze tables are written by dlt (see bronze/<source>/assets.py), which
manages its own Postgres connection from .dlt/secrets.toml. This resource is
separate and is only for silver/gold assets, which are plain Python + SQL:
each asset reads a .sql file sitting next to it and runs it against this
connection. There's no dbt, no migration framework — a silver/gold model is
just a `CREATE TABLE ... AS SELECT ...` that fully rebuilds its table each
run. That's enough for this project's scale; revisit (incremental models,
dbt) only if full-rebuild runtimes actually become a problem.
"""

import dagster as dg
import psycopg2


class PostgresResource(dg.ConfigurableResource):
    host: str
    port: int
    database: str
    username: str
    password: str

    def execute(self, sql: str) -> None:
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.username,
            password=self.password,
        )
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
        finally:
            conn.close()
