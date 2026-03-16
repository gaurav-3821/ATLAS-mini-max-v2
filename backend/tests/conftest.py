from __future__ import annotations

import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from utils.cache import get_cache


@pytest.fixture(autouse=True)
def clear_service_caches():
    for service in ("geocoding", "weather", "air_quality", "historical"):
        get_cache(service).clear()
    yield


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("WAQI_API_KEY", "test-token")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    from app import create_app

    application = create_app()
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()
