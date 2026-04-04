<div align="center">

# 🌍 ATLAS — Climate Intelligence Platform

**AI-powered real-time climate analysis with weather forecasting, air quality monitoring, and historical climate insights**

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=flat-square&logo=streamlit)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](./docker)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](./LICENSE)

</div>

---

## ✨ Features

- 🌤️ **Real-time weather forecasting** via Open-Meteo API
- 💨 **Air Quality Index (AQI)** monitoring via WAQI
- 📊 **Historical climate analysis** using ERA5 archive data
- 🗺️ **Geocoding** via Nominatim — search any city worldwide
- ⚡ **Parallel data fetching** with ThreadPoolExecutor
- 🌗 **Dark & Light neobrutal UI** themes
- 🐳 **Docker + Nginx** production-ready deployment
- 🧪 **Full test suite** with mocked external APIs

---

## 🏗️ Architecture
ATLAS-minimax-v2/
├── app.py                  # Streamlit legacy app
├── backend/                # Flask REST API
│   ├── app.py
│   ├── requirements.txt
│   └── tests/
├── frontend/               # Vanilla JS + Chart.js + Leaflet UI
├── pages/                  # Streamlit multi-page components
├── utils/                  # Shared utility modules
├── data/                   # Static/reference data
├── assets/                 # Screenshots and media
├── docker/                 # Dockerfile, Compose, Nginx config
├── scripts/                # Dev capture and build scripts
└── docs/                   # Demo video and documentation

---

## 🚀 Quick Start

### Option A — Full-Stack (Flask + Frontend)

**1. Set up environment**
```bash
cd backend
cp .env.example .env   # fill in your WAQI_API_KEY
pip install -r requirements.txt
```

**2. Run the Flask server**
```bash
flask --app app run --debug --port 5000
```

**3. Open in browser**
http://127.0.0.1:5000

### Option B — Streamlit (Legacy)
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔑 Environment Variables

Create `backend/.env`:
```env
WAQI_API_KEY=your_waqi_token_here
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=change_me_for_production
```

Get your free WAQI token at [aqicn.org/data-platform/token](https://aqicn.org/data-platform/token/)

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/location?city=Delhi` | Geocode a city |
| `GET` | `/api/weather?lat=28.61&lon=77.20` | Current forecast |
| `GET` | `/api/air-quality?lat=28.61&lon=77.20` | AQI data |
| `GET` | `/api/history?lat=28.61&lon=77.20` | ERA5 archive |
| `GET` | `/api/climate-summary?city=New York` | Full parallel summary |

---

## 🐳 Docker Deployment
```bash
cd docker
docker compose up --build
```

Starts:
- Flask backend on Gunicorn
- Nginx reverse proxy → `http://localhost:8080`

---

## 🧪 Testing
```bash
cd backend
pytest
```

Coverage includes: geocoding, weather formatting, AQI fallback, risk scores, rate limiting, and climate-summary integration.

---

## 🖼️ Screenshots

| Dark Theme | Light Theme |
|-----------|-------------|
| ![Dark](assets/atlas-flask-dashboard-dark.png) | ![Light](assets/atlas-flask-dashboard-light.png) |

---

## 🛠️ Tech Stack

**Backend:** Flask 3.1 · Flask-CORS · Flask-Limiter · cachetools · python-dotenv  
**Frontend:** Semantic HTML · CSS Variables · Vanilla ES Modules · Chart.js 4 · Leaflet 1.9  
**Data APIs:** Open-Meteo · Open-Meteo ERA5 · WAQI · Nominatim  
**DevOps:** Docker · Gunicorn · Nginx · Render

---

## 👤 Author

**Gaurav** · [@gaurav-3821](https://github.com/gaurav-3821)

---

<div align="center">
⭐ Star this repo if you find it useful!
</div>
