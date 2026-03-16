from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config, FRONTEND_DIR
from models.schemas import error_response, iso_timestamp, success_response
from services.air_quality_service import fetch_air_quality
from services.geocoding_service import geocode_city
from services.history_service import fetch_history
from services.risk_service import calculate_risk_summary
from services.weather_service import fetch_weather
from utils.cache import cache_entry_count
from utils.logger import logger
from utils.validators import validate_city, validate_coordinates, validate_date_range


START_TIME = time.time()


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=None,
        template_folder=str(FRONTEND_DIR),
    )
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})
    limiter = Limiter(get_remote_address, app=app, default_limits=[Config.RATE_LIMIT_DEFAULT], storage_uri=Config.RATE_LIMIT_STORAGE_URI)

    @app.after_request
    def apply_security_headers(response):
        for key, value in Config.SECURITY_HEADERS.items():
            response.headers[key] = value
        return response

    @app.errorhandler(429)
    def handle_rate_limit(_error):
        payload, status = error_response("Too many requests. Please wait.", "RATE_LIMITED", status_code=429)
        return jsonify(payload), status

    @app.errorhandler(Exception)
    def handle_unexpected(_error):
        logger.critical("Unhandled exception", extra={"event": "unhandled_exceptions"})
        payload, status = error_response("Unexpected server error", "INTERNAL_ERROR", status_code=500)
        return jsonify(payload), status

    @app.get("/")
    def index():
        return send_from_directory(str(FRONTEND_DIR), "index.html")

    @app.get("/api/health")
    def health():
        payload, status = success_response(
            {
                "status": "healthy",
                "uptime_seconds": int(time.time() - START_TIME),
                "cache_entries": cache_entry_count(),
                "services": {"weather": "ok", "aqi": "ok", "geocoding": "ok"},
            }
        )
        return jsonify(payload), status

    @app.get("/api/location")
    @limiter.limit("20 per minute")
    def location():
        city = request.args.get("city", "")
        valid, cleaned, message = validate_city(city)
        if not valid:
            payload, status = error_response(f"Invalid input: {message}", "INVALID_INPUT", status_code=400)
            return jsonify(payload), status

        result = geocode_city(cleaned or "")
        if result["status"] != "success":
            payload, status = error_response(result["message"], result["code"], status_code=404)
            return jsonify(payload), status
        payload, status = success_response(result["data"])
        return jsonify(payload), status

    @app.get("/api/weather")
    def weather():
        coords_valid, coords, error = validate_coordinates(request.args.get("lat"), request.args.get("lon"))
        if not coords_valid:
            payload, status = error_response(f"Invalid input: {error}", "INVALID_INPUT", status_code=400)
            return jsonify(payload), status
        result = fetch_weather(*coords)
        if result["status"] != "success":
            payload, status = error_response(result["message"], result["code"], status_code=503)
            return jsonify(payload), status
        payload, status = success_response(result["data"])
        return jsonify(payload), status

    @app.get("/api/air-quality")
    def air_quality():
        coords_valid, coords, error = validate_coordinates(request.args.get("lat"), request.args.get("lon"))
        if not coords_valid:
            payload, status = error_response(f"Invalid input: {error}", "INVALID_INPUT", status_code=400)
            return jsonify(payload), status
        result = fetch_air_quality(*coords)
        if result["status"] != "success":
            payload, status = error_response(result["message"], result["code"], status_code=200)
            return jsonify(payload), status
        payload, status = success_response(result["data"])
        return jsonify(payload), status

    @app.get("/api/history")
    def history():
        coords_valid, coords, coord_error = validate_coordinates(request.args.get("lat"), request.args.get("lon"))
        if not coords_valid:
            payload, status = error_response(f"Invalid input: {coord_error}", "INVALID_INPUT", status_code=400)
            return jsonify(payload), status

        dates_valid, dates, date_error = validate_date_range(request.args.get("start_date"), request.args.get("end_date"))
        if not dates_valid:
            payload, status = error_response(f"Invalid input: {date_error}", "INVALID_INPUT", status_code=400)
            return jsonify(payload), status

        start_date, end_date = dates
        result = fetch_history(coords[0], coords[1], start_date, end_date)
        if result["status"] != "success":
            payload, status = error_response(result["message"], result["code"], status_code=503)
            return jsonify(payload), status
        payload, status = success_response(result["data"])
        return jsonify(payload), status

    @app.get("/api/climate-summary")
    @limiter.limit("30 per minute")
    def climate_summary():
        city = request.args.get("city", Config.DEFAULT_CITY)
        valid, cleaned, message = validate_city(city)
        if not valid:
            payload, status = error_response(f"Invalid input: {message}", "INVALID_INPUT", status_code=400)
            return jsonify(payload), status

        location_result = geocode_city(cleaned or "")
        if location_result["status"] != "success":
            payload, status = error_response(location_result["message"], location_result["code"], status_code=404)
            return jsonify(payload), status

        location = location_result["data"]
        lat = float(location["lat"])
        lon = float(location["lon"])

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                "weather": executor.submit(fetch_weather, lat, lon),
                "air_quality": executor.submit(fetch_air_quality, lat, lon),
                "history": executor.submit(fetch_history, lat, lon, None, None),
            }
            results = {}
            try:
                for name, future in futures.items():
                    results[name] = future.result(timeout=Config.REQUEST_TIMEOUT)
            except FuturesTimeoutError:
                payload, status = error_response("Upstream services timed out", "TIMEOUT", status_code=504)
                return jsonify(payload), status

        if results["weather"]["status"] != "success":
            payload, status = error_response(results["weather"]["message"], results["weather"]["code"], status_code=503)
            return jsonify(payload), status
        if results["history"]["status"] != "success":
            payload, status = error_response(results["history"]["message"], results["history"]["code"], status_code=503)
            return jsonify(payload), status

        weather_data = results["weather"]["data"]
        air_data = results["air_quality"]["data"] if results["air_quality"]["status"] == "success" else None
        history_data = results["history"]["data"]
        risk = calculate_risk_summary(weather_data, air_data, history_data)

        summary = {
            "location": {
                "city": location["city"],
                "lat": location["lat"],
                "lon": location["lon"],
                "country": location["country"],
                "display_name": location["display_name"],
            },
            "weather": {
                "temperature": weather_data["current"]["temperature"],
                "humidity": weather_data["current"]["humidity"],
                "wind_speed": weather_data["current"]["wind_speed"],
                "description": weather_data["current"]["description"],
            },
            "air_quality": air_data or {
                "aqi": None,
                "category": "Unavailable",
                "dominant_pollutant": "",
                "pollutants": {},
                "message": "Air quality data unavailable for this location",
            },
            "history": {
                "avg_temp_30d": round(sum(history_data["daily_averages"]["temperature"]) / max(len(history_data["daily_averages"]["temperature"]), 1), 2),
                "total_precipitation_30d": round(sum(history_data["daily_averages"]["precipitation"]), 2),
                "daily_averages": history_data["daily_averages"],
                "comparison_period": history_data["comparison_period"],
            },
            "risk_index": risk,
            "forecast": weather_data["hourly_forecast"],
            "fetched_at": iso_timestamp(),
        }
        payload, status = success_response(summary)
        return jsonify(payload), status

    @app.get("/<path:path>")
    def static_proxy(path: str):
        file_path = Path(FRONTEND_DIR) / path
        if file_path.exists():
            return send_from_directory(str(FRONTEND_DIR), path)
        return send_from_directory(str(FRONTEND_DIR), "index.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=Config.DEBUG, port=5000)
