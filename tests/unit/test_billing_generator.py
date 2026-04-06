"""Unit tests for the synthetic billing generator."""

from __future__ import annotations

from datetime import timedelta

from finops_capex.generators import GenerationConfig, SyntheticBillingGenerator


def test_generator_produces_expected_core_columns() -> None:
    """The generated DataFrame should contain the core raw contract columns."""

    generator = SyntheticBillingGenerator(GenerationConfig(days=30, seed=7))
    dataframe = generator.generate_dataframe()

    expected_columns = {
        "line_item_id",
        "billing_period_start",
        "usage_start_time",
        "usage_end_time",
        "invoice_date",
        "cloud_provider",
        "payer_account_id",
        "linked_account_id",
        "service",
        "usage_type",
        "operation",
        "region",
        "resource_id",
        "line_item_type",
        "usage_amount",
        "unblended_cost",
        "blended_cost",
        "discount_type",
        "cost_center",
        "owner_team",
        "environment",
        "product_line",
        "capitalization_candidate",
        "initiative_id",
        "initiative_stage",
        "asset_lifecycle",
        "accounting_policy_version",
        "generator_batch_id",
        "generated_at",
    }

    assert expected_columns.issubset(set(dataframe.columns))
    assert not dataframe.empty


def test_generator_covers_requested_date_range() -> None:
    """The generator should emit data covering the configured number of days."""

    config = GenerationConfig(days=15, seed=11)
    generator = SyntheticBillingGenerator(config)
    dataframe = generator.generate_dataframe()

    start_date = dataframe["usage_start_time"].min().date()
    end_date = dataframe["usage_start_time"].max().date()

    assert end_date - start_date == timedelta(days=config.days - 1)


def test_generator_creates_credit_or_discount_rows() -> None:
    """The generator should occasionally model credits or discounts."""

    config = GenerationConfig(days=120, seed=22, credit_row_rate=0.2)
    generator = SyntheticBillingGenerator(config)
    dataframe = generator.generate_dataframe()

    non_usage_rows = dataframe[dataframe["line_item_type"] != "Usage"]

    assert not non_usage_rows.empty
    assert (non_usage_rows["unblended_cost"] < 0).all()
