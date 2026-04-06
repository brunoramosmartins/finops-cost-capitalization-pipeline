"""Unit tests for Phase 3 pipeline runtime helpers."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from finops_capex.pipeline.runtime import (
    PipelineRunSummary,
    PipelineStageResult,
    WarehouseQualitySnapshot,
    build_metadata_path,
    collect_warehouse_quality_snapshot,
)


def test_build_metadata_path_uses_partitioned_run_date(tmp_path: Path) -> None:
    """Run metadata should be partitioned by run date for easier incident review."""

    metadata_path = build_metadata_path(
        repository_root=tmp_path,
        metadata_root="local_lake/metadata/pipeline_runs",
        run_date="2026-04-06",
    )

    assert metadata_path.name == "run_summary.json"
    assert "run_date=2026-04-06" in metadata_path.as_posix()


def test_collect_warehouse_quality_snapshot_reads_expected_metrics(tmp_path: Path) -> None:
    """Warehouse snapshot collection should summarize Bronze and Gold state."""

    warehouse_path = tmp_path / "finops.duckdb"
    connection = duckdb.connect(str(warehouse_path))
    connection.execute("create schema analytics_bronze")
    connection.execute("create schema analytics_gold")
    connection.execute("create schema analytics_marts")
    connection.execute(
        "create table analytics_bronze.brz_cloud_cost_usage as "
        "select * from (values ('a'), ('b'), ('c')) as t(line_item_id)"
    )
    connection.execute(
        "create table analytics_gold.fct_cost_classification as "
        "select * from (values ('a', 'opex'), ('b', 'capex_eligible'), ('c', 'opex')) "
        "as t(line_item_id, classification_status)"
    )
    connection.execute(
        "create table analytics_marts.mart_monthly_finops_summary as "
        "select * from (values (date '2026-04-01')) as t(billing_month)"
    )
    connection.close()

    snapshot = collect_warehouse_quality_snapshot(warehouse_path)

    assert snapshot.bronze_row_count == 3
    assert snapshot.gold_row_count == 3
    assert snapshot.latest_billing_month == "2026-04-01"
    assert snapshot.classification_counts == {"capex_eligible": 1, "opex": 2}


def test_pipeline_run_summary_serialization_keeps_nested_stage_results() -> None:
    """Run summaries should serialize cleanly for metadata publication."""

    summary = PipelineRunSummary(
        project_name="finops-cost-capitalization-pipeline",
        status="success",
        run_date="2026-04-06",
        batch_id="batch-1",
        row_count=10,
        started_at="2026-04-06T10:00:00+00:00",
        finished_at="2026-04-06T10:01:00+00:00",
        data_file="local_lake/raw/file.parquet",
        sample_file="data/sample/file.csv",
        metadata_file="local_lake/metadata/pipeline_runs/run_date=2026-04-06/run_summary.json",
        warehouse_path="warehouse/finops.duckdb",
        dbt_artifact_path="dbt/target/run_results.json",
        stage_results=[
            PipelineStageResult(
                stage_name="dbt_run",
                command=["dbt", "run"],
                started_at="2026-04-06T10:00:00+00:00",
                finished_at="2026-04-06T10:00:30+00:00",
                duration_seconds=30.0,
                return_code=0,
            )
        ],
        warehouse_snapshot=WarehouseQualitySnapshot(
            bronze_row_count=10,
            gold_row_count=10,
            latest_billing_month="2026-04-01",
            classification_counts={"opex": 7, "capex_eligible": 3},
        ),
    )

    payload = summary.to_dict()

    assert payload["stage_results"][0]["stage_name"] == "dbt_run"
    assert payload["warehouse_snapshot"]["gold_row_count"] == 10
    assert json.loads(json.dumps(payload))["status"] == "success"
