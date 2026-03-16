from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import requests

from config import Config
from utils.cache import build_cache_key, get_cached, set_cached
from utils.logger import logger


def fetch_history(lat: float, lon: float, start_date: date | None = None, end_date: date | None = None) -> dict[str, Any]:
    end_value = end_date or date.today()
    start_value = start_date or (end_value - timedelta(days=30))
    current = _fetch_hourly_history(lat, lon, start_value, end_value)
    if current["status"] != "success":
        return current

    compare_start = start_value.replace(year=start_value.year - 1)
    compare_end = end_value.replace(year=end_value.year - 1)
    previous = _fetch_hourly_history(lat, lon, compare_start, compare_end)

    data = current["data"]
    data["comparison_period"] = {
        "start": compare_start.isoformat(),
        "end": compare_end.isoformat(),
        "daily_averages": previous.get("data", {}).get("daily_averages", {"dates": [], "temperature": [], "precipitation": []}),
    }
    return {"status": "success", "data": data}


def _fetch_hourly_history(lat: float, lon: float, start_date: date, end_date: date) -> dict[str, Any]:
    cache_key = build_cache_key("historical", lat, lon, start_date.isoformat(), end_date.isoformat())
    cached = get_cached("historical", cache_key)
    if cached:
        logger.debug("History cache hit", extra={"service": "historical", "cache_key": cache_key})
        return {"status": "success", "data": cached}

    try:
        response = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "hourly": "temperature_2m,precipitation",
                "timezone": "auto",
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        logger.error("History request failed", extra={"service": "historical", "url": "open-meteo-archive", "event": "api_errors"})
        return {"status": "error", "message": "Historical climate data unavailable", "code": "HISTORY_UNAVAILABLE"}

    hourly = payload.get("hourly", {})
    dates = hourly.get("time") or []
    temperatures = hourly.get("temperature_2m") or []
    precipitation = hourly.get("precipitation") or []
    grouped: dict[str, dict[str, list[float]]] = {}
    for timestamp, temp, rain in zip(dates, temperatures, precipitation):
        day = str(timestamp).split("T", 1)[0]
        bucket = grouped.setdefault(day, {"temperature": [], "precipitation": []})
        if temp is not None:
            bucket["temperature"].append(float(temp))
        if rain is not None:
            bucket["precipitation"].append(float(rain))

    ordered_days = sorted(grouped.keys())
    daily_temp = [
        round(sum(grouped[day]["temperature"]) / len(grouped[day]["temperature"]), 2)
        if grouped[day]["temperature"]
        else 0.0
        for day in ordered_days
    ]
    daily_precip = [
        round(sum(grouped[day]["precipitation"]), 2) if grouped[day]["precipitation"] else 0.0
        for day in ordered_days
    ]
    formatted = {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "daily_averages": {
            "dates": ordered_days,
            "temperature": daily_temp,
            "precipitation": daily_precip,
        },
    }
    set_cached("historical", cache_key, formatted)
    return {"status": "success", "data": formatted}
