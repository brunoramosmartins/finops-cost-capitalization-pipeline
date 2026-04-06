"""Dagster ops for orchestrating the local FinOps pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from dagster import OpExecutionContext, Out, op

from finops_capex.pipeline.runtime import (
    PipelineRunSummary,
    collect_warehouse_quality_snapshot,
    load_pipeline_config,
    resolve_dbt_executable,
    run_command,
    run_local_pipeline,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@op(out=Out(dict))
def load_pipeline_settings_op(_: OpExecutionContext) -> dict:
    """Load the shared pipeline YAML used by local execution and Dagster."""

    return load_pipeline_config(REPOSITORY_ROOT / "conf" / "pipeline.yml")


@op(out=Out(PipelineRunSummary))
def run_daily_finops_pipeline_op(context: OpExecutionContext, settings: dict) -> PipelineRunSummary:
    """Run the full local-first pipeline and emit summary metadata."""

    summary = run_local_pipeline(
        REPOSITORY_ROOT,
        profile_name=str(settings["execution"]["generator_profile"]),
    )
    context.add_output_metadata(
        {
            "status": summary.status,
            "run_date": summary.run_date,
            "batch_id": summary.batch_id or "n/a",
            "metadata_file": summary.metadata_file,
        }
    )
    return summary


@op
def emit_pipeline_health_op(context: OpExecutionContext, summary: PipelineRunSummary) -> None:
    """Publish a concise health snapshot for the latest successful pipeline run."""

    warehouse_snapshot = summary.warehouse_snapshot or collect_warehouse_quality_snapshot(
        Path(summary.warehouse_path)
    )
    context.log.info(
        "Pipeline %s for %s completed with Bronze=%s Gold=%s classifications=%s",
        summary.status,
        summary.run_date,
        warehouse_snapshot.bronze_row_count,
        warehouse_snapshot.gold_row_count,
        warehouse_snapshot.classification_counts,
    )


@op(out=Out(str))
def validate_dbt_environment_op(_: OpExecutionContext, settings: dict) -> str:
    """Validate that the dbt runtime can be resolved before a scheduled run."""

    dbt_executable = resolve_dbt_executable()
    dbt_project_dir = str(settings["dbt"]["project_dir"])
    profiles_dir = str((REPOSITORY_ROOT / str(settings["dbt"]["profiles_dir"])).resolve())
    stage = run_command(
        [dbt_executable, "debug", "--project-dir", dbt_project_dir],
        cwd=REPOSITORY_ROOT,
        env={"DBT_PROFILES_DIR": profiles_dir, **os.environ},
        stage_name="dagster_dbt_debug",
    )
    return stage.stage_name
