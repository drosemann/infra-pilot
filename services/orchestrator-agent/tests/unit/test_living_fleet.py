"""Focused tests for the Living Fleet mood engine and creature store."""

import pytest

import living_fleet


@pytest.fixture()
def isolated_store(monkeypatch, tmp_path):
    """Point the SQLite store at a temp DB so tests never touch real data."""
    monkeypatch.setattr(living_fleet, "DB_PATH", str(tmp_path / "fleet.db"))
    monkeypatch.setattr(living_fleet, "STORE_PATH", str(tmp_path / "legacy.json"))
    monkeypatch.setattr(living_fleet, "ENABLED", True)
    return tmp_path


class TestComputeMood:
    def test_ghost_wins_over_everything(self):
        vitals = {"health": 100, "energy": 100, "hunger": 100}
        assert living_fleet.compute_mood(vitals, {"running": True}, down_minutes=400) == "ghost"

    def test_confirmed_stopped_is_sick_never_thriving(self):
        vitals = {"health": 100, "energy": 100, "hunger": 100, "hygiene": 100, "morale": 100}
        assert living_fleet.compute_mood(vitals, {"running": False}) == "sick"

    def test_unknown_running_state_can_thrive(self):
        vitals = {"health": 90, "energy": 90, "hunger": 90, "hygiene": 90, "morale": 90}
        assert living_fleet.compute_mood(vitals, {}) == "thriving"

    def test_all_unknown_vitals_is_content(self):
        vitals = {k: None for k in living_fleet.VITAL_FNS}
        assert living_fleet.compute_mood(vitals, {}) == "content"

    def test_failed_healthcheck_is_sick(self):
        assert living_fleet.compute_mood({"health": None}, {"healthcheck_ok": False}) == "sick"

    def test_stale_deploy_is_hungry(self):
        vitals = {k: None for k in living_fleet.VITAL_FNS} | {"hunger": 10}
        assert living_fleet.compute_mood(vitals, {}) == "hungry"


class TestVitals:
    def test_no_signals_means_no_scores(self):
        assert all(v is None for v in living_fleet.compute_vitals({}).values())

    def test_restarts_drag_health_down(self):
        assert living_fleet.vital_health({"restart_count_24h": 0}) == 100
        assert living_fleet.vital_health({"restart_count_24h": 4}) < 50


class TestStore:
    def test_birth_only_on_healthy_first_sighting(self, isolated_store):
        view = living_fleet.refresh("sick-arrival", {"running": False})
        assert view["mood"] == "sick"
        assert "sick-arrival" not in living_fleet._load_all()

    def test_healthy_first_sighting_births_and_persists(self, isolated_store):
        view = living_fleet.refresh("w1", {"running": True, "display_name": "api"})
        assert view["display_name"] == "api"
        assert view["stage"] == "egg"
        assert living_fleet._load_all()["w1"]["display_name"] == "api"

    def test_rename_rejects_non_string_names(self, isolated_store):
        living_fleet.refresh("w1", {"running": True})
        assert living_fleet.rename("w1", None) is None
        assert living_fleet.rename("w1", "   ") is None
        assert living_fleet.rename("unknown", "x") is None

    def test_rename_accepts_valid_name(self, isolated_store):
        living_fleet.refresh("w1", {"running": True})
        view = living_fleet.rename("w1", "Sir Deploys-a-Lot")
        assert view is not None
        assert view["display_name"] == "Sir Deploys-a-Lot"

    def test_legacy_json_imports_once(self, isolated_store, tmp_path):
        import json

        legacy = {
            "old": {
                "workload_id": "old",
                "display_name": "old",
                "born_at": 0,
                "retired": False,
                "down_since": None,
                "vitals": {},
                "mood": "content",
                "stage": "adult",
            }
        }
        (tmp_path / "legacy.json").write_text(json.dumps(legacy))
        assert living_fleet._load_all()["old"]["stage"] == "adult"

    def test_explanation_traces_raw_signals(self, isolated_store):
        view = living_fleet.refresh("w1", {"running": True, "restart_count_24h": 2})
        by_vital = {e["vital"]: e for e in view["explanation"]}
        assert by_vital["health"]["signals"]["restart_count_24h"] == 2
