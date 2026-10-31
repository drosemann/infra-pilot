"""Unit tests for scripts/flag-hygiene.py (pure find_stale logic)."""

import datetime
import importlib.util
import os

import pytest

SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "..", "scripts", "flag-hygiene.py"
)

spec = importlib.util.spec_from_file_location("flag_hygiene", SCRIPT)
flag_hygiene = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flag_hygiene)

NOW = datetime.datetime(2026, 10, 26, tzinfo=datetime.timezone.utc)


def _flag(key, **overrides):
    base = {
        "key": key,
        "status": "active",
        "expires_at": None,
        "updated_at": "2026-10-20T00:00:00Z",
        "created_at": "2026-10-01T00:00:00Z",
        "rules": {},
    }
    base.update(overrides)
    return base


def test_fresh_flag_not_stale():
    assert flag_hygiene.find_stale([_flag("a")], NOW) == []


def test_expired_flag_is_stale():
    stale = flag_hygiene.find_stale(
        [_flag("old", expires_at="2026-01-01T00:00:00Z")], NOW
    )
    assert [s["key"] for s in stale] == ["old"]
    assert "expired" in stale[0]["reason"]


def test_untouched_flag_is_stale():
    stale = flag_hygiene.find_stale(
        [_flag("dusty", updated_at="2025-01-01T00:00:00Z")], NOW, untouched_days=90
    )
    assert [s["key"] for s in stale] == ["dusty"]


def test_archived_flag_ignored():
    flags = [_flag("gone", status="archived", expires_at="2020-01-01T00:00:00Z")]
    assert flag_hygiene.find_stale(flags, NOW) == []


def test_rule_touch_counts_as_activity():
    flags = [
        _flag(
            "tended",
            updated_at="2025-01-01T00:00:00Z",
            rules={"production": {"updated_at": "2026-10-25T00:00:00Z"}},
        )
    ]
    assert flag_hygiene.find_stale(flags, NOW) == []


def test_main_requires_token(capsys):
    assert flag_hygiene.main(["--token", ""]) == 2
    assert "admin token required" in capsys.readouterr().err
