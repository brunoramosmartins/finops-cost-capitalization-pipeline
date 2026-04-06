"""Unit tests for versioned Gold exports."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

from finops_capex.exports.gold_exporter import export_gold_tables


def build_export_fixture_database(warehouse_path: Path) -> None:
    """Create minimal warehouse tables required by the Gold exporter."""

    connection = duckdb.connect(str(warehouse_path))
    connection.execute("create schema analytics_gold")
    connection.execute("create schema analytics_marts")
    connection.execute(
        """
        create table analytics_gold.fct_cost_classification as
        select * from (
            values
                (
                    'l1',
                    timestamp '2026-04-06 10:00:00',
                    'opex',
                    10.0,
                    timestamp '2026-04-06 10:10:00'
                ),
                (
                    'l2',
                    timestamp '2026-04-06 11:00:00',
                    'capex_eligible',
                    15.0,
                    timestamp '2026-04-06 10:10:00'
                )
        ) as t(
            line_item_id,
            usage_start_time_utc,
            classification_status,
            unblended_cost,
            generated_at_utc
        )
        """
    )
    connection.execute(
        """
        create table analytics_gold.fct_capex_candidate_costs as
        select * from (
            values
                ('l2', timestamp '2026-04-06 11:00:00', 15.0)
        ) as t(line_item_id, usage_start_time_utc, unblended_cost)
        """
    )
    connection.execute(
        """
        create table analytics_marts.mart_monthly_finops_summary as
        select * from (
            values
                (date '2026-04-01', 'payments-platform', 'payments', 'opex', 1, 10.0),
                (date '2026-04-01', 'payments-platform', 'payments', 'capex_eligible', 1, 15.0)
        ) as t(
            billing_month,
            owner_team,
            product_line,
            classification_status,
            line_item_count,
            total_unblended_cost
        )
        """
    )
    connection.execute(
        """
        create table analytics_marts.mart_capitalization_waterfall as
        select * from (
            values
                (date '2026-04-01', 'compute', 'capex_eligible', 'eligible_build_cost', 1, 15.0)
        ) as t(
            billing_month,
            service_family,
            classification_status,
            classification_reason,
            line_item_count,
            total_unblended_cost
        )
        """
    )
    connection.close()


def test_export_gold_tables_writes_manifest_and_artifacts(tmp_path: Path) -> None:
    """Gold exports should be versioned, materialized, and accompanied by a manifest."""

    warehouse_path = tmp_path / "warehouse.duckdb"
    export_root = tmp_path / "gold_exports"
    build_export_fixture_database(warehouse_path)

    summary = export_gold_tables(
        warehouse_path=warehouse_path,
        export_root=export_root,
        snapshot_date="2026-04-06",
        relations=[
            "analytics_gold.fct_cost_classification",
            "analytics_gold.fct_capex_candidate_costs",
            "analytics_marts.mart_monthly_finops_summary",
            "analytics_marts.mart_capitalization_waterfall",
        ],
    )

    manifest_path = Path(summary.manifest_file)
    assert manifest_path.exists()
    assert summary.export_version == "v0.4.0"
    assert summary.freshness_within_threshold is True
    assert len(summary.artifacts) == 4

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_payload["latest_billing_month"] == "2026-04-01"

    artifact_path = export_root / summary.artifacts[0].relative_path
    assert artifact_path.exists()
    assert len(pd.read_parquet(artifact_path)) == summary.artifacts[0].row_count
