# src/rne_cli/commands/auth.py
"""Commandes d'authentification."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from getpass import getpass

import typer
from rich.console import Console

from rne_cli.client import Client
from rne_cli.config import Config, delete_config, load_config, save_config

console = Console()


def login(
    ctx: typer.Context,
    token: str | None = typer.Option(None, "--token", help="Token JWT (skip le flow interactif)."),
    email: str | None = typer.Option(None, "--email", help="Email INPI (sinon prompt)."),
):
    """Configure le token INPI (interactif ou via --token pour CI)."""
    from rne_cli.main import _handle_error
    try:
        if token:
            cfg = Config(token=token, email=email or "", saved_at=datetime.now(timezone.utc).isoformat())
            save_config(cfg)
            console.print("[green]Token enregistré.[/]")
            return

        if email is None:
            email = typer.prompt("Email INPI")
        password = getpass("Mot de passe INPI : ")
        with Client() as c:
            jwt = c.login(email, password)
        cfg = Config(token=jwt, email=email, saved_at=datetime.now(timezone.utc).isoformat())
        save_config(cfg)
        console.print(f"[green]Connecté en tant que[/] [bold]{email}[/].")
    except Exception as e:
        _handle_error(ctx, e)


def logout(ctx: typer.Context):
    """Supprime le token local."""
    from rne_cli.main import _handle_error
    try:
        delete_config()
        console.print("[green]Déconnecté.[/]")
    except Exception as e:
        _handle_error(ctx, e)


def whoami(ctx: typer.Context):
    """Affiche l'utilisateur connecté."""
    from rne_cli.main import _handle_error
    try:
        cfg = load_config()
        if cfg is None or not cfg.token:
            console.print("[yellow]Pas de token INPI configuré.[/] Lance [bold]rne login[/].")
            raise typer.Exit(code=1)
        if ctx.obj.get("json"):
            typer.echo(json.dumps({"email": cfg.email, "saved_at": cfg.saved_at}, ensure_ascii=False, indent=2))
        else:
            console.print(f"Connecté : [bold]{cfg.email or '(token seul)'}[/]")
            console.print(f"Sauvegardé : {cfg.saved_at}")
    except typer.Exit:
        raise
    except Exception as e:
        _handle_error(ctx, e)
