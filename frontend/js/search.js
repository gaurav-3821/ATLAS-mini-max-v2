const RECENT_KEY = 'atlas_recent_searches';

export function initSearch(onSearch) {
  const input = document.getElementById('city-search');
  const button = document.getElementById('search-button');
  const triggerSearch = () => {
    const city = input.value.trim();
    if (!city) {
      return;
    }
    addRecentSearch(city);
    renderRecentSearches(onSearch);
    onSearch(city);
  };

  let debounceHandle = null;
  input.addEventListener('input', () => {
    window.clearTimeout(debounceHandle);
    debounceHandle = window.setTimeout(() => {
      renderRecentSearches(onSearch, input.value.trim());
    }, 300);
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      triggerSearch();
    }
  });

  button.addEventListener('click', triggerSearch);
  renderRecentSearches(onSearch);
}

export function setSearchLoading(loading) {
  const button = document.getElementById('search-button');
  const spinner = button.querySelector('.button-spinner');
  const label = button.querySelector('.button-text');
  button.disabled = loading;
  spinner.hidden = !loading;
  label.textContent = loading ? 'Loading...' : 'Search Climate Data';
}

export function addRecentSearch(city) {
  const existing = getRecentSearches().filter((item) => item.toLowerCase() !== city.toLowerCase());
  const next = [city, ...existing].slice(0, 5);
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
}

export function getRecentSearches() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
  } catch {
    return [];
  }
}

function renderRecentSearches(onSearch, filter = '') {
  const container = document.getElementById('recent-searches');
  const normalized = filter.toLowerCase();
  const items = getRecentSearches().filter((item) => item.toLowerCase().includes(normalized));
  container.innerHTML = '';
  items.forEach((item) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'recent-chip';
    button.textContent = item;
    button.setAttribute('aria-label', `Search recent city ${item}`);
    button.addEventListener('click', () => {
      document.getElementById('city-search').value = item;
      onSearch(item);
    });
    container.appendChild(button);
  });
}
