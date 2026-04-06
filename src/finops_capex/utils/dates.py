"""Date parsing helpers for repository scripts."""

from __future__ import annotations

from datetime import date


def parse_iso_date(value: str) -> date:
    """Parse an ISO date string into a ``date`` instance."""

    return date.fromisoformat(value)
