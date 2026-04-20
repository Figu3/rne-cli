# src/rne_cli/commands/people.py
"""Stub pour `rne dirigeant` — non supporté par l'API RNE publique en V1."""
import json

import typer
from rich.console import Console

console = Console()


def dirigeant_cmd(
    ctx: typer.Context,
    nom: str = typer.Argument(..., help="Nom (et prénom) du dirigeant."),
):
    """[Non supporté en V1] Recherche par nom de dirigeant."""
    if ctx.obj.get("json"):
        payload = {
            "error": "La recherche par nom de dirigeant n'est pas supportée par l'API RNE publique.",
            "hint_cli": f'rne search "{nom}"',
            "hint_url": "https://annuaire-entreprises.data.gouv.fr/",
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        console.print(
            "[yellow]La recherche par nom de dirigeant n'est pas supportée par l'API RNE publique.[/]\n"
            f'Essaie [bold]rne search "{nom}"[/] pour chercher par dénomination d\'entreprise,\n'
            "ou consulte [link]https://annuaire-entreprises.data.gouv.fr/[/] qui indexe les dirigeants."
        )
    raise typer.Exit(code=1)
