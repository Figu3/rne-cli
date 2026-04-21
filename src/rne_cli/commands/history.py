# src/rne_cli/commands/history.py
"""Commande historique (diffs INPI)."""
from __future__ import annotations

import json
from datetime import date, timedelta

import typer
from rich.console import Console

from rne_cli.commands.company import _make_client
from rne_cli.format import render_history
from rne_cli.siren import validate_siren, warn_if_luhn_bad

console = Console()


def history_cmd(
    ctx: typer.Context,
    siren: str = typer.Argument(..., help="Numéro SIREN (9 chiffres)."),
    date_from: str = typer.Option(None, "--from", help="Date début (YYYY-MM-DD). Défaut : il y a 1 an."),
    date_to: str = typer.Option(None, "--to", help="Date fin (YYYY-MM-DD). Défaut : aujourd'hui."),
):
    """Affiche l'historique des modifications d'une entreprise."""
    from rne_cli.main import _handle_error
    try:
        siren = validate_siren(siren)
        if not ctx.obj.get("json"):
            warn_if_luhn_bad(siren)
        today = date.today()
        date_to = date_to or today.isoformat()
        date_from = date_from or (today - timedelta(days=365)).isoformat()
        with _make_client(ctx) as c:
            changes = c.get_history(siren, date_from=date_from, date_to=date_to)
        if ctx.obj.get("json"):
            typer.echo(json.dumps(changes, ensure_ascii=False, indent=2))
        else:
            render_history(console, changes)
    except Exception as e:
        _handle_error(ctx, e)
