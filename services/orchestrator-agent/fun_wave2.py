"""Welle 2: Visualisierung, die es so nicht gibt (Features 11-20).

Pure descriptor builders: frontend renders, backend only computes data.
Optional aiohttp wiring at the bottom.
"""

import hashlib
import math

WAVE = 2
FEATURES = [
    "sternenkarte",
    "waermebild",
    "aquarium",
    "metroplan",
    "latenz-wetterkarte",
    "pacman-health",
    "schallplatte",
    "lego-bauplan",
    "morse-status",
    "fleet-wrapped",
]


def sternbild(services: list, deps: list) -> dict:
    """Feature 11: services as constellations."""
    stars = [{"id": s, "x": (int(hashlib.sha256(s.encode()).hexdigest()[:4], 16) % 1000) / 10,
              "y": (int(hashlib.sha256(s.encode()).hexdigest()[4:8], 16) % 1000) / 10}
             for s in services]
    return {"stars": stars, "lines": deps}


def waermebild(cpu_by_service: dict) -> dict:
    """Feature 12: thermal color ramp per service."""
    def color(cpu: float) -> str:
        stops = [(0, "blau"), (50, "gruen"), (75, "gelb"), (90, "rot")]
        return next((c for t, c in reversed(stops) if cpu >= t), "blau")
    return {s: color(c) for s, c in cpu_by_service.items()}


def aquarium(services: list) -> dict:
    """Feature 13: containers as fish."""
    fish = []
    for s in services:
        state = "bauch-oben" if s.get("status") == "dead" else (
            "schnell" if s.get("cpu", 0) > 80 else "schwimmt")
        fish.append({"name": s.get("name"), "fisch": state})
    return {"fische": fish}


def metroplan(branches: dict, deploys: list) -> dict:
    """Feature 14: branches as subway lines, deploys as stations."""
    return {"linien": [{"name": b, "stationen": [d for d in deploys if d.get("branch") == b]}
                       for b in branches]}


def latenz_wetter(p95_by_service: dict) -> dict:
    """Feature 15: p95 as high/low pressure zones."""
    vals = list(p95_by_service.values()) or [0]
    avg = sum(vals) / len(vals)
    return {"gebiete": [
        {"service": s, "druck": "tief" if v > avg * 1.5 else "hoch" if v < avg * 0.5 else "normal", "p95": v}
        for s, v in p95_by_service.items()]}


def schallplatte(metrics_30d: list) -> dict:
    """Feature 17: 30-day metrics as vinyl grooves (time scrub descriptor)."""
    return {"rillen": len(metrics_30d), "sync": True, "tage": 30}


MORSE = {"ok": "--- -.-", "warn": ".-- .- .-. -.", "down": "-.. --- .-- -."}


def morse_status(health: str) -> dict:
    """Feature 19: fleet health as morse code."""
    return {"klartext": health, "morse": MORSE.get(health, "... --- ...")}


def fleet_wrapped(stats: dict) -> dict:
    """Feature 20: year-in-review descriptor."""
    top = max(stats.get("deploys_by_day", {"montag": 0}), key=lambda k: stats["deploys_by_day"][k]) \
        if stats.get("deploys_by_day") else None
    return {"schlimmster_tag": top, "deploys_gesamt": stats.get("deploys_total", 0),
            "treuester_container": stats.get("longest_uptime_app")}


def register_fun_wave2(app) -> None:
    """Attach read-only routes to an aiohttp app (optional wiring)."""
    from aiohttp import web

    async def _morse(request: web.Request) -> web.Response:
        return web.json_response(morse_status(request.rel_url.query.get("health", "ok")))

    app.router.add_get("/api/fun/morse", _morse)
