"""Deployment-Freeze-Gate (Idee #20 moon-phase-deployment-gate, sachlich).

Blockiert POST /api/v1/deployments und /webhook/gitops ausserhalb von
Wartungsfenstern, wenn ein Freeze aktiv ist. Dry-Runs bleiben immer erlaubt,
damit Diffs und Policy-Checks weiterlaufen. Ein Freeze kann explizit mit
``freeze_override=true`` + ``freeze_reason`` (nicht leer, Audit) umgangen werden.

Konfiguration ueber Umgebung:
  DEPLOY_FREEZE=1|true            manueller Freeze (sofort aktiv)
  DEPLOY_FREEZE_WINDOWS="sat:00:00-sun:23:59;fri:22:00-sat:06:00"
    wiederkehrende Fenster; Wochentage englisch (mon..sun), Zeit HH:MM,
    Ende darf ueber Mitternacht/Wochengrenze hinausgehen.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _parse_hhmm(value: str) -> int:
    hours, _, minutes = value.strip().partition(":")
    h, m = int(hours), int(minutes or 0)
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"invalid time: {value!r}")
    return h * 60 + m


def _parse_windows(raw: str):
    """Parse "sat:00:00-sun:23:59;fri:22:00-sat:06:00" into minute-based ranges."""
    windows = []
    for part in (raw or "").split(";"):
        part = part.strip().lower()
        if not part:
            continue
        try:
            start_s, _, end_s = part.partition("-")
            start_day_s, _, start_time_s = start_s.partition(":")
            end_day_s, _, end_time_s = end_s.partition(":")
            start_day, end_day = start_day_s.strip()[:3], end_day_s.strip()[:3]
            start = _WEEKDAYS.index(start_day) * 24 * 60 + _parse_hhmm(start_time_s)
            end = _WEEKDAYS.index(end_day) * 24 * 60 + _parse_hhmm(end_time_s)
            if end <= start:
                end += 7 * 24 * 60  # Fenster ueber die Wochengrenze hinaus
            windows.append((start, end, part))
        except (ValueError, IndexError):
            logger.warning("ignoring invalid DEPLOY_FREEZE_WINDOWS entry: %r", part)
    return windows


def freeze_active(now: Optional[datetime] = None) -> Tuple[bool, str]:
    """Return (frozen, reason). Never raises."""
    try:
        if (os.getenv("DEPLOY_FREEZE", "").strip().lower() in ("1", "true", "on")):
            return True, "manual freeze via DEPLOY_FREEZE"
        raw = os.getenv("DEPLOY_FREEZE_WINDOWS", "")
        if raw.strip():
            current = now or datetime.now()
            pos = current.weekday() * 24 * 60 + current.hour * 60 + current.minute
            for start, end, label in _parse_windows(raw):
                # Wochengrenze: Position auch eine Woche versetzt pruefen
                if any(start <= p < end for p in (pos, pos + 7 * 24 * 60)):
                    return True, f"freeze window active ({label})"
        return False, ""
    except Exception as exc:  # fail open, aber sichtbar
        logger.warning("deploy-freeze check failed, allowing deploy: %s", exc)
        return False, ""


def check_deploy_allowed(
    body: Dict[str, Any], dry_run: bool = False, now: Optional[datetime] = None
) -> Tuple[bool, str]:
    """Prueft, ob ein Deployment trotz Freeze laufen darf."""
    frozen, reason = freeze_active(now)
    if not frozen or dry_run:
        return True, reason
    if body.get("freeze_override") is True:
        ack = body.get("freeze_reason", "")
        if isinstance(ack, str) and ack.strip():
            logger.warning("deployment during freeze with override: %s", ack.strip())
            return True, f"freeze overridden: {ack.strip()}"
        return False, reason + " (freeze_override needs non-empty freeze_reason)"
    return False, reason


def status(now: Optional[datetime] = None) -> Dict[str, Any]:
    frozen, reason = freeze_active(now)
    return {
        "frozen": frozen,
        "reason": reason,
        "manual_freeze": os.getenv("DEPLOY_FREEZE", ""),
        "windows": os.getenv("DEPLOY_FREEZE_WINDOWS", ""),
    }
