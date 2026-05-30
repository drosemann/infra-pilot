"""Tests for Session Manager."""
import pytest
import time
from datetime import datetime, timedelta
from session_manager import SessionManager, DeviceFingerprint, GeoIPRecord, SessionActivity


@pytest.fixture
def manager():
    return SessionManager({
        "session_ttl": 86400,
        "max_sessions_per_user": 10,
        "fingerprint_ttl": 2592000,
        "anomaly_score_threshold": 0.7,
        "geoip_enabled": True
    })


class TestSessionLifecycle:
    def test_create_session(self, manager):
        session = manager.create_session("user-001", "127.0.0.1", "Mozilla/5.0", {"device_id": "dev-1"})
        assert session.session_id is not None
        assert session.user_id == "user-001"
        assert session.ip_address == "127.0.0.1"
        assert session.is_active is True
        assert session.created_at is not None

    def test_get_session(self, manager):
        original = manager.create_session("user-001", "10.0.0.1", "Chrome/120")
        retrieved = manager.get_session(original.session_id)
        assert retrieved.session_id == original.session_id

    def test_get_missing_session(self, manager):
        assert manager.get_session("nonexistent") is None

    def test_update_session_activity(self, manager):
        session = manager.create_session("user-001", "10.0.0.1", "Firefox/121")
        old_time = session.last_activity
        time.sleep(0.01)
        manager.update_session_activity(session.session_id)
        assert session.last_activity > old_time

    def test_end_session(self, manager):
        session = manager.create_session("user-001", "10.0.0.1", "Safari/17")
        assert manager.end_session(session.session_id) is True
        assert session.is_active is False
        assert session.ended_at is not None

    def test_end_already_ended_session(self, manager):
        session = manager.create_session("user-001", "10.0.0.1", "Edge")
        manager.end_session(session.session_id)
        assert manager.end_session(session.session_id) is False

    def test_end_missing_session(self, manager):
        assert manager.end_session("nonexistent") is False

    def test_get_active_sessions(self, manager):
        manager.create_session("user-001", "10.0.0.1", "Chrome")
        manager.create_session("user-001", "10.0.0.2", "Firefox")
        sessions = manager.get_active_sessions("user-001")
        assert len(sessions) == 2
        manager.end_session(sessions[0].session_id)
        active = manager.get_active_sessions("user-001")
        assert len(active) == 1

    def test_session_expiry(self, manager):
        session = manager.create_session("user-001", "10.0.0.1", "Browser")
        session.expires_at = datetime.utcnow() - timedelta(seconds=1)
        assert session.is_expired is True

    def test_max_sessions_enforcement(self, manager):
        for _ in range(15):
            manager.create_session("user-max", "10.0.0.1", "Browser")
        sessions = manager.get_active_sessions("user-max")
        assert len(sessions) <= 10


class TestDeviceFingerprinting:
    def test_create_fingerprint(self, manager):
        fp = manager.create_fingerprint("user-001", {"user_agent": "Chrome/120", "screen_resolution": "1920x1080", "timezone": "UTC", "language": "en-US"})
        assert fp.fingerprint_id is not None
        assert fp.user_id == "user-001"
        assert fp.is_trusted is False

    def test_trust_fingerprint(self, manager):
        fp = manager.create_fingerprint("user-001", {"user_agent": "Chrome"})
        assert manager.trust_fingerprint(fp.fingerprint_id) is True
        assert fp.is_trusted is True

    def test_get_user_fingerprints(self, manager):
        manager.create_fingerprint("user-001", {"ua": "Chrome"})
        manager.create_fingerprint("user-001", {"ua": "Firefox"})
        fps = manager.get_user_fingerprints("user-001")
        assert len(fps) == 2

    def test_is_known_device(self, manager):
        fp = manager.create_fingerprint("user-001", {"ua": "Chrome"})
        manager.trust_fingerprint(fp.fingerprint_id)
        assert manager.is_known_device("user-001", fp.fingerprint_id) is True

    def test_is_unknown_device(self, manager):
        assert manager.is_known_device("user-001", "unknown-device") is False


