# ATLAS Climate Intelligence Platform

This repository now contains two application paths:

- the existing Streamlit prototype at [app.py](/C:/Users/Gaurav/Documents/ATLAS%20v3/app.py)
- a new full-stack Flask + static frontend implementation under [backend](/C:/Users/Gaurav/Documents/ATLAS%20v3/backend) and [frontend](/C:/Users/Gaurav/Documents/ATLAS%20v3/frontend)

## Full-Stack Architecture

Backend:

- Flask 3.1
- Flask-CORS
- Flask-Limiter
- cachetools TTLCache
- python-dotenv
- requests

Frontend:

- semantic HTML
- CSS variables with dark and light neobrutal themes
- vanilla ES modules
- Chart.js 4
- Leaflet 1.9

Live services:

- Nominatim for geocoding
- Open-Meteo forecast
- Open-Meteo ERA5 archive
- WAQI for air quality

## Full-Stack Setup

1. Create the environment file at [backend/.env](/C:/Users/Gaurav/Documents/ATLAS%20v3/backend/.env)
2. Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Start the Flask app in development:

```bash
flask --app app run --debug --port 5000
```

4. Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

Environment variables:

```bash
WAQI_API_KEY=your_waqi_token_here
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=change_me_for_production
```

## API Endpoints

- `GET /api/health`
- `GET /api/location?city=Delhi`
- `GET /api/weather?lat=28.61&lon=77.20`
- `GET /api/air-quality?lat=28.61&lon=77.20`
- `GET /api/history?lat=28.61&lon=77.20`
- `GET /api/climate-summary?city=New York`

`/api/climate-summary` resolves the city and then calls weather, AQI, and history in parallel with `ThreadPoolExecutor`.

## Testing

Run the backend tests:

```bash
cd backend
pytest
```

The tests mock all external API calls and cover:

- city validation and geocoding
- weather formatting
- AQI formatting and graceful fallback
- risk score calculation
- climate-summary integration
- rate limiting

## Docker

Files:

- [docker/Dockerfile](/C:/Users/Gaurav/Documents/ATLAS%20v3/docker/Dockerfile)
- [docker/docker-compose.yml](/C:/Users/Gaurav/Documents/ATLAS%20v3/docker/docker-compose.yml)
- [docker/nginx.conf](/C:/Users/Gaurav/Documents/ATLAS%20v3/docker/nginx.conf)

Run:

```bash
cd docker
docker compose up --build
```

This starts:

- Flask backend on Gunicorn
- Nginx reverse proxy on `http://localhost:8080`

## Legacy Streamlit App

The original Streamlit app is still available for comparison and demo continuity:

```bash
streamlit run app.py
```
