---
date: 2026-04-20
topic: rne-cli
status: approved-design
---

# `rne-cli` — CLI INPI grand public pour le Registre National des Entreprises

## 1. Contexte & objectifs

Construire une CLI Python qui expose l'API RNE (Registre National des Entreprises) de l'INPI à un public non-technique (avocats, journalistes, chercheurs, curieux) et qui sert aussi de backend pour un agent LLM (Claude Code, Codex) traduisant des questions en langage naturel en commandes CLI.

Double surface d'usage :
- **Humain** : sortie Rich en français (tableaux colorés, messages actionnables).
- **Machine/LLM** : sortie JSON via `--json` sur chaque commande retournant des données.

Positionnement DevRel pour l'INPI : code propre, documenté, packageable `pipx install`. Livraison = repo GitHub public MIT.

## 2. Scope V1

### Inclus
- Auth : `rne login` (interactif email+password), `rne login --token <JWT>` (headless/CI), `rne logout`, `rne whoami`.
- Lectures : `rne company <siren>`, `rne search "<dénomination>"`, `rne bilans <siren>`, `rne actes <siren>`, `rne historique <siren>`.
- Mode humain (Rich) et mode `--json`.
- Cache disque 24h sur GET idempotents.
- Validation SIREN côté client.
- Packaging `pipx install .` + `uv tool install .`.
- README avec installation, obtention du token, 5 exemples humains, section « Utiliser avec Claude Code ».
- Tests pytest ≥ 70% sur `client.py` et `format.py`, sans appel réseau.

### Exclus (V2 ou jamais)
- `rne dirigeant "<nom>"` — retirée de la V1 car l'API `/companies` n'expose pas de filtre par nom de personne physique. Un stub est gardé pour renvoyer un message explicite vers `rne search` plutôt que promettre ce qu'on ne peut pas livrer.
- API marques, brevets, dessins.
- Guichet unique / formalités.
- Wrapper Web.
- Mode `--explain` avec LLM intégré.

## 3. Endpoints INPI (vérifiés contre la doc technique v4.0)

Base URL production : `https://registre-national-entreprises.inpi.fr/api`

| Commande CLI | Méthode | Endpoint | Notes |
|---|---|---|---|
| `rne login` | `POST` | `/sso/login` | body `{username, password}` → `{token}` (JWT) |
| `rne company <siren>` | `GET` | `/companies/{siren}` | fiche complète |
| `rne search "<nom>"` | `GET` | `/companies?companyName=<nom>&page=&pageSize=` | pagination côté client |
| `rne bilans <siren>` | `GET` | `/companies/{siren}/attachments` | filtre `bilans[]` de la réponse |
| `rne actes <siren>` | `GET` | `/companies/{siren}/attachments` | filtre `actes[]` de la réponse |
| `rne historique <siren>` | `GET` | `/companies/diff?siren[]=<siren>&from=&to=` | params `from`/`to` en `YYYY-MM-DD` |
| `rne dirigeant "<nom>"` | — | — | stub, renvoie un message explicite, pas d'appel API |

Authentification : header `Authorization: Bearer <JWT>` sur tout sauf `/sso/login`.

Codes HTTP et erreurs transport attendus :
- 200 OK
- 401 token manquant/expiré → `RNEAuthError`
- 404 SIREN inconnu → `RNENotFoundError`
- 429 rate limit → `RNENetworkError` avec message « quota INPI atteint, réessaie plus tard »
- 5xx → `RNENetworkError`
- `httpx.TimeoutException`, `httpx.ConnectError`, `httpx.RemoteProtocolError` → `RNENetworkError` avec message « Connexion INPI impossible ou lente. Vérifie ta connexion réseau. »

Quotas documentés par INPI : 10 000 requêtes/jour et 10 Go/jour par compte (tier standard gratuit). Rien à gérer proactivement côté CLI ; on laisse remonter le 429 si ça tape.

## 4. Architecture

### Structure du repo

```
rne-cli/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/rne_cli/
│   ├── __init__.py
│   ├── main.py           # entry point Typer, sous-apps montées
│   ├── client.py         # wrapper httpx autour de l'API INPI
│   ├── config.py         # gestion ~/.rne/config.toml
│   ├── cache.py          # cache disque JSON
│   ├── format.py         # rendu Rich (tableaux entreprise, bilans, etc.)
│   ├── errors.py         # exceptions custom + handler Typer global
│   ├── siren.py          # validation (regex + Luhn)
│   └── commands/
│       ├── __init__.py
│       ├── auth.py       # login, logout, whoami
│       ├── company.py    # company, search
│       ├── people.py     # dirigeant (stub)
│       ├── docs.py       # bilans, actes
│       └── history.py    # historique
├── docs/
│   └── superpowers/specs/2026-04-20-rne-cli-design.md
└── tests/
    ├── conftest.py
    ├── test_client.py
    ├── test_format.py
    ├── test_config.py
    ├── test_siren.py
    └── fixtures/
        ├── company_sas.json
        ├── company_sarl.json
        ├── company_microentreprise.json
        ├── attachments.json
        └── search_results.json
```

