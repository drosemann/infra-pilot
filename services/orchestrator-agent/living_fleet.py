"""Living Fleet barecode: creatures derived from real workload signals.

Phase 1 skeleton. Pure mood engine + JSON file store + aiohttp handlers.
Rules (frozen by docs/LIVING-FLEET-PLAN.md):
- Unknown signals stay None and never fabricate a score.
- Mood is a closed enum derived from vitals, never random.
- Creatures persist across rebuilds (keyed by workload id, not container id).
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ENABLED = os.getenv("LIVING_FLEET_ENABLED", "false").lower() == "true"
STORE_PATH = os.getenv(
    "LIVING_FLEET_STORE", os.path.join(os.path.dirname(__file__), "living_fleet.json")
)

# Closed mood enum — extend only via the plan file.
MOODS = (
    "thriving",
    "content",
    "sleepy",
    "hungry",
    "sick",
    "stressed",
    "sad",
    "ghost",
)

STAGES = ("egg", "hatchling", "juvenile", "adult", "elder")

# Thresholds (plan §4.2). Tunable via env in later phases.
THRIVING_MIN = 80
SICK_MAX = 35
STRESS_CPU = 85.0
STRESS_MEM = 90.0
HUNGER_DAYS = 30
GHOST_MINUTES = 360


def _clamp(v: float) -> int:
    return max(0, min(100, int(round(v))))


def vital_health(signals: Dict[str, Any]) -> Optional[int]:
    """0-100 from restarts/healthcheck, or None when no signal exists."""
    restarts = signals.get("restart_count_24h")
    healthy = signals.get("healthcheck_ok")
    if restarts is None and healthy is None:
        return None
    score = 100.0
    if isinstance(restarts, (int, float)) and restarts > 0:
        score -= min(70.0, 20.0 * restarts)
    if healthy is False:
        score -= 50.0
    return _clamp(score)


def vital_energy(signals: Dict[str, Any]) -> Optional[int]:
    cpu = signals.get("cpu_percent")
    mem = signals.get("mem_percent")
    if cpu is None and mem is None:
        return None
    pressure = max(
        float(cpu or 0.0) / 100.0,
        float(mem or 0.0) / 100.0,
    )
    return _clamp(100.0 - pressure * 100.0)


def vital_hunger(signals: Dict[str, Any]) -> Optional[int]:
    days = signals.get("days_since_deploy")
    if days is None:
        return None
    if days <= 1:
        return 100
    return _clamp(100.0 - (float(days) / HUNGER_DAYS) * 100.0)


def vital_hygiene(signals: Dict[str, Any]) -> Optional[int]:
    ok = signals.get("last_backup_ok")
    age_days = signals.get("days_since_backup")
    if ok is None and age_days is None:
        return None
    score = 100.0
    if ok is False:
        score -= 60.0
    if isinstance(age_days, (int, float)) and age_days > 1:
        score -= min(50.0, float(age_days) * 2.0)
    return _clamp(score)


def vital_morale(signals: Dict[str, Any]) -> Optional[int]:
    uptime = signals.get("uptime_30d_percent")
    streak = signals.get("deploy_streak")
    if uptime is None and streak is None:
        return None
    score = float(uptime) if uptime is not None else 80.0
    if isinstance(streak, (int, float)) and streak > 0:
        score = min(100.0, score + min(10.0, streak))
    return _clamp(score)


VITAL_FNS = {
    "health": vital_health,
    "energy": vital_energy,
    "hunger": vital_hunger,
    "hygiene": vital_hygiene,
    "morale": vital_morale,
}


def compute_vitals(signals: Dict[str, Any]) -> Dict[str, Optional[int]]:
    return {name: fn(signals) for name, fn in VITAL_FNS.items()}


def compute_mood(
    vitals: Dict[str, Optional[int]],
    signals: Dict[str, Any],
    down_minutes: float = 0.0,
) -> str:
    """Deterministic mood derivation. Order matters: ghost first, thriving last."""
    if down_minutes >= GHOST_MINUTES:
        return "ghost"
    if signals.get("running") is False:
        # Confirmed stopped: never thriving/sad/content on vitals alone.
        return "sick"
    if (vitals.get("health") is not None and vitals["health"] <= SICK_MAX) or signals.get(
        "healthcheck_ok"
    ) is False:
        return "sick"
    cpu = signals.get("cpu_percent") or 0.0
    mem = signals.get("mem_percent") or 0.0
    if cpu >= STRESS_CPU or mem >= STRESS_MEM:
        return "stressed"
    if vitals.get("hunger") is not None and vitals["hunger"] <= SICK_MAX:
        return "hungry"
    if signals.get("idle_24h") is True:
        return "sleepy"
    known = [v for v in vitals.values() if v is not None]
    if known and min(known) >= THRIVING_MIN and not signals.get("recent_incident"):
        return "thriving"
    if any(v is not None and v <= 50 for v in vitals.values()):
        return "sad"
    return "content"


def stage_for_age_days(age_days: float) -> str:
    if age_days < 1:
        return "egg"
    if age_days < 7:
        return "hatchling"
    if age_days < 30:
        return "juvenile"
    if age_days < 180:
        return "adult"
    return "elder"


def explain(vitals: Dict[str, Optional[int]], signals: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Per-vital raw-signal trace so the UI can answer 'why does it feel like this?'."""
    watched = {
        "health": ("restart_count_24h", "healthcheck_ok"),
        "energy": ("cpu_percent", "mem_percent"),
        "hunger": ("days_since_deploy",),
        "hygiene": ("last_backup_ok", "days_since_backup"),
        "morale": ("uptime_30d_percent", "deploy_streak"),
    }
    out = []
    for name, keys in watched.items():
        out.append(
            {
                "vital": name,
                "score": vitals.get(name),
                "signals": {k: signals.get(k) for k in keys if k in signals},
            }
        )
    return out


