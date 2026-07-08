# evd_warehouse

A [Dagster](https://docs.dagster.io/) project that turns the raw JSON landed in MinIO by [`evd-surveillance-scripts`](../EVD-Surveillance-scripts-v1) into structured, queryable data marts in Postgres — the bronze → silver → gold layer of the EVD surveillance platform. This repo is deliberately separate from the ingestion repo: MinIO is the handoff point between them, and this side only ever *reads* from MinIO, never writes to it.

```
MinIO (bronze, raw JSON)  →  Postgres: bronze  →  Postgres: silver  →  Postgres: gold  →  (future) APIs
      evd-surveillance-scripts        this repo (typed, de-identified)   (marts)
```

See [AGENTS.md](AGENTS.md) for the full rationale and conventions — read that before adding a source or a model, it's written for a future Claude session (or human) picking this up cold.

## The three layers

| Layer | Schema | What it holds | How it's built |
| --- | --- | --- | --- |
| Bronze | `bronze` | Raw records, copied as-is from MinIO | `dlt` — one filesystem→Postgres pipeline per source, under `src/warehouse/bronze/<source>/` |
| Silver | `silver` | Typed, joined, **de-identified** tables | Plain SQL — one model per table, under `src/warehouse/silver/<model>/` |
| Gold | `gold` | Data marts — the shape dashboards/APIs actually want | Plain SQL — one model per mart, under `src/warehouse/gold/<mart>/` |

No dbt here — silver/gold models are plain `asset.py` + `transform.sql` pairs, each asset just executing its SQL file against Postgres. See AGENTS.md for why, and for the convention every new model should follow.

`mdharura` is the reference implementation for all three layers — copy its shape (`bronze/mdharura/`, `silver/signals/`, `gold/county_signal_daily_counts/`) when adding a new source or model.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python ≥ 3.10.

```bash
git clone <this-repo> && cd evd-warehouse
uv sync
```

Start a local Postgres:

```bash
cp .env.example .env
docker compose up -d
```

Configure MinIO read access + Postgres write access:

```bash
cp .dlt/secrets.example.toml .dlt/secrets.toml
# edit: MinIO access key (a scoped source-specific user, e.g. mdharura-svc,
# from the ingestion repo's MinIO setup) + endpoint_url, and the Postgres
# password (matches .env if using the local docker-compose Postgres)
```

Run it:

```bash
dg dev                                          # Dagster UI at http://localhost:3000
dg list defs                                    # list all assets
dg launch --assets "mdharura_bronze"            # bronze: MinIO -> Postgres
dg launch --assets "signals"                    # silver: type + de-identify
dg launch --assets "county_signal_daily_counts" # gold: the first mart
```

Verify against Postgres directly:

```bash
docker exec -it evd-warehouse-postgres psql -U postgres -d evd_warehouse \
  -c "select * from gold.county_signal_daily_counts limit 10;"
```

## Adding a new source (bronze)

1. `mkdir -p src/warehouse/bronze/<source>` and copy the shape of `bronze/mdharura/assets.py` — swap the `bucket_url` for that source's MinIO prefix (matches its `dataset_name` in the ingestion repo, e.g. `s3://evd/<source>_raw/<resource>`), and the `pipeline_name`/`dataset_name`.
2. Use that source's own scoped MinIO credentials (see the ingestion repo's multi-source MinIO setup) — never the MinIO root user, and never another source's credentials.
3. Import the new `@dlt_assets`-decorated function in `definitions.py` and add it to the `assets` list.
4. `dg check defs`, then `dg launch --assets "<pipeline_name>"` to verify.

## Adding a new silver or gold model

1. `mkdir -p src/warehouse/silver/<model>` (or `gold/<mart>`).
2. Write `transform.sql` — a `CREATE SCHEMA IF NOT EXISTS ...` + `DROP TABLE IF EXISTS ...` + `CREATE TABLE ... AS SELECT ...`, full-rebuild style (see `silver/signals/transform.sql` for the pattern, including the PII de-identification convention — read it before writing a silver model with any potentially-identifying column).
3. Write `asset.py` — a `@dg.asset` that reads `transform.sql` and calls `postgres.execute(SQL)`, with `deps=[...]` pointing at whatever upstream table(s) it reads.
4. Import it in `definitions.py`, add it to the `assets` list.

## Documentation

- [AGENTS.md](AGENTS.md) — why this repo exists, why plain SQL instead of dbt, the PII de-identification rule, and conventions for adding sources/models. Read this first.
- [evd-surveillance-scripts/docs](../EVD-Surveillance-scripts-v1/docs/) — the ingestion side: how sources land in MinIO, the multi-source MinIO credential/prefix scheme this repo's bronze layer depends on.
