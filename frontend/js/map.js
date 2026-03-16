import { getState, setState } from './state.js';

export function initMap() {
  const map = window.L.map('atlas-map').setView([40.7128, -74.0060], 10);
  window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);
  setState({ map });
}

export function updateMap(location, summary) {
  const { map, marker } = getState();
  if (!map) {
    return;
  }
  if (marker) {
    map.removeLayer(marker);
  }
  const nextMarker = window.L.marker([location.lat, location.lon]).addTo(map);
  nextMarker.bindPopup(
    `<strong>${location.city}</strong><br>Temperature: ${summary.weather.temperature} °C<br>AQI: ${summary.air_quality.aqi ?? 'N/A'}`
  );
  map.setView([location.lat, location.lon], 10);
  setState({ marker: nextMarker });
}
