from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
import xarray as xr


LAT_NAMES = ("lat", "latitude", "y")
LON_NAMES = ("lon", "longitude", "x")
TIME_NAMES = ("time", "date")

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"
DEMO_DATA_PATH = DATA_DIR / "demo_temperature.nc"

SESSION_BYTES_KEY = "atlas_uploaded_bytes"
SESSION_NAME_KEY = "atlas_uploaded_name"
SESSION_DATASET_KEY = "atlas_dataset_choice"

DATASET_CHOICES = {
    "ATLAS Demo (ERA5-style)": "Synthetic monthly reanalysis-like dataset for reliable demos.",
    "ERA5 Monthly Reanalysis": "Use uploaded or demo data while presenting the workflow as ERA5-compatible.",
    "CMIP6 Climate Model": "Use uploaded or demo data while presenting the workflow as CMIP6-compatible.",
    "CESM Simulation Output": "Use uploaded or demo data while presenting the workflow as CESM-compatible.",
}

REGION_BOUNDS: dict[str, dict[str, tuple[float, float] | None]] = {
    "Global": {"lat": None, "lon": None},
    "Asia": {"lat": (5.0, 55.0), "lon": (60.0, 150.0)},
    "Europe": {"lat": (35.0, 70.0), "lon": (-10.0, 40.0)},
    "North America": {"lat": (15.0, 75.0), "lon": (-170.0, -50.0)},
    "South America": {"lat": (-60.0, 15.0), "lon": (-90.0, -30.0)},
    "Africa": {"lat": (-35.0, 37.0), "lon": (-20.0, 55.0)},
    "Arctic": {"lat": (60.0, 90.0), "lon": None},
    "Antarctica": {"lat": (-90.0, -60.0), "lon": None},
}


