import pytest
from datetime import datetime, timedelta
from services.integration_service.src.compliance_v4.continuous_compliance import (
    ContinuousComplianceMonitor, FrameworkPosture, ComplianceControl,
)

@pytest.fixture
def monitor():
    return ContinuousComplianceMonitor({"compliance_data_file": "data/test_cc.json"})

def test_assess_framework(monitor):
    posture = monitor.assess_framework("SOC_2")
    assert posture.framework == "SOC_2"
    assert posture.control_count > 0
    assert 0 <= posture.overall_score <= 100
    assert posture.status in ("compliant", "non_compliant")

def test_assess_unknown_framework(monitor):
    with pytest.raises(ValueError):
        monitor.assess_framework("UNKNOWN")

def test_assess_all_frameworks(monitor):
    results = monitor.assess_all_frameworks()
    assert len(results) == len(monitor.frameworks)
    for fw, posture in results.items():
        assert posture.overall_score >= 0

def test_get_posture(monitor):
    monitor.assess_framework("SOC_2")
    posture = monitor.get_posture("SOC_2")
    assert posture is not None
    assert posture.framework == "SOC_2"

def test_get_posture_all(monitor):
    monitor.assess_all_frameworks()
    postures = monitor.get_posture()
    assert len(postures) == len(monitor.frameworks)

def test_get_summary(monitor):
    monitor.assess_all_frameworks()
    summary = monitor.get_summary()
    assert summary["frameworks_assessed"] == len(monitor.frameworks)
    assert "overall_compliance_rate" in summary
    assert "status" in summary

def test_get_alerts(monitor):
    monitor.assess_all_frameworks()
    alerts = monitor.get_alerts()
    assert isinstance(alerts, list)

def test_get_trend(monitor):
    monitor.assess_framework("SOC_2")
    trend = monitor.get_trend("SOC_2", days=30)
    assert len(trend) >= 1

def test_detect_drift(monitor):
    monitor.assess_framework("SOC_2")
    drift = monitor.detect_drift("SOC_2")
    assert isinstance(drift, list)

def test_compare_frameworks(monitor):
    monitor.assess_all_frameworks()
    comp = monitor.compare_frameworks()
    assert "comparison" in comp
    assert "highest" in comp
    assert "lowest" in comp

def test_generate_report(monitor):
    monitor.assess_framework("SOC_2")
    report = monitor.generate_report("SOC_2")
    assert report["framework"] == "SOC_2"
    assert "overall_score" in report
    assert "control_summary" in report

def test_generate_report_nonexistent(monitor):
    report = monitor.generate_report("NONEXISTENT")
    assert "error" in report

def test_assess_batch(monitor):
    results = monitor.assess_batch(["SOC_2", "HIPAA"])
    assert len(results) == 2

def test_schedule_scans(monitor):
    sched = monitor.schedule_scans(interval_minutes=30)
    assert sched["interval_minutes"] == 30
    assert sched["status"] == "active"

def test_get_remediation_plan(monitor):
    monitor.assess_framework("SOC_2")
    plan = monitor.get_remediation_plan("SOC_2")
    assert isinstance(plan, list)

def test_get_compliance_trend(monitor):
    monitor.assess_all_frameworks()
    trend = monitor.get_compliance_trend(days=90)
    assert "daily_scores" in trend
    assert "overall_trend" in trend

def test_set_notification_hook(monitor):
    hook = monitor.set_notification_hook("https://hooks.example.com", ["score_change", "drift"])
    assert hook["status"] == "active"
    assert hook["url"] == "https://hooks.example.com"

def test_assessment_history_recorded(monitor):
    monitor.assess_framework("GDPR")
    assert len(monitor.assessment_history) >= 1
    entry = monitor.assessment_history[-1]
    assert entry["framework"] == "GDPR"
    assert "score" in entry

def test_controls_have_remediation_steps(monitor):
    posture = monitor.assess_framework("PCI_DSS")
    for c in posture.controls:
        assert len(c.remediation_steps) > 0
