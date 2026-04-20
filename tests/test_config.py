import os
import stat
from pathlib import Path

import pytest

from rne_cli.config import Config, load_config, save_config, delete_config


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    # Force re-evaluation of Path.home()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


class TestSaveLoad:
    def test_roundtrip(self, fake_home):
        cfg = Config(token="jwt-abc", email="me@example.com", saved_at="2026-04-20T10:00:00Z")
        save_config(cfg)
        loaded = load_config()
        assert loaded.token == "jwt-abc"
        assert loaded.email == "me@example.com"
        assert loaded.saved_at == "2026-04-20T10:00:00Z"

    def test_file_permissions_0600(self, fake_home):
        cfg = Config(token="x", email="", saved_at="")
        save_config(cfg)
        path = fake_home / ".rne" / "config.toml"
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600

    def test_missing_returns_none(self, fake_home):
        assert load_config() is None


class TestDelete:
    def test_delete_removes_file(self, fake_home):
        save_config(Config(token="x", email="", saved_at=""))
        assert (fake_home / ".rne" / "config.toml").exists()
        delete_config()
        assert not (fake_home / ".rne" / "config.toml").exists()
        assert load_config() is None

    def test_delete_idempotent(self, fake_home):
        # No exception when file doesn't exist
        delete_config()
