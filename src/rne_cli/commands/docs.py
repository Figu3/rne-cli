# src/rne_cli/commands/docs.py
"""Commandes bilans & actes."""
from __future__ import annotations

import json

import typer
from rich.console import Console

from rne_cli.commands.company import _make_client
from rne_cli.format import render_attachments
from rne_cli.siren import validate_siren, warn_if_luhn_bad

console = Console()


def _list_attachment(ctx: typer.Context, siren: str, kind: str) -> None:
    from rne_cli.main import _handle_error
    try:
        siren = validate_siren(siren)
        if not ctx.obj.get("json"):
            warn_if_luhn_bad(siren)
        with _make_client(ctx) as c:
            data = c.get_attachments(siren)
        items = data.get(kind, [])
        if ctx.obj.get("json"):
            typer.echo(json.dumps(items, ensure_ascii=False, indent=2))
        else:
            label = {"bilans": "bilan(s)", "actes": "acte(s)"}[kind]
            render_attachments(console, label, items)
    except Exception as e:
        _handle_error(ctx, e)


def bilans_cmd(
    ctx: typer.Context,
    siren: str = typer.Argument(..., help="Numéro SIREN (9 chiffres)."),
):
    """Liste les bilans déposés par une entreprise."""
    _list_attachment(ctx, siren, "bilans")


def actes_cmd(
    ctx: typer.Context,
    siren: str = typer.Argument(..., help="Numéro SIREN (9 chiffres)."),
):
    """Liste les actes déposés par une entreprise."""
    _list_attachment(ctx, siren, "actes")
