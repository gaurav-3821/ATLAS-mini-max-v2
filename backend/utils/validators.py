from __future__ import annotations

import html
import re
from datetime import date, datetime, timedelta


CITY_PATTERN = re.compile(r"[^A-Za-z0-9\s\-\.',]")
SQL_PATTERN = re.compile(r"\b(select|insert|update|delete|drop|union|alter|create|truncate|table)\b", re.IGNORECASE)


def sanitize_city(city: str) -> str:
    cleaned = html.unescape(city or "").strip()
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = SQL_PATTERN.sub("", cleaned)
    cleaned = CITY_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def validate_city(city: str) -> tuple[bool, str | None, str | None]:
    cleaned = sanitize_city(city)
    if not cleaned:
        return False, None, "City is required"
    if len(cleaned) > 100:
        return False, None, "City must be 100 characters or fewer"
    return True, cleaned, None


def validate_coordinates(lat: str | float, lon: str | float) -> tuple[bool, tuple[float, float] | None, str | None]:
    try:
        latitude = float(lat)
        longitude = float(lon)
    except (TypeError, ValueError):
        return False, None, "Latitude and longitude must be valid numbers"

    if not -90 <= latitude <= 90:
        return False, None, "Latitude must be between -90 and 90"
    if not -180 <= longitude <= 180:
        return False, None, "Longitude must be between -180 and 180"
    return True, (latitude, longitude), None


def validate_date_range(
    start_date_raw: str | None,
    end_date_raw: str | None,
    *,
    max_past_days: int = 365,
    default_days: int = 30,
) -> tuple[bool, tuple[date, date] | None, str | None]:
    today = date.today()
    end_date = today if not end_date_raw else _parse_date(end_date_raw)
    start_date = today - timedelta(days=default_days) if not start_date_raw else _parse_date(start_date_raw)

    if end_date is None or start_date is None:
        return False, None, "Dates must be in YYYY-MM-DD format"
    if end_date > today or start_date > today:
        return False, None, "Dates cannot be in the future"
    if start_date > end_date:
        return False, None, "Start date must be before end date"
    if (end_date - start_date).days > max_past_days:
        return False, None, f"Date range cannot exceed {max_past_days} days"
    return True, (start_date, end_date), None


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
