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
        use_cache: bool = True,
        cache_ttl: int = 24 * 3600,
    ):
        self.base_url = base_url
        self.token = token
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
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
        except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
            raise RNENetworkError("Connexion INPI impossible ou lente. Vérifie ta connexion réseau.") from e
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

    # -------- Helpers --------
    def _auth_headers(self) -> dict[str, str]:
        if not self.token:
            raise RNEAuthError("Pas de token INPI configuré. Lance 'rne login' pour t'authentifier.")
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        """`path` must be api-relative, e.g. '/companies/732829320'. The API prefix
        is added here so callers don't have to remember it."""
        try:
            resp = self._http.get(
                f"{API_PREFIX}{path}",
                params=params,
                headers=self._auth_headers(),
            )
        except httpx.TimeoutException as e:
            raise RNENetworkError("Connexion INPI trop lente. Réessaie dans un instant.") from e
        except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
            raise RNENetworkError("Connexion INPI impossible ou lente. Vérifie ta connexion réseau.") from e
        except httpx.HTTPError as e:
            raise RNENetworkError(f"Erreur réseau INPI : {e}") from e
        return resp

    def _check(self, resp: httpx.Response, not_found_msg: str) -> None:
        if resp.status_code == 401:
            raise RNEAuthError("Token INPI expiré ou invalide. Lance 'rne login' pour le renouveler.")
        if resp.status_code == 404:
            raise RNENotFoundError(not_found_msg)
        if resp.status_code == 429:
            raise RNENetworkError("Quota INPI atteint, réessaie plus tard.")
        if resp.status_code >= 500:
            raise RNENetworkError(f"Service INPI indisponible ({resp.status_code}).")
        if resp.status_code != 200:
            raise RNENetworkError(f"Réponse INPI inattendue ({resp.status_code}).")

    def _cached_get_json(self, path: str, params: dict | None, not_found_msg: str):
        """Lit depuis le cache si use_cache et frais. Écrit toujours (même si
        use_cache=False) pour que le prochain appel bénéficie du cache — cf
        spec §5.2: '--no-cache force refetch mais réécrit le cache'."""
        from rne_cli.cache import cache_get, cache_key, cache_put
        params = params or {}
        key = cache_key("GET", path, params)
        if self.use_cache:
            cached = cache_get(key, ttl_seconds=self.cache_ttl)
            if cached is not None:
                return cached
        resp = self._get(path, params=params)
        self._check(resp, not_found_msg)
        data = resp.json()
        cache_put(key, data)  # always write, regardless of use_cache
        return data

    # -------- Company --------
    def get_company(self, siren: str) -> dict:
        return self._cached_get_json(
            f"/companies/{siren}",
            params=None,
            not_found_msg=f"Aucune entreprise trouvée pour le SIREN {siren}. Vérifie le numéro (9 chiffres).",
        )

    # -------- Search --------
    PAGE_SIZE = 20  # fixé : on ne surcharge pas l'API

    def search(self, company_name: str, limit: int = 20) -> list[dict]:
        if limit < 1 or limit > 100:
            raise RNEValidationError(
                f"limit doit être entre 1 et 100 (reçu : {limit})."
            )
        results: list[dict] = []
        page = 1
        while len(results) < limit:
            items = self._cached_get_json(
                "/companies",
                params={"companyName": company_name, "page": page, "pageSize": self.PAGE_SIZE},
                not_found_msg=f"Aucun résultat pour '{company_name}'.",
            )
            if not items:
                break
            results.extend(items)
            if len(items) < self.PAGE_SIZE:
                break
            page += 1
        return results[:limit]

    # -------- Attachments (bilans + actes) --------
    def get_attachments(self, siren: str) -> dict:
        data = self._cached_get_json(
            f"/companies/{siren}/attachments",
            params=None,
            not_found_msg=f"Aucune pièce jointe trouvée pour le SIREN {siren}.",
        )
        return {"bilans": data.get("bilans", []), "actes": data.get("actes", [])}

    # -------- History / diff --------
    def get_history(self, siren: str, date_from: str, date_to: str) -> list[dict]:
        data = self._cached_get_json(
            "/companies/diff",
            params={"siren[]": siren, "from": date_from, "to": date_to, "pageSize": 100},
            not_found_msg=f"Aucun historique trouvé pour le SIREN {siren}.",
        )
        return data if isinstance(data, list) else data.get("results", [])
