# src/rne_cli/errors.py
"""Hiérarchie d'exceptions pour rne-cli. Toutes portent un message en français, orienté action."""


class RNEError(Exception):
    """Base class. Porte un message FR et un exit_code."""

    exit_code = 1

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class RNEAuthError(RNEError):
    """401 ou token manquant."""
    exit_code = 1


class RNENotFoundError(RNEError):
    """404 (SIREN inconnu)."""
    exit_code = 1


class RNEValidationError(RNEError):
    """Argument utilisateur invalide (SIREN malformé, limit négatif, etc.)."""
    exit_code = 1


class RNENetworkError(RNEError):
    """Timeout, 5xx, 429, JSON malformé."""
    exit_code = 2
