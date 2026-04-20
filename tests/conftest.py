# tests/conftest.py
"""Fixtures partagées pour les tests rne-cli."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import httpx
import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def fake_home(tmp_path, monkeypatch):
    """Isole ~/.rne dans un tmp_path pour CHAQUE test (autouse). Config & cache
    utilisent tous les deux Path.home(), donc sans cette isolation un test pourrait
    lire/écrire dans le vrai home du dev."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def load_fixture():
    def _load(name: str):
        return json.loads((FIXTURES_DIR / name).read_text())
    return _load


@pytest.fixture
def mock_transport():
    """Factory qui construit un httpx.MockTransport à partir d'un handler."""
    def _make(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
        return httpx.MockTransport(handler)
    return _make
