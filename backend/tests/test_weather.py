from __future__ import annotations

from services.weather_service import fetch_weather


def test_weather_service_formats_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "current": {
                    "temperature_2m": 32.5,
                    "relative_humidity_2m": 65,
                    "wind_speed_10m": 12.3,
                    "weather_code": 2,
                    "time": "2025-01-15T14:30:00Z",
                },
                "hourly": {
                    "time": ["2025-01-15T00:00", "2025-01-15T01:00"],
                    "temperature_2m": [28.1, 27.8],
                    "relative_humidity_2m": [70, 72],
                    "precipitation": [0.0, 0.0],
                    "wind_speed_10m": [8.5, 9.1],
                },
            }

    monkeypatch.setattr("services.weather_service.requests.get", lambda *args, **kwargs: FakeResponse())
    result = fetch_weather(28.61, 77.20)
    assert result["status"] == "success"
    assert result["data"]["current"]["description"] == "Partly Cloudy"
    assert result["data"]["hourly_forecast"]["temperature_2m"][0] == 28.1
