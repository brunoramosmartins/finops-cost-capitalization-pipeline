"""Dagster jobs for the FinOps pipeline."""

from dagster import job

from .ops import emit_pipeline_health_op, load_pipeline_settings_op, run_daily_finops_pipeline_op


@job(name="daily_finops_pipeline")
def daily_finops_pipeline_job():
    """Run the synthetic generation, dbt build, and health publication flow."""

    settings = load_pipeline_settings_op()
    summary = run_daily_finops_pipeline_op(settings)
    emit_pipeline_health_op(summary)
