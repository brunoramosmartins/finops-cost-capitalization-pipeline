"""Integration tests for local mock lake persistence."""

from __future__ import annotations

import json
from pathlib import Path

from finops_capex.generators import GenerationConfig, SyntheticBillingGenerator
from finops_capex.ingestion.lake_writer import write_raw_billing_batch


def test_write_raw_billing_batch_creates_partition_files(tmp_path: Path) -> None:
    """Writing a raw batch should create data, sample, and manifest files."""

    generator = SyntheticBillingGenerator(GenerationConfig(days=10, seed=5))
    dataframe = generator.generate_dataframe()

    manifest = write_raw_billing_batch(
        dataframe=dataframe,
        repository_root=tmp_path,
        run_date="2026-04-06",
        output_format="csv",
        sample_size=25,
    )

    data_file = Path(manifest.data_file)
    sample_file = Path(manifest.sample_file)
    manifest_file = (
        tmp_path
        / "local_lake"
        / "raw"
        / "cloud_costs"
        / "run_date=2026-04-06"
        / "manifest.json"
    )

    assert data_file.exists()
    assert sample_file.exists()
    assert manifest_file.exists()

    payload = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert payload["row_count"] == len(dataframe)
    assert payload["run_date"] == "2026-04-06"
