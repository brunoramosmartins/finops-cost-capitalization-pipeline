"""Dagster schedules for the FinOps pipeline."""

from pathlib import Path

from dagster import ScheduleDefinition

from finops_capex.pipeline.runtime import load_pipeline_config

from .jobs import daily_finops_pipeline_job

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_SETTINGS = load_pipeline_config(REPOSITORY_ROOT / "conf" / "pipeline.yml")

daily_finops_pipeline_schedule = ScheduleDefinition(
    job=daily_finops_pipeline_job,
    cron_schedule=str(PIPELINE_SETTINGS["orchestration"]["schedule_cron"]),
)
