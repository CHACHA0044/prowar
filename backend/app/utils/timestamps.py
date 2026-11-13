"""
Datetime utilities for consistent UTC timestamp handling.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current datetime in UTC."""
    return datetime.now(timezone.utc)

