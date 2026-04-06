"""CLI entrypoint for the full local pipeline run."""

from __future__ import annotations

import argparse
from pathlib import Path

from finops_capex.pipeline.runtime import run_local_pipeline

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the local orchestration workflow."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        default=None,
        help="Generator profile name inside the YAML config.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Override the configured generation window.",
    )
    parser.add_argument(
        "--run-date",
        default=None,
        help="Override the pipeline run date in ISO format (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--output-format",
        choices=["parquet", "csv"],
        default=None,
        help="Raw file output format for the generator stage.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Override the sample CSV row count.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the full local pipeline and print the summary metadata path."""

    args = parse_args()
    summary = run_local_pipeline(
        REPOSITORY_ROOT,
        profile_name=args.profile,
        days_override=args.days,
        run_date_override=args.run_date,
        output_format_override=args.output_format,
        sample_size_override=args.sample_size,
    )
    print(summary.metadata_file)
