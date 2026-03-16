from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def success_response(data: dict[str, Any], *, status_code: int = 200) -> tuple[dict[str, Any], int]:
    return {"status": "success", "data": data}, status_code


def error_response(message: str, code: str, *, status_code: int) -> tuple[dict[str, Any], int]:
    return {"status": "error", "message": message, "code": code}, status_code


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def category_from_aqi(aqi: int | float | None) -> str:
    if aqi is None:
        return "Unavailable"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"
