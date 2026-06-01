"""Tests for Auto Shutdown Policies."""

import pytest
from datetime import datetime
from cogs.auto_shutdown_policies import (
    AutoShutdownPolicies, ShutdownPolicy, ShutdownSchedule,
    ShutdownAction, PolicyScope, ScheduleType
)


@pytest.fixture
def shutdown():
    return AutoShutdownPolicies({})


class TestShutdownPolicy:
    def test_create(self):
        policy = ShutdownPolicy(
            "pol-001", "night-shutdown",
            ShutdownAction.HIBERNATE,
            enabled=True
        )
        assert policy.policy_id == "pol-001"
        assert policy.action == ShutdownAction.HIBERNATE

    def test_to_dict(self):
        policy = ShutdownPolicy("pol-001", "test", ShutdownAction.SHUTDOWN)
        d = policy.to_dict()
        assert d["policy_id"] == "pol-001"
        assert d["enabled"] is True


class TestAutoShutdownPolicies:
    def test_initialization(self, shutdown):
        assert len(shutdown.policies) > 0
        assert len(shutdown.schedules) > 0

    def test_create_policy(self, shutdown):
        policy = shutdown.create_policy(
            "pol-new", "weekend-off",
            ShutdownAction.SHUTDOWN,
            scope=PolicyScope.GLOBAL
        )
        assert policy.policy_id == "pol-new"
        assert policy.scope == PolicyScope.GLOBAL

    def test_get_policy(self, shutdown):
        pid = list(shutdown.policies.keys())[0]
        assert shutdown.get_policy(pid) is not None

    def test_get_policy_not_found(self, shutdown):
        assert shutdown.get_policy("nonexistent") is None

    def test_list_policies(self, shutdown):
        policies = shutdown.list_policies()
        assert len(policies) > 0

    def test_update_policy(self, shutdown):
        pid = list(shutdown.policies.keys())[0]
        updated = shutdown.update_policy(pid, {"enabled": False})
        assert updated is not None
        assert updated.enabled is False

    def test_update_policy_not_found(self, shutdown):
        assert shutdown.update_policy("nonexistent", {}) is None

    def test_delete_policy(self, shutdown):
        pid = list(shutdown.policies.keys())[0]
        assert shutdown.delete_policy(pid) is True

    def test_delete_policy_not_found(self, shutdown):
        assert shutdown.delete_policy("nonexistent") is False

    def test_create_schedule(self, shutdown):
        schedule = shutdown.create_schedule(
            "sched-new", "pol-new",
            ScheduleType.WEEKLY,
            time_start="22:00",
            time_end="06:00",
            days_of_week=["Mon", "Tue", "Wed", "Thu", "Fri"]
        )
        assert schedule.schedule_id == "sched-new"
        assert schedule.time_start == "22:00"

    def test_get_schedule(self, shutdown):
        sid = list(shutdown.schedules.keys())[0]
        assert shutdown.get_schedule(sid) is not None

    def test_get_schedule_not_found(self, shutdown):
        assert shutdown.get_schedule("nonexistent") is None

    def test_list_schedules(self, shutdown):
        schedules = shutdown.list_schedules()
        assert len(schedules) > 0

    def test_list_schedules_by_policy(self, shutdown):
        first = list(shutdown.schedules.values())[0]
        filtered = shutdown.list_schedules(policy_id=first.policy_id)
        assert len(filtered) > 0

    def test_delete_schedule(self, shutdown):
        sid = list(shutdown.schedules.keys())[0]
        assert shutdown.delete_schedule(sid) is True

    def test_delete_schedule_not_found(self, shutdown):
        assert shutdown.delete_schedule("nonexistent") is False

    def test_simulate_policy(self, shutdown):
        pid = list(shutdown.policies.keys())[0]
        result = shutdown.simulate_policy(pid, ["dev-001"])
        assert result["devices_affected"] > 0
        assert "estimated_savings" in result

    def test_simulate_policy_not_found(self, shutdown):
        result = shutdown.simulate_policy("nonexistent", ["dev-001"])
        assert result["devices_affected"] == 0

    def test_get_shutdown_summary(self, shutdown):
        summary = shutdown.get_shutdown_summary()
        assert "total_policies" in summary
        assert "enabled_policies" in summary
        assert "active_schedules" in summary
        assert "estimated_daily_savings_kwh" in summary
        assert "estimated_montly_savings" in summary
        assert "devices_covered" in summary

    def test_get_policy_effectiveness(self, shutdown):
        pid = list(shutdown.policies.keys())[0]
        effectiveness = shutdown.get_policy_effectiveness(pid)
        assert "hours_saved_daily" in effectiveness
        assert "energy_saved_kwh" in effectiveness
        assert "cost_saved" in effectiveness
        assert "compliance_rate_pct" in effectiveness

    def test_get_policy_effectiveness_not_found(self, shutdown):
        assert shutdown.get_policy_effectiveness("nonexistent") is None

    def test_generate_report(self, shutdown):
        report = shutdown.generate_report()
        assert "generated_at" in report
        assert "total_policies" in report
        assert "total_schedules" in report
        assert "total_savings" in report
        assert "policy_details" in report

    def test_shutdown_action_enum(self):
        assert ShutdownAction.SHUTDOWN.value == "shutdown"
        assert ShutdownAction.HIBERNATE.value == "hibernate"
        assert ShutdownAction.SLEEP.value == "sleep"
        assert ShutdownAction.STOP.value == "stop"

    def test_policy_scope_enum(self):
        assert PolicyScope.GLOBAL.value == "global"
        assert PolicyScope.DEVICE.value == "device"
        assert PolicyScope.GROUP.value == "group"
