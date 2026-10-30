"""Welle-3 CLI: Forensik-Helfer (read-only, brauchen keine API)."""

import typer

app = typer.Typer(help="Welle 3: Zeitmaschine, Tatort-Akte, Echolot & Co.")


@app.command()
def tatort():
    """Demo-Tatort-Akte aus Beispiel-Events."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave3 import tatort_akte as _t

    akte = _t([{"ts": "03:12", "text": "OOM worker"}],
              [{"ts": "03:05", "text": "deploy api v42"}], [], [])
    typer.echo(f"Tatort-Akte: {akte['anzahl']} Ereignisse")
    for e in akte["ereignisse"]:
        typer.echo(f"  {e['ts']} [{e['typ']}] {e['text']}")


@app.command()
def echolot(stationen: str = "dns,lb,api,db-read"):
    """Echolot-Route als Sonarbild."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave3 import echolot as _e

    for hop in _e(stationen.split(","))["sonar"]:
        typer.echo(f"{'~' * hop['tiefe']} {hop['station']}")


@app.command()
def flaschenpost(nachricht: str, trigger: str = "crash"):
    """Flaschenpost fuer den naechsten On-Call hinterlegen."""
    import sys

    sys.path.insert(0, "services/orchestrator-agent")
    from fun_wave3 import flaschenpost_legen as _f

    r = _f(nachricht, trigger)
    typer.echo(f"Flaschenpost {r['id']} hinterlegt (trigger: {r['trigger']})")
