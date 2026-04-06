"""CLI entrypoint for versioned Gold exports."""

from __future__ import annotations

import argparse
from pathlib import Path

from finops_capex.exports.gold_exporter import export_gold_tables
from finops_capex.pipeline.runtime import load_pipeline_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for Gold export execution."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot-date",
        required=True,
        help="Snapshot date used to version the export (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--file-format",
        choices=["parquet", "csv"],
        default=None,
        help="Override the configured export file format.",
    )
    return parser.parse_args()


def main() -> None:
    """Export the configured Gold analytical tables and print the manifest path."""

    args = parse_args()
    pipeline_config = load_pipeline_config(REPOSITORY_ROOT / "conf" / "pipeline.yml")
    file_format = args.file_format or str(pipeline_config["exports"]["file_format"])
    summary = export_gold_tables(
        warehouse_path=REPOSITORY_ROOT / str(pipeline_config["warehouse"]["path"]),
        export_root=REPOSITORY_ROOT / str(pipeline_config["storage"]["gold_root"]),
        snapshot_date=args.snapshot_date,
        relations=list(pipeline_config["exports"]["include_tables"]),
        file_format=file_format,
        freshness_threshold_hours=int(pipeline_config["observability"]["freshness_threshold_hours"]),
    )
    print(summary.manifest_file)