class TestGeoIP:
    def test_record_geoip(self, manager):
        geo = manager.record_geoip("user-001", "8.8.8.8", {"city": "Mountain View", "country": "US", "latitude": 37.386, "longitude": -122.0838})
        assert geo is not None
        assert geo.city == "Mountain View"
        assert geo.country == "US"

    def test_get_last_location(self, manager):
        manager.record_geoip("user-001", "8.8.8.8", {"city": "Mountain View", "country": "US", "lat": 37.386, "lng": -122.0838})
        manager.record_geoip("user-001", "1.1.1.1", {"city": "Sydney", "country": "AU", "lat": -33.8688, "lng": 151.2093})
        last = manager.get_last_location("user-001")
        assert last is not None
        assert last["city"] == "Sydney"

    def test_no_geoip_data(self, manager):
        assert manager.get_last_location("unknown-user") is None


class TestAnomalyDetection:
    def test_detect_impossible_travel(self, manager):
        manager.record_geoip("user-001", "8.8.8.8", {"city": "New York", "country": "US", "lat": 40.7128, "lng": -74.006})
        suspicious = manager.detect_impossible_travel("user-001", "1.1.1.1", {"city": "Tokyo", "country": "JP", "lat": 35.6762, "lng": 139.6503})
        assert suspicious is True

    def test_detect_normal_travel(self, manager):
        manager.record_geoip("user-001", "8.8.8.8", {"city": "New York", "country": "US", "lat": 40.7128, "lng": -74.006})
        normal = manager.detect_impossible_travel("user-001", "8.8.4.4", {"city": "Newark", "country": "US", "lat": 40.7357, "lng": -74.1724})
        assert normal is False

    def test_new_device_anomaly(self, manager):
        score = manager.calculate_anomaly_score("user-001", "unknown-device", "8.8.8.8")
        assert score > 0.5

    def test_known_device_no_anomaly(self, manager):
        fp = manager.create_fingerprint("user-001", {"ua": "Chrome"})
        manager.trust_fingerprint(fp.fingerprint_id)
        score = manager.calculate_anomaly_score("user-001", fp.fingerprint_id, "8.8.8.8")
        assert score < 0.5

    def test_suspicious_session(self, manager):
        foreign_geo = GeoIPRecord("user-001", "foreign_ip", datetime.utcnow(), "Moscow", "RU", 55.7558, 37.6173)
        manager._last_locations["user-001"] = foreign_geo
        session = manager.create_session("user-001", "10.0.0.1", "Browser")
        session.anomaly_score = 0.85
        assert session.is_suspicious is True
        assert session.anomaly_flags is not None

    def test_normal_session_not_suspicious(self, manager):
        session = manager.create_session("user-001", "10.0.0.1", "Browser")
        session.anomaly_score = 0.1
        assert session.is_suspicious is False


class TestSessionActivityLogging:
    def test_log_activity(self, manager):
        session = manager.create_session("user-001", "10.0.0.1", "Browser")
        activity = manager.log_activity(session.session_id, "login", {"method": "password"})
        assert activity is not None
        assert activity.activity_type == "login"

    def test_get_session_activities(self, manager):
        session = manager.create_session("user-001", "10.0.0.1", "Browser")
        manager.log_activity(session.session_id, "login", {})
        manager.log_activity(session.session_id, "page_view", {"page": "/dashboard"})
        manager.log_activity(session.session_id, "logout", {})
        activities = manager.get_session_activities(session.session_id)
        assert len(activities) == 3

    def test_activity_types(self, manager):
        session = manager.create_session("user-001", "10.0.0.1", "Browser")
        activity = manager.log_activity(session.session_id, "sensitive_action", {"action": "delete_server"})
        assert activity.activity_type == "sensitive_action"

    def test_get_activities_empty(self, manager):
        activities = manager.get_session_activities("nonexistent")
        assert len(activities) == 0
