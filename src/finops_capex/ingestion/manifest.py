"""Manifest helpers for synthetic billing output batches."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class BatchManifest:
    """Metadata describing a generated raw data batch."""

    batch_id: str
    run_date: str
    row_count: int
    start_date: str
    end_date: str
    file_format: str
    data_file: str
    sample_file: str

    def to_dict(self) -> dict[str, str | int]:
        """Serialize the manifest to a dictionary."""

        return asdict(self)


def build_manifest(
    dataframe: pd.DataFrame,
    run_date: str,
    file_format: str,
    data_file: Path,
    sample_file: Path,
) -> BatchManifest:
    """Create a manifest from a generated billing DataFrame."""

    return BatchManifest(
        batch_id=str(dataframe["generator_batch_id"].iloc[0]),
        run_date=run_date,
        row_count=int(len(dataframe)),
        start_date=str(pd.to_datetime(dataframe["usage_start_time"]).min().date()),
        end_date=str(pd.to_datetime(dataframe["usage_start_time"]).max().date()),
        file_format=file_format,
        data_file=str(data_file),
        sample_file=str(sample_file),
    )
