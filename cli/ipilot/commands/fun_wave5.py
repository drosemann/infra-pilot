"""Welle-5 CLI: Story- und Ritual-Befehle (lokal, brauchen keine API)."""

import typer

app = typer.Typer(help="Welle 5: Krimi, Tagebuch, Memorial & Co.")


@app.command()
def krimi(opfer: str, tatzeit: str, aufloesung: str, verdaechtige: str = "deploy,config"):
    """Incident als Krimi-Kapitel (Fakten echt, Ton Dekor)."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave5 import incident_krimi as _k

    r = _k(opfer, tatzeit, verdaechtige.split(","), aufloesung)
    typer.echo(r["titel"])
    typer.echo(r["kapitel"])


@app.command()
def tagebuch(app_name: str, restarts: int = 0):
    """Deploy-Tagebuch aus Containersicht."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave5 import tagebuch as _t

    typer.echo(_t(app_name, restarts)["eintrag"])


@app.command()
def erklaeren(apps_up: int = 0, technisch: bool = False):
    """Neuling-Modus: Flottenzustand ganz einfach erklaert."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave5 import neuling_erklaerung as _n

    typer.echo(_n({"apps_up": apps_up}, technisch)["text"])


@app.command()
def abschied(app_name: str, uptime_tage: int = 0, letztes_log: str = "-"):
    """Container wuerdevoll stilllegen (Testament + Archiv)."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave5 import abschied as _a

    typer.echo(_a(app_name, uptime_tage, letztes_log)["testament"])
