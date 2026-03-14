from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _clip_score(value: float) -> float:
    return float(max(0.0, min(100.0, value)))


def risk_label(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 50:
        return "Elevated"
    if score >= 25:
        return "Moderate"
    return "Low"


def _latest_station_normal(history_df: pd.DataFrame, column: str) -> float | None:
    if history_df.empty or column not in history_df:
        return None
    values = history_df[column].dropna()
    if values.empty:
        return None
    return float(values.mean())


def build_risk_profile(
    weather: dict[str, float | str],
    forecast_df: pd.DataFrame,
    air_current: dict[str, float | str],
    history_df: pd.DataFrame | None = None,
) -> dict[str, object]:
    history_df = history_df if history_df is not None else pd.DataFrame()
    current_temp = float(weather.get("temperature_c", 0.0))
    humidity = float(weather.get("humidity_pct", 0.0))
    wind = float(weather.get("wind_mps", 0.0))
    pressure = float(weather.get("pressure_hpa", 1013.0))
    aqi = float(air_current.get("aqi", 1.0))

    max_forecast_temp = float(forecast_df["temperature_c"].max()) if not forecast_df.empty else current_temp
    max_precip_prob = float(forecast_df["precip_probability_pct"].max()) if not forecast_df.empty else 0.0
    max_forecast_wind = float(forecast_df["wind_mps"].max()) if not forecast_df.empty else wind

    recent_rain_mm = float(history_df["PRCP"].tail(7).fillna(0).sum()) if "PRCP" in history_df else 0.0
    recent_temp_normal = _latest_station_normal(history_df, "TMAX")
    heat_departure = max(0.0, current_temp - recent_temp_normal) if recent_temp_normal is not None else max(0.0, current_temp - 30.0)

    heatwave_score = _clip_score((max_forecast_temp - 28.0) * 5.5 + heat_departure * 4.0 - max(0.0, humidity - 75.0) * 0.5)
    flood_score = _clip_score(max_precip_prob * 0.65 + recent_rain_mm * 1.1 + max(0.0, humidity - 70.0) * 0.45)
    wildfire_score = _clip_score((max_forecast_temp - 24.0) * 4.0 + max_forecast_wind * 4.5 + max(0.0, 50.0 - humidity) * 1.1 - recent_rain_mm * 0.7)
    storm_score = _clip_score(max_precip_prob * 0.45 + max_forecast_wind * 5.0 + max(0.0, 1010.0 - pressure) * 3.2)
    health_score = _clip_score((aqi - 1.0) * 22.0 + float(air_current.get("pm2_5", 0.0)) * 1.2)

    risk_scores = {
        "Heatwave": heatwave_score,
        "Flood": flood_score,
        "Wildfire": wildfire_score,
        "Storm": storm_score,
        "Air quality": health_score,
    }
    composite = float(np.mean(list(risk_scores.values()))) if risk_scores else 0.0

    alerts: list[str] = []
    if heatwave_score >= 65:
        alerts.append(f"Heat stress is elevated with forecast highs up to {max_forecast_temp:.1f} deg C.")
    if flood_score >= 65:
        alerts.append(f"Flood watch conditions are elevated from {max_precip_prob:.0f}% precipitation risk and recent rainfall.")
    if wildfire_score >= 65:
        alerts.append("Fire weather conditions are elevated because of heat, wind, and dry air.")
    if storm_score >= 65:
        alerts.append("Storm probability is elevated due to wind, pressure, and precipitation setup.")
    if health_score >= 60:
        alerts.append(f"Air quality risk is elevated with AQI {aqi:.0f}.")

    panels = {
        key: {
            "score": value,
            "label": risk_label(value),
        }
        for key, value in risk_scores.items()
    }

    return {
        "panels": panels,
        "scores": risk_scores,
        "composite": composite,
        "composite_label": risk_label(composite),
        "alerts": alerts,
    }


def build_risk_timeline(forecast_df: pd.DataFrame) -> pd.DataFrame:
    if forecast_df.empty:
        return pd.DataFrame(columns=["time", "heatwave", "flood", "storm"])

    timeline = forecast_df.copy()
    timeline["heatwave"] = ((timeline["temperature_c"] - 28.0) * 6.0).clip(lower=0, upper=100)
    timeline["flood"] = (timeline["precip_probability_pct"] * 0.9).clip(lower=0, upper=100)
    timeline["storm"] = (timeline["precip_probability_pct"] * 0.5 + timeline["wind_mps"] * 7.0).clip(lower=0, upper=100)
    return timeline[["time", "heatwave", "flood", "storm"]]
