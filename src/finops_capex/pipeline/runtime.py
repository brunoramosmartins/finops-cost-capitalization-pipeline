"""Local pipeline runtime for quality validation and orchestration."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import yaml

from finops_capex.generators import (
    SyntheticBillingGenerator,
    build_generation_runtime_config,
    load_generator_profile,
)
from finops_capex.ingestion.lake_writer import write_raw_billing_batch
from finops_capex.ingestion.manifest import BatchManifest
from finops_capex.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineStageResult:
    """Execution metadata for a single pipeline stage."""

    stage_name: str
    command: list[str]
    started_at: str
    finished_at: str
    duration_seconds: float
    return_code: int


@dataclass(frozen=True)
class WarehouseQualitySnapshot:
    """High-level warehouse validation metrics used for observability."""

    bronze_row_count: int
    gold_row_count: int
    latest_billing_month: str | None
    classification_counts: dict[str, int]


@dataclass(frozen=True)
class PipelineRunSummary:
    """Summary persisted after each local or orchestrated pipeline run."""

    project_name: str
    status: str
    run_date: str
    batch_id: str | None
    row_count: int | None
    started_at: str
    finished_at: str
    data_file: str | None
    sample_file: str | None
    metadata_file: str
    warehouse_path: str
    dbt_artifact_path: str
    stage_results: list[PipelineStageResult]
    warehouse_snapshot: WarehouseQualitySnapshot | None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the summary for JSON output."""

        payload = asdict(self)
        payload["stage_results"] = [asdict(stage) for stage in self.stage_results]
        return payload


def load_pipeline_config(config_path: Path) -> dict[str, Any]:
    """Load the pipeline YAML configuration file."""

    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def resolve_dbt_executable() -> str:
    """Resolve the dbt executable for the active Python environment."""

    dbt_executable = shutil.which("dbt")
    if dbt_executable:
        return dbt_executable

    script_name = "dbt.exe" if os_name_is_windows() else "dbt"
    fallback = Path(sys.executable).with_name(script_name)
    if fallback.exists():
        return str(fallback)

    raise FileNotFoundError(
        "dbt executable not found. Install development dependencies with "
        "`pip install -e \".[dev]\"` and ensure the environment is activated."
    )


def os_name_is_windows() -> bool:
    """Return whether the current runtime is Windows."""

    return sys.platform.startswith("win")


def run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stage_name: str,
) -> PipelineStageResult:
    """Run a subprocess command and return structured execution metadata."""

    started = datetime.now(tz=timezone.utc)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        check=True,
        capture_output=True,
    )
    finished = datetime.now(tz=timezone.utc)

    if completed.stdout:
        LOGGER.info("%s stdout:\n%s", stage_name, completed.stdout.strip())
    if completed.stderr:
        LOGGER.warning("%s stderr:\n%s", stage_name, completed.stderr.strip())

    return PipelineStageResult(
        stage_name=stage_name,
        command=command,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        duration_seconds=round((finished - started).total_seconds(), 3),
        return_code=completed.returncode,
    )


def generate_raw_batch(
    *,
    repository_root: Path,
    config_path: Path,
    profile_name: str,
    days_override: int | None = None,
    run_date_override: str | None = None,
    output_format_override: str | None = None,
    sample_size_override: int | None = None,
) -> BatchManifest:
    """Generate one raw synthetic billing drop using the shared profile loader."""

    profile = load_generator_profile(config_path, profile_name)
    generation_config = build_generation_runtime_config(
        profile,
        days_override=days_override,
        run_date_override=run_date_override,
    )
    output_format = output_format_override or str(profile["output_format"])
    sample_size = sample_size_override or int(profile["sample_size"])

    generator = SyntheticBillingGenerator(generation_config)
    dataframe = generator.generate_dataframe()
    return write_raw_billing_batch(
        dataframe=dataframe,
        repository_root=repository_root,
        run_date=generation_config.run_date.isoformat(),
        output_format=output_format,
        sample_size=sample_size,
    )


def collect_warehouse_quality_snapshot(warehouse_path: Path) -> WarehouseQualitySnapshot:
    """Collect high-level quality metrics from the local DuckDB warehouse."""

    connection = duckdb.connect(str(warehouse_path))
    try:
        bronze_row_count = connection.execute(
            "select count(*) from analytics_bronze.brz_cloud_cost_usage"
        ).fetchone()[0]
        gold_row_count = connection.execute(
            "select count(*) from analytics_gold.fct_cost_classification"
        ).fetchone()[0]
        latest_billing_month = connection.execute(
            "select cast(max(billing_month) as varchar) "
            "from analytics_marts.mart_monthly_finops_summary"
        ).fetchone()[0]
        rows = connection.execute(
            """
            select classification_status, count(*) as line_items
            from analytics_gold.fct_cost_classification
            group by 1
            order by 1
            """
        ).fetchall()
    finally:
        connection.close()

    return WarehouseQualitySnapshot(
        bronze_row_count=int(bronze_row_count),
        gold_row_count=int(gold_row_count),
        latest_billing_month=latest_billing_month,
        classification_counts={status: int(count) for status, count in rows},
    )


