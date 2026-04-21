# src/rne_cli/siren.py
"""Validation SIREN : format (9 chiffres) obligatoire, Luhn informatif."""
import re

from rne_cli.errors import RNEValidationError

_SIREN_RE = re.compile(r"^\d{9}$")


def validate_siren(raw: str) -> str:
    """Retourne le SIREN normalisé (trimmed). Lève RNEValidationError sinon."""
    s = raw.strip() if raw else ""
    if not _SIREN_RE.match(s):
        raise RNEValidationError(
            f'Le SIREN doit faire 9 chiffres (reçu : "{raw}"). Vérifie le numéro.'
        )
    return s


def luhn_valid(siren: str) -> bool:
    """Vérifie la clé Luhn du SIREN. Informatif — certains SIREN valides à l'INPI
    ne passent pas Luhn (entités anciennes)."""
    total = 0
    for i, ch in enumerate(reversed(siren)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def check_siren(raw: str) -> tuple[str, bool]:
    """Valide + informe sur Luhn. Retourne (siren_normalisé, luhn_ok).
    Lève RNEValidationError si le format 9-chiffres est mauvais."""
    s = validate_siren(raw)
    return s, luhn_valid(s)


def warn_if_luhn_bad(siren: str) -> None:
    """Affiche un warning stderr si le SIREN ne passe pas Luhn. Muet sinon."""
    if not luhn_valid(siren):
        from rich.console import Console
        Console(stderr=True).print(
            f"[yellow]⚠ Le SIREN {siren} ne passe pas la clé Luhn — vérifie qu'il n'y a pas de faute de frappe.[/]"
        )
