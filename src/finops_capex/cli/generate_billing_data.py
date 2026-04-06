"""CLI entrypoint for synthetic billing data generation."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from finops_capex.generators import (
    GenerationConfig,
    SyntheticBillingGenerator,
    build_generation_runtime_config,
    load_generator_profile,
)
from finops_capex.ingestion.lake_writer import write_raw_billing_batch
from finops_capex.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the generation workflow."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="conf/generator_profiles.yml",
        help="Path to the generator profile YAML file.",
    )
    parser.add_argument(
        "--profile",
        default="default",
        help="Profile name inside the YAML config.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Override the configured number of days to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the configured random seed.",
    )
    parser.add_argument(
        "--run-date",
        default=None,
        help="Override the configured run date in ISO format (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--output-format",
        choices=["parquet", "csv"],
        default=None,
        help="Write the raw output as parquet or csv.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of rows to write into the sample CSV.",
    )
    return parser.parse_args()


def build_generation_config(args: argparse.Namespace) -> tuple[GenerationConfig, str, int]:
    """Build runtime configuration plus persistence options."""

    profile = load_generator_profile(Path(args.config), args.profile)
    config = build_generation_runtime_config(
        profile,
        days_override=args.days,
        seed_override=args.seed,
        run_date_override=args.run_date,
    )

    output_format = args.output_format or str(profile["output_format"])
    sample_size = args.sample_size or int(profile["sample_size"])
    return config, output_format, sample_size


def main() -> None:
    """Run the synthetic billing generation workflow."""

    configure_logging()
    args = parse_args()
    config, output_format, sample_size = build_generation_config(args)
    generator = SyntheticBillingGenerator(config)
    dataframe = generator.generate_dataframe()

    manifest = write_raw_billing_batch(
        dataframe=dataframe,
        repository_root=REPOSITORY_ROOT,
        run_date=config.run_date.isoformat(),
        output_format=output_format,
        sample_size=sample_size,
    )

    LOGGER.info("Generated %s rows for batch %s.", manifest.row_count, manifest.batch_id)
    LOGGER.info("Raw data written to %s.", manifest.data_file)
    LOGGER.info("Sample data written to %s.", manifest.sample_file)
