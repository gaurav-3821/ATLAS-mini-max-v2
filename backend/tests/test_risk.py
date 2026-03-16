from __future__ import annotations

from services.risk_service import calculate_risk_summary
from utils.validators import validate_coordinates


def test_risk_calculation_known_inputs():
    weather = {
        "current": {"temperature": 42, "humidity": 85, "wind_speed": 72},
        "hourly_forecast": {"precipitation": [10]},
    }
    air_quality = {"aqi": 180}
    history = {"daily_averages": {"temperature": [25, 26, 27], "precipitation": [1, 2, 3]}}
    risk = calculate_risk_summary(weather, air_quality, history)
    assert risk["score"] > 7
    assert risk["level"] in {"High", "Critical"}


def test_risk_edge_case_all_low():
    weather = {
        "current": {"temperature": 24, "humidity": 45, "wind_speed": 8},
        "hourly_forecast": {"precipitation": [1]},
    }
    history = {"daily_averages": {"temperature": [24, 24, 24], "precipitation": [1, 1, 1]}}
    risk = calculate_risk_summary(weather, {"aqi": 20}, history)
    assert risk["score"] <= 3
    assert risk["level"] == "Low"


def test_validate_coordinates_out_of_range():
    valid, _, message = validate_coordinates(120, 50)
    assert valid is False
    assert "Latitude" in message
