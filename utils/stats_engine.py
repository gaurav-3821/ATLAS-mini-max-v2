from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import linregress, zscore


def summarize_values(_data_array: xr.DataArray) -> dict[str, float]:
    values = np.asarray(_data_array.values, dtype=float)
    return {
        "mean": float(np.nanmean(values)),
        "max": float(np.nanmax(values)),
        "min": float(np.nanmin(values)),
    }


def compute_linear_trend(_series: xr.DataArray, time_axis: str) -> dict[str, float | str]:
    time_values = pd.to_datetime(_series[time_axis].values)
    if len(time_values) < 2:
        base = float(_series.values[0]) if len(_series.values) else 0.0
        return {"slope_per_year": 0.0, "intercept": base, "r_value": 0.0, "label": "Stable", "arrow": "flat"}

    x = time_values.year + (time_values.month - 1) / 12.0
    y = np.asarray(_series.values, dtype=float)
    result = linregress(x, y)
    slope = float(result.slope)
    label = "Warming" if slope > 0 else "Cooling" if slope < 0 else "Stable"
    arrow = "up" if slope > 0 else "down" if slope < 0 else "flat"
    return {
        "slope_per_year": slope,
        "intercept": float(result.intercept),
        "r_value": float(result.rvalue),
        "label": label,
        "arrow": arrow,
    }


def build_trend_series(_series: xr.DataArray, time_axis: str, trend: dict[str, float | str]) -> pd.DataFrame:
    time_values = pd.to_datetime(_series[time_axis].values)
    x = time_values.year + (time_values.month - 1) / 12.0
    slope = float(trend["slope_per_year"])
    intercept = float(trend["intercept"])
    fitted = intercept + slope * x
    return pd.DataFrame({"time": time_values, "trend": fitted})


def detect_anomalies(_series: xr.DataArray, threshold: float = 2.0) -> dict[str, object]:
    values = np.asarray(_series.values, dtype=float)
    if np.all(np.isnan(values)):
        return {"count": 0, "mask": np.zeros_like(values, dtype=bool)}

    z_scores = zscore(values, nan_policy="omit")
    mask = np.abs(z_scores) >= threshold
    return {"count": int(np.nansum(mask)), "mask": mask}


def compute_period_change(_before_slice: xr.DataArray, _after_slice: xr.DataArray) -> dict[str, float]:
    before_mean = float(np.nanmean(_before_slice.values))
    after_mean = float(np.nanmean(_after_slice.values))
    return {"before_mean": before_mean, "after_mean": after_mean, "delta": after_mean - before_mean}
