"""Incident & On-Call fuer den Orchestrator (Ideen #69, #17, #75, #81).

Sachliche Umsetzung des Ideen-Buendels "Incident & Bereitschaft":

- #69 (skyrim-arrow): Incident-Workflow mit Service, Schweregrad, Runbook
  und Status-Updates bis zur bestaetigten Behebung.
- #17 (horoscope-routing): Zuweisung nach Dienst-Zustaendigkeit und
  Bereitschaftsplan statt Sternzeichen — die erste Eskalationsstufe
  liefert den Duty-Owner.
- #75 (klingon-escalation): Eskalationskette mit Fristen, Ruhezeiten,
  Bestaetigung und nachvollziehbarem Verlauf.
- #81 (sith-postmortem): sachlicher Incident-Bericht als ENTWURF aus
  Timeline, Alerts und Deployments; Verantwortliche pruefen und ergaenzen.

Speicherung: JSON-Datei mit atomarem Replace (Muster wie living_fleet).
Alle /api/-Routen sind bereits durch das Federation-Token-Middleware
in webhook_server.py geschuetzt.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SEVERITIES = ("critical", "high", "medium", "low")
STATUSES = ("open", "acknowledged", "resolved")

DEFAULT_ESCALATE_AFTER_S = 1800


def _store_path() -> str:
    return os.getenv(
        "INCIDENTS_STORE", os.path.join(os.path.dirname(__file__), "incidents.json")
    )


def _escalation_levels() -> List[List[str]]:
    """Parse INCIDENTS_ESCALATION="alice|bob;carol" in Stufen."""
    raw = os.getenv("INCIDENTS_ESCALATION", "")
    levels: List[List[str]] = []
    for part in raw.split(";"):
        members = [m.strip() for m in part.split("|") if m.strip()]
        if members:
            levels.append(members)
    return levels


def _escalate_after_s() -> int:
    try:
        return max(60, int(os.getenv("INCIDENTS_ESCALATE_AFTER_S", DEFAULT_ESCALATE_AFTER_S)))
    except ValueError:
        return DEFAULT_ESCALATE_AFTER_S


def _quiet_hours() -> Optional[tuple]:
    """Parse INCIDENTS_QUIET_HOURS="22:00-06:00". None = keine Ruhezeit."""
    raw = os.getenv("INCIDENTS_QUIET_HOURS", "").strip()
    if "-" not in raw:
        return None
    try:
        start_s, _, end_s = raw.partition("-")

        def _mins(v: str) -> int:
            h, _, m = v.strip().partition(":")
            return int(h) * 60 + int(m or 0)

        start, end = _mins(start_s), _mins(end_s)
        if not (0 <= start < 1440 and 0 <= end < 1440):
            return None
        return (start, end)
    except ValueError:
        return None


def _in_quiet_hours(now: Optional[float] = None) -> bool:
    window = _quiet_hours()
    if window is None:
        return False
    start, end = window
    ts = now if now is not None else time.time()
    local = datetime.fromtimestamp(ts)
    pos = local.hour * 60 + local.minute
    if start <= end:
        return start <= pos < end
    return pos >= start or pos < end


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_all() -> Dict[str, Any]:
    try:
        with open(_store_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_all(data: Dict[str, Any]) -> None:
    path = _store_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)


def _event(incident: Dict[str, Any], kind: str, actor: str, detail: str) -> None:
    incident.setdefault("timeline", []).append(
        {"at": _now_iso(), "kind": kind, "actor": actor, "detail": detail}
    )


def _duty_owner(level: int = 0) -> Optional[str]:
    """Duty-Owner aus Bereitschaftsplan (#17): erstes Mitglied der Stufe."""
    levels = _escalation_levels()
    if 0 <= level < len(levels):
        return levels[level][0]
    return None


def create_incident(
    service: str,
    severity: str,
    title: str,
    runbook: str = "",
    reporter: str = "",
) -> Dict[str, Any]:
    """Neuen Incident anlegen; wirft ValueError bei ungueltigen Eingaben."""
    service, title = service.strip(), title.strip()
    severity = severity.strip().lower()
    if not service:
        raise ValueError("service is required")
    if not title:
        raise ValueError("title is required")
    if severity not in SEVERITIES:
        raise ValueError(f"severity must be one of {SEVERITIES}")
    incident_id = f"inc-{uuid.uuid4().hex[:12]}"
    owner = _duty_owner(0)
    incident = {
        "id": incident_id,
        "service": service,
        "severity": severity,
        "title": title[:256],
        "runbook": runbook[:1024],
        "reporter": reporter[:128],
        "status": "open",
        "owner": owner,
        "escalation_level": 0,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "acknowledged_at": None,
        "resolved_at": None,
        "timeline": [],
    }
    _event(incident, "created", reporter or "system",
           f"{severity}/{service}: {title}")
    if owner:
        _event(incident, "assigned", "system",
               f"duty owner {owner} (escalation level 0)")
    data = _load_all()
    data[incident_id] = incident
    _save_all(data)
    logger.info("incident %s created for %s by %s", incident_id, service, reporter)
    return incident


def get_incident(incident_id: str) -> Optional[Dict[str, Any]]:
    return _load_all().get(incident_id)


def list_incidents(
    status: str = "", service: str = ""
) -> List[Dict[str, Any]]:
    """Alle Incidents, optional gefiltert; neueste zuerst."""
    status, service = status.strip(), service.strip()
    incidents = list(_load_all().values())
    if status:
        incidents = [i for i in incidents if i.get("status") == status]
    if service:
        incidents = [i for i in incidents if i.get("service") == service]
    incidents.sort(key=lambda i: i.get("created_at", ""), reverse=True)
    return incidents


def _store(incident: Dict[str, Any]) -> Dict[str, Any]:
    data = _load_all()
    data[incident["id"]] = incident
    _save_all(data)
    return incident


def set_status(
    incident_id: str, status: str, actor: str = "", note: str = ""
) -> Optional[Dict[str, Any]]:
    """Statuswechsel; 'resolved' verlangt eine Abschlussnotiz."""
    status = status.strip().lower()
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    incident = get_incident(incident_id)
    if incident is None:
        return None
    if status == "resolved" and not note.strip():
        raise ValueError("resolving requires a resolution note")
    incident["status"] = status
    incident["updated_at"] = _now_iso()
    if status == "acknowledged" and not incident.get("acknowledged_at"):
        incident["acknowledged_at"] = _now_iso()
    if status == "resolved":
        incident["resolved_at"] = _now_iso()
    _event(incident, "status", actor or "system",
           f"-> {status}" + (f": {note.strip()[:512]}" if note.strip() else ""))
    if note.strip() and status != "resolved":
        _event(incident, "note", actor or "system", note.strip()[:1024])
    return _store(incident)


def add_note(incident_id: str, actor: str, note: str) -> Optional[Dict[str, Any]]:
    """Status-Update an die Timeline haengen (#69)."""
    if not note.strip():
        raise ValueError("note must not be empty")
    incident = get_incident(incident_id)
    if incident is None:
        return None
    if incident.get("status") == "resolved":
        raise ValueError("incident is resolved; reopen it before adding notes")
    _event(incident, "note", actor or "system", note.strip()[:1024])
    incident["updated_at"] = _now_iso()
    return _store(incident)


def assign(
    incident_id: str, owner: str, actor: str = ""
) -> Optional[Dict[str, Any]]:
    """Manuelle Zuweisung; wird in der Timeline auditiert."""
    if not owner.strip():
        raise ValueError("owner must not be empty")
    incident = get_incident(incident_id)
    if incident is None:
        return None
    incident["owner"] = owner.strip()[:128]
    incident["updated_at"] = _now_iso()
    _event(incident, "assigned", actor or "system",
           f"manual assign -> {incident['owner']}")
    return _store(incident)


def escalate(
    incident_id: str, actor: str = "", force: bool = False
) -> Optional[Dict[str, Any]]:
    """Naechste Eskalationsstufe (#75).

    Gibt (incident, escalated, reason) zurueck: waehrend der Ruhezeiten
    wird ohne force nur als 'deferred' protokolliert, nicht eskaliert.
    Ohne konfigurierte Stufen oder auf hoechster Stufe passiert nichts.
    """
    incident = get_incident(incident_id)
    if incident is None:
        return None
    levels = _escalation_levels()
    current = int(incident.get("escalation_level", 0))
    if incident.get("status") == "resolved":
        raise ValueError("incident is resolved; nothing to escalate")
    if current + 1 >= len(levels):
        _event(incident, "escalation", actor or "system",
               "already at highest escalation level; no-op")
        _store(incident)
        return {"incident": incident, "escalated": False,
                "reason": "already at highest level"}
    if _in_quiet_hours() and not force:
        _event(incident, "escalation", actor or "system",
               f"deferred during quiet hours ({os.getenv('INCIDENTS_QUIET_HOURS')})")
        _store(incident)
        return {"incident": incident, "escalated": False,
                "reason": "deferred: quiet hours"}
    incident["escalation_level"] = current + 1
    incident["owner"] = levels[current + 1][0]
    incident["updated_at"] = _now_iso()
    _event(incident, "escalation", actor or "system",
           f"level {current} -> {current + 1}, owner {incident['owner']}"
           + (" (forced during quiet hours)" if force else ""))
    _store(incident)
    logger.warning("incident %s escalated to level %d (%s)",
                   incident_id, current + 1, incident["owner"])
    return {"incident": incident, "escalated": True,
            "reason": f"escalated to level {current + 1}"}


def escalation_due(incident: Dict[str, Any], now: Optional[float] = None) -> bool:
    """True, wenn die Eskalationsfrist abgelaufen ist (#75: Fristen)."""
    if incident.get("status") == "resolved":
        return False
    try:
        updated = datetime.fromisoformat(incident.get("updated_at", ""))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        age = (now if now is not None else time.time()) - updated.timestamp()
    except (ValueError, TypeError):
        return False
    return age >= _escalate_after_s()


def postmortem_draft(incident_id: str) -> Optional[Dict[str, Any]]:
    """Sachlichen Incident-Bericht als ENTWURF erzeugen (#81).

    Der Entwurf fasst nur gespeicherte Timeline-Fakten zusammen und ist
    nie final — Verantwortliche muessen pruefen und ergaenzen.
    """
    incident = get_incident(incident_id)
    if incident is None:
        return None
    lines = [
        f"# Postmortem-ENTWURF: {incident['id']} (unreviewed)",
        "",
        f"Service: {incident['service']} | Schweregrad: {incident['severity']} "
        f"| Status: {incident['status']}",
        f"Titel: {incident['title']}",
        f"Owner: {incident.get('owner') or '-'} | "
        f"Eskalationsstufe: {incident.get('escalation_level', 0)}",
        f"Erstellt: {incident['created_at']} | Aktualisiert: {incident['updated_at']}",
    ]
    if incident.get("acknowledged_at"):
        lines.append(f"Bestaetigt: {incident['acknowledged_at']}")
    if incident.get("resolved_at"):
        lines.append(f"Behoben: {incident['resolved_at']}")
    if incident.get("runbook"):
        lines.append(f"Runbook: {incident['runbook']}")
    lines += ["", "## Timeline (Fakten, keine Schuldzuweisungen)", ""]
    for ev in incident.get("timeline", []):
        lines.append(f"- {ev['at']} [{ev['kind']}] {ev['actor']}: {ev['detail']}")
    lines += [
        "",
        "## TODO fuer Verantwortliche",
        "",
        "- [ ] Ursache ergaenzen und verifizieren",
        "- [ ] Follow-up-Massnahmen mit Owner und Datum festlegen",
        "- [ ] Entwurf reviewen und freigeben",
    ]
    return {"incident_id": incident_id, "draft": True,
            "markdown": "\n".join(lines)}


def public_view(incident: Dict[str, Any]) -> Dict[str, Any]:
    """Kompakte Listenansicht plus Faelligkeits-Hinweis."""
    return {
        "id": incident["id"],
        "service": incident["service"],
        "severity": incident["severity"],
        "title": incident["title"],
        "status": incident["status"],
        "owner": incident.get("owner"),
        "escalation_level": incident.get("escalation_level", 0),
        "escalation_due": escalation_due(incident),
        "created_at": incident["created_at"],
        "updated_at": incident["updated_at"],
    }


# --- aiohttp handlers (registriert in webhook_server.py) ---


def _json_body_error(body: Any) -> Optional[str]:
    if not isinstance(body, dict):
        return "invalid JSON body"
    return None


async def incident_create(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    if _json_body_error(body):
        return web.json_response({"error": "invalid JSON body"}, status=400)
    try:
        incident = create_incident(
            service=str(body.get("service", "")),
            severity=str(body.get("severity", "medium")),
            title=str(body.get("title", "")),
            runbook=str(body.get("runbook", "")),
            reporter=str(body.get("reporter", "")),
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(incident, status=201)


async def incident_list(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    items = list_incidents(
        status=request.query.get("status", ""),
        service=request.query.get("service", ""),
    )
    return web.json_response({"incidents": [public_view(i) for i in items]})


async def incident_detail(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    incident = get_incident(request.match_info["incident_id"])
    if incident is None:
        return web.json_response({"error": "unknown incident"}, status=404)
    return web.json_response(incident)


async def incident_status(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    if _json_body_error(body):
        return web.json_response({"error": "invalid JSON body"}, status=400)
    try:
        incident = set_status(
            request.match_info["incident_id"],
            str(body.get("status", "")),
            actor=str(body.get("actor", "")),
            note=str(body.get("note", "")),
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    if incident is None:
        return web.json_response({"error": "unknown incident"}, status=404)
    return web.json_response(incident)


async def incident_note(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    if _json_body_error(body):
        return web.json_response({"error": "invalid JSON body"}, status=400)
    try:
        incident = add_note(
            request.match_info["incident_id"],
            str(body.get("actor", "")),
            str(body.get("note", "")),
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    if incident is None:
        return web.json_response({"error": "unknown incident"}, status=404)
    return web.json_response(incident)


async def incident_assign(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    if _json_body_error(body):
        return web.json_response({"error": "invalid JSON body"}, status=400)
    try:
        incident = assign(
            request.match_info["incident_id"],
            str(body.get("owner", "")),
            actor=str(body.get("actor", "")),
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    if incident is None:
        return web.json_response({"error": "unknown incident"}, status=404)
    return web.json_response(incident)


async def incident_escalate(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    try:
        result = escalate(
            request.match_info["incident_id"],
            actor=str(body.get("actor", "")),
            force=bool(body.get("force", False)),
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    if result is None:
        return web.json_response({"error": "unknown incident"}, status=404)
    return web.json_response(result)


async def incident_postmortem(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    draft = postmortem_draft(request.match_info["incident_id"])
    if draft is None:
        return web.json_response({"error": "unknown incident"}, status=404)
    return web.json_response(draft)
