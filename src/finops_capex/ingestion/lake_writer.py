"""Write generated billing data to a local mock data lake."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .manifest import BatchManifest, build_manifest


def write_raw_billing_batch(
    dataframe: pd.DataFrame,
    repository_root: Path,
    run_date: str,
    output_format: str = "parquet",
    sample_size: int = 250,
) -> BatchManifest:
    """Write a generated batch to the repository-local mock data lake."""

    partition_dir = repository_root / "local_lake" / "raw" / "cloud_costs" / f"run_date={run_date}"
    sample_dir = repository_root / "data" / "sample"
    partition_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    if output_format not in {"parquet", "csv"}:
        raise ValueError("output_format must be either 'parquet' or 'csv'")

    data_extension = "parquet" if output_format == "parquet" else "csv"
    data_file = partition_dir / f"cloud_cost_usage.{data_extension}"
    sample_file = sample_dir / "cloud_cost_usage_sample.csv"

    if output_format == "parquet":
        dataframe.to_parquet(data_file, index=False)
    else:
        dataframe.to_csv(data_file, index=False)

    dataframe.head(sample_size).to_csv(sample_file, index=False)

    manifest = build_manifest(
        dataframe=dataframe,
        run_date=run_date,
        file_format=output_format,
        data_file=data_file,
        sample_file=sample_file,
    )

    manifest_file = partition_dir / "manifest.json"
    sample_manifest_file = sample_dir / "cloud_cost_usage_sample_manifest.json"

    manifest_file.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    sample_manifest_file.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

    return manifest
