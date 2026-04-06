"""Deterministic usage pattern helpers for synthetic billing generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DemandEvent:
    """Represents a temporary demand shock in the generated billing dataset."""

    name: str
    start_date: date
    end_date: date
    multiplier: float


MONTHLY_MULTIPLIERS = {
    1: 1.08,
    2: 0.97,
    3: 1.01,
    4: 1.03,
    5: 1.06,
    6: 0.98,
    7: 1.10,
    8: 1.12,
    9: 1.04,
    10: 1.07,
    11: 1.15,
    12: 1.22,
}


def monthly_multiplier(day: date) -> float:
    """Return the seasonal multiplier for a given month."""

    return MONTHLY_MULTIPLIERS[day.month]


def weekday_multiplier(day: date) -> float:
    """Return a weekday versus weekend multiplier."""

    if day.weekday() >= 5:
        return 0.82
    return 1.0


def event_multiplier(day: date, events: list[DemandEvent]) -> float:
    """Return the product of all active event multipliers for a date."""

    multiplier = 1.0
    for event in events:
        if event.start_date <= day <= event.end_date:
            multiplier *= event.multiplier
    return multiplier


def environment_multiplier(environment: str) -> float:
    """Return a cost multiplier driven by environment semantics."""

    if environment == "prod":
        return 1.15
    if environment == "staging":
        return 0.85
    if environment == "test":
        return 0.65
    if environment == "sandbox":
        return 0.55
    return 1.0
