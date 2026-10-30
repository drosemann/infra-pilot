"""Welle-2 CLI: lokale Visualisierungs-Helfer (brauchen keine API)."""

import typer

app = typer.Typer(help="Welle 2: Sternenkarte, Aquarium, Morse & Co.")


@app.command()
def morse(health: str = "ok"):
    """Flotten-Health als Morsecode."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave2 import morse_status as _m

    r = _m(health)
    typer.echo(f"{r['klartext']}: {r['morse']}")


@app.command()
def aquarium():
    """Demo: Aquarium-Ansicht aus Beispiel-Daten."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave2 import aquarium as _a

    demo = [{"name": "api", "status": "up", "cpu": 23}, {"name": "worker", "status": "up", "cpu": 91}]
    for f in _a(demo)["fische"]:
        typer.echo(f"{f['name']}: {f['fisch']}")


@app.command()
def wrapped(deploys: int = 0, treuester: str = "-"):
    """Mini Fleet-Wrapped aus Kennzahlen."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave2 import fleet_wrapped as _w

    typer.echo(_w({"deploys_total": deploys, "longest_uptime_app": treuester}))
