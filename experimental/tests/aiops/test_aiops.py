import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from services.integration_service.src.aiops.alert_correlation import AlertCorrelationEngine
from services.integration_service.src.aiops.capacity_planning import CapacityPlanner
from services.integration_service.src.aiops.change_risk import ChangeRiskAnalyzer
from services.integration_service.src.aiops.conversational_ops import ConversationalOpsAssistant
from services.integration_service.src.aiops.digital_experience import DigitalExperienceMonitor
from services.integration_service.src.aiops.health_forecasting import ServiceHealthForecaster
from services.integration_service.src.aiops.incident_remediation import IncidentRemediationEngine, RemediationStatus
from services.integration_service.src.aiops.ops_chatbot import OpsChatbot
from services.integration_service.src.aiops.predictive_scaling import PredictiveScalingEngine
from services.integration_service.src.aiops.root_cause_analysis import RootCauseAnalyzer


# === test_alert_correlation.py ===

@pytest.fixture
def alert_correlation_engine():
    return AlertCorrelationEngine({})


class TestAlertCorrelation:
    def test_ingest_alert(self, alert_correlation_engine):
        alert = alert_correlation_engine.ingest_alert("HighCPU", "prometheus", "critical", "CPU at 95%")
        assert alert["name"] == "HighCPU"
        assert alert["status"] in ("firing", "suppressed")

    def test_dedup_same_alert(self, alert_correlation_engine):
        a1 = alert_correlation_engine.ingest_alert("DupTest", "source", "warning", "test message")
        a2 = alert_correlation_engine.ingest_alert("DupTest", "source", "warning", "test message")
        assert a1["id"] == a2["id"]

    def test_create_incident(self, alert_correlation_engine):
        alert_correlation_engine.ingest_alert("Alert1", "source", "critical", "message 1")
        alert_correlation_engine.ingest_alert("Alert2", "source", "warning", "message 2 about same source")
        incidents = alert_correlation_engine.list_incidents()
        assert len(incidents) >= 1

    def test_acknowledge_alert(self, alert_correlation_engine):
        alert = alert_correlation_engine.ingest_alert("AckTest", "source", "warning", "ack me")
        alert_correlation_engine.acknowledge_alert(alert["id"])
        assert alert["status"] == "acknowledged"

    def test_resolve_alert(self, alert_correlation_engine):
        alert = alert_correlation_engine.ingest_alert("ResolveTest", "source", "warning", "resolve me")
        alert_correlation_engine.resolve_alert(alert["id"])
        assert alert["status"] == "resolved"

    def test_suppression_rule(self, alert_correlation_engine):
        rule = alert_correlation_engine.add_suppression_rule("Suppress Test CPU", match_name="CPU")
        assert rule["status"] == "active"
        suppressed = alert_correlation_engine.ingest_alert("HighCPUAlert", "test", "critical", "CPU high")
        assert suppressed["status"] == "suppressed"

    def test_incident_resolution(self, alert_correlation_engine):
        alert_correlation_engine.ingest_alert("IncTest", "source", "critical", "incident test")
        incident = alert_correlation_engine.list_incidents(status="firing")[0]
        alert_correlation_engine.resolve_incident(incident["id"])
        assert incident["status"] == "resolved"

    def test_statistics(self, alert_correlation_engine):
        stats = alert_correlation_engine.get_statistics()
        assert "total_alerts" in stats
        assert "noise_reduction_percentage" in stats


# === test_capacity_planning.py ===

@pytest.fixture
def planner():
    return CapacityPlanner({})


class TestCapacityPlanning:
    def test_record_usage(self, planner):
        result = planner.record_usage("web-cluster", "cpu", 100, 45)
        assert result["utilization"] == 0.45

    def test_get_usage_no_data(self, planner):
        usage = planner.get_usage("unknown", "cpu")
        assert usage["data_points"] == 0

    def test_recommendation_insufficient_data(self, planner):
        rec = planner.generate_recommendation("test-svc", "cpu")
        assert "error" in rec

    def test_recommendation_with_data(self, planner):
        for i in range(15):
            planner.record_usage("svc-growth", "cpu", 100, 30 + i * 2)
        rec = planner.generate_recommendation("svc-growth", "cpu")
        assert "priority" in rec
        assert "recommended_capacity" in rec

    def test_what_if_simulation(self, planner):
        for i in range(20):
            planner.record_usage("sim-svc", "cpu", 100, 40 + i)
        result = planner.what_if_simulation("sim-svc", "cpu", "traffic_spike")
        assert result["peak_utilization"] > result["base_utilization"]

    def test_black_friday_simulation(self, planner):
        for i in range(20):
            planner.record_usage("bf-svc", "cpu", 100, 30 + i)
        result = planner.what_if_simulation("bf-svc", "cpu", "black_friday")
        assert "peak_utilization" in result

    def test_dismiss_recommendation(self, planner):
        for i in range(15):
            planner.record_usage("dismiss-svc", "cpu", 100, 40)
        rec = planner.generate_recommendation("dismiss-svc", "cpu")
        assert planner.dismiss_recommendation(rec["id"]) is True

    def test_summary(self, planner):
        summary = planner.get_summary()
        assert "total_recommendations" in summary


