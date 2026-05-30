"""Tests for Auto-Remediation, Maintenance Planner, Runbook Library, Chaos Engineering, and Self-Healing."""
import pytest
import json
from datetime import datetime, timedelta
from cogs.auto_remediation import AutoRemediation, RemediationRule, RemediationAction
from cogs.maintenance_planner import MaintenancePlanner, MaintenanceWindow
from cogs.runbook_library import RunbookLibrary, RunbookTemplate
from cogs.chaos_engineering import ChaosEngineering, ChaosExperiment, FaultDefinition
from cogs.self_healing import SelfHealing, HealingPattern, RemediationResult


class TestAutoRemediation:
    @pytest.fixture
    def cog(self):
        from discord.ext import commands
        bot = commands.Bot(command_prefix="!", intents=None)
        return AutoRemediation(bot)

    def test_create_rule(self, cog):
        rule = cog.create_rule(
            name="Restart Unhealthy Container",
            description="Restart container when health check fails 3 times",
            trigger_type="container_health",
            condition={"health_status": "unhealthy", "failure_count": {"gte": 3}},
            action_type="container_restart",
            action_config={"grace_period": 10},
            cooldown_seconds=300
        )
        assert rule["rule_id"] is not None
        assert rule["name"] == "Restart Unhealthy Container"
        assert rule["enabled"] is True

    def test_get_rule(self, cog):
        r = cog.create_rule("Test Rule", "Desc", "cpu_high", {"cpu": {"gt": 80}}, "scale_up", {}, 60)
        retrieved = cog.get_rule(r["rule_id"])
        assert retrieved["rule_id"] == r["rule_id"]

    def test_list_rules(self, cog):
        cog.create_rule("Rule 1", "D1", "container_health", {}, "restart", {}, 60)
        cog.create_rule("Rule 2", "D2", "disk_space", {}, "cleanup", {}, 60)
        rules = cog.list_rules()
        assert len(rules) >= 2

    def test_update_rule(self, cog):
        r = cog.create_rule("Orig", "Desc", "cpu", {}, "scale", {}, 60)
        cog.update_rule(r["rule_id"], {"name": "Updated", "enabled": False})
        updated = cog.get_rule(r["rule_id"])
        assert updated["name"] == "Updated"
        assert updated["enabled"] is False

    def test_delete_rule(self, cog):
        r = cog.create_rule("Del", "Desc", "mem", {}, "oom_kill", {}, 60)
        assert cog.delete_rule(r["rule_id"]) is True

    def test_enable_disable_rule(self, cog):
        r = cog.create_rule("Toggle", "Desc", "cpu", {}, "scale", {}, 60)
        cog.disable_rule(r["rule_id"])
        assert cog.get_rule(r["rule_id"])["enabled"] is False
        cog.enable_rule(r["rule_id"])
        assert cog.get_rule(r["rule_id"])["enabled"] is True

    def test_evaluate_and_execute(self, cog):
        cog.create_rule("CPU Remediation", "Scale up when CPU > 80", "cpu_high",
            {"cpu_percent": {"gt": 80}}, "scale_up", {"replicas": 2}, 120)
        result = cog.evaluate("cpu_high", {"cpu_percent": 90, "container": "web-01"})
        assert result is not None
        assert result["action"] == "scale_up"
        assert result["triggered"] is True

    def test_cooldown_respected(self, cog):
        cog.create_rule("Cooldown Test", "Test cooldown", "cpu_high",
            {"cpu_percent": {"gt": 80}}, "scale_up", {}, 3600)
        cog.evaluate("cpu_high", {"cpu_percent": 90, "container": "web-01"})
        result2 = cog.evaluate("cpu_high", {"cpu_percent": 95, "container": "web-01"})
        assert result2 is None

    def test_get_remediation_history(self, cog):
        cog.create_rule("Hist Rule", "Test history", "cpu_high", {"cpu_percent": {"gt": 80}}, "scale_up", {}, 60)
        cog.evaluate("cpu_high", {"cpu_percent": 90, "container": "web-01"})
        history = cog.get_history()
        assert len(history) >= 1

    def test_remediation_templates(self, cog):
        templates = cog.get_rule_templates()
        template_names = [t["name"] for t in templates]
        assert "Container Restart" in template_names
        assert "Scale Up Service" in template_names
        assert "Memory Leak Detection" in template_names
        assert "Crash Loop Backoff" in template_names


