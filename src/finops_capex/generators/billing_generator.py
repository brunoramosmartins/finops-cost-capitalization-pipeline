"""Synthetic cloud billing generator for Phase 1 of the project."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from random import Random
from typing import Any

import pandas as pd
from faker import Faker

from .patterns import (
    DemandEvent,
    environment_multiplier,
    event_multiplier,
    monthly_multiplier,
    weekday_multiplier,
)
from .tags import generate_tag_bundle

SERVICE_PROFILES = [
    {
        "service": "AmazonEC2",
        "usage_type": "BoxUsage:m6i.large",
        "operation": "RunInstances",
        "base_cost": 82.0,
        "base_usage_amount": 24.0,
    },
    {
        "service": "AmazonS3",
        "usage_type": "TimedStorage-ByteHrs",
        "operation": "StandardStorage",
        "base_cost": 19.0,
        "base_usage_amount": 780.0,
    },
    {
        "service": "AmazonRDS",
        "usage_type": "InstanceUsage:db.r6g.large",
        "operation": "CreateDBInstance",
        "base_cost": 44.0,
        "base_usage_amount": 24.0,
    },
    {
        "service": "AWSDataTransfer",
        "usage_type": "DataTransfer-Out-Bytes",
        "operation": "InterRegionOut",
        "base_cost": 14.0,
        "base_usage_amount": 160.0,
    },
    {
        "service": "AWSSupport",
        "usage_type": "EnterpriseSupport",
        "operation": "SupportSubscription",
        "base_cost": 8.0,
        "base_usage_amount": 1.0,
    },
]

RESOURCE_PREFIX = {
    "AmazonEC2": "i-",
    "AmazonS3": "bucket-",
    "AmazonRDS": "db-",
    "AWSDataTransfer": "eni-",
    "AWSSupport": "support-",
}


@dataclass(frozen=True)
class GenerationConfig:
    """Runtime configuration for synthetic billing data generation."""

    days: int = 365
    seed: int = 42
    payer_account_id: str = "111111111111"
    linked_accounts: tuple[str, ...] = (
        "222222222221",
        "222222222222",
        "222222222223",
        "222222222224",
    )
    regions: tuple[str, ...] = ("us-east-1", "us-west-2", "eu-west-1")
    run_date: date = date(2026, 4, 6)
    imperfect_tag_rate: float = 0.08
    credit_row_rate: float = 0.02
    event_spike_rate: float = 0.03
    accounting_policy_version: str = "2026.1"


class SyntheticBillingGenerator:
    """Generate provider-like cloud billing data for local analytics development."""

    def __init__(self, config: GenerationConfig) -> None:
        """Initialize the generator with deterministic randomness."""

        self.config = config
        self.rng = Random(config.seed)
        self.faker = Faker()
        self.faker.seed_instance(config.seed)
        self._events = self._build_event_calendar()
        self._resource_cache: dict[tuple[int, str], str] = {}

    def generate_dataframe(self) -> pd.DataFrame:
        """Generate a pandas DataFrame containing billing line items."""

        rows: list[dict[str, Any]] = []
        generation_timestamp = datetime.now(tz=timezone.utc)
        batch_id = self._build_batch_id(generation_timestamp)
        start_day = self.config.run_date - timedelta(days=self.config.days - 1)

        for day_offset in range(self.config.days):
            usage_day = start_day + timedelta(days=day_offset)
            for account_index, linked_account_id in enumerate(self.config.linked_accounts):
                for service_profile in SERVICE_PROFILES:
                    rows.append(
                        self._build_usage_row(
                            usage_day=usage_day,
                            account_index=account_index,
                            linked_account_id=linked_account_id,
                            service_profile=service_profile,
                            batch_id=batch_id,
                            generation_timestamp=generation_timestamp,
                        )
                    )

                    maybe_credit = self._build_credit_or_discount_row(
                        usage_day=usage_day,
                        account_index=account_index,
                        linked_account_id=linked_account_id,
                        service_profile=service_profile,
                        batch_id=batch_id,
                        generation_timestamp=generation_timestamp,
                    )
                    if maybe_credit is not None:
                        rows.append(maybe_credit)

        dataframe = pd.DataFrame(rows)
        dataframe.sort_values(["usage_start_time", "linked_account_id", "service"], inplace=True)
        dataframe.reset_index(drop=True, inplace=True)
        return dataframe

    def _build_usage_row(
        self,
        usage_day: date,
        account_index: int,
        linked_account_id: str,
        service_profile: dict[str, Any],
        batch_id: str,
        generation_timestamp: datetime,
    ) -> dict[str, Any]:
        """Create a single usage billing row."""

        tags = generate_tag_bundle(
            rng=self.rng,
            imperfect_tag_rate=self.config.imperfect_tag_rate,
            account_index=account_index,
        )
        environment = tags.environment or "prod"
        resource_id = self._resource_id(account_index, service_profile["service"])
        region = self.rng.choice(self.config.regions)

        base_multiplier = (
            monthly_multiplier(usage_day)
            * weekday_multiplier(usage_day)
            * event_multiplier(usage_day, self._events)
            * environment_multiplier(environment)
        )
        random_noise = self.rng.uniform(0.94, 1.08)
        event_noise = 1.0 + (self.config.event_spike_rate * self.rng.random())
        gross_cost = service_profile["base_cost"] * base_multiplier * random_noise * event_noise
        gross_usage_amount = (
            service_profile["base_usage_amount"]
            * base_multiplier
            * self.rng.uniform(0.91, 1.09)
        )

        usage_start_time = datetime.combine(
            usage_day,
            time(hour=0, minute=0),
            tzinfo=timezone.utc,
        )
        usage_end_time = usage_start_time + timedelta(days=1)
        billing_period_start = datetime.combine(
            usage_day.replace(day=1),
            time.min,
            tzinfo=timezone.utc,
        )
        invoice_date = (usage_day.replace(day=1) + timedelta(days=32)).replace(day=5)

        blended_cost = round(gross_cost * self.rng.uniform(0.97, 1.0), 4)
        unblended_cost = round(gross_cost, 4)
        line_item_id = (
            f"{batch_id}-{linked_account_id}-"
            f"{service_profile['service']}-{usage_day.isoformat()}"
        )

        return {
            "line_item_id": line_item_id,
            "billing_period_start": billing_period_start,
            "usage_start_time": usage_start_time,
            "usage_end_time": usage_end_time,
            "invoice_date": invoice_date,
            "cloud_provider": "aws",
            "payer_account_id": self.config.payer_account_id,
            "linked_account_id": linked_account_id,
            "service": service_profile["service"],
            "usage_type": service_profile["usage_type"],
            "operation": service_profile["operation"],
            "region": region,
            "resource_id": resource_id,
            "line_item_type": "Usage",
            "usage_amount": round(gross_usage_amount, 4),
            "currency_code": "USD",
            "unblended_cost": unblended_cost,
            "blended_cost": blended_cost,
            "discount_type": "none",
            **asdict(tags),
            "accounting_policy_version": self.config.accounting_policy_version,
            "generator_batch_id": batch_id,
            "generated_at": generation_timestamp,
        }

    def _build_credit_or_discount_row(
        self,
        usage_day: date,
        account_index: int,
        linked_account_id: str,
        service_profile: dict[str, Any],
        batch_id: str,
        generation_timestamp: datetime,
    ) -> dict[str, Any] | None:
        """Create an occasional credit or discount row."""

        if self.rng.random() >= self.config.credit_row_rate:
            return None

        usage_start_time = datetime.combine(
            usage_day,
            time(hour=0, minute=0),
            tzinfo=timezone.utc,
        )
        usage_end_time = usage_start_time + timedelta(days=1)
        billing_period_start = datetime.combine(
            usage_day.replace(day=1),
            time.min,
            tzinfo=timezone.utc,
        )
        invoice_date = (usage_day.replace(day=1) + timedelta(days=32)).replace(day=5)
        tags = generate_tag_bundle(
            rng=self.rng,
            imperfect_tag_rate=self.config.imperfect_tag_rate,
            account_index=account_index,
        )
        discount_type = self.rng.choice(
            [
                "promotional_credit",
                "enterprise_discount",
                "sustained_use_discount",
            ]
        )
        magnitude = round(service_profile["base_cost"] * self.rng.uniform(0.04, 0.18) * -1, 4)
        line_item_type = "Credit" if discount_type == "promotional_credit" else "Discount"

        return {
            "line_item_id": (
                f"{batch_id}-{linked_account_id}-"
                f"{service_profile['service']}-{usage_day.isoformat()}-{discount_type}"
            ),
            "billing_period_start": billing_period_start,
            "usage_start_time": usage_start_time,
            "usage_end_time": usage_end_time,
            "invoice_date": invoice_date,
            "cloud_provider": "aws",
            "payer_account_id": self.config.payer_account_id,
            "linked_account_id": linked_account_id,
            "service": service_profile["service"],
            "usage_type": service_profile["usage_type"],
            "operation": service_profile["operation"],
            "region": self.rng.choice(self.config.regions),
            "resource_id": self._resource_id(account_index, service_profile["service"]),
            "line_item_type": line_item_type,
            "usage_amount": 0.0,
            "currency_code": "USD",
            "unblended_cost": magnitude,
            "blended_cost": magnitude,
            "discount_type": discount_type,
            **asdict(tags),
            "accounting_policy_version": self.config.accounting_policy_version,
            "generator_batch_id": batch_id,
            "generated_at": generation_timestamp,
        }

    def _resource_id(self, account_index: int, service: str) -> str:
        """Return a stable synthetic resource identifier for an account and service."""

        key = (account_index, service)
        if key not in self._resource_cache:
            prefix = RESOURCE_PREFIX[service]
            self._resource_cache[key] = f"{prefix}{self.faker.lexify(text='????????')}".lower()
        return self._resource_cache[key]

    def _build_event_calendar(self) -> list[DemandEvent]:
        """Build deterministic business events that create demand spikes."""

        start_day = self.config.run_date - timedelta(days=self.config.days - 1)
        mid_year = date(start_day.year, 7, 15)
        quarter_close = date(start_day.year, 11, 20)

        return [
            DemandEvent(
                name="summer-product-launch",
                start_date=mid_year - timedelta(days=3),
                end_date=mid_year + timedelta(days=4),
                multiplier=1.32,
            ),
            DemandEvent(
                name="holiday-traffic-ramp",
                start_date=quarter_close - timedelta(days=5),
                end_date=quarter_close + timedelta(days=8),
                multiplier=1.24,
            ),
        ]

    def _build_batch_id(self, generation_timestamp: datetime) -> str:
        """Build a stable batch identifier for a single generation run."""

        return generation_timestamp.strftime("batch-%Y%m%dT%H%M%SZ")