# --- persistence (JSON file; SQLite migration is a later phase) ---


def _load_all() -> Dict[str, Any]:
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_all(data: Dict[str, Any]) -> None:
    tmp = STORE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    os.replace(tmp, STORE_PATH)


def get_or_birth(workload_id: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    data = _load_all()
    creature = data.get(workload_id)
    if creature is None:
        now = time.time()
        creature = {
            "workload_id": workload_id,
            "display_name": display_name or workload_id,
            "born_at": now,
            "retired": False,
            "down_since": None,
            "vitals": {k: None for k in VITAL_FNS},
            "mood": "content",
            "stage": "egg",
        }
        data[workload_id] = creature
        _save_all(data)
    return creature


def refresh(workload_id: str, signals: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute vitals/mood/stage from fresh signals. Returns public view."""
    data = _load_all()
    creature = data.get(workload_id)
    if creature is None:
        # Birth only on a healthy first sighting; a stopped workload with no
        # creature gets a transient view, never a persisted birth.
        if signals.get("running") is not True or signals.get("healthcheck_ok") is False:
            vitals = compute_vitals(signals)
            return public_view(
                {
                    "workload_id": workload_id,
                    "display_name": workload_id,
                    "mood": compute_mood(vitals, signals),
                    "stage": "egg",
                    "vitals": vitals,
                    "retired": False,
                },
                signals,
            )
        birth_name = signals.get("display_name")
        creature = get_or_birth(
            workload_id, birth_name if isinstance(birth_name, str) else None
        )
        data[workload_id] = creature
    vitals = compute_vitals(signals)
    down_since = creature.get("down_since")
    if signals.get("running") is False and not down_since:
        creature["down_since"] = time.time()
        down_since = creature["down_since"]
    elif signals.get("running") is True:
        creature["down_since"] = None
        down_since = None
    down_minutes = (time.time() - down_since) / 60.0 if down_since else 0.0
    # Window the cumulative Docker restart counter into a real 24h delta
    # from persisted samples instead of fabricating history.
    total = signals.get("restart_count_total")
    if isinstance(total, (int, float)):
        now = time.time()
        samples = [
            (ts, c)
            for ts, c in (creature.get("restart_samples") or [])
            if now - ts <= 86400.0
        ] + [(now, float(total))]
        creature["restart_samples"] = samples[-48:]
        signals = dict(
            signals, restart_count_24h=max(0.0, float(total) - samples[0][1])
        )
        vitals = compute_vitals(signals)
    creature["vitals"] = vitals
    creature["last_signals"] = signals
    creature["mood"] = compute_mood(vitals, signals, down_minutes)
    age_days = (time.time() - creature["born_at"]) / 86400.0
    creature["stage"] = stage_for_age_days(age_days)
    _save_all(data)
    return public_view(creature, signals)


def public_view(
    creature: Dict[str, Any], signals: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    signals = signals or {}
    return {
        "workload_id": creature["workload_id"],
        "display_name": creature["display_name"],
        "mood": creature["mood"],
        "stage": creature["stage"],
        "vitals": creature["vitals"],
        "explanation": explain(creature["vitals"], signals),
        "retired": creature.get("retired", False),
    }


def rename(workload_id: str, display_name: str) -> Optional[Dict[str, Any]]:
    data = _load_all()
    creature = data.get(workload_id)
    if creature is None or creature.get("retired"):
        return None
    creature["display_name"] = display_name[:64]
    _save_all(data)
    return public_view(creature)


# --- aiohttp handlers (registered in webhook_server.py) ---


async def fleet_list(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    if not ENABLED:
        return web.json_response({"error": "living fleet disabled"}, status=404)
    data = _load_all()
    return web.json_response(
        [
            public_view(c, c.get("last_signals") or {})
            for c in data.values()
            if not c.get("retired")
        ]
    )


async def fleet_detail(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    if not ENABLED:
        return web.json_response({"error": "living fleet disabled"}, status=404)
    workload_id = request.match_info["workload_id"]
    data = _load_all()
    creature = data.get(workload_id)
    if creature is None:
        return web.json_response({"error": "unknown workload"}, status=404)
    return web.json_response(public_view(creature, creature.get("last_signals") or {}))


async def fleet_rename(request) -> Any:  # type: ignore[no-untyped-def]
    from aiohttp import web

    if not ENABLED:
        return web.json_response({"error": "living fleet disabled"}, status=404)
    workload_id = request.match_info["workload_id"]
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid JSON body"}, status=400)
    raw_name = body.get("display_name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        return web.json_response({"error": "display_name required"}, status=400)
    name = raw_name.strip()
    view = rename(workload_id, name)
    if view is None:
        return web.json_response({"error": "unknown or retired workload"}, status=404)
    logger.info("fleet rename: %s", workload_id)
    return web.json_response(view)
