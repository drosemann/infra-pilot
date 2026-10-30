"""Welle-4 CLI: Chaos nur in Sandbox/Staging (Prod wird verweigert)."""

import typer

app = typer.Typer(help="Welle 4: Chaos & Simulation (nie Prod).")


@app.command()
def karte(umgebung: str = "sandbox", seed: int = 0):
    """Chaos-Karte ziehen (prod wird verweigert)."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave4 import ChaosVerweigert, chaos_karte_ziehen as _k

    try:
        r = _k(umgebung, seed)
        typer.echo(f"[{r['umgebung']}] Karte: {r['karte']} (Abbruch: {r['abbruch_knopf']})")
    except ChaosVerweigert as exc:
        typer.echo(f"Verweigert: {exc}", err=True)
        raise typer.Exit(code=3)


@app.command()
def domino(start: str = "api", kanten: str = "api:worker,worker:db,api:cache"):
    """Domino-Vorschau: was faellt mit, wenn `start` faellt?"""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave4 import domino_vorschau as _d

    graph: dict = {}
    for k in kanten.split(","):
        a, b = k.split(":")
        graph.setdefault(a.strip(), []).append(b.strip())
    r = _d(graph, start)
    typer.echo(" -> ".join(r["kaskade"]))
    if r["pflicht_bestaetigung"]:
        typer.echo("Pflicht-Bestaetigung noetig (>3 Betroffene).")
