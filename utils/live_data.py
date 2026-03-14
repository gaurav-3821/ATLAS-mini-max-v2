from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
import os
import re
from typing import Any

import pandas as pd
import requests
import streamlit as st


OPENWEATHER_SESSION_KEY = "atlas_openweather_api_key"
NOAA_SESSION_KEY = "atlas_noaa_api_token"
NASA_SESSION_KEY = "atlas_nasa_earthdata_token"
COPERNICUS_SESSION_KEY = "atlas_copernicus_api_key"
GEE_SESSION_KEY = "atlas_gee_project_id"

OPENWEATHER_SECRET_NAMES = (
    "OPENWEATHER_API_KEY",
    "OPEN_WEATHER_API_KEY",
    "OPEN_WEATHER_MAP_API_KEY",
    "OWM_API_KEY",
)
NOAA_SECRET_NAMES = (
    "NOAA_API_TOKEN",
    "NOAA_CDO_API_TOKEN",
    "NOAA_TOKEN",
)
NASA_SECRET_NAMES = (
    "NASA_EARTHDATA_TOKEN",
    "EARTHDATA_TOKEN",
    "NASA_TOKEN",
)
COPERNICUS_SECRET_NAMES = (
    "COPERNICUS_CDS_API_KEY",
    "COPERNICUS_API_KEY",
    "CDSAPI_KEY",
)
GEE_SECRET_NAMES = (
    "GOOGLE_EARTH_ENGINE_PROJECT",
    "GEE_PROJECT_ID",
)
RUNTIME_CREDENTIAL_FLAG_NAMES = (
    "ATLAS_ENABLE_RUNTIME_CREDENTIAL_INPUTS",
    "ATLAS_ALLOW_RUNTIME_CREDENTIAL_INPUTS",
)
DEFAULT_LOCATION_SECRET_NAMES = (
    "ATLAS_DEFAULT_LOCATION",
    "ATLAS_LOCATION",
)

DIAGNOSTIC_LOCATION = {
    "label": "San Francisco, CA, US",
    "lat": 37.7749,
    "lon": -122.4194,
}

SATELLITE_LAYERS: dict[str, dict[str, str]] = {
    "Terra True Color": {
        "layer": "MODIS_Terra_CorrectedReflectance_TrueColor",
        "description": "Natural color MODIS imagery from the Terra satellite.",
    },
    "Aqua True Color": {
        "layer": "MODIS_Aqua_CorrectedReflectance_TrueColor",
        "description": "Natural color MODIS imagery from the Aqua satellite.",
    },
    "VIIRS True Color": {
        "layer": "VIIRS_SNPP_CorrectedReflectance_TrueColor",
        "description": "Natural color VIIRS imagery for high-frequency monitoring.",
    },
}

AQI_LABELS = {
    1: "Good",
    2: "Fair",
    3: "Moderate",
    4: "Poor",
    5: "Very poor",
}

COORDINATE_QUERY = re.compile(
    r"^\s*(?P<lat>-?\d+(?:\.\d+)?)\s*,\s*(?P<lon>-?\d+(?:\.\d+)?)\s*$"
)

REQUEST_HEADERS = {"User-Agent": "ATLAS-Climate-Intelligence/1.0"}
DEMO_LOCATION = {"name": "New Delhi", "state": "Delhi", "country": "IN", "lat": 28.6139, "lon": 77.2090}
DEMO_LOCATIONS = {
    "new delhi": {"name": "New Delhi", "state": "Delhi", "country": "IN", "lat": 28.6139, "lon": 77.2090},
    "delhi": {"name": "New Delhi", "state": "Delhi", "country": "IN", "lat": 28.6139, "lon": 77.2090},
    "san francisco": {"name": "San Francisco", "state": "California", "country": "US", "lat": 37.7749, "lon": -122.4194},
    "new york": {"name": "New York", "state": "New York", "country": "US", "lat": 40.7128, "lon": -74.0060},
    "london": {"name": "London", "state": "", "country": "GB", "lat": 51.5072, "lon": -0.1276},
    "tokyo": {"name": "Tokyo", "state": "", "country": "JP", "lat": 35.6762, "lon": 139.6503},
    "paris": {"name": "Paris", "state": "", "country": "FR", "lat": 48.8566, "lon": 2.3522},
}


