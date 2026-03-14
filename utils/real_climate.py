from __future__ import annotations

import gzip
import io
import math
import os
import tempfile
from typing import Any

import numpy as np
import pandas as pd
import requests
import streamlit as st
import xarray as xr


NASA_GISTEMP_GLOBAL_CSV_URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
NASA_GISTEMP_ZONAL_CSV_URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts+dSST.csv"
NASA_GISTEMP_GRID_URL = "https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz"
NASA_EONET_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

REQUEST_HEADERS = {"User-Agent": "ATLAS-Climate-Intelligence/1.0"}
MONTH_COLUMNS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _request_text(url: str, timeout: int = 45) -> str:
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def _request_bytes(url: str, timeout: int = 90) -> bytes:
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.content


def _extract_point(geometry: dict[str, Any]) -> tuple[float | None, float | None]:
    if not geometry:
        return None, None
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Point" and isinstance(coords, list) and len(coords) >= 2:
        return float(coords[0]), float(coords[1])
    if geom_type == "Polygon" and isinstance(coords, list) and coords:
        ring = coords[0]
        if ring:
            lons = [float(item[0]) for item in ring]
            lats = [float(item[1]) for item in ring]
            return float(np.mean(lons)), float(np.mean(lats))
    return None, None


@st.cache_data(show_spinner=False, ttl=86400)
def load_nasa_gistemp_gridded() -> xr.DataArray | None:
    try:
        archive_bytes = _request_bytes(NASA_GISTEMP_GRID_URL)
        dataset_bytes = gzip.decompress(archive_bytes)
        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as temp_file:
            temp_file.write(dataset_bytes)
            temp_path = temp_file.name
        try:
            with xr.open_dataset(temp_path, decode_times=True, mask_and_scale=True) as dataset:
                data_array = dataset["tempanomaly"].load()
        finally:
            os.unlink(temp_path)
    except Exception:
        return None

    if set(data_array.dims) >= {"time", "lat", "lon"}:
        data_array = data_array.transpose("time", "lat", "lon")
    elif set(data_array.dims) >= {"time", "latitude", "longitude"}:
        data_array = data_array.rename({"latitude": "lat", "longitude": "lon"}).transpose("time", "lat", "lon")

    data_array = data_array.astype("float32")
    data_array.attrs = dict(data_array.attrs)
    data_array.attrs["units"] = "deg C anomaly"
    data_array.attrs["long_name"] = "NASA GISTEMP Temperature Anomaly"
    data_array.attrs["source"] = "NASA GISS GISTEMP v4"
    return data_array


@st.cache_data(show_spinner=False, ttl=86400)
def load_nasa_gistemp_global_means() -> dict[str, pd.DataFrame] | None:
    try:
        csv_text = _request_text(NASA_GISTEMP_GLOBAL_CSV_URL)
        annual_frame = pd.read_csv(io.StringIO(csv_text), skiprows=1, na_values="***")
    except Exception:
        return None

    annual_frame = annual_frame.rename(columns={"Year": "year"})
    annual_frame["year"] = pd.to_numeric(annual_frame["year"], errors="coerce")
    annual_frame = annual_frame.dropna(subset=["year"]).copy()
    annual_frame["year"] = annual_frame["year"].astype(int)

    monthly_frame = annual_frame[["year", *MONTH_COLUMNS]].copy()
    monthly_frame = monthly_frame.melt(id_vars="year", value_vars=MONTH_COLUMNS, var_name="month_name", value_name="anomaly")
    monthly_frame["month"] = monthly_frame["month_name"].map({name: index + 1 for index, name in enumerate(MONTH_COLUMNS)})
    monthly_frame["time"] = pd.to_datetime(dict(year=monthly_frame["year"], month=monthly_frame["month"], day=1))
    monthly_frame = monthly_frame.dropna(subset=["anomaly"]).sort_values("time").reset_index(drop=True)

    annual_series = annual_frame[["year", "J-D"]].rename(columns={"J-D": "anomaly"}).dropna(subset=["anomaly"])
    annual_series["time"] = pd.to_datetime(annual_series["year"].astype(str) + "-01-01")
    annual_series = annual_series.sort_values("time").reset_index(drop=True)
    return {"monthly": monthly_frame, "annual": annual_series}


