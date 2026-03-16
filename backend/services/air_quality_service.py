from __future__ import annotations

from typing import Any

import requests

from config import Config
from models.schemas import category_from_aqi
from utils.cache import build_cache_key, get_cached, set_cached
from utils.logger import logger


def fetch_air_quality(lat: float, lon: float) -> dict[str, Any]:
    if not Config.WAQI_API_KEY:
        return {"status": "error", "message": "Air quality data unavailable for this location", "code": "AQI_UNAVAILABLE"}

    cache_key = build_cache_key("air_quality", lat, lon)
    cached = get_cached("air_quality", cache_key)
    if cached:
        logger.debug("AQI cache hit", extra={"service": "air_quality", "cache_key": cache_key})
        return {"status": "success", "data": cached}

    try:
        response = requests.get(
            f"https://api.waqi.info/feed/geo:{lat};{lon}/",
            params={"token": Config.WAQI_API_KEY},
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        logger.error("AQI request failed", extra={"service": "air_quality", "url": "waqi", "event": "api_errors"})
        return {"status": "error", "message": "Air quality data unavailable for this location", "code": "AQI_UNAVAILABLE"}

    if payload.get("status") != "ok":
        return {"status": "error", "message": "Air quality data unavailable for this location", "code": "AQI_UNAVAILABLE"}

    data = payload.get("data", {})
    iaqi = data.get("iaqi", {})
    pollutants = {
        "pm25": _extract_component(iaqi, "pm25"),
        "pm10": _extract_component(iaqi, "pm10"),
        "o3": _extract_component(iaqi, "o3"),
        "no2": _extract_component(iaqi, "no2"),
        "so2": _extract_component(iaqi, "so2"),
        "co": _extract_component(iaqi, "co"),
    }
    formatted = {
        "aqi": data.get("aqi"),
        "category": category_from_aqi(data.get("aqi")),
        "dominant_pollutant": data.get("dominentpol", ""),
        "pollutants": pollutants,
        "timestamp": (data.get("time") or {}).get("iso"),
    }
    set_cached("air_quality", cache_key, formatted)
    return {"status": "success", "data": formatted}


def _extract_component(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if isinstance(value, dict):
        return value.get("v")
    return None
