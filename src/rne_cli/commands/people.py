# src/rne_cli/commands/people.py (stub — real impl in Task 19)
import typer


def dirigeant_cmd(ctx: typer.Context, nom: str = typer.Argument(...)):
    """[stub]"""
    typer.echo(f"stub dirigeant {nom}")
