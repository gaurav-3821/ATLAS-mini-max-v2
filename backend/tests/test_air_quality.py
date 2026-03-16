from __future__ import annotations

from services.air_quality_service import fetch_air_quality


def test_air_quality_service_formats_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "ok",
                "data": {
                    "aqi": 142,
                    "dominentpol": "pm25",
                    "time": {"iso": "2025-01-15T14:00:00Z"},
                    "iaqi": {
                        "pm25": {"v": 55.3},
                        "pm10": {"v": 78.1},
                        "o3": {"v": 42.0},
                        "no2": {"v": 28.5},
                        "so2": {"v": 5.2},
                        "co": {"v": 0.8},
                    },
                },
            }

    monkeypatch.setattr("services.air_quality_service.requests.get", lambda *args, **kwargs: FakeResponse())
    result = fetch_air_quality(28.61, 77.20)
    assert result["status"] == "success"
    assert result["data"]["category"] == "Unhealthy for Sensitive Groups"
    assert result["data"]["pollutants"]["pm25"] == 55.3


def test_air_quality_service_handles_unavailable(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "error"}

    monkeypatch.setattr("services.air_quality_service.requests.get", lambda *args, **kwargs: FakeResponse())
    result = fetch_air_quality(28.61, 77.20)
    assert result["status"] == "error"
    assert result["code"] == "AQI_UNAVAILABLE"
