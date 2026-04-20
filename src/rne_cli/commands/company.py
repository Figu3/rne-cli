# src/rne_cli/commands/company.py (stub — real impl in Task 16)
import typer


def company_cmd(ctx: typer.Context, siren: str = typer.Argument(...)):
    """[stub]"""
    typer.echo(f"stub company {siren}")


def search_cmd(ctx: typer.Context, name: str = typer.Argument(...)):
    """[stub]"""
    typer.echo(f"stub search {name}")
