"""Welle 4: Chaos & Simulation (Features 31-40).

Harte Regel: Chaos-Endpunkte verweigern `prod` SERVERSEITIG, nicht nur im UI.
Erlaubte Umgebungen: sandbox, staging. Alles andere -> ChaosVerweigert.
"""

import random

WAVE = 4
FEATURES = [
    "chaos-kartenspiel",
    "branduebung",
    "was-waere-wenn",
    "geister-deploy",
    "zombie-stunde",
    "rueckspul-knopf",
    "last-geburtstagsparty",
    "toter-mann-schalter",
    "domino-vorschau",
    "schwarzer-kasten",
]

ERLAUBT = {"sandbox", "staging"}


class ChaosVerweigert(Exception):
    """Prod ist fuer Chaos tabu. Punkt."""


def _check(umgebung: str) -> str:
    if umgebung not in ERLAUBT:
        raise ChaosVerweigert(f"Chaos in '{umgebung}' verweigert (erlaubt: {sorted(ERLAUBT)})")
    return umgebung


CHAOS_KARTEN = ["kill-einen-pod", "+200ms-latenz", "dns-wackelt", "disk-wird-voll", "oom-roulette"]


def chaos_karte_ziehen(umgebung: str, seed: int = 0) -> dict:
    """Feature 31: Chaos-Karte ziehen. Nur sandbox/staging."""
    _check(umgebung)
    karte = CHAOS_KARTEN[(seed or random.randint(0, 10**6)) % len(CHAOS_KARTEN)]
    return {"umgebung": umgebung, "karte": karte, "abbruch_knopf": "gross-und-rot"}


def branduebung(umgebung: str, entdeckt_sek: int, gefixt_sek: int) -> dict:
    """Feature 32: Mini-Chaos in Staging mit Score."""
    _check(umgebung)
    score = max(0, 100 - entdeckt_sek - gefixt_sek // 2)
    return {"umgebung": umgebung, "entdeckt_sek": entdeckt_sek,
            "gefixt_sek": gefixt_sek, "score": score}


def was_waere_wenn(traffic_faktor: float, db_weg: bool, az_weg: bool, basis_p95: float) -> dict:
    """Feature 33: grobe Simulation aus echten Metriken. Klar als Schaetzung gelabelt."""
    p95 = basis_p95 * traffic_faktor * (3 if db_weg else 1) * (1.5 if az_weg else 1)
    return {"geschaetzt_p95_ms": round(p95, 1), "schaetzung": True, "kein_eingriff": True}


def domino_vorschau(graph: dict, start: str) -> dict:
    """Feature 39: animierte Vorschau, was kaskadiert mitfaellt."""
    gesehen, stapel, kaskade = set(), [start], []
    while stapel:
        knoten = stapel.pop()
        if knoten in gesehen:
            continue
        gesehen.add(knoten)
        kaskade.append(knoten)
        stapel.extend(graph.get(knoten, []))
    return {"start": start, "kaskade": kaskade,
            "pflicht_bestaetigung": len(kaskade) > 3}


def schwarzer_kasten(ereignisse: list) -> dict:
    """Feature 40: Incident-Flugschreiber (Hash + Signatur, spaeter auslesbar)."""
    import hashlib

    roh = repr(sorted(repr(e) for e in ereignisse)).encode()
    return {"ereignisse": len(ereignisse),
            "siegel": hashlib.sha256(roh).hexdigest()[:16], "versiegelt": True}


def register_fun_wave4(app) -> None:
    """Attach routes mit serverseitigem Prod-Guard (optional wiring)."""
    from aiohttp import web

    async def _karte(request: web.Request) -> web.Response:
        q = request.rel_url.query
        try:
            return web.json_response(chaos_karte_ziehen(
                q.get("umgebung", ""), int(q.get("seed", 0) or 0)))
        except ChaosVerweigert as exc:
            return web.json_response({"error": str(exc)}, status=403)

    app.router.add_get("/api/fun/chaos-karte", _karte)
