"""Welle 3: Zeit, Forensik, Gedaechtnis (Features 21-30).

Read-only Rekonstruktion aus Audit + Metriken + Manifest-Historie.
Schreibt nur verdichtete Snapshots (Retention: 90 Tage, danach Tages-Aggregate).
"""

import hashlib
from datetime import datetime, timezone

WAVE = 3
FEATURES = [
    "zeitmaschinen-slider",
    "drei-uhr-nachts",
    "deploy-genealogie",
    "karteileichen",
    "flaschenpost",
    "time-capsule",
    "geraeusch-archiv",
    "prophezeiungs-protokoll",
    "ahnenpass-secrets",
    "echolot",
]


def zeitmaschine(snapshots: list, zeitpunkt: str) -> dict:
    """Feature 21: Flottenzustand zu Zeitpunkt t rekonstruieren (read-only)."""
    past = [s for s in snapshots if s.get("ts", "") <= zeitpunkt]
    jetzt = snapshots[-1] if snapshots else {}
    return {"zeitpunkt": zeitpunkt, "zustand": past[-1] if past else None,
            "diff_zu_jetzt": {"felder": [k for k in jetzt if past and past[-1].get(k) != jetzt.get(k)] if past else []},
            "read_only": True}


def tatort_akte(alerts: list, deploys: list, crons: list, log_spitzen: list) -> dict:
    """Feature 22: 'Was war um 3 Uhr nachts?' -> einseitige Tatort-Akte."""
    ereignisse = (
        [{"typ": "alert", **a} for a in alerts]
        + [{"typ": "deploy", **d} for d in deploys]
        + [{"typ": "cron", **c} for c in crons]
        + [{"typ": "log-spitze", **s} for s in log_spitzen]
    )
    ereignisse.sort(key=lambda e: e.get("ts", ""))
    return {"titel": "Tatort-Akte", "ereignisse": ereignisse, "anzahl": len(ereignisse)}


def genealogie(image: str, eltern: list, base_images: list) -> dict:
    """Feature 23: Stammbaum eines laufenden Images."""
    return {"image": image, "eltern": eltern, "grosseltern": base_images}


def karteileichen(apps: list, tage_schwelle: int = 90) -> dict:
    """Feature 24: Container ohne Traffic/Owner/Deploy seit X Tagen. Loescht nie selbst."""
    leichen = [a.get("name") for a in apps
               if a.get("tage_ohne_traffic", 0) >= tage_schwelle and not a.get("owner")]
    return {"karteileichen": leichen, "vorschlag": "archivieren?", "auto_delete": False}


def flaschenpost_legen(nachricht: str, trigger: str = "crash") -> dict:
    """Feature 25: Nachricht an den naechsten On-Call bei trigger."""
    return {"nachricht": nachricht[:500], "trigger": trigger,
            "id": hashlib.sha256(nachricht.encode()).hexdigest()[:8]}


def prophezeiung(metrik: str, rest_tage: float) -> dict:
    """Feature 28: Vorhersage + spaetere Selbstbenotung."""
    return {"ereignis": metrik, "prognose_tage": round(rest_tage, 1),
            "trefferquote_bisher": None, "selbstbenotung": "ausstehend"}


def ahnenpass(secret_name: str, fingerprint: str, alter_tage: int, rotationen: int, letzte_rolle: str) -> dict:
    """Feature 29: nur Metadaten, niemals Werte."""
    return {"secret": secret_name, "fingerprint": fingerprint[:16],
            "alter_tage": alter_tage, "rotationen": rotationen,
            "zuletzt_rotiert_von_rolle": letzte_rolle, "wert_niemals_enthalten": True}


def echolot(route: list) -> dict:
    """Feature 30: synthetische Pings durch die echte Kette als Sonarbild."""
    hops = [{"station": r, "tiefe": i + 1} for i, r in enumerate(route)]
    return {"sonar": hops, "hops": len(hops)}


def register_fun_wave3(app) -> None:
    """Attach read-only routes to an aiohttp app (optional wiring)."""
    from aiohttp import web

    async def _ahnenpass(request: web.Request) -> web.Response:
        q = request.rel_url.query
        return web.json_response(ahnenpass(
            request.match_info["name"], q.get("fp", ""), int(q.get("alter", 0) or 0),
            int(q.get("rot", 0) or 0), q.get("rolle", "unbekannt")))

    app.router.add_get("/api/fun/ahnenpass/{name}", _ahnenpass)
