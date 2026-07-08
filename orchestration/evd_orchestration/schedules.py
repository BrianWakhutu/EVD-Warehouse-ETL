from dagster import ScheduleDefinition

from evd_orchestration.jobs import ingest_job

lims_daily_schedule = ScheduleDefinition(
    job=ingest_job,
    cron_schedule="0 6 * * *",
)