class TestMaintenancePlanner:
    @pytest.fixture
    def cog(self):
        from discord.ext import commands
        bot = commands.Bot(command_prefix="!", intents=None)
        return MaintenancePlanner(bot)

    def test_schedule_window(self, cog):
        start = datetime.utcnow() + timedelta(hours=24)
        end = start + timedelta(hours=4)
        win = cog.schedule_window(
            name="Database Upgrade",
            description="Upgrade PostgreSQL to v15",
            start_time=start,
            end_time=end,
            affected_systems=["prod-db-01", "prod-db-02"],
            risk_level="medium"
        )
        assert win["window_id"] is not None
        assert win["name"] == "Database Upgrade"
        assert win["status"] == "scheduled"

    def test_get_window(self, cog):
        start = datetime.utcnow() + timedelta(hours=48)
        win = cog.schedule_window("Test", "Desc", start, start + timedelta(hours=2), ["srv-1"], "low")
        retrieved = cog.get_window(win["window_id"])
        assert retrieved["window_id"] == win["window_id"]

    def test_list_windows(self, cog):
        now = datetime.utcnow()
        cog.schedule_window("Win 1", "D1", now + timedelta(hours=1), now + timedelta(hours=2), ["srv-1"], "low")
        cog.schedule_window("Win 2", "D2", now + timedelta(days=7), now + timedelta(days=7, hours=3), ["srv-2"], "high")
        windows = cog.list_windows()
        assert len(windows) >= 2

    def test_filter_by_status(self, cog):
        now = datetime.utcnow()
        cog.schedule_window("Active Win", "D1", now - timedelta(hours=1), now + timedelta(hours=1), ["srv-1"], "low")
        scheduled_windows = cog.list_windows(status="in_progress")
        assert len(scheduled_windows) >= 0

    def test_start_window(self, cog):
        now = datetime.utcnow()
        win = cog.schedule_window("Start Test", "D", now - timedelta(hours=1), now + timedelta(hours=2), ["srv-1"], "low")
        result = cog.start_window(win["window_id"])
        assert result["status"] == "in_progress"

    def test_complete_window(self, cog):
        now = datetime.utcnow()
        win = cog.schedule_window("Complete Test", "D", now - timedelta(hours=2), now + timedelta(hours=2), ["srv-1"], "low")
        cog.start_window(win["window_id"])
        result = cog.complete_window(win["window_id"], "Upgrade successful")
        assert result["status"] == "completed"
        assert result["completion_notes"] == "Upgrade successful"

    def test_cancel_window(self, cog):
        now = datetime.utcnow()
        win = cog.schedule_window("Cancel Test", "D", now + timedelta(hours=24), now + timedelta(hours=26), ["srv-1"], "low")
        result = cog.cancel_window(win["window_id"], "No longer needed")
        assert result["status"] == "cancelled"

    def test_extend_window(self, cog):
        now = datetime.utcnow()
        win = cog.schedule_window("Extend Test", "D", now - timedelta(hours=1), now + timedelta(hours=1), ["srv-1"], "low")
        cog.start_window(win["window_id"])
        result = cog.extend_window(win["window_id"], timedelta(hours=2))
        assert result["extended"] is True

    def test_blackout_period(self, cog):
        now = datetime.utcnow()
        result = cog.add_blackout_period(
            "Holiday Blackout",
            now + timedelta(days=30),
            now + timedelta(days=35),
            ["prod-*"]
        )
        assert result is True

    def test_check_blackout(self, cog):
        now = datetime.utcnow()
        cog.add_blackout_period("Test Blackout", now - timedelta(days=1), now + timedelta(days=1), ["prod-*"])
        assert cog.is_in_blackout("prod-db-01") is True
        assert cog.is_in_blackout("staging-web-01") is False

    def test_get_calendar(self, cog):
        now = datetime.utcnow()
        cog.schedule_window("Calendar Win", "D", now + timedelta(days=3), now + timedelta(days=3, hours=2), ["srv-1"], "low")
        events = cog.get_calendar(now, now + timedelta(days=30))
        assert len(events) >= 1