# === test_change_risk.py ===

@pytest.fixture
def analyzer():
    return ChangeRiskAnalyzer({})


class TestChangeRisk:
    def test_plan_change(self, analyzer):
        result = analyzer.plan_change("Update nginx config", "Update SSL cert", "config_change",
                                       "nginx-proxy", ["nginx-config", "ssl-certs"])
        assert "change" in result
        assert "analysis" in result

    def test_analyze_risk(self, analyzer):
        result = analyzer.plan_change("Database migration", "Migrate to new schema", "migration",
                                       "postgres-db", ["db-primary", "db-replica", "app-config", "cache"])
        analysis = result["analysis"]
        assert "overall_risk_level" in analysis
        assert "risk_factors" in analysis

    def test_approve_change(self, analyzer):
        result = analyzer.plan_change("Test change", "", "deployment", "web", ["web-1"])
        change_id = result["change"]["id"]
        approved = analyzer.approve_change(change_id, "admin")
        assert approved["status"] == "approved"

    def test_reject_change(self, analyzer):
        result = analyzer.plan_change("Bad change", "", "deployment", "web", ["web-1"])
        change_id = result["change"]["id"]
        rejected = analyzer.reject_change(change_id, "Too risky")
        assert rejected["status"] == "rejected"

    def test_record_outcome(self, analyzer):
        result = analyzer.plan_change("Outcome test", "", "deployment", "api", ["api-1"])
        change_id = result["change"]["id"]
        outcome = analyzer.record_outcome(change_id, "completed", {"rollback_plan": True})
        assert outcome["status"] == "completed"

    def test_high_risk_migration(self, analyzer):
        result = analyzer.plan_change("Critical DB migration", "", "migration", "db",
                                       ["db-1", "db-2", "db-3", "cache", "app", "worker"])
        assert result["analysis"]["overall_risk_level"] in ("high", "critical", "medium")

    def test_low_risk_change(self, analyzer):
        result = analyzer.plan_change("Minor config", "", "config_change", "web", ["web-config"])
        assert result["change"]["status"] == "pending"

    def test_statistics(self, analyzer):
        stats = analyzer.get_statistics()
        assert "total_changes" in stats
        assert "success_rate" in stats


# === test_conversational_ops.py ===

@pytest.fixture
def assistant():
    return ConversationalOpsAssistant({})


class TestConversationalOps:
    def test_status_check(self, assistant):
        result = assistant.process_message("session-1", "user-1", "What's the status of web-server?")
        assert result["intent"] == "status_check"
        assert result["success"] is True

    def test_restart_intent(self, assistant):
        result = assistant.process_message("session-2", "user-1", "restart nginx")
        assert result["intent"] == "restart"
        assert result["success"] is True

    def test_deploy_intent(self, assistant):
        result = assistant.process_message("session-3", "user-1", "deploy version 3.2 to staging")
        assert result["intent"] == "deploy"
        assert result["success"] is True

    def test_logs_intent(self, assistant):
        result = assistant.process_message("session-4", "user-1", "show logs for database")
        assert result["intent"] == "logs"

    def test_help_intent(self, assistant):
        result = assistant.process_message("session-5", "user-1", "help")
        assert result["intent"] == "help"

    def test_list_resources(self, assistant):
        result = assistant.process_message("session-6", "user-1", "list all servers")
        assert result["intent"] == "list_resources"

    def test_unknown_intent(self, assistant):
        result = assistant.process_message("session-7", "user-1", "xyzzy the magic word")
        assert result["intent"] == "unknown"
        assert result["success"] is False

    def test_session_management(self, assistant):
        result1 = assistant.process_message("sess-mgmt", "user-2", "status web")
        result2 = assistant.process_message("sess-mgmt", "user-2", "restart web")
        session = assistant.get_session("sess-mgmt")
        assert len(session["messages"]) >= 4

    def test_statistics(self, assistant):
        assistant.process_message("stats-sess", "user-3", "status app")
        assistant.process_message("stats-sess", "user-3", "restart app")
        stats = assistant.get_statistics()
        assert stats["total_messages"] >= 2

    def test_scale_intent(self, assistant):
        result = assistant.process_message("sess-scale", "user-1", "scale api-service to 5 replicas")
        assert result["intent"] == "scale"

    def test_metrics_intent(self, assistant):
        result = assistant.process_message("sess-metrics", "user-1", "show CPU for web-server")
        assert result["intent"] == "metrics"

    def test_backup_intent(self, assistant):
        result = assistant.process_message("sess-backup", "user-1", "create a backup of postgres")
        assert result["intent"] == "backup"


