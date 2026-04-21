# src/rne_cli/commands/company.py
"""Commandes company & search."""
from __future__ import annotations

import json

import typer
from rich.console import Console

from rne_cli.client import Client
from rne_cli.config import load_config
from rne_cli.errors import RNEAuthError
from rne_cli.format import render_company, render_search_results
from rne_cli.siren import validate_siren, warn_if_luhn_bad

console = Console()


def _make_client(ctx: typer.Context) -> Client:
    cfg = load_config()
    if cfg is None or not cfg.token:
        raise RNEAuthError("Pas de token INPI configuré. Lance 'rne login' pour t'authentifier.")
    return Client(token=cfg.token, use_cache=not ctx.obj.get("no_cache", False))


def company_cmd(
    ctx: typer.Context,
    siren: str = typer.Argument(..., help="Numéro SIREN (9 chiffres)."),
):
    """Affiche la fiche d'une entreprise."""
    from rne_cli.main import _handle_error
    try:
        siren = validate_siren(siren)
        if not ctx.obj.get("json"):
            warn_if_luhn_bad(siren)
        with _make_client(ctx) as c:
            data = c.get_company(siren)
        if ctx.obj.get("json"):
            typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            render_company(console, data)
    except Exception as e:
        _handle_error(ctx, e)


def search_cmd(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Dénomination (ou fragment)."),
    limit: int = typer.Option(20, "--limit", "-n", min=1, max=100, help="Nombre max de résultats."),
):
    """Cherche une entreprise par dénomination."""
    from rne_cli.main import _handle_error
    try:
        with _make_client(ctx) as c:
            results = c.search(name, limit=limit)
        if ctx.obj.get("json"):
            typer.echo(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            render_search_results(console, results)
    except Exception as e:
        _handle_error(ctx, e)
