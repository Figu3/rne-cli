# rne-cli

CLI pour l'API [Registre National des Entreprises](https://data.inpi.fr/) de l'INPI. Pensée pour les humains **et** pour les agents LLM (sortie `--json` sur toutes les commandes).

## Installation

```bash
pipx install rne-cli
# ou
uv tool install rne-cli
```

## Obtenir un token INPI

1. Crée un compte gratuit sur https://data.inpi.fr
2. Lance `rne login` et entre ton email + mot de passe INPI
3. C'est tout. Le token est stocké dans `~/.rne/config.toml` (chmod 0600).

Tu peux aussi passer un token existant : `rne login --token <JWT>`.

## Exemples

```bash
# Fiche entreprise (L'Oréal)
rne company 732829320

# Recherche par dénomination
rne search "Danone" --limit 10

# Bilans et actes déposés
rne bilans 732829320
rne actes 732829320

# Historique des modifications sur 1 an
rne historique 732829320

# Mode JSON pour scripter
rne company 732829320 --json | jq .
```

## Utiliser avec Claude Code

Tu peux poser une question en langage naturel, et Claude appellera la CLI pour y répondre :

> « Donne-moi les bilans déposés par L'Oréal en 2024 »

Claude va lancer `rne search "L'Oréal" --json` pour trouver le SIREN, puis `rne bilans 732829320 --json` et te présenter la réponse.

## Configuration

- Token : `~/.rne/config.toml` (permissions 0600)
- Cache : `~/.rne/cache/` (TTL 24h, efface avec `rm -rf ~/.rne/cache/`)
- Flags globaux : `--json`, `--no-cache`, `--verbose`, `--version`

## Limites V1

- `rne dirigeant` n'est pas supporté (l'API RNE ne permet pas la recherche par nom de personne physique). Utilise https://annuaire-entreprises.data.gouv.fr/ pour ça.
- Quota INPI : 10 000 requêtes / 10 Go par jour par compte.

## Développement

```bash
git clone <repo>
cd rne-cli
pip install -e ".[dev]"
pytest
```

## License

MIT
