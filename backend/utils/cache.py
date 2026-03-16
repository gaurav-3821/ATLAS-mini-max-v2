from __future__ import annotations

from threading import RLock
from typing import Any

from cachetools import TTLCache


_cache_lock = RLock()

_caches = {
    "geocoding": TTLCache(maxsize=500, ttl=60 * 60 * 24 * 7),
    "weather": TTLCache(maxsize=100, ttl=60 * 10),
    "air_quality": TTLCache(maxsize=100, ttl=60 * 15),
    "historical": TTLCache(maxsize=50, ttl=60 * 60 * 24),
}


def build_cache_key(service: str, *parts: Any) -> str:
    rendered: list[str] = [service]
    for part in parts:
        if isinstance(part, float):
            rendered.append(f"{part:.2f}")
        else:
            rendered.append(str(part))
    return ":".join(rendered)


def get_cache(service: str) -> TTLCache:
    return _caches[service]


def get_cached(service: str, key: str) -> Any | None:
    with _cache_lock:
        return _caches[service].get(key)


def set_cached(service: str, key: str, value: Any) -> Any:
    with _cache_lock:
        _caches[service][key] = value
    return value


def cache_entry_count() -> int:
    with _cache_lock:
        return sum(len(cache) for cache in _caches.values())