def persist_pipeline_run_summary(
    *,
    repository_root: Path,
    metadata_root: str,
    summary: PipelineRunSummary,
) -> Path:
    """Persist pipeline run metadata under the repository-local metadata zone."""

    run_directory = repository_root / metadata_root / f"run_date={summary.run_date}"
    run_directory.mkdir(parents=True, exist_ok=True)
    metadata_path = run_directory / "run_summary.json"
    metadata_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
    return metadata_path


def build_metadata_path(repository_root: Path, metadata_root: str, run_date: str) -> Path:
    """Build the metadata output path for a given pipeline run date."""

    run_directory = repository_root / metadata_root / f"run_date={run_date}"
    run_directory.mkdir(parents=True, exist_ok=True)
    return run_directory / "run_summary.json"


def run_local_pipeline(
    repository_root: Path,
    *,
    pipeline_config_path: Path | None = None,
    generator_config_path: Path | None = None,
    profile_name: str | None = None,
    days_override: int | None = None,
    run_date_override: str | None = None,
    output_format_override: str | None = None,
    sample_size_override: int | None = None,
) -> PipelineRunSummary:
    """Run the full local-first FinOps pipeline and persist a run summary."""

    configure_logging()
    pipeline_config_path = pipeline_config_path or repository_root / "conf" / "pipeline.yml"
    generator_config_path = (
        generator_config_path
        or repository_root / "conf" / "generator_profiles.yml"
    )
    pipeline_config = load_pipeline_config(pipeline_config_path)
    profile_name = profile_name or str(pipeline_config["execution"]["generator_profile"])
    warehouse_path = repository_root / str(pipeline_config["warehouse"]["path"])
    dbt_project_dir = str(pipeline_config["dbt"]["project_dir"])
    dbt_profiles_dir = str(
        (repository_root / str(pipeline_config["dbt"]["profiles_dir"])).resolve()
    )
    metadata_root = str(pipeline_config["storage"]["metadata_root"])

    started_at = datetime.now(tz=timezone.utc)
    stage_results: list[PipelineStageResult] = []
    dbt_artifact_path = str(repository_root / dbt_project_dir / "target" / "run_results.json")
    dbt_env = {**os.environ, "DBT_PROFILES_DIR": dbt_profiles_dir}

    try:
        manifest = generate_raw_batch(
            repository_root=repository_root,
            config_path=generator_config_path,
            profile_name=profile_name,
            days_override=days_override,
            run_date_override=run_date_override,
            output_format_override=output_format_override,
            sample_size_override=sample_size_override,
        )

        dbt_executable = resolve_dbt_executable()
        stage_results.extend(
            [
                run_command(
                    [dbt_executable, "debug", "--project-dir", dbt_project_dir],
                    cwd=repository_root,
                    env=dbt_env,
                    stage_name="dbt_debug",
                ),
                run_command(
                    [dbt_executable, "seed", "--project-dir", dbt_project_dir],
                    cwd=repository_root,
                    env=dbt_env,
                    stage_name="dbt_seed",
                ),
                run_command(
                    [dbt_executable, "run", "--project-dir", dbt_project_dir],
                    cwd=repository_root,
                    env=dbt_env,
                    stage_name="dbt_run",
                ),
                run_command(
                    [dbt_executable, "test", "--project-dir", dbt_project_dir],
                    cwd=repository_root,
                    env=dbt_env,
                    stage_name="dbt_test",
                ),
            ]
        )

        finished_at = datetime.now(tz=timezone.utc)
        snapshot = collect_warehouse_quality_snapshot(warehouse_path)
        metadata_path = build_metadata_path(
            repository_root=repository_root,
            metadata_root=metadata_root,
            run_date=manifest.run_date,
        )
        summary = PipelineRunSummary(
            project_name=str(pipeline_config["project_name"]),
            status="success",
            run_date=manifest.run_date,
            batch_id=manifest.batch_id,
            row_count=manifest.row_count,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            data_file=manifest.data_file,
            sample_file=manifest.sample_file,
            metadata_file=str(metadata_path),
            warehouse_path=str(warehouse_path),
            dbt_artifact_path=dbt_artifact_path,
            stage_results=stage_results,
            warehouse_snapshot=snapshot,
        )
    except subprocess.CalledProcessError as exc:
        finished_at = datetime.now(tz=timezone.utc)
        LOGGER.exception("Pipeline stage failed: %s", exc.cmd)
        failed_run_date = run_date_override or datetime.now(tz=timezone.utc).date().isoformat()
        metadata_path = build_metadata_path(
            repository_root=repository_root,
            metadata_root=metadata_root,
            run_date=failed_run_date,
        )
        summary = PipelineRunSummary(
            project_name=str(pipeline_config["project_name"]),
            status="failed",
            run_date=failed_run_date,
            batch_id=None,
            row_count=None,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            data_file=None,
            sample_file=None,
            metadata_file=str(metadata_path),
            warehouse_path=str(warehouse_path),
            dbt_artifact_path=dbt_artifact_path,
            stage_results=stage_results,
            warehouse_snapshot=None,
            error_message=f"Command failed with exit code {exc.returncode}: {' '.join(exc.cmd)}",
        )
        metadata_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
        raise

    metadata_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
    return summary
