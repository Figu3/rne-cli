import json
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from rne_cli.format import render_company, render_search_results, render_attachments, render_history


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _capture(fn, *args, **kwargs) -> str:
    buf = StringIO()
    console = Console(file=buf, record=False, width=120, color_system=None)
    fn(console, *args, **kwargs)
    return buf.getvalue()


def test_render_company_includes_denomination():
    data = json.loads((FIXTURES_DIR / "company_sas.json").read_text())
    out = _capture(render_company, data)
    assert "L'OREAL" in out
    assert "732829320" in out


def test_render_company_missing_fields_graceful():
    # Protocol resilience: missing nested keys shouldn't crash
    out = _capture(render_company, {"siren": "000000000"})
    assert "000000000" in out
