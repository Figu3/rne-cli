# src/rne_cli/config.py
"""Lecture/écriture de ~/.rne/config.toml avec permissions 0600."""
from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import tomli_w


CONFIG_DIR_NAME = ".rne"
CONFIG_FILE_NAME = "config.toml"


@dataclass
class Config:
    token: str
    email: str
    saved_at: str  # ISO-8601 UTC


def _config_path() -> Path:
    return Path.home() / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def load_config() -> Optional[Config]:
    """Charge la config. Retourne None si absente."""
    path = _config_path()
    if not path.exists():
        return None
    with path.open("rb") as f:
        data = tomllib.load(f)
    return Config(
        token=data.get("token", ""),
        email=data.get("email", ""),
        saved_at=data.get("saved_at", ""),
    )


def save_config(cfg: Config) -> None:
    """Écrit la config avec permissions 0600. Crée ~/.rne/ si besoin."""
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(cfg)
    with path.open("wb") as f:
        tomli_w.dump(payload, f)
    path.chmod(0o600)


def delete_config() -> None:
    """Supprime la config. Idempotent (no-op si absente)."""
    path = _config_path()
    path.unlink(missing_ok=True)
