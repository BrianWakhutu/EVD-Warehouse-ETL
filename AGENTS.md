# Agent instructions for this repository

Read this before touching anything here — it explains *why* this repo exists and why several choices were made deliberately, so they don't get accidentally reversed by a future session that doesn't have this context.

## What this repo is

`evd_warehouse` is the transform layer of the EVD surveillance platform, sitting downstream of a separate repo, **`evd-surveillance-scripts`** (expected as a sibling directory, `../EVD-Surveillance-scripts-v1`), which pulls from source APIs (m-Dharura and others over time) and lands raw JSON in a shared MinIO bucket (`s3://evd/`), one prefix per source.

This repo does **not** talk to any source API and **never writes to MinIO** — it only reads from it. Its job is bronze → silver → gold:

```
MinIO (bronze, raw JSON)  →  Postgres: bronze  →  Postgres: silver  →  Postgres: gold  →  (future) APIs
      evd-surveillance-scripts        this repo (typed, de-identified)   (marts)
```

**Why a separate repo instead of adding this to evd-surveillance-scripts:** that repo's whole design (see its own AGENTS.md) is scoped to ingestion — MinIO is the intentional decoupling point between however many independent sources push data and whatever consumes it. This repo is one consumer of that shared bucket, with its own lifecycle, its own database, and eventually its own API layer. Keeping it separate means the ingestion repo's scope never has to grow to accommodate transform/warehouse concerns.

## The three layers, and the rules that go with each

- **Bronze** (Postgres schema `bronze`) — raw records, copied from MinIO with no reshaping. One `dlt` pipeline per source, under `src/warehouse/bronze/<source>/`. If it's in MinIO, it should be a straight copy in bronze — no filtering, no typing, no joins.
- **Silver** (Postgres schema `silver`) — typed, joined, and **de-identified**. This is the only layer allowed to read bronze directly.
- **Gold** (Postgres schema `gold`) — data marts: the aggregated/modeled shape a dashboard or API actually wants. Reads silver (or other gold tables), never bronze.

**Hard rule: PII de-identification happens in silver, and only in silver.** Any column that could identify an individual — name, phone number, patient/case identifier, precise geolocation, free-text notes — must be hashed, masked, or dropped in the silver model's `transform.sql`, before the row is ever written. Gold and any future API only ever read from silver/gold. Doing it once, centrally, at the bronze→silver boundary is what makes "nothing downstream ever sees raw PII" an actual guarantee instead of a hope. See `silver/signals/transform.sql` for the pattern and comment convention — copy it into every new silver model even if that particular source has nothing to hash yet (mdharura's current fields don't).

## Deliberate technology choices — don't relitigate without new information

These were decided in conversation with the project owner, with explicit trade-offs discussed. If reconsidering one, ask first rather than assuming the original choice was an oversight.

- **Postgres for gold, not ClickHouse.** ClickHouse is genuinely better suited to heavy analytical/aggregate workloads at large scale, but adds real operational weight (harder backups, no easy row-level updates, another system to run). At this project's realistic data volume (national EBS-style surveillance data, not high-frequency telemetry), Postgres is simpler to operate and plenty fast, and it's a better direct backend for the APIs planned on top of gold. Revisit only if a *specific* mart's query performance actually becomes a problem — swap that one mart, not the whole system.
- **Plain Python + SQL for silver/gold, not dbt.** dbt is the more standard tool for exactly this layer (SQL models as a testable DAG) and was explicitly offered as the recommended option — the project owner chose plain scripts instead, to keep the tool count down and match the ingestion repo's existing `loader.py`-per-folder shape. The convention that replaces dbt's structure here: one folder per model, `asset.py` (Dagster asset, thin wrapper) + `transform.sql` (the actual logic), full-rebuild style (`DROP TABLE ... CREATE TABLE ... AS SELECT ...`) rather than incremental. This is fine at current scale; if full-rebuild runtimes become a real problem as data grows, that's the point to reconsider — either incremental SQL or dbt, not before.
- **dlt for bronze.** Not in tension with the "no dbt" choice above — dlt is an extract/load tool, not a transform tool. Bronze uses dlt's `filesystem` *source* (reading `.jsonl.gz` from MinIO via the same S3-compatible interface the ingestion repo writes with) piped through `read_jsonl()`, loading into dlt's `postgres` *destination*. This mirrors the ingestion repo's own use of dlt, just source and destination swapped.
- **Full-rebuild, not incremental, for silver/gold.** Every model drops and recreates its table on each run. Simple, always-correct, no cursor/watermark bookkeeping to get wrong. Fine while bronze data volume is small; if this starts taking too long, that's a real signal to revisit — not a reason to preemptively add complexity now.

## Conventions

- **Bronze**: `src/warehouse/bronze/<source>/assets.py`. `bucket_url` points at that source's MinIO prefix (matches the ingestion repo's `dataset_name` for that source, e.g. `s3://evd/<source>_raw/<resource>`). Use that source's own scoped MinIO credential (see the ingestion repo's multi-source MinIO setup — every source has its own `<source>-svc` user limited to its own prefix). Never use the MinIO root user or another source's credentials here.
- **Silver/gold**: `src/warehouse/<layer>/<model>/asset.py` + `transform.sql`. The asset just reads the adjacent `.sql` file and executes it via the shared `PostgresResource` (`src/warehouse/resources.py`) — keep logic in SQL, not Python.
- **Wiring**: nothing autoloads. Every new asset must be imported and added to the `assets` list in `src/warehouse/definitions.py` by hand — deliberate, since this repo doesn't use the ingestion repo's component-autoload system.
- **Reference implementation**: `mdharura` end-to-end (`bronze/mdharura/`, `silver/signals/`, `gold/county_signal_daily_counts/`) — copy its shape for anything new.

## Current status (as of scaffolding)

This repo was just scaffolded and **has not been run yet** — nothing here has been verified against live MinIO/Postgres. Before trusting any of it:

1. `uv sync`, then `cp .dlt/secrets.example.toml .dlt/secrets.toml` and `cp .env.example .env`, fill in real credentials.
2. `docker compose up -d` for local Postgres, `dg check defs` to validate the project loads.
3. Run bronze first (`dg launch --assets "mdharura_bronze"`), then inspect the actual table it created (`\d bronze.mdharura_signals` in `psql`) — dlt normalizes JSON field names, and `silver/signals/transform.sql` assumes specific column names that need to be checked against reality before the silver model will run cleanly.
4. Only then run silver, then gold.

## Not yet built

- **Deployment.** This repo only has a local-dev `docker-compose.yml` (Postgres only). Production deployment (mirroring the ingestion repo's Docker Compose + `evd-net` pattern on the shared Ubuntu server) hasn't been done — do this once the pipeline is verified locally, and once it's deployed, join it to `evd-net` so it can reach MinIO the same way the ingestion repo does.
- **APIs.** Gold is meant to be queried by an API layer eventually — not started. When it is, it should read from `gold` (or `silver` for record-level access), never `bronze`.
- **More sources.** Only `mdharura` exists so far. Each new source in the ingestion repo needs a matching `bronze/<source>/` here once there's a reason to warehouse it.