# === test_digital_experience.py ===

@pytest.fixture
def monitor():
    return DigitalExperienceMonitor({})


class TestDigitalExperience:
    def test_create_monitor(self, monitor):
        m = monitor.create_monitor("Test Site", "https://example.com", "browser_synthetic")
        assert m["name"] == "Test Site"
        assert m["status"] == "active"

    def test_get_monitor(self, monitor):
        m = monitor.create_monitor("Get Test", "https://test.com")
        found = monitor.get_monitor(m["id"])
        assert found["id"] == m["id"]

    def test_update_monitor(self, monitor):
        m = monitor.create_monitor("Update Test", "https://update.com")
        updated = monitor.update_monitor(m["id"], {"name": "Updated Name"})
        assert updated["name"] == "Updated Name"

    def test_delete_monitor(self, monitor):
        m = monitor.create_monitor("Delete Test", "https://delete.com")
        assert monitor.delete_monitor(m["id"]) is True
        assert monitor.get_monitor(m["id"]) is None

    def test_run_check(self, monitor):
        m = monitor.create_monitor("Check Test", "https://check.com")
        result = monitor.run_check(m["id"])
        assert "result" in result
        assert "metrics" in result

    def test_monitor_stats(self, monitor):
        m = monitor.create_monitor("Stats Test", "https://stats.com")
        stats = monitor.get_monitor_stats(m["id"])
        assert "uptime_percentage" in stats

    def test_global_summary(self, monitor):
        summary = monitor.get_global_summary()
        assert "total_monitors" in summary

    def test_core_web_vitals(self, monitor):
        m = monitor.create_monitor("Vitals Test", "https://vitals.com")
        monitor.run_check(m["id"])
        vitals = monitor.get_core_web_vitals(m["id"])
        assert "data_points" in vitals

    def test_list_monitors_filtered(self, monitor):
        monitor.create_monitor("Active", "https://a.com")
        monitor.create_monitor("Paused", "https://b.com", status="paused")
        active = monitor.list_monitors(status="active")
        assert all(m["status"] == "active" for m in active)


# === test_health_forecasting.py ===

@pytest.fixture
def forecaster():
    return ServiceHealthForecaster({})


class TestHealthForecasting:
    def test_register_service(self, forecaster):
        svc = forecaster.register_service("svc-01", "Web Server")
        assert svc["name"] == "Web Server"
        assert svc["current_health"] == "unknown"

    def test_record_snapshot(self, forecaster):
        forecaster.register_service("svc-02", "API Gateway")
        result = forecaster.record_snapshot("svc-02", {"availability": 0.99, "performance": 0.95, "capacity": 0.85})
        assert result["overall_score"] > 0

    def test_forecast_insufficient_data(self, forecaster):
        forecaster.register_service("svc-03", "Test")
        result = forecaster.forecast("svc-03")
        assert "error" in result

    def test_forecast_with_data(self, forecaster):
        forecaster.register_service("svc-04", "Test 2")
        for i in range(15):
            score = 0.95 - i * 0.02
            forecaster.record_snapshot("svc-04", {"availability": score, "performance": score, "capacity": score})
        result = forecaster.forecast("svc-04")
        assert "forecast_scores" in result

    def test_dashboard(self, forecaster):
        forecaster.register_service("svc-da", "Dash A")
        forecaster.register_service("svc-db", "Dash B")
        dash = forecaster.get_dashboard()
        assert dash["total_services"] >= 2

    def test_trend_detection(self, forecaster):
        forecaster.register_service("svc-trend", "Trend Test")
        for i in range(15):
            forecaster.record_snapshot("svc-trend", {"performance": 0.9 - i * 0.03})
        service = forecaster.get_service("svc-trend")
        assert service["trend"] in ("improving", "stable", "degrading")

    def test_service_list(self, forecaster):
        forecaster.register_service("svc-list", "List Test")
        services = forecaster.list_services()
        assert len(services) >= 1

    def test_delete_service(self, forecaster):
        forecaster.register_service("svc-del", "Delete Me")
        assert forecaster.delete_service("svc-del") is True
        assert forecaster.get_service("svc-del") is None


