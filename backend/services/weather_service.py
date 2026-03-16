from __future__ import annotations

from typing import Any

import requests

from config import Config
from utils.cache import build_cache_key, get_cached, set_cached
from utils.logger import logger


WEATHER_CODE_MAP = {
    0: "Clear",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow",
    80: "Rain Showers",
    95: "Thunderstorm",
}


def fetch_weather(lat: float, lon: float) -> dict[str, Any]:
    cache_key = build_cache_key("weather", lat, lon)
    cached = get_cached("weather", cache_key)
    if cached:
        logger.debug("Weather cache hit", extra={"service": "weather", "cache_key": cache_key})
        return {"status": "success", "data": cached}

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "forecast_days": 2,
                "timezone": "auto",
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        logger.error("Weather request failed", extra={"service": "weather", "url": "open-meteo", "event": "api_errors"})
        return {"status": "error", "message": "Weather data temporarily unavailable", "code": "WEATHER_UNAVAILABLE"}

    current = payload.get("current", {})
    hourly = payload.get("hourly", {})
    formatted = {
        "current": {
            "temperature": current.get("temperature_2m"),
            "unit": "°C",
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_unit": "km/h",
            "weather_code": current.get("weather_code"),
            "description": WEATHER_CODE_MAP.get(current.get("weather_code"), "Unknown"),
            "timestamp": current.get("time"),
        },
        "hourly_forecast": {
            "time": (hourly.get("time") or [])[:24],
            "temperature_2m": (hourly.get("temperature_2m") or [])[:24],
            "relative_humidity_2m": (hourly.get("relative_humidity_2m") or [])[:24],
            "precipitation": (hourly.get("precipitation") or [])[:24],
            "wind_speed_10m": (hourly.get("wind_speed_10m") or [])[:24],
        },
    }
    set_cached("weather", cache_key, formatted)
    return {"status": "success", "data": formatted}