def _session_value(key: str) -> str | None:
    try:
        value = st.session_state.get(key)
    except Exception:
        return None
    return str(value).strip() if value else None


def _secret_value(names: tuple[str, ...]) -> str | None:
    for name in names:
        env_value = os.getenv(name)
        if env_value:
            return env_value.strip()

    try:
        secrets = st.secrets
    except Exception:
        return None

    for name in names:
        if name in secrets and secrets[name]:
            return str(secrets[name]).strip()
        lowered = name.lower()
        if lowered in secrets and secrets[lowered]:
            return str(secrets[lowered]).strip()
    return None


def _demo_location_for_query(query: str) -> dict[str, Any]:
    lowered = query.strip().lower()
    for key, value in DEMO_LOCATIONS.items():
        if key in lowered:
            label_parts = [value["name"]]
            if value["state"]:
                label_parts.append(value["state"])
            if value["country"]:
                label_parts.append(value["country"])
            return {
                "query": query,
                "label": ", ".join(label_parts),
                "name": value["name"],
                "state": value["state"],
                "country": value["country"],
                "lat": value["lat"],
                "lon": value["lon"],
            }

    fallback = DEMO_LOCATION
    return {
        "query": query,
        "label": f"{fallback['name']}, {fallback['state']}, {fallback['country']}",
        "name": fallback["name"],
        "state": fallback["state"],
        "country": fallback["country"],
        "lat": fallback["lat"],
        "lon": fallback["lon"],
    }


def _demo_weather(lat: float, lon: float) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    seasonal = math.sin((now.timetuple().tm_yday / 365.0) * 2.0 * math.pi)
    spatial = math.cos(math.radians(lat)) * 6.0 - math.sin(math.radians(lon)) * 1.5
    temperature = 24.0 + seasonal * 4.5 + spatial
    humidity = max(28.0, min(88.0, 62.0 - spatial * 2.2))
    wind = max(1.2, 4.8 + math.sin(math.radians(lat + lon)) * 2.4)
    pressure = 1008.0 + math.cos(math.radians(lat * 2.5)) * 4.5
    return {
        "temperature_c": float(round(temperature, 1)),
        "feels_like_c": float(round(temperature + 1.4, 1)),
        "humidity_pct": float(round(humidity, 1)),
        "pressure_hpa": float(round(pressure, 1)),
        "wind_mps": float(round(wind, 1)),
        "visibility_km": 8.0,
        "condition": "Clear",
        "description": "demo clear sky",
        "icon": "01d",
        "precip_mm_1h": 0.0,
        "updated_at": now,
    }


def _demo_forecast(lat: float, lon: float) -> pd.DataFrame:
    base = _demo_weather(lat, lon)
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    rows: list[dict[str, Any]] = []
    for step in range(40):
        timestamp = start + timedelta(hours=3 * step)
        daily_wave = math.sin((step / 8.0) * math.pi)
        rows.append(
            {
                "time": pd.Timestamp(timestamp).tz_localize(None),
                "temperature_c": float(round(base["temperature_c"] + daily_wave * 3.2, 2)),
                "feels_like_c": float(round(base["feels_like_c"] + daily_wave * 3.5, 2)),
                "humidity_pct": float(round(max(30.0, min(92.0, base["humidity_pct"] + daily_wave * 8.0)), 2)),
                "wind_mps": float(round(max(1.0, base["wind_mps"] + math.cos(step / 4.0) * 1.4), 2)),
                "precip_probability_pct": float(round(max(5.0, min(95.0, 28.0 + (daily_wave + 1.0) * 24.0)), 2)),
            }
        )
    return pd.DataFrame(rows)


def _demo_air_quality(lat: float, lon: float) -> tuple[dict[str, Any], pd.DataFrame]:
    current = {
        "aqi": 2,
        "category": AQI_LABELS[2],
        "pm2_5": 18.0,
        "pm10": 28.0,
        "no2": 14.0,
        "o3": 22.0,
        "updated_at": datetime.now(timezone.utc),
    }
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    rows: list[dict[str, Any]] = []
    for step in range(96):
        timestamp = start + timedelta(hours=step)
        wave = math.sin(step / 6.0)
        aqi = 2 if wave < 0.5 else 3
        rows.append(
            {
                "time": pd.Timestamp(timestamp).tz_localize(None),
                "aqi": aqi,
                "category": AQI_LABELS[aqi],
                "pm2_5": float(round(16.0 + wave * 6.0, 2)),
                "pm10": float(round(26.0 + wave * 9.0, 2)),
                "no2": float(round(12.0 + wave * 4.0, 2)),
                "o3": float(round(20.0 + wave * 5.0, 2)),
            }
        )
    return current, pd.DataFrame(rows)


