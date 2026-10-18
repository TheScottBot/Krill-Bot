"""Pure time-of-day grammar and daily occurrence arithmetic for posts and resets."""

from __future__ import annotations

import re
from datetime import UTC, datetime, time, timedelta, tzinfo

# Comfortably longer than any way of writing a time of day, so it bounds input
# from Discord and the environment file before the pattern reads it.
MAXIMUM_CLOCK_TEXT_LENGTH = 16

_CLOCK_PATTERN = re.compile(r"\s*(\d{1,2})(?:[:.]?(\d{2}))?\s*(am|pm)?\s*")


def parse_clock(supplied_text: str) -> str | None:
    """Read 17:00, 5pm, 6:30pm or 0930 as HH:MM, or return None for anything else."""
    if len(supplied_text) > MAXIMUM_CLOCK_TEXT_LENGTH:
        return None
    clock_match = _CLOCK_PATTERN.fullmatch(supplied_text.lower())
    if clock_match is None:
        return None
    hour = int(clock_match.group(1))
    minute = int(clock_match.group(2) or 0)
    meridiem = clock_match.group(3)
    if meridiem is not None:
        if not 1 <= hour <= 12:
            return None
        hour = hour % 12 + (12 if meridiem == "pm" else 0)
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"


def _occurrence_on(clock: str, local_date: datetime, zone: tzinfo) -> datetime:
    hour_text, minute_text = clock.split(":")
    local_occurrence = datetime.combine(
        local_date.date(), time(int(hour_text), int(minute_text)), tzinfo=zone
    )
    # Comparing in UTC matters: aware datetimes sharing one zone compare by wall
    # clock, which misorders instants either side of a summer-time change.
    return local_occurrence.astimezone(UTC)


def next_occurrence(clock: str, after: datetime, zone: tzinfo) -> datetime:
    """Return the first UTC instant strictly after `after` when the local clock shows `clock`."""
    local_after = after.astimezone(zone)
    candidate = _occurrence_on(clock, local_after, zone)
    if candidate <= after.astimezone(UTC):
        candidate = _occurrence_on(clock, local_after + timedelta(days=1), zone)
    return candidate


def previous_occurrence(clock: str, at_or_before: datetime, zone: tzinfo) -> datetime:
    """Return the latest UTC instant, at or before the given one, when the clock shows `clock`."""
    local_instant = at_or_before.astimezone(zone)
    candidate = _occurrence_on(clock, local_instant, zone)
    if candidate > at_or_before.astimezone(UTC):
        candidate = _occurrence_on(clock, local_instant - timedelta(days=1), zone)
    return candidate