def detect_axes(data_array: xr.DataArray) -> dict[str, str | None]:
    dims = {dim.lower(): dim for dim in data_array.dims}

    def match(candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if candidate in dims:
                return dims[candidate]
        return None

    return {"lat": match(LAT_NAMES), "lon": match(LON_NAMES), "time": match(TIME_NAMES)}


@st.cache_data(show_spinner=False)
def build_demo_dataset() -> xr.Dataset:
    time = pd.date_range("1950-01-01", "2023-12-01", freq="MS")
    lat = np.arange(-90.0, 90.1, 2.5)
    lon = np.arange(0.0, 360.0, 2.5)

    time_years = ((time.year + (time.month - 1) / 12.0).to_numpy(dtype=np.float32)) - np.float32(1950.0)
    t_idx = np.arange(len(time), dtype=np.float32)[:, None, None]
    lat_grid = lat[None, :, None]
    lon_grid = lon[None, None, :]

    abs_lat = np.abs(lat_grid)
    tropical_mask = np.exp(-((lat_grid / 12.0) ** 2))
    pacific_distance = np.minimum(np.abs(lon_grid - 220.0), 360.0 - np.abs(lon_grid - 220.0))
    pacific_mask = np.exp(-((pacific_distance / 35.0) ** 2))
    arctic_mask = np.clip((lat_grid - 55.0) / 35.0, 0.0, 1.0)

    base_temp = 300.0 - 48.0 * ((abs_lat / 90.0) ** 1.25)
    land_ocean_texture = 1.6 * np.sin(np.deg2rad(lon_grid * 1.5)) + 0.9 * np.cos(np.deg2rad(lon_grid * 0.7))

    seasonal_amplitude = 1.5 + 11.0 * np.sin(np.deg2rad(abs_lat)) ** 1.2
    hemisphere_phase = np.where(lat_grid >= 0.0, 0.0, np.pi)
    seasonal_cycle = seasonal_amplitude * np.sin((2.0 * np.pi * t_idx / 12.0) + hemisphere_phase)

    warming_base = 0.015 * time_years + 0.010 * np.clip(time_years - 30.0, 0.0, None)
    warming_base = warming_base[:, None, None]
    arctic_extra = warming_base * (1.5 * arctic_mask)

    enso_1998 = np.exp(-(((time_years - 48.0) / 0.75) ** 2))[:, None, None]
    enso_2016 = np.exp(-(((time_years - 66.0) / 0.80) ** 2))[:, None, None]
    pacific_spike = 0.55 * enso_1998 * (0.35 + tropical_mask * pacific_mask) + 0.40 * enso_2016 * (
        0.25 + tropical_mask * pacific_mask
    )

    record_2023 = np.clip((time_years - 72.4) / 0.6, 0.0, 1.0)[:, None, None] * 0.30

    rng = np.random.default_rng(404)
    spatial_noise = rng.normal(0.0, 0.55, size=(1, lat.size, lon.size))
    monthly_noise = rng.normal(0.0, 0.18, size=(len(time), 1, lon.size))
    zonal_noise = rng.normal(0.0, 0.14, size=(len(time), lat.size, 1))

    temperature = (
        base_temp
        + land_ocean_texture
        + seasonal_cycle
        + warming_base
        + arctic_extra
        + pacific_spike
        + record_2023
        + spatial_noise
        + monthly_noise
        + zonal_noise
    ).astype("float32")

    precipitation = (
        45.0
        + 145.0 * tropical_mask
        + 18.0 * np.cos(2.0 * np.pi * t_idx / 12.0)
        + 8.0 * np.sin(np.deg2rad(lon_grid))
        + 20.0 * pacific_spike
        + rng.normal(0.0, 6.0, size=(len(time), lat.size, lon.size))
    ).astype("float32")
    precipitation = np.clip(precipitation, 0.0, None)

    sea_level_pressure = (
        1013.0
        - 7.0 * np.cos(np.deg2rad(lat_grid * 2.0))
        + 2.2 * np.cos(np.deg2rad(lon_grid))
        - 2.0 * pacific_spike
        + rng.normal(0.0, 0.9, size=(len(time), lat.size, lon.size))
    ).astype("float32")

    wind_speed = (
        5.5
        + 4.0 * np.sin(np.deg2rad(abs_lat))
        + 1.2 * np.cos(np.deg2rad(lon_grid * 1.3))
        + 0.8 * np.sin(2.0 * np.pi * t_idx / 12.0)
        + 1.2 * arctic_mask
        + rng.normal(0.0, 0.35, size=(len(time), lat.size, lon.size))
    ).astype("float32")
    wind_speed = np.clip(wind_speed, 0.2, None)

    dataset = xr.Dataset(
        data_vars={
            "t2m": (("time", "lat", "lon"), temperature),
            "precipitation": (("time", "lat", "lon"), precipitation),
            "sea_level_pressure": (("time", "lat", "lon"), sea_level_pressure),
            "wind_speed": (("time", "lat", "lon"), wind_speed),
        },
        coords={"time": time, "lat": lat, "lon": lon},
        attrs={
            "title": "ATLAS synthetic climate demo dataset",
            "source": "Generated locally for offline demo reliability",
            "description": "Monthly climate fields with warming trend, Arctic amplification, ENSO spikes, and a 2023 record heat signal.",
        },
    )
    dataset["t2m"].attrs.update(long_name="2m Temperature", units="K")
    dataset["precipitation"].attrs.update(long_name="Precipitation", units="mm/month")
    dataset["sea_level_pressure"].attrs.update(long_name="Sea Level Pressure", units="hPa")
    dataset["wind_speed"].attrs.update(long_name="Wind Speed", units="m/s")
    return dataset


@st.cache_data(show_spinner=False)
def ensure_demo_dataset() -> str:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DEMO_DATA_PATH.exists():
        try:
            with xr.open_dataset(DEMO_DATA_PATH) as existing:
                required_vars = {"t2m", "precipitation", "sea_level_pressure", "wind_speed"}
                if required_vars <= set(existing.data_vars):
                    return str(DEMO_DATA_PATH)
        except Exception:
            pass

    dataset = build_demo_dataset()
    encoding = {name: {"zlib": True, "complevel": 4} for name in dataset.data_vars}
    try:
        dataset.to_netcdf(DEMO_DATA_PATH, engine="netcdf4", encoding=encoding)
    except Exception:
        dataset.to_netcdf(DEMO_DATA_PATH)
    return str(DEMO_DATA_PATH)


@st.cache_data(show_spinner=False)
def load_demo_dataset() -> xr.Dataset:
    ensure_demo_dataset()
    with xr.open_dataset(DEMO_DATA_PATH) as dataset:
        return dataset.load()


@st.cache_data(show_spinner=False)
def load_uploaded_dataset(file_bytes: bytes, file_name: str) -> xr.Dataset:
    suffix = Path(file_name).suffix.lower()
    if suffix not in {".nc", ".nc4", ".cdf", ".netcdf"}:
        raise ValueError("Upload a NetCDF file with a supported extension: .nc, .nc4, .cdf, or .netcdf.")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(file_bytes)
        temp_path = Path(temp_file.name)

    try:
        with xr.open_dataset(temp_path) as dataset:
            return dataset.load()
    finally:
        temp_path.unlink(missing_ok=True)


def register_uploaded_file(uploaded_file: Any) -> None:
    if uploaded_file is None:
        return
    st.session_state[SESSION_BYTES_KEY] = uploaded_file.getvalue()
    st.session_state[SESSION_NAME_KEY] = uploaded_file.name


def clear_uploaded_file() -> None:
    st.session_state.pop(SESSION_BYTES_KEY, None)
    st.session_state.pop(SESSION_NAME_KEY, None)


def get_dataset_choices() -> list[str]:
    return list(DATASET_CHOICES.keys())


def register_dataset_choice(choice: str) -> None:
    st.session_state[SESSION_DATASET_KEY] = choice


def get_dataset_choice() -> str:
    return st.session_state.get(SESSION_DATASET_KEY, get_dataset_choices()[0])


def get_active_dataset() -> tuple[xr.Dataset, str]:
    file_bytes = st.session_state.get(SESSION_BYTES_KEY)
    file_name = st.session_state.get(SESSION_NAME_KEY)
    dataset_choice = get_dataset_choice()
    if file_bytes and file_name:
        try:
            return load_uploaded_dataset(file_bytes, file_name), f"{dataset_choice} via upload ({file_name})"
        except Exception:
            clear_uploaded_file()
    return load_demo_dataset(), dataset_choice


def variable_options(dataset: xr.Dataset) -> list[str]:
    options: list[str] = []
    for name, data in dataset.data_vars.items():
        axes = detect_axes(data)
        if np.issubdtype(data.dtype, np.number) and all([axes["lat"], axes["lon"], axes["time"]]):
            options.append(name)
    return options


def get_time_values(data_array: xr.DataArray, axes: dict[str, str | None]) -> pd.DatetimeIndex:
    time_axis = axes["time"]
    if time_axis is None:
        return pd.DatetimeIndex([])
    return pd.to_datetime(data_array[time_axis].values)


def format_variable_label(data_array: xr.DataArray, variable_name: str) -> str:
    return str(data_array.attrs.get("long_name") or variable_name.replace("_", " ").title())


def format_variable_units(data_array: xr.DataArray) -> str:
    return str(data_array.attrs.get("units", ""))


def to_display_array(data_array: xr.DataArray, variable_name: str) -> xr.DataArray:
    display_array = data_array.copy()
    if variable_name == "t2m" and format_variable_units(display_array) in {"K", "Kelvin"}:
        display_array = display_array - 273.15
        display_array.attrs = dict(data_array.attrs)
        display_array.attrs["units"] = "deg C"
        display_array.attrs["long_name"] = "2m Temperature"
    return display_array


def variable_label_map(dataset: xr.Dataset) -> dict[str, str]:
    labels: dict[str, str] = {}
    for name in variable_options(dataset):
        labels[name] = format_variable_label(to_display_array(dataset[name], name), name)
    return labels


def to_mod360(values: xr.DataArray | np.ndarray) -> np.ndarray:
    arr = np.asarray(values)
    return np.mod(arr + 360.0, 360.0)


def subset_region(_data_array: xr.DataArray, axes: dict[str, str | None], region_name: str) -> xr.DataArray:
    region = REGION_BOUNDS.get(region_name, REGION_BOUNDS["Global"])
    subset = _data_array
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]

    if lat_axis and region["lat"] is not None:
        lat_min, lat_max = region["lat"]
        subset = subset.sel({lat_axis: slice(lat_min, lat_max)})

    if lon_axis and region["lon"] is not None:
        lon_min, lon_max = region["lon"]
        lon_values = xr.DataArray(
            to_mod360(subset[lon_axis].values),
            dims=(lon_axis,),
            coords={lon_axis: subset[lon_axis].values},
        )
        lon_min_mod = lon_min % 360.0
        lon_max_mod = lon_max % 360.0
        if lon_min_mod <= lon_max_mod:
            mask = (lon_values >= lon_min_mod) & (lon_values <= lon_max_mod)
        else:
            mask = (lon_values >= lon_min_mod) | (lon_values <= lon_max_mod)
        subset = subset.where(mask, drop=True)

    return subset


