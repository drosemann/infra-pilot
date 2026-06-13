"""Tests for session_manager_ext module."""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from services.integration_service.src.session_manager_ext import SessionManager, EnhancedDeviceFingerprint, SessionRiskLevel


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = SessionManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestSessionCreation:
    def test_create_session(self, manager):
        session = manager.create_session(
            user_id="user123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            auth_method="password",
        )
        assert session.session_id is not None
        assert session.user_id == "user123"
        assert session.ip_address == "192.168.1.100"
        assert session.risk_level == SessionRiskLevel.LOW
        assert session.is_active == True

    def test_get_session(self, manager):
        session = manager.create_session(user_id="user1", ip_address="10.0.0.1", user_agent="Chrome")
        retrieved = manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id


class TestDeviceFingerprinting:
    def test_register_device_fingerprint(self, manager):
        fp = EnhancedDeviceFingerprint(
            user_agent="Mozilla/5.0",
            platform="Windows",
            platform_version="10",
            screen_resolution="1920x1080",
            screen_orientation="landscape",
            color_depth=24,
            pixel_ratio=1.0,
            timezone="America/New_York",
            timezone_offset=-300,
            language="en-US",
            languages=["en-US", "en"],
            canvas_hash="abc123",
            webgl_vendor="Google Inc.",
            webgl_renderer="ANGLE",
            webgl_version="WebGL 2.0",
            installed_fonts=["Arial", "Verdana"],
            installed_plugins=["Chrome PDF Plugin"],
            ip_address="10.0.0.1",
            accept_language="en-US,en;q=0.9",
            hardware_concurrency=8,
            device_memory=8,
            touch_support=False,
            max_touch_points=0,
            audio_fingerprint="def456",
            battery_level=0.85,
            charging=True,
            cpu_architecture="x86_64",
            device_model="Unknown",
            device_vendor="Unknown",
            do_not_track=False,
            ad_blocker_detected=False,
            cookies_enabled=True,
            localStorage_available=True,
            sessionStorage_available=True,
            indexed_db_available=True,
        )
        result = manager.register_device_fingerprint("user1", "sess1", fp)
        assert result is not None
        assert result["device_id"] is not None
        assert result["fingerprint_hash"] is not None

    def test_compute_fingerprint_hash(self, manager):
        fp = EnhancedDeviceFingerprint(
            user_agent="Mozilla/5.0",
            platform="Linux",
            platform_version=None,
            screen_resolution=None,
            screen_orientation=None,
            color_depth=None,
            pixel_ratio=None,
            timezone=None,
            timezone_offset=None,
            language=None,
            languages=[],
            canvas_hash=None,
            webgl_vendor=None,
            webgl_renderer=None,
            webgl_version=None,
            installed_fonts=[],
            installed_plugins=[],
            ip_address="10.0.0.1",
            accept_language=None,
            hardware_concurrency=None,
            device_memory=None,
            touch_support=False,
            max_touch_points=None,
            audio_fingerprint=None,
            battery_level=None,
            charging=None,
            cpu_architecture=None,
            device_model=None,
            device_vendor=None,
            do_not_track=None,
            ad_blocker_detected=None,
            cookies_enabled=None,
            localStorage_available=None,
            sessionStorage_available=None,
            indexed_db_available=None,
        )
        hash1 = fp.compute_hash()
        assert hash1 is not None
        assert len(hash1) == 64


class TestImpossibleTravel:
    def test_detect_impossible_travel(self, manager):
        manager.create_session(user_id="user1", ip_address="10.0.0.1", user_agent="Chrome")
        detection = manager.detect_impossible_travel(
            "user1", ip_address="10.0.0.2", latitude=51.5, longitude=-0.12,
            previous_latitude=40.7, previous_longitude=-74.0, time_diff_seconds=300,
        )
        assert detection is not None
        assert detection["is_impossible_travel"] == True

    def test_same_location_no_travel(self, manager):
        detection = manager.detect_impossible_travel(
            "user1", ip_address="10.0.0.1", latitude=40.7, longitude=-74.0,
            previous_latitude=40.7, previous_longitude=-74.0, time_diff_seconds=3600,
        )
        assert detection is not None
        assert detection["is_impossible_travel"] == False

    def test_slow_travel_allowed(self, manager):
        detection = manager.detect_impossible_travel(
            "user1", ip_address="10.0.0.2", latitude=51.5, longitude=-0.12,
            previous_latitude=40.7, previous_longitude=-74.0, time_diff_seconds=86400,
        )
        assert detection["is_impossible_travel"] == False


class TestRiskScoring:
    def test_compute_risk_score_low(self, manager):
        score = manager.compute_risk_score(
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            auth_method="password",
            failed_attempts=0,
            is_new_device=False,
            is_new_location=False,
        )
        assert score < 30

    def test_compute_risk_score_high(self, manager):
        score = manager.compute_risk_score(
            ip_address="10.0.0.1",
            user_agent="unknown",
            auth_method="password",
            failed_attempts=5,
            is_new_device=True,
            is_new_location=True,
        )
        assert score > 50


class TestSessionRevocation:
    def test_revoke_session(self, manager):
        session = manager.create_session(user_id="user1", ip_address="10.0.0.1", user_agent="Chrome")
        assert manager.revoke_session(session.session_id, "user_requested") == True
        retrieved = manager.get_session(session.session_id)
        assert retrieved.is_active == False

    def test_revoke_all_user_sessions(self, manager):
        manager.create_session(user_id="user1", ip_address="10.0.0.1", user_agent="Chrome")
        manager.create_session(user_id="user1", ip_address="10.0.0.2", user_agent="Firefox")
        count = manager.revoke_all_user_sessions("user1")
        assert count == 2
        assert len(manager.list_user_sessions("user1", active_only=True)) == 0

    def test_revoke_nonexistent_session(self, manager):
        assert manager.revoke_session("nonexistent-session", "test") == False


class TestGeolocation:
    def test_get_geolocation(self, manager):
        geo = manager.get_geolocation("8.8.8.8")
        assert geo is not None


class TestSessionLimits:
    def test_max_sessions_per_user(self, manager):
        for i in range(5):
            manager.create_session(user_id="user1", ip_address=f"10.0.0.{i}", user_agent="Chrome")
        reached, count = manager.check_session_limit("user1", max_sessions=3)
        assert reached == True
        assert count == 5


class TestStatistics:
    def test_get_statistics(self, manager):
        manager.create_session(user_id="user1", ip_address="10.0.0.1", user_agent="Chrome")
        stats = manager.get_statistics()
        assert stats["total_sessions"] >= 1


class TestAnomalyDetection:
    def test_detect_anomalous_activity(self, manager):
        anomaly = manager.detect_anomalous_activity(
            user_id="user1", action="login", ip_address="10.0.0.1",
            user_agent="Mozilla/5.0", resource="admin-panel",
        )
        assert anomaly is not None
        assert "risk_score" in anomaly