### Flow d'exécution

```
main.py (Typer)
  ├── @app.callback() : lit les flags globaux --json / --no-cache / --verbose
  │                     → stocke {"json": bool, "no_cache": bool, "verbose": bool} dans ctx.obj
  ├── error_handler : wrap chaque commande, map RNEError → message FR + exit code
  │
  └── commands/*.py
        ├── valide les arguments (ex: SIREN)
        ├── appelle client.py
        │     ├── charge token depuis config.py
        │     ├── tente cache (cache.py)
        │     ├── sinon httpx.get/post avec Bearer
        │     ├── map status codes → exceptions custom
        │     └── stocke en cache si succès
        └── rend via format.py (Rich) OU json.dumps
```

## 5. Décisions de design

### 5.1. Authentification (option 3 — dual-mode)

- `rne login` (interactif) : prompt email (visible) + `getpass` password (masqué) → POST `/sso/login` → stocke `{token, email, saved_at}` dans `~/.rne/config.toml` avec `chmod 0600`.
- `rne login --token <JWT>` : stocke directement le token fourni, sans appel API. `email` laissé vide. Utile pour CI / scripts. Contrepartie : un token invalide ne sera détecté qu'au premier vrai appel (on ne valide pas pro-activement pour rester offline). Acceptable pour V1. En V2 on pourra ajouter `rne whoami --validate` qui tape un GET léger.
- `rne logout` : supprime `~/.rne/config.toml`.
- `rne whoami` : affiche `email` et date de sauvegarde. Si pas de token → message actionnable « lance `rne login` ».
- Sur 401 en cours d'usage : `RNEAuthError` → message « Token INPI expiré ou invalide. Lance `rne login` pour le renouveler. » + exit 1.
- Pas de refresh token côté INPI → pas de logique de refresh côté CLI.

### 5.2. Cache

- Appliqué uniquement aux GET idempotents : `company`, `search`, `bilans`, `actes`, `historique`.
- Clé : `sha256(method + endpoint + sorted(query_params))`.
- Stockage : `~/.rne/cache/<hash>.json`, contenu `{data, fetched_at, endpoint, params}`.
- TTL : 24h (configurable via env `RNE_CACHE_TTL` en secondes, pas exposé en flag pour garder la CLI simple).
- Hit : renvoie `data`. Miss ou expiré : refetch + rewrite.
- `--no-cache` : force refetch (mais réécrit le cache pour la prochaine fois).
- Invalidation manuelle : `rm -rf ~/.rne/cache/` (documenté dans `--help`). Pas de commande `rne cache clear` en V1 (YAGNI).
- **Interaction avec la pagination** : chaque page (`page=1`, `page=2`, ...) est cachée indépendamment. C'est volontaire : si `search` a déjà ramené page 1 et 2 hier et qu'on relance aujourd'hui avec `--limit 40`, on sert page 1 et 2 depuis le cache et on ne refetch que page 3+. Conséquence acceptée : les résultats peuvent mélanger des pages de fraîcheurs différentes dans la même commande. Non-bug, ne pas « corriger ».

### 5.3. Pagination

- `client.iter_pages(endpoint, params, limit)` : générateur qui boucle sur `page=1, 2, ...` jusqu'à atteindre `limit` résultats ou page vide (`len(results) == 0`).
- Commandes reçoivent une liste plate (déjà tronquée à `limit`).
- Défaut `--limit 20`, max 100, min 1. `--limit 0` ou négatif → `RNEValidationError` avant tout appel réseau.
- `pageSize` envoyé à l'API = 20 (fixe, on ne surcharge pas l'API avec des gros pages si le user veut 10 résultats).

### 5.4. Validation SIREN

- Regex `^\d{9}$` obligatoire.
- Luhn optionnel (warning, pas blocage) pour ne pas rejeter des SIREN valides que l'INPI connaît mais qui ne passent pas Luhn (cas réel sur certaines entités anciennes).
- Erreur claire avant tout appel réseau : `Le SIREN doit faire 9 chiffres (reçu : "12345"). Vérifie le numéro.`
- Luhn : 10 lignes Python pur, pas de dépendance externe.

### 5.5. Mode JSON vs humain

- Flag global `--json` sur l'app Typer (pas sur chaque commande), stocké dans `ctx.obj["json"]`.
- Chaque commande termine par :
  ```python
  if ctx.obj["json"]:
      typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
  else:
      format.render_company(data)  # ou render_search, etc.
  ```
- Le JSON émis est le JSON brut de l'API INPI (zéro transformation) pour que les consommateurs LLM aient la même surface que la doc officielle.

### 5.6. Erreurs

