import pytest
from services.integration_service.src.compliance_v4.compliance_as_code import (
    ComplianceAsCodeEngine, PolicyStatus, ControlSeverity, PolicyEffect,
)

@pytest.fixture
def engine(tmp_path):
    return ComplianceAsCodeEngine({"compliance_code_data_file": str(tmp_path / "cac.json")})

def test_default_controls_loaded(engine):
    controls = engine.get_controls()
    assert len(controls) > 0

def test_get_controls_by_framework(engine):
    soc2 = engine.get_controls(framework="SOC_2")
    assert len(soc2) > 0
    for c in soc2:
        assert c.framework == "SOC_2"

def test_create_control(engine):
    control = engine.create_control("SOC_2", "Test Control", "Test desc",
                                     "security", "high", "package test\ndefault deny = true")
    assert control.framework == "SOC_2"
    assert control.status == PolicyStatus.DRAFT

def test_evaluate_compliant(engine):
    result = engine.evaluate("SOC2-CC5", {"resource_type": "storage", "encryption_at_rest": True, "encryption_in_transit": True})
    assert result["status"] == "compliant"

def test_evaluate_violation(engine):
    result = engine.evaluate("SOC2-CC5", {"resource_type": "database", "encryption_at_rest": False})
    assert result["status"] == "violation"

def test_evaluate_unknown_control(engine):
    with pytest.raises(ValueError):
        engine.evaluate("UNKNOWN", {})

def test_update_control_status(engine):
    engine.update_control_status("SOC2-CC5", "inactive")
    c = engine.get_controls(control_id="SOC2-CC5")[0] if hasattr(engine, 'get_controls') else None
    controls = engine.get_controls()
    target = next((c for c in controls if c.control_id == "SOC2-CC5"), None)
    assert target is not None
    assert target.status == PolicyStatus.INACTIVE

def test_update_control_invalid_status(engine):
    with pytest.raises(ValueError):
        engine.update_control_status("SOC2-CC5", "invalid_status")

def test_test_policy(engine):
    results = engine.test_policy(
        "package test\ndeny { input.x == 1 }",
        [{"x": 1}, {"x": 2}, {"x": 1}],
    )
    assert results["total_tests"] == 3
    assert results["passed"] == 1

def test_get_policy_templates(engine):
    templates = engine.get_policy_templates()
    assert "ensure_encryption" in templates
    assert "access_control" in templates

def test_get_statistics(engine):
    stats = engine.get_statistics()
    assert stats["total_controls"] > 0
    assert "by_framework" in stats

def test_bulk_evaluate(engine):
    inputs = [
        {"control_id": "SOC2-CC5", "input_data": {"resource_type": "storage", "encryption_at_rest": True, "encryption_in_transit": True}},
        {"control_id": "SOC2-A1", "input_data": {"environment": "production", "backup_enabled": False}},
    ]
    results = engine.bulk_evaluate(inputs)
    assert len(results) == 2

def test_create_policy_version(engine):
    version = engine.create_policy_version("SOC2-CC5", "package v2\ndefault deny = true", "2.0.0")
    assert version["control_id"] == "SOC2-CC5"
    assert version["status"] == "draft"

def test_export_import_template(engine, tmp_path):
    path = engine.export_template("ensure_encryption")
    assert path is not None
    result = engine.import_template(path, "imported_template")
    assert result["imported"] is True

def test_dry_run_policy(engine):
    result = engine.dry_run_policy(
        "package test\ndeny { input.severity == \"critical\" }",
        {"severity": "critical"},
    )
    assert result["result"] == "violation"
    assert result["trigger_count"] > 0

def test_gap_analysis(engine):
    gap = engine.gap_analysis("SOC_2")
    assert gap["framework"] == "SOC_2"
    assert "policy_coverage" in gap

def test_compare_policies(engine):
    comp = engine.compare_policies("SOC2-CC5", "SOC2-A1")
    assert comp["control_1"]["id"] == "SOC2-CC5"
    assert comp["control_2"]["id"] == "SOC2-A1"
