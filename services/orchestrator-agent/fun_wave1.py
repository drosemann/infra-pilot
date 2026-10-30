"""Welle 1: Sofort-Spass mit echtem Nutzen (Features 1-10).

Self-contained, read-only helpers + optional aiohttp route registration.
Nothing here writes state or blocks deploys. Wire-up (one line, later)::

    from fun_wave1 import register_fun_wave1
    register_fun_wave1(app)
"""

import hashlib
from datetime import datetime, timezone

WAVE = 1
FEATURES = [
    "deploy-wetterbericht",
    "container-horoskope",
    "seismograph",
    "flotten-radio",
    "blame-poetic",
    "emoji-wappen",
    "uptime-geburtstage",
    "muellcontainer-des-tages",
    "schlafenszeit-modus",
    "deploy-daumenkino",
]


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)


def deploy_wetter(friday: bool, error_rate: float, open_incidents: int) -> dict:
    """Feature 1: deploy weather report. Informational only, never blocks."""
    score = error_rate * 100 + open_incidents * 15 + (25 if friday else 0)
    level = "sturm" if score >= 50 else "wechselhaft" if score >= 20 else "sonnig"
    return {"level": level, "score": round(score, 1), "blocks_deploy": False}


HOROSKOPES = [
    "Merkur ruecklaeufig: deine Restarts sagen mehr.",
    "Heute stehen die Container guenstig. Deploy mutig, aber mit Backup.",
    "Ein OOM im Verborgenen: schau auf den Speicher.",
    "Der Cache laechelt dir zu. Nutze den Tag.",
    "Vorsicht vor Freitag-Deploys. Die Sterne warnen.",
    "Deine Latenz sinkt, deine Laune steigt.",
]


def horoskop(app_name: str, day: str = "") -> dict:
    """Feature 2: deterministic daily one-liner per app."""
    day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    idx = _seed(f"{app_name}:{day}") % len(HOROSKOPES)
    return {"app": app_name, "day": day, "text": HOROSKOPES[idx]}


def quake_magnitude(restarts: int, ooms: int, crashloops: int) -> dict:
    """Feature 3: fleet seismograph magnitude per app."""
    mag = min(9.9, restarts * 0.3 + ooms * 0.8 + crashloops * 1.5)
    return {"magnitude": round(mag, 1), "level": "rot" if mag >= 5 else "gelb" if mag >= 2 else "gruen"}


def radio_tone(cpu: float, error_rate: float) -> dict:
    """Feature 4: sonification descriptor (frontend renders WebAudio)."""
    freq = 110 + min(cpu, 100) * 4
    return {"freq_hz": round(freq, 1), "alert": error_rate > 0.05, "muted_by_default": True}


HAIKU_TEMPLATE = ("Alter Build faellt,\n{cause} fluesterte leise -\nRollback bringt den Tag.")


def blame_poetic(cause: str) -> dict:
    """Feature 5: haiku + factual root cause."""
    return {"haiku": HAIKU_TEMPLATE.format(cause=cause[:40]), "cause": cause}


def wappen(app_name: str, commits: int) -> dict:
    """Feature 6: deterministic crest (colors/shapes) from commit history."""
    h = hashlib.sha256(app_name.encode()).hexdigest()
    shapes = ["schild", "kreis", "raute", "welle"]
    return {"farbe": f"#{h[:6]}", "form": shapes[_seed(app_name) % 4], "sterne": min(commits // 100, 5)}


def geburtstag(uptime_days: int) -> dict:
    """Feature 7: uptime anniversary?"""
    milestones = [30, 100, 365, 1000]
    hit = [m for m in milestones if uptime_days >= m]
    return {"feiert": bool(hit and uptime_days in hit), "meilenstein": max(hit) if hit else None}


def muellcontainer(apps: list) -> dict:
    """Feature 8: biggest idle resource, suggestion only."""
    if not apps:
        return {"koenig": None, "vorschlag": None}
    idle = max(apps, key=lambda a: a.get("idle_cpu", 0))
    return {"koenig": idle.get("name"), "vorschlag": f"{idle.get('name')} verkleinern?"}


def schlafenszeit(now_hour: int, prod: bool) -> dict:
    """Feature 9: sleep schedule; prod never sleeps."""
    if prod:
        return {"schlafen": False, "grund": "prod schlaeft nie"}
    return {"schlafen": now_hour < 6 or now_hour >= 22, "snooze_max": 3}


def daumenkino(snapshots: list) -> dict:
    """Feature 10: deploy flipbook descriptor."""
    return {"frames": len(snapshots), "dauer_sek": min(10, len(snapshots)), "export": "gif"}


def register_fun_wave1(app) -> None:
    """Attach read-only routes to an aiohttp app (optional wiring)."""
    from aiohttp import web

    async def _wetter(request: web.Request) -> web.Response:
        q = request.rel_url.query
        return web.json_response(deploy_wetter(
            friday=q.get("friday") == "1",
            error_rate=float(q.get("error_rate", 0) or 0),
            open_incidents=int(q.get("incidents", 0) or 0),
        ))

    async def _horoskop(request: web.Request) -> web.Response:
        return web.json_response(horoskop(request.match_info["app"]))

    app.router.add_get("/api/fun/wetter", _wetter)
    app.router.add_get("/api/fun/horoskop/{app}", _horoskop)