Hiérarchie :
```python
class RNEError(Exception): ...
class RNEAuthError(RNEError): ...          # 401, token absent
class RNENotFoundError(RNEError): ...       # 404, SIREN inconnu
class RNEValidationError(RNEError): ...     # SIREN malformé, etc.
class RNENetworkError(RNEError): ...        # timeout, 5xx, 429
```

Chaque exception porte un `message` en français, orienté action. Le handler Typer global (`@app.callback()` via `try/except`) map :
- `RNEValidationError`, `RNENotFoundError`, `RNEAuthError` → exit code 1
- `RNENetworkError` → exit code 2
- Affiche le message via `typer.echo(..., err=True)` en rouge (Rich) sauf si `--json` (alors `{"error": "...", "code": "..."}` sur stderr).

Pas de stack trace jamais, sauf `--verbose` (flag global débug).

### 5.7. Exit codes

- `0` : succès (inclut « zéro résultat trouvé » pour `search`, qui n'est pas une erreur).
- `1` : erreur utilisateur (SIREN invalide, not found, token manquant, mauvais args).
- `2` : erreur réseau / API (timeout, 5xx, 429, JSON malformé).

## 6. Tests

### 6.1. Stratégie

- `pytest` avec `httpx.MockTransport` injecté via fixture `mock_inpi` dans `conftest.py`.
- Aucun appel réseau réel (`pytest` doit tourner offline).
- Fixtures JSON dans `tests/fixtures/` : réponses INPI réalistes, anonymisées si nécessaires.
- Objectif couverture : ≥ 70% sur `client.py` et `format.py`. Le reste best-effort.

### 6.2. Cas couverts

`test_client.py` :
- `login()` happy path → token stocké
- `login()` 401 → `RNEAuthError`
- `get_company()` happy path
- `get_company()` 404 → `RNENotFoundError`
- `get_company()` 401 (token expiré) → `RNEAuthError`
- `search()` pagination multi-pages
- `search()` limit respecté (pas plus de N résultats)
- Cache hit (pas de call HTTP la 2e fois)
- Cache miss (TTL expiré → refetch)
- `--no-cache` → skip cache

`test_format.py` :
- Rendu fiche entreprise (snapshot via `console.record()`)
- Rendu liste bilans (tableau)
- Rendu résultats de recherche (tableau)
- Rendu historique (timeline)
- Rendu « aucun résultat » (message amical)

`test_config.py` :
- Round-trip save/load TOML
- Permissions 0600 vérifiées après save
- Config absente → `None` (pas d'exception)
- `logout` : après save puis logout, la config est bien supprimée et un load renvoie `None`

`test_siren.py` :
- 9 chiffres valides → OK
- 8 ou 10 chiffres → `RNEValidationError`
- Non-numérique → `RNEValidationError`
- Luhn valide → OK
- Luhn invalide → warning mais pas d'exception

## 7. Packaging

### `pyproject.toml` (schéma)

```toml
[project]
name = "rne-cli"
version = "0.1.0"
description = "CLI pour l'API Registre National des Entreprises (INPI)"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "httpx>=0.27",
    "rich>=13.7",
    "tomli-w>=1.0",       # écriture TOML (tomllib est stdlib pour la lecture en 3.11+)
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov>=5"]

[project.scripts]
rne = "rne_cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Installation cible

```bash
pipx install .
# ou
uv tool install .
```

## 8. README (structure)

1. Pitch (1 paragraphe FR).
2. Installation (`pipx`, `uv`).
3. Obtenir un token INPI — 3 étapes avec lien vers https://data.inpi.fr.
4. 5 exemples humains (company, search, bilans, actes, historique).
5. Mode JSON pour scripts.
6. Section « Utiliser avec Claude Code » — exemple de question naturelle → commande.
7. Configuration (`~/.rne/config.toml`).
8. Contributing / License.

## 9. Livraison GitHub

- `gh repo create rne-cli --public --description "CLI pour l'API Registre National des Entreprises (INPI)" --source . --remote origin --push` en toute fin de parcours, après que tous les tests passent.
- Pas de workflow GitHub Actions en V1 (YAGNI, on ajoute quand on a un vrai besoin).

## 10. Ordre d'implémentation

1. `pyproject.toml` + structure de dossiers + `.gitignore` + `LICENSE` MIT.
2. `errors.py` + `siren.py` + tests unitaires associés.
3. `config.py` + test round-trip TOML.
4. `client.py` squelette avec `login()` et `get_company()` + tests mockés.
5. `cache.py` + intégration dans `client.py` + tests.
6. `format.py` — rendu fiche entreprise (le plus visible).
7. `main.py` + `commands/auth.py` + `commands/company.py` (boucle minimale fonctionnelle).
8. Étendre : `search`, `bilans`, `actes`, `historique`.
9. `commands/people.py` (stub).
10. README + screenshots `--help`.
11. Tests couverture ≥ 70% sur `client.py` et `format.py`.
12. `gh repo create` et push.