@st.cache_data(show_spinner=False, ttl=86400)
def load_nasa_gistemp_zonal_means() -> pd.DataFrame | None:
    try:
        csv_text = _request_text(NASA_GISTEMP_ZONAL_CSV_URL)
        frame = pd.read_csv(io.StringIO(csv_text), skiprows=1, na_values="***")
    except Exception:
        return None

    frame = frame.rename(columns={"Year": "year"})
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame = frame.dropna(subset=["year"]).copy()
    frame["year"] = frame["year"].astype(int)
    frame["time"] = pd.to_datetime(frame["year"].astype(str) + "-01-01")
    return frame.sort_values("time").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def load_nasa_eonet_events(limit: int = 15) -> pd.DataFrame:
    try:
        response = requests.get(
            NASA_EONET_EVENTS_URL,
            params={"status": "open", "limit": limit, "category": "severeStorms,wildfires"},
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return pd.DataFrame(columns=["title", "category", "lat", "lon", "date"])

    rows: list[dict[str, Any]] = []
    for event in payload.get("events", []):
        geometry_items = event.get("geometry", [])
        geometry = geometry_items[-1] if geometry_items else {}
        lon, lat = _extract_point(geometry)
        if lat is None or lon is None:
            continue
        categories = event.get("categories", [])
        rows.append(
            {
                "title": event.get("title", "Unnamed event"),
                "category": categories[0].get("title", "Event") if categories else "Event",
                "lat": lat,
                "lon": lon,
                "date": pd.to_datetime(geometry.get("date")).tz_localize(None) if geometry.get("date") else pd.NaT,
            }
        )
    return pd.DataFrame(rows)


def get_real_temperature_array(fallback_array) -> tuple[Any, str]:
    real_array = load_nasa_gistemp_gridded()
    if real_array is not None:
        return real_array, "NASA GISS GISTEMP v4"
    return fallback_array, "Bundled ATLAS climate workspace"


def get_real_global_temperature_frames() -> tuple[pd.DataFrame | None, pd.DataFrame | None, str]:
    payload = load_nasa_gistemp_global_means()
    if payload is None:
        return None, None, "Bundled ATLAS climate workspace"
    return payload["monthly"], payload["annual"], "NASA GISS GISTEMP v4"


def build_projection_scenarios(observed_df: pd.DataFrame, value_column: str) -> dict[str, pd.DataFrame]:
    ordered = observed_df[["time", value_column]].dropna().sort_values("time").reset_index(drop=True)
    if ordered.empty:
        empty = pd.DataFrame(columns=["time", "value"])
        return {"low_emissions": empty, "medium_emissions": empty, "high_emissions": empty}

    ordered["time"] = pd.to_datetime(ordered["time"])
    recent = ordered.tail(min(len(ordered), 30)).copy()
    x_values = np.arange(len(recent), dtype=float)
    slope = np.polyfit(x_values, recent[value_column], 1)[0] if len(recent) > 1 else 0.02
    last_time = ordered["time"].iloc[-1]
    horizon = 30
    future_times = pd.date_range(last_time + pd.DateOffset(years=1), periods=horizon, freq="YS")
    scenario_factors = {"low_emissions": 0.45, "medium_emissions": 0.8, "high_emissions": 1.2}

    scenarios: dict[str, pd.DataFrame] = {}
    last_value = float(ordered[value_column].iloc[-1])
    for name, factor in scenario_factors.items():
        values = [last_value + slope * factor * (index + 1) for index in range(horizon)]
        scenarios[name] = pd.DataFrame({"time": future_times, "value": values})
    return scenarios
