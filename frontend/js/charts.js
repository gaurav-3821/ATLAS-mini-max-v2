import { getState, setState } from './state.js';

function baseOptions() {
  const root = getComputedStyle(document.documentElement);
  const themeText = root.getPropertyValue('--atlas-text-secondary').trim();
  const gridColor = root.getPropertyValue('--atlas-grid').trim();
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: themeText,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: themeText },
        grid: { color: gridColor },
      },
      y: {
        ticks: { color: themeText },
        grid: { color: gridColor },
      },
    },
  };
}

export function renderCharts(summary) {
  renderTemperatureForecast(summary.forecast);
  renderPrecipitation(summary.forecast);
  renderAirQuality(summary.air_quality);
  renderRisk(summary.risk_index);
  renderHistory(summary.history);
}

function renderTemperatureForecast(forecast) {
  upsertChart('temperatureForecast', 'temperature-forecast-chart', 'line', {
    labels: forecast.time.map((item) => item.slice(11, 16)),
    datasets: [
      {
        label: 'Temperature °C',
        data: forecast.temperature_2m,
        borderColor: themeColors()[0],
        backgroundColor: 'rgba(34, 211, 238, 0.15)',
        tension: 0.35,
        fill: true,
      },
    ],
  });
}

function renderPrecipitation(forecast) {
  upsertChart('precipitation', 'precipitation-chart', 'bar', {
    labels: forecast.time.map((item) => item.slice(11, 16)),
    datasets: [
      {
        label: 'Precipitation mm',
        data: forecast.precipitation,
        backgroundColor: themeColors()[1],
        borderRadius: 8,
      },
    ],
  });
}

function renderAirQuality(airQuality) {
  const pollutants = airQuality.pollutants || {};
  upsertChart(
    'airQuality',
    'air-quality-chart',
    'doughnut',
    {
      labels: Object.keys(pollutants),
      datasets: [
        {
          data: Object.values(pollutants).map((value) => value || 0),
          backgroundColor: themeColors(),
          borderWidth: 2,
        },
      ],
    },
    {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--atlas-text-secondary').trim(),
          },
        },
      },
    },
  );
}

function renderRisk(riskIndex) {
  upsertChart(
    'riskIndex',
    'risk-index-chart',
    'radar',
    {
      labels: riskIndex.factors.map((item) => item.name),
      datasets: [
        {
          label: 'Risk factor score',
          data: riskIndex.factors.map((item) => item.score),
          borderColor: themeColors()[2],
          backgroundColor: 'rgba(244, 114, 182, 0.18)',
          pointBackgroundColor: themeColors()[2],
        },
      ],
    },
    {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: getComputedStyle(document.documentElement).getPropertyValue('--atlas-grid').trim() },
          grid: { color: getComputedStyle(document.documentElement).getPropertyValue('--atlas-grid').trim() },
          pointLabels: { color: getComputedStyle(document.documentElement).getPropertyValue('--atlas-text-secondary').trim() },
          ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--atlas-text-secondary').trim(), backdropColor: 'transparent' },
          min: 0,
          max: 10,
        },
      },
      plugins: {
        legend: {
          labels: { color: getComputedStyle(document.documentElement).getPropertyValue('--atlas-text-secondary').trim() },
        },
      },
    },
  );
}

function renderHistory(history) {
  const current = history.daily_averages;
  const previous = history.comparison_period.daily_averages;
  upsertChart('history', 'historical-comparison-chart', 'line', {
    labels: current.dates,
    datasets: [
      {
        label: 'Current period',
        data: current.temperature,
        borderColor: themeColors()[0],
        tension: 0.35,
      },
      {
        label: 'Same period last year',
        data: previous.temperature,
        borderColor: themeColors()[1],
        tension: 0.35,
      },
    ],
  });
}

function upsertChart(key, elementId, type, data, options = null) {
  const state = getState();
  const existing = state.charts[key];
  const canvas = document.getElementById(elementId);
  canvas.parentElement.style.height = '320px';
  if (existing) {
    existing.data = data;
    existing.options = options || baseOptions();
    existing.update();
    return;
  }

  const chart = new window.Chart(canvas, {
    type,
    data,
    options: options || baseOptions(),
  });
  setState({ charts: { ...state.charts, [key]: chart } });
}

function themeColors() {
  const root = getComputedStyle(document.documentElement);
  return [
    root.getPropertyValue('--atlas-accent').trim() || '#22d3ee',
    root.getPropertyValue('--atlas-accent-secondary').trim() || '#6366f1',
    '#f472b6',
    '#22c55e',
    '#facc15',
    '#94a3b8',
  ];
}
