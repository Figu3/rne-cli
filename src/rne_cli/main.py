# src/rne_cli/main.py
"""Entry point Typer pour rne-cli."""
from __future__ import annotations

import json
import sys

import typer
from rich.console import Console

from rne_cli import __version__
from rne_cli.errors import RNEError

app = typer.Typer(
    name="rne",
    help="CLI pour l'API Registre National des Entreprises (INPI).",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

err_console = Console(stderr=True)


def _version_callback(value: bool):
    if value:
        typer.echo(f"rne-cli {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    ctx: typer.Context,
    json_out: bool = typer.Option(False, "--json", help="Sortie JSON brute (pour scripts et LLM)."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Force le refetch depuis l'API."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Affiche les stack traces complètes sur erreur."),
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True, help="Affiche la version."),
):
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_out
    ctx.obj["no_cache"] = no_cache
    ctx.obj["verbose"] = verbose


def _handle_error(ctx: typer.Context, exc: Exception) -> None:
    """Map une exception en message FR + exit code. Ré-raise si --verbose."""
    if ctx.obj.get("verbose"):
        raise exc
    if isinstance(exc, RNEError):
        if ctx.obj.get("json"):
            err_console.print_json(json.dumps({"error": exc.message, "code": exc.__class__.__name__}))
        else:
            err_console.print(f"[red]Erreur :[/] {exc.message}")
        raise typer.Exit(code=exc.exit_code)
    err_console.print(f"[red]Erreur inattendue :[/] {exc}")
    raise typer.Exit(code=2)


from rne_cli.commands import auth, company, docs, history, people  # noqa: E402

app.command("login")(auth.login)
app.command("logout")(auth.logout)
app.command("whoami")(auth.whoami)
app.command("company")(company.company_cmd)
app.command("search")(company.search_cmd)
app.command("bilans")(docs.bilans_cmd)
app.command("actes")(docs.actes_cmd)
app.command("historique")(history.history_cmd)
app.command("dirigeant")(people.dirigeant_cmd)


if __name__ == "__main__":
    app()
