from __future__ import annotations

import math

import numpy as np
import pandas as pd


VARIABLE_KEYWORDS = {
    "temperature": "t2m",
    "heat": "t2m",
    "precipitation": "precipitation",
    "rain": "precipitation",
    "pressure": "sea_level_pressure",
    "wind": "wind_speed",
}

REGION_KEYWORDS = {
    "global": "Global",
    "asia": "Asia",
    "europe": "Europe",
    "north america": "North America",
    "south america": "South America",
    "africa": "Africa",
    "arctic": "Arctic",
    "antarctica": "Antarctica",
}


def parse_natural_language_query(query: str) -> dict[str, str | bool]:
    lowered = query.lower()
    variable = next((value for key, value in VARIABLE_KEYWORDS.items() if key in lowered), "t2m")
    region = next((value for key, value in REGION_KEYWORDS.items() if key in lowered), "Global")
    anomaly = "anomaly" in lowered
    return {"variable": variable, "region": region, "anomaly_mode": anomaly}


def build_forecast_frame(
    series_df: pd.DataFrame,
    *,
    time_column: str,
    value_column: str,
    horizon: int = 24,
    freq: str = "MS",
) -> pd.DataFrame:
    ordered = series_df[[time_column, value_column]].dropna().copy()
    ordered = ordered.sort_values(time_column).reset_index(drop=True)
    if ordered.empty:
        return pd.DataFrame(columns=["time", "forecast", "lower", "upper"])

    ordered["time"] = pd.to_datetime(ordered[time_column])
    ordered["x"] = np.arange(len(ordered), dtype=float)
    ordered["month"] = ordered["time"].dt.month

    trend_coeffs = np.polyfit(ordered["x"], ordered[value_column], 1)
    fitted = np.polyval(trend_coeffs, ordered["x"])
    residuals = ordered[value_column] - fitted
    seasonal = residuals.groupby(ordered["month"]).mean()
    residual_std = float(max(residuals.std(ddof=1) if len(residuals) > 1 else 0.0, 1e-6))

    last_time = ordered["time"].iloc[-1]
    future_times = pd.date_range(last_time + pd.tseries.frequencies.to_offset(freq), periods=horizon, freq=freq)
    start_index = len(ordered)
    future_x = np.arange(start_index, start_index + horizon, dtype=float)

    forecasts: list[dict[str, float | pd.Timestamp]] = []
    for idx, future_time in enumerate(future_times):
        base = float(np.polyval(trend_coeffs, future_x[idx]))
        seasonal_adjustment = float(seasonal.get(future_time.month, 0.0))
        forecast_value = base + seasonal_adjustment
        spread = residual_std * (1.0 + 0.05 * math.sqrt(idx + 1))
        forecasts.append(
            {
                "time": future_time,
                "forecast": forecast_value,
                "lower": forecast_value - 1.64 * spread,
                "upper": forecast_value + 1.64 * spread,
            }
        )
    return pd.DataFrame(forecasts)


def compute_model_diagnostics(series_df: pd.DataFrame, value_column: str) -> dict[str, float]:
    clean = series_df[[value_column]].dropna()
    if clean.empty:
        return {"latest": 0.0, "mean": 0.0, "volatility": 0.0}
    values = clean[value_column].to_numpy(dtype=float)
    return {
        "latest": float(values[-1]),
        "mean": float(np.mean(values)),
        "volatility": float(np.std(values)),
    }
