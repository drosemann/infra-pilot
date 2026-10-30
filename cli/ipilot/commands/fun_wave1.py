"""Welle-1 CLI: lokale Spass-Befehle (brauchen keine API)."""

import typer

app = typer.Typer(help="Welle 1: Deploy-Wetter, Horoskope, Seismograph & Co.")


@app.command()
def wetter(freitag: bool = False, fehlerquote: float = 0.0, incidents: int = 0):
    """Deploy-Wetterbericht (rein informativ, blockiert nie)."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave1 import deploy_wetter as _w

    typer.echo(_w(freitag, fehlerquote, incidents))


@app.command()
def horoskop(app_name: str):
    """Tages-Horoskop fuer eine App."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave1 import horoskop as _h

    typer.echo(_h(app_name)["text"])


@app.command()
def blame_poetic(ursache: str):
    """Gescheiterte Aenderung als Haiku + echte Ursache."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave1 import blame_poetic as _b

    r = _b(ursache)
    typer.echo(r["haiku"])
    typer.echo(f"Ursache: {r['cause']}")