def prepare_map_slice(
    _data_array: xr.DataArray,
    axes: dict[str, str | None],
    selected_time: pd.Timestamp,
    region_name: str = "Global",
    anomaly_mode: bool = False,
) -> xr.DataArray:
    time_axis = axes["time"]
    if time_axis is None:
        raise ValueError("Selected variable does not have a time axis.")
    map_slice = _data_array.sel({time_axis: selected_time}, method="nearest")
    if anomaly_mode:
        map_slice = map_slice - _data_array.mean(dim=time_axis)
    return subset_region(map_slice, axes, region_name)


def nearest_point_series(
    _data_array: xr.DataArray,
    axes: dict[str, str | None],
    selected_lat: float,
    selected_lon: float,
    anomaly_mode: bool = False,
) -> xr.DataArray:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    time_axis = axes["time"]
    if lat_axis is None or lon_axis is None or time_axis is None:
        raise ValueError("The variable must include latitude, longitude, and time.")

    series = _data_array.sel({lat_axis: selected_lat, lon_axis: selected_lon}, method="nearest")
    if anomaly_mode:
        series = series - series.mean(dim=time_axis)
    return series


def period_mean(
    _data_array: xr.DataArray,
    axes: dict[str, str | None],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    region_name: str = "Global",
) -> xr.DataArray:
    time_axis = axes["time"]
    if time_axis is None:
        raise ValueError("Selected variable does not have a time axis.")
    subset = _data_array.sel({time_axis: slice(start_date, end_date)}).mean(dim=time_axis)
    return subset_region(subset, axes, region_name)


