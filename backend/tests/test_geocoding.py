from __future__ import annotations

from services.geocoding_service import geocode_city
from utils.validators import sanitize_city, validate_city


def test_sanitize_city_removes_html_and_sql():
    assert sanitize_city("<b>Delhi</b> DROP TABLE") == "Delhi"


def test_validate_city_rejects_empty():
    valid, cleaned, message = validate_city("   ")
    assert valid is False
    assert cleaned is None
    assert message == "City is required"


def test_geocode_city_success(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    "lat": "28.6139",
                    "lon": "77.2090",
                    "display_name": "Delhi, India",
                    "address": {"city": "Delhi", "country": "India"},
                }
            ]

    monkeypatch.setattr("services.geocoding_service.requests.get", lambda *args, **kwargs: FakeResponse())
    result = geocode_city("Delhi")
    assert result["status"] == "success"
    assert result["data"]["city"] == "Delhi"
    assert result["data"]["lat"] == 28.6139
