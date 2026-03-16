from __future__ import annotations


def test_climate_summary_success(client, monkeypatch):
    monkeypatch.setattr(
        "app.geocode_city",
        lambda city: {
            "status": "success",
            "data": {
                "city": city,
                "display_name": f"{city}, India",
                "lat": 28.6139,
                "lon": 77.2090,
                "country": "India",
            },
        },
    )
    monkeypatch.setattr(
        "app.fetch_weather",
        lambda lat, lon: {
            "status": "success",
            "data": {
                "current": {"temperature": 32.5, "humidity": 65, "wind_speed": 12.3, "description": "Partly Cloudy"},
                "hourly_forecast": {
                    "time": ["2025-01-15T00:00", "2025-01-15T01:00"],
                    "temperature_2m": [28.1, 27.8],
                    "relative_humidity_2m": [70, 72],
                    "precipitation": [0.0, 0.0],
                    "wind_speed_10m": [8.5, 9.1],
                },
            },
        },
    )
    monkeypatch.setattr(
        "app.fetch_air_quality",
        lambda lat, lon: {
            "status": "success",
            "data": {"aqi": 142, "category": "Unhealthy for Sensitive Groups", "dominant_pollutant": "pm25", "pollutants": {}},
        },
    )
    monkeypatch.setattr(
        "app.fetch_history",
        lambda lat, lon, start_date, end_date: {
            "status": "success",
            "data": {
                "daily_averages": {"temperature": [20, 21], "precipitation": [1, 2], "dates": ["2025-01-01", "2025-01-02"]},
                "comparison_period": {"daily_averages": {"temperature": [19, 20], "precipitation": [0, 1], "dates": ["2024-01-01", "2024-01-02"]}},
            },
        },
    )
    monkeypatch.setattr(
        "app.calculate_risk_summary",
        lambda weather, air, history: {"score": 7.2, "level": "High", "color": "#f97316", "factors": []},
    )

    response = client.get("/api/climate-summary?city=Delhi")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["data"]["location"]["city"] == "Delhi"
    assert payload["data"]["air_quality"]["aqi"] == 142


def test_climate_summary_allows_partial_aqi_failure(client, monkeypatch):
    monkeypatch.setattr(
        "app.geocode_city",
        lambda city: {"status": "success", "data": {"city": city, "display_name": city, "lat": 1.0, "lon": 2.0, "country": "Test"}},
    )
    monkeypatch.setattr(
        "app.fetch_weather",
        lambda lat, lon: {"status": "success", "data": {"current": {"temperature": 20, "humidity": 40, "wind_speed": 8, "description": "Clear"}, "hourly_forecast": {"time": [], "temperature_2m": [], "relative_humidity_2m": [], "precipitation": [], "wind_speed_10m": []}}},
    )
    monkeypatch.setattr("app.fetch_air_quality", lambda lat, lon: {"status": "error", "message": "Air quality data unavailable", "code": "AQI_UNAVAILABLE"})
    monkeypatch.setattr(
        "app.fetch_history",
        lambda lat, lon, start_date, end_date: {"status": "success", "data": {"daily_averages": {"temperature": [20], "precipitation": [0], "dates": ["2025-01-01"]}, "comparison_period": {"daily_averages": {"temperature": [19], "precipitation": [0], "dates": ["2024-01-01"]}}}},
    )
    monkeypatch.setattr("app.calculate_risk_summary", lambda weather, air, history: {"score": 2.0, "level": "Low", "color": "#22c55e", "factors": []})
    response = client.get("/api/climate-summary?city=Delhi")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["air_quality"]["category"] == "Unavailable"


def test_rate_limiter_kicks_in(client, monkeypatch):
    monkeypatch.setattr("app.geocode_city", lambda city: {
        "status": "success",
        "data": {"city": city, "display_name": city, "lat": 1.0, "lon": 2.0, "country": "Test"},
    })
    for _ in range(20):
        client.get("/api/location?city=Delhi")
    response = client.get("/api/location?city=Delhi")
    assert response.status_code == 429
