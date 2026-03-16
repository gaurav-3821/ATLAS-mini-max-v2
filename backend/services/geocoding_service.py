from __future__ import annotations

import time
from typing import Any

import requests

from config import Config
from utils.cache import build_cache_key, get_cached, set_cached
from utils.logger import logger


_last_nominatim_request = 0.0


def geocode_city(city: str) -> dict[str, Any]:
    cache_key = build_cache_key("geocoding", city.lower())
    cached = get_cached("geocoding", cache_key)
    if cached:
        logger.debug("Geocoding cache hit", extra={"service": "geocoding", "cache_key": cache_key})
        return {"status": "success", "data": cached}

    global _last_nominatim_request
    elapsed = time.monotonic() - _last_nominatim_request
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "ATLAS Climate Intelligence Dashboard"},
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
        _last_nominatim_request = time.monotonic()
    except requests.RequestException:
        logger.error("Geocoding request failed", extra={"service": "geocoding", "url": "nominatim", "event": "api_errors"})
        return {"status": "error", "message": "Location service temporarily unavailable", "code": "LOCATION_SERVICE_UNAVAILABLE"}

    if not results:
        return {"status": "error", "message": "Location not found. Please check the city name.", "code": "LOCATION_NOT_FOUND"}

    item = results[0]
    address = item.get("address", {})
    payload = {
        "city": address.get("city") or address.get("town") or address.get("state") or city,
        "display_name": item.get("display_name", city),
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "country": address.get("country", ""),
    }
    set_cached("geocoding", cache_key, payload)
    return {"status": "success", "data": payload}
