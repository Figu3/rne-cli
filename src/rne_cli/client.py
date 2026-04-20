# src/rne_cli/client.py
"""Wrapper httpx autour de l'API INPI RNE."""
from __future__ import annotations

import httpx

from rne_cli.errors import (
    RNEAuthError,
    RNENetworkError,
    RNENotFoundError,
    RNEValidationError,
)

BASE_URL = "https://registre-national-entreprises.inpi.fr"
API_PREFIX = "/api"
DEFAULT_TIMEOUT = 30.0


class Client:
    def __init__(
        self,
        token: str | None = None,
        base_url: str = BASE_URL,
        transport: httpx.BaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url
        self.token = token
        self._http = httpx.Client(
            base_url=base_url,
            transport=transport,
            timeout=timeout,
            headers={"User-Agent": "rne-cli/0.1.0"},
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -------- Auth --------
    def login(self, username: str, password: str) -> str:
        try:
            resp = self._http.post(
                f"{API_PREFIX}/sso/login",
                json={"username": username, "password": password},
            )
        except httpx.TimeoutException as e:
            raise RNENetworkError("Connexion INPI trop lente. Réessaie dans un instant.") from e
        except httpx.HTTPError as e:
            raise RNENetworkError(f"Erreur réseau INPI : {e}") from e

        if resp.status_code == 401:
            raise RNEAuthError("Mauvais identifiants INPI. Vérifie email et mot de passe.")
        if resp.status_code >= 500:
            raise RNENetworkError("Service INPI indisponible. Réessaie plus tard.")
        if resp.status_code != 200:
            raise RNENetworkError(f"Réponse INPI inattendue ({resp.status_code}).")

        data = resp.json()
        token = data.get("token")
        if not token:
            raise RNENetworkError("Réponse INPI sans token.")
        return token
