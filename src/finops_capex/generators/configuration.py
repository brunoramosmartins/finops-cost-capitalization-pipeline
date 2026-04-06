"""Configuration helpers shared by generation and orchestration entrypoints."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

from finops_capex.generators.billing_generator import GenerationConfig
from finops_capex.utils.dates import parse_iso_date


def load_generator_profile(config_path: Path, profile_name: str) -> dict[str, object]:
    """Load a named synthetic generation profile from YAML."""

    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        return config_payload[profile_name]
    except KeyError as exc:
        raise KeyError(f"Profile '{profile_name}' not found in {config_path}.") from exc


def build_generation_runtime_config(
    profile: Mapping[str, object],
    *,
    days_override: int | None = None,
    seed_override: int | None = None,
    run_date_override: str | None = None,
) -> GenerationConfig:
    """Build the generator dataclass from a YAML profile plus optional overrides."""

    if run_date_override:
        run_date = parse_iso_date(run_date_override)
    elif "run_date" in profile:
        run_date = parse_iso_date(str(profile["run_date"]))
    else:
        run_date = parse_iso_date("2026-04-06")

    return GenerationConfig(
        days=days_override or int(profile["days"]),
        seed=seed_override or int(profile["seed"]),
        payer_account_id=str(profile["payer_account_id"]),
        linked_accounts=tuple(profile["linked_accounts"]),
        regions=tuple(profile["regions"]),
        run_date=run_date,
        imperfect_tag_rate=float(profile["imperfect_tag_rate"]),
        credit_row_rate=float(profile["credit_row_rate"]),
        event_spike_rate=float(profile["event_spike_rate"]),
        accounting_policy_version=str(profile["accounting_policy_version"]),
    )
