"""Unit tests for generator configuration helpers."""

from __future__ import annotations

from pathlib import Path

from finops_capex.generators.configuration import (
    build_generation_runtime_config,
    load_generator_profile,
)


def test_load_generator_profile_reads_default_profile() -> None:
    """The default generator profile should remain available for local runs."""

    profile = load_generator_profile(
        Path("conf/generator_profiles.yml"),
        "default",
    )

    assert profile["payer_account_id"] == "111111111111"
    assert profile["output_format"] == "parquet"


def test_build_generation_runtime_config_applies_overrides() -> None:
    """CLI and orchestration overrides should take precedence over YAML defaults."""

    profile = load_generator_profile(
        Path("conf/generator_profiles.yml"),
        "default",
    )

    config = build_generation_runtime_config(
        profile,
        days_override=30,
        seed_override=7,
        run_date_override="2026-04-10",
    )

    assert config.days == 30
    assert config.seed == 7
    assert config.run_date.isoformat() == "2026-04-10"