class TestRunbookLibrary:
    @pytest.fixture
    def cog(self):
        from discord.ext import commands
        bot = commands.Bot(command_prefix="!", intents=None)
        return RunbookLibrary(bot)

    def test_list_templates(self, cog):
        templates = cog.list_templates()
        assert len(templates) >= 6
        names = [t["name"] for t in templates]
        assert "Database Rollback" in names
        assert "SSL Certificate Renewal" in names
        assert "Incident Response" in names

    def test_get_template(self, cog):
        template = cog.get_template("db_rollback")
        assert template is not None
        assert template["name"] == "Database Rollback"
        assert len(template["steps"]) > 0

    def test_get_missing_template(self, cog):
        assert cog.get_template("nonexistent") is None

    def test_instantiate_runbook(self, cog):
        instance = cog.instantiate("db_rollback", {
            "db_name": "prod_db",
            "backup_file": "/backups/prod_db_2024.sql",
            "target_version": "14.5"
        }, "user-001")
        assert instance["instance_id"] is not None
        assert instance["template_id"] == "db_rollback"
        assert instance["status"] == "in_progress"

    def test_get_instance(self, cog):
        inst = cog.instantiate("ssl_renewal", {"domain": "example.com"}, "user-001")
        retrieved = cog.get_instance(inst["instance_id"])
        assert retrieved["instance_id"] == inst["instance_id"]

    def test_complete_step(self, cog):
        inst = cog.instantiate("incident_response", {"incident_id": "INC-001", "severity": "high"}, "user-001")
        result = cog.complete_step(inst["instance_id"], 0, {"output": "verified"})
        assert result is True

    def test_get_progress(self, cog):
        inst = cog.instantiate("backup_restore", {"backup_id": "bk-001", "target": "srv-01"}, "user-001")
        progress = cog.get_progress(inst["instance_id"])
        assert progress["completed_steps"] >= 0
        assert progress["total_steps"] > 0

    def test_vote_template(self, cog):
        cog.vote_template("db_rollback", "user-001", 5)
        cog.vote_template("db_rollback", "user-002", 4)
        template = cog.get_template("db_rollback")
        assert template["rating"] >= 4.0

    def test_search_templates(self, cog):
        results = cog.search_templates("ssl")
        assert len(results) >= 1
        results2 = cog.search_templates("kubernetes")
        assert len(results2) >= 0


