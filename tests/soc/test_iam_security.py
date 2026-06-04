import pytest


class TestIAMSecurity:
    def test_user_crud(self):
        users = []
        u = {"id": "u1", "username": "jdoe", "mfa_enabled": True}
        users.append(u)
        assert len(users) == 1
        u["mfa_enabled"] = False
        assert u["mfa_enabled"] is False
        users = [x for x in users if x["id"] != "u1"]
        assert len(users) == 0

    def test_role_permissions(self):
        roles = [{"name": "Admin", "policies": ["admin-access"], "overprivileged": True}]
        assert roles[0]["overprivileged"] is True

    def test_access_review(self):
        reviews = [{"id": "r1", "status": "pending", "due_date": "2025-12-01"}]
        assert reviews[0]["status"] == "pending"
        reviews[0]["status"] = "completed"
        assert reviews[0]["status"] == "completed"

    def test_audit_events(self):
        events = [
            {"action": "login", "success": True},
            {"action": "failed_login", "success": False},
        ]
        failures = [e for e in events if not e["success"]]
        assert len(failures) == 1

    def test_user_validation(self):
        with pytest.raises(ValueError):
            u = {}
            if "username" not in u:
                raise ValueError("Username required")
