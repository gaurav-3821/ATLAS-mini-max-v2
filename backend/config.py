from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
LOG_DIR = BASE_DIR.parent / "logs"
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


class Config:
    APP_NAME = "ATLAS Climate Intelligence Platform"
    SECRET_KEY = os.getenv("SECRET_KEY", "atlas-development-secret")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    WAQI_API_KEY = os.getenv("WAQI_API_KEY", "")
    DEFAULT_CITY = "New York"
    REQUEST_TIMEOUT = 10
    HISTORY_MAX_DAYS = 365
    CACHE_MAX_MEMORY_MB = 50
    RATE_LIMIT_DEFAULT = "60 per minute"
    RATE_LIMIT_STORAGE_URI = "memory://"
    CORS_ORIGINS = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://atlas-climate.yourdomain.com",
    ]

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "img-src 'self' data: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; "
            "connect-src 'self' https://nominatim.openstreetmap.org https://api.open-meteo.com "
            "https://archive-api.open-meteo.com https://api.waqi.info; "
            "font-src 'self' data: https://cdn.jsdelivr.net;"
        ),
    }
