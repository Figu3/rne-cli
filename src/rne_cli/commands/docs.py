# src/rne_cli/commands/docs.py (stub — real impl in Task 17)
import typer


def bilans_cmd(ctx: typer.Context, siren: str = typer.Argument(...)):
    """[stub]"""
    typer.echo(f"stub bilans {siren}")


def actes_cmd(ctx: typer.Context, siren: str = typer.Argument(...)):
    """[stub]"""
    typer.echo(f"stub actes {siren}")