# === test_incident_remediation.py ===

@pytest.fixture
def remediation_engine():
    return IncidentRemediationEngine({})


class TestIncidentRemediation:
    def test_suggest_remediation(self, remediation_engine):
        incident = {"title": "High CPU Usage Detected", "description": "CPU at 95% for 5 minutes"}
        suggestions = remediation_engine.suggest_remediation(incident)
        assert len(suggestions) > 0
        assert suggestions[0]["adjusted_confidence"] > 0

    def test_create_remediation(self, remediation_engine):
        rem = remediation_engine.create_remediation("inc-001", "restart_service", {"service": "nginx"}, 0.85, "service_down")
        assert rem["status"] == "pending"
        assert rem["incident_id"] == "inc-001"

    def test_auto_approve_high_confidence(self, remediation_engine):
        rem = remediation_engine.create_remediation("inc-002", "rollback_deploy", {}, 0.95, "deploy_failure")
        assert rem["status"] == "approved"

    def test_approve_remediation(self, remediation_engine):
        rem = remediation_engine.create_remediation("inc-003", "scale_up", {}, 0.7, "high_cpu")
        result = remediation_engine.approve_remediation(rem["id"], "admin")
        assert result["status"] == "approved"

    def test_reject_remediation(self, remediation_engine):
        rem = remediation_engine.create_remediation("inc-004", "restart_service", {}, 0.6, "generic")
        result = remediation_engine.reject_remediation(rem["id"], "No approval for this action")
        assert result["status"] == "rejected"

    def test_execute_remediation(self, remediation_engine):
        rem = remediation_engine.create_remediation("inc-005", "restart_service", {}, 0.9, "service_down")
        result = remediation_engine.execute_remediation(rem["id"])
        assert result["status"] in ("completed", "failed")

    def test_list_remediations(self, remediation_engine):
        remediation_engine.create_remediation("inc-a", "restart", {}, 0.8, "pattern-a")
        remediation_engine.create_remediation("inc-b", "scale", {}, 0.7, "pattern-b")
        all_rems = remediation_engine.list_remediations()
        assert len(all_rems) >= 2

    def test_get_statistics(self, remediation_engine):
        stats = remediation_engine.get_statistics()
        assert "total_remediations" in stats
        assert "success_rate" in stats

    def test_get_patterns(self, remediation_engine):
        patterns = remediation_engine.get_patterns()
        assert len(patterns) > 0
        assert any(p["pattern"] == "high_cpu" for p in patterns)


# === test_ops_chatbot.py ===

@pytest.fixture
def chatbot():
    return OpsChatbot({})


class TestOpsChatbot:
    def test_restart_service(self, chatbot):
        result = chatbot.process_message("user-1", "restart nginx")
        assert result["type"] == "success"
        assert "restarting" in result["text"].lower()

    def test_check_logs(self, chatbot):
        result = chatbot.process_message("user-1", "logs api-server")
        assert result["type"] == "success"
        assert "logs" in result["text"].lower()

    def test_run_backup(self, chatbot):
        result = chatbot.process_message("user-1", "backup postgres")
        assert result["type"] == "success"
        assert "backup" in result["text"].lower()

    def test_check_status(self, chatbot):
        result = chatbot.process_message("user-1", "status web-server")
        assert result["type"] == "success"

    def test_list_services(self, chatbot):
        result = chatbot.process_message("user-1", "list services")
        assert result["type"] == "success"
        assert "services" in result["text"].lower()

    def test_scale_service(self, chatbot):
        result = chatbot.process_message("user-1", "scale api-service 5")
        assert result["type"] == "success"

    def test_deploy_version(self, chatbot):
        result = chatbot.process_message("user-1", "deploy v3.2 staging")
        assert result["type"] == "success"

    def test_clear_cache(self, chatbot):
        result = chatbot.process_message("user-1", "clear cache cdn")
        assert result["type"] == "success"

    def test_run_diagnostic(self, chatbot):
        result = chatbot.process_message("user-1", "diagnostic database")
        assert result["type"] == "success"

    def test_show_metrics(self, chatbot):
        result = chatbot.process_message("user-1", "metrics gateway")
        assert result["type"] == "success"

    def test_unknown_command(self, chatbot):
        result = chatbot.process_message("user-1", "do something weird and crazy")
        assert result["type"] == "error"

    def test_conversation_tracking(self, chatbot):
        r1 = chatbot.process_message("user-2", "status nginx")
        conv_id = r1["conversation_id"]
        r2 = chatbot.process_message("user-2", "restart nginx", conversation_id=conv_id)
        conv = chatbot.get_conversation(conv_id)
        assert len(conv["messages"]) >= 4

    def test_task_history(self, chatbot):
        chatbot.process_message("user-3", "restart web")
        chatbot.process_message("user-3", "logs web")
        tasks = chatbot.list_tasks(user_id="user-3")
        assert len(tasks) >= 2

    def test_analytics(self, chatbot):
        chatbot.process_message("user-analytics", "status app")
        chatbot.process_message("user-analytics", "restart app")
        chatbot.process_message("user-analytics", "logs app")
        analytics = chatbot.get_analytics()
        assert analytics["total_messages"] >= 3


