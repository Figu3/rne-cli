import json
import time
from pathlib import Path

import pytest

from rne_cli.cache import cache_get, cache_put, cache_key


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


class TestCacheKey:
    def test_deterministic(self):
        k1 = cache_key("GET", "/companies/123", {"page": 1, "pageSize": 20})
        k2 = cache_key("GET", "/companies/123", {"pageSize": 20, "page": 1})
        assert k1 == k2  # param order doesn't matter

    def test_different_params_different_key(self):
        k1 = cache_key("GET", "/companies/123", {"page": 1})
        k2 = cache_key("GET", "/companies/123", {"page": 2})
        assert k1 != k2


class TestCachePutGet:
    def test_put_then_get(self, fake_home):
        data = {"siren": "732829320", "name": "L'OREAL"}
        cache_put("k1", data)
        got = cache_get("k1", ttl_seconds=60)
        assert got == data

    def test_miss_returns_none(self, fake_home):
        assert cache_get("nonexistent", ttl_seconds=60) is None

    def test_expired_returns_none(self, fake_home, monkeypatch):
        cache_put("k1", {"x": 1})
        # Backdate fetched_at to 2 hours ago
        path = fake_home / ".rne" / "cache" / "k1.json"
        payload = json.loads(path.read_text())
        payload["fetched_at"] = time.time() - 7200
        path.write_text(json.dumps(payload))
        assert cache_get("k1", ttl_seconds=3600) is None

    def test_rewrite_overwrites(self, fake_home):
        cache_put("k1", {"v": 1})
        cache_put("k1", {"v": 2})
        assert cache_get("k1", ttl_seconds=60) == {"v": 2}
