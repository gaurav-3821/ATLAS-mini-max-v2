from __future__ import annotations

from typing import Any


WEIGHTS = {
    "extreme_temperature": 0.30,
    "air_quality": 0.30,
    "precipitation_anomaly": 0.20,
    "wind_severity": 0.10,
    "humidity_stress": 0.10,
}


def calculate_risk_summary(weather: dict[str, Any], air_quality: dict[str, Any] | None, history: dict[str, Any]) -> dict[str, Any]:
    current = weather["current"]
    current_temp = float(current.get("temperature") or 0.0)
    humidity = float(current.get("humidity") or 0.0)
    wind_speed = float(current.get("wind_speed") or 0.0)
    aqi = float((air_quality or {}).get("aqi") or 0.0)

    precipitation_now = float((weather.get("hourly_forecast", {}).get("precipitation") or [0.0])[0] or 0.0)
    history_precip = history["daily_averages"]["precipitation"]
    history_temp = history["daily_averages"]["temperature"]
    avg_precip = sum(history_precip) / len(history_precip) if history_precip else 0.0
    avg_temp = sum(history_temp) / len(history_temp) if history_temp else current_temp
    precipitation_deviation = 0.0 if avg_precip == 0 else abs((precipitation_now - avg_precip) / avg_precip)

    factor_scores = {
        "extreme_temperature": _score_temperature(current_temp),
        "air_quality": _score_air_quality(aqi),
        "precipitation_anomaly": _score_precipitation(precipitation_deviation),
        "wind_severity": _score_wind(wind_speed),
        "humidity_stress": _score_humidity(humidity),
    }

    score = round(sum(factor_scores[name] * WEIGHTS[name] for name in WEIGHTS), 2)
    level, color = _risk_level(score)
    factors = [{"name": name, "score": round(value, 2)} for name, value in factor_scores.items()]

    return {
        "score": score,
        "level": level,
        "color": color,
        "factors": factors,
        "baseline_temp_30d": round(avg_temp, 2),
    }


def _score_temperature(value: float) -> float:
    if 15 <= value <= 30:
        return 1.0
    if 0 <= value < 15 or 30 < value <= 40:
        return 5.0
    return 9.0


def _score_air_quality(value: float) -> float:
    if value <= 50:
        return 1.0
    if value <= 150:
        return 5.0
    return 9.0


def _score_precipitation(deviation_ratio: float) -> float:
    if deviation_ratio <= 0.2:
        return 1.0
    if deviation_ratio <= 0.6:
        return 5.0
    return 9.0


def _score_wind(value: float) -> float:
    if value < 20:
        return 1.0
    if value <= 60:
        return 5.0
    return 9.0


def _score_humidity(value: float) -> float:
    if 30 <= value <= 60:
        return 1.0
    if value < 30 or value <= 80:
        return 5.0
    return 9.0


def _risk_level(score: float) -> tuple[str, str]:
    if score <= 3:
        return "Low", "#22c55e"
    if score <= 6:
        return "Moderate", "#eab308"
    if score <= 8:
        return "High", "#f97316"
    return "Critical", "#ef4444"