# === test_predictive_scaling.py ===

@pytest.fixture
def scaling_engine():
    return PredictiveScalingEngine({})


class TestPredictiveScaling:
    def test_record_metric(self, scaling_engine):
        result = scaling_engine.record_metric("web-01", "cpu", 45.2)
        assert result["value"] == 45.2

    def test_predict_insufficient_data(self, scaling_engine):
        result = scaling_engine.predict("web-01", "cpu")
        assert "error" in result

    def test_predict_with_data(self, scaling_engine):
        for i in range(30):
            scaling_engine.record_metric("web-02", "cpu", 40 + i * 0.5)
        result = scaling_engine.predict("web-02", "cpu")
        assert "forecast" in result
        assert len(result["forecast"]) > 0

    def test_set_policy(self, scaling_engine):
        assert scaling_engine.set_scaling_policy("web-03", "aggressive") is True
        assert scaling_engine.set_scaling_policy("web-03", "invalid") is False

    def test_get_metrics(self, scaling_engine):
        for i in range(20):
            scaling_engine.record_metric("web-04", "cpu", 50 + i)
        metrics = scaling_engine.get_metrics("web-04", "cpu")
        assert metrics["data_points"] >= 1

    def test_scaling_action(self, scaling_engine):
        for i in range(25):
            scaling_engine.record_metric("web-05", "cpu", 30 + i * 2)
        pred = scaling_engine.predict("web-05", "cpu")
        action = scaling_engine.execute_scaling_action(pred["id"])
        assert action is not None

    def test_summary(self, scaling_engine):
        summary = scaling_engine.get_summary()
        assert "total_predictions" in summary


# === test_root_cause_analysis.py ===

@pytest.fixture
def rca_analyzer():
    return RootCauseAnalyzer({})


class TestRootCauseAnalyzer:
    def test_ingest_event(self, rca_analyzer):
        event = rca_analyzer.ingest_event("metric", "prometheus", "High CPU", "CPU at 95%", {"value": 95}, "critical")
        assert event["event_type"] == "metric"
        assert event["source"] == "prometheus"
        assert event["severity"] == "critical"

    def test_analyze_with_no_events(self, rca_analyzer):
        result = rca_analyzer.analyze(incident_title="Test Incident", incident_description="Testing")
        assert result["root_cause"] is None
        assert result["confidence"] == 0.0

    def test_analyze_with_events(self, rca_analyzer):
        rca_analyzer.ingest_event("metric", "web-server", "High CPU", "CPU at 95%", {"value": 95}, "critical")
        rca_analyzer.ingest_event("log", "web-server", "Error rate spike", "Connection timeout errors", {}, "high")
        result = rca_analyzer.analyze(incident_title="Web Server Down", incident_description="Server unreachable")
        assert result["incident_id"] is not None

    def test_dependency_graph(self, rca_analyzer):
        rca_analyzer.set_dependency("web-server", ["database", "cache"])
        graph = rca_analyzer.get_dependency_graph()
        assert "web-server" in graph
        assert "database" in graph["web-server"]

    def test_list_incidents(self, rca_analyzer):
        rca_analyzer.analyze(incident_title="Incident A")
        rca_analyzer.analyze(incident_title="Incident B")
        incidents = rca_analyzer.list_incidents()
        assert len(incidents) >= 2

    def test_get_events_filtered(self, rca_analyzer):
        rca_analyzer.ingest_event("metric", "source-a", "Event A", "")
        rca_analyzer.ingest_event("log", "source-b", "Event B", "")
        filtered = rca_analyzer.get_events(source="source-a")
        assert all(e["source"] == "source-a" for e in filtered)

    def test_clear_events(self, rca_analyzer):
        rca_analyzer.ingest_event("metric", "test", "Test", "")
        rca_analyzer.clear_events()
        assert len(rca_analyzer.events) == 0

    def test_clear_incidents(self, rca_analyzer):
        rca_analyzer.analyze(incident_title="Test")
        rca_analyzer.clear_incidents()
        assert len(rca_analyzer.incidents) == 0