def annual_mean_series(
    _data_array: xr.DataArray,
    axes: dict[str, str | None],
    region_name: str = "Global",
    anomaly_mode: bool = False,
) -> xr.DataArray:
    time_axis = axes["time"]
    if time_axis is None:
        raise ValueError("Selected variable does not have a time axis.")

    annual = _data_array.groupby(f"{time_axis}.year").mean(dim=time_axis)
    if anomaly_mode:
        annual = annual - annual.mean(dim="year")
    return subset_region(annual, axes, region_name)


def spatial_mean_series(
    _data_array: xr.DataArray,
    axes: dict[str, str | None],
    region_name: str = "Global",
    anomaly_mode: bool = False,
) -> xr.DataArray:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    time_axis = axes["time"]
    if lat_axis is None or lon_axis is None or time_axis is None:
        raise ValueError("Selected variable does not have latitude, longitude, and time axes.")

    region_view = subset_region(_data_array, axes, region_name)
    series = region_view.mean(dim=[lat_axis, lon_axis])
    if anomaly_mode:
        series = series - series.mean(dim=time_axis)
    return series


def top_signal_hotspots(
    map_slice: xr.DataArray,
    axes: dict[str, str | None],
    *,
    top_n: int = 12,
    absolute: bool = True,
) -> pd.DataFrame:
    lat_axis = axes["lat"]
    lon_axis = axes["lon"]
    if lat_axis is None or lon_axis is None:
        return pd.DataFrame(columns=["lat", "lon", "value"])

    frame = map_slice.to_dataframe(name="value").reset_index()
    if absolute:
        frame["_rank"] = frame["value"].abs()
    else:
        frame["_rank"] = frame["value"]
    frame = frame.sort_values("_rank", ascending=False).head(top_n).drop(columns="_rank")
    return frame.rename(columns={lat_axis: "lat", lon_axis: "lon"}).reset_index(drop=True)