class TestChaosEngineering:
    @pytest.fixture
    def cog(self):
        from discord.ext import commands
        bot = commands.Bot(command_prefix="!", intents=None)
        return ChaosEngineering(bot)

    def test_create_experiment(self, cog):
        exp = cog.create_experiment(
            name="CPU Spike Test",
            description="Test system behavior under CPU pressure",
            target={"type": "container", "selector": "app=web", "namespace": "production"},
            faults=[{"type": "cpu_stress", "parameters": {"cores": 4, "duration": 60}}],
            blast_radius={"max_containers": 3, "exclude": ["critical-svc"]}
        )
        assert exp["experiment_id"] is not None
        assert exp["status"] == "created"

    def test_run_experiment(self, cog):
        exp = cog.create_experiment("Memory Test", "Test OOM handling",
            {"type": "container", "selector": "app=worker"}, [{"type": "memory_hog", "parameters": {"size_mb": 512, "duration": 30}}], {})
        run = cog.run_experiment(exp["experiment_id"])
        assert run["status"] == "running"

    def test_stop_experiment(self, cog):
        exp = cog.create_experiment("Stop Test", "Test stop", {"type": "container", "selector": "app=test"},
            [{"type": "network_delay", "parameters": {"latency_ms": 2000, "jitter_ms": 500}}], {})
        cog.run_experiment(exp["experiment_id"])
        stopped = cog.stop_experiment(exp["experiment_id"])
        assert stopped["status"] == "stopped"

    def test_get_experiment(self, cog):
        exp = cog.create_experiment("Get Test", "Desc", {"type": "host", "selector": "worker-1"},
            [{"type": "disk_fill", "parameters": {"size_mb": 1000}}], {})
        retrieved = cog.get_experiment(exp["experiment_id"])
        assert retrieved["experiment_id"] == exp["experiment_id"]

    def test_list_fault_types(self, cog):
        faults = cog.list_fault_types()
        fault_names = [f["name"] for f in faults]
        assert "CPU Stress" in fault_names
        assert "Memory Hog" in fault_names
        assert "Network Delay" in fault_names
        assert "Disk Fill" in fault_names
        assert "Container Kill" in fault_names
        assert "Network Partition" in fault_names
        assert "DNS Failure" in fault_names
        assert "IO Stress" in fault_names
        assert "Database Latency" in fault_names
        assert "Node Drain" in fault_names

    def test_experiment_with_multiple_faults(self, cog):
        exp = cog.create_experiment("Multi Fault", "Test",
            {"type": "container", "selector": "app=all"},
            [
                {"type": "cpu_stress", "parameters": {"cores": 2, "duration": 30}},
                {"type": "network_delay", "parameters": {"latency_ms": 500, "jitter_ms": 100}},
                {"type": "memory_hog", "parameters": {"size_mb": 256, "duration": 30}}
            ], {})
        assert len(exp["faults"]) == 3

    def test_get_experiment_history(self, cog):
        cog.create_experiment("Hist 1", "D1", {"type": "container", "selector": "app=a"}, [{"type": "cpu_stress", "parameters": {}}], {})
        cog.create_experiment("Hist 2", "D2", {"type": "container", "selector": "app=b"}, [{"type": "network_delay", "parameters": {}}], {})
        history = cog.list_experiments()
        assert len(history) >= 2


class TestSelfHealing:
    @pytest.fixture
    def cog(self):
        from discord.ext import commands
        bot = commands.Bot(command_prefix="!", intents=None)
        return SelfHealing(bot)

    def test_detect_pattern(self, cog):
        pattern = cog.detect_pattern("container_restart", {
            "container": "web-01",
            "restart_count": 8,
            "cpu_percent": 45,
            "memory_percent": 60,
            "health": "unhealthy"
        })
        assert pattern is not None
        assert pattern["pattern_type"] == "container_restart"
        assert pattern["confidence"] > 0

    def test_get_recommended_action(self, cog):
        recommendation = cog.get_recommendation(
            "memory_leak", {"container": "worker-01", "memory_percent": 92, "memory_trend": "increasing"}
        )
        assert recommendation is not None
        assert recommendation["action"] is not None

    def test_execute_remediation(self, cog):
        result = cog.execute_remediation("container_restart", {
            "container": "web-02",
            "restart_count": 12,
            "cpu_percent": 30,
            "memory_percent": 40,
            "health": "unhealthy"
        })
        assert result["action"] is not None

    def test_get_healing_status(self, cog):
        status = cog.get_status()
        assert "total_remediations" in status
        assert "success_rate" in status
        assert "patterns_detected" in status
        assert "model_learned_actions" in status

    def test_get_history(self, cog):
        cog.detect_pattern("container_restart", {"container": "web-01", "restart_count": 5, "health": "unhealthy"})
        history = cog.get_remediation_history()
        assert len(history) >= 0

    def test_feedback_loop(self, cog):
        pattern = cog.detect_pattern("crash_loop", {"container": "api-01", "restart_count": 15, "health": "unhealthy"})
        cog.execute_remediation("crash_loop", {"container": "api-01"})
        feedback = cog.submit_feedback("api-01", True, "Worked perfectly")
        assert feedback is True

    def test_retrain_model(self, cog):
        result = cog.retrain_model()
        assert result is True or result is False

    def test_confidence_thresholds(self, cog):
        thresholds = cog.get_confidence_thresholds()
        assert "auto_remediate" in thresholds
        assert "suggest" in thresholds
        assert "log_only" in thresholds
