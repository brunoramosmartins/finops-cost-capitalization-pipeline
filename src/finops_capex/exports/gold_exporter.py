"""Export versioned Gold analytical tables for downstream ML consumption."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from finops_capex import __version__


@dataclass(frozen=True)
class GoldExportArtifact:
    """Metadata for one exported analytical table."""

    relation_name: str
    schema_name: str
    table_name: str
    relative_path: str
    row_count: int
    columns: list[dict[str, str]]


@dataclass(frozen=True)
class GoldExportSummary:
    """Summary manifest for a Gold export snapshot."""

    export_version: str
    snapshot_date: str
    exported_at: str
    export_root: str
    manifest_file: str
    warehouse_path: str
    latest_generator_timestamp: str | None
    freshness_threshold_hours: int
    freshness_within_threshold: bool | None
    latest_billing_month: str | None
    artifacts: list[GoldExportArtifact]

    def to_dict(self) -> dict[str, object]:
        """Serialize the export summary to a JSON-friendly dictionary."""

        payload = asdict(self)
        payload["artifacts"] = [asdict(artifact) for artifact in self.artifacts]
        return payload


def export_gold_tables(
    *,
    warehouse_path: Path,
    export_root: Path,
    snapshot_date: str,
    relations: list[str],
    file_format: str = "parquet",
    freshness_threshold_hours: int = 24,
) -> GoldExportSummary:
    """Export selected Gold and mart relations to a versioned snapshot folder."""

    if file_format not in {"parquet", "csv"}:
        raise ValueError("file_format must be either 'parquet' or 'csv'")

    export_version = f"v{__version__}"
    export_directory = export_root / f"version={export_version}" / f"snapshot_date={snapshot_date}"
    export_directory.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(warehouse_path))
    artifacts: list[GoldExportArtifact] = []
    exported_at = datetime.now(tz=timezone.utc)

    try:
        latest_generator_timestamp = connection.execute(
            """
            select cast(max(generated_at_utc) as varchar)
            from analytics_gold.fct_cost_classification
            """
        ).fetchone()[0]
        latest_billing_month = connection.execute(
            """
            select cast(max(billing_month) as varchar)
            from analytics_marts.mart_monthly_finops_summary
            """
        ).fetchone()[0]

        freshness_within_threshold = None
        if latest_generator_timestamp is not None:
            latest_generated_at = datetime.fromisoformat(latest_generator_timestamp)
            if latest_generated_at.tzinfo is None:
                latest_generated_at = latest_generated_at.replace(tzinfo=timezone.utc)
            freshness_within_threshold = (
                exported_at - latest_generated_at
            ).total_seconds() <= freshness_threshold_hours * 3600

        for relation in relations:
            schema_name, table_name = relation.split(".", maxsplit=1)
            dataframe = connection.execute(f"select * from {relation}").fetchdf()
            column_frame = connection.execute(f"describe select * from {relation}").fetchdf()
            artifact_directory = export_directory / schema_name
            artifact_directory.mkdir(parents=True, exist_ok=True)
            artifact_path = artifact_directory / f"{table_name}.{file_format}"

            if file_format == "parquet":
                dataframe.to_parquet(artifact_path, index=False)
                exported_row_count = len(pd.read_parquet(artifact_path))
            else:
                dataframe.to_csv(artifact_path, index=False)
                exported_row_count = len(pd.read_csv(artifact_path))

            if exported_row_count != len(dataframe):
                raise ValueError(
                    f"Exported row count mismatch for {relation}: "
                    f"warehouse={len(dataframe)} exported={exported_row_count}"
                )

            artifacts.append(
                GoldExportArtifact(
                    relation_name=relation,
                    schema_name=schema_name,
                    table_name=table_name,
                    relative_path=str(artifact_path.relative_to(export_root)),
                    row_count=int(len(dataframe)),
                    columns=[
                        {
                            "name": str(row["column_name"]),
                            "type": str(row["column_type"]),
                        }
                        for _, row in column_frame.iterrows()
                    ],
                )
            )
    finally:
        connection.close()

    manifest_file = export_directory / "export_manifest.json"
    summary = GoldExportSummary(
        export_version=export_version,
        snapshot_date=snapshot_date,
        exported_at=exported_at.isoformat(),
        export_root=str(export_root),
        manifest_file=str(manifest_file),
        warehouse_path=str(warehouse_path),
        latest_generator_timestamp=latest_generator_timestamp,
        freshness_threshold_hours=freshness_threshold_hours,
        freshness_within_threshold=freshness_within_threshold,
        latest_billing_month=latest_billing_month,
        artifacts=artifacts,
    )
    manifest_file.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
    return summary
