#!/usr/bin/env python3
"""Feature-flag hygiene report: list stale flags.

A flag is stale when it is still `active` and either its `expires_at` has
passed or neither the flag nor any of its rules was updated within
`--untouched-days` (default 90). Reads from the panel admin endpoint
`GET /api/feature-flags` (admin token required) so the report always
reflects the source of truth.

Exit status is 0 unless `--fail-on-stale` is given and stale flags exist.
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request
from typing import Any, Dict, List


def parse_ts(value: Any) -> datetime.datetime | None:
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def newest_touch(flag: Dict[str, Any]) -> datetime.datetime | None:
    touches = [parse_ts(flag.get("updated_at")), parse_ts(flag.get("created_at"))]
    for rule in (flag.get("rules") or {}).values():
        touches.append(parse_ts(rule.get("updated_at")))
    touches = [t for t in touches if t]
    return max(touches) if touches else None


def find_stale(
    flags: List[Dict[str, Any]],
    now: datetime.datetime,
    untouched_days: int = 90,
) -> List[Dict[str, Any]]:
    """Return active flags that expired or went untouched. Pure: unit-tested."""
    stale = []
    cutoff = now - datetime.timedelta(days=untouched_days)
    for flag in flags:
        if flag.get("status") != "active":
            continue
        expires_at = parse_ts(flag.get("expires_at"))
        touched = newest_touch(flag)
        reason = None
        if expires_at and expires_at <= now:
            reason = f"expired {expires_at.date().isoformat()}"
        elif touched and touched <= cutoff:
            reason = f"untouched since {touched.date().isoformat()}"
        elif touched is None:
            reason = "no update timestamp recorded"
        if reason:
            stale.append({"key": flag.get("key"), "reason": reason})
    return stale


def fetch_flags(api_url: str, token: str) -> List[Dict[str, Any]]:
    req = urllib.request.Request(
        f"{api_url.rstrip('/')}/api/feature-flags",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310 - operator-configured URL
        return json.loads(resp.read().decode()).get("flags", [])


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report stale feature flags.")
    parser.add_argument("--api-url", default=os.getenv("FEATURE_FLAGS_PANEL_URL", "http://localhost:3001"))
    parser.add_argument("--token", default=os.getenv("FLAG_ADMIN_TOKEN", ""))
    parser.add_argument("--untouched-days", type=int, default=90)
    parser.add_argument("--fail-on-stale", action="store_true")
    args = parser.parse_args(argv)
    if not args.token:
        print("error: admin token required (--token or FLAG_ADMIN_TOKEN)", file=sys.stderr)
        return 2
    try:
        flags = fetch_flags(args.api_url, args.token)
    except Exception as exc:
        print(f"error: cannot reach panel: {exc}", file=sys.stderr)
        return 2
    stale = find_stale(flags, datetime.datetime.now(datetime.timezone.utc), args.untouched_days)
    if not stale:
        print(f"OK: {len(flags)} active flag(s), none stale.")
        return 0
    print(f"STALE: {len(stale)} of {len(flags)} flag(s):")
    for item in stale:
        print(f"  - {item['key']}: {item['reason']}")
    return 1 if args.fail_on_stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
