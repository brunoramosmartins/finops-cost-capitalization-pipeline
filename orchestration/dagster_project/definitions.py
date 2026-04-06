"""Dagster definitions entrypoint for local development."""

from dagster import Definitions

from .jobs import daily_finops_pipeline_job
from .schedules import daily_finops_pipeline_schedule

defs = Definitions(
    jobs=[daily_finops_pipeline_job],
    schedules=[daily_finops_pipeline_schedule],
)
