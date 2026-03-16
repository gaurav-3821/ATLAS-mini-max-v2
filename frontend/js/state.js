const state = {
  currentCity: 'New York',
  summary: null,
  theme: null,
  charts: {},
  map: null,
  marker: null,
  refreshTimer: null,
  listeners: new Set(),
};

export function getState() {
  return state;
}

export function setState(partial) {
  Object.assign(state, partial);
  for (const listener of state.listeners) {
    listener(state);
  }
}

export function subscribe(listener) {
  state.listeners.add(listener);
  return () => state.listeners.delete(listener);
}
