import { renderCharts } from './charts.js';
import { initMap, updateMap } from './map.js';
import { initSearch, setSearchLoading } from './search.js';
import { getState, setState } from './state.js';
import { initTheme } from './theme.js';

const AUTO_REFRESH_MS = 10 * 60 * 1000;

document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initMap();
  initSearch(loadSummary);
  document.addEventListener('atlas:theme-changed', () => {
    if (getState().summary) {
      renderCharts(getState().summary);
    }
  });
  scheduleRefresh();
  await loadSummary(getState().currentCity);
});

async function loadSummary(city, retry = false) {
  setSearchLoading(true);
  setSkeletonState(true);
  try {
    const response = await fetch(`/api/climate-summary?city=${encodeURIComponent(city)}`);
    const payload = await response.json();
    if (!response.ok || payload.status !== 'success') {
      throw new Error(payload.message || 'Request failed');
    }

    const summary = payload.data;
    setState({ currentCity: city, summary });
    renderSummary(summary);
    updateMap(summary.location, summary);
    renderCharts(summary);
    setLastUpdated(summary.fetched_at);
  } catch (error) {
    showToast(error.message, () => loadSummary(city, true));
    if (!retry && getState().summary) {
      renderSummary(getState().summary);
    }
  } finally {
    setSearchLoading(false);
    setSkeletonState(false);
  }
}

function renderSummary(summary) {
  document.getElementById('location-name').textContent = summary.location.city;
  document.getElementById('location-display').textContent = summary.location.display_name;
  document.getElementById('location-description').textContent = summary.weather.description;
  document.getElementById('temperature-card').textContent = `${summary.weather.temperature} °C`;
  document.getElementById('humidity-card').textContent = `${summary.weather.humidity} %`;
  document.getElementById('wind-card').textContent = `${summary.weather.wind_speed} km/h`;
  document.getElementById('aqi-card').textContent = summary.air_quality.aqi == null
    ? 'Unavailable'
    : `${summary.air_quality.aqi} · ${summary.air_quality.category}`;
  document.getElementById('risk-card').textContent = `${summary.risk_index.score} · ${summary.risk_index.level}`;
  colorizeAqi(summary.air_quality.aqi);
  colorizeRisk(summary.risk_index.color);
}

function colorizeAqi(aqi) {
  const el = document.getElementById('aqi-card');
  let color = '#7f1d1d';
  if (aqi == null) {
    color = getComputedStyle(document.documentElement).getPropertyValue('--atlas-text').trim();
  } else if (aqi <= 50) {
    color = '#22c55e';
  } else if (aqi <= 100) {
    color = '#eab308';
  } else if (aqi <= 150) {
    color = '#f97316';
  } else if (aqi <= 200) {
    color = '#ef4444';
  } else if (aqi <= 300) {
    color = '#a855f7';
  }
  el.style.color = color;
}

function colorizeRisk(color) {
  document.getElementById('risk-card').style.color = color;
}

function setLastUpdated(timestamp) {
  const value = new Date(timestamp);
  document.getElementById('last-updated').textContent = `Last updated: ${value.toLocaleTimeString()}`;
}

function setSkeletonState(loading) {
  for (const id of ['temperature-card', 'humidity-card', 'wind-card', 'aqi-card', 'risk-card']) {
    document.getElementById(id).classList.toggle('skeleton', loading);
  }
}

function scheduleRefresh() {
  const existing = getState().refreshTimer;
  if (existing) {
    window.clearInterval(existing);
  }
  const timer = window.setInterval(() => {
    if (!document.hidden) {
      loadSummary(getState().currentCity);
    }
  }, AUTO_REFRESH_MS);
  setState({ refreshTimer: timer });
}

function showToast(message, onRetry) {
  const region = document.getElementById('toast-region');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<div>${message}</div>`;
  const retryButton = document.createElement('button');
  retryButton.type = 'button';
  retryButton.textContent = 'Retry';
  retryButton.addEventListener('click', () => {
    toast.remove();
    onRetry();
  });
  toast.appendChild(retryButton);
  region.appendChild(toast);
  window.setTimeout(() => toast.remove(), 5000);
}
