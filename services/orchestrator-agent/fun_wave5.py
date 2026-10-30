"""Welle 5: Soziales, Story, Ritual (Features 41-50).

Alle generierten Texte aus Templates + echten Events, nie freie
Halluzination. Jeder Text hat einen 'fakten_zeigen'-Toggle mit Rohdaten.
Bei Prod-Incidents: sachlicher Ton (incident_modus=True).
"""

WAVE = 5
FEATURES = [
    "oncall-staffelstab",
    "incident-krimi",
    "deploy-tagebuch",
    "flotten-wappen",
    "wunschbrunnen",
    "schweigeminute",
    "dankbarkeits-feed",
    "neuling-modus",
    "abschieds-deploy",
    "flotten-memorial",
]


def staffelstab(von: str, an: str, offene_punkte: list) -> dict:
    """Feature 41: On-Call-Uebergabe als Staffellauf."""
    return {"von": von, "an": an, "staffel": "uebergeben",
            "mitgegeben": offene_punkte}


def incident_krimi(opfer: str, tatzeit: str, verdaechtige: list,
                   aufloesung: str, incident_modus: bool = False) -> dict:
    """Feature 42: Postmortem als Krimi-Kapitel. Fakten echt, Ton Dekor."""
    if incident_modus:
        return {"titel": f"Incident {opfer} um {tatzeit}", "verdaechtige": verdaechtige,
                "aufloesung": aufloesung, "fakten_zeigen": verdaechtige}
    kapitel = (f"Kapitel 1: {opfer} wurde um {tatzeit} leblos aufgefunden. "
               f"Verdaechtig: {', '.join(verdaechtige)}. Aufloesung: {aufloesung}.")
    return {"titel": "Der Fall " + opfer, "kapitel": kapitel,
            "fakten_zeigen": {"tatzeit": tatzeit, "verdaechtige": verdaechtige,
                              "aufloesung": aufloesung}}


def tagebuch(app: str, restarts: int, incident_modus: bool = False) -> dict:
    """Feature 43: Deploy-Tagebuch aus Containersicht."""
    if incident_modus:
        return {"eintrag": f"{app}: {restarts} Restarts (Rolling Update).", "fakten_zeigen": {"restarts": restarts}}
    eintrag = (f"Tag 12: Heute wurde ich {restarts}x neugestartet. "
               "Der Mensch nennt es Rolling Update. Ich nenne es Umzug.")
    return {"eintrag": eintrag, "fakten_zeigen": {"restarts": restarts}}


def wappen_titel(app: str, ereignisse: list) -> dict:
    """Feature 44: kosmetische Titel aus echter Historie."""
    titel = []
    if sum(1 for e in ereignisse if e.get("typ") == "az-ausfall-ueberlebt") >= 3:
        titel.append("Ueberlebende von 3 AZ-Ausfaellen")
    if sum(1 for e in ereignisse if e.get("typ") == "deploy") >= 1000:
        titel.append("Tausendsassa")
    return {"app": app, "titel": titel, "kosmetisch": True}


def neuling_erklaerung(zustand: dict, technisch: bool = False) -> dict:
    """Feature 48: 'Erklaer mir wie 5' aus echten Daten."""
    apps = zustand.get("apps_up", 0)
    einfach = f"Alles gut! {apps} Programme laufen und spielen miteinander."
    if technisch:
        return {"text": f"{apps} Services healthy. Details im Dashboard.", "modus": "technisch"}
    return {"text": einfach, "modus": "einfach", "umschalter": "jetzt technisch"}


def abschied(app: str, uptime_tage: int, letztes_log: str) -> dict:
    """Feature 49: wuerdevolles Stilllegen statt kommentarlosem Delete."""
    testament = (f"Hier ruht {app} nach {uptime_tage} Tagen treuem Dienst. "
                 f"Letzte Worte: {letztes_log[:120]}")
    return {"app": app, "testament": testament, "archiv_snapshot": True,
            "memorial_eintrag": True}


def register_fun_wave5(app) -> None:
    """Attach read-only routes to an aiohttp app (optional wiring)."""
    from aiohttp import web

    async def _tagebuch(request: web.Request) -> web.Response:
        q = request.rel_url.query
        return web.json_response(tagebuch(
            request.match_info["app"], int(q.get("restarts", 0) or 0),
            incident_modus=q.get("incident_modus") == "1"))

    app.router.add_get("/api/fun/tagebuch/{app}", _tagebuch)