def _demo_noaa_history(lat: float, lon: float, days: int) -> dict[str, Any]:
    end_date = date.today()
    dates = pd.date_range(end=end_date, periods=days, freq="D")
    base_temp = _demo_weather(lat, lon)["temperature_c"]
    rows: list[dict[str, Any]] = []
    for index, timestamp in enumerate(dates):
        wave = math.sin(index / 3.5)
        rows.append(
            {
                "date": pd.Timestamp(timestamp).normalize(),
                "TAVG": float(round(base_temp + wave * 2.1, 2)),
                "TMAX": float(round(base_temp + 3.5 + wave * 2.4, 2)),
                "TMIN": float(round(base_temp - 3.8 + wave * 1.7, 2)),
                "PRCP": float(round(max(0.0, 4.0 + math.cos(index / 2.2) * 3.5), 2)),
            }
        )
    history = pd.DataFrame(rows)
    return {
        "station": {
            "id": "ATLAS-DEMO-001",
            "name": "ATLAS Demo Climate Station",
            "latitude": lat,
            "longitude": lon,
            "distance_km": 0.0,
        },
        "history": history,
    }


def _truthy(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def runtime_credential_entry_enabled() -> bool:
    return _truthy(_secret_value(RUNTIME_CREDENTIAL_FLAG_NAMES))


def get_default_location_query() -> str:
    return _secret_value(DEFAULT_LOCATION_SECRET_NAMES) or "New Delhi, IN"


def _configured_value(session_key: str, secret_names: tuple[str, ...]) -> str | None:
    secret = _secret_value(secret_names)
    if secret:
        return secret
    if runtime_credential_entry_enabled():
        return _session_value(session_key)
    return None


def get_openweather_api_key() -> str | None:
    return _configured_value(OPENWEATHER_SESSION_KEY, OPENWEATHER_SECRET_NAMES)


def get_noaa_api_token() -> str | None:
    return _configured_value(NOAA_SESSION_KEY, NOAA_SECRET_NAMES)


def get_nasa_earthdata_token() -> str | None:
    return _configured_value(NASA_SESSION_KEY, NASA_SECRET_NAMES)


def get_copernicus_api_key() -> str | None:
    return _configured_value(COPERNICUS_SESSION_KEY, COPERNICUS_SECRET_NAMES)


def get_gee_project_id() -> str | None:
    return _configured_value(GEE_SESSION_KEY, GEE_SECRET_NAMES)


def get_source_status() -> list[dict[str, str]]:
    return [
        {
            "name": "OpenWeather",
            "status": "Configured" if get_openweather_api_key() else "Demo fallback",
            "detail": "Current weather, five-day forecast, and air-quality intelligence with automatic demo fallback.",
        },
        {
            "name": "NOAA Climate Data Online",
            "status": "Configured" if get_noaa_api_token() else "Demo fallback",
            "detail": "Station search and recent daily summaries with demo fallback for reliable pages.",
        },
        {
            "name": "NASA GIBS",
            "status": "Live",
            "detail": "Satellite imagery snapshots from NASA Global Imagery Browse Services. No frontend key exposure required.",
        },
        {
            "name": "NetCDF Workspace",
            "status": "Ready",
            "detail": "Bundled climate grids plus uploaded datasets for deeper historical analysis.",
        },
    ]


def get_deferred_integrations() -> list[dict[str, str]]:
    return [
        {
            "name": "Copernicus Climate Data",
            "status": "Deferred",
            "detail": (
                "Excluded from the hackathon deploy profile so the live demo stays fast and reliable without "
                "adding extra auth and data-ingestion complexity."
            ),
        },
        {
            "name": "Google Earth Engine",
            "status": "Deferred",
            "detail": (
                "Not enabled in this deploy profile because Earth Engine requires OAuth or service-account "
                "authentication beyond a simple project id."
            ),
        },
    ]


def get_deploy_source_count() -> int:
    return len(get_source_status())


def _status_result(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def run_live_diagnostics() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    if get_openweather_api_key():
        try:
            weather = fetch_current_weather(DIAGNOSTIC_LOCATION["lat"], DIAGNOSTIC_LOCATION["lon"])
            forecast = fetch_forecast(DIAGNOSTIC_LOCATION["lat"], DIAGNOSTIC_LOCATION["lon"])
            air_current, air_forecast = fetch_air_quality(DIAGNOSTIC_LOCATION["lat"], DIAGNOSTIC_LOCATION["lon"])
            results.append(
                _status_result(
                    "OpenWeather",
                    "Pass",
                    (
                        f"{DIAGNOSTIC_LOCATION['label']} resolved with current weather, {len(forecast)} forecast rows, "
                        f"and AQI {air_current['aqi']} plus {len(air_forecast)} AQI forecast rows."
                    ),
                )
            )
        except Exception as exc:
            results.append(_status_result("OpenWeather", "Fail", str(exc)))
    else:
        results.append(_status_result("OpenWeather", "Skipped", "No server-side API key is configured."))

    if get_noaa_api_token():
        try:
            noaa_result = fetch_noaa_station_history(
                DIAGNOSTIC_LOCATION["lat"],
                DIAGNOSTIC_LOCATION["lon"],
                days=21,
            )
            station = noaa_result["station"]
            history = noaa_result["history"]
            results.append(
                _status_result(
                    "NOAA Climate Data Online",
                    "Pass",
                    f"Nearest station {station['name']} returned {len(history)} daily records.",
                )
            )
        except Exception as exc:
            results.append(_status_result("NOAA Climate Data Online", "Fail", str(exc)))
    else:
        results.append(_status_result("NOAA Climate Data Online", "Skipped", "No server-side API token is configured."))

    try:
        snapshot, meta = fetch_satellite_snapshot(
            DIAGNOSTIC_LOCATION["lat"],
            DIAGNOSTIC_LOCATION["lon"],
            image_date=date.today() - timedelta(days=1),
            layer_name="Terra True Color",
            span_degrees=10.0,
        )
        results.append(
            _status_result(
                "NASA GIBS",
                "Pass",
                f"Fetched {len(snapshot)} bytes from {meta['layer_name']} for {meta['image_date']}.",
            )
        )
    except Exception as exc:
        results.append(_status_result("NASA GIBS", "Fail", str(exc)))

    for item in get_deferred_integrations():
        results.append(item)

    return results


def _raise_for_status(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        message = ""
        try:
            payload = response.json()
            if isinstance(payload, dict):
                message = str(payload.get("message") or payload.get("errors") or "")
        except Exception:
            message = response.text[:240]
        detail = f"{response.status_code} {response.reason}"
        if message:
            detail = f"{detail}: {message}"
        raise RuntimeError(detail) from exc


def _request_json(
    url: str,
    *,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 25,
) -> Any:
    merged_headers = dict(REQUEST_HEADERS)
    if headers:
        merged_headers.update(headers)
    response = requests.get(url, params=params, headers=merged_headers, timeout=timeout)
    _raise_for_status(response)
    return response.json()


def _request_bytes(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 35,
) -> bytes:
    merged_headers = dict(REQUEST_HEADERS)
    if headers:
        merged_headers.update(headers)
    response = requests.get(url, params=params, headers=merged_headers, timeout=timeout)
    _raise_for_status(response)
    return response.content


def _normalize_location(query: str, payload: dict[str, Any]) -> dict[str, Any]:
    coord = payload.get("coord", {})
    sys_data = payload.get("sys", {})
    name = payload.get("name") or query
    state = payload.get("state")
    country = sys_data.get("country") or payload.get("country") or ""
    parts = [name]
    if state:
        parts.append(state)
    if country:
        parts.append(country)
    label = ", ".join([part for part in parts if part])
    return {
        "query": query,
        "label": label,
        "name": name,
        "state": state or "",
        "country": country,
        "lat": float(coord.get("lat", 0.0)),
        "lon": float(coord.get("lon", 0.0)),
    }


def _normalize_weather(payload: dict[str, Any]) -> dict[str, Any]:
    weather_items = payload.get("weather", [])
    weather_item = weather_items[0] if weather_items else {}
    main = payload.get("main", {})
    wind = payload.get("wind", {})
    visibility_m = payload.get("visibility")
    rain = payload.get("rain", {})
    snow = payload.get("snow", {})
    updated_at = payload.get("dt")
    return {
        "temperature_c": float(main.get("temp", 0.0)),
        "feels_like_c": float(main.get("feels_like", 0.0)),
        "humidity_pct": float(main.get("humidity", 0.0)),
        "pressure_hpa": float(main.get("pressure", 0.0)),
        "wind_mps": float(wind.get("speed", 0.0)),
        "visibility_km": (float(visibility_m) / 1000.0) if visibility_m is not None else None,
        "condition": str(weather_item.get("main", "Clear")),
        "description": str(weather_item.get("description", "No condition description")),
        "icon": str(weather_item.get("icon", "")),
        "precip_mm_1h": float(rain.get("1h", 0.0) or snow.get("1h", 0.0)),
        "updated_at": datetime.fromtimestamp(updated_at, tz=timezone.utc) if updated_at else None,
    }


@st.cache_data(show_spinner=False, ttl=900)
def _resolve_query_with_openweather(query: str, api_key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = _request_json(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": query, "appid": api_key, "units": "metric"},
    )
    return _normalize_location(query, payload), _normalize_weather(payload)


def resolve_location(query: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    coordinate_match = COORDINATE_QUERY.match(query)
    if coordinate_match:
        lat = float(coordinate_match.group("lat"))
        lon = float(coordinate_match.group("lon"))
        return (
            {
                "query": query,
                "label": f"{lat:.2f}, {lon:.2f}",
                "name": "Selected coordinates",
                "state": "",
                "country": "",
                "lat": lat,
                "lon": lon,
            },
            None,
        )

    api_key = get_openweather_api_key()
    if api_key:
        try:
            return _resolve_query_with_openweather(query, api_key)
        except Exception:
            pass
    demo_location = _demo_location_for_query(query)
    return demo_location, _demo_weather(demo_location["lat"], demo_location["lon"])


@st.cache_data(show_spinner=False, ttl=900)
def _fetch_current_weather(lat: float, lon: float, api_key: str) -> dict[str, Any]:
    payload = _request_json(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
    )
    return _normalize_weather(payload)


def fetch_current_weather(lat: float, lon: float) -> dict[str, Any]:
    api_key = get_openweather_api_key()
    if api_key:
        try:
            return _fetch_current_weather(lat, lon, api_key)
        except Exception:
            pass
    return _demo_weather(lat, lon)


@st.cache_data(show_spinner=False, ttl=900)
def _fetch_forecast(lat: float, lon: float, api_key: str) -> pd.DataFrame:
    payload = _request_json(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
    )
    rows: list[dict[str, Any]] = []
    for item in payload.get("list", []):
        if item.get("dt_txt"):
            timestamp = pd.to_datetime(item["dt_txt"], utc=True)
        else:
            timestamp = pd.to_datetime(item.get("dt"), unit="s", utc=True)
        rows.append(
            {
                "time": timestamp,
                "temperature_c": float(item.get("main", {}).get("temp", 0.0)),
                "feels_like_c": float(item.get("main", {}).get("feels_like", 0.0)),
                "humidity_pct": float(item.get("main", {}).get("humidity", 0.0)),
                "wind_mps": float(item.get("wind", {}).get("speed", 0.0)),
                "precip_probability_pct": float(item.get("pop", 0.0)) * 100.0,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["time"] = pd.to_datetime(frame["time"], utc=True).dt.tz_convert(None)
    return frame.sort_values("time").reset_index(drop=True)


def fetch_forecast(lat: float, lon: float) -> pd.DataFrame:
    api_key = get_openweather_api_key()
    if api_key:
        try:
            return _fetch_forecast(lat, lon, api_key)
        except Exception:
            pass
    return _demo_forecast(lat, lon)


@st.cache_data(show_spinner=False, ttl=900)
def _fetch_air_quality(lat: float, lon: float, api_key: str) -> tuple[dict[str, Any], pd.DataFrame]:
    current_payload = _request_json(
        "https://api.openweathermap.org/data/2.5/air_pollution",
        params={"lat": lat, "lon": lon, "appid": api_key},
    )
    forecast_payload = _request_json(
        "https://api.openweathermap.org/data/2.5/air_pollution/forecast",
        params={"lat": lat, "lon": lon, "appid": api_key},
    )

    current_item = (current_payload.get("list") or [{}])[0]
    current_components = current_item.get("components", {})
    current_aqi = int(current_item.get("main", {}).get("aqi", 0) or 0)
    current_summary = {
        "aqi": current_aqi,
        "category": AQI_LABELS.get(current_aqi, "Unknown"),
        "pm2_5": float(current_components.get("pm2_5", 0.0)),
        "pm10": float(current_components.get("pm10", 0.0)),
        "no2": float(current_components.get("no2", 0.0)),
        "o3": float(current_components.get("o3", 0.0)),
        "updated_at": datetime.fromtimestamp(current_item.get("dt", 0), tz=timezone.utc)
        if current_item.get("dt")
        else None,
    }

    rows: list[dict[str, Any]] = []
    for item in forecast_payload.get("list", []):
        components = item.get("components", {})
        aqi = int(item.get("main", {}).get("aqi", 0) or 0)
        rows.append(
            {
                "time": datetime.fromtimestamp(item.get("dt", 0), tz=timezone.utc),
                "aqi": aqi,
                "category": AQI_LABELS.get(aqi, "Unknown"),
                "pm2_5": float(components.get("pm2_5", 0.0)),
                "pm10": float(components.get("pm10", 0.0)),
                "no2": float(components.get("no2", 0.0)),
                "o3": float(components.get("o3", 0.0)),
            }
        )

    forecast_frame = pd.DataFrame(rows)
    if not forecast_frame.empty:
        forecast_frame["time"] = pd.to_datetime(forecast_frame["time"], utc=True).dt.tz_convert(None)
        forecast_frame = forecast_frame.sort_values("time").reset_index(drop=True)
    return current_summary, forecast_frame


def fetch_air_quality(lat: float, lon: float) -> tuple[dict[str, Any], pd.DataFrame]:
    api_key = get_openweather_api_key()
    if api_key:
        try:
            return _fetch_air_quality(lat, lon, api_key)
        except Exception:
            pass
    return _demo_air_quality(lat, lon)


def _haversine_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    radius_km = 6371.0
    lat_a_r = math.radians(lat_a)
    lon_a_r = math.radians(lon_a)
    lat_b_r = math.radians(lat_b)
    lon_b_r = math.radians(lon_b)
    d_lat = lat_b_r - lat_a_r
    d_lon = lon_b_r - lon_a_r
    value = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(lat_a_r) * math.cos(lat_b_r) * math.sin(d_lon / 2.0) ** 2
    )
    return 2.0 * radius_km * math.asin(math.sqrt(value))


@st.cache_data(show_spinner=False, ttl=21600)
def _find_noaa_station(lat: float, lon: float, token: str) -> dict[str, Any]:
    search_windows = [0.75, 1.5, 3.0, 6.0]
    for half_window in search_windows:
        extent = f"{lat - half_window},{lon - half_window},{lat + half_window},{lon + half_window}"
        payload = _request_json(
            "https://www.ncei.noaa.gov/cdo-web/api/v2/stations",
            params={"datasetid": "GHCND", "extent": extent, "limit": 50},
            headers={"token": token},
        )
        stations = payload.get("results", [])
        if not stations:
            continue

        ranked: list[dict[str, Any]] = []
        for station in stations:
            station_lat = float(station.get("latitude", 0.0))
            station_lon = float(station.get("longitude", 0.0))
            ranked.append(
                {
                    "id": station.get("id"),
                    "name": station.get("name"),
                    "latitude": station_lat,
                    "longitude": station_lon,
                    "distance_km": _haversine_km(lat, lon, station_lat, station_lon),
                }
            )
        ranked.sort(key=lambda item: item["distance_km"])
        return ranked[0]
    raise RuntimeError("NOAA did not return a nearby station for the selected location.")


@st.cache_data(show_spinner=False, ttl=3600)
def _fetch_noaa_history(
    station_id: str,
    start_date_iso: str,
    end_date_iso: str,
    token: str,
) -> pd.DataFrame:
    params: list[tuple[str, Any]] = [
        ("datasetid", "GHCND"),
        ("stationid", station_id),
        ("startdate", start_date_iso),
        ("enddate", end_date_iso),
        ("units", "metric"),
        ("limit", 1000),
    ]
    for datatype in ("TAVG", "TMAX", "TMIN", "PRCP"):
        params.append(("datatypeid", datatype))

    payload = _request_json(
        "https://www.ncei.noaa.gov/cdo-web/api/v2/data",
        params=params,
        headers={"token": token},
    )
    results = payload.get("results", [])
    if not results:
        return pd.DataFrame(columns=["date", "TAVG", "TMAX", "TMIN", "PRCP"])

    frame = pd.DataFrame(results)
    frame["date"] = pd.to_datetime(frame["date"]).dt.tz_localize(None).dt.normalize()
    pivot = (
        frame.pivot_table(index="date", columns="datatype", values="value", aggfunc="last")
        .reset_index()
        .sort_values("date")
        .reset_index(drop=True)
    )
    pivot.columns.name = None
    return pivot


def fetch_noaa_station_history(
    lat: float,
    lon: float,
    *,
    days: int = 45,
) -> dict[str, Any]:
    token = get_noaa_api_token()
    if token:
        try:
            station = _find_noaa_station(lat, lon, token)
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            history = _fetch_noaa_history(station["id"], start_date.isoformat(), end_date.isoformat(), token)
            if not history.empty:
                return {"station": station, "history": history}
        except Exception:
            pass
    return _demo_noaa_history(lat, lon, days)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _build_bbox(lat: float, lon: float, span_degrees: float) -> tuple[float, float, float, float]:
    half_span = span_degrees / 2.0
    south = _clamp(lat - half_span, -89.5, 89.5)
    north = _clamp(lat + half_span, -89.5, 89.5)
    west = _clamp(lon - half_span, -179.5, 179.5)
    east = _clamp(lon + half_span, -179.5, 179.5)
    return south, west, north, east


@st.cache_data(show_spinner=False, ttl=21600)
def _fetch_satellite_snapshot(
    lat: float,
    lon: float,
    image_date_iso: str,
    layer_id: str,
    span_degrees: float,
) -> bytes:
    south, west, north, east = _build_bbox(lat, lon, span_degrees)
    return _request_bytes(
        "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
        params={
            "SERVICE": "WMS",
            "REQUEST": "GetMap",
            "VERSION": "1.3.0",
            "FORMAT": "image/jpeg",
            "TRANSPARENT": "FALSE",
            "LAYERS": layer_id,
            "STYLES": "",
            "CRS": "EPSG:4326",
            "BBOX": f"{south},{west},{north},{east}",
            "WIDTH": 1280,
            "HEIGHT": 720,
            "TIME": image_date_iso,
        },
    )


def fetch_satellite_snapshot(
    lat: float,
    lon: float,
    *,
    image_date: date,
    layer_name: str,
    span_degrees: float = 8.0,
) -> tuple[bytes, dict[str, Any]]:
    layer = SATELLITE_LAYERS.get(layer_name, SATELLITE_LAYERS["Terra True Color"])
    snapshot = _fetch_satellite_snapshot(lat, lon, image_date.isoformat(), layer["layer"], span_degrees)
    south, west, north, east = _build_bbox(lat, lon, span_degrees)
    return snapshot, {
        "layer_name": layer_name,
        "layer_id": layer["layer"],
        "description": layer["description"],
        "image_date": image_date.isoformat(),
        "worldview_url": (
            "https://worldview.earthdata.nasa.gov/"
            f"?v={west},{south},{east},{north}&t={image_date.isoformat()}"
        ),
    }


def build_briefing_headline(
    location: dict[str, Any],
    weather: dict[str, Any],
    air_quality: dict[str, Any],
    station: dict[str, Any] | None,
) -> str:
    temperature = weather.get("temperature_c")
    aqi = air_quality.get("aqi")
    station_name = station["name"] if station else "no nearby NOAA station"
    return (
        f"{location['label']} is currently {weather.get('description', 'clear').lower()} at "
        f"{temperature:.1f} deg C. Air quality is {air_quality.get('category', 'unknown')} "
        f"(AQI {aqi}). NOAA ground truth is anchored to {station_name}."
    )
