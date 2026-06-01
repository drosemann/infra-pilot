"""Tests for Green Scheduling."""

import pytest
from cogs.green_scheduling import (
    GreenScheduling, ScheduleJob, SchedulePolicy, CarbonWindow,
    JobPriority, ScheduleStatus
)


@pytest.fixture
def scheduler():
    return GreenScheduling({})


class TestGreenScheduling:
    def test_initialization(self, scheduler):
        assert len(scheduler.jobs) > 0
        assert len(scheduler.policies) > 0
        assert len(scheduler.carbon_forecasts) > 0

    def test_create_job(self, scheduler):
        job = scheduler.create_job(
            "job-001", "backup-task",
            priority=JobPriority.MEDIUM,
            estimated_duration_minutes=120
        )
        assert job.job_id == "job-001"
        assert job.status == ScheduleStatus.PENDING

    def test_get_job(self, scheduler):
        jid = list(scheduler.jobs.keys())[0]
        assert scheduler.get_job(jid) is not None

    def test_get_job_not_found(self, scheduler):
        assert scheduler.get_job("nonexistent") is None

    def test_list_jobs(self, scheduler):
        jobs = scheduler.list_jobs()
        assert len(jobs) > 0

    def test_cancel_job(self, scheduler):
        jid = list(scheduler.jobs.keys())[0]
        assert scheduler.cancel_job(jid) is True
        assert scheduler.get_job(jid).status == ScheduleStatus.CANCELLED

    def test_cancel_job_not_found(self, scheduler):
        assert scheduler.cancel_job("nonexistent") is False

    def test_create_policy(self, scheduler):
        policy = scheduler.create_policy(
            "policy-001", "green-hours",
            max_carbon_intensity=200,
            allowed_hours={"start": "08:00", "end": "18:00"}
        )
        assert policy.policy_id == "policy-001"
        assert policy.max_carbon_intensity == 200

    def test_get_policy(self, scheduler):
        pid = list(scheduler.policies.keys())[0]
        assert scheduler.get_policy(pid) is not None

    def test_get_policy_not_found(self, scheduler):
        assert scheduler.get_policy("nonexistent") is None

    def test_list_policies(self, scheduler):
        policies = scheduler.list_policies()
        assert len(policies) > 0

    def test_delete_policy(self, scheduler):
        pid = list(scheduler.policies.keys())[0]
        assert scheduler.delete_policy(pid) is True
        assert scheduler.get_policy(pid) is None

    def test_get_best_window(self, scheduler):
        window = scheduler.get_best_window("dev-001", 60)
        assert window is not None
        assert window["duration_minutes"] >= 60

    def test_get_best_window_no_forecast(self, scheduler):
        window = scheduler.get_best_window("dev-nonexistent", 30)
        assert window is None

    def test_get_carbon_forecast(self, scheduler):
        forecast = scheduler.get_carbon_forecast("dev-001")
        assert forecast is not None
        assert len(forecast) > 0

    def test_get_carbon_forecast_no_data(self, scheduler):
        assert scheduler.get_carbon_forecast("dev-nonexistent") is None

    def test_optimize_schedule(self, scheduler):
        jobs = scheduler.optimize_schedule("dev-001")
        assert len(jobs) > 0

    def test_get_schedule_summary(self, scheduler):
        summary = scheduler.get_schedule_summary()
        assert "total_jobs" in summary
        assert "pending_jobs" in summary
        assert "running_jobs" in summary
        assert "policies" in summary
        assert "projected_carbon_savings_kg" in summary

    def test_add_carbon_forecast(self, scheduler):
        forecast = scheduler.add_carbon_forecast("dev-new", [{"time": "00:00", "intensity": 50}])
        assert forecast is not None
        assert scheduler.get_carbon_forecast("dev-new") is not None

    def test_update_job_status(self, scheduler):
        jid = list(scheduler.jobs.keys())[0]
        assert scheduler.update_job_status(jid, ScheduleStatus.RUNNING) is True
        assert scheduler.get_job(jid).status == ScheduleStatus.RUNNING

    def test_get_schedule_insights(self, scheduler):
        insights = scheduler.get_schedule_insights()
        assert "total_carbon_savings_kg" in insights
        assert "avg_delay_minutes" in insights

    def test_job_priority_enum(self):
        assert JobPriority.LOW.value == "low"
        assert JobPriority.MEDIUM.value == "medium"
        assert JobPriority.HIGH.value == "high"
        assert JobPriority.CRITICAL.value == "critical"

    def test_schedule_status_enum(self):
        assert ScheduleStatus.PENDING.value == "pending"
        assert ScheduleStatus.RUNNING.value == "running"
        assert ScheduleStatus.COMPLETED.value == "completed"
        assert ScheduleStatus.FAILED.value == "failed"
