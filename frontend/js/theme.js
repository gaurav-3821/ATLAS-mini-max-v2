import { getState, setState } from './state.js';

const STORAGE_KEY = 'atlas_theme';

export function initTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = stored || (systemDark ? 'dark_mode' : 'light_neobrutalism');
  applyTheme(theme);

  document.getElementById('theme-toggle').addEventListener('click', () => {
    const next = getState().theme === 'dark_mode' ? 'light_neobrutalism' : 'dark_mode';
    applyTheme(next);
    document.dispatchEvent(new CustomEvent('atlas:theme-changed', { detail: next }));
  });
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  document.getElementById('theme-toggle-label').textContent = theme === 'dark_mode' ? 'Dark' : 'Light';
  localStorage.setItem(STORAGE_KEY, theme);
  setState({ theme });
}
