"""CLI entrypoint for synthetic billing data generation."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import yaml

from finops_capex.generators import GenerationConfig, SyntheticBillingGenerator
from finops_capex.ingestion.lake_writer import write_raw_billing_batch
from finops_capex.utils.dates import parse_iso_date
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


def load_profile(config_path: Path, profile_name: str) -> dict[str, object]:
    """Load a named generator profile from YAML."""

    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        return config_payload[profile_name]
    except KeyError as exc:
        raise KeyError(f"Profile '{profile_name}' not found in {config_path}.") from exc


def build_generation_config(args: argparse.Namespace) -> tuple[GenerationConfig, str, int]:
    """Build runtime configuration plus persistence options."""

    profile = load_profile(Path(args.config), args.profile)
    if args.run_date:
        run_date = parse_iso_date(args.run_date)
    elif "run_date" in profile:
        run_date = parse_iso_date(str(profile["run_date"]))
    else:
        run_date = parse_iso_date("2026-04-06")

    config = GenerationConfig(
        days=args.days or int(profile["days"]),
        seed=args.seed or int(profile["seed"]),
        payer_account_id=str(profile["payer_account_id"]),
        linked_accounts=tuple(profile["linked_accounts"]),
        regions=tuple(profile["regions"]),
        run_date=run_date,
        imperfect_tag_rate=float(profile["imperfect_tag_rate"]),
        credit_row_rate=float(profile["credit_row_rate"]),
        event_spike_rate=float(profile["event_spike_rate"]),
        accounting_policy_version=str(profile["accounting_policy_version"]),
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
