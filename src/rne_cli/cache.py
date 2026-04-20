# src/rne_cli/cache.py
"""Cache disque JSON, clé sha256(method + endpoint + sorted(params))."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

CACHE_DIR_NAME = ".rne/cache"


def _cache_dir() -> Path:
    return Path.home() / CACHE_DIR_NAME


def cache_key(method: str, endpoint: str, params: dict[str, Any]) -> str:
    """Retourne une clé stable pour (méthode, endpoint, params)."""
    serialised = json.dumps(params, sort_keys=True, separators=(",", ":"), default=str)
    raw = f"{method.upper()}|{endpoint}|{serialised}".encode()
    return hashlib.sha256(raw).hexdigest()


def cache_get(key: str, ttl_seconds: int) -> Optional[Any]:
    """Retourne la valeur cachée si présente et non expirée, sinon None."""
    path = _cache_dir() / f"{key}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    fetched_at = payload.get("fetched_at", 0)
    if time.time() - fetched_at > ttl_seconds:
        return None
    return payload.get("data")


def cache_put(key: str, data: Any) -> None:
    """Écrit la valeur dans le cache. Crée le dossier si besoin."""
    d = _cache_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{key}.json"
    payload = {"data": data, "fetched_at": time.time()}
    path.write_text(json.dumps(payload, ensure_ascii=False))
