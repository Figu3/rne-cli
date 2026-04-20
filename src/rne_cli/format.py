"""Rendu Rich (tableaux français) pour la CLI humaine."""
from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table


def _dig(d: dict, *keys: str, default: Any = "—") -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur if cur not in ("", None) else default


def render_company(console: Console, data: dict) -> None:
    siren = data.get("siren", "—")
    entreprise = _dig(data, "formality", "content", "personneMorale", "identite", "entreprise", default={})
    if not isinstance(entreprise, dict):
        entreprise = {}
    denom = entreprise.get("denomination", "—")
    forme = entreprise.get("formeJuridique", "—")
    creation = entreprise.get("dateCreation", "—")

    table = Table(title=f"Entreprise {siren}", show_header=False, title_style="bold cyan")
    table.add_column("Champ", style="dim")
    table.add_column("Valeur")
    table.add_row("SIREN", siren)
    table.add_row("Dénomination", str(denom))
    table.add_row("Forme juridique", str(forme))
    table.add_row("Date de création", str(creation))
    console.print(table)


def render_search_results(console: Console, results: list[dict]) -> None:
    if not results:
        console.print("[yellow]Aucun résultat.[/]")
        return
    table = Table(title=f"{len(results)} résultat(s)", title_style="bold cyan")
    table.add_column("SIREN", style="green")
    table.add_column("Dénomination")
    for r in results:
        siren = r.get("siren", "—")
        denom = _dig(r, "formality", "content", "personneMorale", "identite", "entreprise", "denomination")
        table.add_row(str(siren), str(denom))
    console.print(table)


def render_attachments(console: Console, kind: str, items: list[dict]) -> None:
    if not items:
        console.print(f"[yellow]Aucun {kind}.[/]")
        return
    table = Table(title=f"{len(items)} {kind}", title_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Date dépôt", style="green")
    table.add_column("Type")
    table.add_column("Description")
    for it in items:
        table.add_row(
            str(it.get("id", "—")),
            str(it.get("dateDepot", "—")),
            str(it.get("typeBilan") or it.get("typeActe") or "—"),
            str(it.get("nomDocument") or it.get("dateCloture") or "—"),
        )
    console.print(table)


def render_history(console: Console, changes: list[dict]) -> None:
    if not changes:
        console.print("[yellow]Aucune modification sur cette période.[/]")
        return
    table = Table(title=f"{len(changes)} modification(s)", title_style="bold cyan")
    table.add_column("Date", style="green")
    table.add_column("SIREN", style="dim")
    table.add_column("Changement")
    for c in changes:
        table.add_row(
            str(c.get("submitDate", "—")),
            str(c.get("siren", "—")),
            str(c.get("change", "—")),
        )
    console.print(table)
