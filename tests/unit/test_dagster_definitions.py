"""Smoke tests for Dagster definitions registration."""

from orchestration.dagster_project.definitions import defs


def test_daily_finops_pipeline_job_is_registered() -> None:
    """Dagster definitions should expose the daily pipeline job by name."""

    assert defs.get_job_def("daily_finops_pipeline").name == "daily_finops_pipeline"
